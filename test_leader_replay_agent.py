import ast
import unittest
from pathlib import Path

from agents.leader_replay_agent import ACTIONS, agent


class LeaderReplayAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).parent / "agents" / "leader_replay_agent.py"
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_returns_action_from_following_replay_record(self) -> None:
        self.assertEqual(agent({"step": 0}), ACTIONS[1])
        self.assertEqual(agent({"step": 718}), ACTIONS[719])


if __name__ == "__main__":
    unittest.main()