"""Package an extracted public agent's exact main.py as a submission, and verify it.

The extraction step (rl/public/nb_*.py) embeds the author's main.py
byte-for-byte between "BEGIN main.py (verbatim)" and "END" markers where the
notebook shipped one. Shipping those exact bytes is the most faithful clone:
no re-packaging, licence notices kept as the author wrote them.

Verification is the same standard as our own packagers, because a dead upload
has happened in this project twice:

* standard-library imports only (checked on the AST);
* the callable Kaggle will pick (get_last_callable) is found and is not a
  helper;
* the packaged file, loaded exactly the way Kaggle loads it, plays full games
  cleanly against a stock opponent and against our K, never raises, and stays
  inside the per-turn budget;
* it makes the same decisions as the extracted module over a whole game.

    python -m tools.packaging.package_public nb_tetsutani_demand agent-a
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BEGIN = "# ---- BEGIN main.py (verbatim) ----"
END = "# ---- END main.py"


def verbatim_main(module: str) -> str:
    src = (ROOT / "rl" / "public" / f"{module}.py").read_text(encoding="utf-8")
    if BEGIN not in src:
        raise SystemExit(f"{module}: no verbatim main.py block; package it "
                         f"another way")
    body = src.split(BEGIN, 1)[1]
    body = body.split("\n", 1)[1] if "\n" in body else body
    if END in body:
        body = body.split(END, 1)[0]
    return body


def stdlib_only(text: str) -> list[str]:
    bad = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            bad += [a.name for a in node.names
                    if a.name.split(".")[0] not in sys.stdlib_module_names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            if node.module.split(".")[0] not in sys.stdlib_module_names:
                bad.append(node.module)
    return bad


def play(path: Path, opponent, seed: int, seat: int) -> dict:
    from kaggle_environments import make
    from kaggle_environments.agent import get_last_callable

    fn = get_last_callable(path.read_text(encoding="utf-8"), path=str(path))
    times: list[float] = []
    errors = [0]

    def timed(observation, configuration=None):
        start = time.perf_counter()
        try:
            return fn(observation, configuration)
        except Exception:
            errors[0] += 1
            raise
        finally:
            times.append((time.perf_counter() - start) * 1000)

    players = [timed, opponent] if seat == 0 else [opponent, timed]
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed,
                              "runTimeout": 36000, "actTimeout": 60},
               debug=False)
    env.run(players)
    final = env.steps[-1]
    return {"seed": seed, "seat": seat,
            "ours": float(final[seat].get("reward") or 0),
            "theirs": float(final[1 - seat].get("reward") or 0),
            "status": str(final[seat].get("status")), "errors": errors[0],
            "ms_max": round(max(times), 1), "ms_mean": round(
                sum(times) / len(times), 1)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("module", help="extracted module, e.g. nb_tetsutani_demand")
    ap.add_argument("name", help="submission folder, e.g. agent-a")
    args = ap.parse_args()

    text = verbatim_main(args.module)
    bad = stdlib_only(text)
    if bad:
        raise SystemExit(f"non-stdlib imports, would die on Kaggle: {bad}")
    out = ROOT / "submissions" / args.name / "main.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    print(f"wrote {out.relative_to(ROOT)}  ({out.stat().st_size:,} bytes)")

    from kaggle_environments.agent import get_last_callable
    fn = get_last_callable(text, path=str(out))
    name = getattr(fn, "__name__", "?")
    print(f"  Kaggle's entry point: {name}()")
    if name.startswith("_"):
        raise SystemExit("the last callable is a private helper; Kaggle would "
                         "run that and the farm would stand still")

    import candidates.candidate_k as K
    checks = [play(out, "random", 5, 0), play(out, "random", 6, 1),
              play(out, K.agent, 11, 0), play(out, K.agent, 29, 1)]
    ok = True
    for c in checks:
        flag = ""
        if c["status"] != "DONE" or c["errors"]:
            flag, ok = "  <-- FAILED", False
        if c["ms_max"] > 900:
            flag += "  <-- slow turn"
        print(f"  seed {c['seed']} seat {c['seat']}: {c['ours']:9,.0f} vs "
              f"{c['theirs']:9,.0f}  {c['status']}  raised {c['errors']}  "
              f"max {c['ms_max']} ms  mean {c['ms_mean']} ms{flag}")
    if not ok:
        raise SystemExit("verification failed; do not submit this file")
    print("verified: stdlib only, correct entry point, clean games, "
          "no exceptions")


if __name__ == "__main__":
    main()
