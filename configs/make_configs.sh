#################################################################
# Makes configs for MC and Data
#
# Links: (and more below)
# https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/Releases/NanoAODv14#run3-2024-data-prompt-and-mc
#
# Author(s): Raghav Kansal
#################################################################

NEVENTS=1
NTHREADS=1

base_args="--customise DAZSLE/DAZSLE/customize.customize --step NANO:@BTV --scenario pp --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000\" --no_exec -n $NEVENTS --nThreads $NTHREADS --era Run3"
base_args_mc="$base_args --eventcontent NANOAODSIM --datatier NANOAODSIM --mc"
base_args_data="$base_args --eventcontent NANOAOD --datatier NANOAOD --data"

echo $base_args_mc

############# MC #############

# 2022-23 MC
# GTs from https://cms-talk.web.cern.ch/t/call-for-conditions-full-2022-2023-data-rereco-and-mc-production-in-140x/32887/54

name=MC_preEE2022
gt=140X_mcRun3_2022_realistic_v12
filein=/store/mc/Run3Summer22MiniAODv4/QCD_PT-15to20_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/MINIAODSIM/130X_mcRun3_2022_realistic_v5-v2/2520000/056b90db-c5cf-4f5f-a4cb-1c69bf4e65b5.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_mc

name=MC_postEE2022
gt=140X_mcRun3_2022_realistic_v12
filein=/store/mc/Run3Summer22EEMiniAODv4/QCD_PT-15to20_MuEnrichedPt5_TuneCP5_13p6TeV_pythia8/MINIAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/2520000/177762d0-23ed-436f-aa0d-a20c33e33dc3.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_mc

name=MC_preBPix2023
gt=140X_mcRun3_2023_realistic_v9
filein=/store/mc/Run3Summer23BPixMiniAODv4/DYTo2L_MLL-4to50_TuneCP5_13p6TeV_pythia8/MINIAODSIM/130X_mcRun3_2023_realistic_postBPix_v2-v1/60000/661a9e9a-e693-4216-9ea1-8d03793951ab.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_mc

name=MC_postBPix2023
gt=140X_mcRun3_2023_realistic_v9
filein=/store/mc/Run3Summer23BPixMiniAODv4/DYTo2L_MLL-4to50_TuneCP5_13p6TeV_pythia8/MINIAODSIM/130X_mcRun3_2023_realistic_postBPix_v2-v1/60000/661a9e9a-e693-4216-9ea1-8d03793951ab.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_mc

# 2024 MC
# GT: latest one from https://docs.google.com/presentation/d/1EHxQcWzw8IxPgCn8hm1prwSP-EktFtiuaEzH8WkQNVY/edit?slide=id.g34e821b3a62_2_0#slide=id.g34e821b3a62_2_0
name=MC_2024
gt=140X_mcRun3_2024_realistic_v26
filein=/store/mc/RunIII2024Summer24MiniAOD/QCD-4Jets_Bin-HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/MINIAODSIM/140X_mcRun3_2024_realistic_v26-v2/100000/00f7403b-49bf-4efd-9b8f-0398bd61d910.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_mc

############# DATA #############

# GT: using latest v14 one from https://docs.google.com/presentation/d/1EHxQcWzw8IxPgCn8hm1prwSP-EktFtiuaEzH8WkQNVY/edit?slide=id.g34e821b3a62_2_0#slide=id.g34e821b3a62_2_0
gt=140X_dataRun3_v20

name=DATA_2022
filein=/store/data/Run2022E/BTagMu/MINIAOD/22Sep2023-v1/2530000/004c666b-bfd9-4e91-b15b-8f7bb1587e75.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_data

# 2023 data
name=DATA_2023
filein=/store/data/Run2023C/BTagMu/MINIAOD/22Sep2023_v2-v1/2540000/0a4d9d3c-566d-48f2-886d-fbd4d5d513cf.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_data

# 2024 data
gt=140X_dataRun3_v20
filein=/store/data/Run2024E/BTagMu/MINIAOD/2024CDEReprocessing-v1/120000/0f8aeefe-1ccd-44a1-ba6d-dcb521f34188.root
cmsDriver.py $name --fileout file:$name.root --conditions $gt --filein $filein $base_args_data