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
cmsRun.py configs/[CONFIG]
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
