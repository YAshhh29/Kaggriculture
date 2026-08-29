import ast
import sys
import types
import unittest
from unittest.mock import patch

from tools.packaging import prepare_tiered_fertilizer_submission
from tests.test_experimental_scale_agent import scale_observation


class PrepareTieredFertilizerSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_ends_with_agent(self) -> None:
        source = prepare_tiered_fertilizer_submission.build_source()
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
        self.assertIn("decide_idle", aliases)
        self.assertEqual(aliases.count("SELECTION_DAY"), 1)
        self.assertIn("CROP_SERVICE_SELECTION_DAY", aliases)
        self.assertIn("TIERED_SELECTION_DAY", aliases)
        self.assertEqual(functions.count("agent"), 1)
        self.assertEqual(functions[-2:], ["decide", "agent"])
        code = compile(
            source,
            "submissions/tiered-fertilizer/main.py",
            "exec",
        )
        package_module = types.ModuleType("tiered_submission_test")
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

    def test_source_paths_are_readable_python_or_model_files(self) -> None:
        for path in prepare_tiered_fertilizer_submission.SOURCE_PATHS:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                if path.suffix == ".py":
                    ast.parse(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
