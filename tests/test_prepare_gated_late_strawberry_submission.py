import ast
import sys
import types
import unittest
from unittest.mock import patch

from tests.test_experimental_scale_agent import scale_observation
from tools.packaging import prepare_gated_late_strawberry_submission


class PrepareGatedLateStrawberrySubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_kaggle_selects_agent(self) -> None:
        source = prepare_gated_late_strawberry_submission.build_source()
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
        aliases = [
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]

        self.assertEqual(local_imports, [])
        self.assertIn("decide_tiered", aliases)
        self.assertIn("LATE_STRAWBERRY_SELECTION_DAY", aliases)
        self.assertEqual(functions.count("agent"), 1)
        self.assertEqual(functions[-2:], ["decide", "agent"])
        code = compile(
            source,
            "submissions/gated-late-strawberry/main.py",
            "exec",
        )
        package_module = types.ModuleType("gated_late_submission_test")
        modules = {package_module.__name__: package_module}
        with patch.dict(sys.modules, modules):
            exec(code, package_module.__dict__)
        selected_callable = [
            value
            for value in package_module.__dict__.values()
            if callable(value)
        ][-1]

        self.assertIs(selected_callable, package_module.agent)
        decision = selected_callable(scale_observation())
        self.assertEqual(decision["farmer"], ["BUILD_PASTURE"])
        self.assertEqual(decision["market"].count(["HIRE"]), 5)

    def test_build_is_deterministic(self) -> None:
        self.assertEqual(
            prepare_gated_late_strawberry_submission.build_source(),
            prepare_gated_late_strawberry_submission.build_source(),
        )


if __name__ == "__main__":
    unittest.main()
