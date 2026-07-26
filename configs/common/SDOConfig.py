"""Shared, fail-closed configuration helpers for SDO."""


# These are non-mechanism controls from the successful HPCA27
# sparespec-stt checkpoint run.  They are applied only when the dedicated
# performance-parity profile is explicitly requested; the historical SDO
# defaults remain available for reference/reproduction runs.
HPCA27_CPU_PARITY = {
    "cacheStorePorts": 200,
    "cacheValidationPorts": 200,
    "fetchWidth": 8,
    "fetchBufferSize": 64,
    "fetchQueueSize": 32,
    "decodeWidth": 8,
    "renameWidth": 8,
    "dispatchWidth": 8,
    "issueWidth": 8,
    "wbWidth": 8,
    "commitWidth": 8,
    "squashWidth": 8,
    "LQEntries": 32,
    "SQEntries": 32,
    "numPhysIntRegs": 256,
    "numPhysFloatRegs": 256,
    "numPhysVecRegs": 256,
    "numPhysCCRegs": 1280,
    "numIQEntries": 64,
    "numROBEntries": 192,
}


HPCA27_BRANCH_PREDICTOR_PARITY = {
    "BTBEntries": 4096,
    "BTBTagSize": 16,
    "RASSize": 16,
    "instShiftAmt": 2,
    "localPredictorSize": 2048,
    "localCtrBits": 2,
    "localHistoryTableSize": 2048,
    "globalPredictorSize": 8192,
    "globalCtrBits": 2,
    "choicePredictorSize": 8192,
    "choiceCtrBits": 2,
}


HPCA27_INDIRECT_PREDICTOR_PARITY = {
    "indirectHashGHR": True,
    "indirectHashTargets": True,
    "indirectSets": 256,
    "indirectWays": 2,
    "indirectTagSize": 16,
    "indirectPathLength": 3,
    "indirectGHRBits": 13,
    "instShiftAmt": 2,
}


HPCA27_OPTION_PARITY = {
    "scheme": "SDO",
    "mem_model": "RC",
    "threat_model": "Futuristic",
    "STT": 1,
    "impChannel": 1,
    "ifPrintROB": 0,
    "moreTransTypes": 0,
    "ruby_enable_resource_stall": 0,
    "ruby_sequencer_hit_latency": 1,
    "llc_data_array_banks": 1,
    "llc_tag_array_banks": 1,
    "llc_data_access_latency": 1,
    "llc_tag_access_latency": 1,
    "llc_data_issue_interval": 0,
    "llc_tag_issue_interval": 0,
    "ports": 4,
    "num_cpus": 1,
    "num_l2caches": 1,
    "num_dirs": 1,
    "mesh_rows": 1,
    "cacheline_size": 64,
    "l1d_size": "64kB",
    "l1i_size": "32kB",
    "l2_size": "2MB",
    "l1d_assoc": 8,
    "l1i_assoc": 4,
    "l2_assoc": 16,
    "mem_size": "8GB",
    "network": "simple",
    "topology": "Mesh_XY",
    "ruby": True,
    "cpu_type": "DerivO3CPU",
    "bp_type": None,
    "indirect_bp_type": "SimpleIndirectPredictor",
    "sys_clock": "1GHz",
    "cpu_clock": "2GHz",
    "ruby_clock": "2GHz",
    "mem_type": "DDR3_1600_8x8",
    "mem_channels": 1,
    "MSHR_size": 16,
    "maxinsts": 500000000,
}


def is_sdo_enabled(options):
    """Return true only for the exact, explicitly selected SDO scheme."""

    return getattr(options, "scheme", None) == "SDO"


def hpca27_parity_enabled(options):
    """Return whether the explicit sparespec-stt parity profile is selected."""

    return bool(getattr(options, "hpca27_performance_parity", False))


def validate_hpca27_parity_options(options):
    """Fail closed if a parity-profile run drifts from reviewed controls."""

    if not hpca27_parity_enabled(options):
        return

    mismatches = []
    for name, expected in HPCA27_OPTION_PARITY.items():
        actual = getattr(options, name, None)
        if actual != expected:
            mismatches.append(
                "{}={!r} (expected {!r})".format(name, actual, expected)
            )
    if mismatches:
        raise ValueError(
            "HPCA27 sparespec-stt parity profile mismatch: "
            + ", ".join(sorted(mismatches))
        )


def configure_hpca27_parity_cpu(cpu_list, options):
    """Apply reviewed O3 non-mechanism controls to the measured CPU(s)."""

    if not hpca27_parity_enabled(options):
        return
    validate_hpca27_parity_options(options)
    for cpu in cpu_list:
        for name, value in HPCA27_CPU_PARITY.items():
            setattr(cpu, name, value)
    configure_hpca27_parity_branch_predictor(cpu_list, options)


def configure_hpca27_parity_branch_predictor(cpu_list, options):
    """Bind the target's nested predictor schema to reviewed reference values."""

    if not hpca27_parity_enabled(options):
        return
    validate_hpca27_parity_options(options)
    for cpu in cpu_list:
        branch_pred = getattr(cpu, "branchPred", None)
        if branch_pred is None or \
                getattr(branch_pred, "type", None) != "TournamentBP":
            raise ValueError(
                "HPCA27 parity requires a TournamentBP branch predictor"
            )
        for name, value in HPCA27_BRANCH_PREDICTOR_PARITY.items():
            setattr(branch_pred, name, value)

        indirect_pred = getattr(branch_pred, "indirectBranchPred", None)
        if indirect_pred is None or \
                getattr(indirect_pred, "type", None) != \
                "SimpleIndirectPredictor":
            raise ValueError(
                "HPCA27 parity requires a nested "
                "SimpleIndirectPredictor"
            )
        for name, value in HPCA27_INDIRECT_PREDICTOR_PARITY.items():
            setattr(indirect_pred, name, value)
