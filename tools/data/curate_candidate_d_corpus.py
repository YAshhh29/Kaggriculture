"""Build Candidate D's first curated corpus index from cached replays.

Scans kaggle_cache/episode-*-replay.json (raw downloads via the Kaggle API,
git-ignored -- see kaggle_cache/pull_and_analyze.py), validates each replay
with the same checks rl/replay_dataset.py uses for training examples, then
writes one deduplicated, team-split index row per usable episode to
rl/data/candidate_d_corpus_index.jsonl.

This is a curation/indexing pass, not a feature-extraction pass: it does not
call encode_state or build per-step (state, action) examples, because that
requires a choice of baseline and Option-level label design Candidate D has
not settled yet (see docs/research/GOAL.md section 10 and the "Candidate D" plan). What
it produces is a queryable manifest -- one row per real game, with opponent
identity, result, quadrant/hand-count outcomes, and a leakage-free
train/validation/test split -- that both (a) is the direct prerequisite for
building the per-step example files once labels are chosen, and (b) is
useful on its own for opponent-archetype analysis (e.g. the land-quadrant
economics question).

Split policy: bucket by sha256(opponent_name.casefold()) mod 10 so every
game against the same opponent lands in the same split (no identity
leakage). Buckets 0-6 -> train, 7-8 -> validation, 9 -> test. This is a
team-split, not a temporal holdout: the cached replays carry no reliable
per-episode timestamp (Kaggle's replay JSON has no CreateTime field), so a
true temporal holdout would require re-querying the episodes API and
cross-referencing by episode ID. Documented as a known v2 gap, not solved
here.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rl.replay_dataset import SIMULATOR_VERSION, _validate_replay


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "kaggle_cache"
OUTPUT = ROOT / "rl" / "data" / "candidate_d_corpus_index.jsonl"
INDEX_SCHEMA_VERSION = 1
OUR_TEAM_NAME = "YASH JAIN"
TRAIN_BUCKETS = frozenset(range(0, 7))
VALIDATION_BUCKETS = frozenset({7, 8})
TEST_BUCKETS = frozenset({9})


def _split_for(opponent_name: str) -> str:
    digest = hashlib.sha256(opponent_name.casefold().encode("utf-8"))
    bucket = digest.digest()[0] % 10
    if bucket in TRAIN_BUCKETS:
        return "train"
    if bucket in VALIDATION_BUCKETS:
        return "validation"
    return "test"


def _resolve_sides(replay: dict[str, Any]) -> tuple[int, int]:
    agents = replay.get("info", {}).get("Agents", [])
    names = [str(agent.get("Name", "")) for agent in agents]
    ours = [i for i, name in enumerate(names) if name.casefold() == OUR_TEAM_NAME.casefold()]
    if len(ours) != 1:
        raise ValueError(f"Expected exactly one {OUR_TEAM_NAME!r} side, found {len(ours)}")
    our_side = ours[0]
    opp_side = 1 - our_side
    return our_side, opp_side


def _final_farm_stats(replay: dict[str, Any], player: int) -> dict[str, Any]:
    last_step = replay["steps"][-1]
    observation = last_step[0].get("observation") or last_step[1].get("observation")
    farms = observation.get("farms", []) if isinstance(observation, dict) else []
    if player >= len(farms) or not isinstance(farms[player], dict):
        return {"hands": None, "money": None, "unlocked_quadrants": None}
    farm = farms[player]
    return {
        "hands": len(farm.get("hands", []) or []),
        "money": farm.get("money"),
        "unlocked_quadrants": list(farm.get("unlocked_quadrants", []) or []),
    }


def _index_row(path: Path) -> dict[str, Any] | None:
    raw = path.read_bytes()
    replay = json.loads(raw)
    try:
        episode_id, seed, rewards, _steps = _validate_replay(replay, expected_records=720)
        our_side, opp_side = _resolve_sides(replay)
    except (ValueError, KeyError, TypeError) as exc:
        return {"excluded": True, "path": path.name, "reason": str(exc)}

    agents = replay["info"]["Agents"]
    opponent_name = str(agents[opp_side].get("Name", ""))
    our_reward, opp_reward = rewards[our_side], rewards[opp_side]
    result = (
        "win" if our_reward > opp_reward
        else "loss" if our_reward < opp_reward
        else "tie"
    )
    return {
        "excluded": False,
        "type": "episode",
        "episode_id": episode_id,
        "seed": seed,
        "replay_sha256": hashlib.sha256(raw).hexdigest(),
        "replay_file": path.name,
        "our_side": our_side,
        "opponent_name": opponent_name,
        "our_reward": our_reward,
        "opponent_reward": opp_reward,
        "result": result,
        "our_final": _final_farm_stats(replay, our_side),
        "opponent_final": _final_farm_stats(replay, opp_side),
        "split": _split_for(opponent_name),
    }


def build_index(cache_dir: Path = CACHE_DIR) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen_episode_ids: set[int] = set()
    seen_hashes: set[str] = set()
    for path in sorted(cache_dir.glob("episode-*-replay.json")):
        row = _index_row(path)
        if row is None:
            continue
        if row["excluded"]:
            excluded.append(row)
            continue
        if row["episode_id"] in seen_episode_ids or row["replay_sha256"] in seen_hashes:
            excluded.append(
                {
                    "excluded": True,
                    "path": path.name,
                    "reason": f"duplicate of episode {row['episode_id']}",
                }
            )
            continue
        seen_episode_ids.add(row["episode_id"])
        seen_hashes.add(row["replay_sha256"])
        included.append(row)
    return included, excluded


def write_index(included: list[dict[str, Any]], output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    split_counts = {"train": 0, "validation": 0, "test": 0}
    opponents_by_split: dict[str, set[str]] = {"train": set(), "validation": set(), "test": set()}
    for row in included:
        split_counts[row["split"]] += 1
        opponents_by_split[row["split"]].add(row["opponent_name"])
    header = {
        "type": "metadata",
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulator_version": SIMULATOR_VERSION,
        "our_team_name": OUR_TEAM_NAME,
        "source": "kaggle_cache/episode-*-replay.json (Kaggle API downloads)",
        "split_policy": (
            "sha256(opponent_name.casefold())[0] % 10; buckets 0-6=train, "
            "7-8=validation, 9=test -- team-split, not temporal"
        ),
        "episodes": len(included),
        "split_counts": split_counts,
        "unique_opponents_by_split": {
            split: len(names) for split, names in opponents_by_split.items()
        },
    }
    rows = [header] + [
        {k: v for k, v in row.items() if k != "excluded"} for row in included
    ]
    output.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> None:
    included, excluded = build_index()
    write_index(included)
    print(f"Scanned: {len(included) + len(excluded)}")
    print(f"Included: {len(included)}")
    print(f"Excluded: {len(excluded)}")
    for row in excluded:
        print(f"  - {row['path']}: {row['reason']}")
    counts = {"train": 0, "validation": 0, "test": 0}
    for row in included:
        counts[row["split"]] += 1
    print(f"Split counts: {counts}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
