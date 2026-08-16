import unittest

from collect_market_counterfactuals import (
    clone_for_counterfactual,
    force_wheat_choice,
    summarize,
)


class MarketCounterfactualTests(unittest.TestCase):
    def test_clone_preserves_independent_episode_seed_metadata(self) -> None:
        class FakeEnvironment:
            def __init__(self) -> None:
                self.info = {"seed": 30, "nested": {"value": 1}}

            def clone(self):
                clone = FakeEnvironment()
                clone.info = {}
                return clone

        source = FakeEnvironment()

        branch = clone_for_counterfactual(source)
        branch.info["nested"]["value"] = 2

        self.assertEqual(branch.info["seed"], 30)
        self.assertEqual(source.info["nested"]["value"], 1)

    def test_forces_one_market_choice_and_preserves_other_actions(self) -> None:
        action = {
            "farmer": ["WATER"],
            "hands": [],
            "market": [
                ["SELL", "WHEAT", 4],
                ["BUY_SEED", "WHEAT", 2],
            ],
        }

        hold = force_wheat_choice(action, 12, "HOLD")
        sell = force_wheat_choice(action, 12, "SELL")

        self.assertEqual(hold["farmer"], ["WATER"])
        self.assertEqual(hold["market"], [["BUY_SEED", "WHEAT", 2]])
        self.assertEqual(
            sell["market"],
            [
                ["SELL", "WHEAT", 12],
                ["BUY_SEED", "WHEAT", 2],
            ],
        )
        self.assertEqual(action["market"][0], ["SELL", "WHEAT", 4])

    def test_summarizes_preferred_counterfactual_choices(self) -> None:
        episodes = [
            {
                "rows": [
                    self._row("SELL", 10),
                    self._row("HOLD", -4),
                    self._row("TIE", 0),
                ]
            }
        ]

        summary = summarize(episodes)

        self.assertEqual(summary["counterfactual_states"], 3)
        self.assertEqual(
            summary["preferred_choices"],
            {"HOLD": 1, "SELL": 1, "TIE": 1},
        )
        self.assertEqual(
            summary["mean_sell_minus_hold_terminal_coins"],
            2.0,
        )

    @staticmethod
    def _row(choice: str, delta: int) -> dict:
        return {
            "outcomes": {
                "preferred_choice": choice,
                "sell_minus_hold_terminal_coins": delta,
            }
        }


if __name__ == "__main__":
    unittest.main()