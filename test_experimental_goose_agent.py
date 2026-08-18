import ast
import unittest
from pathlib import Path

from experimental_goose_agent import agent
from test_main import observation


def goose_tile(
    *,
    consecutive_unfed: int = 0,
    fed_today: bool = False,
    fertilizer_available: bool = False,
    yield_units: int = 0,
) -> dict:
    return {
        "kind": "COOP",
        "animal": "GOOSE",
        "placed_day": 0,
        "yield_units": yield_units,
        "consecutive_unfed": consecutive_unfed,
        "fed_today": fed_today,
        "cared_today": False,
        "fertilizer_available": fertilizer_available,
        "pending_care_bonus": 0,
    }


class ExperimentalGooseAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).with_name("experimental_goose_agent.py")
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_builds_near_shed_coop_and_buys_goose_and_seeds(self) -> None:
        decision = agent(observation(money=3_000))

        self.assertEqual(decision["farmer"], ["BUILD_COOP"])
        self.assertIn(["BUY_ANIMAL", "GOOSE", 1], decision["market"])
        self.assertNotIn(["BUY_PRODUCT", "WHEAT", 1], decision["market"])
        self.assertIn(["BUY_SEED", "WHEAT", 6], decision["market"])

    def test_buys_feed_only_when_goose_is_at_escape_risk(self) -> None:
        safe = observation()
        safe["farms"][0]["tiles"][0][0] = goose_tile()
        urgent = observation()
        urgent["farms"][0]["tiles"][0][0] = goose_tile(
            consecutive_unfed=1
        )

        self.assertNotIn(
            ["BUY_PRODUCT", "WHEAT", 1],
            agent(safe)["market"],
        )
        self.assertIn(
            ["BUY_PRODUCT", "WHEAT", 1],
            agent(urgent)["market"],
        )

    def test_picks_up_and_places_purchased_goose(self) -> None:
        pickup = observation()
        pickup["farms"][0]["tiles"][0][0] = {"kind": "COOP"}
        pickup["private"]["shed"]["GOOSE"] = 1

        place = observation()
        place["farms"][0]["tiles"][0][0] = {"kind": "COOP"}
        place["private"]["inventories"][0]["GOOSE"] = 1

        self.assertEqual(agent(pickup)["farmer"], ["PICKUP", "GOOSE", 1])
        self.assertEqual(agent(place)["farmer"], ["PLACE", "GOOSE"])

    def test_repurchases_goose_for_empty_coop(self) -> None:
        state = observation(money=3_000)
        state["farms"][0]["tiles"][0][0] = {"kind": "COOP"}

        decision = agent(state)

        self.assertIn(["BUY_ANIMAL", "GOOSE", 1], decision["market"])

    def test_picks_up_feed_then_feeds_goose_at_escape_risk(self) -> None:
        pickup = observation()
        pickup["farms"][0]["tiles"][0][0] = goose_tile(
            consecutive_unfed=1
        )
        pickup["private"]["shed"]["WHEAT"] = 1

        feed = observation()
        feed["farms"][0]["tiles"][0][0] = goose_tile(
            consecutive_unfed=1
        )
        feed["private"]["inventories"][0]["WHEAT"] = 1

        self.assertEqual(agent(pickup)["farmer"], ["PICKUP", "WHEAT", 1])
        self.assertEqual(agent(feed)["farmer"], ["FEED"])

    def test_collects_fertilizer_before_full_egg_harvest(self) -> None:
        fertilizer = observation()
        fertilizer["farms"][0]["tiles"][0][0] = goose_tile(
            fed_today=True,
            fertilizer_available=True,
            yield_units=4,
        )
        eggs = observation()
        eggs["farms"][0]["tiles"][0][0] = goose_tile(
            fed_today=True,
            yield_units=4,
        )

        self.assertEqual(
            agent(fertilizer)["farmer"],
            ["COLLECT_FERTILIZER"],
        )
        self.assertEqual(agent(eggs)["farmer"], ["HARVEST"])

    def test_skips_unsellable_final_day_fertilizer(self) -> None:
        state = observation(day=29)
        state["farms"][0]["tiles"][0][0] = goose_tile(
            fed_today=True,
            fertilizer_available=True,
        )

        self.assertNotEqual(
            agent(state)["farmer"],
            ["COLLECT_FERTILIZER"],
        )

    def test_sells_eggs_and_fertilizer_from_shed(self) -> None:
        state = observation()
        state["farms"][0]["tiles"][0][0] = goose_tile(fed_today=True)
        state["private"]["shed"]["EGG"] = 4
        state["private"]["shed"]["FERTILIZER"] = 2

        market = agent(state)["market"]

        self.assertIn(["SELL", "EGG", 4], market)
        self.assertIn(["SELL", "FERTILIZER", 2], market)

    def test_goose_policy_stops_seed_buying_after_day_21(self) -> None:
        open_state = observation(day=21)
        open_state["farms"][0]["tiles"][0][0] = goose_tile(
            fed_today=True
        )
        closed_state = observation(day=22)
        closed_state["farms"][0]["tiles"][0][0] = goose_tile(
            fed_today=True
        )

        self.assertIn(
            ["BUY_SEED", "WHEAT", 6],
            agent(open_state)["market"],
        )
        self.assertNotIn(
            ["BUY_SEED", "WHEAT", 6],
            agent(closed_state)["market"],
        )


if __name__ == "__main__":
    unittest.main()