import unittest

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS


class ExperimentalDeadlineTaperedWheatAgentTests(unittest.TestCase):
    def test_preserves_final_harvest_crew_before_liquidation(self) -> None:
        self.assertEqual(len(DEADLINE_HAND_TARGETS), 30)
        self.assertEqual(
            DEADLINE_HAND_TARGETS[23:],
            (10, 10, 10, 10, 8, 4, 3),
        )


if __name__ == "__main__":
    unittest.main()
