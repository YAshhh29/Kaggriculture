import ast
import unittest

import prepare_adaptive_submission


class PrepareAdaptiveSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_ends_with_agent(self) -> None:
        source = prepare_adaptive_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module in prepare_adaptive_submission.LOCAL_MODULES
        ]
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]
        aliases = [
            node
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "decide_premium"
                for target in node.targets
            )
        ]

        self.assertEqual(local_imports, [])
        self.assertEqual(len(aliases), 1)
        self.assertEqual(functions[-1], "agent")
        compile(source, "submission-adaptive/main.py", "exec")


if __name__ == "__main__":
    unittest.main()
