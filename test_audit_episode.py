import unittest

from audit_episode import build_audit


class AuditEpisodeTests(unittest.TestCase):
    def test_audits_records_and_reconciles_wheat_cash(self) -> None:
        replay = {
            "name": "kaggriculture",
            "version": "test",
            "configuration": {
                "episodeSteps": 3,
                "turnsPerDay": 24,
            },
            "steps": [
                [self._state(0, 3_000, seeds=0, shed=0)],
                [
                    self._state(
                        1,
                        2_980,
                        seeds=2,
                        shed=4,
                        action={
                            "farmer": ["PASS"],
                            "hands": [],
                            "market": [["BUY_SEED", "WHEAT", 2]],
                        },
                    )
                ],
                [
                    self._state(
                        2,
                        3_080,
                        seeds=1,
                        shed=0,
                        planted=True,
                        action={
                            "farmer": ["PLANT", "WHEAT"],
                            "hands": [],
                            "market": [["SELL", "WHEAT", 4]],
                        },
                        reward=3_080,
                        status="DONE",
                    )
                ],
            ],
        }

        audit = build_audit(replay)

        self.assertEqual(audit["metadata"]["replay_records"], 3)
        self.assertEqual(audit["metadata"]["executed_transitions"], 2)
        self.assertEqual(len(audit["records"]), 3)
        self.assertEqual(audit["summary"]["successful_seed_spend"], 20)
        self.assertEqual(audit["summary"]["realized_sale_revenue"], 100)
        self.assertEqual(audit["summary"]["wheat_units_sold"], 4)
        self.assertEqual(
            audit["summary"]["weighted_average_wheat_sale_price"],
            25.0,
        )
        self.assertEqual(
            audit["summary"]["cash_reconciliation"]["difference"],
            0.0,
        )
        self.assertEqual(
            audit["records"][2]["board_changes"]["created_plants"][0][
                "tile"
            ],
            [0, 0],
        )

    def test_records_an_explicit_market_policy(self) -> None:
        replay = {
            "configuration": {"episodeSteps": 2, "turnsPerDay": 24},
            "steps": [
                [self._state(0, 3_000, seeds=0, shed=0)],
                [
                    self._state(
                        1,
                        3_000,
                        seeds=0,
                        shed=0,
                        reward=3_000,
                        status="DONE",
                    )
                ],
            ],
        }

        audit = build_audit(replay, market_policy=["sell immediately"])

        self.assertEqual(
            audit["policy_under_audit"]["market_policy"],
            ["sell immediately"],
        )

    @staticmethod
    def _state(
        step: int,
        money: int,
        *,
        seeds: int,
        shed: int,
        planted: bool = False,
        action: dict | None = None,
        reward: int | None = None,
        status: str = "ACTIVE",
    ) -> dict:
        tile = (
            {
                "kind": "PLANT",
                "crop": "WHEAT",
                "planted_day": 0,
                "yield_units": 1,
                "watered_today": False,
                "consecutive_unwatered": 1,
            }
            if planted
            else None
        )
        return {
            "action": action
            or {"farmer": ["PASS"], "hands": [], "market": []},
            "reward": reward,
            "status": status,
            "observation": {
                "step": step,
                "day": 0,
                "hour": step,
                "farms": [
                    {
                        "money": float(money),
                        "farmer": [0, 0],
                        "tiles": [[tile]],
                    },
                    {
                        "money": 3_000.0,
                        "farmer": [0, 0],
                        "tiles": [[None]],
                    },
                ],
                "private": {
                    "shed": {"WHEAT": shed},
                    "seeds": {"WHEAT": seeds},
                    "inventories": [{}],
                },
                "market": {
                    "prices": {"WHEAT": 25},
                    "inventory": {"WHEAT": 10_000},
                },
                "town": {"unlocked_shops": []},
            },
        }


if __name__ == "__main__":
    unittest.main()
