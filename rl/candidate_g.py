"""Candidate G: a farm built around the two goods whose price never falls.

Not a clone. Every agent this project has submitted replays a recorded
route -- C1, C2, D and F are the same guard stack over four different
tapes, which is why they span 2094 to 1375 with no logic differing between
them. Cloning has a ceiling and we are under it.

This is built from the simulator's own constants instead, and it rests on
one fact the entire leaderboard appears to have missed.

**Nine goods, two of which cannot be flooded.** Price is
`base -+ amp * f(|inventory - 10000|)`, and `f` differs per good. Counting
units past equilibrium until the quote reaches the floor of 1:

    WOOL 59, STRAWBERRY 62, MILK 76, MELON 158, FERTILIZER 493,
    TOMATO 529, CARROT 842 ... and EGG and WHEAT **never**, because
    their curves are logarithmic.

The thousandth egg still fetches 38. The seventy-seventh unit of milk
fetches 1.

**So the animal economics are lopsided.** From `ANIMALS` and
`_daily_refresh_animals`: a bird fed *and* cared yields `base 1 + bonus 1`
per interval, and the goose interval is 1 against the cow's 2 and the
sheep's 3, first yield day 4 against 8 and 6, cost 300 against 400 and
500. Twenty head, tended, to day 29:

    20 GEESE -> 1,000 EGG  -> 39,799 coins   (birds cost 6,000)
    20 COWS  ->   630 MILK ->  6,735 coins   (birds cost 8,000)
    20 SHEEP ->   613 WOOL ->  8,482 coins   (birds cost 10,000)

Six to one, for the cheapest animal on the board. The nine top-rated teams
average **2.1 geese** against 7.9 cows and 7.5 sheep, and Agent E buys 22
cows and no geese. The whole field crowds the two commodities that
collapse.

**And every animal drops one fertilizer a day unconditionally** --
`fertilizer_available = True` on the daily refresh whether or not it was
fed -- into a book 493 units deep. So a goose pays twice: eggs into a
market that never saturates, and manure into the deepest book after it.

The design follows from that and from three more rules:

* `BUILD_COOP` costs nothing and only needs an empty tile, so housing is
  free and the flock is limited by feed and labour, not capital;
* an animal unfed for two consecutive days **escapes**, so feed is not
  optional and the wheat area has to track the flock;
* reward is the money on the books at step 720, so everything sells.

It grows melon, carrot and strawberry on ground the flock does not need
(`CROP_TILES`), but it does not chase wool or milk. In a contested game
both collapse: measured across a real D-against-C1 match, milk runs
160 -> 203 -> 13 and wool 200 -> 217 -> 1, while egg goes 50 -> 92 because
the town keeps draining a book nobody floods.

Agent E failed twenty-six times because its economics priced every job by
the coins *it* received and its scheduler could not follow a build order.
This one has a fixed thesis and a scheduler that serves it.
"""

from __future__ import annotations

from typing import Any

from core.routing import distance, step_toward
from rl.demand import remaining_demand
from rl.economics import ANIMALS, CROPS
from rl.market import MARKET_PARAMS, inventory_of, price_at
from rl.runtime import AgentAction

PASS: list[str] = ["PASS"]
BOARD = 10
LAST_DAY = 29
MAX_ORDERS = 10

# --- the thesis, as numbers -------------------------------------------
# Crew ramp, not a constant. Hands are wiped nightly and re-hired at a
# fibonacci wage, so a full roster costs ~376 a day from day one against
# 3,000 of starting capital -- hiring twelve immediately bankrupted the
# farm by day six before it had any income at all. The corpus hires 4 by
# day 2, 8 by day 6 and 11 by day 10, and pays for each from the last.
#
# Was ((0, 4), (6, 5), (8, 8), (11, 10), (14, 12)). The current top twelve
# hire about 5 on day 0, 7-9 by days 6-9 and 11 by day 10. Inspected on the
# pruned current corpus against the old ramp, 12 top teams with 8 replays
# each, paired game by game:
#     like the top twelve   +1,083 a game on 68 clean games (median +1,355,
#                           better in 42, worse in 26), +1,484 over all 96
#     5 from day 0 only       -57 a game (median +836, better 39, worse 29)
# So the gain is the steeper build from day 6 to day 10, not the day-0 hire.
# Day-11 cash gap to the opponent narrows from 9,126 to 6,697, and crops
# dying unwatered fall from 1,805 to 1,062 coins a game.
#
# Pushing further both lose against this ramp, on the same 96 games:
#     6 hands on day 0        -885 a game on 70 clean games (better 30,
#                             worse 40), -728 over all 96
#     each step a day or two sooner, 12 by day 12
#                             -837 a game on 70 clean games (better 26,
#                             worse 44), -551 over all 96
# Both leave more crops dying unwatered (1,062 -> 1,593 and 1,617) and more
# overflow (3,849 -> 4,757 and 5,615): the wages come due before the ground
# they would work is sown, so the farm starves its own watering later on.
HAND_RAMP = ((0, 5), (6, 7), (8, 9), (10, 11), (14, 12))
# Hire to the last day. This read 27 and was measured as a dead constant,
# bit-identical however it was set -- because the `closing` short-circuit
# above returned before the crew block and dismissed everyone on day 28
# regardless. With that moved, this one is live again and the last two
# days are worked rather than watched.
HIRE_UNTIL_DAY = 29          # the crew is wiped nightly; stopping early
                            # starved a 22-bird flock down to five
