import unittest
from unittest.mock import patch

from research.collection.collect_live_replay_league import (
    DECISION_POINTS,
    _decision_contexts,
    _resolve_player,
    merge_records,
)


def record(episode_id: int, *, seed: int | None = None) -> dict:
    return {
        "episode_id": episode_id,
        "seed": episode_id if seed is None else seed,
        "own_player": 1,
        "expected_rewards": [10.0, 20.0],
    }


class CollectLiveReplayLeagueTests(unittest.TestCase):
    def test_resolves_and_validates_player_from_replay_name(self) -> None:
        replay = {
            "info": {
                "Agents": [{"Name": "other"}, {"Name": "YASH JAIN"}]
            }
        }

        self.assertEqual(_resolve_player(replay, "auto", "YASH JAIN"), 1)
        self.assertEqual(_resolve_player(replay, "1", "YASH JAIN"), 1)
        with self.assertRaisesRegex(ValueError, "Requested player 0"):
            _resolve_player(replay, "0", "YASH JAIN")

    def test_extracts_every_late_decision_context(self) -> None:
        steps = []
        for day, hour in DECISION_POINTS:
            observation = {
                "day": day,
                "hour": hour,
                "town": {"unlocked_shops": [f"shop-{day}-{hour}"]},
            }
            steps.append([{}, {"observation": observation}])

        with patch(
            "research.collection.collect_live_replay_league."
            "extract_live_macro_features",
            side_effect=lambda observation: {
                "point": f"{observation['day']}:{observation['hour']}"
            },
        ):
            contexts = _decision_contexts({"steps": steps}, 1)

        self.assertEqual(len(contexts), len(DECISION_POINTS))
        self.assertEqual(
            contexts["day12_hour12"]["features"],
            {"point": "12:12"},
        )

    def test_append_refreshes_known_episode_and_sorts(self) -> None:
        refreshed = {**record(2), "decision_contexts": {"new": True}}

        merged = merge_records(
            [record(2), record(1)],
            [refreshed, record(3)],
        )

        self.assertEqual([item["episode_id"] for item in merged], [1, 2, 3])
        self.assertEqual(merged[1]["decision_contexts"], {"new": True})

    def test_append_rejects_conflicting_episode_metadata(self) -> None:
        with self.assertRaisesRegex(ValueError, "episode metadata"):
            merge_records([record(1)], [record(1, seed=99)])


if __name__ == "__main__":
    unittest.main()
