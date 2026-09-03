import ast
import sys
import types
import unittest
from unittest.mock import patch

from tests.test_experimental_scale_agent import scale_observation
from tools.packaging import prepare_calendar_recovery_submission


class PrepareCalendarRecoverySubmissionTests(unittest.TestCase):
    def test_build_is_standalone_and_exposes_agent(self) -> None:
        source = prepare_calendar_recovery_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith(
                ("agents.", "policies.", "core.", "rl.")
            )
        ]
        function_names = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(local_imports, [])
        self.assertIn("calendar_decide", function_names)
        self.assertIn("agent", function_names)
        code = compile(
            source,
            "submissions/candidate-a(calendar recovery first attempt)"
            "/main.py",
            "exec",
        )
        package_module = types.ModuleType("calendar_recovery_submission_test")
        modules = {package_module.__name__: package_module}
        with patch.dict(sys.modules, modules):
            exec(code, package_module.__dict__)
        decision = package_module.agent(scale_observation())
        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_manifest_matches_built_package(self) -> None:
        prepare_calendar_recovery_submission.main()
        package = prepare_calendar_recovery_submission.OUTPUT.read_text(
            encoding="utf-8"
        )
        manifest = prepare_calendar_recovery_submission.MANIFEST.read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            package,
            prepare_calendar_recovery_submission.build_source(),
        )
        self.assertIn("Crop Dusta public calendar", manifest)


if __name__ == "__main__":
    unittest.main()
