# Datasets

## Setup

Follow [installation](https://github.com/DAZSLE/Run3_nano_submission/tree/NanoAODv14_140X?tab=readme-ov-file#installation) instructions, inluding the `dbs3-client`.

Make sure you have activated `cmsenv` but NOT sourced `crab-setup.sh`. 


## Scripts

For data:

```bash
python get_datasets.py [--year YEAR] [--dataset DATASET]  # DATASET is JetMET, Muon etc.
```

For MC:

```bash
# SAMPLES is HH4b, TT etc.
# --tsg allows TSG samples as well
python get_mc.py [--year YEAR] [--samples SAMPLES] [--tsg | --no-tsg]
```


## Adding datasets

### Data

1. Add the dataset (and/or selector) to the `DATASETS` dictionary in `get_datasets.py`.
2. Run `get_datasets.py` as above to update the JSONs.
3. Check that the correct datasets were added and that no datasets were removed unintentionally.
3. Make a PR.

### MC

1. Check the expected number of datasets that should be added.
2. Add the sample (and/or subsample) to the `SAMPLES` dictionary in `get_mc.py` with the expected number of datasets..
3. Run `get_mc.py` as above to update the JSONs.
4. Check that the correct datasets were added and that no datasets were removed unintentionally.
5. Make a PR.

