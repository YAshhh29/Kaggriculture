import unittest

from rl.sell_gate import (
    CASH_FLOOR,
    GATED,
    MAX_HOLD_STEPS,
    SHED_CAPACITY,
    SHED_HEADROOM,
    TERMINAL_STEP,
    SellGateState,
    gate_orders,
)


def state_at(step, *, inventory=None, money=50_000.0, shed=None):
    return {
        "step": step,
        "day": step // 24,
        "player": 0,
        "farms": [{"money": money}, {"money": money}],
        "market": {"inventory": inventory or {}, "prices": {}},
        "private": {"shed": shed or {}},
    }


def action(market):
    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": [list(o) for o in market],
    }


class SellGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = SellGateState()

    def test_saturated_market_holds_the_sale(self) -> None:
        obs = state_at(300, inventory={"WOOL": 10_060.0})
        out = gate_orders(obs, action([["SELL", "WOOL", 12]]), self.state)

        self.assertEqual(out["market"], [])

    def test_quiet_market_lets_the_sale_through(self) -> None:
        obs = state_at(300, inventory={"WOOL": 10_030.0})
        out = gate_orders(obs, action([["SELL", "WOOL", 12]]), self.state)

        self.assertEqual(out["market"], [["SELL", "WOOL", 12]])

    def test_thresholds_sit_inside_the_real_inventory_band(self) -> None:
        # The first attempt at this rule used 10,500 and never fired once,
        # because real inventory only moves through roughly 10,040-10,060.
        # Guard the calibration so that regression cannot come back.
        for item, limit in GATED.items():
            self.assertGreater(limit, 10_000.0, item)
            self.assertLess(limit, 10_100.0, item)

    def test_ungated_products_are_never_held(self) -> None:
        obs = state_at(300, inventory={"STRAWBERRY": 10_090.0})
        orders = [["SELL", "STRAWBERRY", 30]]
        out = gate_orders(obs, action(orders), self.state)

        self.assertEqual(out["market"], orders)

    def test_non_sell_orders_are_never_touched(self) -> None:
        obs = state_at(300, inventory={"MILK": 10_099.0})
        orders = [["HIRE"], ["BUY_SEED", "WHEAT", 4], ["SELL", "MILK", 9]]
        out = gate_orders(obs, action(orders), self.state)

        self.assertEqual(out["market"], [["HIRE"], ["BUY_SEED", "WHEAT", 4]])

    def test_low_cash_overrides_the_gate(self) -> None:
        obs = state_at(
            300, inventory={"MILK": 10_099.0}, money=CASH_FLOOR - 1
        )
        out = gate_orders(obs, action([["SELL", "MILK", 9]]), self.state)

        self.assertEqual(out["market"], [["SELL", "MILK", 9]])

    def test_full_shed_overrides_the_gate(self) -> None:
        nearly_full = {"MILK": SHED_CAPACITY - SHED_HEADROOM + 1}
        obs = state_at(300, inventory={"MILK": 10_099.0}, shed=nearly_full)
        out = gate_orders(obs, action([["SELL", "MILK", 9]]), self.state)

        self.assertEqual(out["market"], [["SELL", "MILK", 9]])

    def test_terminal_window_overrides_the_gate(self) -> None:
        obs = state_at(TERMINAL_STEP, inventory={"MILK": 10_099.0})
        out = gate_orders(obs, action([["SELL", "MILK", 9]]), self.state)

        self.assertEqual(out["market"], [["SELL", "MILK", 9]])

    def test_patience_runs_out_so_goods_are_never_stranded(self) -> None:
        held = state_at(300, inventory={"MILK": 10_099.0})
        self.assertEqual(
            gate_orders(held, action([["SELL", "MILK", 5]]), self.state)["market"],
            [],
        )
        later = state_at(
            300 + MAX_HOLD_STEPS, inventory={"MILK": 10_099.0}
        )
        out = gate_orders(later, action([["SELL", "MILK", 5]]), self.state)

        self.assertEqual(out["market"], [["SELL", "MILK", 5]])

    def test_recovery_clears_the_hold_clock(self) -> None:
        glutted = state_at(300, inventory={"MILK": 10_099.0})
        gate_orders(glutted, action([["SELL", "MILK", 5]]), self.state)
        self.assertIn("MILK", self.state.held_since)

        quiet = state_at(310, inventory={"MILK": 10_000.0})
        gate_orders(quiet, action([["SELL", "MILK", 5]]), self.state)

        self.assertNotIn("MILK", self.state.held_since)

    def test_new_episode_resets_the_state(self) -> None:
        glutted = state_at(300, inventory={"MILK": 10_099.0})
        gate_orders(glutted, action([["SELL", "MILK", 5]]), self.state)

        fresh = state_at(0, inventory={"MILK": 10_099.0})
        gate_orders(fresh, action([]), self.state)

        self.assertEqual(self.state.held_since, {})

    def test_baseline_action_is_not_mutated(self) -> None:
        obs = state_at(300, inventory={"MILK": 10_099.0})
        act = action([["SELL", "MILK", 5]])
        original = [list(o) for o in act["market"]]

        gate_orders(obs, act, self.state)

        self.assertEqual(act["market"], original)


if __name__ == "__main__":
    unittest.main()
