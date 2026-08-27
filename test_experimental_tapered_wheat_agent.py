import unittest

from agents.experimental_tapered_wheat_agent import TAPERED_HAND_TARGETS


class ExperimentalTaperedWheatAgentTests(unittest.TestCase):
    def test_late_hiring_tracks_observed_workload(self) -> None:
        self.assertEqual(len(TAPERED_HAND_TARGETS), 30)
        self.assertEqual(
            TAPERED_HAND_TARGETS[23:],
            (10, 9, 8, 6, 5, 3, 3),
        )


if __name__ == "__main__":
    unittest.main()