# Two fixed purchases behind a reserve. The corpus buys ground the instant
# it is affordable -- median cash 644 at the moment of purchase -- and
# copying that measured 11,083 at three quadrants against 22,438 here,
# because G's limit is worker throughput and it already leaves tiles idle.
# Measured, and it inverts the corpus. Buying ground as soon as affordable
# -- their behaviour -- gave 11,083 at three quadrants and 19,326 at two,
# against 21,235 for two fixed purchases behind a 1,200 reserve, and the
# note here read: G's limit is worker throughput, not ground, so a
# quadrant only spends cash and spreads the crew thinner.
#
# **That note was measured on a farm that could not use the ground, and
# it was wrong by the time it was being quoted.** With the harvest held to
# its last yield day, the housing following what we own and the herd
# mixed, the same purchase moved four days earlier is the largest single
# gain measured on this agent:
#
#     days 1,5    55,157 mean   55,625 median   40,132 min   (38/60)
#     days 0,4    55,535        57,878          30,116       (33/60)
#     days 2,7    50,826        51,502          35,945       (25/60)
#     days 4,9    49,106        51,168          31,382
#     days 6,12   47,697        50,617          27,384       (27/60)
#     days 1,5,10 52,505        52,048          33,162       (11/60)
#
# Day 0 buys a slightly better median and gives up 10,016 of floor, since
# it spends the opening purse before the farm knows anything. A third
# quadrant still loses. And the spacing is sharp rather than smooth --
# days 1,4 collapses to 36,530, winning 2 games of 60, because the second
# purchase catches the farm with just enough to spend and nothing left to
# work it with. That cliff sits one day from the chosen value, so this is
# a fixed schedule standing next to a hole; a cash-gated rule would be the
# sturdier shape if it can be made to measure as well.
# The third purchase on day 9 is part of the strawberry change measured at
# CROP_TILES: the ground it opens is where the strawberries go.
#
# Each new quadrant sits half empty for days because the purchase leaves
# too little cash to seed it, so later schedules were tried, paired on 30
# contested opponents in a fixed town: (1, 6, 11) margin -2,543 a game
# (better in 8 of 60), (1, 7, 11) -413 (27/60), (1, 6, 10) -616 (23/60).
# All worse. The top teams' days 6 and 11 do not suit G.
# Third quadrant on day 12 instead of 9, re-checked on 2026-09-16 because G
# owns all 75 tiles by day 11 while H's live opponents own 50 and G has
# planted only 36: on the v14 field (83 games, against midday drop 500)
# +155 a game on 60 clean games (median -405, better in 29, worse in 31),
# +272 over all 83. Day-11 cash rises 2,680 -> 5,943 and overflow halves,
# but it is all given back by day 17. (1, 5, 9) stays.
LAND_DAYS = (1, 5, 9)
LAND_RESERVE = 1200.0
# Cash a quadrant must leave behind before it is bought. Measured, and
# OFF: the fixed schedule wins despite standing on a cliff.
#
#     fixed days 1,5   67,697 mean   69,229 median   48,168 min
#     cash 1,800       63,604        63,850          28,396   (24/60)
#     cash 3,000       62,990        64,627          37,294   (24/60)
#
# The reasoning for trying it was sound -- days 1,5 scores 67,697 and days
# 1,4 scores 44,943, so a one-day slip costs 22,754 and a rule with no
# cliff ought to be sturdier at the same height. But a cash gate buys
# *late*, because the farm is poorest exactly when the ground is worth
# most, and the day-one purchase earns across the whole season. The cliff
# is a real fragility and this is not the cure for it.
LAND_CASH = 0.0
LAND_LAST_DAY = 12
MAX_QUADRANTS = 3
GOOSE_COST = 300
# Working capital, and it was strangling the opening. Turn-by-turn against
# sixteen elite games: G holds 367 coins at turn 24 against their 67, 481
# at turn 96 against their 203 -- more cash than the corpus the whole way
# -- and stalls at three animals from turn 48 to turn 168 while they climb
# to eight. A bird costs 300, so a 450 floor demands 750 in hand, and G
# never clears it during the window that decides the game.
#
# The corpus runs broke on purpose: median cash at the moment they buy
# ground is 644 and the minimum is 22. Capital held in the opening is
# capital not laying eggs.
# Re-checked after the ground moved to day one, and unchanged: 450 gives
# 57,044, against 53,572 at 200 (23/60) and 49,198 at 900 (17/60). Not
# every measurement taken on the old farm went stale -- this one held.
#
# A trace of three clean v13 games found this floor binding on 17 to 24 of
# 24 turns a day from day 1 to 9: G buys one animal as each day's sales
# land, while the top teams spend down to about 300 and buy in bursts. On
# the v13 field (83 games), against 450:
#     150 alone                       +923 a game on 61 clean games (better
#                                     in 36, worse in 25), -858 over all 83
#     150 + pasture first + 3 a turn  -3,358 on 59 clean games (better in
#       + pens 4 ahead                16, worse in 43): escapes 453 -> 1,318
#                                     coins a game, day-11 cash 8,797 -> 4,932
#     the same + a herd of 12         -5,373 on 60 clean games (better in 26,
#                                     worse in 34), with animal tile-days
#                                     level with the opponent's (362 vs 352)
#                                     but crop tile-days down to 955
# Spent down, the cash that buys the animal is the cash that feeds it, and
# the crops pay for the herd until day 11. 450 stays.
GOOSE_CASH_FLOOR = 450.0
# A wheat tile yields about four units over five days unfertilized, which
# is 0.8 a day. The 1.2 here assumed the fertilized figure (1 + 3x2 = 6),
# and this agent never issues FERTILIZE -- it collects manure and sells
# it. The feed plan was therefore 50% optimistic and the flock chronically
# underfed, which is the same failure that killed Agent E's goose runs.
WHEAT_PER_BIRD = 0.8
# Wheat area is a plan, not a function of the flock. Deriving it from the
# animals standing gave a target of three tiles with no animals, which
# fed no birds, so none were bought, so the target never grew.
# Re-fitted after the ground moved to day one, which is the point: this
# was 20, measured on a farm that bought its second quadrant on day four
# and had nowhere to put more wheat.
#
#     20   55,157 mean   55,625 median   40,132 min
#     28   57,044        53,373          36,839   (39/60)
#     36   56,960        55,536          37,636   (34/60)
#
# 39 of 60 paired games is a real result rather than a coin flip, so it is
# followed here even though the floor gives up 3,293 -- the same rule that
# kept the herd at six, where the paired count was chance and the floor
# was the only signal worth reading.
# Re-checked on contested opponents and unchanged: 67,697 at 28 against
# 67,313 at both 36 and 44, ahead on 20 of 60. The two larger values are
# identical to each other, so the cap stops binding somewhere below 36.
# 28 held half of a two-quadrant farm in wheat to feed about nine animals,
# roughly eleven tiles' worth, and sold the rest at 36. Cut to 16 as part of
# the strawberry change measured at CROP_TILES.
#
# Twenty, measured alone on the pruned current corpus against sixteen:
# margin -3,044 a game on 68 clean games (better in 17, worse in 51). G
# still buys about 20,800 coins of wheat a game, so the extra ground only
# takes tiles from strawberry. Sixteen stays.
#
# Re-checked at 24 once feed pickups were sized to need and wheat bought
# fell to about 3,600 coins a game, since the town's wheat book then sat open
# 14 days a game: -2,271 a game on 69 clean games (better in 33, worse in
# 36), -2,091 over all 96. G sells 248 wheat instead of 154, but at 37, and
# the tiles still come out of strawberry. Sixteen stays.
#
# Wheat only on ground no crop seed can fill -- the inspector's WHEAT_FILL,
# tested in its own copy of G -- does not take tiles from strawberry, and
# still loses. Uncapped, on the v12 field: -594 a game on 66 clean games
# (better in 33, worse in 33); it sows the new quadrants faster than the
# day-5 to day-9 crew can water and the seedlings die. Capped to what the
# crew can water, on the v13 field: -931 a game on 61 clean games (better in
# 31, worse in 30). The deaths are fixed and day-14 cash rises 2,237, but it
# is all given back by day 23: cow buying falls 308 a game, animal-days 16
# and milk 14 units, most likely because day-8 cash, the day the cows are
# bought, drops 236.
# Re-checked on 2026-09-16 against the live ladder, where the biggest single
# revenue gap is grain: over H's 84 real games the opponents earn 17,776 a
# season from wheat against G's 7,577, most of it in the last week. Widening
# the wheat area to 24 does not close it: on the v14 field, 65 paired games
# against "v14 midday drop 500", margin -1,985 a game (46 clean games -2,003,
# median -260), G's own score -1,552, better in 24 and worse in 41, wins
# 12 -> 10. The grain gap is not the size of the patch.
WHEAT_TILES = 16
COOPS_AFTER_WHEAT = 8
EARLY_BIRDS = 6
# Herd size and mix.
#
# 332 elite tapes buy a median of 3 geese, 8 cows and 6 sheep -- about
# seventeen animals, permanently mixed, never a single species. G ran six
# or seven of one. Adopting the *mix* is worth a great deal; adopting the
# *size* is ruinous:
#
#     target  6   49,106 mean   51,168 median   31,382 min
#     target  8   49,378        51,205          27,221
#     target 10   45,307        43,704          25,893
#     target 12   40,021        35,501          14,716
#     target 17   35,486        27,236          13,543
#
# Two reasons the elite herd does not transfer. Labour: hands are priced
# on a fibonacci, the crew is capped near twelve, and every animal wants
# feeding and caring daily whatever it produces. And the books: milk dies
# after 76 units and wool after 59, while egg never floors. Eight cows
# make some 128 units of milk, half of it worth a coin. Their cattle are a
# capital engine for the first twelve days -- dump 50 units at 160 before
# the collapse, bank the manure -- not a season-long line, and we have
# neither the crew nor the opening to run it that way.
#
# Six, mixed, is ours. 8 wins the mean by 272 and the median by 37, both
# noise at 33/60 paired, and gives up 4,161 of floor to get them.
# Re-checked on contested opponents and unchanged: 67,697 at six against
# 65,512 at eight and 63,447 at ten, ahead on 27 of 60 both ways.
#
# **All of the above was measured with the town tied to G's empty tiles
# and on the old crop plan, so none of it stands.** Re-measured in a fixed
# town on the strawberry defaults with SELL_CARRIED_AT_CLOSE on, paired
# game by game on 30 contested opponents: 9 gives margin +10,161 a game
# (better in 60 of 60), 12 gives +8,632 (54/60), 17 gives +352 (36/60).
# Confirmed at 9 on 12 current top teams with 8 replays each, against G
# with both kept switches on: +3,452 a game on the 72 games where the
# opponent replay stayed in step (median +2,176, better in 47, worse in
# 25), +3,620 over all 96. It costs shed overflow (1,218 to 4,723 coins a
# game) and more skipped care. At 12 and 17 the crew falls behind: unfed
# days and missed care climb steeply, and G banks less despite selling
# more milk. Bracketed on the same panel: 8 gives +13,951 and 10 gives
# +13,412, both better in 60 of 60, so the peak looked flat from 8 to 10.
#
# Inspected against the refreshed field, 12 current top teams with 8
# replays each, paired with 9 on the 71 games where the opponent replay
# stayed in step: 8 gives -30 a game (better in 34, worse in 36), which
# is noise; 10 gives -910 (better in 26, worse in 40), with shed overflow
# up from 4,763 to 6,366 coins a game. Nine stays.
#
# Re-checked once feed pickups were sized to need, since cheaper feeding
# might carry a larger herd: 11 gives -8,643 a game on 69 clean games
# (better in 8, worse in 61), and the idle share of worker turns doubles
# from 9.2% to 18.1%. Nine stays.
#
# The inspector found animals carried all day and tipped back into the shed
# beside empty pens, because PLACE is discounted by distance like any job.
# Committing a worker to a reachable PLACE (its PLACE_COMMIT, tested in its
# own copy of G) loses on its own, -2,029 a game on 66 clean games, by
# shrinking the herd, so it was retried with room to grow: PLACE_COMMIT with
# a herd of 10 on the v12 field is -968 a game on 66 clean games (median
# -80, better in 32, worse in 34), -1,241 over all 92. Nine stays.
# Re-checked on 2026-09-16, on the theory that the old sweep was measured on
# a farm that could not use the ground: 65 paired games on the v14 field,
# margin -460 a game over all of them and -1,797 on the 46 clean games, G's
# own score -2,851. The reason is grain. With twelve head G's wheat sold
# falls from 303 units a game to 160, because a bigger flock eats the crop
# the farm would otherwise sell, and hungry animals release the early
# harvest. Nine stays.
HERD_TARGET = 9
# A fixed herd, as {animal: head}, in place of the demand-weighted plan.
#
# The engine's own ledger, G against the plan most of the ladder copies,
# both facing the same opponent: the plan's six sheep sell 16,452 of wool
# against G's one sheep and 2,604, the single largest line in a 29,000
# gap. G's herd follows `demand x price`, which keeps landing on geese.
# None keeps the demand-weighted plan.
#
# Re-measured at nine head on the pruned current corpus, against the
# demand-weighted plan at HERD_TARGET 9, on 68 clean games:
#     1 goose, 4 cows, 4 sheep    margin -6,391 a game (better 25, worse 43)
#     2 geese, 3 cows, 4 sheep    margin -9,667 a game (better 19, worse 49)
# More sheep sold more wool (114 against 66) but put about 40 units a game
# on the floor price, into a book the town drains slowly, and fewer cows
# cut milk from 176 units to 100-121. The demand-weighted plan stays.
HERD_MIX: dict[str, int] | None = None
# Count animals in transit when deciding what to buy.
#
# Correct bookkeeping, and it raises our own score -- 62,158 against
# 56,178 on thirty current-agent opponents, higher in 44 of 60 games,
# wins 2 against 0. It also hands the opponent about 29,000: the
# accidental over-buying was flooding the milk, wool and egg books the
# other farm sells into, and the margin falls from -52,472 to -75,442,
# better in only 4 of 60. Margin decides, so it stays off. Measured
# against replayed tapes, which cannot react to a flooded book, so the
# denial it removes may be worth less in live play than this says.
#
# Re-checked once PEN_BEFORE_WHEAT and SHED_ALL_ACCESS were on, because the
# inspector's drill caught a goose re-bought while the first was still in a
# worker's hands on day 0. On the v14 field (83 games): -11,509 a game on 57
# clean games (median -10,543, better in 6, worse in 51), -10,886 over all
# 83. Sheep buying falls from about 3,100 to 1,482 a game, a land purchase
# goes missing and the idle share doubles, 8.1% to 16.6%. The "re-buy" is how
# G's herd actually grows. Off.
COUNT_CARRIED = False
# The share a line keeps once we own any of it. A pen and the animal in it
# are capital already spent and a shift in the town's draw does not refund
# them, so demand decides which line *grows*, never which line survives.
HERD_FLOOR = 0.15
EARLY_COOPS = 6
# How many birds may be bought in one turn while the opening is still
# being built.
#
# One a turn looks safe and starves the opening. A bought animal lands in
# the shed and then needs a worker to pick it up, walk it to a pen and
# place it, so at one purchase a turn the pipeline never fills: G stands
# at one animal on turn 24 and three on turn 48 where the corpus has four
# and four. Those are the turns that compound for the rest of the game.
#
# Measured, and it changes nothing: 36,892 against 36,913 at one a turn,
# because the real bottleneck is not the purchase. Tracing the opening
# shows G already buys four animals inside the first 26 turns -- three
# cows and a sheep, the same count the corpus has -- and only *one* is
# standing on a tile at turn 24. The rest are in the shed waiting for a
# worker to pick them up, walk them to a pen and place them.
#
# So the opening is throttled by the placement chain and by COOP_LEAD
# holding only two pens open, not by how many birds are ordered. Raising
# the lead to four costs 7,700, because pens are built by the same workers
# that feed and harvest.
BIRDS_PER_TURN = 1
# Animals carried per trip to the shed, and how long placement outranks
# routine tending.
#
# The opening is throttled by the buy -> shed -> carry -> place chain: G
# orders four animals inside 26 turns and has one standing on a tile at
# turn 24. A worker that walks to the shed for one bird and back has spent
# two trips to place two, so carrying three makes the existing trip cheaper
# rather than asking the crew for more trips.
#
# Thirty paired games across three top-of-ladder routes: carrying three
# means 38,749 against 34,219 at one, and wins 21 of the 30 pairs. The
# medians are level (30,303 against 30,098), so the gain is in the upper
# half of the spread -- it lifts the good games and does not rescue the
# bad ones.
BIRDS_CARRIED = 3
# Placement did *not* deserve to outrank tending, which is the opposite of
# what the arithmetic above suggests. Making PLACE outbid feeding costs
# 9,500: a bird that goes unfed two days escapes and takes its whole
# remaining stream with it, so the crew must finish tending before it
# starts placing.
#
# It is tempting to read that alongside the pen and land losses (7,700 and
# 10,000) as one rule -- that the opening crew is saturated and any new
# job displaces a better one. That reading is wrong, and worth recording
# as wrong: G spends 21.4% of its worker turns on PASS, 1,368 of 6,401,
# against 8.8% for the corpus. A worker PASSes only when the entire board
# offers it nothing, so the farm runs out of *work*, not out of hands.
#
# The three losses have three different causes. Pens and land lose because
# they cost capital the opening has not got. Placement priority loses
# because it starves what is already standing. None of them is crowding.
# Work that costs nothing and starves nothing -- FERTILIZE, cheap seed --
# is free to add, and that is where the idle fifth of the crew goes.
PLACE_PRIORITY_DAY = -1
COOP_LEAD = 2
# Cash crops for the ground the flock does not need. The goose economy is
# an addition to a farm, not a replacement for one: with wheat and coops
# satisfied it was leaving roughly thirty of seventy-one tiles idle all
# game, where the corpus has twenty-nine tiles planted by turn 168.
#
# Tile counts come from each good's book depth (10.8v) rather than its
# base price. Melon pays 250 and floors after 158 units; strawberry 120
# and floors after 62; carrot only 35 but absorbs 842, which is why the
# top of the board plants it and the field does not (10.8z).
# Which crop earns a scarce worker-turn, which is the only question that
# matters on a farm capped at twelve hands.
#
#     crop         units   turns   units/turn
#     WHEAT          4       5        0.80
#     CARROT         3       4        0.75
#     MELON          6       9        0.67
#     TOMATO         4      13        0.31
#     STRAWBERRY     4      18        0.22
#
# Turns are the waterings inside the yield window plus sowing and
# harvesting. Ongoing crops are the expensive ones: they must be watered
# every day from sowing or they go to weed, and tomato waits eight days
# before it yields anything at all.
#
# That table is an input, not a rule, and it was overstated when first
# written here. It does explain tomato: against the reference route the
# town drains 378 units of it and the price runs to 257, four times base,
# while we plant none -- and planting it anyway costs 18,971 (38,073
# against 57,044, at any cap), because eight days of daily watering come
# before the first unit.
#
# But it does not explain strawberry, which is dearer still at eighteen
# turns a tile and pays for itself anyway. Dropping it costs 3,974
# (53,070 against 57,044). Two things the turn count misses: an ongoing
# crop keeps its tile and produces again without being resown, and
# strawberry is the one crop the manure gate accepts, which doubles it
# from four units to eight.
#
# Diversity itself is worth something too -- carrot alone, at any cap,
# scores 42,507. So the honest reading is that cheap labour, a persistent
# tile and a deep enough book each count, and no single number ranks the
# crops.
#
# Measured against every alternative worth trying, and unchanged.
#
# 332 elite tapes plant a median of 31 carrots and 33 strawberries to our
# 16 and 8, which reads as a large gap. It is not one:
#
#     now 12/16/8      49,106 mean   51,168 median   31,382 min
#     carrot 31        49,106         51,168          31,382   (0/60)
#     strawberry 24    49,531         51,633          31,382   (21/60)
#     melon 18         48,186         48,075          29,501   (26/60)
#     melon 24 carr 8  47,757         50,902          29,501   (23/60)
#
# Raising the carrot cap changes nothing at all -- bit-identical over
# sixty games -- because the cap has never once bound. A census finds the
# farm holding 15 carrots against a cap of 16, 8 strawberries against 8
# and 12 melons against 12: the binding constraint is *tiles*, roughly 55
# of them across 20 wheat and 35 crop, not the caps.
#
# So the question is which crop deserves a scarce tile, and the books
# answer it. Melon pays 225 a unit at +50 against carrot's 27, thirteen
# times more per tile -- but it floors after 158 units, and twelve tiles
# at six units over two cycles is 144. The cap is already sized just under
# its own book, which is why every attempt to raise it loses: the marginal
# melon sells for a coin. Strawberry's book is the shallowest in the game
# at 62 units, so its cap of 8 is likewise near its ceiling, and the 24
# variant wins only 21 of 60 games for its 425 -- it wins rarely and
# hugely and loses often, which is not a trade worth taking.
#
# The elite plant carrots because carrot's 842-unit book is the only one
# deep enough to absorb *their* volume. Ours is limited by tiles and
# labour long before any book runs out, and the two farms are correctly
# solving different problems.
# Strawberry first, on ground freed from wheat and a third quadrant.
#
# The town eats about 408 strawberries a game and the top teams sell 222;
# G sold 24. Seed was never the limit. A daily trace showed the board full
# from day 9, with wheat on 24-28 of 50 tiles and strawberry frozen at the
# four tiles it got when the second quadrant opened. Buying more seed
# earlier only spent the opening purse, starving land and the herd (margin
# 22,652 to 38,180 worse, no paired game better).
#
# Freeing ground instead -- this list, WHEAT_TILES 16, LAND_DAYS (1, 5, 9)
# -- measured in a fixed town against 12 current top teams with 8 replays
# each: margin +10,235 a game over 96 paired games, better in 80; on the
# 71 games where the opponent replay stayed in step in both runs, +10,924
# (median +12,459), better in 59 and worse in 12. G's mean rises from
# 67,324 to 75,718, strawberry sold from 24 to 150, idle crew from 16.7%
# of turns to 5.6%. On the separate 30-opponent contested panel the mean
# margin moved +130 but 46 of 60 games improved; the two losses there were
# a SpaTaro replay that had collapsed in the baseline run.
#
# What it costs, for the next change: crops dying unwatered rise from 636
# to 1,963 coins a game (carrot and melon at age zero, on the days new
# ground opens), and more strawberry is left unsold at the close.
#
# Melon capped at 8 instead of 12, since the town takes about 30 melons a
# game and later batches sold at 155 and 126: neutral on the pruned
# current corpus, margin -67 a game on 68 clean games (median 0, better
# in 22, worse in 29). The price per melon rises from 177 to 187 but
# fewer are sold. Twelve stays.
# Re-checked on 2026-09-16, because the inspector ranks strawberry as G's
# largest revenue gap (G sells 136 units a game against the opponent's 215,
# and the town takes 467). A cap of 44 does not buy it: 65 paired games on
# the v14 field, margin -166 a game (46 clean games -231), better in 4,
# worse in 35 and bit-identical in 26. The extra tiles sell 167 units at 182
# instead of 136 at 194, and wheat sold falls from 303 to 203 as the ground
# goes over -- the farm is already full, so a larger cap only moves tiles
# between books.
#
# Tomato, 8 tiles beside the rest, on the same field: -8,100 a game (44
# clean games -8,488), better in 6, worse in 56, wins 12 -> 7. Eight days of
# daily watering before the first unit is still more than this crew has.
CROP_TILES = (("STRAWBERRY", 32), ("MELON", 12), ("CARROT", 16))
# The opening, crop by crop.
#
# The money gap opens early: by day 11 the median opponent has earned about
# 5,100 more, mostly from melon, wool and fertilizer. Across 235 replays of
# the current top twelve, day 0 sows about eight melon and no strawberry or
# carrot, which wait for days four and five. G's day 0 buys four each of
# melon, strawberry and carrot, so it ripens half the early melon and has
# spent its cash on crops that pay later.
#
# While the day is at most OPENING_UNTIL_DAY, this list replaces CROP_TILES
# for both sowing and seed buying, and each crop's seed is bought up to its
# cap rather than CROP_SEED_BATCH. None keeps CROP_TILES throughout.
#
# Rejected: melon (8) then strawberry in the opening, inspected on the pruned
# current corpus against the same agent without it: margin -6,745 a game on
# the 66 games where the opponent replay stayed in step (better in 9, worse
# in 57), -5,409 over all 96. Day-11 cash rises, but the crew stands idle
# 14.0% of turns against 6.7% -- the opening sows fewer tiles -- and the
# season never recovers it. Stays off.
#
# Re-tested on 2026-09-16 as melon alone on day 0 (12 tiles, OPENING_UNTIL_DAY
# 0), because every one of H's 84 live opponents sows about twelve melons in
# the first turns of day 0 and banks 14,267 from them by day 11, where G has
# nothing until day 14. It still loses: 65 paired games on the v14 field,
# margin -4,072 a game (44 clean games -4,785), better in 10 and worse in 34,
# G's own score -372. The reason is the book, not the timing -- G ends up
# selling 103 melons at 149 where the opponent sells 73 at 218, and the town
# only takes about 30 a game. Sowing earlier floods a market G already fills.
OPENING_CROP_TILES: tuple[tuple[str, int], ...] | None = None
OPENING_UNTIL_DAY = 3
OPENING_SEED_BATCH = 8
# Which pen gets built first when both are wanted.
#
# The same replays buy two cows and two sheep on day 0, so wool (from day 6)
# and milk (from day 8) arrive while those books still pay near base. G's
# first animal is a goose. Raising its early herd targets did nothing -- the
# herd plan already wants four cows and four sheep on day 0 -- because the
# limit is housing: G builds its coop first, buys one animal per turn only
# into a standing pen, and its first pastures appear at steps 11 and 17.
# ("PASTURE", "COOP") builds pasture first. The default keeps coop first.
#
# Rejected: pasture first, inspected on the pruned current corpus against
# the same agent without it: margin -6,083 a game on the 67 games where the
# opponent replay stayed in step (better in 13, worse in 54), -4,692 over all
# 96. Idle turns rise from 6.7% to 9.7%, and overflow and unsold goods both
# grow. Coop first stays.
PEN_ORDER = ("COOP", "PASTURE")


# Fill the late season's spare ground with a short crop.
#
# Replayed on H's 84 real ladder games, G's planted tiles fall from 55 on day
# 20 to 47 on day 26 while the opponents keep 58, with G holding 25,000+ cash
# and fewer free turns lost to cash than to its crop caps: strawberry and
# melon can no longer finish, wheat is held to WHEAT_TILES, and carrot to its
# CROP_TILES cap of 16, though the town still takes about 248 carrots a game
# and G sells 70 to the opponent's 117. From LATE_FILL_FROM_DAY the cap of
# LATE_FILL_CROP rises by LATE_FILL_TILES; carrot is ripe in three days. The
# cap drives both sowing and seed buying through crop_plan. None is off.
#
# Inert, and left off. From day 18 with 12 more carrot tiles, a preview on
# both reference games changed nothing. A day-by-day trace of the first game
# shows why: through day 25 only 2-6 tiles stand empty, and carrot seed is
# bought about four a day and sown, so the carrot cap never binds. Ground
# only empties on days 26-27, when wheat drops from 16 tiles to 10 and is not
# resown, and the crew mostly passes.
LATE_FILL_FROM_DAY: int | None = None
LATE_FILL_CROP = "CARROT"
LATE_FILL_TILES = 12


def crop_plan(day: int) -> tuple[tuple[str, int], ...]:
    """The crop list in force today: the opening one, then CROP_TILES."""
    if OPENING_CROP_TILES is not None and day <= OPENING_UNTIL_DAY:
        return tuple(tuple(pair) for pair in OPENING_CROP_TILES)
    if LATE_FILL_FROM_DAY is not None and day >= LATE_FILL_FROM_DAY:
        return tuple((crop, cap + LATE_FILL_TILES if crop == LATE_FILL_CROP
                      else cap) for crop, cap in CROP_TILES)
    return CROP_TILES
