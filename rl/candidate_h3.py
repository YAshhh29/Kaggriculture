"""Candidate H3: H2's base with our demand layer, plus order sequencing.

Local evaluation module. The base and the layer are exactly H2's; the only
difference is that the layer now emits sales before purchases, which the
engine rewards because it walks both players' orders by index and aborts an
order whose unit fails on cash or shed room.
"""

import importlib.util
from pathlib import Path

_PATH = (Path(__file__).resolve().parents[1] / "submissions"
         / "candidate-h2" / "main.py")
_spec = importlib.util.spec_from_file_location("h2_base_for_h3", _PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

_packaged = _module.agent
_base = next(cell.cell_contents for cell in (_packaged.__closure__ or ())
             if callable(cell.cell_contents) and cell.cell_contents is not _packaged)

from rl.candidate_h_demand import wrap  # noqa: E402

_settings = dict(getattr(_packaged, "demand_settings", {}) or {})
_settings["sequence_orders"] = True
agent = wrap(_base, _settings)
