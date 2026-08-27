import ast
import unittest

from tools.packaging import prepare_learned_service_submission


class PrepareLearnedServiceSubmissionTests(unittest.TestCase):
    def test_built_source_is_standalone_and_ends_with_agent(self) -> None:
        source = prepare_learned_service_submission.build_source()
        module = ast.parse(source)
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (
                node.module.startswith("experimental_")
                or node.module
                in {"learned_service_model", "macro_policy", "service_policy"}
            )
        ]
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]
        assignments = {
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }

        self.assertEqual(local_imports, [])
        self.assertIn("SERVICE_MODEL", assignments)
        self.assertEqual(functions[-2:], ["decide", "agent"])
        compile(source, "submission-learned-service/main.py", "exec")


if __name__ == "__main__":
    unittest.main()
