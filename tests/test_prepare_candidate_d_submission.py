import ast
import sys
import types
import unittest
from unittest.mock import patch

from tests.test_experimental_scale_agent import scale_observation
from tests.test_prepare_candidate_c_submission import get_last_callable
from tools.packaging import prepare_candidate_d_submission


class PrepareCandidateDSubmissionTests(unittest.TestCase):
    def test_kaggle_loader_picks_the_real_agent(self) -> None:
        # Regression cover for rl/GOAL.md section 9h: Kaggle's loader takes
        # the last callable in the exec namespace by insertion order, not
        # `module.agent` by name, so a stray earlier `agent = ...` from the
        # embedded Candidate B bundle can silently outrank this module's.
        source = prepare_candidate_d_submission.build_source()
        picked = get_last_callable(source, "submissions/candidate-d/main.py")

        decision = picked(scale_observation())

        self.assertIn("farmer", decision)
        self.assertIn("hands", decision)
        self.assertIn("market", decision)

    def test_agent_is_assigned_exactly_once(self) -> None:
        source = prepare_candidate_d_submission.build_source()
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
        source = prepare_candidate_d_submission.build_source()
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
        assigned = [
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]

        self.assertEqual(local_imports, [])
        self.assertIn("elite_andrey_route", assigned)
        self.assertIn("agent", assigned)
        self.assertEqual(module.body[-1].targets[0].id, "agent")

        code = compile(source, "submissions/candidate-d/main.py", "exec")
        package = types.ModuleType("candidate_d_submission_test")
        with patch.dict(sys.modules, {package.__name__: package}):
            exec(code, package.__dict__)
        decision = package.agent(scale_observation())
        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_model_payload_is_embedded_not_read_from_disk(self) -> None:
        # MODEL_PATH survives as a dead reference inside _load_actions'
        # `if payload is None` branch, which never runs once MODEL_PAYLOAD
        # is a literal. The invariant that matters is that no top-level
        # MODEL_PATH assignment remains (nothing resolves a model file at
        # import time) and the payload really is inlined.
        module = ast.parse(prepare_candidate_d_submission.build_source())
        top_level_assigns = [
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]
        payloads = [
            node
            for node in module.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "ANDREY_MODEL_PAYLOAD"
        ]

        self.assertNotIn("MODEL_PATH", top_level_assigns)
        self.assertEqual(len(payloads), 1)
        self.assertIsInstance(payloads[0].value, ast.Constant)
        self.assertIsInstance(payloads[0].value.value, str)

    def test_manifest_matches_built_package(self) -> None:
        prepare_candidate_d_submission.main()
        package = prepare_candidate_d_submission.OUTPUT.read_text(
            encoding="utf-8"
        )
        manifest = prepare_candidate_d_submission.MANIFEST.read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            package, prepare_candidate_d_submission.build_source()
        )
        self.assertIn("105520725", manifest)
        self.assertIn("Andrey Tikhomirov", manifest)


if __name__ == "__main__":
    unittest.main()