# Let the town choose, instead of assuming one animal always wins.
#
# `observation["town"]["unlocked_shops"]` is public and exact, and
# `rl/demand.py` turns it into units the town will still absorb before the
# season ends. GOAL.md section 9v measured adapting production to that
# draw as the cleanest correlate of rank there is: +0.672 for teams above
# 2850 and +0.000 below 2400. Nothing this project has shipped uses it.
#
# The flock stays geese by default -- in a contested game egg runs
# 50 -> 92 while milk collapses 160 -> 13 and wool 200 -> 1, because the
# town keeps draining a book nobody floods. But a town that drew YARN_STORE
# twice wants wool badly enough to beat that, and this is how the agent
# notices.
# Below 1.0 the agent leaves egg for a good the town wants even when egg
# still prices higher, and that measures best: on eight seeds 0.8 gives
# 32,693 against 26,971 at 1.6 and 20,783 at 0.65. The seed spread is wide
# (11,415 to 43,007) so treat the peak as approximate, not tuned.
DEMAND_MARGIN = 0.8
# Wheat carried per trip to the shed. At four, PICKUP was the single most
# common action in the game -- 1,270 of them, more than harvest, feed, care
# and collect together -- because every four meals cost a round trip.
# Settled on eight seeds: 12 gives a mean of 21,031 against Candidate D,
# 18 gives 18,150 and 24 gives 19,267. A two-seed comparison had 24 ahead
# by 1,200 and it was noise -- the spread across seeds is 13,000.
FEED_CARRY = 12
# Fetch only the feed the flock still lacks. Every hand holding no wheat
# used to fetch twelve whenever any animal was unfed, so on day 12 of a
# reference game 46 to 61 wheat sat in hands all day. The shed read empty,
# the emergency ration bought six at 42 every other turn, and at night the
# hoard was tipped back into the shed and sold at 41 -- some thirty units
# bought and sold back every day, 21,861 coins of wheat bought a game
# against the opponent's 11,040. With this on, a pickup is sized to the
# unfed animals less the wheat already carried or fetched this turn.
#
# Inspected on the current top twelve, 8 replays each, paired game by game
# against the ramp defaults:
#     exact need, no spare   -70 a game on 67 clean games (better 32,
#                            worse 35), +3,068 over all 96
#     spare 2              +2,418 a game on 68 clean games (better 43,
#                            worse 25); against spare 4 directly -2,366
#                            (better 28, worse 41)
#     spare 4             +4,948 a game on 68 clean games (median +4,346,
#                            better 57, worse 11), +5,979 over all 96
#     spare 6              +2,981 a game on 68 clean games (better 49,
#                            worse 19); against spare 4 directly -1,968
#                            (better 16, worse 52)
#     spare 12             +1,756 a game on 69 clean games (better 41,
#                            worse 28), +2,366 over all 96
# With spare 4, wheat bought falls from 21,861 to 3,581 coins a game and
# shed overflow from 3,849 to 410, since the nightly return of the hoard no
# longer fills the shed. Exact need left animals unfed two days running
# while the one hand holding their meal was busy elsewhere: escapes rose
# from 35 to 1,022 coins a game, 494 with the spare.
FEED_PICKUP_TO_NEED = True
# Wheat fetched beyond the exact need, so an animal is not left unfed while
# the one hand holding its meal is busy elsewhere.
FEED_PICKUP_SPARE = 4
# An animal that missed yesterday's meal escapes if it misses tonight's.
# Wheat already in some hand can be across the board, so for those animals
# a hand at the shed fetches regardless of what is carried elsewhere.
#
# Neutral on the current top twelve, paired against spare 4 on 96 games:
# +287 a game on 69 clean games (better 39, worse 30), -341 over all 96.
# It all but ends escapes (494 -> 39 coins a game) but the extra wheat in
# hands comes back to the shed at night and overflow rises from 410 to
# 2,364. Off.
FEED_PICKUP_FOR_HUNGRY = False
# Cap on the crew ramp. Twelve hands cost about 376 a day in fibonacci
# wages, some 10,500 across a season, against roughly 51,000 of gross
# production. Labour is the largest cost in this design, not the birds.
#
# Checked on the pruned v12 field (92 games) once a crew trace showed G's
# twelve hands idle only 2 to 6 per cent of their turns from day 12 on:
#     11 from day 14   +269 a game on 66 clean games (median +758, better in
#                      40, worse in 26), +69 over all 92 -- wages fall about
#                      1,800 a game but care missed rises 1,684 to 2,061
#     13 from day 14   identical to the baseline in all 92 games. It cannot
#                      happen: hands leave every night and market_orders
#                      rehires at most 4 a turn on hours 0 to 2, so 12 is
#                      the most a day can hire whatever the cap says.
# Twelve stays.
HAND_CAP = 12
# Hands per standing job, and the smallest crew worth keeping. Set
# CREW_TO_WORK to 0.0 to size the crew by the ramp alone.
#
#     1.0   66,913 mean   67,662 median   (cap never binds)
#     0.5   66,952        67,918          (12/60)
#     0.3   67,308        68,763          (32/60)
#
# Small, and taken because nothing gets worse: the floor is identical at
# every setting and the wage saved on a crew that has nothing to do is
# real money. It is not the answer to the idle turns, though -- see
# hands_target.
#
# Nor is the other half of that diagnosis, tempting as it looked. If 62%
# of idle turns are workers who could not act for want of the right thing
# in their hands, then fetching grain *before* the flock is hungry ought
# to pay: the animals want feeding at every refresh regardless, and a
# worker about to stand still carries it for free. It costs 858 -- 66,450
# against 67,308, worse on mean, median and floor alike. The observation
# is true and does not convert into a gain, at least not this way.
CREW_TO_WORK = 0.3
# Five, to match the five hands the top twelve hire on day 0, changes
# nothing: all 96 games of an inspection came out identical, day by day.
# The floor only lifts the work-based cap; the income ramp in hands_target
# is what holds the opening crew at four.
CREW_FLOOR = 4
HARVEST_AT = 2              # eggs held before a bird is worth the walk
SEED_BUFFER = 10
# Cash held before cash-crop seed is bought, and how much is bought.
#
# G is idle 21.4% of its worker turns -- 1,368 of 6,401 across a game, and
# 43% of day one -- because a worker PASSes only when the whole board
# offers it no job at all. The farm runs out of work, not out of hands.
# Land and pens did not fix that because they cost capital G has not got
# in the opening; seed is the cheap way to turn an idle turn into a tile.
# Lowered to 300 on the current top twelve, paired against 1,500 on 96
# games: -477 a game on 67 clean games (median +691, better in 35, worse in
# 32), -2,517 over all 96 with G's own score lower in 63. Seed then competes
# with the herd for every coin -- escapes rise from 501 to 1,225 coins a game
# and missed care from 1,653 to 2,264 -- and day-11 cash falls from 8,777 to
# 6,373. At 800: +704 a game on 69 clean games (median +681, better in 38,
# worse in 29), +363 over all 96 with G's own score better in only 47 -- too
# close to chance to switch. 1,500 stays.
CROP_SEED_FLOOR = 1500.0
CROP_SEED_BATCH = 4
# Buy crop seed with each day's cash, ahead of the herd, while the season is
# young.
#
# CROP_SEED_FLOOR shuts crop seed out of the whole opening. On a reference
# game G's cash on days 1 to 10 sits between 225 and 1,098, so after the four
# melon and four strawberry of day 0 it sows no melon or strawberry at all
# until day 11 -- by day 10 it has four strawberries and sixteen wheat
# standing on 75 owned tiles. The opponent earns about the same each day
# from manure and spends it on seed the same day (320, 360, 400, 200, 100 on
# days 1 to 5): 23 strawberries and 12 melons by day 8, and 13,000 coins of
# melon on days 10 and 11 while G sells 1,472.
#
# The floor step also never counted what its seed cost. From
# SEED_FIRST_FROM_DAY until SEED_FIRST_UNTIL_DAY, seed is bought at hour 2
# out of the cash the herd leaves, capped by each crop's tile cap, the free
# ground, the cash above SEED_FIRST_FLOOR and SEED_FIRST_DAILY_SPEND, in
# SEED_FIRST_ORDER when that is set. None keeps the floor rule throughout.
#
# A first version, from day 0 and ahead of the animals with no daily limit,
# took a reference game from 99,807 to 63,776. Day 0 spent 1,300 on
# strawberry instead of the first cow and the melons, the herd stood at two
# or three animals until day 7, and the milk and wool that carry days 7 to 9
# never came (376 and 368 of income against 1,727 and 1,949). The animals
# are the opening's income, so seed comes out of what they leave.
#
# Reworked that way, days 1 to 10 at 400 a day, paired on 96 games against
# the v10 defaults, it still loses:
#     crop plan order   -1,594 a game on 69 clean games (median -717, better
#                       in 32, worse in 37), -2,683 over all 96
#     melon first       -3,980 a game on 69 clean games (better in 17, worse
#                       in 52), -4,439 over all 96
# The earlier strawberries sell 176 units instead of 157 but at 156 instead
# of 168, and the earlier melons flood a book the town takes only 30 of a
# game: G sells 106 at 144 while the opponent still gets 215. Seed bought
# in the opening also delays the day-9 and day-10 animals. Off.
SEED_FIRST_UNTIL_DAY: int | None = None
SEED_FIRST_FROM_DAY = 1
SEED_FIRST_FLOOR = 150.0
SEED_FIRST_DAILY_SPEND = 400.0
SEED_FIRST_ORDER: tuple[str, ...] | None = None
# Cash kept back to buy feed in an emergency.
#
# This was 400, which is above the cash G actually operates on: a daily
# census had it between 318 and 562 for the first ten days, because it
# buys animals down to GOOSE_CASH_FLOOR and stops. So the emergency
# ration could never fire, and the farm ran a death spiral -- spend 300 on
# a goose, have nothing left for the wheat it eats, lose the goose on day
# two and the 300 with it. Wheat is about 25 a unit, so a floor of 60
# buys two meals and that is all this needs to do.
#
# Honest about the evidence: on sixty paired games this is worth +3,031
# mean and +1,112 median but wins only 32 of 60, and the worst game is
# worse (17,940 against 22,206). That is a coin flip, not a proven gain.
# It is kept for the mechanism rather than the average -- a daily census
# showed the flock going 4 -> 2 on day two of every game for want of 25
# coins of wheat, and an escaped animal takes its whole remaining stream
# with it.
RATION_FLOOR = 60.0
# Feed bought from the market rather than grown, which is the corpus's
# opening move: their first order of the game is BUY_PRODUCT WHEAT 13.
# Days of feed to keep in the shed, the flock size to plan for before one
# exists, the last day worth buying on, and the cash kept back.
# Measured and OFF: a coin flip at every level, on sixty paired games
# each against top-of-ladder routes. Days 2 gives 45,436 mean / 49,340
# median, days 3 gives 45,460 / 48,034, days 5 gives 45,656 / 47,772,
# against 47,395 / 47,137 with it off -- and 30/60, 30/60, 31/60 paired,
# which is exactly chance. It lifts the median and the floor and lowers
# the mean, because on our purse the feed order competes with the animal
# it is meant to feed. The corpus can open this way because it has income
# we do not.
#
# Re-measured at 2 on the pruned current corpus against the v7 defaults:
# margin -2,553 a game on 67 clean games (better in 22, worse in 45). Day-11
# cash rises from 5,864 to 8,422, but wheat bought goes from about 20,800 to
# 25,800 coins a game and shed overflow grows, and the season gives the early
# cash back. Zero stays.
# Re-tested on 2026-09-16 across the whole season (2 days of stock, bought to
# day 29, floor 150), because H's live opponents buy about 263 units of feed
# a game and sell 17,776 of wheat against G's 7,577. It does fix the grain --
# wheat leaves the top five revenue gaps altogether -- and it loses anyway:
# 65 paired games on the v14 field, margin -7,376 (44 clean games -8,637),
# better in 3 and worse in 41, wins 12 -> 8. The cost moves to the shed,
# which holds 100: overflow rises to 6,732 coins a game from 1,736.
#
# A smaller ration does not rescue it. One day of stock behind a 400 floor
# sells 409 units of wheat against 303 -- the grain gap narrows from 7,976 to
# 4,795 -- and still loses 5,985 a game on 45 clean games, better in 7 and
# worse in 38, because the spill stays at 6,101. What limits G here is how
# fast the shed empties, not what goes into it.
FEED_STOCK_DAYS = 0
FEED_MIN_FLOCK = 4
FEED_BUY_UNTIL = 6
FEED_STOCK_FLOOR = 150.0
# Hold a non-ongoing crop to its last yield day instead of pulling it the
# day it ripens.
#
# Harvest destroys the tile, so taking wheat the moment it ripens throws
# away everything the tile had left to give: pulled at age two it yields
# two units, left to age four it yields four, from the same seed, the same
# ground and the same watering. This is the largest single gain measured
# on G -- 44,364 against 40,072 on sixty paired games against
# top-of-ladder routes, ahead in 43 of the 60.
HARVEST_HOLD = True
# What counts as a starving flock when deciding to pull wheat early.
#
# The hold is released for every ripe wheat tile on the board whenever an
# animal is unfed and the shed holds no wheat. But `fed_today` resets every
# night, so each morning the whole herd reads as unfed, and the moment the
# feed round empties the shed the release fires. The inspector puts G's
# forgone wheat at about 448 units a game, most of it cut at age two.
#
# True means only an animal that already missed yesterday's meal -- the one
# that escapes if unfed again tonight -- releases the hold. False keeps the
# old reading.
#
# Measured on the 38 games G played on the ladder, against the same agent
# with the walking fix: wins 23 -> 20, own score -2,468 a game (median
# -5,520), 4 games flipped to losses and 1 to a win. On the 23 games where
# the opponent stayed close the own score falls 4,646. So the greedy release
# is right, and for the reason the old panel gave: two extra units of wheat
# are worth about 42 coins, while an animal that escapes forfeits its whole
# remaining output. Being wrong about which animal is in danger is cheap;
# being slow is not.
STARVING_MEANS_MISSED_MEAL = False
# Judge hunger by the feed actually short, not by an empty shed.
#
# Both the early wheat harvest and the emergency ration fire when any
# animal is unfed and the shed holds no wheat. Every animal is unfed at
# dawn, and the morning feed round is carried *out* of the shed, so both
# fire daily with the grain already in the workers' hands. Traced on one
# game: G sold all 742 of its wheat at hour 0, bought 511 back between
# hours 1 and 11 at the same price on 24 of 30 days, and on 95 of 103
# buying turns no animal had missed a meal and wheat was already carried.
#
# True releases the hold and buys ration only for the deficit: animals
# still to feed today, less the wheat in the shed and in hand.
#
# Measured and rejected, in a fixed town, against 12 current top teams
# with 8 replays each: margin 1,643 a game worse, better in 35 of 96
# paired games and worse in 61, though our own score rose in 52. It does
# what it says -- wheat bought falls from 18,353 a game to 539 and wheat
# pulled early from 471 units to 198 -- but the round trip was at the same
# price and cost almost nothing, while the crew sits idle more (23.0% of
# turns against 16.7%), the herd shrinks (225 animal-days against 254) and
# more goods are left unsold at the close. The churn looked like waste
# and was mostly working capital.
FEED_DEFICIT_RULE = False
# Days before the close that sowing and seed-buying stop.
#
# This was five for wheat and three for cash crops, and it is what empties
# the farm. A census of the last ten days: to day 24 the board is full,
# nought to five free tiles out of seventy and forty crops standing. On
# day 25 the seed runs out. By day 28 there are forty free tiles, no crop
# at all, a full crew and seventy thousand coins in the bank.
#
# Wheat first yields two days after sowing and carrot the same, so both
# could go in on day 27 and still be harvested. Doing so is worth nothing:
#
#     5 (wheat 24, crops 26)   66,875
#     3 (both to day 26)       67,325   (48/60 against 5)
#     2 (both to day 27)       67,245   (46/60)
#
# against 67,308 for the original pair. So the empty board at the end is
# not a gate holding the farm back -- a carrot sown on day 26 returns one
# or two units before the whistle and does not repay the four worker-turns
# it costs. Those idle turns are barren rather than blocked, which is what
# the idle census called them, and the seed running out on day 25 is a
# symptom of the farm correctly declining to sow rather than a cause.
#
# Kept at 3 because it measures the same as the pair it replaces and puts
# one named number where two unexplained ones were.
SOW_UNTIL = 3
# Last turn of the day on which anything may be sown.
#
# A seed counts its planting day as a day unwatered, so one sown on the last
# turn cannot be watered before nightfall and is a weed by morning: the seed
# is lost and the tile has to be dug. The inspector charged G about 1,963
# coins a game for crops dying unwatered after the strawberry change, and on
# the game drilled every one of them -- 17 of 17 -- was sown at hour 23.
# None keeps sowing at any hour; 22 leaves a turn to water.
#
# Measured at 22 in a fixed town against 12 current top teams, 8 replays
# each, paired with the strawberry defaults: crops dying unwatered fall from
# 1,963 to 593 coins a game, exactly as intended, but the margin does not
# move -- +224 a game on the 72 games where the opponent replay stayed in
# step (better in 38, worse in 34), +111 over all 96 (better in 46, worse
# in 50). A tile lost overnight is dug and resown the next morning, so the
# seed was the whole cost. Neutral, so it stays off.
#
# Re-checked once PEN_BEFORE_WHEAT pushed day-0 sowing later: on v14 every
# game loses the strawberry sown at tile (1,1) on the last turn of day 0.
# On the v14 field (83 games):
#     22   +316 a game on 60 clean games (median +358, better in 32, worse
#          in 28), +377 over all 83
#     21   +94 a game on 60 clean games (better in 31, worse in 29), -207
#          over all 83
# Unwatered deaths fall from 1,414 to about 430 coins a game, as intended,
# but overflow rises from 983 to about 1,760 and escapes from 246 to about
# 430: the late turns no longer spent planting go into carrying, and the
# extra load tips into a full shed at night. Still off.
#
# A day-by-day trace then showed every seedling death on days 0 and 10-15 was
# a seed sown on hour 23, with every earlier sowing watered the same day, so
# 22 is exactly "no sowing on the last turn". Re-tested once MIDDAY_DROP_HAUL
# 500 had cut the overflow (v14 field, 83 games): -213 a game on 60 clean
# games (median +728, better in 31, worse in 29), +341 over all 83. Deaths
# fall 1,419 -> 486 coins a game, but escapes rise 329 -> 594. Still off.
PLANT_CUTOFF_HOUR: int | None = None
# The last errand of the season: tip carried goods into the shed so the
# closing sell can reach them.
#
# Keyed to the step, not to `closing`, which spans two whole days. At that
# width the drop job pulled workers off the field for 48 turns to recover
# a few hundred coins and cost 707 (47,995 against 48,702). Confined to
# the last handful of turns it is worth 48,755 -- a gain of 53, which is
# noise, but it never loses a game and it is recovering goods that were
# otherwise thrown away, so it stays.
# Banking produce mid-game, as the corpus does some forty times a game
# against our one, measures as a clear loss: 59,546 at a 120-coin
# threshold and 64,838 at 400, against 67,308 with it kept to the closing
# turns. Their crew passes the shed in the course of its work and ours
# does not, and the nightly refresh tips every worker's arms into the shed
# for nothing anyway -- so the only thing a mid-game trip buys is selling
# a day earlier, and it costs a turn and a walk to get it.
DROP_FROM_STEP = 713
# Ask to sell more than the shed shows on the closing turns.
#
# Workers act before the market does, so goods DROPped on a closing turn are
# in the shed by the time orders fill -- but the sell quantity is read from
# the shed as the turn began, and a good the shed did not hold yet is
# skipped outright. The inspector finds G ending the season holding about 25
# unsold units a game, mostly strawberry, against half a unit for the
# opponent. The engine fills a SELL only from what the shed holds, so over-
# asking costs nothing.
#
# Measured in a fixed town against 12 current top teams, 8 replays each,
# paired with the strawberry defaults: margin +215 a game on the 72 games
# where the opponent replay stayed in step, better in 43 and worse in 10;
# +243 over all 96, better in 62 and worse in 14. Small and consistent.
# Unsold goods only fall from 2,864 to 2,615 coins a game, so most of what
# is left is harvested after the last market tick rather than dropped late.
SELL_CARRIED_AT_CLOSE = True
# Let a worker already beside the shed drop a valuable load mid-day.
#
# DROP is otherwise offered only from DROP_FROM_STEP, so everything the crew
# harvests stays in hand until the nightly refresh tips it into the shed
# after the day's last sale. With a herd of nine the inspector charges 4,723
# coins a game for shed overflow. A nightly trace finds the shed nearly empty
# at hour 23 and the crew carrying 60 to 106 units, 41 to 52 of them wheat,
# so on nights with melon or strawberry in hand the drop passes 100.
#
# The value is the non-wheat produce in hand, in coins, at which the drop is
# offered. Wheat is excluded because a worker carries it to feed animals.
# None keeps the old behaviour. Mid-day banking was measured as a loss at
# 120 and 400 coins, but in the coupled town on the old crop plan.
#
# Paired on 30 contested opponents in a fixed town against G with both
# kept switches and a herd of nine: 1,000 gives +916 a game (better in 39
# of 60), 2,500 gives +121 (12/60). 2,500 is rejected.
#
# 1,000 confirmed on the refreshed field, 12 current top teams with 8
# replays each, paired with G without it: +1,074 a game on the 71 games
# where the opponent replay stayed in step (median +834, better in 41,
# worse in 30), +912 over all 96. Shed overflow falls from 4,763 to 3,855
# coins a game and goods unsold at the close from 3,030 to 2,650.
#
# Lowered to 500 once PEN_BEFORE_WHEAT and SHED_ALL_ACCESS were on and the
# nightly overflow had doubled: the inspector found goods spread thinly across
# a dozen hands at night, 113 to 125 units with less than half of it wheat.
# On the v14 field (83 games), against 1,000: +960 a game on 60 clean games
# (median +930, better in 43, worse in 17), +475 over all 83. Overflow falls
# 983 -> 776 coins a game and rot 112 -> 50; escapes rise 246 -> 329.
# Tipping sooner does not pay either. A threshold of 250 on the v14 field is
# -240 a game over 46 clean games (median +144), better in 24 and worse in
# 22, own score -504. The nightly spill is not sensitive to this number.
MIDDAY_DROP_HAUL: float | None = 500.0
# Bring loads to the shed before night when the nightly drop would overflow.
#
# With the mid-day drop on, a nightly trace still finds the shed holding 0 to
# 6 units at hour 23 while the crew carries 59 to 106, and on nights the load
# passes 100, melon and strawberry are what get thrown away. Nothing in the
# shed can be sold to make room, because there is nothing in it: the only
# fix is to bring the goods in while the market can still take them.
#
# From NIGHT_FROM_HOUR, when shed plus everything carried exceeds NIGHT_ROOM,
# a carrying worker's DROP is offered and scored without the distance
# discount while it can still reach the shed that day; the every-turn sell
# then clears it. None keeps the old behaviour.
#
# Tried first and removed: dropping once a worker carried a wheat surplus
# (as coins inside the 1,000-coin trigger, then as 8 or 16 units). The night's
# 41 to 59 wheat are a few units in each of a dozen hands, no worker ever
# reached the threshold, and both reference games came out identical.
#
# Rejected at 95, inspected on the pruned current corpus (12 top teams, 8
# replays each) against the same agent without it: margin -314 a game on
# the 68 games where the opponent replay stayed in step (better in 30,
# worse in 38), -396 over all 96. The trips it pulls in cost more field
# work than the overflow they save, and care missed rises. Stays off.
NIGHT_ROOM: int | None = None
NIGHT_FROM_HOUR = 20
# Send home only as many carriers as the shed needs, early enough to sell.
#
# The inspector traced the nightly overflow on v14 (Otter Vibe replay, seat
# 0, seed 13): 113 and 125 units in hands at hour 23 on days 20 and 24, only
# 47 of them wheat, and 19 and 31 units discarded when inventories are tipped
# into a shed holding 6. A carrier 5 to 8 tiles out holding 2,800 coins of
# goods keeps watering, because its drop is divided by distance squared; and
# a drop on hour 23 sells nothing, because SELL quantities are read from the
# shed as the turn begins. NIGHT_ROOM, the earlier fix, pulled every carrier
# home and let them arrive on hour 23.
#
# With this set to a unit count, from NIGHT_FROM_HOUR to hour 22, while the
# shed plus everything carried exceeds it, carriers are offered an
# undiscounted DROP that can land by hour 22; each assigned drop takes its
# load off the projection, so once the night's tip fits nobody else is sent;
# and from hour 22 the shed sells whenever the night's total would overflow.
# None is off.
#
# At 100, on top of MIDDAY_DROP_HAUL 500 (v14 field, 83 games): +166 a game on
# 60 clean games (median +80, better in 38, worse in 22), +232 over all 83.
# Overflow falls 776 -> 678 coins a game, care missed rises 1,003 -> 1,070.
# The lower mid-day drop already took most of the nightly spill; what is left
# is not worth the evening trips. Off.
NIGHT_TIP_GUARD: int | None = None
# Bring the crew's last loads home before the season ends.
#
# A trace of the closing turns finds the shed empty from step 700 while ten
# workers carry goods three to seven tiles from it; at step 719, sixteen
# units are still in hand and never sold (the inspector puts goods unsold at
# the close at 2,623 coins a game). The DROP job is only scored on the
# shed-side tiles and, like every job, divided by (travel + 1) squared, so a
# worker six tiles out always prefers the field. From this step on, a
# carrying worker's DROP is scored without that discount while it can still
# reach the shed by the last acting step. None keeps the old behaviour.
#
# Kept at 705. Inspected on the pruned current corpus (12 top teams, 8
# replays each) against the same agent without it: margin +1,127 a game on
# the 68 games where the opponent replay stayed in step (median +970, better
# in 67, worse in 1), +1,145 over all 96 (better in 95). Goods unsold at the
# close fall from 2,691 to 1,578 coins a game.
#
# Moved to 709. Once drops stopped claiming shed tiles and the last day turned
# to harvesting only, 705 started sending the crew home too early: a drill
# found far strawberries still unpicked at 705, the crew home and unloaded by
# 713, then walking back out to pick them on 714-718 when nothing could be
# sold, with three hands idle at the shed. Swept on the pruned v12 field
# (92 games), each against 705:
#     709   +897 a game on 66 clean games (median +732, better in 64, worse
#           in 2), +939 over all 92; stranded goods 694 -> 17 coins a game
#     711   +552 on clean games (better in 56, worse in 10), and -344 against
#           709 (better in 16, worse in 50); stranded 338
#     713   -633 on clean games (better in 15, worse in 51), and -1,530
#           against 709 (better in 1, worse in 65); stranded 1,503
CLOSE_RETURN_FROM_STEP: int | None = 709
LAST_ACT_STEP = 718
# Harvest at the close only what can still reach the shed.
#
# On a reference game with the return trip on, nine hands still end the
# season holding goods. From step 701 they keep harvesting a strawberry or
# collecting a manure as each comes ripe beside them -- a harvest a tile
# away outscores the long walk home -- and the last harvests happen on step
# 718, after which nothing can be sold. The inspector charges 2,234 coins a
# game for it, about 10 strawberries and 6 fertilizer.
#
# With this on, from CLOSE_RETURN_FROM_STEP a HARVEST or COLLECT_FERTILIZER
# is only offered if the worker can reach the tile, act, walk to the shed
# and DROP by LAST_ACT_STEP.
#
# Neutral, paired on 96 games against the v9 defaults: +23 a game on 69
# clean games (better in 15, worse in 13, the rest identical). Stranded
# goods fall from 2,234 to 1,750 coins a game, but a late harvest that
# cannot land was only ever costing the turn. The goods stranded were
# mostly harvested earlier by workers that never got a shed tile to walk
# to -- see DROP_SHARES_SHED. Off.
CLOSE_HARVEST_MUST_LAND = False
# From this step only harvesting, collecting and carrying home are worth
# anything: what is fed, watered, cared for or planted on the last day
# produces after the final sale. None keeps every job on the board.
#
# From 696, the first turn of the last day, paired on 96 games against the
# v9 defaults: +896 a game on 69 clean games (median +775, better in 65,
# worse in 4), +901 over all 96 (better in 91). The crew stops feeding,
# watering and caring for a farm that has no tomorrow and spends the day
# bringing goods in; stranded goods fall from 2,234 to 1,609 coins a game.
#
# Kept at 696, together with DROP_SHARES_SHED. The two add up: both on
# gives +1,324 a game on 69 clean games against neither (median +1,396,
# better in 60, worse in 9), +429 against this alone (better in 53, worse
# in 16) and +754 against shared drops alone (better in 66, worse in 3).
CLOSE_ONLY_GOODS_FROM_STEP: int | None = 696
GOODS_JOBS = ("HARVEST", "COLLECT_FERTILIZER", "DROP")
# Let any number of workers head for the shed to DROP in the same turn.
# Every assigned job claims its tile so two workers never walk to one job,
# but the shed has only four access tiles and the engine lets units share a
# tile, so at most four workers could be sent home on any turn while nine
# were still carrying goods at the close.
#
# Traced at the close of a reference game: a worker one tile from the shed
# walked away to feed an animal, another two tiles out went to dig, because
# the four shed tiles had gone to four other carriers that turn and went to
# four different ones the next. Paired on 96 games against the v9 defaults:
# +571 a game on 69 clean games (median +742, better in 53, worse in 16),
# +757 over all 96 (better in 74). Goods stranded in hands at the end of the
# season fall from 2,234 to 142 coins a game. Kept, together with
# CLOSE_ONLY_GOODS_FROM_STEP; the combined measurement is recorded there.
DROP_SHARES_SHED = True
# The same for PICKUP. claim() already takes each pickup off the shed's
# count, so two workers are never sent for the same last unit; the tile
# claim only capped feed runs at four workers a turn.
#
# Too small to call, paired on 96 games against the v9 defaults: +161 a game
# on 69 clean games (median +1,179, better in 42, worse in 27), +60 over all
# 96. Since pickups were sized to need, few turns send more than four
# workers for feed, so the cap rarely binds. Off.
PICKUP_SHARES_SHED = False
# Re-check every build against the pens still short as workers are
# assigned, and book a walking builder's pen at once.
#
# The inspector drilled a v11 game at step 244: three workers issued
# BUILD_COOP on the same turn at (3,4), (4,6) and (6,4) while house_needed
# asked for two empty coops and a goose was already being placed, and those
# coops stood empty from day 10 to day 28. Every build is scored from one
# snapshot, still_possible() passed every build, and claim() booked only a
# walking builder's first step. G's pens stand empty 97 tile-days a game
# against the opponent's 20.
#
# Measured on the refreshed ladder (v11 defaults, 92 games) and it loses:
# -2,112 a game on 66 clean games (median -2,545, better in 21, worse in
# 45), -2,035 over all 92. Empty pen tile-days fall only from 97 to 82, and
# deaths and escapes shrink, but cow spending falls from about 3,100 to
# 2,787 a game: animals are only bought into a pen already standing empty,
# so the "extra" coops and pastures were the lead the herd grows into.
# Reserving pens for walking placers (the inspector's PLACE_COMMIT, tested in
# its own copy) loses the same way, -2,029. Off.
BUILD_CLAIM = False
# Work the shed from all four access tiles, locked or not.
#
# The engine lets a unit walk onto a LOCKED tile and resolves DROP, PICKUP
# and shed placement before its LOCKED guard, so the shed is reachable from
# every access tile from day 0 (kaggriculture.py, _apply_unit_action). G
# skipped every tile outside the quadrants it owns, and three of the four
# access tiles sit in quadrants bought on day 5 and day 9, or never. With
# one worker per tile per turn, the shed was a single lane on days 0 to 4:
# the inspector traced a sheep bought at hour 11 of day 0 waiting in the
# shed until nightfall while the pickups queued, which is why G's first wool
# lands a day after the opponent's. With this on, a locked access tile is
# offered for its shed jobs only.
#
# Alone, on the v13 field (83 games): -1,392 a game on 58 clean games
# (median -530, better in 28, worse in 30), +103 over all 83. Care missed
# falls 1,636 -> 907 coins a game and escapes 453 -> 254, but day-0 animals
# standing fall from 2 to 1 in the previews: with pens still going up after
# the wheat, the extra lanes only let workers fetch wheat and animals sooner
# and carry them. See PEN_BEFORE_WHEAT for the two together.
SHED_ALL_ACCESS = True
# Put pens up before wheat while animals wait to be placed.
#
# job_value's empty-tile chain offers PLANT WHEAT first and never reaches the
# pen branch while wheat is under its quota and seed is in hand. On day 0
# the wheat seed lands at hour 1, so a worker drill (the inspector's, Cow Boy
# replay, seed 15) found 27 worker-turns spent planting and watering wheat
# from hour 2 to 8 while bought animals sat in the shed, and pastures only
# going up at hours 11-13. With this on, while any animal is in the shed or
# in a worker's hands and house_needed still wants a pen, an empty tile
# skips the wheat branch and offers the pen. First written and drilled in
# the inspector's copy of G.
#
# Alone, on the v13 field (83 games): +1,239 a game on 61 clean games
# (median +926, better in 34, worse in 27), +1,168 over all 83. Escapes fall
# 453 -> 283 coins a game, but crops dying unwatered rise 862 -> 1,186 and
# overflow 517 -> 1,008. With pens up first, day-0 animals still queue at
# the single usable shed tile: a sheep bought at hour 3 waited until hour
# 20 in the drill.
#
# Kept on, together with SHED_ALL_ACCESS: each fixes one link of the same
# day-0 chain. Pens go up first, and the extra shed lanes then carry the
# animals onto them the same morning -- in the drill the sheep was placed at
# hour 8 of day 0 instead of hour 17 of day 1 and the cow at hour 10 instead
# of 21, and first wool moved from day 7 to day 6. Both on, on the v13 field
# (83 games): +2,945 a game on 59 clean games against neither (median
# +2,900, better in 40, worse in 19), +2,700 over all 83; +1,666 against this
# alone (better in 38, worse in 21) and +4,271 against shed access alone
# (better in 46, worse in 11). Escapes fall 453 -> 246 coins a game and care
# missed 1,636 -> 1,021; crops dying unwatered rise 862 -> 1,414 and overflow
# 517 -> 983, which is where to look next.
PEN_BEFORE_WHEAT = True
# Fertilizer for strawberry.
#
# A strawberry produces four times, and a production made on a day the plant
# is fertilized and watered pays two units instead of one. Across 96 v5
# baseline games G sells 3.74 strawberries per seed bought and the top teams
# 7.03, while G sells 168 fertilizer a game at about 59 and buys none -- the
# top teams buy about 1,714 coins of it. A trace of one game finds 62 of 111
# strawberry productions doubled and 49 not.
#
# Two causes. ONGOING_FERT_ALIGN: fertilizer_gain counted production days a
# day early against the engine's rule. STRAWBERRY_FERT_STOCK: fertilizer only
# reaches a worker's hands from an animal; none is ever picked up from the
# shed, and the shed's stock is sold every turn. With it on, fertilizer
# enough for the plants that would gain from it today is kept back from
# sale, and a worker at the shed with none in hand may pick some up.
#
# Not pursued. On the two reference games every variant but one lost margin:
# align -608 and -12,598, stock -1,778 and -15,637, both -7,346 and -3,554.
# Keeping stock did raise doubled strawberry productions from 62 to 80 in
# the first game, but the pickup trips cost more field work than the
# berries earned. In the second game G already doubled 38 of 40
# productions. The yield-per-seed gap is more likely in when strawberry
# is sown and how much of it is harvested than in fertilizer. Both stay
# off.
#
# Re-measured properly on 96 games against the v10 defaults, since two games
# settle nothing and the pickup trips may have been starved by the old
# four-worker shed claim:
#     align          +435 a game on 69 clean games (better in 41, worse in
#                    28), -20 over all 96 -- too close to call
#     stock        -4,416 a game on 69 clean games (better in 14, worse in
#                    55), -4,922 over all 96
#     both         -3,086 a game on 68 clean games (better in 14, worse in
#                    54), -3,615 over all 96
# Holding manure back for the strawberries fills the shed: overflow rises
# from 550 to 1,577 and 2,130 coins a game, and G still sells 143 to 153
# strawberries against the opponent's 210. Both stay off.
ONGOING_FERT_ALIGN = False
STRAWBERRY_FERT_STOCK = False
# Buy cash-crop seed only for ground the cap still has room for.
#
# The seed order checks that standing plants are below the cap and seed in
# hand is below a batch, but not the two together, so seed already held
# for the last free tiles is bought again. Following every plant through
# two games: 20 melon seeds bought and 13 planted, 12 bought and 8 planted;
# 40 strawberry seeds and 36 plants, 16 and 12. About 1,000 coins a game of
# seed that never goes in the ground. With this on, plants plus seed in hand
# may not pass the cap.
#
# Kept. Inspected on the pruned current corpus (12 top teams, 8 replays
# each) against the same agent without it: margin +301 a game on the 68
# games where the opponent replay stayed in step (median +160, better in
# 42, worse in 7; the rest identical, where the cap never bound), +194 over
# all 96 (better in 58, worse in 12).
SEED_TO_CAP = True
# Do not sell premium goods into a book that has been flooded to the floor.
#
# Strawberry, milk, wool and melon fall to 1 on a modest glut. In one traced
# game G sold strawberries at 1 to 5 coins on days 21 to 23, after the other
# farm had flooded the book, while the town was still consuming them every
# few turns. The demand layer that helps Candidate H was neutral on G
# overall; this is a narrower rule. When a premium good's price is below
# FLOOR_HOLD times its base, the town still takes it, the shed is below
# FLOOR_HOLD_ROOM, and the season is not closing, G holds that good this
# turn. None keeps selling on sight.
#
# Not pursued. On the two reference games 0.3 and 0.5 moved the margin by
# +584 and -154/-438, and G still sold 22 to 24 units of wool or milk at 20
# coins or less. The town drains a flooded book too slowly for holding to
# find a better price; it only delays the same sale. Stays off.
FLOOR_HOLD: float | None = None
FLOOR_HOLD_GOODS = ("STRAWBERRY", "MILK", "WOOL", "MELON")
FLOOR_HOLD_ROOM = 80
# Sow an ongoing crop only while its whole production run fits the season.
#
# A strawberry sown on day d produces at the end of days d+9, d+11, d+13 and
# d+15, and a production at the end of day 29 is never sold, so all four fit
# only up to day 13. Sowing runs to day 18 today. Following every plant
# through a game found 13 strawberry plants still standing at the close and
# 3 that yielded nothing, each a 100-coin seed on a tile a carrot could have
# used. With this on, an ongoing crop is sown (and its seed bought) only
# while its last production still lands on a day that can be sold.
#
# Not pursued. On the two reference games it moved the margin by -1,515 and
# +618. In the first, the 12 strawberries it stopped sowing after day 13
# had still sold 13 more units, about 2,300 coins against about 1,200 of
# seed. A partial run still pays. Stays off.
ONGOING_FULL_CYCLE = False


