"""
Get MC datasets using the DAS API and save to JSONs

Usage:
    python get_mc.py [--year YEAR] [--sample SAMPLE]

Author(s): Raghav Kansal
"""

from dataclasses import dataclass, field
import json
from pprint import pprint
from dbs.apis.dbsClient import DbsApi
import argparse
from pathlib import Path

from utils import print_red, add_bool_arg

dbs = DbsApi("https://cmsweb.cern.ch/dbs/prod/global/DBSReader")

YEARS = ["2022", "2022EE", "2023", "2023BPix", "2024"]
YEARS_2022_23 = ["2022", "2022EE", "2023", "2023BPix"]
YEARS_2024 = ["2024"]

mc_tags = {
    # 2022 summary slide: https://docs.google.com/presentation/d/1F4ndU7DBcyvrEEyLfYqb29NGkBPs20EAnBxe_l7AEII/edit
    "2022": ["Run3Summer22MiniAODv4"],
    "2022EE": ["Run3Summer22EEMiniAODv4"],
    # 2023 summary slide: https://docs.google.com/presentation/d/1TjPem5jX0fzqvTGl271_nQFoVBabsrdrO0i8Qo1uD5E/edit
    "2023": ["Run3Summer23MiniAODv4"],
    "2023BPix": ["Run3Summer23BPixMiniAODv4"],
    # 2024 summary slide: https://docs.google.com/presentation/d/1EHxQcWzw8IxPgCn8hm1prwSP-EktFtiuaEzH8WkQNVY/edit
    "2024": [
        "RunIII2024Summer24MiniAOD-140X",  # This is the recommended tag
        "Run3Winter24MiniAOD-133X_mcRun3_2024_realistic",
    ],
}


@dataclass
class Sample:
    selector: str
    expected_datasets: int
    # If True, will raise an error if the number of datasets found is not = to expected_datasets
    strict: bool = True
    # If True, will raise an error if the number of datasets found is not ≥ expected_datasets
    strictgt: bool = True
    # list of years to check for this sample, in case e.g. naming convention changed at some point - defaults to all years
    years: list[str] = field(default_factory=lambda: YEARS)

    def isStrict(self, year: str = None):
        # no strictness in 2024 for now
        return self.strict and year != "2024"

    def isStrictgt(self, year: str = None):
        # no strictness in 2024 for now
        return self.strictgt and year != "2024"


