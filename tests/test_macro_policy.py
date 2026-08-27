import unittest

from policies.macro_policy import extract_macro_features, select_macro_arm
from tests.test_experimental_scale_agent import scale_observation


class MacroPolicyTests(unittest.TestCase):
    def test_extracts_public_opponent_features_without_private_state(
        self,
    ) -> None:
        state = scale_observation(day=5)
        state["farms"][1]["money"] = 4200
        state["farms"][1]["unlocked_quadrants"] = ["NW", "NE"]
        state["farms"][1]["tiles"][0][0] = {
            "kind": "PLANT",
            "crop": "WHEAT",
        }
        state["private"]["shed"]["WHEAT"] = 999
        state["market"]["prices"].update(
            {
                "STRAWBERRY": 120,
                "MELON": 250,
                "MILK": 160,
                "WOOL": 200,
                "FERTILIZER": 100,
            }
        )

        features = extract_macro_features(state)

        self.assertEqual(features["opponent_money_k"], 4.2)
        self.assertEqual(features["opponent_land"], 2.0)
        self.assertEqual(features["opponent_wheat"], 1.0)
        self.assertNotIn("shed", features)

    def test_evaluates_a_learned_policy_tree(self) -> None:
        model = {
            "feature": "opponent_nonwheat",
            "threshold": 0.5,
            "left": {"arm": 0},
            "right": {"arm": 1},
        }

        self.assertEqual(select_macro_arm(model, {"opponent_nonwheat": 0}), 0)
        self.assertEqual(select_macro_arm(model, {"opponent_nonwheat": 2}), 1)


if __name__ == "__main__":
    unittest.main()
