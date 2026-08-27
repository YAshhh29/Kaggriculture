import unittest

from core.routing import distance, nearest_position, pair_route_cost, step_toward


class RoutingTests(unittest.TestCase):
    def test_each_move_reduces_shortest_distance_by_one(self) -> None:
        actions = {
            "WEST": (-1, 0),
            "EAST": (1, 0),
            "NORTH": (0, -1),
            "SOUTH": (0, 1),
        }
        target = (8, 1)
        for origin in ((0, 0), (9, 9), (8, 8), (4, 1)):
            action = step_toward(origin, target, ["HARVEST"])[0]
            dx, dy = actions[action]
            after = (origin[0] + dx, origin[1] + dy)
            self.assertEqual(distance(after, target), distance(origin, target) - 1)

    def test_action_runs_only_at_target(self) -> None:
        self.assertEqual(step_toward((4, 4), (4, 4), ["CARE"]), ["CARE"])

    def test_nearest_position_uses_stable_row_major_tie_break(self) -> None:
        self.assertEqual(
            nearest_position((4, 4), ((5, 4), (4, 3), (3, 4))),
            (4, 3),
        )

    def test_pair_cost_prioritizes_latest_arrival_then_total_travel(self) -> None:
        self.assertEqual(pair_route_cost(((4, 4), (5, 4)), (3, 4)), (2, 3))


if __name__ == "__main__":
    unittest.main()
