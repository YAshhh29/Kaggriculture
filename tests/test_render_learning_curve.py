import unittest

from research.analysis.render_learning_curve import render_svg


class RenderLearningCurveTests(unittest.TestCase):
    def test_renders_all_validation_series(self) -> None:
        point = {
            "training_contexts": 8,
            "learned": {"games": 40, "wins": 35},
            "fixed_0": {"games": 40, "wins": 33},
            "fixed_1": {"games": 40, "wins": 35},
            "fixed_2": {"games": 40, "wins": 34},
            "oracle": {"games": 40, "wins": 37},
        }

        svg = render_svg({"points": [point]})

        self.assertIn("<svg", svg)
        self.assertIn("Learned tree", svg)
        self.assertIn("Fixed cows", svg)
        self.assertIn("Oracle", svg)


if __name__ == "__main__":
    unittest.main()
