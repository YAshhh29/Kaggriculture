import unittest

from research.analysis.run_overnight_shadow import (
    classify_promotion,
    compact_game,
)


def entry(wins: int, margin: float, errors: int = 0) -> dict:
    games = 4
    return {
        "summary": {
            "games": games,
            "wins": wins,
            "losses": games - wins - errors,
            "ties": 0,
            "errors": errors,
            "mean_margin": margin,
        }
    }


class OvernightShadowTests(unittest.TestCase):
    def test_promotion_requires_more_wins_and_no_opponent_regression(self) -> None:
        variants = {
            "submitted_control": {"a": entry(2, 0), "b": entry(2, 0)},
            "demand_heuristic": {"a": entry(3, 10), "b": entry(2, 5)},
        }

        verdict = classify_promotion(variants)

        self.assertEqual(verdict["decision"], "PROMOTE")

    def test_any_opponent_win_regression_rejects(self) -> None:
        variants = {
            "submitted_control": {"a": entry(2, 0), "b": entry(2, 0)},
            "demand_heuristic": {"a": entry(4, 20), "b": entry(1, 20)},
        }

        verdict = classify_promotion(variants)

        self.assertEqual(verdict["decision"], "REJECT")
        self.assertFalse(verdict["checks"]["no_opponent_win_regression"])

    def test_compact_game_keeps_outcome_and_mechanism_signals(self) -> None:
        record = {
            "seed": 1,
            "agent_player": 0,
            "agent_reward": 10,
            "opponent_reward": 9,
            "agent_status": "DONE",
            "opponent_status": "DONE",
            "result": "win",
            "route_analysis": {
                "all_worker_movement_turns": 12,
                "cycles_planted": 4,
                "cycles_harvested": 4,
                "cycles_weeded": 0,
            },
            "livestock_analysis": {"losses": {"COW": 1}},
        }

        compact = compact_game(record)

        self.assertEqual(compact["movement_turns"], 12)
        self.assertEqual(compact["livestock_losses"], {"COW": 1})


if __name__ == "__main__":
    unittest.main()
