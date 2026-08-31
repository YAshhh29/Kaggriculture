import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research.training.build_public_calendar_model import build_model


class BuildPublicCalendarModelTests(unittest.TestCase):
    def test_builds_verified_compressed_calendar(self) -> None:
        actions = [
            {
                "farmer": ["PASS"],
                "hands": [],
                "market": [],
            }
            for _ in range(720)
        ]
        replay = {
            "module_version": "1.32.7",
            "info": {
                "EpisodeId": 123456,
                "seed": 789,
                "Agents": [
                    {"Name": "Teacher"},
                    {"Name": "Opponent"},
                ],
            },
            "steps": [
                [
                    {"action": action},
                    {"action": None},
                ]
                for action in actions
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            replay_path = Path(directory) / "replay.json"
            replay_bytes = (
                json.dumps(replay, separators=(",", ":")) + "\n"
            ).encode("utf-8")
            replay_path.write_bytes(replay_bytes)

            model = build_model(replay_path, "Teacher")

        self.assertEqual(model["source_episode_id"], 123456)
        self.assertEqual(model["source_player"], 0)
        self.assertEqual(model["records"], 720)
        self.assertEqual(
            model["replay_sha256"],
            hashlib.sha256(replay_bytes).hexdigest(),
        )
        self.assertTrue(model["actions_zlib_b64"])


if __name__ == "__main__":
    unittest.main()
