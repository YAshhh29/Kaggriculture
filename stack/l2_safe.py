"""L inside the outermost safety layer (stack/safety.py). Must play exactly like L."""
from stack.candidate_l import l_stack
from stack.safety import sf_wrap


def build():
    return sf_wrap(l_stack(), name="L+safety")
