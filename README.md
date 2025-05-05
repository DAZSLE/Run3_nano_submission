# Run3_nano_submission

[![Codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

```bash
cmsrel CMSSW_14_0_6_patch1
cd  CMSSW_14_0_6_patch1/src
cmsenv
scram-venv  # python venv
cmsenv
git cms-checkout-topic DAZSLE:CMSSW_14_0_6_BTVnano_GPT # Code is also in DAZSLE github
scram b -j 4
cd ../..
git clone git@github.com:DAZSLE/Run3_nano_submission.git -b NanoAODv14_140X
cd Run3_nano_submission
```

## Testing locally

```bash
cmsRun.py configs/[CONFIG]
```

## Submission

For testing:

```bash
python3 crabby.py --user [USERNAME] --year 2022 --dataset [XYZ] --make --submit --test True
```

where `--dataset` can take JetMET, QCD etc.

For full submission, simply remove `--test True`.
