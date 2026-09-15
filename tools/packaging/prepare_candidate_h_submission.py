"""Package Candidate H: a public route-replay agent, kept intact and credited.

Candidate H is deliberately not our own design. It is one of the public
Kaggriculture agents built on the shared route-replay chassis, submitted
unchanged so that it can be measured against Candidate G on the ladder.
Those notebooks are released under the Apache License 2.0, which allows this
provided the license text and notices travel with the work and changes are
stated. So this script:

* copies every file of the chosen submission archive, byte for byte;
* keeps any LICENSE and NOTICE files the archive carries, and writes the
  Apache 2.0 attribution notice into submissions/candidate-h/NOTICE naming
  the source notebook and stating that the files are unmodified;
* checks the package imports with the repository off the path, exposes
  agent(), and plays a full game from each seat against Candidate G;
* records hashes in a manifest.

    python -m tools.packaging.prepare_candidate_h_submission \\
        --archive PATH/TO/submission.tar.gz --source OWNER/NOTEBOOK-SLUG
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "submissions" / "candidate-h"

NOTICE = """Candidate H

The files in this directory, other than this NOTICE and manifest.json, are
the unmodified contents of the submission archive published with the Kaggle
notebook:

    https://www.kaggle.com/code/{source}

That work is licensed under the Apache License, Version 2.0. Any LICENSE and
NOTICE files it carried are included here unchanged, and the license text is
available at https://www.apache.org/licenses/LICENSE-2.0. No changes have been
made to the agent's code or data. Credit for the agent and for the public
work it builds on belongs to its authors, as recorded in their notices.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unpack(archive: Path) -> list[str]:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    names = []
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            name = member.name.lstrip("./")
            if name.startswith("/") or ".." in Path(name).parts:
                raise SystemExit(f"refusing unsafe path in archive: {member.name}")
            if "__pycache__" in Path(name).parts:
                continue
            target = OUT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            names.append(name)
    if "main.py" not in names:
        raise SystemExit("archive has no top-level main.py")
    return sorted(names)


def check(out: Path = OUT) -> dict:
    """Import from the package directory alone and play both seats vs G."""
    from kaggle_environments import make

    results = {}
    saved_path = list(sys.path)
    try:
        sys.path = [str(out)] + [p for p in saved_path
                                 if Path(p).resolve() != ROOT.resolve()]
        spec = importlib.util.spec_from_file_location("candidate_h_main",
                                                      out / "main.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path = saved_path
    agent = getattr(module, "agent", None)
    if not callable(agent):
        raise SystemExit("main.py does not expose a callable agent()")
    results["exposes_agent"] = True

    sys.path.insert(0, str(ROOT))
    import rl.candidate_g as G

    for seat in (0, 1):
        agents = [agent, G.agent] if seat == 0 else [G.agent, agent]
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": 31 + seat,
                                  "runTimeout": 36000, "actTimeout": 60},
                   debug=False)
        env.run(agents)
        statuses = [s.status for s in env.state]
        h, g = env.state[seat].reward, env.state[1 - seat].reward
        results[f"seat_{seat}"] = {"status": statuses, "H": h, "G": g}
        print(f"  seat {seat}: status {statuses}  H {h:,.0f}  G {g:,.0f}")
        if any(s != "DONE" for s in statuses):
            raise SystemExit(f"game in seat {seat} did not finish cleanly")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--source", required=True,
                        help="OWNER/NOTEBOOK-SLUG of the Kaggle notebook")
    args = parser.parse_args()

    archive = Path(args.archive)
    names = unpack(archive)
    (OUT / "NOTICE").write_text(NOTICE.format(source=args.source),
                                encoding="utf-8")
    licenses = [n for n in names if "LICENSE" in n.upper() or "NOTICE" in n.upper()]
    # Most of these archives carry only main.py, with the Apache notices kept
    # inside the source. The license text itself has to travel with the work,
    # so it is supplied from the copy kept beside this script.
    if not any("LICENSE" in n.upper() for n in names):
        shutil.copyfile(Path(__file__).with_name("APACHE-2.0.txt"),
                        OUT / "LICENSE")
    print(f"unpacked {len(names)} files from {archive.name}; license/notice files: "
          f"{licenses or 'none in archive'}")
    results = check()
    manifest = {
        "candidate": "H",
        "source_notebook": args.source,
        "archive": archive.name,
        "archive_sha256": sha256(archive),
        "files": {n: sha256(OUT / n) for n in names},
        "license": "Apache-2.0 (upstream); files unmodified",
        "checks": results,
        "packaged": time.strftime("%Y-%m-%d %H:%M"),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                       encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} (main.py sha {manifest['files']['main.py'][:12]})")


if __name__ == "__main__":
    main()
