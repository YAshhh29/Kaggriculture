import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.evaluation import evaluate_live_macro_arms
from research.evaluation.evaluate_live_macro_arms import (
    replay_agent,
    summarize,
    validate_control_reproduction,
)


class EvaluateLiveMacroArmsTests(unittest.TestCase):
    def test_replay_agent_uses_action_after_observation_step(self) -> None:
        actions = [{"id": index} for index in range(3)]
        agent = replay_agent(actions)

        self.assertEqual(
            tuple(inspect.signature(agent).parameters),
            ("observation",),
        )
        self.assertEqual(agent({"step": 0}), {"id": 1})

    def test_summary_prioritizes_own_reward_delta(self) -> None:
        outcomes = [
            {"episode_id": 1, "reward": 110.0, "opponent_reward": 200.0},
            {"episode_id": 2, "reward": 90.0, "opponent_reward": 80.0},
        ]

        result = summarize(outcomes, {1: 100.0, 2: 100.0})

        self.assertEqual(result["wins"], 1)
        self.assertEqual(result["mean_reward_delta"], 0.0)
        self.assertEqual(result["improved_tied_worse"], [1, 0, 1])
        self.assertEqual(result["minimum_reward_delta"], -10.0)

    def test_control_reproduction_checks_opponent_reward(self) -> None:
        record = {
            "episode_id": 42,
            "own_player": 1,
            "expected_rewards": [80.0, 100.0],
        }

        validate_control_reproduction(record, 100.0, 80.0)
        with self.assertRaisesRegex(ValueError, "episode 42"):
            validate_control_reproduction(record, 100.0, 81.0)

    def test_main_records_control_and_episode_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "dataset.json"
            output = root / "report.json"
            control = root / "control.py"
            dataset.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "episode_id": 42,
                                "seed": 1,
                                "own_player": 0,
                                "expected_rewards": [100.0, 90.0],
                                "opponent_actions": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            control.write_text("def agent(observation): return {}\n")
            argv = [
                "evaluate_live_macro_arms",
                str(dataset),
                "--control",
                str(control),
                "--episode",
                "42",
                "--arm",
                "tiered_late_strawberry",
                "--output",
                str(output),
            ]
            with (
                patch("sys.argv", argv),
                patch.object(
                    evaluate_live_macro_arms,
                    "load_simulator",
                    return_value=(object(), "1.32.7"),
                ),
                patch.object(
                    evaluate_live_macro_arms,
                    "load_agent_callable",
                    return_value=lambda observation: {},
                ),
                patch.object(
                    evaluate_live_macro_arms,
                    "run_episode",
                    return_value=(100.0, 90.0),
                ),
            ):
                evaluate_live_macro_arms.main()

            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["control"], str(control))
            self.assertEqual(report["episodes"], [42])


if __name__ == "__main__":
    unittest.main()
