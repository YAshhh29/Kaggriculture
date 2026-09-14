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
HAND_RAMP = ((0, 4), (6, 5), (8, 8), (11, 10), (14, 12))
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
LAND_DAYS = (1, 5)
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
WHEAT_TILES = 28
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
HERD_TARGET = 6
# A fixed herd, as {animal: head}, in place of the demand-weighted plan.
#
# The engine's own ledger, G against the plan most of the ladder copies,
# both facing the same opponent: the plan's six sheep sell 16,452 of wool
# against G's one sheep and 2,604, the single largest line in a 29,000
# gap. G's herd follows `demand x price`, which keeps landing on geese.
# None keeps the demand-weighted plan.
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
CROP_TILES = (("MELON", 12), ("CARROT", 16), ("STRAWBERRY", 8))
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
# Cap on the crew ramp. Twelve hands cost about 376 a day in fibonacci
# wages, some 10,500 across a season, against roughly 51,000 of gross
# production. Labour is the largest cost in this design, not the birds.
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
CROP_SEED_FLOOR = 1500.0
CROP_SEED_BATCH = 4
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
BAND_FERTILIZE = 1600.0     # 0 disables the job entirely

BAND_BUILD = 800.0
BAND_CROP = 600.0
# Assign every worker-job pair best-first, rather than letting each worker
# in turn take the best job left anywhere.
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
        gain = 0
        for ahead in (0, 1, 2):
            since = (day + ahead) - planted - int(spec["first"])
            if since >= 0 and since % interval == 0:
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
    for house in ("COOP", "PASTURE"):
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
        if empty < waiting + carried + lead:
            return house
    return None


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
        if int(observation.get("step", 0)) >= DROP_FROM_STEP:
            haul = 0.0
            for item, qty in inventory.items():
                if int(qty) > 0 and item in MARKET_PARAMS:
                    haul += int(qty) * price_at(
                        item, inventory_of(observation, item))
            if haul > 0:
                jobs.append((BAND_HARVEST + haul, ["DROP"]))
        carrying = int(inventory.get("WHEAT", 0))
        if (counts["unfed"] > 0 and carrying <= 0
                and counts.get("shed_WHEAT", int(shed.get("WHEAT", 0))) > 0):
            jobs.append((BAND_FEED * 0.9, ["PICKUP", "WHEAT", FEED_CARRY]))
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

    if tile is None:
        # Everything built here is worked from the shed for the rest of the
        # season, so near ground is worth more than far ground.
        near = 1.0 / (1.0 + COMPACT * min(
            abs(x - sx) + abs(y - sy) for sx, sy in shed_tiles()
        ))
        if (counts["wheat"] < wheat_target
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
            for crop, cap in CROP_TILES:
                spec = CROPS.get(crop)
                if spec is None or counts.get("crop_" + crop, 0) >= cap:
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
        if held <= 0 or len(orders) >= MAX_ORDERS:
            continue
        base = float(MARKET_PARAMS.get(item, {}).get("base", 1))
        want = base * SELL_TARGET.get(item, 0.8) * SELL_PATIENCE * slack
        now = price_at(item, inventory_of(observation, item))
        # Sell when the price is worth taking, when the season is closing,
        # or when the shed is near its hundred-unit cap and the overflow
        # would be discarded at the day boundary anyway.
        if now >= want or closing or total_shed >= 85:
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
    if hour == 2 and budget > CROP_SEED_FLOOR and day <= LAST_DAY - SOW_UNTIL:
        for crop, cap in CROP_TILES:
            if len(orders) >= MAX_ORDERS:
                break
            if (counts.get("crop_" + crop, 0) < cap
                    and int(seeds.get(crop, 0)) < CROP_SEED_BATCH):
                orders.append(["BUY_SEED", crop, CROP_SEED_BATCH])

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
                if not _owned(tiles, x, y):
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
                    score = value / (travel + 1.0) ** TRAVEL_EXPONENT
                    if not in_zone:
                        score *= ZONE_TAX
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
    for _score, worker, cell, act, travel in candidates:
        if worker in chosen or cell in claimed:
            continue
        # Scores were computed before any of this turn's jobs were handed
        # out, so a job that needed the last seed or the last empty pen
        # may no longer be possible by the time it is reached.
        if travel == 0 and not still_possible(counts, act):
            continue
        final = (act if travel == 0
                 else step_toward(positions[worker], cell, act))
        chosen[worker] = final
        claimed.add(cell)
        claim(counts, final)
    actions = [chosen.get(worker, list(PASS))
               for worker in range(len(positions))]

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
