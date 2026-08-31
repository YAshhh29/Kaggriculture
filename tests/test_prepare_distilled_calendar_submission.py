import ast
import hashlib
import json
import sys
import tempfile
import types
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from tests.test_experimental_scale_agent import scale_observation
from tools.packaging import prepare_distilled_calendar_submission


class PrepareDistilledCalendarSubmissionTests(unittest.TestCase):
    def test_build_is_standalone_and_kaggle_selects_agent(self) -> None:
        source = prepare_distilled_calendar_submission.build_source()
        module = ast.parse(source)
        functions = [
            node.name
            for node in module.body
            if isinstance(node, ast.FunctionDef)
        ]
        local_imports = [
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith(("agents.", "policies.", "core."))
        ]

        self.assertEqual(local_imports, [])
        self.assertEqual(functions[-2:], ["decide", "agent"])
        code = compile(
            source,
            "submissions/distilled-calendar/main.py",
            "exec",
        )
        package_module = types.ModuleType("distilled_calendar_submission_test")
        modules = {package_module.__name__: package_module}
        with patch.dict(sys.modules, modules):
            exec(code, package_module.__dict__)
        selected_callable = [
            value
            for value in package_module.__dict__.values()
            if callable(value)
        ][-1]

        self.assertIs(selected_callable, package_module.agent)
        self.assertEqual(len(package_module.CALENDAR_ACTIONS), 720)
        decision = selected_callable(scale_observation())
        self.assertIn("farmer", decision)
        self.assertIn("market", decision)

    def test_rejects_tampered_model_action_hash(self) -> None:
        model = json.loads(
            prepare_distilled_calendar_submission.MODEL_PATH.read_text(
                encoding="utf-8"
            )
        )
        tampered = deepcopy(model)
        tampered["actions_sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "tampered-model.json"
            model_path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "action hash mismatch"):
                prepare_distilled_calendar_submission.load_verified_model(
                    model_path
                )

    def test_checked_in_package_and_manifest_are_fresh(self) -> None:
        model = prepare_distilled_calendar_submission.load_verified_model()
        package_bytes = (
            prepare_distilled_calendar_submission.OUTPUT.read_bytes()
        )
        package_hash = hashlib.sha256(package_bytes).hexdigest()
        evidence = (
            prepare_distilled_calendar_submission.load_verified_evidence(
                package_hash,
                model,
            )
        )
        package = prepare_distilled_calendar_submission.OUTPUT.read_text(
            encoding="utf-8"
        )
        manifest = json.loads(
            prepare_distilled_calendar_submission.MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(model["source_episode_id"], 99058164)
        self.assertEqual(model["source_team"], "Crop Dusta")
        self.assertEqual(
            model["actions_sha256"],
            "298bcb8d2e5b7543bc1403e76062ef6b9a0bc778ce95365ccc5395e99fb22cef",
        )
        self.assertEqual(
            package,
            prepare_distilled_calendar_submission.build_source(),
        )
        self.assertEqual(
            manifest["sha256"],
            package_hash,
        )
        self.assertEqual(
            manifest["combined_source_sha256"],
            prepare_distilled_calendar_submission.combined_source_hash(),
        )
        self.assertEqual(manifest["training_data"]["license"], "Apache-2.0")
        self.assertEqual(
            manifest["validation"]["evidence_sha256"],
            hashlib.sha256(
                prepare_distilled_calendar_submission.EVIDENCE_PATH
                .read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            evidence["gates"]["broad"]["candidate"]["record"],
            "72-8-0",
        )


if __name__ == "__main__":
    unittest.main()
