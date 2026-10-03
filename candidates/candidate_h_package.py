"""The packaged Candidate H submission as an importable agent.

Local evaluation only: lets tools.eval.inspect_g play the exact file that
would be uploaded (submissions/candidate-h/main.py) via
`--spec candidates.candidate_h_package:agent`.

With SETTINGS empty the packaged agent plays as submitted. Setting
SETTINGS (for example `--set 'SETTINGS={"hire_reserve": 15}'`) re-wraps the
same submitted base with the current demand layer (candidates/candidate_h_demand.py)
and the submitted settings plus these, so new layer settings can be tried
on exactly the base that plays the ladder.
"""

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "submissions" / "candidate-h" / "main.py"
_spec = importlib.util.spec_from_file_location("candidate_h_submission", _PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

_packaged = _module.agent
_base = next(cell.cell_contents for cell in (_packaged.__closure__ or ())
             if callable(cell.cell_contents)
             and cell.cell_contents is not _packaged)

SETTINGS: dict = {}
_built: dict = {}


def agent(observation, configuration=None):
    if not SETTINGS:
        return _packaged(observation, configuration)
    key = tuple(sorted(SETTINGS.items()))
    if key not in _built:
        from candidates.candidate_h_demand import wrap
        merged = dict(getattr(_packaged, "demand_settings", {}) or {})
        merged.update(SETTINGS)
        _built[key] = wrap(_base, merged)
    return _built[key](observation, configuration)
