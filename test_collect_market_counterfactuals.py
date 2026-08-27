import unittest
import tempfile
from pathlib import Path

from research.collection.collect_market_counterfactuals import (
    clone_for_counterfactual,
    force_wheat_choice,
    load_or_create_report,
    summarize,
    write_checkpoint,
)


class MarketCounterfactualTests(unittest.TestCase):
    def test_checkpoints_and_rejects_incompatible_resume(self) -> None:
        collection = {
            "agent_sha256": "policy",
            "seed_start": 30,
            "seed_count": 1,
            "positions": [0],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "counterfactuals.json"
            report = load_or_create_report(output, collection)
            report["episodes"].append(
                {
                    "seed": 30,
                    "agent_player": 0,
                    "rows": [],
                }
            )
            write_checkpoint(output, report, expected_episodes=1)
            resumed = load_or_create_report(output, collection)

            with self.assertRaisesRegex(ValueError, "agent_sha256"):
                load_or_create_report(
                    output,
                    {**collection, "agent_sha256": "different"},
                )

        self.assertTrue(resumed["complete"])
        self.assertEqual(resumed["summary"]["episodes"], 1)

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