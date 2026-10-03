"""Agent G with constants overridden from an environment variable.

Local evaluation only: lets the head-to-head harness sweep G's portfolio
against a live opponent without a module per variant.

    G_SET='{"HERD_TARGET": 17}' python -m tools.eval.head_to_head \
        candidates.g_variant:agent --reference candidates.candidate_h2_package:agent
"""

import json
import os

import candidates.candidate_g as G

for _key, _value in json.loads(os.environ.get("G_SET", "{}")).items():
    setattr(G, _key, _value)

agent = G.agent
