"""
This script is used to submit crab jobs for Run3 nanoAOD production.
"""

#! /usr/bin/env python3
import yaml
import argparse
import os
import re
import copy
import json
from pathlib import Path

# use python3 because crab client needs to call LumiList with python3 script
from CRABAPI.RawCommand import crabCommand

# from httplib import HTTPException
from http.client import HTTPException

# in python3, http.client replaces httplib
import string
import random
import hashlib


DATASETS = ["JetMET", "EGamma", "Muon", "MuonEG", "BTagMu", "Tau"]

CONFIGS = {
    "data": {
        "2022": "DATA_2022_NANO.py",
        "2022EE": "DATA_2022_NANO.py",
        "2023": "DATA_2023_NANO.py",
        "2023BPix": "DATA_2023_NANO.py",
        "2024": "DATA_2024_NANO.py",
    },
    "mc": {
        "2022": "MC_preEE2022_NANO.py",
        "2022EE": "MC_postEE2022_NANO.py",
        "2023": "MC_preBPix2023_NANO.py",
        "2023BPix": "MC_postBPix2023_NANO.py",
        "2024": "MC_2024_NANO.py",
    },
}

JSONS = {
    "2022": "Cert_Collisions2022_355100_362760_Golden.json",
    "2022EE": "Cert_Collisions2022_355100_362760_Golden.json",
    "2023": "Cert_Collisions2023_366442_370790_Golden.json",
    "2023BPix": "Cert_Collisions2023_366442_370790_Golden.json",
}


def submit(config):
    try:
        crabCommand("submit", config=config)
    except HTTPException as hte:
        print("Cannot execute command")
        print(hte.headers)


def rnd_str(N, seedstr="test"):
    # Seed with dataset name hash to be reproducible
    random.seed(int(hashlib.sha512(seedstr.encode("utf-8")).hexdigest(), 16))
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(N))


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def make(card, datasets, base_crab_config, test: bool):
    """Make crab configs."""
    print("Making configs in {}:".format(card["workArea"]))
    for dataset in datasets:
        print("   ==> " + dataset)
        crab_config = copy.deepcopy(base_crab_config)
        dataset_name = dataset.lstrip("/").replace("/", "_")

        tag = dataset.split("/")[2]
        if card["tag_mod"] is not None:
            tag = (
                re.sub(r"MiniAOD[v]?[0-9]?", card["tag_mod"], tag)
                if tag.startswith("RunII")
                else tag + "_" + card["tag_mod"]
            )
        elif card["tag_extension"] is not None:
            tag = tag + "_" + card["tag_extension"]
        else:
            raise ValueError(
                "Either ``campaign: tag_mod`` or ``campaign: tag_extension`` need to be specified"
            )

        if len(dataset_name) < 95:
            request_name = dataset_name
        else:
            request_name = dataset_name[:90] + rnd_str(8, dataset_name)

        verbatim_lines = []
        card_info = {
            "_requestName_": request_name,
            "_workArea_": card["workArea"],
            "_psetName_": card["config"],
            "_inputDataset_": dataset,
            "_outLFNDirBase_": card["outLFNDirBase"],
            "_storageSite_": card["storageSite"],
            "_publication_": str(card["publication"]),
            "_splitting_": "LumiBased" if card["data"] else "Automatic",
            "_outputDatasetTag_": tag,
        }

        if test:
            verbatim_lines.append("config.Data.totalUnits = 1")
            card_info["_publication_"] = "False"

        if card["data"]:
            verbatim_lines.append("config.Data.unitsPerJob = 50")
            verbatim_lines.append("config.JobType.maxJobRuntimeMin = 2750")
        if card["data"] and card["lumiMask"] is not None:
            verbatim_lines.append("config.Data.lumiMask = '{}'".format(card["lumiMask"]))
        if card["voGroup"] is not None:
            verbatim_lines.append("config.User.voGroup = '{}'".format(card["voGroup"]))

        for line in verbatim_lines:
            crab_config += "\n" + line
        crab_config += "\n"

        for key in card_info:
            crab_config = crab_config.replace(key, card_info[key])

        cfg_filename = os.path.join(card["workArea"], "submit_{}.py".format(dataset_name))
        with open(cfg_filename, "w") as cfg_file:
            cfg_file.write(crab_config)


def submit_wrapper(card, datasets, base_crab_config, test: bool):
    """Submit crab configs."""
    from multiprocessing import Process
    import imp

    print("Submitting configs:")
    for dataset in datasets:
        print("   ==> " + dataset)
        dataset_name = dataset.lstrip("/").replace("/", "_")
        cfg_filename = os.path.join(card["workArea"], "submit_{}.py".format(dataset_name))
        config_file = imp.load_source("config", cfg_filename)
        p = Process(target=submit, args=(config_file.config,))
        p.start()
        p.join()


