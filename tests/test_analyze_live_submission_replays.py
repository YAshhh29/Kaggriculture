import unittest

from research.analysis.analyze_live_submission_replays import summarize


class AnalyzeLiveSubmissionReplaysTests(unittest.TestCase):
    def test_empty_result_partition_has_zero_means(self) -> None:
        record = {
            "episode_id": 1,
            "result": "win",
            "reward": 100.0,
            "margin": 10.0,
            "day12": {"staging_distance": 0},
            "own": {
                "movement_turns": 1,
                "cycles_planted": 1,
                "cycles_harvested": 1,
                "cycles_weeded": 0,
                "cycles_unfinished": 0,
                "missed_planting_day_water": 0,
                "harvested_units": 4,
                "fertilize_actions": 0,
                "fertilize_events": [],
                "total_livestock_losses": 0,
                "sales": {},
                "final": {"money": 100},
            },
        }

        result = summarize([record])

        self.assertEqual(result["loss"]["games"], 0)
        self.assertEqual(result["loss"]["reward"], 0.0)
        self.assertEqual(result["tie"]["games"], 0)


if __name__ == "__main__":
    unittest.main()
