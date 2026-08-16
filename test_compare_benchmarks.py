import unittest

from compare_benchmarks import compare_reports


class CompareBenchmarksTests(unittest.TestCase):
    def test_compares_identical_games_and_excluded_seed_subset(self) -> None:
        candidate = self._report([110, 130])
        control = self._report([100, 120], parameters={"threshold": 1})

        comparison = compare_reports(candidate, control, {1})

        self.assertEqual(
            comparison["summary"]["all_games"]["mean_coin_delta"],
            10.0,
        )
        self.assertEqual(
            comparison["summary"]["excluded_seed_check"]["games"][
                "games"
            ],
            1,
        )
        self.assertTrue(
            comparison["checks"]["candidate_improved_every_game"]
        )
        self.assertTrue(comparison["checks"]["identical_harvested_units"])
        self.assertEqual(
            comparison["summary"]["all_games"][
                "one_sided_sign_test_p_value"
            ],
            0.25,
        )
        self.assertEqual(
            comparison["summary"]["all_seeds"]["improved_games"],
            2,
        )
        self.assertEqual(len(comparison["seeds"]), 2)

    def test_rejects_different_game_sets(self) -> None:
        candidate = self._report([110, 130])
        control = self._report([100])

        with self.assertRaisesRegex(ValueError, "identical games"):
            compare_reports(candidate, control)

    @staticmethod
    def _report(
        rewards: list[int], parameters: dict | None = None
    ) -> dict:
        games = [
            {
                "seed": seed,
                "agent_player": 0,
                "agent_reward": reward,
                "result": "win",
            }
            for seed, reward in enumerate(rewards)
        ]
        return {
            "simulator_version": "test",
            "opponent": "starter",
            "episode_steps": 720,
            "complete": True,
            "parameters": parameters or {},
            "summary": {
                "wins": len(games),
                "losses": 0,
                "ties": 0,
                "errors": 0,
                "mean_agent_coins": sum(rewards) / len(rewards),
                "min_agent_coins": min(rewards),
                "max_agent_coins": max(rewards),
                "final_inventory_totals": {},
                "route_analysis": {
                    "harvested_units": 8,
                    "matched_sold_units": 8,
                    "unmatched_harvested_units": 0,
                    "mean_harvest_to_sale_turns": 10,
                },
            },
            "games": games,
        }


if __name__ == "__main__":
    unittest.main()