import unittest

from research.training.train_demand_animal_curve import learning_curve


def record(value: float, preferred: int) -> dict:
    outcomes = {
        str(arm): {
            "result": "win" if arm == preferred else "loss",
            "utility": 1000.0 if arm == preferred else -1000.0,
            "margin": 10.0 if arm == preferred else -10.0,
        }
        for arm in (0, 1, 2)
    }
    return {
        "features": {"player": value},
        "outcomes": outcomes,
        "label": preferred,
    }


class DemandAnimalLearningCurveTests(unittest.TestCase):
    def test_curve_reports_fixed_and_learned_validation(self) -> None:
        training = [record(0.0, 0), record(1.0, 1)] * 4
        validation = [record(0.0, 0), record(1.0, 1)]

        points, model = learning_curve(
            training,
            validation,
            (4, 8),
            max_depth=1,
            min_leaf=1,
        )

        self.assertEqual([point["training_contexts"] for point in points], [4, 8])
        self.assertIn("learned", points[-1])
        self.assertIn("fixed_0", points[-1])
        self.assertIn("oracle", points[-1])
        self.assertIn("feature", model)


if __name__ == "__main__":
    unittest.main()
