import unittest
from copy import deepcopy

from research.training.train_live_macro_selector import (
    TRAINING_FEATURES,
    leave_one_episode_out,
    select_arm,
    train_tree,
)


def record(feature: float, control: float, fertilizer: float) -> dict:
    features = {name: 0.0 for name in TRAINING_FEATURES}
    features["opponent_wheat"] = feature
    return {
        "features": features,
        "rewards": {
            "control": control,
            "pressure_late_strawberry": control - 1,
            "fertilizer_70": fertilizer,
        },
    }


class TrainLiveMacroSelectorTests(unittest.TestCase):
    def test_tree_learns_own_reward_split(self) -> None:
        records = [
            record(0, 100, 90),
            record(1, 100, 90),
            record(5, 100, 120),
            record(6, 100, 120),
        ]

        model, _ = train_tree(records, max_depth=1, min_leaf=2)

        self.assertEqual(select_arm(model, records[0]["features"]), "control")
        self.assertEqual(
            select_arm(model, records[-1]["features"]),
            "fertilizer_70",
        )

    def test_cross_validation_restricts_fold_to_common_arms(self) -> None:
        records = [
            record(0, 100, 120),
            record(1, 100, 120),
            record(2, 100, 120),
        ]
        records[0]["episode_id"] = 1
        records[1]["episode_id"] = 2
        records[2]["episode_id"] = 3
        del records[2]["rewards"]["fertilizer_70"]

        result = leave_one_episode_out(
            records,
            max_depth=1,
            min_leaf=1,
        )

        self.assertEqual(result["arm_counts"]["control"], 3)
        self.assertNotIn("fertilizer_70", result["arm_counts"])

    def test_cross_validation_deduplicates_episode_ids(self) -> None:
        records = [
            record(0, 100, 90),
            record(1, 100, 90),
            record(2, 100, 90),
        ]
        for episode_id, item in enumerate(records, start=1):
            item["episode_id"] = episode_id
        records.append(deepcopy(records[0]))

        result = leave_one_episode_out(
            records,
            max_depth=1,
            min_leaf=1,
        )

        self.assertEqual(len(result["outcomes"]), 3)

    def test_cross_validation_rejects_conflicting_duplicate(self) -> None:
        first = record(0, 100, 90)
        second = record(0, 100, 120)
        first["episode_id"] = 1
        second["episode_id"] = 1

        with self.assertRaisesRegex(ValueError, "episode 1"):
            leave_one_episode_out(
                [first, second],
                max_depth=1,
                min_leaf=1,
            )


if __name__ == "__main__":
    unittest.main()