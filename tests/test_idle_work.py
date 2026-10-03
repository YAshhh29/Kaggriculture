import unittest

from candidates.idle_work import build_idle_work_agent
from tests.test_experimental_scale_agent import scale_observation


def fixed(action):
    def decide(observation):
        del observation
        return {
            "farmer": list(action.get("farmer", ["PASS"])),
            "hands": [list(h) for h in action.get("hands", [])],
            "market": [list(o) for o in action.get("market", [])],
        }

    return decide


def wheat_tile(day, *, age=2, watered=False, fertilized=-1, yield_units=0):
    return {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": day - age,
        "watered_today": watered,
        "fertilized_until_day": fertilized,
        "yield_units": yield_units,
        "consecutive_unwatered": 0,
    }


def state(*, day=10, farmer=(0, 0), tile=None, inventory=None, shed=None):
    obs = scale_observation(day=day)
    obs["step"] = day * 24
    farm = obs["farms"][0]
    farm["farmer"] = list(farmer)
    farm["hands"] = []
    if tile is not None:
        farm["tiles"][farmer[1]][farmer[0]] = tile
    obs["private"]["inventories"] = [inventory or {}]
    obs["private"]["shed"] = shed or {}
    return obs


class IdleWorkTests(unittest.TestCase):
    def test_only_pass_turns_are_replaced(self) -> None:
        obs = state(tile=wheat_tile(10), inventory={"FERTILIZER": 1})
        agent = build_idle_work_agent(fixed({"farmer": ["HARVEST"]}))

        self.assertEqual(agent(obs)["farmer"], ["HARVEST"])

    def test_idle_worker_fertilizes_wheat_when_holding_fertilizer(self) -> None:
        obs = state(tile=wheat_tile(10), inventory={"FERTILIZER": 1})
        agent = build_idle_work_agent(fixed({"farmer": ["PASS"]}))

        self.assertEqual(agent(obs)["farmer"], ["FERTILIZE"])

    def test_no_fertilizer_held_means_no_fertilize(self) -> None:
        obs = state(tile=wheat_tile(10), inventory={})
        agent = build_idle_work_agent(fixed({"farmer": ["PASS"]}))

        self.assertNotEqual(agent(obs)["farmer"], ["FERTILIZE"])

    def test_already_fertilized_tile_is_left_alone(self) -> None:
        obs = state(
            tile=wheat_tile(10, fertilized=12), inventory={"FERTILIZER": 1}
        )
        agent = build_idle_work_agent(fixed({"farmer": ["PASS"]}))

        self.assertNotEqual(agent(obs)["farmer"], ["FERTILIZE"])

    def test_idle_worker_waters_a_dry_plant_in_window(self) -> None:
        obs = state(tile=wheat_tile(10, age=3), inventory={})
        agent = build_idle_work_agent(fixed({"farmer": ["PASS"]}))

        self.assertEqual(agent(obs)["farmer"], ["WATER"])

    def test_watered_plant_is_not_rewatered(self) -> None:
        obs = state(tile=wheat_tile(10, age=3, watered=True), inventory={})
        agent = build_idle_work_agent(fixed({"farmer": ["PASS"]}))

        self.assertNotEqual(agent(obs)["farmer"], ["WATER"])

    def test_idle_worker_on_shed_tile_restocks_fertilizer(self) -> None:
        obs = state(farmer=(4, 4), inventory={}, shed={"FERTILIZER": 3})
        agent = build_idle_work_agent(fixed({"farmer": ["PASS"]}))

        self.assertEqual(agent(obs)["farmer"], ["PICKUP", "FERTILIZER", 1])

    def test_no_restock_when_shed_is_empty(self) -> None:
        obs = state(farmer=(4, 4), inventory={}, shed={})
        agent = build_idle_work_agent(fixed({"farmer": ["PASS"]}))

        self.assertEqual(agent(obs)["farmer"], ["PASS"])

    def test_market_orders_are_never_touched(self) -> None:
        obs = state(tile=wheat_tile(10), inventory={"FERTILIZER": 1})
        orders = [["SELL", "WHEAT", 5], ["HIRE"]]
        agent = build_idle_work_agent(
            fixed({"farmer": ["PASS"], "market": orders})
        )

        self.assertEqual(agent(obs)["market"], orders)

    def test_flags_disable_each_rule(self) -> None:
        obs = state(tile=wheat_tile(10), inventory={"FERTILIZER": 1})
        agent = build_idle_work_agent(
            fixed({"farmer": ["PASS"]}),
            fertilize=False,
            water=False,
            restock=False,
        )

        self.assertEqual(agent(obs)["farmer"], ["PASS"])


if __name__ == "__main__":
    unittest.main()
