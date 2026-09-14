"""Take the town's shop draws out of the farms' hands, for evaluation.

Each night the engine spawns weeds and draws the next shop from one random
stream, and every empty tile on *either* farm takes a number from that
stream before the shop is chosen. So which shops a game gets -- whether a
yarn store opens on day 12, three bakeries or none -- depends on how many
tiles both farms happened to leave empty that night.

That turns every comparison of two versions of G into a comparison of two
different towns. Measured on one game: a switch that has nothing to do
with wool left a few more tiles empty on day 11, the town drew a yarn
store instead of something else, the wool book never crashed, and the
opponent banked 17,000 more from a change it never saw.

With this installed, weeds come from their own stream per farm and per
night, keyed on the seed, and the shop draw keeps the stream it was meant
to use. The town then depends on the seed and the day and nothing else,
so paired games really are paired. The odds of a weed on an empty tile and
of each shop are unchanged; only the coupling between them is gone. Live
games keep the coupling, which is noise we cannot control, not a lever.
"""

from __future__ import annotations

import random


def install() -> None:
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    if getattr(engine, "_fair_town", False):
        return
    end_of_day = engine._end_of_day
    night = {"seed": 0, "day": 0, "farm": 0}

    def spawn_weeds(farm, board_size, weed_chance, rng):
        own = random.Random(
            (night["seed"] * 1_000_003) ^ (night["day"] * 7_919)
            ^ (night["farm"] * 104_729 + 1))
        night["farm"] += 1
        for y in range(board_size):
            for x in range(board_size):
                if farm["tiles"][y][x] is None and own.random() < weed_chance:
                    farm["tiles"][y][x] = {"kind": "WEED"}

    def fair_end_of_day(state, env, day):
        night["seed"] = int(env.info.get("seed", 0) or 0)
        night["day"] = int(day)
        night["farm"] = 0
        return end_of_day(state, env, day)

    engine._spawn_weeds = spawn_weeds
    engine._end_of_day = fair_end_of_day
    engine._fair_town = True
