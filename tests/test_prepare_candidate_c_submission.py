import ast
import sys
import types
import unittest
from unittest.mock import patch

from tests.test_experimental_scale_agent import scale_observation
from tools.packaging import prepare_candidate_c_submission


class PrepareCandidateCSubmissionTests(unittest.TestCase):
    def test_build_is_standalone_and_exposes_agent(self) -> None:
        source = prepare_candidate_c_submission.build_source()
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
        assigned_names = [
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]

        self.assertEqual(local_imports, [])
        self.assertIn("elite_pasture_route", assigned_names)
        self.assertIn("calendar_route", assigned_names)
        self.assertIn("agent", assigned_names)
        self.assertEqual(module.body[-1].targets[0].id, "agent")
        code = compile(
            source,
            "submissions/candidate-c/main.py",
            "exec",
        )
        package_module = types.ModuleType("candidate_c_submission_test")
        modules = {package_module.__name__: package_module}
        with patch.dict(sys.modules, modules):
            exec(code, package_module.__dict__)
        decision = package_module.agent(scale_observation())
        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_manifest_matches_built_package(self) -> None:
        prepare_candidate_c_submission.main()
        package = prepare_candidate_c_submission.OUTPUT.read_text(
            encoding="utf-8"
        )
        manifest = prepare_candidate_c_submission.MANIFEST.read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            package,
            prepare_candidate_c_submission.build_source(),
        )
        self.assertIn("fog flower", manifest)


if __name__ == "__main__":
    unittest.main()
