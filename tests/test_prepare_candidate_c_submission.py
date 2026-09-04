import ast
import sys
import types
import unittest
from unittest.mock import patch

from tests.test_experimental_scale_agent import scale_observation
from tools.packaging import prepare_candidate_c_submission


def get_last_callable(source: str, path: str):
    """Reimplements kaggle_environments.agent.get_last_callable exactly.

    Kaggle's real loader does not look up a variable named "agent" -- it
    execs the whole module into a fresh namespace and takes
    `[v for v in env.values() if callable(v)][-1]`. A stray earlier
    assignment to the name "agent" (from an embedded parent package, say)
    does not get filtered out by checking `module.agent` directly, or by
    checking that the source's last statement assigns "agent": reassigning
    an existing dict key does not move it, so an earlier `agent = ...`
    pins that key's position near the top of the namespace regardless of
    what it is reassigned to later, and the loader picks whatever *other*
    callable ends up last instead. This is exactly the mechanism that
    broke the first real Kaggle upload of this package -- see
    `_drop_top_level_agent`'s docstring in prepare_candidate_c_submission.
    """
    code = compile(source, path, "exec")
    env = {}
    exec(code, env)
    return [v for v in env.values() if callable(v)][-1]


class PrepareCandidateCSubmissionTests(unittest.TestCase):
    def test_kaggle_loader_picks_the_real_agent(self) -> None:
        # Regression test for the bug above: assert against the actual
        # extraction mechanism Kaggle uses, not against `module.agent`
        # (direct attribute access always returns the latest value and
        # cannot see this class of bug) or against source-order position
        # (insertion order in the exec namespace is what matters, and a
        # reassigned name does not move there).
        source = prepare_candidate_c_submission.build_source()
        picked = get_last_callable(source, "submissions/candidate-c/main.py")

        decision = picked(scale_observation())

        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_agent_is_assigned_exactly_once(self) -> None:
        source = prepare_candidate_c_submission.build_source()
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
        source = prepare_candidate_c_submission.build_source()
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
        assigned_names = [
            target.id
            for node in module.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        ]

        self.assertEqual(local_imports, [])
        self.assertIn("elite_pasture_route", assigned_names)
        self.assertIn("calendar_route", assigned_names)
        self.assertIn("agent", assigned_names)
        self.assertEqual(module.body[-1].targets[0].id, "agent")
        code = compile(
            source,
            "submissions/candidate-c/main.py",
            "exec",
        )
        package_module = types.ModuleType("candidate_c_submission_test")
        modules = {package_module.__name__: package_module}
        with patch.dict(sys.modules, modules):
            exec(code, package_module.__dict__)
        decision = package_module.agent(scale_observation())
        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_manifest_matches_built_package(self) -> None:
        prepare_candidate_c_submission.main()
        package = prepare_candidate_c_submission.OUTPUT.read_text(
            encoding="utf-8"
        )
        manifest = prepare_candidate_c_submission.MANIFEST.read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            package,
            prepare_candidate_c_submission.build_source(),
        )
        self.assertIn("fog flower", manifest)


if __name__ == "__main__":
    unittest.main()
