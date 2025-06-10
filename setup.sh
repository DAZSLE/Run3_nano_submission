#!/usr/bin/env bash

#############################################################
# CMSSW setup
# Based on https://github.com/cms-tau-pog/NanoProd/blob/main/env.sh
#
# Author(s): Raghav Kansal
#############################################################

CMSSW_VER=CMSSW_14_0_6_patch1
this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

run_cmd() {
  "$@"
  RESULT=$?
  if (( $RESULT != 0 )); then
    echo "Error while running '$@'"
    exit $RESULT
  fi
}

run_cmd source /cvmfs/cms.cern.ch/cmsset_default.sh

if ! [ -f "$this_dir/cmssw/$CMSSW_VER/.installed" ]; then
    run_cmd mkdir -p "$this_dir/cmssw"
    run_cmd cd "$this_dir/cmssw"
    if [ -d $CMSSW_VER ]; then
      echo "Removing incomplete $CMSSW_VER installation..."
      run_cmd rm -rf $CMSSW_VER
    fi
    echo "Creating $CMSSW_VER area in $PWD ..."
    run_cmd scramv1 project CMSSW $CMSSW_VER
    run_cmd cd $CMSSW_VER/src
    run_cmd eval `scramv1 runtime -sh`

    #install CMSSW updates not in official releases
    master_ver=`echo $CMSSW_VER | cut -d'_' -f 2`
    sub_ver=`echo $CMSSW_VER | cut -d'_' -f 3`
    subsub_ver=`echo $CMSSW_VER | cut -d'_' -f 4`
    if [[ $master_ver == "14"  && $sub_ver == "0" ]]; then
      run_cmd echo "=> Installing addons for CMSSW_"${master_ver}"_"$sub_ver
      run_cmd git cms-checkout-topic DAZSLE:CMSSW_14_0_6_BTVnano_GPT
      # Extra tau models from Tau POG
      run_cmd wget https://github.com/cms-tau-pog/RecoTauTag-TrainingFiles/raw/refs/heads/BoostedDeepTau_v2/BoostedDeepTauId/boosteddeepTau_RunIIv2p0_{core,inner,outer}.pb -P RecoTauTag/TrainingFiles/data/BoostedDeepTauId/
      run_cmd wget https://github.com/cms-tau-pog/RecoTauTag-TrainingFiles/raw/refs/heads/deepTau_v2p5_noDomainAdaptation/DeepTauId/deepTau_2018v2p5_noDomainAdaptation_{core,inner,outer}.pb -P RecoTauTag/TrainingFiles/data/DeepTauId/
    fi

    # custom code
    # not sure why, but this directory structure is necessary...
    run_cmd mkdir -p DAZSLE/DAZSLE
    run_cmd ln -s "$this_dir/customizations" DAZSLE/DAZSLE/python

    run_cmd scram b -j8
    run_cmd cmsenv
    run_cmd cd "$this_dir"
    run_cmd touch "$this_dir/cmssw/$CMSSW_VER/.installed"
else
    run_cmd cd "$this_dir/cmssw/$CMSSW_VER/"
    run_cmd cmsenv
    run_cmd cd ../..
fi