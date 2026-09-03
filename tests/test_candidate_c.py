import unittest

from rl.candidate_b import agent as candidate_b
from rl.candidate_c import (
    CandidateCExecutor,
    RouteExpert,
    ROUTES,
    agent,
    build_candidate_c_agent,
)
from tests.test_experimental_scale_agent import scale_observation


def stub_route(name: str, *, reentrant: bool) -> RouteExpert:
    def decide(observation):
        del observation
        return {"farmer": [name], "hands": [], "market": []}

    return RouteExpert(name=name, decide=decide, reentrant=reentrant)


class CandidateCTests(unittest.TestCase):
    def test_shipped_config_matches_candidate_b_exactly(self) -> None:
        # Only one validated route exists; Candidate C must not diverge
        # from it until a second route is actually wired in.
        state = scale_observation(day=0, hour=0)
        state["step"] = 0

        self.assertEqual(agent(state), candidate_b(state))

    def test_ships_with_exactly_one_route_today(self) -> None:
        self.assertEqual(len(ROUTES), 1)
        self.assertEqual(ROUTES[0].name, "calendar")
        self.assertFalse(ROUTES[0].reentrant)

    def test_commits_once_and_ignores_later_signal_changes(self) -> None:
        # A synthetic selector that would flip every step must not change
        # the executor's committed route: hysteresis is unconditional.
        routes = (
            stub_route("first", reentrant=True),
            stub_route("second", reentrant=True),
        )
        calls = {"count": 0}

        def alternating_select(observation, candidates):
            del observation
            calls["count"] += 1
            return candidates[calls["count"] % 2].name

        executor = CandidateCExecutor(routes=routes)
        executor._select = alternating_select  # test seam, not public API

        state = scale_observation(day=0, hour=0)
        decisions = []
        for step in range(4):
            state["step"] = step
            decisions.append(executor.decide(state)["farmer"][0])

        self.assertEqual(len(set(decisions)), 1)

    def test_non_reentrant_route_cannot_be_selected_after_step_zero(
        self,
    ) -> None:
        routes = (stub_route("scripted", reentrant=False),)

        def select_late(observation, candidates):
            del observation
            return candidates[0].name

        executor = CandidateCExecutor(routes=routes)
        executor._select = select_late

        state = scale_observation(day=0, hour=0)
        state["step"] = 5

        with self.assertRaises(ValueError):
            executor.decide(state)

    def test_non_reentrant_route_is_fine_at_step_zero(self) -> None:
        routes = (stub_route("scripted", reentrant=False),)
        executor = CandidateCExecutor(routes=routes)

        state = scale_observation(day=0, hour=0)
        state["step"] = 0

        decision = executor.decide(state)

        self.assertEqual(decision["farmer"], ["scripted"])

    def test_episode_reset_allows_a_fresh_commitment(self) -> None:
        routes = (
            stub_route("first", reentrant=True),
            stub_route("second", reentrant=True),
        )
        selection = {"name": "first"}

        def select(observation, candidates):
            del observation, candidates
            return selection["name"]

        executor = CandidateCExecutor(routes=routes)
        executor._select = select

        state = scale_observation(day=0, hour=0)
        state["step"] = 0
        first_episode = executor.decide(state)
        self.assertEqual(first_episode["farmer"], ["first"])

        # A later step in the same episode ignores the new selection signal.
        selection["name"] = "second"
        state["step"] = 1
        still_first = executor.decide(state)
        self.assertEqual(still_first["farmer"], ["first"])

        # step == 0 again signals a new episode: fresh commitment allowed.
        state["step"] = 0
        second_episode = executor.decide(state)
        self.assertEqual(second_episode["farmer"], ["second"])

    def test_unknown_selected_route_raises(self) -> None:
        routes = (stub_route("only", reentrant=True),)

        def select_missing(observation, candidates):
            del observation, candidates
            return "does-not-exist"

        executor = CandidateCExecutor(routes=routes)
        executor._select = select_missing

        state = scale_observation(day=0, hour=0)
        state["step"] = 0

        with self.assertRaises(ValueError):
            executor.decide(state)

    def test_rejects_empty_route_set(self) -> None:
        with self.assertRaises(ValueError):
            CandidateCExecutor(routes=())

    def test_build_candidate_c_agent_is_independent_per_call(self) -> None:
        # Two separately built agents must not share commitment state.
        routes = (
            stub_route("first", reentrant=True),
            stub_route("second", reentrant=True),
        )
        agent_a = build_candidate_c_agent(routes=routes)
        agent_b = build_candidate_c_agent(routes=routes)

        state = scale_observation(day=0, hour=0)
        state["step"] = 0
        decision_a = agent_a(state)
        decision_b = agent_b(state)

        self.assertEqual(decision_a["farmer"], decision_b["farmer"])


if __name__ == "__main__":
    unittest.main()
