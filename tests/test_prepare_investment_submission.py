import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.packaging import prepare_investment_submission
from tools.packaging import prepare_scale_submission


class PrepareInvestmentSubmissionTests(unittest.TestCase):
    def test_built_file_ends_with_investment_agent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scale_output = root / "scale.py"
            scale_manifest = root / "scale-manifest.json"
            output = root / "main.py"
            manifest = root / "manifest.json"
            with (
                patch.object(prepare_scale_submission, "OUTPUT", scale_output),
                patch.object(
                    prepare_scale_submission,
                    "MANIFEST",
                    scale_manifest,
                ),
                patch.object(prepare_investment_submission, "OUTPUT", output),
                patch.object(
                    prepare_investment_submission,
                    "MANIFEST",
                    manifest,
                ),
            ):
                prepare_investment_submission.main()

            module = ast.parse(output.read_text(encoding="utf-8"))
            functions = [
                node.name
                for node in module.body
                if isinstance(node, ast.FunctionDef)
            ]

        self.assertEqual(functions[-1], "agent")


if __name__ == "__main__":
    unittest.main()