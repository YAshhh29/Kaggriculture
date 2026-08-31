import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from rl.replay_dataset import load_replay_dataset, write_jsonl
from rl.rewards import win_first_reward
from rl.rollout import run_episode, run_paired
from tests.test_experimental_scale_agent import scale_observation


def action(operation):
    return {"farmer": [operation], "hands": [], "market": []}


class FakeEnvironment:
    def __init__(
        self,
        *,
        statuses=("DONE", "DONE"),
        rewards=(10, 20),
    ) -> None:
        self.statuses = statuses
        self.rewards = rewards
        self.agents = []
        self.steps = []

    def run(self, agents) -> None:
        self.agents = agents
        self.steps = [
            [],
            [
                SimpleNamespace(
                    status=self.statuses[0],
                    reward=self.rewards[0],
                ),
                SimpleNamespace(
                    status=self.statuses[1],
                    reward=self.rewards[1],
                ),
            ],
        ]


class RlDataTests(unittest.TestCase):
    def test_replay_alignment_uses_following_record_action(self) -> None:
        observations = [
            scale_observation(day=0, hour=0),
            scale_observation(day=0, hour=1),
            scale_observation(day=0, hour=2),
        ]
        replay = {
            "module_version": "1.32.7",
            "statuses": ["DONE", "DONE"],
            "rewards": [30, 20],
            "info": {
                "EpisodeId": 42,
                "seed": 7,
                "Agents": [
                    {"Name": "Teacher"},
                    {"Name": "Opponent"},
                ],
            },
            "steps": [
                [
                    {"observation": observation, "action": own_action},
                    {"observation": observation, "action": None},
                ]
                for observation, own_action in zip(
                    observations,
                    [None, action("NORTH"), action("SOUTH")],
                    strict=True,
                )
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            replay_path = Path(directory) / "replay.json"
            replay_bytes = json.dumps(replay).encode("utf-8")
            replay_path.write_bytes(replay_bytes)
            dataset = load_replay_dataset(
                replay_path,
                team_name="Teacher",
                split="train",
                source_submission_id=123,
                source_score_snapshot=1500.0,
                replay_date="2026-08-30T00:00:00Z",
                collected_at="2026-08-31T00:00:00Z",
                expected_records=3,
            )

            self.assertEqual(len(dataset.examples), 2)
            self.assertEqual(
                dataset.examples[0].teacher_action,
                action("NORTH"),
            )
            self.assertEqual(
                dataset.examples[1].teacher_action,
                action("SOUTH"),
            )
            self.assertEqual(
                dataset.replay_sha256,
                hashlib.sha256(replay_bytes).hexdigest(),
            )

            output = Path(directory) / "dataset.jsonl"
            write_jsonl(dataset, output)
            rows = [
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(rows[0]["type"], "metadata")
            self.assertEqual(rows[0]["examples"], 2)
            self.assertEqual(rows[0]["dataset_schema_version"], 1)
            self.assertEqual(rows[0]["feature_schema_version"], 1)
            self.assertEqual(rows[0]["action_schema_version"], 1)
            self.assertEqual(rows[0]["source_submission_id"], 123)
            self.assertEqual(rows[0]["split"], "train")
            self.assertEqual(rows[0]["result"], "win")
            self.assertEqual(len(rows), 3)

    def test_replay_rejects_missing_action_and_failed_status(self) -> None:
        observation = scale_observation()
        replay = {
            "module_version": "1.32.7",
            "statuses": ["DONE", "ERROR"],
            "rewards": [0, None],
            "info": {
                "EpisodeId": 42,
                "seed": 7,
                "Agents": [
                    {"Name": "Teacher"},
                    {"Name": "Opponent"},
                ],
            },
            "steps": [
                [
                    {"observation": observation, "action": action("PASS")},
                    {"observation": observation, "action": action("PASS")},
                ],
                [
                    {"observation": observation, "action": None},
                    {"observation": observation, "action": action("PASS")},
                ],
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "failed.json"
            path.write_text(json.dumps(replay), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "did not finish"):
                load_replay_dataset(
                    path,
                    team_name="Teacher",
                    split="train",
                    expected_records=2,
                )

            replay["statuses"] = ["DONE", "DONE"]
            replay["rewards"] = [1, 0]
            path.write_text(json.dumps(replay), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no teacher action"):
                load_replay_dataset(
                    path,
                    team_name="Teacher",
                    split="train",
                    expected_records=2,
                )

    def test_replay_rejects_malformed_action_semantics(self) -> None:
        observation = scale_observation()
        replay = {
            "module_version": "1.32.7",
            "statuses": ["DONE", "DONE"],
            "rewards": [1, 0],
            "info": {
                "EpisodeId": 42,
                "seed": 7,
                "Agents": [
                    {"Name": "Teacher"},
                    {"Name": "Opponent"},
                ],
            },
            "steps": [
                [
                    {"observation": observation, "action": action("PASS")},
                    {"observation": observation, "action": action("PASS")},
                ],
                [
                    {
                        "observation": observation,
                        "action": {
                            "farmer": ["BOGUS"],
                            "hands": [],
                            "market": [["BUY_SEED"]],
                        },
                    },
                    {"observation": observation, "action": action("PASS")},
                ],
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.json"
            path.write_text(json.dumps(replay), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "unknown operation"):
                load_replay_dataset(
                    path,
                    team_name="Teacher",
                    split="train",
                    expected_records=2,
                )

            replay["steps"][1][0]["action"] = {
                "farmer": ["PASS"],
                "hands": [],
                "market": [["BUY_SEED"]],
            }
            path.write_text(json.dumps(replay), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid BUY_SEED"):
                load_replay_dataset(
                    path,
                    team_name="Teacher",
                    split="train",
                    expected_records=2,
                )

            replay["steps"][1][0]["action"]["market"] = [
                ["BUY_SEED", "WHEAT", 0]
            ]
            path.write_text(json.dumps(replay), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "positive integer"):
                load_replay_dataset(
                    path,
                    team_name="Teacher",
                    split="train",
                    expected_records=2,
                )

            malformed_actions = [
                {
                    "farmer": ["PICKUP"],
                    "hands": [],
                    "market": [],
                },
                {
                    "farmer": ["PLANT", "MILK"],
                    "hands": [],
                    "market": [],
                },
                {
                    "farmer": ["PASS"],
                    "hands": [["PASS"]],
                    "market": [],
                },
                {
                    "farmer": ["PASS"],
                    "hands": [],
                    "market": [["HIRE"]] * 11,
                },
                {
                    "farmer": ["PASS"],
                    "hands": [],
                    "market": [["SELL", "WHEAT", True]],
                },
            ]
            for malformed_action in malformed_actions:
                replay["steps"][1][0]["action"] = malformed_action
                path.write_text(json.dumps(replay), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_replay_dataset(
                        path,
                        team_name="Teacher",
                        split="train",
                        expected_records=2,
                    )

    def test_teacher_action_does_not_leak_into_encoded_state(self) -> None:
        observation = scale_observation()

        def dataset_for(teacher_operation):
            replay = {
                "module_version": "1.32.7",
                "statuses": ["DONE", "DONE"],
                "rewards": [1, 0],
                "info": {
                    "EpisodeId": 42,
                    "seed": 7,
                    "Agents": [
                        {"Name": "Teacher"},
                        {"Name": "Opponent"},
                    ],
                },
                "steps": [
                    [
                        {
                            "observation": observation,
                            "action": action("PASS"),
                        },
                        {
                            "observation": observation,
                            "action": action("PASS"),
                        },
                    ],
                    [
                        {
                            "observation": observation,
                            "action": action(teacher_operation),
                        },
                        {
                            "observation": observation,
                            "action": action("PASS"),
                        },
                    ],
                ],
            }
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "replay.json"
                path.write_text(json.dumps(replay), encoding="utf-8")
                return load_replay_dataset(
                    path,
                    team_name="Teacher",
                    split="train",
                    expected_records=2,
                )

        north = dataset_for("NORTH")
        south = dataset_for("SOUTH")

        self.assertEqual(north.examples[0].state, south.examples[0].state)
        self.assertNotEqual(
            north.examples[0].teacher_action,
            south.examples[0].teacher_action,
        )

    def test_win_first_reward_preserves_outcome_sign(self) -> None:
        win = win_first_reward(50_001, 50_000)
        loss = win_first_reward(50_000, 50_001)
        tie = win_first_reward(50_000, 50_000)

        self.assertGreater(win.total, 0)
        self.assertLess(loss.total, 0)
        self.assertEqual(tie.total, 0)
        self.assertAlmostEqual(win.total, -loss.total)
        with self.assertRaisesRegex(ValueError, "finite"):
            win_first_reward(math.inf, 0)

    def test_rollout_keeps_candidate_player_mapping(self) -> None:
        environment = FakeEnvironment()

        def factory(*args, **kwargs):
            del args, kwargs
            return environment

        def candidate(observation):
            del observation
            return action("PASS")

        result = run_episode(
            candidate,
            "starter",
            seed=7,
            candidate_player=1,
            make_environment=factory,
        )

        self.assertEqual(environment.agents, ["starter", candidate])
        self.assertEqual(result.candidate_reward, 20)
        self.assertEqual(result.opponent_reward, 10)
        self.assertEqual(result.result, "win")

    def test_paired_rollout_runs_both_player_positions(self) -> None:
        environments = []

        def factory(*args, **kwargs):
            del args, kwargs
            environment = FakeEnvironment()
            environments.append(environment)
            return environment

        def candidate(observation):
            del observation
            return action("PASS")

        result = run_paired(
            candidate,
            "starter",
            seed=7,
            make_environment=factory,
        )

        self.assertEqual(len(environments), 2)
        self.assertEqual(environments[0].agents, [candidate, "starter"])
        self.assertEqual(environments[1].agents, ["starter", candidate])
        self.assertEqual((result.wins, result.losses, result.ties), (1, 1, 0))
        self.assertEqual(result.mean_margin, 0)

    def test_failed_rollout_checks_status_before_reward(self) -> None:
        environment = FakeEnvironment(
            statuses=("ERROR", "DONE"),
            rewards=(None, 20),
        )

        def factory(*args, **kwargs):
            del args, kwargs
            return environment

        def candidate(observation):
            del observation
            return action("PASS")

        with self.assertRaisesRegex(RuntimeError, "did not finish"):
            run_episode(
                candidate,
                "starter",
                seed=7,
                candidate_player=0,
                make_environment=factory,
            )


if __name__ == "__main__":
    unittest.main()