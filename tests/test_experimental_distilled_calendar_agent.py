import hashlib
import json
import unittest

from agents.experimental_distilled_calendar_agent import (
    CALENDAR_ACTIONS,
    _local_repair,
    _sanitize_units,
    agent,
)
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalDistilledCalendarAgentTests(unittest.TestCase):
    def test_calendar_has_full_episode(self) -> None:
        self.assertEqual(len(CALENDAR_ACTIONS), 720)

    def test_matches_every_model_calendar_decision(self) -> None:
        mismatches = [
            record
            for record in range(1, len(CALENDAR_ACTIONS))
            if agent({"step": record - 1}) != CALENDAR_ACTIONS[record]
        ]
        raw = json.dumps(
            CALENDAR_ACTIONS,
            separators=(",", ":"),
        ).encode("utf-8")

        self.assertEqual(mismatches, [])
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "298bcb8d2e5b7543bc1403e76062ef6b9a0bc778ce95365ccc5395e99fb22cef",
        )

    def test_invalid_action_repairs_urgent_water_on_current_tile(self) -> None:
        state = scale_observation(day=2)
        farm = state["farms"][0]
        x, y = farm["farmer"]
        farm["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 0,
            "yield_units": 0,
            "watered_today": False,
            "consecutive_unwatered": 1,
        }

        action = _local_repair(state, 0, tuple(farm["farmer"]))

        self.assertEqual(action, ["WATER"])

    def test_atomic_plant_sanitizer_never_exceeds_seed_stock(self) -> None:
        state = scale_observation()
        state["farms"][0]["hands"] = [[1, 0], [2, 0]]
        state["private"]["inventories"] = [{}, {}, {}]
        state["private"]["seeds"]["WHEAT"] = 1
        planned = {
            "farmer": ["PLANT", "WHEAT"],
            "hands": [["PLANT", "WHEAT"], ["PLANT", "WHEAT"]],
            "market": [],
        }

        farmer, hands = _sanitize_units(state, planned)

        self.assertEqual(
            [farmer, *hands].count(["PLANT", "WHEAT"]),
            1,
        )

    def test_runtime_preserves_full_calendar_action_list(self) -> None:
        state = scale_observation()
        state["step"] = 0

        decision = agent(state)

        self.assertEqual(decision, CALENDAR_ACTIONS[1])


if __name__ == "__main__":
    unittest.main()
