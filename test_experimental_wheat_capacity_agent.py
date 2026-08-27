import unittest
from unittest.mock import patch

from policies.capacity_policy import ARM_WHEAT
from agents.experimental_wheat_capacity_agent import decide
from test_experimental_scale_agent import scale_observation


class ExperimentalWheatCapacityAgentTests(unittest.TestCase):
    def test_uses_fixed_wheat_capacity_arm(self) -> None:
        state = scale_observation(day=4)

        with patch(
            "agents.experimental_wheat_capacity_agent.decide_capacity_arm"
        ) as capacity:
            decide(state)

        self.assertEqual(capacity.call_args.args[1], ARM_WHEAT)


if __name__ == "__main__":
    unittest.main()
