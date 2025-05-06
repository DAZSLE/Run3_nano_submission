"""
Get DATA datasets using the DAS API and save to JSONs

Usage:
    python get_datasets.py [--year YEAR] [--datasets DATASET]

Author(s): Raghav Kansal
"""


import json
from pprint import pprint
from dbs.apis.dbsClient import DbsApi
import argparse

dbs = DbsApi("https://cmsweb.cern.ch/dbs/prod/global/DBSReader")

DATASETS = {
    # Name: selectors
    "JetMET": ["JetHT", "JetMET"],
    "Muon": ["SingleMuon", "Muon"],
    "EGamma": ["EGamma"],
    "Tau": ["Tau"],
    "BTagMu": ["BTagMu"],
    "MuonEG": ["MuonEG"],
    "ParkingVBF": ["ParkingVBF"],
    "ParkingSingleMuon": ["ParkingSingleMuon"],
}

YEARS = ["2022", "2022EE", "2023", "2023BPix", "2024"]

data_tags = {
    # 2022 summary slide: https://docs.google.com/presentation/d/1F4ndU7DBcyvrEEyLfYqb29NGkBPs20EAnBxe_l7AEII/edit
    "2022": {
        "C": "Run2022C-22Sep2023",
        "D": "Run2022D-22Sep2023",
    },
    "2022EE": {
        "E": "Run2022E-22Sep2023",
        "F": "Run2022F-22Sep2023",
        "G": "Run2022G-22Sep2023",
    },
    # 2023 summary slide: https://docs.google.com/presentation/d/1TjPem5jX0fzqvTGl271_nQFoVBabsrdrO0i8Qo1uD5E/edit
    "2023": {
        "C": "Run2023C-22Sep2023",
    },
    "2023BPix": {
        "D": "Run2023D-22Sep2023",
    },
    # 2024 summary slide: https://docs.google.com/presentation/d/1EHxQcWzw8IxPgCn8hm1prwSP-EktFtiuaEzH8WkQNVY/edit
    "2024": {
        "C": "Run2024C-2024CDEReprocessing",
        "D": "Run2024D-2024CDEReprocessing",
        "E": "Run2024E-2024CDEReprocessing",
        "F": "Run2024F-PromptReco",
        "G": "Run2024G-PromptReco",
        "H": "Run2024H-PromptReco",
        "I": "Run2024I-PromptReco",
    },
}


def get_data(datasets: list[str] = list(DATASETS.keys()), year: str = "2024"):
    """Get MINIAOD datasets for 2024 using the DAS API"""
    ddict = {}

    datasets = {k: DATASETS[k] for k in datasets}

    for dataset, selectors in datasets.items():
        print(f"Getting {dataset}")
        tdict = {}
        for tag in data_tags[year]:
            print(f"\t{tag}")
            for selector in selectors:
                if (selector in ["JetHT", "SingleMuon"]) and (year != "2022"):
                    # These are old names only used in 2022
                    continue

                das_datasets = dbs.listDatasets(dataset=f"/{selector}*/{data_tags[year][tag]}*/MINIAOD")
                for entry in das_datasets:
                    d = entry["dataset"]
                    # splitting index if dataset is split, e.g. JetMET0
                    d_split = d.split(selector)[1].split("/")[0]

                    if d_split.isdigit():
                        # check if the dataset is split
                        # if not any((d.split("/")[1] == selector + d_split) for selector in selectors):
                        if d.split("/")[1] != selector + d_split:
                            # Name matching
                            print(f"\t\tSkipping {d}")
                            continue

                        idx = f"{selector}_Run{year[:4]}{tag}_{d_split}"
                    else:
                        if d.split("/")[1] != selector:
                            # Name matching
                            print(f"\t\tSkipping {d}")
                            continue

                        idx = f"{selector}_Run{year[:4]}{tag}"

                    if idx not in tdict:
                        tdict[idx] = [d]
                    else:
                        tdict[idx].append(d)

        print("\tChecking for multiple entries")
        for idx, dlist in list(tdict.items()):
            if len(dlist) == 1:
                tdict[idx] = dlist[0]
            else:
                # Some datasets appear to split even further into computing versions
                # Based on this PDMV table https://pdmv-pages.web.cern.ch/run_3_data/full_table.html, we need to use them all
                print(
                    f"\t\t{idx} has multiple entries, will assume they are different computing versions and keep all"
                )

                for i in range(len(dlist)):
                    tdict[f"{idx}v{i+1}"] = dlist[i]

                tdict.pop(idx)

        ddict[dataset] = tdict

    return ddict

    # pprint(ddict)


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
        "--datasets",
        type=str,
        nargs="+",
        default=list(DATASETS.keys()),
        choices=list(DATASETS.keys()),
        help=f"List of datasets to query (default: {list(DATASETS.keys())})",
    )

    args = parser.parse_args()

    for year in args.years:
        ddict = get_data(datasets=args.datasets, year=year)

        # save to json
        with open(f"DATA_{year}.json", "w") as f:
            json.dump(ddict, f, indent=4)
