import unittest

from research.analysis.analyze_public_replay import analyze_replay


def state(
    *,
    action,
    step,
    day,
    hour,
    money,
    tiles,
    hands=None,
    shed=None,
    seeds=None,
    reward=0,
    status="ACTIVE",
):
    farm = {
        "money": money,
        "tiles": tiles,
        "farmer": [0, 0],
        "hands": hands or [],
        "unlocked_quadrants": ["NW"],
    }
    return {
        "action": action,
        "observation": {
            "step": step,
            "day": day,
            "hour": hour,
            "farms": [farm],
            "private": {
                "shed": shed or {},
                "seeds": seeds or {},
                "inventories": [{} for _ in range(1 + len(hands or []))],
            },
        },
        "reward": reward,
        "status": status,
    }


class AnalyzePublicReplayTests(unittest.TestCase):
    def test_summarizes_workforce_land_crops_and_animals(self) -> None:
        empty = [[None, None]]
        pasture = [[{"kind": "PASTURE"}, None]]
        cow_and_melon = [[
            {
                "kind": "PASTURE",
                "animal": "COW",
                "placed_day": 0,
            },
            {
                "kind": "PLANT",
                "crop": "MELON",
                "planted_day": 0,
            },
        ]]
        replay = {
            "name": "kaggriculture",
            "module_version": "1.32.7",
            "configuration": {"turnsPerDay": 24},
            "info": {
                "EpisodeId": 7,
                "seed": 11,
                "TeamNames": ["leader"],
            },
            "rewards": [5000],
            "steps": [
                [state(
                    action={"farmer": ["PASS"], "hands": [], "market": []},
                    step=0,
                    day=0,
                    hour=0,
                    money=3000,
                    tiles=empty,
                )],
                [state(
                    action={
                        "farmer": ["BUILD_PASTURE"],
                        "hands": [],
                        "market": [
                            ["HIRE"],
                            ["BUY_ANIMAL", "COW", 1],
                            ["BUY_SEED", "MELON", 1],
                            ["BUY_LAND"],
                        ],
                    },
                    step=1,
                    day=0,
                    hour=1,
                    money=1580,
                    tiles=pasture,
                    hands=[[0, 0]],
                    shed={"COW": 1},
                    seeds={"MELON": 1},
                )],
                [state(
                    action={
                        "farmer": ["PLACE", "COW", 1],
                        "hands": [["PLANT", "MELON"]],
                        "market": [["SELL", "MILK", 3]],
                    },
                    step=2,
                    day=0,
                    hour=2,
                    money=2060,
                    tiles=cow_and_melon,
                    hands=[[1, 0]],
                    reward=5000,
                    status="DONE",
                )],
            ],
        }

        player = analyze_replay(replay)["players"][0]

        self.assertEqual(player["workforce"]["hires"], 1)
        self.assertEqual(player["workforce"]["maximum_simultaneous_hands"], 1)
        self.assertEqual(player["market_units_requested"]["BUY_ANIMAL:COW"], 1)
        self.assertEqual(player["market_units_requested"]["SELL:MILK"], 3)
        self.assertEqual(
            player["successful_board_transitions"]["plants"],
            {"MELON": 1},
        )
        self.assertEqual(
            player["successful_board_transitions"]["plants_by_day"],
            {"0": {"MELON": 1}},
        )
        self.assertEqual(
            player["successful_board_transitions"]["animal_placements"],
            {"COW": 1},
        )
        self.assertEqual(player["crop_harvest_ages"], {})
        self.assertEqual(len(player["land_purchases"]), 1)
        self.assertEqual(
            player["board_utilization"]["maximum_concurrent_counts"],
            {
                "animals": 1,
                "crops": 1,
                "productive_tiles": 2,
                "structures": 1,
                "weeds": 0,
            },
        )
        self.assertEqual(
            player["board_utilization"]["peak_productive_utilization"][
                "productive_tiles"
            ],
            2,
        )
        self.assertEqual(
            player["actions_by_day"],
            [
                {
                    "day": 0,
                    "worker_actions": 3,
                    "passes": 0,
                    "pass_rate": 0.0,
                    "counts": {
                        "BUILD_PASTURE": 1,
                        "PLACE": 1,
                        "PLANT": 1,
                    },
                }
            ],
        )
        self.assertEqual(player["terminal"]["money"], 2060)


if __name__ == "__main__":
    unittest.main()
