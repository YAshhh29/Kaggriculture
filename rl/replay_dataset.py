"""Convert a private local public replay into aligned imitation examples."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any

from agents.experimental_distilled_calendar_agent import decide as calendar
from rl.features import EncodedState, STATE_FEATURE_NAMES, encode_state
from rl.runtime import AgentAction, Baseline, clone_action


SIMULATOR_VERSION = "1.32.7"
DATASET_SCHEMA_VERSION = 1
FEATURE_SCHEMA_VERSION = 1
ACTION_SCHEMA_VERSION = 1
DATASET_SPLITS = frozenset({"train", "validation", "test"})
CROPS = frozenset({"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"})
ANIMALS = frozenset({"GOOSE", "COW", "SHEEP"})
PRODUCTS = frozenset(
    {
        "WHEAT",
        "CARROT",
        "TOMATO",
        "STRAWBERRY",
        "MELON",
        "EGG",
        "MILK",
        "WOOL",
        "FERTILIZER",
    }
)
TRANSPORT_ITEMS = PRODUCTS | ANIMALS
NO_ARGUMENT_UNIT_OPERATIONS = frozenset(
    {
        "NORTH",
        "SOUTH",
        "EAST",
        "WEST",
        "PASS",
        "DROP",
        "WATER",
        "HARVEST",
        "FERTILIZE",
        "BUILD_COOP",
        "BUILD_PASTURE",
        "DIG",
        "FEED",
        "COLLECT_FERTILIZER",
        "CARE",
    }
)
NO_ARGUMENT_MARKET_OPERATIONS = frozenset({"HIRE", "BUY_LAND"})
MARKET_ITEM_DOMAINS = {
    "BUY_SEED": CROPS,
    "BUY_PRODUCT": frozenset({"WHEAT", "FERTILIZER"}),
    "BUY_ANIMAL": ANIMALS,
    "SELL": PRODUCTS,
}


@dataclass(frozen=True)
class ReplayExample:
    episode_id: int
    player: int
    record_index: int
    state: EncodedState
    teacher_action: AgentAction

    def as_json(self) -> dict[str, Any]:
        return {
            "type": "example",
            "episode_id": self.episode_id,
            "player": self.player,
            "record_index": self.record_index,
            "state": list(self.state.values),
            "teacher_action": clone_action(self.teacher_action),
        }


@dataclass(frozen=True)
class ReplayDataset:
    episode_id: int
    seed: int
    source_team: str
    source_player: int
    source_submission_id: int | None
    source_score_snapshot: float | None
    replay_date: str | None
    collected_at: str
    split: str
    simulator_version: str
    replay_sha256: str
    rewards: tuple[float, float]
    examples: tuple[ReplayExample, ...]

    def metadata(self) -> dict[str, Any]:
        return {
            "type": "metadata",
            "dataset_schema_version": DATASET_SCHEMA_VERSION,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "action_schema_version": ACTION_SCHEMA_VERSION,
            "episode_id": self.episode_id,
            "seed": self.seed,
            "source_team": self.source_team,
            "source_player": self.source_player,
            "source_submission_id": self.source_submission_id,
            "source_score_snapshot": self.source_score_snapshot,
            "replay_date": self.replay_date,
            "collected_at": self.collected_at,
            "split": self.split,
            "simulator_version": self.simulator_version,
            "replay_sha256": self.replay_sha256,
            "rewards": list(self.rewards),
            "result": (
                "win"
                if self.rewards[self.source_player]
                > self.rewards[1 - self.source_player]
                else "loss"
                if self.rewards[self.source_player]
                < self.rewards[1 - self.source_player]
                else "tie"
            ),
            "feature_names": list(STATE_FEATURE_NAMES),
            "examples": len(self.examples),
        }


def resolve_player(replay: dict[str, Any], team_name: str) -> int:
    agents = replay.get("info", {}).get("Agents", [])
    matches = [
        player
        for player, agent in enumerate(agents)
        if str(agent.get("Name", "")).casefold() == team_name.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one replay agent named {team_name!r}, "
            f"found {len(matches)}"
        )
    return matches[0]


def _positive_integer(value: Any, context: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{context} quantity must be a positive integer")
    return value


def _validate_unit_action(action: Any, context: str) -> None:
    if not isinstance(action, list) or not action:
        raise ValueError(f"{context} must be a nonempty list")
    operation = action[0]
    if not isinstance(operation, str):
        raise ValueError(f"{context} operation must be a string")
    if operation in NO_ARGUMENT_UNIT_OPERATIONS:
        if len(action) != 1:
            raise ValueError(f"{context} {operation} takes no arguments")
        return
    if operation == "PLANT":
        if len(action) != 2 or action[1] not in CROPS:
            raise ValueError(f"{context} has an invalid PLANT action")
        return
    if operation in {"PICKUP", "PLACE"}:
        if len(action) not in (2, 3) or action[1] not in TRANSPORT_ITEMS:
            raise ValueError(f"{context} has an invalid {operation} action")
        if len(action) == 3:
            _positive_integer(action[2], context)
        return
    raise ValueError(f"{context} has unknown operation {operation!r}")


def _validate_market_order(order: Any, context: str) -> None:
    if not isinstance(order, list) or not order:
        raise ValueError(f"{context} must be a nonempty list")
    operation = order[0]
    if not isinstance(operation, str):
        raise ValueError(f"{context} operation must be a string")
    if operation in NO_ARGUMENT_MARKET_OPERATIONS:
        if len(order) != 1:
            raise ValueError(f"{context} {operation} takes no arguments")
        return
    item_domain = MARKET_ITEM_DOMAINS.get(operation)
    if (
        item_domain is None
        or len(order) != 3
        or order[1] not in item_domain
    ):
        raise ValueError(f"{context} has an invalid {operation} order")
    _positive_integer(order[2], context)


def _require_action(
    value: Any,
    record_index: int,
    expected_hands: int,
) -> AgentAction:
    if not isinstance(value, dict):
        raise ValueError(
            f"Replay record {record_index} has no teacher action"
        )
    if set(value) != {"farmer", "hands", "market"}:
        raise ValueError(
            f"Replay record {record_index} has invalid action fields"
        )
    farmer = value.get("farmer")
    hands = value.get("hands")
    market = value.get("market")
    if not isinstance(hands, list) or len(hands) != expected_hands:
        raise ValueError(
            f"Replay record {record_index} has {len(hands) if isinstance(hands, list) else 0} "
            f"hand actions; expected {expected_hands}"
        )
    if not isinstance(market, list) or len(market) > 10:
        raise ValueError(
            f"Replay record {record_index} has an invalid market action list"
        )
    _validate_unit_action(
        farmer,
        f"Replay record {record_index} farmer action",
    )
    for hand_index, hand_action in enumerate(hands):
        _validate_unit_action(
            hand_action,
            f"Replay record {record_index} hand {hand_index} action",
        )
    for order_index, order in enumerate(market):
        _validate_market_order(
            order,
            f"Replay record {record_index} market order {order_index}",
        )
    return clone_action(value)


def _validate_replay(
    replay: dict[str, Any],
    expected_records: int,
) -> tuple[int, int, tuple[float, float], list[Any]]:
    version = str(replay.get("module_version", ""))
    if version != SIMULATOR_VERSION:
        raise ValueError(f"Unexpected simulator version: {version!r}")
    if replay.get("statuses") != ["DONE", "DONE"]:
        raise ValueError(
            f"Replay did not finish successfully: {replay.get('statuses')!r}"
        )
    rewards_value = replay.get("rewards")
    if not isinstance(rewards_value, list) or len(rewards_value) != 2:
        raise ValueError("Replay must contain two terminal rewards")
    rewards = tuple(float(reward) for reward in rewards_value)
    if not all(isfinite(reward) for reward in rewards):
        raise ValueError("Replay rewards must be finite")
    info = replay.get("info", {})
    episode_id = int(info.get("EpisodeId", -1))
    if episode_id < 0:
        raise ValueError("Replay has no valid episode ID")
    seed = int(info.get("seed", -1))
    if seed < 0:
        raise ValueError("Replay has no valid seed")
    steps = replay.get("steps")
    if not isinstance(steps, list) or len(steps) != expected_records:
        actual = len(steps) if isinstance(steps, list) else 0
        raise ValueError(
            f"Expected {expected_records} replay records, found {actual}"
        )
    for record_index, step in enumerate(steps):
        if not isinstance(step, list) or len(step) != 2:
            raise ValueError(
                f"Replay record {record_index} must contain two players"
            )
        if not all(isinstance(player, dict) for player in step):
            raise ValueError(
                f"Replay record {record_index} has an invalid player state"
            )
    return episode_id, seed, rewards, steps


def build_replay_dataset(
    replay: dict[str, Any],
    *,
    replay_sha256: str,
    team_name: str,
    split: str,
    source_submission_id: int | None = None,
    source_score_snapshot: float | None = None,
    replay_date: str | None = None,
    collected_at: str | None = None,
    expected_records: int = 720,
    baseline: Baseline = calendar,
) -> ReplayDataset:
    """Align observation record n-1 with the action in replay record n."""
    if split not in DATASET_SPLITS:
        raise ValueError(f"Unknown dataset split: {split!r}")
    episode_id, seed, rewards, steps = _validate_replay(
        replay,
        expected_records,
    )
    player = resolve_player(replay, team_name)
    examples = []
    for record_index in range(1, len(steps)):
        observation_value = steps[record_index - 1][player].get(
            "observation"
        )
        if not isinstance(observation_value, dict):
            raise ValueError(
                f"Replay record {record_index - 1} has no observation"
            )
        observation = copy.deepcopy(observation_value)
        observation["step"] = record_index - 1
        baseline_action = baseline(copy.deepcopy(observation))
        player_id = int(observation.get("player", player))
        farms = observation.get("farms", [])
        if not isinstance(farms, list) or player_id >= len(farms):
            raise ValueError(
                f"Replay record {record_index - 1} has invalid farms"
            )
        farm = farms[player_id]
        if not isinstance(farm, dict):
            raise ValueError(
                f"Replay record {record_index - 1} has no own farm"
            )
        expected_hands = len(farm.get("hands", []))
        teacher_action = _require_action(
            steps[record_index][player].get("action"),
            record_index,
            expected_hands,
        )
        examples.append(
            ReplayExample(
                episode_id=episode_id,
                player=player,
                record_index=record_index,
                state=encode_state(observation, baseline_action),
                teacher_action=teacher_action,
            )
        )
    return ReplayDataset(
        episode_id=episode_id,
        seed=seed,
        source_team=team_name,
        source_player=player,
        source_submission_id=source_submission_id,
        source_score_snapshot=source_score_snapshot,
        replay_date=replay_date,
        collected_at=(
            collected_at
            or datetime.now(timezone.utc).isoformat()
        ),
        split=split,
        simulator_version=SIMULATOR_VERSION,
        replay_sha256=replay_sha256,
        rewards=rewards,
        examples=tuple(examples),
    )


def load_replay_dataset(
    replay_path: Path,
    *,
    team_name: str,
    split: str,
    source_submission_id: int | None = None,
    source_score_snapshot: float | None = None,
    replay_date: str | None = None,
    collected_at: str | None = None,
    expected_records: int = 720,
    baseline: Baseline = calendar,
) -> ReplayDataset:
    replay_bytes = replay_path.read_bytes()
    replay = json.loads(replay_bytes)
    return build_replay_dataset(
        replay,
        replay_sha256=hashlib.sha256(replay_bytes).hexdigest(),
        team_name=team_name,
        split=split,
        source_submission_id=source_submission_id,
        source_score_snapshot=source_score_snapshot,
        replay_date=replay_date,
        collected_at=collected_at,
        expected_records=expected_records,
        baseline=baseline,
    )


def write_jsonl(dataset: ReplayDataset, output: Path) -> None:
    """Write one metadata row followed by one row per decision."""
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [dataset.metadata()]
    rows.extend(example.as_json() for example in dataset.examples)
    output.write_text(
        "".join(
            json.dumps(row, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--team-name", required=True)
    parser.add_argument("--split", choices=sorted(DATASET_SPLITS), required=True)
    parser.add_argument("--submission-id", type=int)
    parser.add_argument("--score-snapshot", type=float)
    parser.add_argument("--replay-date")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = load_replay_dataset(
        args.replay,
        team_name=args.team_name,
        split=args.split,
        source_submission_id=args.submission_id,
        source_score_snapshot=args.score_snapshot,
        replay_date=args.replay_date,
    )
    write_jsonl(dataset, args.output)
    print(f"Episode: {dataset.episode_id}")
    print(f"Player: {dataset.source_player}")
    print(f"Examples: {len(dataset.examples)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()