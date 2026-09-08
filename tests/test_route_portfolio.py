"""Tests for rl/route_portfolio.py."""

from __future__ import annotations

from typing import Any

import pytest

from rl.route_portfolio import (
    BLOCK_TURNS,
    RouteStats,
    build_portfolio_agent,
    cycling_route,
    fixed_route,
    matching_route,
    roster_gap,
    sticky,
)


def tape(marker: str, hands: int = 0, land_on: int | None = None,
         animals_on: int | None = None, turns: int = 720):
    """A synthetic recording whose farmer action names its own route."""
    actions = []
    for turn in range(turns):
        market: list[list[Any]] = []
        if land_on is not None and turn == land_on:
            market.append(["BUY_LAND"])
        if animals_on is not None and turn == animals_on:
            market.append(["BUY_ANIMAL", "COW", 3])
        actions.append({
            "farmer": [marker],
            "hands": [["PASS"]] * hands,
            "market": market,
        })
    return actions


def observation(step: int, hands: int = 0, quadrants: int = 1,
                animals: int = 0, player: int = 0) -> dict[str, Any]:
    tiles: list[list[Any]] = [[None] * 10 for _ in range(10)]
    placed = 0
    for y in range(10):
        for x in range(10):
            if placed < animals:
                tiles[y][x] = {"animal": "COW"}
                placed += 1
    farm = {
        "hands": [[0, 0]] * hands,
        "unlocked_quadrants": list(range(quadrants)),
        "tiles": tiles,
        "money": 1000.0,
    }
    return {
        "step": step,
        "player": player,
        "farms": [farm, farm] if player == 0 else [farm, farm],
    }


class TestRouteStats:
    def test_records_crew_size_per_turn(self):
        stats = RouteStats(tape("a", hands=4))
        assert stats.hands[0] == 4
        assert stats.hands[500] == 4

    def test_accumulates_land_and_animals(self):
        stats = RouteStats(tape("a", land_on=10, animals_on=20))
        assert stats.land[9] == 0
        assert stats.land[10] == 1
        assert stats.animals[19] == 0
        assert stats.animals[20] == 3

    def test_at_clamps_past_the_end(self):
        stats = RouteStats(tape("a", turns=100))
        assert stats.at(999)["farmer"] == ["a"]
        assert stats.at(-5)["farmer"] == ["a"]

    def test_survives_a_malformed_record(self):
        stats = RouteStats([None, {"hands": [], "market": []}])  # type: ignore
        assert stats.hands[0] == 0


class TestRosterGap:
    def test_zero_when_the_route_matches_the_farm(self):
        stats = RouteStats(tape("a", hands=6))
        assert roster_gap(observation(0, hands=6), stats, 0) == 0.0

    def test_crew_mismatch_is_weighted_hardest(self):
        stats = RouteStats(tape("a", hands=6, animals_on=0))
        crew = roster_gap(observation(0, hands=0, animals=3), stats, 0)
        herd = roster_gap(observation(0, hands=6, animals=0), stats, 0)
        assert crew > herd


class TestChoosers:
    def test_fixed_never_moves(self):
        stats = [RouteStats(tape("a")), RouteStats(tape("b"))]
        assert fixed_route(0, observation(0), -1, stats) == 0
        assert fixed_route(5, observation(360), 1, stats) == 1

    def test_cycling_advances_every_block(self):
        stats = [RouteStats(tape("a")), RouteStats(tape("b"))]
        picks = [cycling_route(b, observation(0), 0, stats) for b in range(4)]
        assert picks == [0, 1, 0, 1]

    def test_matching_prefers_the_nearer_crew(self):
        stats = [RouteStats(tape("a", hands=2)), RouteStats(tape("b", hands=9))]
        assert matching_route(0, observation(0, hands=9), -1, stats) == 1
        assert matching_route(0, observation(0, hands=2), -1, stats) == 0

    def test_sticky_holds_a_route_inside_the_margin(self):
        stats = [RouteStats(tape("a", hands=5)), RouteStats(tape("b", hands=4))]
        obs = observation(0, hands=4)
        assert matching_route(0, obs, 0, stats) == 1
        assert sticky(matching_route, margin=99.0)(0, obs, 0, stats) == 0

    def test_sticky_switches_when_the_gap_is_wide(self):
        stats = [RouteStats(tape("a", hands=0)), RouteStats(tape("b", hands=9))]
        obs = observation(0, hands=9)
        assert sticky(matching_route, margin=1.0)(0, obs, 0, stats) == 1


class TestPortfolioAgent:
    def test_follows_one_route_under_fixed(self):
        agent = build_portfolio_agent(
            [tape("a"), tape("b")], chooser=fixed_route
        )
        assert agent(observation(0))["farmer"] == ["a"]
        assert agent(observation(400))["farmer"] == ["a"]

    def test_switches_on_block_boundaries_only(self):
        agent = build_portfolio_agent(
            [tape("a"), tape("b")], chooser=cycling_route
        )
        assert agent(observation(0))["farmer"] == ["a"]
        assert agent(observation(BLOCK_TURNS - 1))["farmer"] == ["a"]
        assert agent(observation(BLOCK_TURNS))["farmer"] == ["b"]

    def test_applies_the_replay_off_by_one(self):
        first = tape("a")
        first[5] = {"farmer": ["MARKED"], "hands": [], "market": []}
        agent = build_portfolio_agent([first], chooser=fixed_route)
        assert agent(observation(4))["farmer"] == ["MARKED"]

    def test_passes_past_the_end_of_the_tape(self):
        agent = build_portfolio_agent(
            [tape("a", turns=10)], chooser=fixed_route
        )
        assert agent(observation(20)) == {
            "farmer": ["PASS"], "hands": [], "market": []
        }

    def test_returns_copies_the_caller_cannot_corrupt(self):
        source = tape("a", hands=1)
        agent = build_portfolio_agent([source], chooser=fixed_route)
        action = agent(observation(0))
        action["farmer"].append("MUTATED")
        action["hands"][0].append("MUTATED")
        assert agent(observation(0))["farmer"] == ["a"]
        assert agent(observation(0))["hands"][0] == ["PASS"]

    def test_resets_when_a_new_game_starts(self):
        agent = build_portfolio_agent(
            [tape("a"), tape("b")], chooser=cycling_route
        )
        agent(observation(BLOCK_TURNS))
        assert agent(observation(0))["farmer"] == ["a"]

    def test_keeps_seats_apart(self):
        agent = build_portfolio_agent(
            [tape("a"), tape("b")], chooser=cycling_route
        )
        agent(observation(BLOCK_TURNS, player=0))
        assert agent(observation(0, player=1))["farmer"] == ["a"]

    def test_rejects_an_unknown_chooser_result(self):
        agent = build_portfolio_agent(
            [tape("a")], chooser=lambda b, o, p, s: 7
        )
        with pytest.raises(IndexError):
            agent(observation(0))
