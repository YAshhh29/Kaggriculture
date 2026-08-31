import unittest

from research.analysis.analyze_strategy_cohort import summarize


class AnalyzeStrategyCohortTests(unittest.TestCase):
    def test_summarizes_capacity_and_late_planting_by_band(self) -> None:
        record = {
            "band": "top",
            "result": "win",
            "margin": 10.0,
            "own": {
                "reward": 100.0,
                "hires": 12,
                "maximum_hands": 12,
                "maximum_concurrent": {"productive_tiles": 75},
                "season_productive_utilization": 0.8,
                "plants": {"WHEAT": 10},
                "animal_placements": {"COW": 2},
                "animal_losses": {"COW": 1},
                "sales": {"WHEAT": 40},
                "actions": {"PLANT": 10, "PASS": 2},
                "plant_actions_by_day": {"19": 2, "20": 3, "27": 1},
            },
        }

        result = summarize([record])["top"]

        self.assertEqual(result["wins"], 1)
        self.assertEqual(result["mean_maximum_productive_tiles"], 75.0)
        self.assertEqual(result["total_plants"], {"WHEAT": 10})
        self.assertEqual(result["mean_late_plant_actions"], 4.0)


if __name__ == "__main__":
    unittest.main()
