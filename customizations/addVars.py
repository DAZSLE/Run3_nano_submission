# coding: utf-8

"""
Nano customizations, including
1. Tau POG variables


Based on https://github.com/uhh-cms/nanogen/blob/master/nanogen/customizations/default.py.
"""

from __future__ import annotations

import os
import enum

import FWCore.ParameterSet.Config as cms  # type: ignore[import-not-found]
from PhysicsTools.NanoAOD.common_cff import Var  # type: ignore[import-not-found]
from Configuration.DataProcessing.Utils import addMonitoring


# get the cmssw version triplet
cmssw_version = tuple(map(int, os.environ["CMSSW_VERSION"].split("_")[1:4]))


class Run(enum.Enum):
    II = "II"
    III = "III"


class NanoVersion(enum.Enum):
    V12 = "v12"
    V14 = "v14"


#
# High-level customization functions.
#

def no_customization(process, *, dataset_kind: str, **kwargs):
    """
    No customization and returns the process unchanged.
    """
    return process


def _customize(
    process,
    run: Run,
    nano_version: NanoVersion,
    *,
    # added by task
    dataset_kind: str,
    # added by nano config yaml
    pf_candidates: bool = True,
    l1t_objects: bool = True,
    **kwargs,
):
    # default customization recommended here https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/Instructions/Private-production
    addMonitoring(process)

    # update gen particle selection
    if dataset_kind == "mc":
        process = update_gen_particles(process, run, nano_version)

    # add pv variables
    process = add_pv_variables(process, run, nano_version)

    # add tau variables
    process = add_tau_variables(process, run, nano_version)

    # add met variables
    process = add_met_variables(process, run, nano_version)

    # add PF candidates
    if pf_candidates:
        process = add_pf_candidates(process, run, nano_version)

    # add L1 Trigger objects
    if l1t_objects:
        process = add_l1t_objects(process)

    return process


def customize_run2_v12(process, **kwargs):
    return _customize(process, Run.II, NanoVersion.V12, **kwargs)


def customize_run3_v12(process, **kwargs):
    return _customize(process, Run.III, NanoVersion.V12, **kwargs)


def customize_run3_v14(process, **kwargs):
    return _customize(process, Run.III, NanoVersion.V14, **kwargs)


#
# Utils.
#

def pdg_abs_or(pdgs: list[int]) -> str:
    abs_or = " || ".join([f"abs(pdgId) == {pdg}" for pdg in pdgs])
    return f"({abs_or})"


def var_f8(expr: str, **kwargs) -> Var:
    return Var(expr, float, precision=8, **kwargs)


def var_f10(expr: str, **kwargs) -> Var:
    return Var(expr, float, precision=10, **kwargs)


def var_i32(expr: str, **kwargs) -> Var:
    return Var(expr, int, **kwargs)


def var_i16(expr: str, **kwargs) -> Var:
    return Var(expr, "int16", **kwargs)


def var_ui32(expr: str, **kwargs) -> Var:
    return Var(expr, "uint", **kwargs)


def var_b(expr: str, **kwargs) -> Var:
    return Var(expr, bool, **kwargs)


#
# Lower-level modular customizations.
#

def update_gen_particles(process, run: Run, nano_version: NanoVersion):
    """
    With infos taken from TAU POG.
    https://github.com/cms-tau-pog/NanoProd/blob/c66e12e738528f5155043472f51452853abe9b14/NanoProd/python/customize.py#L5
    """
    vip = pdg_abs_or([6, 21, 22, 23, 24, 25, 35, 36, 37, 39, 9990012, 9900012, 1000015])
    leptons = pdg_abs_or([11, 12, 13, 14, 15, 16])
    process.finalGenParticles.select += [
        # parents and daughers of important particles
        f"keep+ statusFlags().isLastCopy() && {vip}",
        f"+keep statusFlags().isFirstCopy() && {vip}",
        # parents and full decay history of leptons
        f"keep++ statusFlags().isLastCopy() && {leptons}",
        f"+keep statusFlags().isFirstCopy() && {leptons}",
    ]

    # store the production vertex coordinate
    for coord in ["x", "y", "z"]:
        new_var = var_f10(f"vertex().{coord}", doc=f"{coord} coordinate of the production vertex")
        setattr(process.genParticleTable.variables, f"v{coord}", new_var)

    return process


