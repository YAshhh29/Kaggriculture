import unittest

from policies.macro_policy import select_macro_arm
from train_macro_knn import build_model


def _record(value: float, best_arm: int) -> dict:
    features = {name: 0.0 for name in (
        "player",
        "own_money_k",
        "opponent_money_k",
        "money_lead_k",
        "opponent_hands",
        "opponent_land",
        "opponent_wheat",
        "opponent_nonwheat",
        "opponent_cows",
        "opponent_sheep",
        "opponent_geese",
        "opponent_structures",
        "opponent_weeds",
        "price_wheat",
        "price_strawberry",
        "price_melon",
        "price_milk",
        "price_wool",
        "price_fertilizer",
        "shops_wheat",
        "shops_strawberry",
        "shops_milk",
        "shops_wool",
    )}
    features["opponent_money_k"] = value
    return {
        "features": features,
        "outcomes": {
            str(arm): {
                "utility": 1000 if arm == best_arm else -1000,
                "margin": 1 if arm == best_arm else -1,
                "result": "win" if arm == best_arm else "loss",
            }
            for arm in range(4)
        },
    }


class TrainMacroKnnTests(unittest.TestCase):
    def test_knn_selects_counterfactual_arm_from_nearest_context(self) -> None:
        records = [_record(0.0, 1), _record(10.0, 2)]
        model = build_model(records, k=1, distance_power=1.0)

        self.assertEqual(
            select_macro_arm(model, records[0]["features"]),
            1,
        )
        self.assertEqual(
            select_macro_arm(model, records[1]["features"]),
            2,
        )


if __name__ == "__main__":
    unittest.main()
