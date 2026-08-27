import json
import tempfile
import unittest
from pathlib import Path

from research.collection.collect_market_dataset import load_or_create_report, write_checkpoint


class CollectMarketDatasetTests(unittest.TestCase):
    def test_checkpoints_and_resumes_matching_collection(self) -> None:
        collection = self._collection()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dataset.json"
            report = load_or_create_report(output, collection)
            report["episodes"].append(
                {
                    "episode_id": "seed-30",
                    "seed": 30,
                    "agent_player": 0,
                    "source_replay": "collected/seed-30.json",
                }
            )
            report["rows"].append(
                {
                    "episode_id": "seed-30",
                    "decision": {"action": "HOLD"},
                }
            )
            write_checkpoint(output, report, expected_episodes=2)
            resumed = load_or_create_report(output, collection)
            saved = json.loads(output.read_text(encoding="utf-8"))

        self.assertFalse(saved["complete"])
        self.assertEqual(saved["summary"]["market_decisions"], 1)
        self.assertEqual(resumed["episodes"][0]["seed"], 30)
        self.assertEqual(resumed["episodes"][0]["source_replay"], "")
        self.assertFalse(
            resumed["episodes"][0]["raw_replay_persisted"]
        )

    def test_rejects_checkpoint_from_different_policy(self) -> None:
        collection = self._collection()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dataset.json"
            report = load_or_create_report(output, collection)
            write_checkpoint(output, report, expected_episodes=2)
            changed = {**collection, "agent_sha256": "different"}

            with self.assertRaisesRegex(ValueError, "agent_sha256"):
                load_or_create_report(output, changed)

    @staticmethod
    def _collection() -> dict:
        return {
            "agent_sha256": "policy",
            "opponent": "starter",
            "episode_steps": 720,
            "seed_start": 30,
            "seed_count": 1,
            "positions": [0, 1],
            "simulator_version": "test",
        }


if __name__ == "__main__":
    unittest.main()