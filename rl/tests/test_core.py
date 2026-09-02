import hashlib
import unittest
from pathlib import Path

from agents.experimental_distilled_calendar_agent import decide as calendar
from benchmark import load_agent_callable
from rl.action_space import (
    ACTION_HEAD_SIZES,
    KEEP_CALENDAR,
    LaborDecision,
    ResidualAction,
)
from rl.features import STATE_FEATURE_NAMES, encode_state
from rl.policy import KeepCalendarPolicy
from rl.runtime import UnsupportedResidualAction, build_residual_agent
from tests.test_experimental_scale_agent import scale_observation


class StaticPolicy:
    def __init__(self, action: ResidualAction) -> None:
        self.action = action

    def select_action(self, state):
        del state
        return self.action


class RlCoreTests(unittest.TestCase):
    def test_keep_action_has_one_index_per_policy_head(self) -> None:
        self.assertTrue(KEEP_CALENDAR.is_keep_calendar)
        self.assertEqual(KEEP_CALENDAR.head_indices(), (0, 0, 0, 0, 0, 0))
        self.assertEqual(len(ACTION_HEAD_SIZES), 6)

    def test_state_encoding_is_stable_and_named(self) -> None:
        observation = scale_observation(day=6, hour=12)
        observation["step"] = 156
        baseline = calendar(observation)

        first = encode_state(observation, baseline)
        second = encode_state(observation, baseline)

        self.assertEqual(first, second)
        self.assertEqual(first.names, STATE_FEATURE_NAMES)
        self.assertEqual(len(first.names), len(set(first.names)))
        self.assertEqual(first.as_dict()["day_fraction"], 6 / 29)

    def test_keep_policy_exactly_preserves_calendar_action(self) -> None:
        observation = scale_observation(day=10, hour=4)
        observation["step"] = 244
        expected = calendar(observation)
        agent = build_residual_agent(KeepCalendarPolicy())

        actual = agent(observation)

        self.assertEqual(actual, expected)
        self.assertIsNot(actual, expected)

    def test_keep_policy_matches_frozen_package(self) -> None:
        root = Path(__file__).resolve().parents[2]
        package = root / "submissions" / "distilled-calendar" / "main.py"
        digest = hashlib.sha256(package.read_bytes()).hexdigest()
        packaged = load_agent_callable(package)
        agent = build_residual_agent(KeepCalendarPolicy())

        self.assertEqual(
            digest,
            "43d24a73c346c7687e574de69b8ffaf0ef959b34649e4e333a70f3f6c44b0976",
        )
        for step in range(720):
            observation = scale_observation(
                day=step // 24,
                hour=step % 24,
            )
            observation["step"] = step
            self.assertEqual(agent(observation), packaged(observation))

    def test_unimplemented_residual_fails_closed(self) -> None:
        observation = scale_observation(day=10, hour=4)
        observation["step"] = 244
        policy = StaticPolicy(
            ResidualAction(labor=LaborDecision.ADD_ONE)
        )
        agent = build_residual_agent(policy)

        with self.assertRaises(UnsupportedResidualAction):
            agent(observation)


if __name__ == "__main__":
    unittest.main()