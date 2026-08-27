import ast
import unittest

from tools.packaging.prepare_center_out_submission import (
    LOCAL_MODULES,
    build_source,
)


class PrepareCenterOutSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_ends_with_agent(self) -> None:
        source = build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (
                node.module in LOCAL_MODULES
                or node.module.startswith(("agents.", "policies.", "core."))
            )
        ]
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]

        self.assertEqual(local_imports, [])
        self.assertEqual(functions[-1], "agent")
        compile(source, "submission-center-out/main.py", "exec")


if __name__ == "__main__":
    unittest.main()