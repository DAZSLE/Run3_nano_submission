# Run3_nano_submission

[![Codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

Only tested on el9 machines.

```bash
git clone https://github.com/DAZSLE/Run3_nano_submission
cd Run3_nano_submission
./setup.sh
```

Also install the DAS client if you are fetching datasets. 
**Note:** DAS client does not work after sourcing crab-setup.sh!

```bash
pip3 install dbs3-client
```

## Testing locally

```bash
cmsRun configs/[CONFIG]
```

## HTML documentation

To make documentation pages like [this](https://cms-nanoaod-integration.web.cern.ch/autoDoc/NanoAODv14/2024Prompt/doc_TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8_RunIII2024Summer24NanoAOD-140X_mcRun3_2024_realistic_v26-v2.html) run:

```bash
python3 cmssw/CMSSW_14_0_6_patch1/src/PhysicsTools/NanoAOD/test/inspectNanoFile.py MC_postEE2022.root -s MC_size.html -d MC_description.html
python3 cmssw/CMSSW_14_0_6_patch1/src/PhysicsTools/NanoAOD/test/inspectNanoFile.py DATA_2022.root -s DATA_size.html -d DATA_description.html
```

## Submission

First, run this to set up crab:

```bash
source /cvmfs/cms.cern.ch/common/crab-setup.sh
```

For testing:

```bash
python3 crabby.py --user [USERNAME] --year 2022 --dataset [XYZ] --make --submit --test True
```

where `--dataset` can take JetMET, QCD etc.

For full submission, simply remove `--test True`.
