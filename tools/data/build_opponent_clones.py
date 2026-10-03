"""Extract every corpus opponent's real action sequence as an opponent tape.

Reuses the exact convention already established in kaggle_cache/clones/
(verified against the existing files: clone["actions"][k] ==
replay["steps"][k][opponent_side]["action"] for k in 0..719, no offset).
Extends that library from the original 56 broad-gate opponents to the
full 245-episode corpus so local head-to-head testing (rl/replay_agent.py
+ benchmark.run_game) can draw on the whole cache, not just the panel.

Output: kaggle_cache/clones/opp_<episode_id>.json (git-ignored, matches
the existing file naming and schema exactly: actions_zlib_b64,
source_team, source_episode_id).
"""

from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path
from typing import Any

from rl.replay_dataset import _validate_replay


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "kaggle_cache"
CLONES_DIR = CACHE_DIR / "clones"
OUR_TEAM_NAME = "YASH JAIN"


def _resolve_sides(replay: dict[str, Any]) -> tuple[int, int]:
    agents = replay.get("info", {}).get("Agents", [])
    names = [str(agent.get("Name", "")) for agent in agents]
    ours = [
        i for i, name in enumerate(names)
        if name.casefold() == OUR_TEAM_NAME.casefold()
    ]
    if len(ours) != 1:
        raise ValueError(
            f"Expected exactly one {OUR_TEAM_NAME!r} side, found {len(ours)}"
        )
    our_side = ours[0]
    return our_side, 1 - our_side


def extract_clone(replay: dict[str, Any]) -> dict[str, Any]:
    episode_id, _seed, _rewards, steps = _validate_replay(
        replay, expected_records=720
    )
    _our_side, opp_side = _resolve_sides(replay)
    opponent_name = str(replay["info"]["Agents"][opp_side].get("Name", ""))
    actions = [step[opp_side].get("action") for step in steps]
    compressed = zlib.compress(
        json.dumps(actions, separators=(",", ":")).encode("utf-8"),
        level=9,
    )
    return {
        "actions_zlib_b64": base64.b64encode(compressed).decode("ascii"),
        "source_team": opponent_name,
        "source_episode_id": episode_id,
    }


def build_all_clones(
    cache_dir: Path = CACHE_DIR,
    clones_dir: Path = CLONES_DIR,
) -> tuple[list[int], list[str]]:
    clones_dir.mkdir(parents=True, exist_ok=True)
    written: list[int] = []
    skipped: list[str] = []
    for path in sorted(cache_dir.glob("episode-*-replay.json")):
        try:
            replay = json.loads(path.read_bytes())
            clone = extract_clone(replay)
        except (ValueError, KeyError, TypeError) as exc:
            skipped.append(f"{path.name}: {exc}")
            continue
        output = clones_dir / f"opp_{clone['source_episode_id']}.json"
        output.write_text(
            json.dumps(clone, separators=(",", ":")),
            encoding="utf-8",
        )
        written.append(clone["source_episode_id"])
    return written, skipped


def main() -> None:
    written, skipped = build_all_clones()
    print(f"Clones written: {len(written)}")
    print(f"Skipped: {len(skipped)}")
    for reason in skipped:
        print(f"  - {reason}")


if __name__ == "__main__":
    main()
