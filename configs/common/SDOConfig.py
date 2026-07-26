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
