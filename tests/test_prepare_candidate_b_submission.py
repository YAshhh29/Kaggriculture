import ast
import sys
import types
import unittest
from unittest.mock import patch

from tests.test_experimental_scale_agent import scale_observation
from tests.test_prepare_candidate_c_submission import get_last_callable
from tools.packaging import prepare_candidate_b_submission


class PrepareCandidateBSubmissionTests(unittest.TestCase):
    def test_kaggle_loader_picks_the_real_agent(self) -> None:
        # Regression coverage for the class of bug documented in
        # prepare_candidate_c_submission._drop_top_level_agent: Kaggle's
        # real loader takes the last callable in the exec namespace by
        # insertion order, not `module.agent` by name. Currently safe
        # here (Candidate A's embedded bundle ends in `def agent(...)`, a
        # FunctionDef, which this module's own _drop_top_level_agent does
        # filter), but that safety is a property of Candidate A's current
        # shape, not something the other assertions in this file check --
        # if A ever moves to the same `agent = build_x_agent()` pattern B
        # and C already use, this is what would catch it.
        source = prepare_candidate_b_submission.build_source()
        picked = get_last_callable(source, "submissions/candidate-b/main.py")

        decision = picked(scale_observation())

        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_agent_is_assigned_exactly_once(self) -> None:
        source = prepare_candidate_b_submission.build_source()
        module = ast.parse(source)
        agent_assigns = [
            node
            for node in ast.walk(module)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "agent"
                for target in node.targets
            )
        ]

        self.assertEqual(len(agent_assigns), 1)

    def test_build_is_standalone_and_exposes_agent(self) -> None:
        source = prepare_candidate_b_submission.build_source()
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
        function_names = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]
        assigned_names = [
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]

        self.assertEqual(local_imports, [])
        self.assertIn("calendar_decide", function_names)
        self.assertIn("decide", function_names)
        self.assertIn("agent", assigned_names)
        self.assertEqual(module.body[-1].targets[0].id, "agent")
        code = compile(
            source,
            "submissions/candidate-b/main.py",
            "exec",
        )
        package_module = types.ModuleType("candidate_b_submission_test")
        modules = {package_module.__name__: package_module}
        with patch.dict(sys.modules, modules):
            exec(code, package_module.__dict__)
        decision = package_module.agent(scale_observation())
        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_manifest_matches_built_package(self) -> None:
        prepare_candidate_b_submission.main()
        package = prepare_candidate_b_submission.OUTPUT.read_text(
            encoding="utf-8"
        )
        manifest = prepare_candidate_b_submission.MANIFEST.read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            package,
            prepare_candidate_b_submission.build_source(),
        )
        self.assertIn("sequential-affordability", manifest)


if __name__ == "__main__":
    unittest.main()
