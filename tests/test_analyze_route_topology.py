import unittest

from research.analysis.analyze_route_topology import analyze_route_topology


class AnalyzeRouteTopologyTests(unittest.TestCase):
    def test_tracks_worker_task_quadrants_and_switches(self) -> None:
        farm = {
            "farmer": [0, 0],
            "hands": [],
            "tiles": [[None] * 10 for _ in range(10)],
        }
        replay = {
            "configuration": {"boardSize": 10},
            "steps": [
                [{"observation": {"day": 0, "farms": [farm]}}],
                [
                    {
                        "action": {"farmer": ["PLANT", "WHEAT"]},
                        "observation": {
                            "day": 0,
                            "farms": [{**farm, "farmer": [5, 0]}],
                        },
                    }
                ],
                [
                    {
                        "action": {"farmer": ["WATER"]},
                        "observation": {
                            "day": 0,
                            "farms": [{**farm, "farmer": [5, 0]}],
                        },
                    }
                ],
            ],
        }

        worker = analyze_route_topology(replay, 0)["workers"][0]

        self.assertEqual(worker["tasks"], 2)
        self.assertEqual(worker["task_quadrants"], {"NE": 1, "NW": 1})
        self.assertEqual(worker["quadrant_switches"], 1)


if __name__ == "__main__":
    unittest.main()
