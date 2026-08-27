import unittest

from research.analysis.build_live_macro_labels import build_labels


class BuildLiveMacroLabelsTests(unittest.TestCase):
    def test_labels_by_own_reward_and_prefers_control_on_tie(self) -> None:
        dataset = {
            "records": [
                {
                    "episode_id": 1,
                    "day6_features": {"pressure": 1.0},
                    "day6_shops": ["BAKERY"],
                },
                {
                    "episode_id": 2,
                    "day6_features": {"pressure": 2.0},
                    "day6_shops": [],
                },
            ]
        }
        evaluation = {
            "results": {
                "control": {
                    "outcomes": [
                        {"episode_id": 1, "reward": 100},
                        {"episode_id": 2, "reward": 100},
                    ]
                },
                "candidate": {
                    "outcomes": [
                        {"episode_id": 1, "reward": 110},
                        {"episode_id": 2, "reward": 100},
                    ]
                },
            }
        }

        result = build_labels(dataset, evaluation)

        self.assertEqual(
            [record["best_arm"] for record in result["records"]],
            ["candidate", "control"],
        )
        self.assertEqual(result["oracle"]["total_reward_gain"], 10)
        self.assertEqual(result["oracle"]["mean_reward_gain"], 5.0)


if __name__ == "__main__":
    unittest.main()