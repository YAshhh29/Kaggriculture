"""L inside the outermost safety layer (rl/safety.py). Must play exactly like L."""
from rl.candidate_l import l_stack
from rl.safety import sf_wrap


def build():
    return sf_wrap(l_stack(), name="L+safety")
