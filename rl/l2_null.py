"""Null L2 candidate: exactly Agent L. Used to check the paired harness (L vs L must be all draws)."""
from rl.candidate_l import l_stack


def build():
    return l_stack()
