import unittest

from rl.candidate_d import (
    DEFERRAL_CUTOFF_STEP,
    FLUSH_BY_STEP,
    MARKET_I0,
    MAX_DEFER_STEPS,
    CandidateDExecutor,
)
from tests.test_experimental_scale_agent import scale_observation


def fixed_baseline(action):
    def decide(observation):
        del observation
        return {
            "farmer": list(action.get("farmer", ["PASS"])),
            "hands": [list(item) for item in action.get("hands", [])],
            "market": [list(item) for item in action.get("market", [])],
        }

    return decide


def scripted_baseline(actions_by_step, default=None):
    default = default or {"farmer": ["PASS"], "hands": [], "market": []}

    def decide(observation):
        action = actions_by_step.get(int(observation["step"]), default)
        return {
            "farmer": list(action.get("farmer", ["PASS"])),
            "hands": [list(item) for item in action.get("hands", [])],
            "market": [list(item) for item in action.get("market", [])],
        }

    return decide


def state_at(step, *, inventory=None):
    state = scale_observation(day=20, hour=0)
    state["step"] = step
    state["market"]["inventory"] = inventory or {}
    return state


class CandidateDGlutDeferralTests(unittest.TestCase):
    def test_glut_sell_is_deferred_from_this_turns_batch(self) -> None:
        baseline = fixed_baseline(
            {"farmer": ["PASS"], "hands": [], "market": [["SELL", "MELON", 5]]}
        )
        executor = CandidateDExecutor(baseline)

        decision = executor.decide(state_at(300, inventory={"MELON": 11_000}))

        self.assertEqual(decision["market"], [])

    def test_non_glut_item_is_never_deferred(self) -> None:
        baseline = fixed_baseline(
            {"farmer": ["PASS"], "hands": [], "market": [["SELL", "WHEAT", 5]]}
        )
        executor = CandidateDExecutor(baseline)

        decision = executor.decide(state_at(300, inventory={"WHEAT": 15_000}))

        self.assertEqual(decision["market"], [["SELL", "WHEAT", 5]])

    def test_glut_sell_below_threshold_is_not_deferred(self) -> None:
        baseline = fixed_baseline(
            {"farmer": ["PASS"], "hands": [], "market": [["SELL", "WOOL", 3]]}
        )
        executor = CandidateDExecutor(baseline)

        decision = executor.decide(
            state_at(300, inventory={"WOOL": MARKET_I0})
        )

        self.assertEqual(decision["market"], [["SELL", "WOOL", 3]])

    def test_deferred_quantity_flushes_once_market_recovers(self) -> None:
        actions = {
            300: {"market": [["SELL", "MELON", 5]]},
            301: {"market": []},
        }
        executor = CandidateDExecutor(scripted_baseline(actions))

        first = executor.decide(state_at(300, inventory={"MELON": 11_000}))
        second = executor.decide(state_at(301, inventory={"MELON": MARKET_I0}))

        self.assertEqual(first["market"], [])
        self.assertEqual(second["market"], [["SELL", "MELON", 5]])

    def test_flushes_at_max_defer_steps_even_if_still_glutted(self) -> None:
        actions = {300: {"market": [["SELL", "WOOL", 4]]}}
        for step in range(301, 320):
            actions[step] = {"market": []}
        executor = CandidateDExecutor(scripted_baseline(actions))

        for step in range(300, 300 + MAX_DEFER_STEPS + 1):
            decision = executor.decide(
                state_at(step, inventory={"WOOL": 20_000})
            )
        # By step 300 + MAX_DEFER_STEPS the hold must have been flushed,
        # regardless of the market still being glutted.
        self.assertEqual(decision["market"], [["SELL", "WOOL", 4]])

    def test_no_quantity_is_lost_across_a_long_hold(self) -> None:
        actions = {300: {"market": [["SELL", "MELON", 7]]}}
        for step in range(301, 300 + MAX_DEFER_STEPS + 2):
            actions[step] = {"market": []}
        executor = CandidateDExecutor(scripted_baseline(actions))

        total_sold = 0
        for step in range(300, 300 + MAX_DEFER_STEPS + 2):
            decision = executor.decide(
                state_at(step, inventory={"MELON": 20_000})
            )
            for order in decision["market"]:
                if order[0] == "SELL" and order[1] == "MELON":
                    total_sold += order[2]

        self.assertEqual(total_sold, 7)

    def test_pending_quantity_merges_with_a_fresh_sell_of_the_same_item(
        self,
    ) -> None:
        actions = {
            300: {"market": [["SELL", "WOOL", 4]]},
            301: {"market": [["SELL", "WOOL", 2]]},
        }
        executor = CandidateDExecutor(scripted_baseline(actions))

        executor.decide(state_at(300, inventory={"WOOL": 20_000}))
        second = executor.decide(state_at(301, inventory={"WOOL": MARKET_I0}))

        self.assertEqual(second["market"], [["SELL", "WOOL", 6]])

    def test_everything_flushes_at_the_deferral_cutoff_step(self) -> None:
        actions = {
            300: {"market": [["SELL", "MELON", 5]]},
            DEFERRAL_CUTOFF_STEP: {"market": []},
        }
        executor = CandidateDExecutor(scripted_baseline(actions))

        executor.decide(state_at(300, inventory={"MELON": 20_000}))
        decision = executor.decide(
            state_at(DEFERRAL_CUTOFF_STEP, inventory={"MELON": 20_000})
        )

        self.assertEqual(decision["market"], [["SELL", "MELON", 5]])

    def test_nothing_new_is_deferred_at_or_after_the_cutoff_step(self) -> None:
        baseline = fixed_baseline(
            {"farmer": ["PASS"], "hands": [], "market": [["SELL", "WOOL", 3]]}
        )
        executor = CandidateDExecutor(baseline)

        decision = executor.decide(
            state_at(DEFERRAL_CUTOFF_STEP, inventory={"WOOL": 20_000})
        )

        self.assertEqual(decision["market"], [["SELL", "WOOL", 3]])

    def test_market_order_cap_is_respected_after_a_flush(self) -> None:
        many_orders = [["SELL", "WHEAT", 1] for _ in range(9)]
        actions = {
            300: {"market": [*many_orders, ["SELL", "MELON", 5]]},
            301: {"market": many_orders},
        }
        executor = CandidateDExecutor(scripted_baseline(actions))

        executor.decide(state_at(300, inventory={"MELON": 20_000}))
        decision = executor.decide(
            state_at(301, inventory={"MELON": MARKET_I0})
        )

        self.assertLessEqual(len(decision["market"]), 10)

    def test_episode_reset_clears_state_between_games(self) -> None:
        actions = {300: {"market": [["SELL", "MELON", 5]]}}
        actions[0] = {"market": []}
        executor = CandidateDExecutor(scripted_baseline(actions))
        executor.decide(state_at(300, inventory={"MELON": 20_000}))

        # A fresh episode (step drops back to 0) must not carry the
        # previous game's deferred quantity forward. Using a
        # now-unglutted inventory at step 0 means the old pending MELON
        # would flush (and leak into this decision) if state were not
        # actually cleared -- an empty result here is only guaranteed by
        # a real reset, not a coincidence of the flush conditions.
        decision = executor.decide(
            state_at(0, inventory={"MELON": MARKET_I0})
        )

        self.assertEqual(decision["market"], [])

    def test_players_are_tracked_independently(self) -> None:
        baseline = fixed_baseline(
            {"farmer": ["PASS"], "hands": [], "market": [["SELL", "MELON", 5]]}
        )
        executor = CandidateDExecutor(baseline)

        state0 = state_at(300, inventory={"MELON": 20_000})
        state0["player"] = 0
        state1 = state_at(300, inventory={"MELON": 20_000})
        state1["player"] = 1

        decision0 = executor.decide(state0)
        decision1 = executor.decide(state1)

        self.assertEqual(decision0["market"], [])
        self.assertEqual(decision1["market"], [])

    def test_flush_by_step_forces_release_even_within_the_defer_window(
        self,
    ) -> None:
        actions = {
            FLUSH_BY_STEP - 1: {"market": [["SELL", "MELON", 5]]},
            FLUSH_BY_STEP: {"market": []},
        }
        executor = CandidateDExecutor(scripted_baseline(actions))

        executor.decide(
            state_at(FLUSH_BY_STEP - 1, inventory={"MELON": 20_000})
        )
        decision = executor.decide(
            state_at(FLUSH_BY_STEP, inventory={"MELON": 20_000})
        )

        self.assertEqual(decision["market"], [["SELL", "MELON", 5]])


if __name__ == "__main__":
    unittest.main()
