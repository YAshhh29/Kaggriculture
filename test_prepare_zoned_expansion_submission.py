import ast
import unittest

from tools.packaging import prepare_zoned_expansion_submission


class PrepareZonedExpansionSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_ends_with_expansion_agent(self) -> None:
        source = prepare_zoned_expansion_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module
            in prepare_zoned_expansion_submission.LOCAL_MODULES
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