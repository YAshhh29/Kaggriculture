import ast
import unittest

import prepare_lifecycle_submission


class PrepareLifecycleSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_ends_with_agent(self) -> None:
        source = prepare_lifecycle_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module in prepare_lifecycle_submission.LOCAL_MODULES
        ]
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(local_imports, [])
        self.assertEqual(functions[-1], "agent")


if __name__ == "__main__":
    unittest.main()