def last_sow_day(crop: str) -> int:
    """Last day an ongoing crop may be sown and still finish producing."""
    spec = CROPS.get(crop)
    if not ONGOING_FULL_CYCLE or spec is None or not spec.get("ongoing"):
        return LAST_DAY
    interval = max(1, int(spec["interval"]))
    # Productions land at the end of day d + first - 1 + k * interval;
    # the last one must be no later than the day before the final day.
    run = int(spec["first"]) - 1 + (int(spec["max_yield"]) - 1) * interval
    return LAST_DAY - 1 - run


def town_takes(observation: dict[str, Any], item: str) -> bool:
    """Whether some unlocked shop (or the town centre) consumes `item`."""
    if item != "FERTILIZER":
        return True  # the town centre takes one of every product daily
    return False
# Stop buying a crop's seed once that crop can no longer be sown.
#
# Sowing a cash crop stops once it could not yield before the close
# (strawberry after day 18), but its seed is bought until three days from
# the end. A daily trace of the strawberry defaults ends the season holding
# seven strawberry and four melon seeds, about 1,000 coins that could never
# have been planted.
#
# Measured in a fixed town against 12 current top teams, 8 replays each,
# paired with the strawberry defaults: margin +487 a game on the 72 games
# where the opponent replay stayed in step (median +720), better in 59 and
# worse in none; +483 over all 96, better in 80 and worse in none. Pure
# saving. Together with SELL_CARRIED_AT_CLOSE: +702 a game on 72 clean
# games, better in 67 and worse in none.
SEED_ONLY_WHEN_SOWABLE = True
# Re-checked on contested opponents once COMPACT moved, on the theory
# that the two distance terms interact -- and it does not: 67,697 at 2.0
# against 63,147 at 1.5 and 64,281 at 2.5, ahead on both counts. This one
# was already right.
TRAVEL_EXPONENT = 2.0
# Where a coop or a wheat tile goes matters as much as that it exists.
# Feed comes out of the shed and every meal is a round trip, so a flock
# housed at the far edge spends the season walking: PICKUP was the single
# most frequent action in the game at 1,102, with 3,160 turns of movement
# behind it, against 408 harvests. Ground near the shed is therefore worth
# more than ground far from it, and this is the discount for distance.
# Zoning. Workers pick jobs independently by value over distance squared,
# so they scatter: PICKUP and movement take some 4,200 of 7,000 worker
# turns while feeding, harvesting, watering and collecting share the rest,
# and the farm runs at roughly a third of what its flock is worth. Giving
# each worker a strip of the board to serve and taxing jobs outside it
# should convert walking into work. 1.0 disables the tax.
# Re-checked with compactness on, and still off. Strips fight the shed:
# 59,444 at 1.0 against 52,866 at 0.7 (19/60) and 49,769 at 0.4 (16/60).
# The crew already clusters near the shed for good reason, and cutting the
# board into vertical lanes pulls it away from there.
ZONE_TAX = 1.0
# How much nearer ground is worth than far ground, as a discount on the
# walk from the shed.
#
# This was 0.0, and the note said compactness cost 5,000. It did -- on a
# farm holding one quadrant, where there was no far ground to avoid. The
# second quadrant now arrives on day one, the board is twice the size from
# the start, and the same setting is worth:
#
#     0.00   57,044 mean   53,373 median   36,839 min
#     0.15   59,444        62,392          38,628   (30/60)
#     0.35   57,824        60,852          32,319   (30/60)
#
# 30 of 60 is chance, and it is taken anyway because mean, median and the
# worst game all improve together and the reason is plain: with twelve
# hands and half their turns already spent walking, ground near the shed
# is worked and ground far from it is not.
# Left at 0.15, and the story of why is the useful part.
#
# On a three-route panel 0.35 measured 67,697 against 63,703, ahead in 42
# of 60 paired games, and it was committed as a 3,994 gain. On thirty-six
# contested opponents it is a *loss*: 66,430 against 71,627, and 62,701
# against 63,323 on the fuller run, taking the win count from four to
# nought.
#
# Three opponents cannot tell a real gain from one that happens to suit
# three opponents. That flaw was identified this morning, tools/eval/
# wide_panel.py was written to fix it -- and then every re-fit in the
# afternoon was run on the three-route harness anyway, because it takes
# eight minutes instead of forty. Knowing the flaw and not using the fix
# is worse than not knowing.
#
# Anything measured only on three routes is unproven, and that includes
# the four constants this pass reported as "held".
COMPACT = 0.15               # measured: clustering near the shed costs
                            # 5,000 coins, so it stays off

