import unittest

from rl.replay_dataset import SIMULATOR_VERSION
from tools.data import curate_candidate_d_corpus as curate


def _farm(hands: int, money: float, quadrants: list[str]) -> dict:
    return {
        "hands": [["PASS"]] * hands,
        "money": money,
        "unlocked_quadrants": quadrants,
    }


def _make_replay(
    *,
    episode_id: int,
    seed: int,
    agent_names: list[str],
    rewards: list[float],
    final_farms: list[dict],
) -> dict:
    empty_step = [{"observation": {}}, {"observation": {}}]
    steps = [empty_step] * 719
    final_step = [
        {"observation": {"farms": final_farms}},
        {"observation": {"farms": final_farms}},
    ]
    return {
        "module_version": SIMULATOR_VERSION,
        "statuses": ["DONE", "DONE"],
        "rewards": rewards,
        "info": {
            "EpisodeId": episode_id,
            "seed": seed,
            "Agents": [{"Name": name} for name in agent_names],
        },
        "steps": [*steps, final_step],
    }


class CurateCandidateDCorpusTests(unittest.TestCase):
    def test_index_row_for_a_real_matchup(self) -> None:
        replay = _make_replay(
            episode_id=42,
            seed=7,
            agent_names=["YASH JAIN", "some opponent"],
            rewards=[123624.0, 59014.0],
            final_farms=[
                _farm(12, 123624.0, ["NW", "NE", "SW"]),
                _farm(0, 59014.0, ["NW"]),
            ],
        )
        # _index_row reads from a path, so exercise the pieces it composes
        # directly rather than writing a temp file.
        episode_id, seed, rewards, _steps = curate._validate_replay(
            replay, expected_records=720
        )
        our_side, opp_side = curate._resolve_sides(replay)
        self.assertEqual(our_side, 0)
        self.assertEqual(opp_side, 1)
        self.assertEqual(episode_id, 42)
        self.assertEqual(seed, 7)
        self.assertEqual(rewards, (123624.0, 59014.0))
        our_final = curate._final_farm_stats(replay, our_side)
        opp_final = curate._final_farm_stats(replay, opp_side)
        self.assertEqual(our_final["hands"], 12)
        self.assertEqual(our_final["unlocked_quadrants"], ["NW", "NE", "SW"])
        self.assertEqual(opp_final["hands"], 0)

    def test_resolve_sides_rejects_zero_or_two_matches(self) -> None:
        neither = _make_replay(
            episode_id=1,
            seed=1,
            agent_names=["fog flower", "Giulio Ravasio"],
            rewards=[1.0, 2.0],
            final_farms=[_farm(1, 1.0, ["NW"]), _farm(1, 2.0, ["NW"])],
        )
        with self.assertRaises(ValueError):
            curate._resolve_sides(neither)

        both = _make_replay(
            episode_id=2,
            seed=1,
            agent_names=["YASH JAIN", "YASH JAIN"],
            rewards=[1.0, 2.0],
            final_farms=[_farm(1, 1.0, ["NW"]), _farm(1, 2.0, ["NW"])],
        )
        with self.assertRaises(ValueError):
            curate._resolve_sides(both)

    def test_split_is_deterministic_per_opponent(self) -> None:
        first = curate._split_for("Some Opponent")
        second = curate._split_for("some opponent")
        self.assertEqual(first, second)
        self.assertIn(first, {"train", "validation", "test"})

    def test_build_index_deduplicates_by_episode_id(self) -> None:
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            replay = _make_replay(
                episode_id=99,
                seed=1,
                agent_names=["YASH JAIN", "dup opponent"],
                rewards=[10.0, 5.0],
                final_farms=[_farm(1, 10.0, ["NW"]), _farm(1, 5.0, ["NW"])],
            )
            (cache_dir / "episode-99-replay.json").write_text(
                json.dumps(replay), encoding="utf-8"
            )
            (cache_dir / "episode-99-replay-copy.json").write_text(
                json.dumps(replay), encoding="utf-8"
            )
            # Only files matching the episode-*-replay.json glob are scanned.
            (cache_dir / "episode-99-replay-copy.json").unlink()
            (cache_dir / "episode-99b-replay.json").write_text(
                json.dumps(replay), encoding="utf-8"
            )

            included, excluded = curate.build_index(cache_dir)

        self.assertEqual(len(included), 1)
        self.assertEqual(len(excluded), 1)
        self.assertIn("duplicate", excluded[0]["reason"])


if __name__ == "__main__":
    unittest.main()
