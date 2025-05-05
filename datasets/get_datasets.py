from pprint import pprint
from dbs.apis.dbsClient import DbsApi

dbs = DbsApi("https://cmsweb.cern.ch/dbs/prod/global/DBSReader")

DATASETS = ["JetMET", "Muon", "EGamma", "Tau", "BTagMu", "MuonEG", "ParkingVBF", "ParkingSingleMuon"]

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
    }
}


def get_data(datasets: list[str] = DATASETS, year: str = "2024"):
    """Get MINIAOD datasets for 2024 using the DAS API"""
    ddict = {}

    for dataset in datasets:
        print(f"Getting {dataset}")
        tdict = {}
        for tag in data_tags[year]:
            print(f"\t{tag}")
            das_datasets = dbs.listDatasets(dataset=f"/{dataset}*/{data_tags[year][tag]}*/MINIAOD")
            for entry in das_datasets:
                d = entry["dataset"]
                # splitting index if dataset is split, e.g. JetMET0
                d_split = d.split(dataset)[1].split("/")[0]  

                if d_split.isdigit():
                    # check if the dataset is split
                    if d.split("/")[1] != dataset + d_split:
                        # Name matching
                        print(f"\t\tSkipping {d}")
                        continue

                    idx = f"{dataset}_Run{year}{tag}_{d_split}"
                else:
                    if d.split("/")[1] != dataset:
                        # Name matching
                        print(f"\t\tSkipping {d}")
                        continue

                    idx = f"{dataset}_Run{year}{tag}"
                
                if idx not in tdict:
                    tdict[idx] = [d]
                else:
                    tdict[idx].append(d)

        print("\tChecking for multiple entires")
        for idx, dlist in list(tdict.items()):
            if len(dlist) == 1:
                tdict[idx] = dlist[0]
            else:
                # Some datasets appear to split even further into computing versions
                # Based on this PDMV table https://pdmv-pages.web.cern.ch/run_3_data/full_table.html, we need to use them all
                print(f"\t\t{idx} has multiple entries, will assume they are different computing versions and keep all")

                for i in range(len(dlist)):
                    tdict[f"{idx}v{i+1}"] = dlist[i]

                tdict.pop(idx)
                
        ddict[dataset] = tdict

    return ddict

    # pprint(ddict)