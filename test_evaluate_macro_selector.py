import unittest
import json
from pathlib import Path

from evaluate_macro_selector import evaluate


def _record(nonwheat: float, compact: float, expanded: float) -> dict:
    return {
        "features": {
            "opponent_nonwheat": nonwheat,
            "opponent_money_k": 0.0 if expanded > compact else 1.0,
        },
        "outcomes": {
            "0": {
                "utility": compact,
                "margin": compact,
                "result": "win" if compact > 0 else "loss",
            },
            "1": {
                "utility": expanded,
                "margin": expanded,
                "result": "win" if expanded > 0 else "loss",
            },
        },
        "label": 0 if compact > expanded else 1,
    }


class EvaluateMacroSelectorTests(unittest.TestCase):
    def test_compares_learned_and_handwritten_selection(self) -> None:
        model = {
            "feature": "opponent_money_k",
            "threshold": 0.5,
            "left": {"arm": 1},
            "right": {"arm": 0},
        }
        records = [
            _record(0, -1000, 1000),
            _record(2, 1000, -1000),
        ]

        result = evaluate(model, records)

        self.assertEqual(result["learned"]["wins"], 2)
        self.assertEqual(result["handwritten"]["wins"], 0)

    def test_real_holdout_files_evaluate(self) -> None:
        root = Path(__file__).resolve().parent
        model = json.loads(
            (
                root
                / "artifacts"
                / "models"
                / "v1327-macro-selector-v2-depth3.json"
            ).read_text(encoding="utf-8")
        )["model"]
        records = [
            record
            for path in (
                root
                / "artifacts"
                / "datasets"
                / "v1327-macro-counterfactuals-holdout-seeds110-112.json",
                root
                / "artifacts"
                / "datasets"
                / "v1327-macro-counterfactuals-top-holdout.json",
            )
            for record in json.loads(path.read_text(encoding="utf-8"))[
                "records"
            ]
        ]

        result = evaluate(model, records)

        self.assertEqual(result["learned"]["games"], 32)
        self.assertIn("oracle", result)


if __name__ == "__main__":
    unittest.main()
