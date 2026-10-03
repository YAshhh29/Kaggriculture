"""H2 with its demand tolerance overridden from an environment variable."""
import importlib.util, json, os
from pathlib import Path

_PATH = (Path(__file__).resolve().parents[1] / "submissions"
         / "candidate-h2" / "main.py")
_spec = importlib.util.spec_from_file_location("h2_base_tol", _PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_packaged = _module.agent
_base = next(c.cell_contents for c in (_packaged.__closure__ or ())
             if callable(c.cell_contents) and c.cell_contents is not _packaged)

from candidates.candidate_h_demand import wrap  # noqa: E402

_settings = dict(getattr(_packaged, "demand_settings", {}) or {})
_settings.update(json.loads(os.environ.get("H_SET", "{}")))
agent = wrap(_base, _settings)
