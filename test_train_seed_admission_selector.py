import unittest

from policies.seed_admission_policy import BASELINE, EXTRA, select_seed_admission
from train_seed_admission_selector import evaluate, train, train_tree


def row(value: float, delta: float) -> dict:
    return {
        "features": {"signal": value},
        "outcomes": {
            "baseline": {"utility": 1000.0, "result": "win"},
            "extra": {"utility": 1000.0 + delta, "result": "win"},
        },
    }


class SeedAdmissionSelectorTests(unittest.TestCase):
    def test_tree_learns_positive_extra_region(self) -> None:
        records = [
            *(row(float(index), -10.0) for index in range(5)),
            *(row(float(index), 10.0) for index in range(5, 10)),
        ]

        model, _ = train_tree(
            records,
            features=("signal",),
            max_depth=1,
            min_leaf=3,
        )

        self.assertEqual(select_seed_admission(model, {"signal": 1}), BASELINE)
        self.assertEqual(select_seed_admission(model, {"signal": 8}), EXTRA)
        self.assertGreater(evaluate(model, records)["utility_gain"], 0)

    def test_tied_leaf_defaults_to_baseline(self) -> None:
        model, _ = train_tree(
            [row(0.0, 0.0), row(1.0, 0.0)],
            features=("signal",),
            max_depth=0,
            min_leaf=1,
        )

        self.assertEqual(model["arm"], BASELINE)

    def test_training_can_fall_back_to_always_baseline(self) -> None:
        records = []
        for seed in (1, 2):
            for opponent in ("a", "b"):
                record = row(float(seed), -10.0)
                record.update({"seed": seed, "opponent": opponent})
                records.append(record)

        model, validation = train(records)

        self.assertEqual(model["arm"], BASELINE)
        self.assertEqual(validation["selected"]["extra_choices"], 0)


if __name__ == "__main__":
    unittest.main()
