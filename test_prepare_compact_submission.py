import ast
import unittest

import prepare_compact_submission


class PrepareCompactSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone(self) -> None:
        source = prepare_compact_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("experimental_")
        ]
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(local_imports, [])
        self.assertEqual(functions[-2:], ["decide", "agent"])
        compile(source, "submission-compact/main.py", "exec")


if __name__ == "__main__":
    unittest.main()
