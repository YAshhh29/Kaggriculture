import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import prepare_scale_submission


class PrepareScaleSubmissionTests(unittest.TestCase):
    def test_built_file_ends_with_scale_agent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "main.py"
            manifest = Path(directory) / "manifest.json"
            with (
                patch.object(prepare_scale_submission, "OUTPUT", output),
                patch.object(prepare_scale_submission, "MANIFEST", manifest),
            ):
                prepare_scale_submission.main()

            module = ast.parse(output.read_text(encoding="utf-8"))
            functions = [
                node.name
                for node in module.body
                if isinstance(node, ast.FunctionDef)
            ]
            assignments = [
                node
                for node in module.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "decide_wheat"
                    for target in node.targets
                )
            ]
            function_names = set(functions)

        self.assertEqual(functions[-1], "agent")
        self.assertEqual(len(assignments), 1)
        self.assertIn("_scale_market_orders", function_names)
        self.assertIn("_scale_hire_orders", function_names)
        self.assertNotIn("_service_action", function_names)


if __name__ == "__main__":
    unittest.main()