def status(card, datasets):
    """Get status of crab jobs."""
    das_names = []
    for dataset in datasets:
        dataset_name = dataset.lstrip("/").replace("/", "_")
        if len(dataset_name) < 95:
            request_name = dataset_name
        else:
            request_name = dataset_name[:90] + rnd_str(8, dataset_name)
        cfg_dir = os.path.join(card["workArea"], "crab_" + request_name)
        o = os.popen("crab status " + cfg_dir).read().split("\n")
        for i, line in enumerate(o):
            if line.startswith("CRAB project directory:"):
                print(line)  # in python3, print(line) replaces print line
            if line.startswith("Jobs status"):
                for j in range(5):
                    if len(o[i + j]) < 2:
                        continue
                    if any(
                        s in o[i + j]
                        for s in [
                            "unsubmitted",
                            "idle",
                            "finished",
                            "running",
                            "transferred",
                            "transferring",
                            "failed",
                        ]
                    ):
                        print(o[i + j])

            if "Output dataset:" in line:
                das_names.append(line.split()[-1])

    das_names_file = "outputs_{}.txt".format(args.card.split("/")[-1].split(".")[0])
    print("Writing output dataset DAS names to: {}".format(das_names_file))
    with open(das_names_file, "w") as das_file:
        das_file.write("\n".join(das_names))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True, type=str, help="username for storing files")
    parser.add_argument(
        "--year",
        required=True,
        type=str,
        choices=["2022", "2022EE", "2023", "2023BPix", "2024"],
        help="year",
    )
    parser.add_argument(
        "--dataset", required=True, type=str, help="dataset to submit, e.g. JetMET, HH4b, etc."
    )
    parser.add_argument(
        "--card", default=None, type=str, help="(Optional) path to the crab config file"
    )
    parser.add_argument(
        "--make", action="store_true", help="Make crab configs according to the spec."
    )
    parser.add_argument(
        "--submit", action="store_true", help="Submit configs created by ``--make``."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Run `crab submit` but filter for only status info. Creates a list of DAS names.",
    )
    parser.add_argument(
        "--test",
        type=str2bool,
        default="False",
        choices={True, False},
        help="Test submit - only 1 file, don't publish.",
    )
    args = parser.parse_args()

    return args


def main(args):
    if args.card is not None:
        with open(args.card, "r") as f:
            input_card = yaml.safe_load(f)

        if "campaign" in input_card:
            input_card = input_card["campaign"]
    else:
        input_card = {}

    isData = args.dataset in DATASETS
    dlabel = "data" if isData else "mc"
    # mc_campaign = MC_CAMPAIGNS[args.year]
    # miniaod_version = "MINIAODv4"
    if isData:
        jsonFile = f"datasets/DATA_{args.year}.json"
    else:
        jsonFile = f"datasets/MC_{args.year}.json"
    with Path(jsonFile).open("r") as f:
        datasets = json.load(f)[args.dataset]

    defaults = {
        "name": f"{dlabel}_{args.year}_{args.dataset}",
        "crab_template": "template_crab.py",
        "workArea": f"crab/{dlabel}_{args.year}_{args.dataset}",
        "storageSite": "T3_US_FNALLPC",
        "outLFNDirBase": f"/store/group/lpcpfnano/PFNano_Run3/25v1/{args.user}/{dlabel}_{args.year}",
        "voGroup": None,
        "publication": True,
        "config": f"configs/{CONFIGS[dlabel][args.year]}",
        "tag_extension": "DAZSLE_PFNano",
        "tag_mod": None,
        "data": isData,
        "lumiMask": f"jsons/{JSONS[args.year]}" if isData else None,
        "datasets": datasets,
    }

    card = defaults | input_card

    work_area = Path(card["workArea"])
    if work_area.exists():
        if args.submit or args.make:
            # in python3, input replaces raw_input
            if input(f"``workArea: {work_area}`` already exists. Continue? (y/n)") != "y":
                exit()
    else:
        work_area.mkdir(parents=True, exist_ok=True)

    if (card["tag_mod"] is not None) and (card["tag_extension"] is not None):
        print(
            "Can't specify both ``campaign: tag_mod`` and ``campaign: tag_extension``. Leave one empty."
        )
        exit()

    with open(card["crab_template"], "r") as template_file:
        base_crab_config = template_file.read()

    datasets = [value for key, value in card["datasets"].items() if len(value) > 10 and not value.startswith("#")]

    if args.make:
        make(card, datasets, base_crab_config, args.test)

    if args.submit:
        submit_wrapper(card, datasets, base_crab_config, args.test)

    if args.status:
        status(card, datasets)


if __name__ == "__main__":
    args = parse_args()
    main(args)