def add_pv_variables(process, run: Run, nano_version: NanoVersion):
    if cmssw_version >= (14, 0, 0):
        from PhysicsTools.NanoAOD.leptonTimeLifeInfo_common_cff import addExtendVertexInfo  # type: ignore[import-not-found] # noqa
        addExtendVertexInfo(process)
        process.pvbsTable.variables.ndof = var_f8("ndof()", doc="number of degrees of freedom")
        process.pvbsTable.variables.valid = var_b("isValid()", doc="PV fit is valid")

    return process


def add_tau_variables(process, run: Run, nano_version: NanoVersion):
    """
    Taken from TAU POG.
    """
    # additional variables
    tau_vars = process.tauTable.variables
    tau_vars.dxyErr = var_f10("dxy_error", doc="dxy error")
    tau_vars.dzErr = var_f10(
        "?leadChargedHadrCand.isNonnull() && leadChargedHadrCand.hasTrackDetails() ? leadChargedHadrCand.dzError() : 1000.0",  # noqa
        doc="dz error",
        **({"lazyEval": True} if cmssw_version >= (14, 0, 0) else {}),
    )
    tau_vars.ip3d = var_f10("ip3d", doc="3D impact parameter")
    tau_vars.ip3dErr = var_f10("ip3d_error", doc="3D impact parameter error")
    tau_vars.hasSV = var_b("hasSecondaryVertex", doc="has secondary vertex")
    tau_vars.flightLengthX = var_f10("flightLength().x()", doc="flight length x")
    tau_vars.flightLengthY = var_f10("flightLength().y()", doc="flight length y")
    tau_vars.flightLengthZ = var_f10("flightLength().z()", doc="flight length z")
    tau_vars.flightLengthSig = var_f10("flightLengthSig()", doc="flight length significance")  # noqa
    tau_vars.leadTkNormChi2 = var_f10("leadingTrackNormChi2()", doc="normalized chi2 of the leading track")  # noqa
    tau_vars.leadChCandEtaAtEcalEntrance = var_f10("etaAtEcalEntranceLeadChargedCand", doc="eta of the leading charged candidate at the entrance of the ECAL")  # noqa

    # lifetime variables (only available above 14_0_X)
    if cmssw_version >= (14, 0, 0):
        from PhysicsTools.NanoAOD.leptonTimeLifeInfo_common_cff import addTrackVarsToTimeLifeInfo  # type: ignore[import-not-found] # noqa
        addTrackVarsToTimeLifeInfo(process)

    return process


def add_met_variables(process, run: Run, nano_version: NanoVersion):
    """
    Adds additional (Puppi)MET variables.
    """
    puppimet_vars = getattr(getattr(process, "puppiMetTable", None), "variables", None)
    if puppimet_vars is None:
        print("no puppiMetTable found, skip adding additional variables")
        return process

    puppimet_vars.covXX = var_f8(
        "getSignificanceMatrix().At(0,0)",
        doc="xx element of met covariance matrix",
    )
    puppimet_vars.covXY = var_f8(
        "getSignificanceMatrix().At(0,1)",
        doc="xy element of met covariance matrix",
    )
    puppimet_vars.covYY = var_f8(
        "getSignificanceMatrix().At(1,1)",
        doc="yy element of met covariance matrix",
    )

    return process


def add_l1t_objects(process):
    # see https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/l1trig_cff.py#L181
    from PhysicsTools.NanoAOD.nano_cff import nanoL1TrigObjCustomize  # type: ignore[import-not-found] # noqa
    process = nanoL1TrigObjCustomize(process)
    # lower some cuts
    process.l1EGTable.cut = "pt>=10"
    process.l1TauTable.cut = "pt>=20"
    process.l1JetTable.cut = "pt>=20"
    process.l1MuTable.cut = "pt>=0"  # && hwQual>=8"
    process.l1EtSumTable.cut = "(getType==8 || getType==1 || getType==2 || getType==3 || getType==21)"  # noqa

    return process


