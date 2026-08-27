import unittest

from agents.future_labor_first_loss_replay_agent import (
    ACTIONS,
    SCHEDULE_PATH,
    SOURCE_PLAYER,
    SOURCE_SEED,
    agent,
)


class FutureLaborFirstLossReplayAgentTests(unittest.TestCase):
    def test_loads_complete_opponent_schedule(self) -> None:
        self.assertTrue(SCHEDULE_PATH.is_file())
        self.assertEqual(SOURCE_PLAYER, 1)
        self.assertEqual(SOURCE_SEED, 1_426_717_232)
        self.assertEqual(len(ACTIONS), 720)

    def test_returns_action_after_observation_step(self) -> None:
        self.assertEqual(agent({"step": 0}), ACTIONS[1])
        self.assertEqual(
            agent({"step": 719}),
            {"farmer": ["PASS"], "hands": [], "market": []},
        )


if __name__ == "__main__":
    unittest.main()