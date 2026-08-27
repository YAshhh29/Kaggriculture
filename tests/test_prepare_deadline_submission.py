import ast
import unittest

from tools.packaging import prepare_deadline_submission


class PrepareDeadlineSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone(self) -> None:
        source = prepare_deadline_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith(
                ("experimental_", "agents.", "policies.", "core.")
            )
        ]
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(local_imports, [])
        self.assertEqual(functions[-2:], ["decide", "agent"])
        compile(source, "submissions/deadline/main.py", "exec")


if __name__ == "__main__":
    unittest.main()