# Priority bands. The chain is feed -> wheat -> housing -> birds, because
# each link is worthless without the one before it, and a coin-valued
# ranking put housing six times above the wheat that keeps its occupant
# alive.
BAND_FEED = 10000.0
# Harvesting, and the clearest illustration in this file that our own
# score and the margin pull in opposite directions.
#
# Against 24 contested opponents:
#
#     band     our mean   their score   margin
#     6,000      51,068       106,101   -55,033
#     3,000      76,637       142,466   -65,829
#     9,000      50,443       118,671   -68,228
#
# Dropping the band raises our own score by 25,569 -- fifty per cent --
# and raises theirs by 36,365, because we harvest less, sell less, the
# books stay shallow and *both* farms get better prices. At 6,000 we are
# flooding hard enough that our own revenue falls with theirs; we are the
# marginal supplier and we set the price for the pair of us.
#
# 6,000 is kept because the game is won on who holds more at step 720,
# not on how much we hold. But it is a deliberate choice to run this farm
# 25,000 poorer than it could be, and worth re-examining if the denial
# ever stops paying -- against a live opponent, or if the field stops
# being a crowd of copies that cannot react.
BAND_HARVEST = 6000.0
BAND_WHEAT = 4000.0
BAND_PLACE = 3000.0
BAND_SERVICE = 2000.0
# Watering, and the band that showed this project it was optimising the
# wrong quantity -- by a route still not understood.
#
# Over 120 games against thirty contested opponents:
#
#     band    our mean    margin
#     1,500     64,395   -78,527
#     3,500     52,294   -65,350
#
# Twelve thousand of our own coins for thirteen thousand of theirs. Every
# measure this project had used -- mean, median, floor -- calls that a
# regression, and all three are the wrong question: the game goes to
# whoever holds more money at step 720 and the rating comes from wins, so
# the margin is the objective and our own total is only a means to it.
# That much is solid, and it invalidates how a whole day of changes was
# judged.
#
# **The mechanism is not.** The obvious story is that more watering means
# more produce, a flooded book and a collapsed price for both sides. A
# single game traced end to end says otherwise: at 3,500 we earn *more*
# (60,949 against 47,604), they earn *more* (110,545 against 91,956), the
# margin is *worse*, and the books are less flooded rather than more --
# wheat moves from -257 to +5, milk from +73 to -39. Idle turns nearly
# double, 674 to 1,111.
#
# So the average is real and the explanation was invented. The variance
# across opponents is wide enough that one game proves nothing either way,
# but it does disprove the flooding account, and nothing has replaced it.
# Treat the setting as measured and unexplained until it is traced across
# the opponents where it actually wins.
BAND_WATER = 3500.0
# Manure on a growing tile -- and *which* tile is the whole question.
#
# Spreading manure was measured as a clear loss and switched off: band
# 1600 scored 35,359, band 900 scored 33,089, band 300 scored 38,130,
# against 44,364 with it off. The reasoning behind that looked sound.
# FERTILIZER needs 493 units past equilibrium to fall to a price of 1, so
# the good reads as worthless, but we only produce about 190 a game and
# the marginal unit really fetches 62 -- while the two extra units of
# wheat it creates fetch 21 each. Three to one against.
#
# All of which is true, and none of which applied to the crops that
# matter, because `fertilizer_gain` returned zero for every *ongoing*
# crop. The simulator applies the bonus to those as well, in
# `_daily_refresh_plants`: a fertilized production day yields two units
# rather than one. Strawberry sells around 235 a unit. Two extra units is
# 470 coins for a unit of manure worth 62 to 84.
#
# So the earlier test never covered the only case where this pays. The
# job now values every application against what the same manure would
# fetch sold, and only fires when the crop wins -- which rejects wheat and
# melon on their own numbers and accepts strawberry and tomato.
#
#     off     47,486 mean   50,058 median   17,863 min
#     1600    48,702         50,738         25,334
#     3000    48,129         50,758         17,633
#
# Honest about the strength of this: 31 of 60 paired games is a coin
# flip. It is kept because every summary statistic improves and the floor
# improves by 7,471, which is the largest gain in the worst case measured
# on this agent, and because the mechanism behind it is verified rather
# than inferred.
#
# Raised on the refreshed ladder (v11 defaults, 92 games), after a trace of a
# reference game found 34 of G's 36 undoubled strawberry productions were
# watered but unfertilized, all on days 20 to 29, while G sold 72 manure over
# the same days:
#     3000   +779 a game on 66 clean games but median -648, better in 26,
#            worse in 40; +1,907 over all 92, better in only 37
#     5000   -1,769 a game on 66 clean games (median -2,848, better in 19,
#            worse in 47), -1,119 over all 92
# Both sell more strawberries (152 to 161 and 167) and cut crops dying
# unwatered from 1,404 to about 800 coins a game, but care goes missing
# (1,646 to 2,036 and 2,155) and the extra berries sell lower. Priority just
# moves the shortage to another job. 1,600 stays.
BAND_FERTILIZE = 1600.0     # 0 disables the job entirely

BAND_BUILD = 800.0
BAND_CROP = 600.0
# Assign every worker-job pair best-first, rather than letting each worker
# in turn take the best job left anywhere.
# How much a job a worker is already walking to is worth over any other job
# it could switch to, as a multiplier on the score. None keeps the old rule,
# where every job on the board is re-auctioned every turn with no memory.
#
# Measured on a reference game before this existed: half of all worker turns
# (49.9%, 3,612 of 7,241) are movement, and on 17.1% of travelling turns the
# destination changes mid-walk -- 618 abandoned journeys in one game. The
# individual steps are fine: only 4.9% of moves fail to close on the target.
# So the waste is re-targeting, not pathfinding.
# Measured on the 38 games G actually played on the ladder (submission
# 56272104, rating 635, opponents rated about 690), replayed exactly -- all
# 38 reproduce the live result to the coin, so this is the population G has
# to beat to climb, not a panel of elite replays:
#
#     strength   wins (of 38)   own score mean / median
#     off              17        --
#     1.5              22        -931 / -538
#     2.0              23        -886 / -3,793
#     3.0              23        +5,142 / +7,972   (higher in 22 of 38)
#     5.0              23        +1,182 / -300
#
# At 3.0, 7 games flip to wins and 1 to a loss, and on the 29 games where the
# opponent tape stayed close the own score still rises 3,539 a game. Abandoned
# journeys fall from 17.1% of travelling turns to 11.9%.
#
# Honest about where it does NOT hold: against the 2300-rated replay field
# this loses -- 1,139 a game on 45 clean games at 2.0 and 3,789 at 4.0. A
# committed worker is worth more when the opponent is weak enough that
# finishing jobs matters more than reacting. If G climbs past about 1500 this
# should be re-measured on the games it is playing then.
STICKY_TARGET: float | None = 3.0
# Where each worker was walking last turn: (player, worker) -> (cell, job).
# Cleared at the start of every episode, because one process replays many
# games in a row.
_EN_ROUTE: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}
GLOBAL_ASSIGN = True
# Crew held back for maintenance only. Measured, and OFF.
#
# The idea came from a competing design and the reasoning is good: the
# bands rank HARVEST, PLANT and PLACE above WATER and CARE, so a busy
# board could earn today at the cost of a plant that turns to weed
# tomorrow and an animal that walks off the day after.
#
#     0.00   49,106 mean   51,168 median   31,382 min
#     0.25   43,561        44,244          18,541    (13/60)
#     0.45   27,531        30,480           9,599    ( 0/60)
#
# 0.45 was the recommended figure and it loses 44%, winning none of sixty
# games. The premise is simply wrong for this scheduler: FEED already sits
# at the top of the bands, well above harvest and planting, so tending is
# not being starved. Reserving a quarter of the crew for tending-only work
# means those workers stand idle whenever nothing needs tending -- and
# this farm already passes on 14 to 21 per cent of its worker turns. The
# reservation deepens the labour shortage it was meant to relieve.
RESCUE_SHARE = 0.0
TENDING = ("WATER", "FEED", "CARE", "PICKUP",
           "NORTH", "SOUTH", "EAST", "WEST")


def _farm(observation: dict[str, Any]) -> dict[str, Any]:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    if player < len(farms) and isinstance(farms[player], dict):
        return farms[player]
    return {}


def _positions(farm: dict[str, Any]) -> list[tuple[int, int]]:
    units = [farm.get("farmer"), *(farm.get("hands") or [])]
    out: list[tuple[int, int]] = []
    for unit in units:
        if isinstance(unit, (list, tuple)) and len(unit) >= 2:
            out.append((int(unit[0]), int(unit[1])))
        else:
            out.append((0, 0))
    return out


def _inventory(observation: dict[str, Any], worker: int) -> dict[str, int]:
    private = observation.get("private") or {}
    inventories = private.get("inventories") or []
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return {str(k): int(v) for k, v in inventories[worker].items()}
    return {}


def _shed(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("shed") or {}).items()}


def _seeds(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("seeds") or {}).items()}


def shed_tiles() -> list[tuple[int, int]]:
    half = BOARD // 2
    return [(half - 1, half - 1), (half, half - 1),
            (half - 1, half), (half, half)]


def _shed_adjacent(x: int, y: int) -> bool:
    """Standing *on* a shed-access tile, which is what the simulator wants.

    `_is_shed_adjacent` in kaggriculture.py is
    `tuple(pos) in set(_shed_access_tiles(board_size))` -- membership of
    exactly four tiles, not proximity to them. Accepting the twelve tiles
    within one step of the shed made 1,067 of 1,273 PICKUP actions in a
    game silent no-ops: the worker stood next to the right square, asked
    for wheat, got nothing, and walked off to feed birds empty-handed.
    """
    return (x, y) in set(shed_tiles())


def _owned(tiles: list[list[Any]], x: int, y: int) -> bool:
    return (0 <= y < len(tiles) and 0 <= x < len(tiles[y])
            and tiles[y][x] != "LOCKED")


def census(tiles: list[list[Any]]) -> dict[str, int]:
    """Everything the scheduler needs to know about the board, in one pass."""
    out = {
        "geese": 0, "animals": 0, "empty_coops": 0, "empty_pastures": 0,
        "wheat": 0, "free": 0, "unfed": 0, "uncared": 0, "hungry": 0,
        "manure": 0, "ripe": 0, "dry": 0,
        "have_GOOSE": 0, "have_COW": 0, "have_SHEEP": 0,
    }
    for row in tiles:
        for tile in row:
            if tile == "LOCKED":
                continue
            if tile is None:
                out["free"] += 1
                continue
            if not isinstance(tile, dict):
                continue
            if "animal" in tile:
                out["animals"] += 1
                kind_of = str(tile.get("animal", ""))
                key = "have_" + kind_of
                if key in out:
                    out[key] += 1
                if kind_of == "GOOSE":
                    out["geese"] += 1
                if not tile.get("fed_today"):
                    out["unfed"] += 1
                    # Missed yesterday too: unfed again tonight, it escapes.
                    if int(tile.get("consecutive_unfed", 0) or 0) >= 1:
                        out["hungry"] += 1
                if not tile.get("cared_today"):
                    out["uncared"] += 1
                if tile.get("fertilizer_available"):
                    out["manure"] += 1
                if int(tile.get("yield_units", 0) or 0) >= HARVEST_AT:
                    out["ripe"] += 1
            elif tile.get("kind") == "COOP":
                out["empty_coops"] += 1
            elif tile.get("kind") == "PASTURE":
                out["empty_pastures"] += 1
            elif tile.get("kind") == "PLANT":
                crop = str(tile.get("crop", ""))
                if crop == "WHEAT":
                    out["wheat"] += 1
                    if not tile.get("watered_today"):
                        out["dry"] += 1
                else:
                    key = "crop_" + crop
                    out[key] = out.get(key, 0) + 1
    return out


def night_load_high(observation: dict[str, Any],
                    counts: dict[str, int]) -> bool:
    """Late in the day, and the nightly drop would overflow the shed."""
    if NIGHT_ROOM is None:
        return False
    if int(observation.get("step", 0)) % 24 < NIGHT_FROM_HOUR:
        return False
    return (counts.get("shed_total", 0)
            + counts.get("carried_total", 0)) > NIGHT_ROOM


def tip_guard_high(observation: dict[str, Any],
                   counts: dict[str, int]) -> bool:
    """Hours 20 to 22, and the loads not yet sent home would overflow."""
    if NIGHT_TIP_GUARD is None:
        return False
    if not NIGHT_FROM_HOUR <= int(observation.get("step", 0)) % 24 <= 22:
        return False
    carried = counts.get("tip_carried", counts.get("carried_total", 0))
    return counts.get("shed_total", 0) + carried > NIGHT_TIP_GUARD


def feed_deficit(counts: dict[str, int], shed: dict[str, int]) -> int:
    """Animals still to feed today beyond the wheat already held."""
    return max(0, counts["unfed"] - int(shed.get("WHEAT", 0))
               - counts.get("wheat_carried", 0))


