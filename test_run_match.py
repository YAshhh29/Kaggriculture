import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from run_match import parse_args


class RunMatchTests(unittest.TestCase):
    def test_accepts_an_explicit_agent_path(self) -> None:
        agent = Path("experimental_zoned_agent.py")
        with patch.object(
            sys,
            "argv",
            ["run_match.py", "--agent", str(agent)],
        ):
            args = parse_args()

        self.assertEqual(args.agent, agent)


if __name__ == "__main__":
    unittest.main()