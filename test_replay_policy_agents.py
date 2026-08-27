import unittest

import agents.current_rank2_replay_agent as current_rank2_replay_agent
import agents.top_holdout_replay_agent as top_holdout_replay_agent


class ReplayPolicyAgentTests(unittest.TestCase):
    def test_rank_two_replay_source(self) -> None:
        self.assertEqual(current_rank2_replay_agent.SOURCE_PLAYER, 1)
        self.assertEqual(current_rank2_replay_agent.SOURCE_SEED, 1_192_301_511)
        self.assertEqual(
            current_rank2_replay_agent.agent({"step": 0}),
            current_rank2_replay_agent.ACTIONS[1],
        )

    def test_holdout_replay_source(self) -> None:
        self.assertEqual(top_holdout_replay_agent.SOURCE_PLAYER, 0)
        self.assertEqual(top_holdout_replay_agent.SOURCE_SEED, 1_002_702_470)
        self.assertEqual(
            top_holdout_replay_agent.agent({"step": 718}),
            top_holdout_replay_agent.ACTIONS[719],
        )


if __name__ == "__main__":
    unittest.main()