def add_pf_candidates(
    process,
    run: Run,
    nano_version: NanoVersion,
    *,
    collection_name: str = "PFCandidate",
    candidate_src: str = "packedPFCandidates",
    puppi_candidates: bool = False,
    jet_src: str = "linkedObjects:jets",
    fat_jet_src: str = "finalJetsAK8",
    tau_src: str = "linkedObjects:taus",
    boosted_tau_src: str = "linkedObjects:boostedTaus",
):
    # add candidate indexes to jets and taus their are contained in
    process.load("NanoGen.NanoGen.pfCandidateIndexer_cfi")
    process.pfCandidateIndexer.candidateCollection = cms.InputTag(candidate_src)
    process.pfCandidateIndexer.jetCollection = cms.InputTag(jet_src)
    process.pfCandidateIndexer.jetIndicesName = cms.string("jet")
    process.pfCandidateIndexer.fatJetCollection = cms.InputTag(fat_jet_src)
    process.pfCandidateIndexer.fatJetIndicesName = cms.string("fatjet")
    process.pfCandidateIndexer.tauCollection = cms.InputTag(tau_src)
    process.pfCandidateIndexer.tauIndicesName = cms.string("tau")
    process.pfCandidateIndexer.boostedTauCollection = cms.InputTag(boosted_tau_src)
    process.pfCandidateIndexer.boostedTauIndicesName = cms.string("boostedtau")
    process.pfCandidateIndexer.containedCandidatesName = cms.string("containedPFCandidates")
    process.nanoTableTaskCommon.add(process.pfCandidateIndexer)
    new_candidate_src = "pfCandidateIndexer:containedPFCandidates"

    # add the nano index table
    process.load("NanoGen.NanoGen.pfCandidateIndicesTable_cfi")
    process.pfCandidateIndicesTable.tableName = cms.string(f"{collection_name}Indices")
    process.pfCandidateIndicesTable.candidateCollection = cms.InputTag(new_candidate_src)
    process.pfCandidateIndicesTable.jetIndicesCollection = cms.InputTag("pfCandidateIndexer:jet")
    process.pfCandidateIndicesTable.fatJetIndicesCollection = cms.InputTag("pfCandidateIndexer:fatjet")  # noqa
    process.pfCandidateIndicesTable.tauIndicesCollection = cms.InputTag("pfCandidateIndexer:tau")
    process.pfCandidateIndicesTable.boostedTauIndicesCollection = cms.InputTag("pfCandidateIndexer:boostedtau")  # noqa
    process.nanoTableTaskCommon.add(process.pfCandidateIndicesTable)

    # define variables in a dict
    variables = dict(
        pt=var_f8("pt"),
        eta=var_f8("eta"),
        phi=var_f8("phi"),
        mass=var_f8("mass"),
        pdgId=var_i32("pdgId"),
        charge=var_i32("charge"),
        dxy=var_f8("dxy"),
        dz=var_f8("dz"),
    )
    if puppi_candidates:
        variables["puppiWeight"] = var_f8("puppiWeight")

    # create the table and add it to the common nano sequence
    if cmssw_version >= (14, 0, 0):
        # use the pat candidate specific table producer that exists since 14_0_0
        from PhysicsTools.NanoAOD.simplePATCandidateFlatTableProducer_cfi import simplePATCandidateFlatTableProducer as candidateTableProducer  # type: ignore[import-not-found] # noqa
    else:
        # fall back to the generic candidate table producer
        from PhysicsTools.NanoAOD.simpleCandidateFlatTableProducer_cfi import simpleCandidateFlatTableProducer as candidateTableProducer # type: ignore[import-not-found] # noqa

    process.pfCandidateTable = candidateTableProducer.clone(
        name=cms.string(collection_name),
        src=cms.InputTag(new_candidate_src),
        doc=cms.string(f"interesting {candidate_src}"),
        variables=cms.PSet(**variables),
    )
    process.nanoTableTaskCommon.add(process.pfCandidateTable)

    return process