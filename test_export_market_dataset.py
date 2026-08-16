import unittest

from export_market_dataset import build_dataset


class MarketDatasetTests(unittest.TestCase):
    def test_exports_pre_decision_features_and_separate_outcomes(self) -> None:
        audit = {
            "metadata": {
                "source_replay": "artifacts/example-replay.json",
                "simulator_version": "test",
                "player": 0,
                "agent_sha256": "example-policy",
                "collection": {
                    "episode_id": "seed-7-player-1",
                    "seed": 7,
                    "agent_player": 1,
                    "opponent": "starter",
                    "raw_replay_persisted": False,
                },
            },
            "policy_under_audit": {"market_policy": ["example rule"]},
            "score": {
                "final_reward": 3_100,
                "opponent_reward": 3_000,
                "result": "win",
            },
            "summary": {"final_money": 3_100},
            "records": [
                {"record_type": "initialized_state"},
                self._transition(1, [], 4, 4, 0),
                self._transition(2, [["SELL", "WHEAT", 4]], 4, 0, 100),
                self._transition(3, [], 0, 0, 0),
            ],
        }

        dataset = build_dataset([audit])

        self.assertEqual(len(dataset["rows"]), 2)
        hold, sell = dataset["rows"]
        self.assertEqual(hold["episode_id"], "seed-7-player-1")
        self.assertEqual(hold["seed"], 7)
        self.assertEqual(hold["agent_player"], 1)
        self.assertFalse(
            dataset["episodes"][0]["raw_replay_persisted"]
        )
        self.assertEqual(hold["decision"]["action"], "HOLD")
        self.assertEqual(sell["decision"]["action"], "SELL")
        self.assertEqual(sell["features"]["shed_wheat"], 4)
        self.assertEqual(sell["decision"]["sale_units_ordered"], 4)
        self.assertEqual(
            sell["behavior_policy_sha256"], "example-policy"
        )
        self.assertNotIn("terminal_money", sell["features"])
        self.assertEqual(sell["outcomes"]["terminal_money"], 3_100)
        self.assertEqual(sell["outcomes"]["wheat_units_sold"], 4)
        self.assertEqual(
            dataset["episodes"][0]["behavior_policy"]["market_policy"],
            ["example rule"],
        )
        self.assertEqual(
            dataset["summary"]["action_counts"],
            {"HOLD": 1, "SELL": 1},
        )

    @staticmethod
    def _transition(
        record_index: int,
        orders: list[list[object]],
        shed_before: int,
        shed_after: int,
        money_delta: int,
    ) -> dict:
        return {
            "record_index": record_index,
            "record_type": "executed_transition",
            "decision_observation_step": record_index - 1,
            "day": 3,
            "hour": record_index,
            "market_orders": orders,
            "state_before": {
                "money": 3_000,
                "wheat_seeds": 1,
                "shed_wheat": shed_before,
                "carried_wheat": 0,
                "planted_wheat": 6,
                "weeds": 0,
                "wheat_market_price": 25,
                "wheat_market_inventory": 1_000,
            },
            "state_after": {"shed_wheat": shed_after},
            "cash_flow": {
                "net_money_delta": money_delta,
                "wheat_units_sold": shed_before - shed_after,
                "realized_sale_revenue": money_delta,
            },
        }


if __name__ == "__main__":
    unittest.main()