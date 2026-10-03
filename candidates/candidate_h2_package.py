"""The packaged Candidate H2 submission as an importable agent.

Local evaluation only: lets the head-to-head harness play the exact file that
is live on the ladder (submissions/candidate-h2/main.py, the one with the
day-one hire reserve) via `--reference candidates.candidate_h2_package:agent`.
"""

import importlib.util
from pathlib import Path

_PATH = (Path(__file__).resolve().parents[1] / "submissions"
         / "candidate-h2" / "main.py")
_spec = importlib.util.spec_from_file_location("candidate_h2_submission", _PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

agent = _module.agent
