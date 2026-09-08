"""Turn a captured live tape into a verified route model.

`kaggle_cache/live_clones/live_<episode>.json` is the compact form
`tools.data.fetch_live_opponents` writes: the 720 actions of one side and
nothing else. The distilled route agents in `agents/` expect the richer
`models/` schema instead -- provenance, record count, and two hashes that
the packagers re-check before a submission is built.

This converts one into the other, so a route found by screening the live
corpus can be shipped through exactly the same verified path as the routes
that came out of `kaggle_cache/clones/`.

    python -m tools.data.build_route_model \\
        kaggle_cache/live_clones/live_106610780.json \\
        --out models/v1327-live-elite-mhuang-106610780.json
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "rl" / "data" / "live_opponents.jsonl"
MODEL_TYPE = "public_calendar_behavior_clone"
SIMULATOR_VERSION = "1.32.7"


def provenance(episode_id: str) -> dict[str, Any]:
    """What the live index recorded about this episode, if anything."""
    if not INDEX.exists():
        return {}
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if str(row.get("episode_id")) == str(episode_id):
            return row
    return {}


def build(tape_path: Path) -> dict[str, Any]:
    tape = json.loads(tape_path.read_text(encoding="utf-8"))
    actions = json.loads(
        zlib.decompress(
            base64.b64decode(str(tape["actions_zlib_b64"]))
        ).decode("utf-8")
    )
    if not isinstance(actions, list) or len(actions) != 720:
        raise ValueError(f"{tape_path} must hold 720 action records")

    episode = str(tape.get("source_episode_id", ""))
    row = provenance(episode)
    raw = json.dumps(actions, separators=(",", ":")).encode("utf-8")
    return {
        "model_type": MODEL_TYPE,
        "simulator_version": SIMULATOR_VERSION,
        "source_episode_id": int(episode) if episode.isdigit() else episode,
        "source_team": tape.get("source_team"),
        "source_team_rating": row.get("rating"),
        "source_reward": row.get("reward"),
        "source_leaderboard_context": (
            "captured from the live ladder by "
            "tools.data.fetch_live_opponents"
        ),
        "records": len(actions),
        "actions_sha256": hashlib.sha256(raw).hexdigest(),
        "actions_zlib_b64": base64.b64encode(
            zlib.compress(raw, 9)
        ).decode("ascii"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tape", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    model = build(args.tape)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(model, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.out} from episode {model['source_episode_id']} "
          f"({model['source_team']}, rated "
          f"{model.get('source_team_rating')})")


if __name__ == "__main__":
    main()
