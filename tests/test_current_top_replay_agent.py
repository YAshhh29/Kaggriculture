import ast
import unittest
from pathlib import Path

from agents.current_top_replay_agent import ACTIONS, SOURCE_SEED, agent


class CurrentTopReplayAgentTests(unittest.TestCase):
    def test_agent_is_last_function_for_file_loader(self) -> None:
        path = Path(__file__).resolve().parents[1] / "agents" / "current_top_replay_agent.py"
        module = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(functions[-1], "agent")

    def test_replays_current_rank_one_actions_and_seed(self) -> None:
        self.assertEqual(SOURCE_SEED, 1_192_301_511)
        self.assertEqual(agent({"step": 0}), ACTIONS[1])
        self.assertEqual(agent({"step": 718}), ACTIONS[719])


if __name__ == "__main__":
    unittest.main()