SAMPLES = {
    # sample name: Subsample(selector, # expected datasets)
    # !!! Adding the right number of expected datasets is a useful check! !!!
    "HH4b": [Sample("GluGlutoHHto4B*", 4), Sample("VBFHHto4B*", 10)],
    # Not strict because of extra FS22 datasets in 2022
    "HHbbtt": [Sample("GluGlutoHHto2B2Tau*", 4, strict=False), Sample("VBFHHto2B2Tau*", 10)],
    "QCD-4Jets_HT": [Sample("QCD-4Jets_HT-*", 11)],
    # Not strict because of extra flat datasets in some years
    "QCD_PT": [Sample("QCD_PT-*", 16, strict=False)],
    "TT": [
        Sample("TTto2L2Nu_TuneCP5_13p6TeV*", 1),
        Sample("TTto4Q_TuneCP5_13p6TeV*", 1),
        Sample("TTtoLNu2Q_TuneCP5_13p6TeV*", 1),
    ],
    "SingleTop": [
        Sample("TbarWplusto4Q_TuneCP5_13p6TeV*", 1),
        Sample("TbarWplustoLNu2Q_TuneCP5_13p6TeV*", 1),
        Sample("TWminusto4Q_TuneCP5_13p6TeV*", 1),
        Sample("TWminustoLNu2Q_TuneCP5_13p6TeV*", 1),
        Sample("TbarBQ_t-channel_4FS*", 1),
        Sample("TBbarQ_t-channel_4FS*", 1),
    ],
    "Hbb": [Sample("*Hto2B*M-125*", 14, strict=False)],  # random extra datasets in some years...
    "Hcc": [Sample("*Hto2C*M-125*", 14, strict=False)],  # random extra datasets in some years...
    "Htautau": [
        Sample("*Hto2Tau*M-125*", 4),
        Sample("*HTo2Tau*M-125*", 8),  # Extra "Filtered" datasets in some years
    ],
    "DYJetsLO": [
        Sample("DYto2L-4Jets_MLL-50to120_HT-*", 7),
        # temporary?
        Sample("DYto2L-4Jets_MLL-50*", 5, years=YEARS_2024),
    ],
    # Not strict because of extra datasets in some years
    "DYJetsNLO": [
        Sample("DYto2L-2Jets_MLL-50_*J_TuneCP5_13p6TeV*", 11, strict=False),
        # temporarily while waiting for [0-2]J datasets
        Sample("DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV*", 11, strict=False, years=YEARS_2024),
    ],
    "VJetsLO": [
        Sample("Wto2Q-3Jets_HT*", 4),
        Sample("WtoLNu-4Jets_*J*", 4),
        Sample("Zto2Q-4Jets_HT*", 4),
    ],
    "VJetsNLO": [
        Sample("Wto2Q-2Jets_PT*", 8),
        Sample("WtoLNu-2Jets_*J*", 3),
        Sample("Zto2Q-2Jets_PTQQ*", 8),
    ],
    "Diboson": [
        Sample("WW_TuneCP5*", 1),
        # "WWto2L2Nu_TuneCP5*"  # Leaving these out for now, unless someone needs them
        # "WWto4Q_TuneCP5*"
        # "WWtoLNu2Q_TuneCP5*"
        Sample("WZ_TuneCP5*", 1),
        # "WZto2L2Q_TuneCP5*",
        # "WZto3LNu_TuneCP5*",
        # "WZtoLNu2Q_TuneCP5*"
        Sample("ZZ_TuneCP5*", 1),
        # "ZZto2L2Nu_TuneCP5*",
        # "ZZto2L2Q_TuneCP5*",
        # "ZZto2Nu2Q_TuneCP5*",
        # "ZZto4L_TuneCP5*",
        # Not strict because they aren't produced for some years
        Sample("WWto4Q-1Jets-4FS*", 1, strict=False, strictgt=False),
        Sample("WWtoLNu2Q-1Jets-4FS*", 1, strict=False, strictgt=False),
        Sample("WZto3LNu-1Jets-4FS*", 1),
        Sample("WZto4Q-1Jets-4FS*", 1),
        Sample("ZZto2L2Q-1Jets*", 1),
        Sample("ZZto4L-1Jets*", 1),
    ],
    "EWKV": [
        Sample("VBFZto2Q*", 1),
        Sample("VBFWto2Q*", 1),
        Sample("VBFto2L_MLL-50*", 1),
        Sample("VBFto2Nu*", 1),
        Sample("VBFtoLNu*", 1),
    ],
    "VGamma": [
        Sample("WGtoLNuG-1Jets_PTG-*", 5),
        Sample("WGto2QG-1Jets_PTG-*", 2, strict=False),
        Sample("ZGto2NuG-1Jets_PTG-*", 5),
        Sample("ZGto2QG-1Jets_PTG-*", 2, strict=False),
    ],
}

# Ignore any paths which contain these strings:
IGNORE_SELECTORS = [
    # Pileup datasets
    "PU65",
    "PU70",
    "NoPU",
    "EpsilonPU",
    "FlatPU0to120",
    "Poisson60ForMUOVal",
    "FlatPU0to70",
    # Unnecessary QCD datasets
    "bcToE",
    "SpinOFF",
    "EMEnriched",
    "MuEnriched",
    "Flat2018",
    # Unecessary WJets datasets
    "PTLNu",  # PTLNu binned
    # Unnecessary Higgs datasets
    "2HDM-II",
    # ?
    "EcalUncalZElectron",
    # Specific edge cases:
    # Have newer versions available
    "/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/Run3Summer23MiniAODv4-130X_mcRun3_2023_realistic_v14-v2/MINIAODSIM",
    "/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/Run3Summer23BPixMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v2/MINIAODSIM",
    "/QCD_PT-15to7000_TuneCP5_Flat2022_13p6TeV_pythia8/Run3Winter24MiniAOD-133X_mcRun3_2024_realistic_v9-v2/MINIAODSIM",
    "/DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Winter24MiniAOD-133X_mcRun3_2024_realistic_v9_ext2-v2/MINIAODSIM",
    "/WZ_TuneCP5_13p6TeV_pythia8/Run3Winter24MiniAOD-133X_mcRun3_2024_realistic_v7-v2/MINIAODSIM",
]


