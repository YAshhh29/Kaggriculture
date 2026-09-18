"""Agent J with constants overridden from an environment variable, for sweeps.

    J_SET='{"WALK_COST": 2.0}' python -m tools.eval.strong_panel rl.j_variant:agent
"""

import json
import os

import rl.candidate_j as J

for _key, _value in json.loads(os.environ.get("J_SET", "{}")).items():
    setattr(J, _key, _value)

agent = J.agent
