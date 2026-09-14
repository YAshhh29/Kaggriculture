"""Build Candidate H: a route-replay farming base with our market-demand layer.

Candidate H has two parts. The farming base -- what to plant, raise and
harvest, day by day -- is a route-replay agent published on Kaggle under the
Apache License 2.0. On top of it sits Candidate H's own market-demand layer
(rl/candidate_h_demand.py), which re-decides the base's sale orders from a
model of the town's consumption and the market's price curves.

The build appends the demand layer to the base source, runs it in its own
namespace so none of its names can collide with the base's, and wraps the
base's final agent(). The base's code is not otherwise changed. As the
license requires, its notices stay in main.py, the Apache 2.0 text ships as
LICENSE, and NOTICE records the source and the modification.

    python -m tools.packaging.build_candidate_h \\
        --base PATH/TO/base/main.py --source OWNER/NOTEBOOK-SLUG \\
        [--set horizon=24 --set rival_share=0.5 ...]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.packaging.prepare_candidate_h_submission import (  # noqa: E402
    OUT, check, sha256)

LAYER = ROOT / "rl" / "candidate_h_demand.py"

NOTICE = """Candidate H

main.py combines two parts.

1. A route-replay farming base, published with the Kaggle notebook
   https://www.kaggle.com/code/{source}
   and licensed under the Apache License, Version 2.0. Its own copyright
   and attribution notices are retained in main.py. The license text is
   provided in LICENSE.

2. Candidate H's market-demand layer, appended at the end of main.py
   (section "Candidate H market-demand layer"). It re-decides the base's
   SELL orders from a forecast of town consumption and the market price
   curves.

Modification to the base: the demand layer is appended and wraps the
base's final agent(); the base's code is otherwise unchanged.
"""


def compose(base_source: str, layer_source: str, settings: dict) -> str:
    layer = "\n".join(line for line in layer_source.splitlines()
                      if line.strip() != "from __future__ import annotations")
    return (
        base_source.rstrip("\n")
        + "\n\n\n# " + "=" * 74
        + "\n# Candidate H market-demand layer\n# " + "=" * 74 + "\n"
        + "_CANDIDATE_H_LAYER_SOURCE = " + repr(layer) + "\n"
        + "_CANDIDATE_H_LAYER = {'__name__': 'candidate_h_demand'}\n"
        + "exec(compile(_CANDIDATE_H_LAYER_SOURCE, 'candidate_h_demand', "
          "'exec'), _CANDIDATE_H_LAYER)\n"
        + f"_CANDIDATE_H_SETTINGS = {settings!r}\n"
        + "agent = _CANDIDATE_H_LAYER['wrap'](globals().pop('agent'), "
          "_CANDIDATE_H_SETTINGS)\n"
    )


def _parse(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--set", action="append", default=[])
    args = parser.parse_args()

    settings = {}
    for item in args.set:
        key, _, raw = item.partition("=")
        settings[key] = _parse(raw)

    base = Path(args.base)
    source = compose(base.read_text(encoding="utf-8"),
                     LAYER.read_text(encoding="utf-8"), settings)
    compile(source, "main.py", "exec")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "main.py").write_text(source, encoding="utf-8")
    shutil.copyfile(ROOT / "tools" / "packaging" / "APACHE-2.0.txt",
                    OUT / "LICENSE")
    (OUT / "NOTICE").write_text(NOTICE.format(source=args.source),
                                encoding="utf-8")

    results = check()
    shutil.rmtree(OUT / "__pycache__", ignore_errors=True)
    manifest = {
        "candidate": "H",
        "base_source_notebook": args.source,
        "base_sha256": sha256(base),
        "demand_layer_sha256": sha256(LAYER),
        "demand_settings": settings,
        "main_sha256": sha256(OUT / "main.py"),
        "license": "Apache-2.0 base with notices retained; demand layer appended",
        "checks": results,
        "built": time.strftime("%Y-%m-%d %H:%M"),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                       encoding="utf-8")
    print(f"built {OUT.relative_to(ROOT)} (main.py sha "
          f"{manifest['main_sha256'][:12]})")


if __name__ == "__main__":
    main()