def fertilizer_gain(tile: dict[str, Any], day: int) -> int:
    """Extra units this tile would yield if manure went on it today.

    Watering inside the window adds one unit, or two on a fertilized
    tile, and the effect lasts three days. So the gain is the number of
    remaining window days the manure would cover -- but only up to the
    yield cap, which is what stops the farm wasting manure on melon: a
    melon tile has seven watering days and a cap of six, so it reaches
    the cap unaided and gains nothing.
    """
    if tile.get("fertilized_until_day", -1) >= day:
        return 0
    spec = CROPS.get(str(tile.get("crop", "")))
    if spec is None:
        return 0
    held = int(tile.get("yield_units", 0) or 0)
    planted = int(tile.get("planted_day", day))
    if spec["ongoing"]:
        # An ongoing crop produces on a fixed cadence rather than on
        # watering, and a fertilized production day yields two units in
        # place of one. So the gain is the number of its production days
        # that fall inside the three days the manure covers.
        #
        # This branch used to return zero, which forbade the only case
        # where spreading manure pays. Strawberry sells around 235 a unit
        # against wheat's 21, so two extra units return some 470 for a
        # unit of manure worth 62 to 84 -- where wheat returns 42 for the
        # same input and loses.
        interval = max(1, int(spec["interval"]))
        # The engine produces at the end of day d when (d + 1 - planted -
        # first) is a multiple of the interval, pays the bonus if manure
        # covers d itself, and stops after max_yield productions.
        # ONGOING_FERT_ALIGN counts those days; the old count is a day early.
        shift = 1 if ONGOING_FERT_ALIGN else 0
        gain = 0
        for ahead in (0, 1, 2):
            since = (day + ahead + shift) - planted - int(spec["first"])
            if since >= 0 and since % interval == 0:
                if (ONGOING_FERT_ALIGN
                        and since // interval + 1 > int(spec["max_yield"])):
                    continue
                gain += 1
        return max(0, min(gain, int(spec["max_yield"]) - held))
    age = day - planted
    start = (int(spec["max_day"]) + 1) // 2
    last = int(spec["max_day"])
    if age > last:
        return 0
    remaining = last - max(age, start) + 1
    if remaining <= 0:
        return 0
    room = int(spec["max_yield"]) - held - remaining
    return max(0, min(room, min(3, remaining)))


def house_needed(counts: dict[str, int], preferred: str) -> str | None:
    """Which pen to build next, or None. Housing follows the animals we
    already own, never the animal the town happens to want today.

    The old gate asked only whether the *preferred* animal's pen type had
    fewer than COOP_LEAD empties. When demand moved to cows the goose
    branch stopped being consulted, no coop was ever built again, and
    every goose bought after that sat in the shed for the rest of the
    game. A census across three seeds showed the herd frozen from day 9
    to day 28 -- 10 animals, 61 free tiles and 57,000 idle coins on one
    seed, thirteen geese stacked in the shed on another.

    So an animal already bought is housed unconditionally; only the
    speculative lead is rationed, and only by whether the wheat is there
    to feed what it would hold.
    """
    for house in PEN_ORDER:
        if pen_short(counts, house):
            return house
    return None


def pen_short(counts: dict[str, int], house: str) -> bool:
    """Whether `house` has fewer empty pens than the animals owed one."""
    empty = counts["empty_coops" if house == "COOP" else "empty_pastures"]
    waiting = counts.get("shed_" + house, 0)
    carried = counts.get("unplaced_" + house, 0)
    # Room to grow the lines that live in this house, capped by the
    # herd plan so the farm does not build pens for animals it can
    # neither feed nor tend.
    wanted = 0
    for animal, home in ANIMAL_HOME.items():
        if home != house:
            continue
        wanted += max(0, counts.get("want_" + animal, 0)
                      - counts.get("have_" + animal, 0))
    lead = 0
    if (wanted > 0
            and (counts["animals"] < EARLY_BIRDS
                 or counts["wheat"] >= COOPS_AFTER_WHEAT)):
        lead = min(COOP_LEAD, wanted)
    return empty < waiting + carried + lead


def job_value(
    observation: dict[str, Any],
    tile: Any,
    x: int,
    y: int,
    inventory: dict[str, int],
    day: int,
    shed: dict[str, int],
    seeds: dict[str, int],
    counts: dict[str, int],
    closing: bool,
) -> list[tuple[float, list[Any]]]:
    """Every job available on this tile, in priority bands.

    An earlier version priced each job in coins and let them compete
    directly. That failed for a reason worth recording: building a coop is
    worth a bird's whole remaining output, which outbid planting the wheat
    that bird eats by roughly six to one, so the farm built empty housing,
    never sowed, and its geese starved out on day three.

    The ordering is a dependency chain, not a preference. Feeding beats
    everything because two missed meals lose the animal outright. Wheat
    beats housing because housing without feed kills what it houses.
    Housing beats buying because an unhoused bird sits in the shed. Within
    a band the value still varies with the live price and the distance
    discount still applies, so the schedule stays sane -- but no job can
    ever outbid the thing it depends on.
    """
    jobs: list[tuple[float, list[Any]]] = []
    egg = max(1.0, price_at("EGG", inventory_of(observation, "EGG")))
    manure = max(
        1.0, price_at("FERTILIZER", inventory_of(observation, "FERTILIZER"))
    )
    days_left = max(0, LAST_DAY - day)
    # Wheat the flock needs standing, plus a small buffer to grow into.
    wheat_target = WHEAT_TILES

    if _shed_adjacent(x, y):
        # Everything still in a worker's arms when the game stops is
        # thrown away. Inventories are tipped into the shed on the nightly
        # refresh, which for day 29 happens *after* the last market tick,
        # so the final day's harvest is never sold. Measured: two wheat,
        # three fertilizer and four eggs left in hand at the last step.
        #
        # A DROP puts the lot in the shed in one action, and the closing
        # sell empties the shed the same turn, so the last errand of the
        # season is worth making. It is priced by what is actually being
        # carried, so a worker holding nothing valuable stays in the field.
        haul = produce = 0.0
        for item, qty in inventory.items():
            if int(qty) > 0 and item in MARKET_PARAMS:
                worth = int(qty) * price_at(
                    item, inventory_of(observation, item))
                haul += worth
                # Wheat in hand is feed on its way to an animal, not stock.
                if item != "WHEAT":
                    produce += worth
        late_from = (DROP_FROM_STEP if CLOSE_RETURN_FROM_STEP is None
                     else min(DROP_FROM_STEP, CLOSE_RETURN_FROM_STEP))
        late = int(observation.get("step", 0)) >= late_from
        midday = (MIDDAY_DROP_HAUL is not None
                  and produce >= MIDDAY_DROP_HAUL)
        night = (night_load_high(observation, counts)
                 or tip_guard_high(observation, counts))
        if haul > 0 and (late or midday or night):
            jobs.append((BAND_HARVEST + haul, ["DROP"]))
        carrying = int(inventory.get("WHEAT", 0))
        in_shed = counts.get("shed_WHEAT", int(shed.get("WHEAT", 0)))
        if FEED_PICKUP_TO_NEED:
            need = (counts["unfed"] + FEED_PICKUP_SPARE
                    - counts.get("wheat_carried", 0))
            if FEED_PICKUP_FOR_HUNGRY and counts.get("hungry", 0) > 0:
                need = max(need, counts["hungry"] + FEED_PICKUP_SPARE
                           - counts.get("hungry_fetched", 0))
            if (counts["unfed"] > 0 and need > 0 and carrying <= 0
                    and in_shed > 0):
                jobs.append((BAND_FEED * 0.9,
                             ["PICKUP", "WHEAT",
                              max(1, min(FEED_CARRY, need, in_shed))]))
        elif counts["unfed"] > 0 and carrying <= 0 and in_shed > 0:
            jobs.append((BAND_FEED * 0.9, ["PICKUP", "WHEAT", FEED_CARRY]))
        if (STRAWBERRY_FERT_STOCK
                and int(inventory.get("FERTILIZER", 0) or 0) <= 0
                and counts.get("fert_need", 0) > counts.get("fert_carried", 0)
                and int(shed.get("FERTILIZER", 0) or 0) > 0):
            wanted = counts["fert_need"] - counts.get("fert_carried", 0)
            berry = price_at("STRAWBERRY",
                             inventory_of(observation, "STRAWBERRY"))
            jobs.append((BAND_FERTILIZE + berry,
                         ["PICKUP", "FERTILIZER",
                          max(1, min(4, wanted,
                                     int(shed.get("FERTILIZER", 0))))]))
        # Collect *any* animal the shed is holding, not just the one the
        # town happens to want today.
        #
        # This gate used to read the demand-preferred animal only. Demand
        # moves, and the moment it moved off whatever was already in the
        # shed that animal was orphaned: a daily census showed one sitting
        # in the shed from day 0 to day 11 with five empty pens standing,
        # a third of the season of lost laying, because the farm had since
        # decided it preferred geese. Preference decides what to *buy*; it
        # has no business deciding what to carry.
        if not any(int(inventory.get(a, 0)) > 0 for a in ANIMAL_HOME):
            preferred = counts.get("bird", "GOOSE")
            for animal in sorted(
                ANIMAL_HOME, key=lambda a: (a != preferred, a)
            ):
                house = ANIMAL_HOME[animal]
                waiting = int(counts.get("shed_" + animal,
                                         int(shed.get(animal, 0))))
                home = ("empty_coops" if house == "COOP"
                        else "empty_pastures")
                # Pens already spoken for by an animal in someone's arms
                # are not free, or four workers fetch eight animals for
                # two pens and six of the trips are silent no-ops.
                free_pens = counts[home] - counts.get("unplaced_" + house, 0)
                if waiting <= 0 or free_pens <= 0:
                    continue
                carry = max(1, min(BIRDS_CARRIED, waiting, free_pens))
                jobs.append((BAND_PLACE * 0.95, ["PICKUP", animal, carry]))
                break

    if tile == "LOCKED":
        # Only a shed-access tile outside our land reaches here (see
        # SHED_ALL_ACCESS), and only its shed jobs can be done from it.
        return [(v, a) for v, a in jobs if v > 0]

    if tile is None:
        # Everything built here is worked from the shed for the rest of the
        # season, so near ground is worth more than far ground.
        near = 1.0 / (1.0 + COMPACT * min(
            abs(x - sx) + abs(y - sy) for sx, sy in shed_tiles()
        ))
        sowable = (PLANT_CUTOFF_HOUR is None
                   or int(observation.get("step", 0)) % 24
                   <= PLANT_CUTOFF_HOUR)
        pen_first = (
            PEN_BEFORE_WHEAT and days_left > 5
            and sum(counts.get(key + house, 0)
                    for key in ("shed_", "unplaced_")
                    for house in ("COOP", "PASTURE")) > 0
            and house_needed(counts, counts.get("bird", "GOOSE")) is not None)
        if (not pen_first
                and counts["wheat"] < wheat_target
                and sowable
                and counts.get("seed_WHEAT", int(seeds.get("WHEAT", 0))) > 0
                and day <= LAST_DAY - SOW_UNTIL):
            jobs.append(((BAND_WHEAT + egg) * near, ["PLANT", "WHEAT"]))
        # Deliberately still an if/elif chain, which is a real limitation
        # and is recorded as one.
        #
        # Because every empty tile offers the same jobs, exclusivity means
        # no tile offers a pen while the wheat quota is short -- and
        # harvesting destroys a wheat tile, so the quota is short most
        # turns. Making these additive does unfreeze the herd (25 animals
        # on a seed that had 7) and it costs 7,000: 40,379 against 47,395
        # on sixty paired games.
        #
        # The reason is the wage curve. Hands are priced on a fibonacci in
        # the number hired that day, so a crew of 12 costs 11,280 a season,
        # 14 costs 29,580 and 16 costs 77,490 -- more than the game pays.
        # Labour is hard-capped near twelve, a flock of 25 needs some 62
        # worker-turns a day to feed, care for and harvest, and the crew
        # cannot be bought. Filling sixty idle tiles with pens buys animals
        # nobody can tend.
        #
        # So the ceiling here is labour, not housing, and unblocking the
        # housing alone is not the answer.
        #
        # Re-tested once the crew was assigned globally, on the theory
        # that jobs now go to whoever is nearest and the extra options
        # would fill idle workers with local work. On coins it looked
        # tempting -- the floor rose 6,864 to 47,472 while mean and median
        # fell about 2,000 -- and on the forty-opponent panel it halves
        # the win rate, 4 games of 160 against 10. The floor was buying
        # consistency at the price of ever winning. Coins could not
        # resolve that and the win rate could.
        elif days_left > 5 and house_needed(
                counts, counts.get("bird", "GOOSE")) is not None:
            house = house_needed(counts, counts.get("bird", "GOOSE"))
            # An animal standing in the shed is capital already spent, so
            # housing it outranks housing one we have not bought yet.
            urgent = (counts.get("shed_" + house, 0)
                      + counts.get("unplaced_" + house, 0)) > 0
            early = counts["animals"] < EARLY_COOPS
            band = BAND_WHEAT + 1.0 if (urgent or early) else BAND_BUILD
            jobs.append((
                (band + egg) * near,
                ["BUILD_COOP" if house == "COOP" else "BUILD_PASTURE"],
            ))
        else:
            # Spare ground goes to cash crops, best price per tile first,
            # each capped at what its book will actually absorb.
            for crop, cap in crop_plan(day):
                if not sowable:
                    break
                spec = CROPS.get(crop)
                if spec is None or counts.get("crop_" + crop, 0) >= cap:
                    continue
                if day > last_sow_day(crop):
                    continue
                if counts.get("seed_" + crop, int(seeds.get(crop, 0))) <= 0:
                    continue
                if day > LAST_DAY - int(spec["first"]) - 1:
                    continue
                price = price_at(crop, inventory_of(observation, crop))
                jobs.append(((BAND_CROP + price) * near,
                             ["PLANT", crop]))
                break
        return jobs

    if not isinstance(tile, dict):
        return jobs

    kind = tile.get("kind")
    if "animal" in tile:
        held = int(tile.get("yield_units", 0) or 0)
        if not tile.get("fed_today") and int(inventory.get("WHEAT", 0)) > 0:
            jobs.append((BAND_FEED + egg * days_left * 0.1, ["FEED"]))
        if held > 0 and (held >= HARVEST_AT or closing):
            jobs.append((BAND_HARVEST + egg * held, ["HARVEST"]))
        if tile.get("fertilizer_available"):
            jobs.append((BAND_SERVICE + manure, ["COLLECT_FERTILIZER"]))
        if not tile.get("cared_today") and tile.get("fed_today"):
            jobs.append((BAND_SERVICE + egg * 0.9, ["CARE"]))
    elif kind in ("COOP", "PASTURE"):
        for animal, house in ANIMAL_HOME.items():
            if house == kind and int(inventory.get(animal, 0)) > 0:
                # Placing beats tending while the flock is still being
                # built: the bird earns for every remaining day, the
                # watering earns once.
                band = (BAND_FEED * 0.95 if day <= PLACE_PRIORITY_DAY
                        else BAND_PLACE)
                jobs.append((band + egg * days_left * 0.1,
                             ["PLACE", animal]))
                break
    elif kind == "PLANT":
        if not tile.get("watered_today"):
            jobs.append((BAND_WATER + egg * 0.5, ["WATER"]))
        if BAND_FERTILIZE > 0 and int(inventory.get("FERTILIZER", 0)) > 0:
            gain = fertilizer_gain(tile, day)
            if gain > 0:
                grown = str(tile.get("crop", "WHEAT"))
                worth = gain * price_at(grown, inventory_of(observation, grown))
                # Manure is a good with a price, not a free input. Spread
                # it only where the crop it creates beats what the same
                # unit would fetch sold, which is 62 to 84 at our volume.
                if worth > manure:
                    jobs.append((BAND_FERTILIZE + worth, ["FERTILIZE"]))
        # Only once it is actually ripe. `_new_plant` gives a non-ongoing
        # crop `yield_units = 1` the moment it goes in the ground, so a
        # bare "has yield" test made every worker harvest wheat on the
        # turn it was sown -- one unit taken and the tile destroyed, which
        # is why the farm never had a harvest to sell.
        crop = str(tile.get("crop", ""))
        spec = CROPS.get(crop)
        age = day - int(tile.get("planted_day", day))
        units = int(tile.get("yield_units", 0) or 0)
        if spec is not None and units > 0 and age >= int(spec["first"]):
            # Harvesting a non-ongoing crop *destroys the tile*, so taking
            # it the day it ripens throws away everything it had left to
            # give. Wheat starts at one unit, gains one for each watering
            # from age two to age four, and caps at six. Pulled at age two
            # it yields two; left to age four it yields four, or the full
            # six if it was fertilized -- the same seed, the same ground
            # and the same watering, for two to three times the grain.
            #
            # After max_day the tile only bleeds one unit every other step
            # before going to weed, so waiting is safe rather than a race.
            last = int(spec["max_day"])
            done = units >= int(spec["max_yield"])
            urgent = age >= last or done or closing
            # Unless the flock is actually going hungry, in which case
            # grain in two days is worth nothing to a bird that starves
            # tomorrow.
            #
            # This is a board-wide flag, not a per-tile one: any animal
            # unfed with an empty shed releases *every* ripe wheat tile at
            # once. That looks like a bug, and an audit flagged it as one
            # -- some seventy per cent of wheat is taken early at 1.69
            # units against a possible four, around 210 units a game.
            #
            # Rationing it to roughly the number of hungry animals costs
            # 5,140 mean and 8,628 median (42,346 / 41,430 against
            # 47,486 / 50,058 on sixty paired games), so the greedy
            # version stays. The arithmetic is not close: two extra units
            # of wheat are worth about 42 coins, while an animal that
            # misses two meals escapes and forfeits its whole remaining
            # output, on the order of 1,000 to 1,800. On this farm keeping
            # animals alive dominates yield per tile, and it is worth
            # over-harvesting to be sure of it.
            if FEED_DEFICIT_RULE:
                starving = (crop == "WHEAT"
                            and feed_deficit(counts, shed) > 0)
            else:
                hungry = (counts.get("hungry", 0)
                          if STARVING_MEANS_MISSED_MEAL else counts["unfed"])
                starving = (crop == "WHEAT" and hungry > 0
                            and int(shed.get("WHEAT", 0)) <= 0)
            if urgent or starving or spec["ongoing"] or not HARVEST_HOLD:
                value = BAND_HARVEST + egg * 0.5 * units
                jobs.append((value * (1.35 if age > last else 1.0),
                             ["HARVEST"]))
    elif kind == "WEED":
        # The corpus digs 36 weeds a game. A weed occupies ground
        # that could hold a coop or a crop for the rest of the season.
        # The corpus digs 36 weeds a game, but raising DIG to compete with
        # watering measured neutral at best (19,326 against 19,583 at two
        # quadrants) and the baseline value is kept.
        jobs.append((BAND_WATER * 0.4, ["DIG"]))

    return [(v, a) for v, a in jobs if v > 0]


def still_possible(counts: dict[str, int], action: list[Any]) -> bool:
    """Can this job still be done, given what has been handed out already?

    Jobs are scored against one snapshot of the board and then assigned in
    order, so by the time a job is reached the seed, the pen or the shed
    animal it needs may already be spoken for.
    """
    op = action[0] if action else "PASS"
    if op == "PLANT":
        crop = str(action[1]) if len(action) > 1 else "WHEAT"
        return counts.get("seed_" + crop, 0) > 0
    if op == "PICKUP":
        item = str(action[1]) if len(action) > 1 else ""
        return counts.get("shed_" + item, 0) > 0
    if op == "PLACE":
        animal = str(action[1]) if len(action) > 1 else "GOOSE"
        key = ("empty_coops" if ANIMAL_HOME.get(animal) == "COOP"
               else "empty_pastures")
        return counts.get(key, 0) > 0
    if BUILD_CLAIM and op in ("BUILD_COOP", "BUILD_PASTURE"):
        return pen_short(counts, "COOP" if op == "BUILD_COOP" else "PASTURE")
    return True


def claim(counts: dict[str, int], action: list[Any]) -> None:
    """Update the board census for a job just handed to a worker.

    Thirteen workers are assigned from one snapshot, so without this every
    one of them sees the same empty board and takes the same job. That is
    literally what happened: all thirteen built a coop on the same turn.
    """
    op = action[0] if action else "PASS"
    if op == "PLANT":
        crop = str(action[1]) if len(action) > 1 else "WHEAT"
        key = "seed_" + crop
        counts[key] = max(0, counts.get(key, 0) - 1)
    if op == "BUILD_PASTURE":
        counts["empty_pastures"] += 1
        counts["free"] = max(0, counts["free"] - 1)
    elif op == "BUILD_COOP":
        counts["empty_coops"] += 1
        counts["free"] = max(0, counts["free"] - 1)
    elif op == "PLANT":
        crop = str(action[1]) if len(action) > 1 else "WHEAT"
        if crop == "WHEAT":
            counts["wheat"] += 1
        else:
            counts["crop_" + crop] = counts.get("crop_" + crop, 0) + 1
        counts["free"] = max(0, counts["free"] - 1)
    elif op == "FEED":
        counts["unfed"] = max(0, counts["unfed"] - 1)
    elif op == "CARE":
        counts["uncared"] = max(0, counts["uncared"] - 1)
    elif op == "COLLECT_FERTILIZER":
        counts["manure"] = max(0, counts["manure"] - 1)
    elif op == "HARVEST":
        counts["ripe"] = max(0, counts["ripe"] - 1)
    elif op == "WATER":
        counts["dry"] = max(0, counts["dry"] - 1)
    elif op == "PLACE":
        animal = str(action[1]) if len(action) > 1 else "GOOSE"
        key = ("empty_coops" if ANIMAL_HOME.get(animal) == "COOP"
               else "empty_pastures")
        counts[key] = max(0, counts[key] - 1)
        counts["animals"] += 1
        if animal == "GOOSE":
            counts["geese"] += 1
        house = ANIMAL_HOME.get(animal, "COOP")
        counts["unplaced_" + house] = max(
            0, counts.get("unplaced_" + house, 0) - 1)
    elif op == "PICKUP":
        # Without this the shed reads full to every worker at once: three
        # of them fetch the same single goose and two of the trips are
        # silent no-ops. Measured at 48 to 58 wasted pickups a game.
        item = str(action[1]) if len(action) > 1 else ""
        qty = int(action[2]) if len(action) > 2 else 1
        key = "shed_" + item
        counts[key] = max(0, counts.get(key, 0) - qty)
        if item == "WHEAT" and FEED_PICKUP_TO_NEED:
            counts["wheat_carried"] = counts.get("wheat_carried", 0) + qty
            counts["hungry_fetched"] = counts.get("hungry_fetched", 0) + qty
        if item in ANIMAL_HOME:
            house = ANIMAL_HOME[item]
            counts["shed_" + house] = max(
                0, counts.get("shed_" + house, 0) - qty)
            counts["unplaced_" + house] = counts.get(
                "unplaced_" + house, 0) + qty


def hands_target(day: int, counts: dict[str, int] | None = None) -> int:
    """How large the crew should be today.

    Ramped with income, and then capped by the work actually standing on
    the board. Instrumenting every idle turn shows they are not spread
    across the game at all: days 0 to 20 are almost fully employed, and
    roughly forty per cent of all idle turns fall in days 27 to 29, when
    the crops are harvested out and there is nothing left to do. The farm
    was paying a full crew to watch.

    The wage makes that expensive. It is fibonacci in the number hired
    that day, so the tenth, eleventh and twelfth hands cost 288 of the 376
    a day a crew of twelve costs -- four idle days is some 1,500 coins for
    no work at all.

    So the crew is sized to the jobs standing: dry ground, ripe tiles,
    hungry and uncared animals, manure waiting to be collected. A floor
    keeps enough hands to feed the flock however quiet the board goes.
    """
    wanted = HAND_RAMP[0][1]
    for start, size in HAND_RAMP:
        if day >= start:
            wanted = size
    wanted = min(wanted, HAND_CAP)
    if counts is not None and CREW_TO_WORK:
        standing = (counts.get("dry", 0) + counts.get("ripe", 0)
                    + counts.get("unfed", 0) + counts.get("uncared", 0)
                    + counts.get("manure", 0))
        wanted = min(wanted, max(CREW_FLOOR, int(standing * CREW_TO_WORK)))
    return wanted


def preferred_bird(observation: dict[str, Any]) -> str:
    """Goose unless this town's own draw clearly wants otherwise.

    `observation["town"]["unlocked_shops"]` is public and exact, and
    `rl/demand.py` turns it into the units the town will still absorb.
    Section 9v measured adapting production to that draw as the cleanest
    correlate of rank in the data: +0.672 for teams above 2850, +0.000
    below 2400.

    Egg is the default because in a contested game it runs 50 -> 92 while
    milk collapses 160 -> 13 and wool 200 -> 1 -- the town keeps draining a
    book neither player floods. It takes a clear margin to beat that.
    """
    demand = remaining_demand(observation)
    best, score = "GOOSE", demand.get("EGG", 0.0) * price_at(
        "EGG", inventory_of(observation, "EGG"))
    for animal, product in (("SHEEP", "WOOL"), ("COW", "MILK")):
        pull = demand.get(product, 0.0) * price_at(
            product, inventory_of(observation, product))
        if pull > score * DEMAND_MARGIN:
            best, score = animal, pull
    return best


ANIMAL_HOME = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def herd_plan(observation: dict[str, Any], counts: dict[str, int],
              total: int) -> dict[str, int]:
    """How many of each animal we want standing.

    This replaces picking a single `preferred_bird` and building only for
    it, which is what froze the farm after day six: once the town's draw
    moved, the winning animal's pen type was the only one ever considered,
    the other had no empty pen, and the buy gate refused for the rest of
    the game.

    It is also the wrong shape economically. A pen and the animal standing
    in it are capital already spent, and a shift in demand does not refund
    it -- the right response to falling demand is to stop *growing* that
    line, not to abandon what it already produces. So demand decides who
    gets the growth, every line that we already own keeps a floor share,
    and nothing is ever torn down.

    332 elite tapes buy a median of 3 geese, 8 cows and 6 sheep: a
    permanently mixed herd of about seventeen, never a single species.

    A known defect, left in place because the fix measured worse. Weighing
    by `demand x price` favours milk and wool -- bases of 160 and 200
    against egg's 50 -- and those are exactly the two books that collapse,
    after 76 and 59 units. A trace shows `want_GOOSE` pinned at 1 for all
    thirty days, the farm holding one goose and five cows, in an agent
    whose thesis is the goose.

    Pricing each line by `sale_revenue` instead, so the curve is walked
    down as units are sold and a sixth cow is valued into the book its
    five predecessors flooded, gives a more balanced herd -- 2 geese, 4
    cows, 2 sheep -- and costs 11,087 (55,826 against 66,913). The
    balanced herd is worth less than the lopsided one, so whatever is
    wrong here, the animal mix is not it.

    Tested again as an interaction, because a six-animal herd cannot flood
    any book and the mix ought to matter only at scale -- and a diagnostic
    had shown that a seventeen-animal herd reaches the corpus's own four
    hundred animal-days, with nothing escaping, feed and care at one per
    animal-day and idle turns down to 7.7%, and *still* loses. The obvious
    reading was that its extra output was going into collapsed books.

    It runs the other way. Pricing by revenue gets steadily worse as the
    herd grows: 60,571 at six, 49,207 at twelve, 41,290 at seventeen,
    against 67,325 for the sticker-priced six. Whatever a large herd costs
    us, it is not the species mix, and the mix is worth less the more
    animals there are to apply it to.
    """
    demand = remaining_demand(observation)
    pull: dict[str, float] = {}
    for animal, product in ANIMAL_PRODUCT.items():
        pull[animal] = max(0.0, demand.get(product, 0.0) * price_at(
            product, inventory_of(observation, product)))
    weight = sum(pull.values())
    if weight <= 0.0:
        share = {a: 1.0 / len(pull) for a in pull}
    else:
        share = {a: pull[a] / weight for a in pull}
    # A line we already keep never drops below its floor, however the
    # town's appetite moves.
    for animal in share:
        if counts.get("have_" + animal, 0) > 0:
            share[animal] = max(share[animal], HERD_FLOOR)
    scale = sum(share.values()) or 1.0
    return {a: int(round(share[a] / scale * total)) for a in share}

# What price the top of the ladder actually accepts, as a multiple of each
# good's base. Measured by pairing every sale in thirty elite games with
# the market inventory at that instant and pricing it:
#
#     WHEAT 1.72   TOMATO 1.32   EGG 1.06   CARROT 0.83   MELON 0.73
#     MILK 0.71    WOOL 0.65     FERTILIZER 0.54   STRAWBERRY 0.15
#
# They are not selling on a schedule. They hold wheat until the town has
# drained it to nearly twice base and they let fertilizer go at half,
# because wheat is consumed by five of the eight shops and manure is
# produced by every animal on both farms. Strawberry at 0.15 is what a
# good looks like when both players flood a 62-unit book.
#
# G sold everything the turn it had it, which takes the average price
# rather than the good one.
SELL_TARGET = {
    "WHEAT": 1.55, "TOMATO": 1.25, "EGG": 1.05, "CARROT": 0.85,
    "MELON": 0.75, "MILK": 0.72, "WOOL": 0.66, "FERTILIZER": 0.55,
    "STRAWBERRY": 0.30,
}
# Scales every threshold, and it is 0.0 -- sell on sight -- because the
# thresholds above do not pay: 32,693 selling immediately against 32,588,
# 31,856 and 24,891 as patience rises.
#
# This is the sixth independent test of holding stock for a better price
# (rl/sell_floor.py, rl/demand_sales.py pacing, rl/trickle.py, and this),
# and all six say no. The reading of the elite ratios above was wrong:
# they are a market *state*, not a decision. Wheat trades at 1.72x base
# because five of the eight shops eat it and it is chronically scarce, not
# because anyone waited. Meanwhile a coin banked on day 6 buys a bird that
# lays for the rest of the season, so patience costs compounding and buys
# a price the market was going to offer anyway.
SELL_PATIENCE = 0.0
# Track seeds as a claimable resource within a turn.
#
# Without it thirteen workers all read the same seed count and all issue
# PLANT when only the first can spend the seed. Turning it on moves the
# action profile onto the elite's -- PLANT 402 to 214 against their 224,
# CARE up to 322 against their 339 -- and is worth nothing: 6 of 12 paired
# seeds, medians 25,412 against 25,418. The wasted plant was displacing a
# job of about equal value, so correcting it just changes which turn is
# spent. Kept because the model is right and the action counts now match
# the corpus, not because it pays.
SEED_CLAIM = True

# A mixed herd, because the two products pay at opposite ends of the game.
#
# In a contested match milk opens at 160 and wool at 200, and both are
# still near that through day 6 -- then they collapse to 13 and 1 as both
# farms flood books that hold 76 and 59 units. Egg opens at 50 and *rises*
# to 92, because its curve is logarithmic and the town keeps draining a
# book nobody floods.
#
# So the first animals should be whichever pasture beast the town wants,
# bought early enough to sell into that opening window, and the rest
# geese for the twenty days after it closes. A monoculture takes one half
# of that and leaves the other.
MIXED_EARLY = 6


def crop_priority(observation: dict[str, Any]) -> list[tuple[str, int]]:
    """Crops worth ground here, best first, with the tile cap for each.

    The same argument as the animal choice. A fixed list plants melon in a
    town that never draws a PIZZA_SHOP and carrot in one that draws three,
    which is planting by habit. `remaining_demand` says what this town will
    still absorb; multiplying by the live price gives the coins actually
    available in each crop, and the cap keeps us from filling a book we
    have already saturated.

    Wheat is excluded deliberately: it is feed, and its acreage is set by
    the size of the flock rather than by what the town wants.
    """
    demand = remaining_demand(observation)
    ranked = []
    for crop, cap in CROP_TILES:
        pull = demand.get(crop, 0.0) * price_at(
            crop, inventory_of(observation, crop))
        ranked.append((pull, crop, cap))
    ranked.sort(reverse=True)
    return [(crop, cap) for pull, crop, cap in ranked if pull > 0]


def early_seed_orders(
    day: int,
    counts: dict[str, int],
    seeds: dict[str, int],
    budget: float,
    orders: list[list[Any]],
) -> float:
    """Crop seed the day's cash can pay for; returns the budget left."""
    free = counts.get("free", 0) - sum(int(v) for v in seeds.values())
    allowance = SEED_FIRST_DAILY_SPEND
    plan = list(crop_plan(day))
    if SEED_FIRST_ORDER is not None:
        rank = {crop: i for i, crop in enumerate(SEED_FIRST_ORDER)}
        plan.sort(key=lambda pair: rank.get(pair[0], len(rank)))
    for crop, cap in plan:
        if len(orders) >= MAX_ORDERS or free <= 0:
            break
        spec = CROPS.get(crop)
        if spec is None or day > LAST_DAY - int(spec["first"]) - 1:
            continue
        if day > last_sow_day(crop):
            continue
        cost = float(spec["seed"])
        quantity = min(
            cap - counts.get("crop_" + crop, 0) - int(seeds.get(crop, 0)),
            free,
            int(min(budget - SEED_FIRST_FLOOR, allowance) // cost),
        )
        if quantity > 0:
            orders.append(["BUY_SEED", crop, quantity])
            budget -= cost * quantity
            allowance -= cost * quantity
            free -= quantity
    return budget


def market_orders(
    observation: dict[str, Any],
    day: int,
    counts: dict[str, int],
    shed: dict[str, int],
    seeds: dict[str, int],
    money: float,
    hands: int,
) -> list[list[Any]]:
    """Sell the deep books, then buy the flock that fills them."""
    orders: list[list[Any]] = []
    closing = day >= LAST_DAY - 1
    budget = money

    # 1. Sell. Egg and fertilizer are the thesis; wheat above the feed
    #    reserve is surplus. Nothing is held back: both books are deep
    #    enough that waiting only forfeits the sale (10.8ad measured
    #    metering the same units onto more turns as strictly worse).
    reserve = 0 if closing else int(counts["animals"] * 2)
    # Patience decays to nothing over the season: a good held past the
    # close is worth zero, so the threshold has to reach zero before then.
    slack = max(0.0, (LAST_DAY - 2 - day) / float(max(1, LAST_DAY - 2)))
    total_shed = sum(shed.values())
    for item in ("EGG", "FERTILIZER", "MILK", "WOOL", "CARROT",
                 "TOMATO", "STRAWBERRY", "MELON", "WHEAT"):
        held = int(shed.get(item, 0))
        if item == "WHEAT":
            held = max(0, held - reserve)
        elif (item == "FERTILIZER" and STRAWBERRY_FERT_STOCK
              and not closing):
            # Keep what today's strawberry productions can use.
            held = max(0, held - counts.get("fert_need", 0))
        if (FLOOR_HOLD is not None and item in FLOOR_HOLD_GOODS
                and not closing and total_shed < FLOOR_HOLD_ROOM
                and town_takes(observation, item)):
            base_price = float(MARKET_PARAMS.get(item, {}).get("base", 1))
            if price_at(item, inventory_of(observation, item)) \
                    < FLOOR_HOLD * base_price:
                # The book is flooded and the town is still eating it.
                continue
        if (SELL_CARRIED_AT_CLOSE
                and int(observation.get("step", 0)) >= DROP_FROM_STEP):
            # Covers whatever is DROPped this turn; fills stop at the shed.
            held += 99
        if held <= 0 or len(orders) >= MAX_ORDERS:
            continue
        base = float(MARKET_PARAMS.get(item, {}).get("base", 1))
        want = base * SELL_TARGET.get(item, 0.8) * SELL_PATIENCE * slack
        now = price_at(item, inventory_of(observation, item))
        # Sell when the price is worth taking, when the season is closing,
        # or when the shed is near its hundred-unit cap and the overflow
        # would be discarded at the day boundary anyway.
        night_tip = (NIGHT_TIP_GUARD is not None
                     and int(observation.get("step", 0)) % 24 >= 22
                     and total_shed + counts.get("carried_total", 0)
                     > NIGHT_TIP_GUARD)
        if now >= want or closing or total_shed >= 85 or night_tip:
            orders.append(["SELL", item, held])

    # 2. Crew. Hands are hired daily and wiped nightly, and the cost is
    #    fibonacci in the number hired today, so the early ones are almost
    #    free and the schedule is what limits the farm, not the wage.
    # Once a day, not once a turn. Hands are wiped nightly and the fibonacci
    # wage restarts each morning, so the roster has to be rebuilt daily --
    # but issuing the order every turn hires seventy-two times a day and
    # took the opening purse from 2,846 to nothing by day eight, leaving
    # one hand to work the whole farm.
    hour = int(observation.get("step", 0)) % 24
    target = hands_target(day, counts)
    if day <= HIRE_UNTIL_DAY and hands < target and hour <= 2:
        wanted = min(target - hands, 4)
        for _ in range(wanted):
            if len(orders) >= MAX_ORDERS:
                break
            orders.append(["HIRE"])

    # Buying stops once the season is closing -- ground, animals and seed
    # cannot pay for themselves in two days -- but the crew and the feed
    # ration above must not, which is why this sits here and not before
    # them. It used to sit above the hiring block, so on day 28 the farm
    # dismissed all twelve hands and played the last two days with the
    # farmer alone: 36 idle tiles, animals escaping for want of a feeder,
    # and every job on the board going unclaimed.
    if closing:
        return orders[:MAX_ORDERS]

    # 3. Ground, as soon as it is affordable.
    quadrants = len(
        (observation.get("farms") or [{}])[
            int(observation.get("player", 0))
        ].get("unlocked_quadrants") or []
    )
    # Bought on cash rather than on a named day, when LAND_CASH is set.
    #
    # The fixed schedule sits on a cliff. Days 1 and 5 give 67,697 and
    # days 1 and 4 give 44,943 -- one day's difference on the second
    # purchase costs 22,754, because it catches the farm with just enough
    # to spend and nothing left to work the ground with. A schedule tuned
    # one day from a hole that size is fragile even when it is standing on
    # the right side of it, and the seed decides which side that is.
    #
    # A cash rule has no cliff: it fires when the farm can actually afford
    # the ground *and* still stock it.
    if LAND_CASH > 0:
        buy_land = (
            quadrants < MAX_QUADRANTS
            and budget > LAND_CASH
            and day <= LAND_LAST_DAY
            and int(observation.get("hour", 0)) == 1
        )
    else:
        buy_land = day in LAND_DAYS and budget > LAND_RESERVE
    if buy_land and quadrants < MAX_QUADRANTS and len(orders) < MAX_ORDERS:
        orders.append(["BUY_LAND"])
        budget -= LAND_RESERVE

    # 3b. On the opening days crop seed is bought out of what the herd
    #     leaves, below -- see SEED_FIRST_UNTIL_DAY.
    early_seed = (SEED_FIRST_UNTIL_DAY is not None
                  and SEED_FIRST_FROM_DAY <= day <= SEED_FIRST_UNTIL_DAY)

    # 4a. Which bird. Geese unless the town's own draw says otherwise by a
    #     clear margin -- a coop and a pasture are both free to build, so
    #     the only cost of following the town is noticing in time.
    bird = counts.get("bird", "GOOSE")
    # Early birds chase the opening price window on milk and wool; the
    # rest are geese, whose book never floors.
    # `preferred_bird` already made this decision in decide() and the
    # scheduler has been building housing for it all turn. Recomputing it
    # here duplicated the logic and silently overrode MIXED_EARLY, which is
    # why the mixed-herd sweep returned four identical numbers.

    # 4. Birds. One per turn, only into a coop that is standing empty and
    #    only while the wheat area can feed what we already have -- the
    #    flock must never outrun its feed, because two missed meals lose
    #    the animal outright.
    # Buy whichever line is furthest below its target and has a pen
    # standing empty. Choosing by deficit rather than by today's favourite
    # is what stops the farm freezing: the old gate asked only whether the
    # *preferred* animal's house had room, so a farm holding pastures and
    # wanting geese bought nothing at all, for the rest of the game.
    total_animals = counts["animals"] + sum(
        int(shed.get(a, 0)) for a in ANIMAL_HOME)
    feedable = counts["wheat"] * WHEAT_PER_BIRD + shed.get("WHEAT", 0) / 3.0
    if (
        budget > GOOSE_COST + GOOSE_CASH_FLOOR
        and (total_animals < EARLY_BIRDS or total_animals < feedable)
        and day <= LAST_DAY - SOW_UNTIL
        and len(orders) < MAX_ORDERS
    ):
        best_gap, pick = 0, None
        for animal in ANIMAL_HOME:
            waiting = int(shed.get(animal, 0))
            pens = counts["empty_coops" if ANIMAL_HOME[animal] == "COOP"
                          else "empty_pastures"]
            if pens <= waiting:
                continue
            # An animal in a worker's arms, on its way to a pen, is bought
            # already. Leaving it out re-bought every one in transit: a
            # herd aimed at seventeen ended the season at twenty-six, with
            # twelve sheep for a target of six and the cash gone by day 9.
            # Off by default -- see COUNT_CARRIED.
            carried = (counts.get("carried_" + animal, 0)
                       if COUNT_CARRIED else 0)
            gap = (counts.get("want_" + animal, 0)
                   - counts.get("have_" + animal, 0) - waiting - carried)
            if gap > best_gap:
                best_gap, pick = gap, animal
        if pick is not None:
            cost = ANIMALS[pick]["cost"]
            room = counts["empty_coops" if ANIMAL_HOME[pick] == "COOP"
                          else "empty_pastures"] - int(shed.get(pick, 0))
            affordable = int((budget - GOOSE_CASH_FLOOR) // cost)
            want = max(0, min(BIRDS_PER_TURN, room, affordable, best_gap))
            if want > 0:
                orders.append(["BUY_ANIMAL", pick, want])
                budget -= cost * want

    # 4b. Feed bought from the market, which is how the top of the ladder
    #     opens. Their very first order of the game is BUY_PRODUCT WHEAT
    #     13, before a single hire or animal, and only then do they hire
    #     five hands and buy four animals -- all on day zero.
    #
    #     G grew every grain it ever ate, which left a hole it could not
    #     cover: nothing is harvestable before day two, and now that crops
    #     are held to their last yield day, nothing arrives before day
    #     four. An animal unfed two days running escapes, so a flock
    #     bought on day zero cannot survive to its first harvest on grain
    #     alone.
    #
    #     The trade is heavily favourable. Wheat costs about 28 a unit to
    #     buy; a goose eats one a day and lays an egg worth 50 to 92. The
    #     old note that buying feed cost 4,000 was measured against the
    #     broken opening -- before the harvest hold widened the gap and
    #     while the ration floor sat above the farm's operating cash.
    stock_target = int(
        max(counts["animals"] + int(shed.get(bird, 0)), FEED_MIN_FLOCK)
        * FEED_STOCK_DAYS
    )
    have_wheat = int(shed.get("WHEAT", 0))
    if (
        FEED_STOCK_DAYS > 0
        and day <= FEED_BUY_UNTIL
        and have_wheat < stock_target
        and budget > FEED_STOCK_FLOOR
        and len(orders) < MAX_ORDERS
    ):
        want = min(stock_target - have_wheat,
                   int((budget - FEED_STOCK_FLOOR) // 30))
        if want > 0:
            orders.append(["BUY_PRODUCT", "WHEAT", want])
            budget -= 30.0 * want


    # 5. Seed, wheat only. Every other crop grows into a book that floors
    #    before the season ends; wheat feeds the flock and its own curve
    #    never falls.
    # Seed, wheat only, and once a day. Ordering it every turn bought two
    # hundred seeds a day and drained the opening purse into ground that
    # was never sown.
    hour = int(observation.get("step", 0)) % 24
    if (
        hour == 1
        and int(seeds.get("WHEAT", 0)) < SEED_BUFFER
        and budget > GOOSE_CASH_FLOOR
        and day <= LAST_DAY - 5
        and len(orders) < MAX_ORDERS
    ):
        want = SEED_BUFFER - int(seeds.get("WHEAT", 0))
        orders.append(["BUY_SEED", "WHEAT", want])
    if early_seed and hour == 2:
        budget = early_seed_orders(day, counts, seeds, budget, orders)
    if (hour == 2 and budget > CROP_SEED_FLOOR and not early_seed
            and day <= LAST_DAY - SOW_UNTIL):
        opening = (OPENING_CROP_TILES is not None
                   and day <= OPENING_UNTIL_DAY)
        for crop, cap in crop_plan(day):
            if len(orders) >= MAX_ORDERS:
                break
            if (SEED_ONLY_WHEN_SOWABLE and crop in CROPS
                    and day > LAST_DAY - int(CROPS[crop]["first"]) - 1):
                continue
            if day > last_sow_day(crop):
                continue
            # In the opening, seed is bought towards the cap in batches of up
            # to OPENING_SEED_BATCH. Buying a whole cap at once spent 3,200
            # coins on strawberry seed on day 0 and starved land, herd and
            # feed: one reference game fell from 62,461 to 30,654.
            batch = (min(OPENING_SEED_BATCH,
                         max(0, cap - counts.get("crop_" + crop, 0)))
                     if opening else CROP_SEED_BATCH)
            standing = counts.get("crop_" + crop, 0)
            in_hand = int(seeds.get(crop, 0))
            quantity = batch - in_hand if opening else CROP_SEED_BATCH
            if SEED_TO_CAP:
                # Seed in hand is ground already spoken for.
                quantity = min(quantity, cap - standing - in_hand)
            if (standing < cap and in_hand < batch and quantity > 0):
                orders.append(["BUY_SEED", crop, quantity])

    # 6. Emergency ration, so a late harvest never costs a bird.
    if FEED_DEFICIT_RULE:
        short = feed_deficit(counts, shed)
        if short > 0 and budget > RATION_FLOOR and len(orders) < MAX_ORDERS:
            orders.append(["BUY_PRODUCT", "WHEAT", min(short, 6)])
    elif (
        counts["unfed"] > 0
        and int(shed.get("WHEAT", 0)) <= 0
        and budget > RATION_FLOOR
        and len(orders) < MAX_ORDERS
    ):
        orders.append(["BUY_PRODUCT", "WHEAT", min(counts["unfed"], 6)])

    return orders[:MAX_ORDERS]


def decide(observation: dict[str, Any]) -> AgentAction:
    farm = _farm(observation)
    tiles = farm.get("tiles") or []
    player_id = int(observation.get("player", 0))
    # One process replays many games in a row, so the walking memory has to
    # start empty at every episode.
    if int(observation.get("step", 0)) == 0:
        _EN_ROUTE.clear()
    if not tiles:
        return {"farmer": PASS, "hands": [], "market": []}

    day = int(observation.get("day", int(observation.get("step", 0)) // 24))
    closing = day >= LAST_DAY - 1
    positions = _positions(farm)
    shed = _shed(observation)
    seeds = _seeds(observation)
    counts = census(tiles)
    money = float(farm.get("money", 0.0) or 0.0)
    # Which animal this town actually wants. The scheduler needs to know
    # before it builds anything, because a cow needs a pasture and a goose
    # needs a coop -- buying the animal the town wants and then housing it
    # nowhere leaves it standing in the shed, which is exactly what the
    # first attempt at this did.
    counts["bird"] = preferred_bird(observation)
    # Seeds are a claimable resource, not a constant. Thirteen workers all
    # read the same seed count and all issue PLANT, but only the first can
    # spend the seed -- the rest walk to a tile and do nothing. G issued
    # 402 PLANT actions a game against the elite's 224 on a larger farm,
    # and that gap is workers planting seed that was already gone.
    if SEED_CLAIM:
        for crop, have in seeds.items():
            counts["seed_" + crop] = int(have)
    # Mirror the shed and every worker's arms into the census, so that
    # claim() can decrement them as jobs are handed out. Without this the
    # thirteen workers all read the same full shed and the same empty
    # pens, and most of the resulting trips are silent no-ops.
    counts["shed_WHEAT"] = int(shed.get("WHEAT", 0))
    counts["wheat_carried"] = sum(
        int(_inventory(observation, worker).get("WHEAT", 0))
        for worker in range(len(positions)))
    counts["carried_total"] = sum(
        sum(int(v) for v in _inventory(observation, worker).values()
            if int(v) > 0)
        for worker in range(len(positions)))
    counts["fert_carried"] = sum(
        int(_inventory(observation, worker).get("FERTILIZER", 0) or 0)
        for worker in range(len(positions)))
    counts["fert_need"] = 0
    if STRAWBERRY_FERT_STOCK:
        for row in tiles:
            for tile in row:
                if (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                        and CROPS.get(str(tile.get("crop", "")), {}).get(
                            "ongoing")
                        and fertilizer_gain(tile, day) > 0):
                    counts["fert_need"] += 1
    counts["shed_total"] = sum(int(v) for v in shed.values())
    # The herd we are aiming at, recomputed each turn so the mix follows
    # the town without ever abandoning a line already paid for.
    herd = (dict(HERD_MIX) if HERD_MIX is not None
            else herd_plan(observation, counts, HERD_TARGET))
    for animal in ANIMAL_HOME:
        counts["want_" + animal] = int(herd.get(animal, 0))
    for house in ("COOP", "PASTURE"):
        counts["shed_" + house] = 0
        counts["unplaced_" + house] = 0
    for animal, house in ANIMAL_HOME.items():
        waiting = int(shed.get(animal, 0))
        counts["shed_" + animal] = waiting
        counts["shed_" + house] += waiting
        counts["carried_" + animal] = 0
        for worker in range(len(positions)):
            held = int(_inventory(observation, worker).get(animal, 0))
            counts["unplaced_" + house] += held
            counts["carried_" + animal] += held
    # crop_priority is deliberately not used to reorder planting. Ranking
    # crops by remaining demand times price measured 24,257 against 32,693
    # for the fixed order, because that product is the coins available in a
    # crop while the binding constraint is *tiles*: melon's demand is small
    # and it still pays 250 a unit, so a total-coins ranking buries it
    # under carrot. The animal choice does not have this problem -- a pen
    # is a pen -- which is why demand drives that and not this.

    # Workers are assigned in order, each taking the best job left on the
    # board. Claimed tiles are struck out so two workers never walk to the
    # same job and waste a turn between them.
    claimed: set[tuple[int, int]] = set()
    actions: list[list[Any]] = []
    # A share of the crew that may only tend: water, feed, care. The
    # bands put HARVEST, PLANT and PLACE above WATER and CARE, so on a
    # busy board maintenance can be starved by work that pays sooner --
    # and a plant unwatered two days becomes a weed, an animal unfed two
    # days escapes. This reserves capacity against that.
    reserved = int(len(positions) * RESCUE_SHARE)
    # Every worker against every job, then assign best pair first.
    #
    # This used to run worker by worker: worker 0 scanned the whole board,
    # took the highest-scoring job anywhere on it, and only then did
    # worker 1 choose from what was left. So the first worker would walk
    # twelve tiles to a job that a worker already standing on it would
    # have taken for nothing, and that worker would then walk somewhere
    # else. 54% of all worker turns were movement.
    #
    # Scoring every (worker, job) pair and assigning the best pair first
    # costs no more calls to job_value -- it is the same crew against the
    # same board -- and lets proximity settle who goes where.
    candidates: list[tuple[float, int, tuple[int, int], list[Any], int]] = []
    for worker, position in enumerate(positions):
        tending_only = worker < reserved
        inventory = _inventory(observation, worker)
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if not _owned(tiles, x, y) and not (
                        SHED_ALL_ACCESS and _shed_adjacent(x, y)):
                    continue
                travel = distance(position, (x, y))
                if ZONE_TAX < 1.0 and len(positions) > 1:
                    width = max(1, len(tiles[y]) // len(positions))
                    home = worker * width
                    in_zone = home <= x < home + width
                else:
                    in_zone = True
                for value, act in job_value(
                    observation, tiles[y][x], x, y, inventory, day,
                    shed, seeds, counts, closing,
                ):
                    if tending_only and act[0] not in TENDING:
                        continue
                    now_step = int(observation.get("step", 0))
                    if (CLOSE_ONLY_GOODS_FROM_STEP is not None
                            and now_step >= CLOSE_ONLY_GOODS_FROM_STEP
                            and act[0] not in GOODS_JOBS):
                        continue
                    if (CLOSE_HARVEST_MUST_LAND
                            and CLOSE_RETURN_FROM_STEP is not None
                            and now_step >= CLOSE_RETURN_FROM_STEP
                            and act[0] in ("HARVEST", "COLLECT_FERTILIZER")):
                        home = min(distance((x, y), s) for s in shed_tiles())
                        # Walk there, act, walk home, drop.
                        if now_step + travel + 1 + home > LAST_ACT_STEP:
                            continue
                    night_trip = (act[0] == "DROP"
                                  and night_load_high(observation, counts)
                                  and travel <= 23 - now_step % 24) or (
                        act[0] == "DROP"
                        and tip_guard_high(observation, counts)
                        and travel <= 22 - now_step % 24)
                    if night_trip or (
                            CLOSE_RETURN_FROM_STEP is not None
                            and act[0] == "DROP"
                            and now_step >= CLOSE_RETURN_FROM_STEP
                            and travel <= LAST_ACT_STEP - now_step):
                        # The season's last trip to the shed is not
                        # discounted for distance while it can still land.
                        score = value
                    else:
                        score = value / (travel + 1.0) ** TRAVEL_EXPONENT
                    if not in_zone:
                        score *= ZONE_TAX
                    if STICKY_TARGET is not None:
                        booked = _EN_ROUTE.get((player_id, worker))
                        if (booked is not None and booked[0] == (x, y)
                                and booked[1] == act[0]):
                            score *= STICKY_TARGET
                    if score > 0.0:
                        candidates.append((score, worker, (x, y), list(act),
                                           travel))
    # GLOBAL_ASSIGN off reverts to the old worker-by-worker rule, where
    # worker 0 took the best job anywhere on the board before worker 1
    # chose at all. Kept switchable so the change can be re-measured on a
    # panel wide enough to mean something.
    if GLOBAL_ASSIGN:
        candidates.sort(key=lambda c: -c[0])
    else:
        candidates.sort(key=lambda c: (c[1], -c[0]))

    chosen: dict[int, list[Any]] = {}
    booked_this_turn: list[tuple[int, tuple[int, int], list[Any], int]] = []
    for _score, worker, cell, act, travel in candidates:
        if worker in chosen or cell in claimed:
            continue
        # Scores were computed before any of this turn's jobs were handed
        # out, so a job that needed the last seed or the last empty pen
        # may no longer be possible by the time it is reached.
        # A walking builder is booked for the pen it is walking to, and every
        # build is re-checked against the pens still short -- see BUILD_CLAIM.
        building = BUILD_CLAIM and act[0] in ("BUILD_COOP", "BUILD_PASTURE")
        if (travel == 0 or building) and not still_possible(counts, act):
            continue
        # Once the night's tip fits, stop sending carriers home early -- see
        # NIGHT_TIP_GUARD. The closing return is left alone.
        if (NIGHT_TIP_GUARD is not None and act[0] == "DROP" and travel > 0
                and NIGHT_FROM_HOUR
                <= int(observation.get("step", 0)) % 24 <= 22
                and (CLOSE_RETURN_FROM_STEP is None
                     or int(observation.get("step", 0))
                     < CLOSE_RETURN_FROM_STEP)
                and not tip_guard_high(observation, counts)):
            continue
        final = (act if travel == 0
                 else step_toward(positions[worker], cell, act))
        chosen[worker] = final
        booked_this_turn.append((worker, cell, list(act), travel))
        if NIGHT_TIP_GUARD is not None and act[0] == "DROP":
            load = sum(int(v) for v in
                       _inventory(observation, worker).values() if int(v) > 0)
            counts["tip_carried"] = counts.get(
                "tip_carried", counts.get("carried_total", 0)) - load
        if not ((DROP_SHARES_SHED and act[0] == "DROP")
                or (PICKUP_SHARES_SHED and act[0] == "PICKUP")):
            claimed.add(cell)
        claim(counts, act if building else final)
    actions = [chosen.get(worker, list(PASS))
               for worker in range(len(positions))]
    if STICKY_TARGET is not None:
        for worker, cell, act, travel in booked_this_turn:
            if travel > 0:
                _EN_ROUTE[(player_id, worker)] = (cell, act[0])
            else:
                _EN_ROUTE.pop((player_id, worker), None)
        for worker in range(len(positions)):
            if worker not in chosen:
                _EN_ROUTE.pop((player_id, worker), None)

    return {
        "farmer": actions[0] if actions else list(PASS),
        "hands": actions[1:],
        "market": market_orders(
            observation, day, counts, shed, seeds, money,
            len(farm.get("hands") or []),
        ),
    }


def agent(observation: dict[str, Any]) -> AgentAction:
    """Run the goose economy."""
    return decide(observation)
