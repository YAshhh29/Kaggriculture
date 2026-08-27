import unittest
from pathlib import Path
from unittest.mock import patch

from research.evaluation.evaluate_future_labor import ROOT, promotion, run_gate


def result(wins: int, margin: float, errors: int = 0) -> dict:
    games = 4
    return {
        "summary": {
            "games": games,
            "wins": wins,
            "losses": games - wins - errors,
            "errors": errors,
            "mean_margin": margin,
        }
    }


def report(
    control: tuple[dict, dict],
    candidate: tuple[dict, dict],
) -> dict:
    return {
        "variants": {
            "submitted_control": {
                "alpha": control[0],
                "beta": control[1],
            },
            "future_labor": {
                "alpha": candidate[0],
                "beta": candidate[1],
            },
        }
    }


class EvaluateFutureLaborTests(unittest.TestCase):
    def test_promotes_more_wins_without_opponent_regression(self) -> None:
        verdict = promotion(
            report(
                (result(2, 0), result(2, 0)),
                (result(3, 10), result(2, 5)),
            )
        )

        self.assertEqual(verdict["decision"], "PROMOTE")
        self.assertTrue(all(verdict["checks"].values()))

    def test_rejects_one_opponent_regression_despite_more_wins(self) -> None:
        verdict = promotion(
            report(
                (result(2, 0), result(2, 0)),
                (result(4, 20), result(1, 20)),
            )
        )

        self.assertEqual(verdict["decision"], "REJECT")
        self.assertFalse(
            verdict["checks"]["no_opponent_win_regression"]
        )

    def test_run_gate_loads_explicit_control_and_candidate_paths(self) -> None:
        def game(
            make: object,
            agent: str,
            opponent: str,
            steps: int,
            seed: int,
            player: int,
        ) -> dict:
            return {
                "seed": seed,
                "agent_player": player,
                "agent_reward": 100.0,
                "opponent_reward": 90.0,
                "result": "win",
                "route_analysis": {},
                "livestock_analysis": {},
            }

        def summary(records: list[dict]) -> dict:
            return {
                "games": len(records),
                "wins": len(records),
                "losses": 0,
                "errors": 0,
                "mean_margin": 10.0,
            }

        with (
            patch(
                "research.evaluation.evaluate_future_labor.load_simulator",
                return_value=(object(), "1.32.7"),
            ),
            patch(
                "research.evaluation.evaluate_future_labor."
                "load_agent_callable",
                side_effect=lambda path: str(path),
            ) as load_agent,
            patch(
                "research.evaluation.evaluate_future_labor.run_game",
                side_effect=game,
            ) as run_game_mock,
            patch(
                "research.evaluation.evaluate_future_labor.summarize",
                side_effect=summary,
            ),
            patch(
                "research.evaluation.evaluate_future_labor.write_report"
            ),
        ):
            run_gate(
                seed_start=1,
                seed_count=1,
                opponents=("opponent.py",),
                output=Path("ignored.json"),
                control_path="control.py",
                candidate_path="candidate.py",
            )

        loaded = [call.args[0] for call in load_agent.call_args_list]
        control = (ROOT / "control.py").resolve()
        candidate = (ROOT / "candidate.py").resolve()
        self.assertIn(control, loaded)
        self.assertIn(candidate, loaded)
        agents = [call.args[1] for call in run_game_mock.call_args_list]
        self.assertEqual(agents[:2], [str(control), str(control)])
        self.assertEqual(agents[2:], [str(candidate), str(candidate)])


if __name__ == "__main__":
    unittest.main()