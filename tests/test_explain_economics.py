import unittest

from research.analysis.explain_economics import replay_snapshot
from tests.test_experimental_scale_agent import scale_observation


class ExplainEconomicsTests(unittest.TestCase):
    def test_explains_one_record_without_private_opponent_state(self) -> None:
        observation = scale_observation(day=9, hour=3)
        observation["town"]["unlocked_shops"] = ["PET_CAFE"]
        replay = {"steps": [[{"observation": observation}, {}]]}

        report = replay_snapshot(replay, 0, 0)

        self.assertEqual(report["day"], 9)
        self.assertEqual(report["daily_demand"]["CARROT"], 13)
        self.assertEqual(report["crops"][0]["crop"], "CARROT")


if __name__ == "__main__":
    unittest.main()
