"""Ablations of the shipped L2 stack: each factory drops one layer."""
from rl.l2_combo import SHIP, combo


def _without(name):
    return combo(*[n for n in SHIP if n != name])


def no_shadow(): return _without("shadow")
def no_rt(): return _without("rt")
def no_lot(): return _without("lot")
def no_fert(): return _without("fert")
def no_feed(): return _without("feed")
def no_labour(): return _without("labour")


# Ablations of L3 (the shipped L2 stack with the library shadow).
def _lib_without(name):
    from rl.l2_shadow import SH_LIBRARY
    return combo(*[n for n in SHIP if n != name], shadow_programs=SH_LIBRARY)


def l3_no_rt(): return _lib_without("rt")
def l3_no_lot(): return _lib_without("lot")
def l3_no_feed(): return _lib_without("feed")
def l3_no_labour(): return _lib_without("labour")
def l3_no_shadow(): return _lib_without("shadow")


def l3_orig_gate():
    from rl.l2_shadow import SH_LIBRARY
    return combo(*SHIP, shadow_programs=SH_LIBRARY, gate=None)
