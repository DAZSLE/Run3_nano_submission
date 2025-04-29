# Run3_nano_submission

[![Codestyle](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Instructions

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
python3 crabby.py -c crab_ymls/mc_summer23_qcdincl.yml --make --submit --test True # Make sure you edit the yml file here
```
