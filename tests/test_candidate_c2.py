import unittest

from candidates.candidate_c import agent as candidate_c1
from candidates.candidate_c2 import (
    ELITE_GIULIO,
    ROUTES,
    agent,
    build_candidate_c2_agent,
)
from tests.test_experimental_scale_agent import scale_observation


class CandidateC2Tests(unittest.TestCase):
    def test_default_route_is_the_giulio_clone(self) -> None:
        state = scale_observation(day=0, hour=0)
        state["step"] = 0

        self.assertEqual(agent(state), ELITE_GIULIO.decide(state))

    def test_ships_with_giulio_first_and_calendar_second(self) -> None:
        self.assertEqual(len(ROUTES), 2)
        self.assertEqual(ROUTES[0].name, "elite_giulio")
        self.assertEqual(ROUTES[1].name, "calendar")
        self.assertFalse(ROUTES[0].reentrant)
        self.assertFalse(ROUTES[1].reentrant)

    def test_differs_from_candidate_c1(self) -> None:
        # The whole point of a second variant is that it is a genuinely
        # different programme. Two variants that agreed everywhere would
        # be indistinguishable against live rating noise and would waste a
        # submission slot -- see this module's docstring.
        differing = 0
        for step in range(0, 400, 17):
            state = scale_observation(day=step // 24, hour=step % 24)
            state["step"] = step
            if agent(state) != candidate_c1(state):
                differing += 1

        self.assertGreater(differing, 0)

    def test_build_is_independent_per_call(self) -> None:
        state = scale_observation(day=0, hour=0)
        state["step"] = 0

        first = build_candidate_c2_agent()
        second = build_candidate_c2_agent()

        self.assertEqual(first(state), second(state))


if __name__ == "__main__":
    unittest.main()
