import ast
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.packaging import prepare_future_labor_submission


class PrepareFutureLaborSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_ends_with_agent(self) -> None:
        source = prepare_future_labor_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith(("agents.", "policies.", "core."))
        ]
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(local_imports, [])
        self.assertEqual(functions[-2:], ["decide", "agent"])
        compile(source, "submissions/future-labor/main.py", "exec")

    def test_main_refuses_to_overwrite_submitted_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "main.py"
            manifest = root / "manifest.json"
            output.write_text("frozen", encoding="utf-8")
            package_hash = hashlib.sha256(output.read_bytes()).hexdigest()
            manifest.write_text(
                json.dumps(
                    {
                        "kaggle": {
                            "submission_id": (
                                prepare_future_labor_submission.FROZEN_SUBMISSION_ID
                            )
                        }
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.object(
                    prepare_future_labor_submission,
                    "OUTPUT",
                    output,
                ),
                patch.object(
                    prepare_future_labor_submission,
                    "MANIFEST",
                    manifest,
                ),
                patch.object(
                    prepare_future_labor_submission,
                    "FROZEN_SHA256",
                    package_hash,
                ),
                self.assertRaisesRegex(SystemExit, "immutable"),
            ):
                prepare_future_labor_submission.main()

    def test_main_refuses_to_rebuild_missing_frozen_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "main.py"
            manifest = root / "manifest.json"
            for missing in (output, manifest):
                with self.subTest(missing=missing.name):
                    output.write_text("frozen", encoding="utf-8")
                    manifest.write_text("{}", encoding="utf-8")
                    missing.unlink()
                    with (
                        patch.object(
                            prepare_future_labor_submission,
                            "OUTPUT",
                            output,
                        ),
                        patch.object(
                            prepare_future_labor_submission,
                            "MANIFEST",
                            manifest,
                        ),
                        self.assertRaisesRegex(SystemExit, "immutable"),
                    ):
                        prepare_future_labor_submission.main()


if __name__ == "__main__":
    unittest.main()