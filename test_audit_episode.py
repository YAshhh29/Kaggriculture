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

    def test_records_every_worker_action_and_position(self) -> None:
        replay = {
            "configuration": {"episodeSteps": 2, "turnsPerDay": 24},
            "steps": [
                [
                    self._state(
                        0,
                        3_000,
                        seeds=1,
                        shed=0,
                        hands=[[0, 0]],
                    )
                ],
                [
                    self._state(
                        1,
                        3_000,
                        seeds=0,
                        shed=0,
                        planted=True,
                        watered=True,
                        hands=[[0, 0]],
                        action={
                            "farmer": ["PLANT", "WHEAT"],
                            "hands": [["WATER"]],
                            "market": [],
                        },
                        reward=3_000,
                        status="DONE",
                    )
                ],
            ],
        }

        workers = build_audit(replay)["records"][1]["worker_actions"]

        self.assertEqual(
            workers,
            [
                {
                    "worker": "farmer",
                    "action": ["PLANT", "WHEAT"],
                    "operation": "PLANT",
                    "position_before": [0, 0],
                    "position_after": [0, 0],
                },
                {
                    "worker": "hand_1",
                    "action": ["WATER"],
                    "operation": "WATER",
                    "position_before": [0, 0],
                    "position_after": [0, 0],
                },
            ],
        )

    def test_records_observed_hires_land_and_animals(self) -> None:
        before = self._state(0, 3_000, seeds=0, shed=0)
        after = self._state(
            1,
            1_599,
            seeds=0,
            shed=0,
            hands=[[0, 0]],
            action={
                "farmer": ["PASS"],
                "hands": [],
                "market": [
                    ["HIRE"],
                    ["BUY_LAND"],
                    ["BUY_ANIMAL", "COW", 1],
                ],
            },
            reward=1_599,
            status="DONE",
        )
        before["observation"]["farms"][0]["unlocked_quadrants"] = ["NW"]
        after["observation"]["farms"][0]["unlocked_quadrants"] = [
            "NW",
            "NE",
        ]
        after["observation"]["farms"][0]["tiles"][0][0] = {
            "kind": "PASTURE",
            "animal": "COW",
        }

        changes = build_audit(
            {
                "configuration": {"episodeSteps": 2, "turnsPerDay": 24},
                "steps": [[before], [after]],
            }
        )["records"][1]["observed_changes"]

        self.assertEqual(changes["hands_added"], 1)
        self.assertEqual(changes["unlocked_quadrants"], ["NE"])
        self.assertEqual(
            changes["created_animals"],
            [{"animal": "COW", "tile": [0, 0]}],
        )

    @staticmethod
    def _state(
        step: int,
        money: int,
        *,
        seeds: int,
        shed: int,
        planted: bool = False,
        watered: bool = False,
        hands: list[list[int]] | None = None,
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
                "watered_today": watered,
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
                        "hands": hands or [],
                        "unlocked_quadrants": ["NW"],
                        "tiles": [[tile]],
                    },
                    {
                        "money": 3_000.0,
                        "farmer": [0, 0],
                        "hands": [],
                        "unlocked_quadrants": ["NW"],
                        "tiles": [[None]],
                    },
                ],
                "private": {
                    "shed": {"WHEAT": shed},
                    "seeds": {"WHEAT": seeds},
                    "inventories": [{} for _ in range(1 + len(hands or []))],
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
