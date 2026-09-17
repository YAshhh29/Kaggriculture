"""Agent G with constants overridden from an environment variable.

Local evaluation only: lets the head-to-head harness sweep G's portfolio
against a live opponent without a module per variant.

    G_SET='{"HERD_TARGET": 17}' python -m tools.eval.head_to_head \
        rl.g_variant:agent --reference rl.candidate_h2_package:agent
"""

import json
import os

import rl.candidate_g as G

for _key, _value in json.loads(os.environ.get("G_SET", "{}")).items():
    setattr(G, _key, _value)

agent = G.agent
