import unittest

from agents.experimental_guarded_colocated_crop_service_agent import (
    _CROP_SERVICE_CHOICES,
    _crop_service_selected,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalGuardedColocatedCropServiceAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _CROP_SERVICE_CHOICES.clear()

    def test_selects_service_only_below_fertilizer_value_guard(self) -> None:
        supported = scale_observation(day=6)
        supported["market"]["prices"]["FERTILIZER"] = 96
        unsupported = scale_observation(day=6)
        unsupported["player"] = 1
        unsupported["market"]["prices"]["FERTILIZER"] = 97

        self.assertTrue(_crop_service_selected(supported))
        self.assertFalse(_crop_service_selected(unsupported))

    def test_service_choice_locks_for_episode(self) -> None:
        state = scale_observation(day=6)
        state["market"]["prices"]["FERTILIZER"] = 96

        self.assertTrue(_crop_service_selected(state))
        state["day"] = 7
        state["market"]["prices"]["FERTILIZER"] = 100
        self.assertTrue(_crop_service_selected(state))


if __name__ == "__main__":
    unittest.main()