def get_mc(samples: list[str] = list(SAMPLES.keys()), year: str = "2024", tsg: bool = False):
    ddict = {}

    samples = {k: SAMPLES[k] for k in samples}

    for sample, subsamples in samples.items():
        print(f"Getting {sample}")
        tdict = {}
        for subsample in subsamples:
            if year not in subsample.years:
                continue
            pre_len = len(tdict)
            print(f"\t{subsample.selector}")
            for tag in mc_tags[year]:
                das_datasets = dbs.listDatasets(
                    dataset=f"/{subsample.selector}/{tag}*/MINIAODSIM", detail=1
                )
                # if sample in ["HH4b", "HHbbtt"]:
                #     print_red(f"/{subsample}/{tag}*/MINIAODSIM")
                #     pprint(das_datasets)
                for entry in das_datasets:
                    d = entry["dataset"]
                    if any(s in d for s in IGNORE_SELECTORS):
                        continue

                    if entry["prep_id"].startswith("TSG") and not tsg:
                        continue

                    dname = d.split("/")[1]
                    if dname not in tdict:
                        # print(f"\t\t{dname}")
                        tdict[dname] = [{d: entry}]
                    else:
                        tdict[dname].append({d: entry})

            # Checking number of datasets
            num_datasets = len(tdict) - pre_len
            if num_datasets == 0:
                print_red("\t\tNo datasets found!")
                if subsample.isStrict(year) and subsample.expected_datasets > 0:
                    raise ValueError(
                        f"This subsample has a strict requirement for {subsample.expected_datasets} dataset(s)!"
                    )
            elif num_datasets > subsample.expected_datasets:
                print_red(
                    f"\t\tFound {num_datasets} dataset(s), {num_datasets - subsample.expected_datasets} more than expected!"
                )
                if subsample.isStrict(year):
                    print(f"\nAll datasets found for {sample}:")
                    pprint([list(entries[0].values())[0]["dataset"] for entries in tdict.values()])
                    raise ValueError(
                        f"This subsample has a strict requirement for {subsample.expected_datasets} dataset(s)!"
                    )
            elif num_datasets < subsample.expected_datasets:
                print_red(
                    f"\t\tFound {num_datasets} dataset(s), {subsample.expected_datasets - num_datasets} fewer than expected!"
                )
                if subsample.isStrict(year) or subsample.isStrictgt(year):
                    pprint([list(entries[0].values())[0]["dataset"] for entries in tdict.values()])
                    raise ValueError(
                        f"This subsample has a strict requirement for (at least) {subsample.expected_datasets} dataset(s)!"
                    )
            else:
                print(f"\t\tFound {num_datasets} dataset(s) as expected.")

        for dname, dlist in list(tdict.items()):
            if len(dlist) > 1:
                # Handling multiple datasets with the same primary_ds_name

                # First remove any extra TSG datasets
                if any(list(d.values())[0]["prep_id"].startswith("TSG") for d in dlist):
                    for d in dlist.copy():
                        if list(d.values())[0]["prep_id"].startswith("TSG"):
                            dlist.remove(d)

                    if len(dlist) == 1:
                        # If there is only one dataset after removing TSG datasets, we pick that one and continue
                        tdict[dname] = list(dlist[0].keys())[0]
                        continue

                if (
                    year == "2024"
                    and "RunIII2024Summer24MiniAOD-140X" in str(list(dlist[0].keys())[0])
                    and "Run3Winter24" in str(list(dlist[1].keys())[0])
                ):
                    # This means there is a RunIII2024Summer24 and a Run3Winter24 dataset, in which case we pick the RunIII2024Summer24 one.
                    print_red(
                        f"\t{dname} has {len(dlist)} datasets, choosing the RunIII2024Summer24 one"
                    )
                    tdict[dname] = list(dlist[0].keys())[0]
                elif any("ext1" in str(list(d.keys())[0]) for d in dlist):
                    # This means there are ext1, ext2 etc. extra datasets, to which we add the _ext{idx} suffix
                    for d in dlist.copy():
                        if "_ext" in str(list(d.keys())[0]):
                            extidx = int(
                                str(list(d.keys())[0]).split("_ext")[1].split("_")[0].split("-")[0]
                            )
                            if f"{dname}_ext{extidx}" not in tdict:
                                tdict[f"{dname}_ext{extidx}"] = list(d.keys())[0]
                            else:
                                pprint([list(d.keys())[0] for d in dlist])
                                raise ValueError(f"{dname} has multiple ext{extidx} datasets!")
                        else:
                            if isinstance(tdict[dname], str):
                                print_red(f"\n{dname} has {len(dlist)} datasets:")
                                pprint([list(d.keys())[0] for d in dlist])
                                raise ValueError(f"Weird edge case for dataset {dname}!")
                            else:
                                tdict[dname] = list(d.keys())[0]
                elif (len(dlist) == 2) and (
                    sum("FS22" in str(list(d.keys())[0]) for d in dlist) == 1
                ):
                    # This means one is an FS22 dataset, to which we add the -FS22 suffix (not sure what FS22 means...)
                    for d in dlist.copy():
                        if "FS22" in str(list(d.keys())[0]):
                            tdict[f"{dname}-FS22"] = list(d.keys())[0]
                            dlist.remove(d)
                        else:
                            tdict[dname] = list(d.keys())[0]
                else:
                    # Run out of known cases
                    print_red(f"\n{dname} has {len(dlist)} datasets:")
                    pprint([list(d.keys())[0] for d in dlist])
                    # tdict.pop(dname)
                    raise ValueError("Don't know what to do here!")
            else:
                if list(dlist[0].values())[0]["prep_id"].startswith("TSG"):
                    # If the dataset is TSG, we add the -TSG suffix
                    tdict[f"{dname}-TSG"] = list(dlist[0].keys())[0]
                    tdict.pop(dname)
                else:
                    tdict[dname] = list(dlist[0].keys())[0]

        ddict[sample] = tdict

    return ddict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get MINIAOD datasets from DAS")
    parser.add_argument(
        "--years",
        type=str,
        nargs="+",
        default=YEARS,
        choices=YEARS,
        help="Year to get datasets for (default: all years)",
    )
    parser.add_argument(
        "--samples",
        type=str,
        nargs="+",
        default=list(SAMPLES.keys()),
        choices=list(SAMPLES.keys()),
        help=f"List of samples to query (default: {list(SAMPLES.keys())})",
    )
    add_bool_arg(parser, "save", "Save the datasets to a JSON file", default=True)
    add_bool_arg(
        parser,
        "append",
        "Append new samples to the JSON file (rather than overwriting it completely) if it already exists. If you want to overwrite the specific input samples, use --overwrite-samples.",
        default=True,
    )
    add_bool_arg(
        parser,
        "overwrite-samples",
        "Overwrite existing samples in the JSON file (if append is True). Will give an error if this is False, append is True, and the samples are already in the JSON file.",
        default=False,
    )
    add_bool_arg(parser, "tsg", "Allow TSG samples", default=False)

    args = parser.parse_args()

    if args.save:
        for year in args.years:
            tsamples = args.samples.copy()
            
            if args.append and Path(f"MC_{year}.json").exists():
                print(f"Appending to {f'MC_{year}.json'}")
                with Path(f"MC_{year}.json").open("r") as f:
                    ddict = json.load(f)
            else:
                ddict = {}
                if Path(f"MC_{year}.json").exists():
                    print_red(f"Overwriting {f'MC_{year}.json'}!")

            if not args.overwrite_samples:
                for sample in tsamples.copy():
                    if sample in ddict:
                        print_red(f"Sample {sample} already exists in {f'MC_{year}.json'} - skipping! If you want to overwrite it, use the --overwrite-samples option.")
                        tsamples.remove(sample)

            ddict_new = get_mc(samples=tsamples, year=year, tsg=args.tsg)

            for sample in ddict_new:
                if sample in ddict:
                    if args.overwrite_samples:
                        print(f"Overwriting {sample} in {f'MC_{year}.json'}!")
                        ddict[sample] = ddict_new[sample]
                else:
                    ddict[sample] = ddict_new[sample]

            # save to json
            with Path(f"MC_{year}.json").open("w") as f:
                json.dump(ddict, f, indent=4)
