import unittest

from agents.experimental_peak_workforce_agent import (
    PEAK_HAND_DAYS,
    PEAK_HAND_TARGETS,
)


class ExperimentalPeakWorkforceAgentTests(unittest.TestCase):
    def test_adds_one_hand_only_on_replay_peak_days(self) -> None:
        self.assertEqual(
            {
                day
                for day, target in enumerate(PEAK_HAND_TARGETS)
                if target == 13
            },
            set(PEAK_HAND_DAYS),
        )


if __name__ == "__main__":
    unittest.main()
