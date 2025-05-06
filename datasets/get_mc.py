"""
Get MC datasets using the DAS API and save to JSONs

Usage:
    python get_mc.py [--year YEAR] [--sample SAMPLE]

Author(s): Raghav Kansal
"""

import json
from pprint import pprint
from dbs.apis.dbsClient import DbsApi
import argparse

from utils import print_red, add_bool_arg

dbs = DbsApi("https://cmsweb.cern.ch/dbs/prod/global/DBSReader")

YEARS = ["2022", "2022EE", "2023", "2023BPix", "2024"]

mc_tags = {
    # 2022 summary slide: https://docs.google.com/presentation/d/1F4ndU7DBcyvrEEyLfYqb29NGkBPs20EAnBxe_l7AEII/edit
    "2022": ["Run3Summer22MiniAODv4"],
    "2022EE": ["Run3Summer22EE"],
    # 2023 summary slide: https://docs.google.com/presentation/d/1TjPem5jX0fzqvTGl271_nQFoVBabsrdrO0i8Qo1uD5E/edit
    "2023": ["Run3Summer23"],
    "2023BPix": ["Run3Summer23BPix"],
    # 2024 summary slide: https://docs.google.com/presentation/d/1EHxQcWzw8IxPgCn8hm1prwSP-EktFtiuaEzH8WkQNVY/edit
    "2024": [
        "RunIII2024Summer24MiniAOD-140X",  # This is the recommended tag
        "Run3Winter24MiniAOD-133X_mcRun3_2024_realistic_v10",
    ],
}

SAMPLES = {
    # sample name: MC selectors
    "HH4b": ["GluGlutoHHto4B*", "VBFHHto4B*"],
    "HHbbtt": ["GluGlutoHHto2B2Tau*", "VBFHHto2B2Tau*"],
    "QCD": ["QCD-4Jets_HT-*"],
    "TT": [
        "TTto2L2Nu_TuneCP5_13p6TeV*",
        "TTto4Q_TuneCP5_13p6TeV*",
        "TTtoLNu2Q_TuneCP5_13p6TeV*",
    ],
    "SingleTop": [
        "TbarWplusto4Q_TuneCP5_13p6TeV*",
        "TbarWplustoLNu2Q_TuneCP5_13p6TeV*",
        "TWminusto4Q_TuneCP5_13p6TeV*",
        "TWminustoLNu2Q_TuneCP5_13p6TeV*",
        "TbarBQ*",
        "TBbarQ*",
    ],
    "Hbb": ["*Hto2B*M-125*"],
    "Hcc": ["*Hto2C*M-125*"],
    "Htautau": ["*HToTauTau*M-125*"],
    "DYJetsLO": ["DYto2L-4Jets_MLL-50to120_HT-*"],
    "DYJetsNLO": ["DYto2L-2Jets_MLL-50_*J_TuneCP5_13p6TeV"],
    "VJetsLO": ["Wto2Q-3Jets_HT*" "Zto2Q-4Jets_HT*"],
    "VJetsNLO": ["Wto2Q-2Jets_PT*", "WtoLNu-2Jets_*J*", "Zto2Q-2Jets_PTQQ*"],
    "Diboson": [
        "WW_TuneCP5*",
        # "WWto2L2Nu_TuneCP5*"
        # "WWto4Q_TuneCP5*"
        # "WWtoLNu2Q_TuneCP5*"
        "WZ_TuneCP5*",
        # "WZto2L2Q_TuneCP5*",
        # "WZto3LNu_TuneCP5*",
        # "WZtoLNu2Q_TuneCP5*"
        "ZZ_TuneCP5*",
        # "ZZto2L2Nu_TuneCP5*",
        # "ZZto2L2Q_TuneCP5*",
        # "ZZto2Nu2Q_TuneCP5*",
        # "ZZto4L_TuneCP5*",
        "WWto4Q-1Jets-4FS*",
        "WWtoLNu2Q-1Jets-4FS*",
        "WZto3LNu-1Jets-4FS*",
        "WZto4Q-1Jets-4FS*",
        "ZZto2L2Q-1Jets*",
        "ZZto4L-1Jets*",
    ],
}

# Ignore any paths which contain these strings:
IGNORE_SELECTORS = [
    # Pileup
    "PU65",
    "PU70",
    "NoPU",
    # Unnecessary TT datasets
    # "TTtoLNuCB",
    "TTtoBctoTauNu",
    "TTtoBsto2Tau",
    # Unecessary WJets
    "PTLNu",
    # ?
    "EcalUncalZElectron",
    "Run3Summer22MiniAODv4-FS22",  # TODO: look this up!
]


def get_mc(samples: list[str] = list(SAMPLES.keys()), year: str = "2024", tsg: bool = False):
    ddict = {}

    samples = {k: SAMPLES[k] for k in samples}

    for sample, subsamples in samples.items():
        print(f"Getting {sample}")
        tdict = {}
        for subsample in subsamples:
            pre_len = len(tdict)
            print(f"\t{subsample}")
            for tag in mc_tags[year]:
                das_datasets = dbs.listDatasets(dataset=f"/{subsample}/{tag}*/MINIAODSIM", detail=1)
                # pprint(das_datasets)
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

            if len(tdict) == pre_len:
                print_red("\t\tNo datasets found!")
            else:
                print(f"\t\tFound {len(tdict) - pre_len} datasets")

        for dname, dlist in list(tdict.items()):
            if len(dlist) > 1:
                if (
                    year == "2024"
                    and "RunIII2024Summer24MiniAOD-140X" in str(list(dlist[0].keys())[0])
                    and "Run3Winter24" in str(list(dlist[1].keys())[0])
                ):
                    # This means there is a RunIII2024Summer24 and a Run3Winter24 dataset, in which case we pick the RunIII2024Summer24 one.
                    print_red(
                        f"\n{dname} has {len(dlist)} datasets, choosing the RunIII2024Summer24 one"
                    )
                    tdict[dname] = list(dlist[0].keys())[0]
                elif any("ext1" in str(list(d.keys())[0]) for d in dlist):
                    # This means there are ext1, ext2 etc. extra datasets
                    for d in dlist.copy():
                        if "_ext" in str(list(d.keys())[0]):
                            extidx = int(
                                str(list(d.keys())[0]).split("_ext")[1].split("_")[0].split("-")[0]
                            )
                            if f"{dname}_ext{extidx}" not in tdict:
                                tdict[f"{dname}_ext{extidx}"] = list(d.keys())[0]
                            else:
                                raise ValueError(f"{dname} has multiple ext{extidx} datasets!")
                        else:
                            if isinstance(tdict[dname], str):
                                print_red(f"\n{dname} has {len(dlist)} datasets:")
                                pprint([list(d.keys())[0] for d in dlist])
                                raise ValueError(f"Weird edge case for dataset {dname}!")
                            else:
                                tdict[dname] = list(d.keys())[0]
                else:
                    # I don't know what this means.
                    print_red(f"\n{dname} has {len(dlist)} datasets:")
                    pprint([list(d.keys())[0] for d in dlist])
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
    add_bool_arg(parser, "TSG", "Allow TSG samples", default=False)

    args = parser.parse_args()

    if args.save:
        for year in args.years:
            ddict = get_mc(samples=args.samples, year=year, tsg=args.TSG)

            # save to json
            with open(f"MC_{year}.json", "w") as f:
                json.dump(ddict, f, indent=4)
