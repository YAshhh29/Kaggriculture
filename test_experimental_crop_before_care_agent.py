import unittest
from unittest.mock import patch

from agents.experimental_crop_before_care_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalCropBeforeCareAgentTests(unittest.TestCase):
    def test_preserves_collection_but_defers_care(self) -> None:
        with patch(
            "agents.experimental_crop_before_care_agent.decide_premium"
        ) as premium:
            decide(scale_observation(day=12))

        self.assertTrue(
            premium.call_args.kwargs["crops_before_care_only"]
        )
        self.assertTrue(
            premium.call_args.kwargs["plant_before_care"]
        )
        self.assertTrue(
            premium.call_args.kwargs["reserve_seeds_per_quadrant"]
        )


if __name__ == "__main__":
    unittest.main()
