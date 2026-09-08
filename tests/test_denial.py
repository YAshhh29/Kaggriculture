"""Tests for rl/denial.py."""

from __future__ import annotations

from typing import Any

from rl.denial import (
    contested_items,
    contested_value,
    denial_value,
    rival_supply,
)
from rl.market import MARKET_I0, sale_revenue


def board(tiles: list[Any] | None = None) -> list[list[Any]]:
    grid: list[list[Any]] = [[None] * 10 for _ in range(10)]
    for index, tile in enumerate(tiles or []):
        grid[index // 10][index % 10] = tile
    return grid


def observation(
    rival_tiles: list[Any] | None = None,
    day: int = 5,
    player: int = 0,
    inventory: dict[str, float] | None = None,
) -> dict[str, Any]:
    mine = {"tiles": board(), "money": 1000.0}
    theirs = {"tiles": board(rival_tiles), "money": 1000.0}
    farms = [mine, theirs] if player == 0 else [theirs, mine]
    return {
        "day": day,
        "player": player,
        "farms": farms,
        "market": {"inventory": dict(inventory or {})},
    }


class TestRivalSupply:
    def test_empty_farm_supplies_nothing(self):
        assert rival_supply(observation(), "MILK") == 0.0

    def test_counts_standing_yield_on_an_animal(self):
        obs = observation([{"animal": "COW", "yield_units": 7}])
        assert rival_supply(obs, "MILK") >= 7.0

    def test_counts_future_production_of_an_animal(self):
        bare = observation([{"animal": "COW", "yield_units": 0}])
        assert rival_supply(bare, "MILK") > 0.0

    def test_maps_each_animal_to_its_own_product(self):
        obs = observation([{"animal": "SHEEP", "yield_units": 4}])
        assert rival_supply(obs, "WOOL") >= 4.0
        assert rival_supply(obs, "MILK") == 0.0
        assert rival_supply(obs, "EGG") == 0.0

    def test_counts_standing_crop_yield(self):
        obs = observation(
            [{"kind": "PLANT", "crop": "MELON", "yield_units": 6}]
        )
        assert rival_supply(obs, "MELON") >= 6.0

    def test_ignores_a_crop_of_another_kind(self):
        obs = observation(
            [{"kind": "PLANT", "crop": "MELON", "yield_units": 6}]
        )
        assert rival_supply(obs, "WHEAT") == 0.0

    def test_nothing_is_supplied_after_the_last_day(self):
        obs = observation([{"animal": "COW", "yield_units": 9}], day=99)
        assert rival_supply(obs, "MILK") == 0.0

    def test_reads_the_rival_not_ourselves_from_either_seat(self):
        tiles = [{"animal": "COW", "yield_units": 5}]
        assert rival_supply(observation(tiles, player=0), "MILK") > 0.0
        assert rival_supply(observation(tiles, player=1), "MILK") > 0.0

    def test_survives_a_farm_of_junk(self):
        obs = observation(["LOCKED", None, 17])
        assert rival_supply(obs, "MILK") == 0.0


class TestDenialValue:
    def test_worth_nothing_when_the_rival_has_nothing(self):
        assert denial_value(observation(), "MILK", 100) == 0.0

    def test_worth_nothing_for_a_sale_of_zero(self):
        obs = observation([{"animal": "COW", "yield_units": 40}])
        assert denial_value(obs, "MILK", 0) == 0.0

    def test_positive_when_the_rival_still_has_supply(self):
        obs = observation([{"animal": "COW", "yield_units": 40}])
        assert denial_value(obs, "MILK", 100) > 0.0

    def test_grows_with_the_size_of_our_sale(self):
        obs = observation([{"animal": "COW", "yield_units": 40}])
        small = denial_value(obs, "MILK", 20)
        large = denial_value(obs, "MILK", 200)
        assert large > small

    def test_share_scales_the_estimate(self):
        obs = observation([{"animal": "COW", "yield_units": 40}])
        full = denial_value(obs, "MILK", 100, share=1.0)
        half = denial_value(obs, "MILK", 100, share=0.5)
        assert half == full * 0.5
        assert denial_value(obs, "MILK", 100, share=0.0) == 0.0

    def test_never_negative(self):
        obs = observation(
            [{"animal": "COW", "yield_units": 40}],
            inventory={"MILK": MARKET_I0 * 4},
        )
        assert denial_value(obs, "MILK", 100) >= 0.0


class TestContestedValue:
    def test_equals_plain_revenue_against_an_empty_farm(self):
        obs = observation()
        assert contested_value(obs, "MILK", 50) == sale_revenue(
            obs, "MILK", 50
        )

    def test_exceeds_plain_revenue_when_the_rival_is_heavy(self):
        obs = observation([{"animal": "COW", "yield_units": 60}])
        assert contested_value(obs, "MILK", 50) > sale_revenue(
            obs, "MILK", 50
        )

    def test_the_opponents_loss_is_a_first_order_term(self):
        """The asymmetry this module exists for.

        Against a rival holding a large herd, denying its price is worth
        about as much again as the sale pays us. An agent that prices only
        its own revenue is therefore ignoring half the value of the
        decision, which is what `rl/economics` has always done.
        """
        obs = observation([{"animal": "COW", "yield_units": 300}])
        ours = sale_revenue(obs, "MILK", 30)
        assert denial_value(obs, "MILK", 30) > ours * 0.5
        assert contested_value(obs, "MILK", 30) > ours * 1.5

    def test_denies_nothing_once_the_price_is_on_the_floor(self):
        """A real property, and a limit on the whole idea.

        MILK's above-equilibrium curve is linear and steep enough to reach
        the floor about seventy-six units past equilibrium. Past that our
        sale cannot push the price any lower, so it takes nothing from the
        opponent however much we dump. Denial is a mid-curve effect.
        """
        obs = observation(
            [{"animal": "COW", "yield_units": 80}],
            inventory={"MILK": MARKET_I0 + 4000},
        )
        assert denial_value(obs, "MILK", 60) == 0.0
        assert contested_value(obs, "MILK", 60) == sale_revenue(
            obs, "MILK", 60
        )


class TestContestedItems:
    def test_lists_only_what_the_rival_can_supply(self):
        obs = observation([
            {"animal": "SHEEP", "yield_units": 12},
            {"kind": "PLANT", "crop": "MELON", "yield_units": 5},
        ])
        found = contested_items(obs)
        assert "WOOL" in found and "MELON" in found
        assert "EGG" not in found

    def test_empty_against_an_empty_farm(self):
        assert contested_items(observation()) == {}

    def test_minimum_filters_a_trivial_supply(self):
        obs = observation([{"kind": "PLANT", "crop": "MELON",
                            "yield_units": 2}])
        assert "MELON" in contested_items(obs, minimum=1.0)
        assert "MELON" not in contested_items(obs, minimum=50.0)
