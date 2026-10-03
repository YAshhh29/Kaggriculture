# Top-200 ladder study (Kaggriculture)

Sample at time of writing: **347 games, 69 teams, leaderboard ranks 1-69**, 694 player
sides. The corpus was still downloading when I stopped; the target band 150-200 had not
landed, so the "rank gradient" section uses ranks 1-10 vs 46-70 and says so. Every table
regenerates from the cached tapes in a few minutes once the download finishes.

## Method

Every tape is **re-run exactly in the engine**, not merely read. Each file carries
`seed`, `configuration` and *both* players' tapes, so setting `env.info["seed"]` and
driving `interpreter()` with tape entry `step+1` reproduces the recorded final money
**bit-exact** (verified: 88625/89660, 102389/101597, 145162/157574, 108138/110881 — all
exact). `_commit_unit`, `_do_hire` and `_do_buy_land` are monkey-patched to log what the
engine actually did, so every quantity below is a *committed* transaction. Blanket
`SELL x 3`-every-turn spam (which several agents emit) is therefore never counted as a
sale unless stock really left the shed.

Two comparisons are used, and they answer different questions:

- **Within-game (winner vs loser), N=347.** Perfectly controlled: same seed, same town,
  same market, same 720 steps. This is the strongest design available and most numbers
  below come from it.
- **Within-team (a team's wins vs its own losses), 54 teams.** Controls for policy.
  Used to show that these agents barely change between wins and losses.

Pooled won-vs-lost is *not* used: the corpus is balanced 3 wins/3 losses per team by
construction, so both pools contain the same policies and the comparison is null by
design (it shows median final money *higher* in losses).

---

## Theses

1. **Games at the top are coin-flips: 73% are decided by less than 5% of the pot**
   (median margin **$2,395, i.e. 2.3%**, on a ~$100k bank). Anything that moves 2-3% of
   revenue decides matches. (N=347 games.)
2. **The leaderboard is a monoculture of forked agents.** **52 of 69 teams (75%)** commit
   an *identical* day-0 basket: 7 WHEAT seed, 12 MELON seed, 2 COW, 2 SHEEP. Four opening
   families cover every team in the corpus: this one (52), bespoke agents (14), the
   top-10 fork (7) and a wheat-heavy fork (5). (69 teams.)
3. **The most widely run agent is the worst of the four families, and the top-10 runs a
   different one.**
   The "MELON6" family (9-10 wheat seed, 6 melon seed, 2 cow, **3 sheep**; ranks
   1,2,5,6,9,10,19 — only 7 teams) goes **39-31 (56%)** and takes a mean margin of
   **+$3,522** against every family other than itself. The 52-team "MELON12" fork goes
   250-265 (49%) and is **-$2,714** against every family other than itself. The most
   widely run agent on the ladder is the worst of the four. (N=347, both sides.)
4. **The clearest single marker of rank is what a team does with animal manure: apply it
   or sell it.** FERTILIZE actions fall monotonically 164 → 159 → 117 → 117 across rank
   bands 1-10 / 11-25 / 26-45 / 46-70, while fertilizer *units sold* rises monotonically
   211 → 247 → 339 → 342. Winners also apply more than losers within the same game
   (**187-111, p=0.00001**). (N=347.)
5. **Selling fertilizer is close to the worst trade in the game and low ranks do it most.**
   FERTILIZER is excluded from every shop *and* from `TOWN_CENTER_PRODUCTS`, so nothing
   ever consumes it: its price decays monotonically $100 → $74 (d10) → $50 (d16) → **$24
   (d28)** and never recovers. Applied to a watered plant it instead doubles that day's
   yield gain for 3 days. (Price trajectory n=24 games; engine `_town_consume`.)
6. **TOMATO is the sharpest strategic discriminator.** Winners hold more tomato tiles
   **110-56 (p=0.00003)**. Median tomato revenue is $4,103 for ranks 1-10, $3,295 for
   ranks 11-25 and **exactly $0 for ranks 26-70** — the big shared fork never plants it.
   Tomato's price *rises* all game ($60 → $74) because only 2 of 8 shop types buy it while
   half the field ignores it. (N=347.)
7. **WOOL is a trap and low-ranked teams walk into it.** Wool collapses from $206 to
   **$34 by day 14 and $1-5 from day 16 onward** (`above_func: sq`, T=105). Sheep tiles
   held jump from **3.00 (ranks 1-10) to 5.38 for every band below it**, while cow tiles
   fall 8.04 → ~7.3. Per dollar over a season a sheep returns roughly 1.7x and a cow 2.5x.
   (N=347; price trajectory n=24.) Caveat: the within-game sheep test is null, so this is
   a rank marker, not a proven cause.
8. **The market is shared, so selling a collapsing good is a race, and winners win it.**
   Winners realize a significantly higher average price than their own opponent on exactly
   the three goods that crash: WOOL 140-76 (p<0.0001), MILK 131-85 (p=0.0017),
   STRAWBERRY 132-84 (p=0.0011). On the stable goods (WHEAT, EGG, MELON, TOMATO) there is
   no difference at all. (Price race measured at N=216; at N=347 the revenue versions hold:
   STRAWBERRY 211-135 p=0.00004, WOOL 209-137 p=0.00011.)
9. **Only about 11% of sides ever buy the third quadrant at $4,000.** The first
   ($1,000) is bought on day 6 by 100% of sides (p10 5, p90 6) and the second ($2,000) on
   day 9-11; ~25 tiles stay locked for the whole game. Top-10 teams buy the second
   quadrant on **day 9**, ranks 26-70 on **day 11**. (694 sides.)
10. **Labour is free and everyone maxes it out at ~11 hands/day.** The fibonacci hire
    price means the first 11 hires of a day cost $232 in total, and hands are wiped every
    night, so the whole field re-hires daily: 5 on day 0 ramping to a plateau of 11 from
    day 10. Median ~280 hires per game, falling with rank: 285 (ranks 1-10), 282, 268,
    **268** (ranks 46-70).
11. **Roughly half of all unit-turns are spent walking.** Op mix over 432 sides: WATER
    16.1%, moves 43.3% (NORTH 13.5 + WEST 12.7 + EAST 9.0 + SOUTH 8.1), PASS 7.2%,
    HARVEST 6.8%, COLLECT_FERTILIZER 5.3%, CARE 4.7%, FEED 4.6%, PLANT 3.5%. Ranks 1-10
    idle least (PASS 4%) and water most (1,236 vs ~1,050 waters).
12. **Revenue is back-loaded and the leader at day 24 almost always wins.** Median
    cumulative revenue is only 19% by day 10 and 62% by day 20; the last ten days carry
    ~45%. The player ahead on cash at day 24 wins **263 of 347 games (76%)**, versus a
    coin-flip at day 6 (133-136) and near-one at day 14 (145-128).
13. **The crop calendar is a three-act play, identical across the whole top of the
    ladder**: MELON days 0-11 (12 tiles, one big harvest), STRAWBERRY days 4-26 (peaks at
    32-33 tiles, the largest single revenue block at $17.2k in days 16-21), then WHEAT and
    CARROT as endgame filler (28 wheat tiles on day 24, 19 carrot tiles on day 26) sold
    into the final liquidation.

---

## Won vs lost

### The honest headline: these agents do not change between wins and losses

Within-team paired deltas (mean over that team's wins minus mean over its losses), all
**54 teams** that have both a win and a loss in the corpus:

| feature | median paired delta | teams: delta>0 / delta<0 / **exactly 0** |
|---|---|---|
| **first land purchase day** | 0.00 | 0 / 0 / **54 of 54** |
| **first sowing day** | 0.00 | 0 / 0 / **54 of 54** |
| day-0-2 hires | 0.00 | 1 / 1 / **52 of 54** |
| animals bought | 0.00 | 22 / 13 / 19 |
| total hires | -0.67 | 20 / 30 / 4 |
| **opponent Elo** | **-34.9** | 11 / **43** / 0 |
| margin | +$7,797 | 54 / 0 / 0 |

Read the top two rows carefully: for **every single one of the 54 teams**, the day it
bought its first quadrant and the day it put its first seed in the ground were *identical*
on average in its wins and in its losses. These are not agents that adapt their opening
and sometimes get it wrong — they play one scripted opening every time. The most reliable
difference between a top team's win and its loss is that it faced a *weaker* opponent
(43 of 54 teams).

### The controlled comparison: winner vs loser inside the same game (N=347)

Same seed, same town, same market, same opponent, same 720 steps. `p` is a two-sided
sign test on the paired differences. Starred rows were re-measured at N=347; the
unstarred rows are from the N=274 pass and were all null there.

| feature | winner | loser | median delta | w>l | l>w | p |
|---|---|---|---|---|---|---|
| **money at day 24** | 74,324 | 71,543 | **+1,544** | **263** | 83 | **<0.0001 \*\*\*** |
| total revenue | 133,865 | 130,154 | +3,155 | 209 | 64 | <0.0001 *** |
| revenue days 20-29 | 57,022 | 55,915 | +1,856 | 185 | 88 | <0.0001 *** |
| **STRAWBERRY revenue** | 29,570 | 29,115 | +327 | 211 | 135 | **0.00004 \*\*\*** |
| **TOMATO revenue** | — | — | — | **104** | 59 | **0.0004 \*\*\*** |
| **FERTILIZE actions** | 129 | 121 | **+3** | 187 | 111 | **0.00001 \*\*\*** |
| **TOMATO tiles held** | — | — | — | 110 | 56 | **0.00003 \*\*\*** |
| WOOL revenue | 12,854 | 12,992 | +165 | 209 | 137 | 0.0001 *** |
| **WHEAT tiles held** | 19.90 | 20.25 | — | 106 | **160** | **0.0009 \*\*\*** |
| MILK revenue | 15,918 | 16,160 | +109 | 154 | 119 | 0.0341 ** |
| revenue days 0-9 | 13,300 | 13,166 | +121 | 146 | 127 | 0.25 |
| money at day 14 | 23,012 | 23,150 | +120 | 145 | 128 | 0.30 |
| fertilizer units sold | 326 | 330 | 0 | 157 | 173 | 0.38 |
| FERTILIZER revenue | 14,455 | 14,746 | -36 | 133 | 140 | 0.67 |
| PASS share | 0.08 | 0.08 | 0 | 137 | 133 | 0.81 |
| HARVEST actions | 480 | 479 | 0 | 127 | 124 | 0.85 |
| money at day 6 | 1,053 | 1,056 | 0 | 133 | 136 | 0.85 |
| total hires | 278 | 280 | 0 | 117 | 109 | 0.59 |
| WATER actions | 1,101 | 1,101 | 0 | 113 | 122 | 0.56 |
| sheep tiles | 5.38 | 5.38 | 0 | 106 | 105 | 0.95 |
| 2nd land day | 11 | 11 | 0 | 48 | 55 | 0.49 |

(TOMATO medians are both $0 / 0 tiles because most sides never plant it; the sign test
counts only the games where the two sides differed.)

**Read this table as four findings:**

1. *Openings, hiring, land timing, watering and harvesting are completely null.* Every
   opening lever the brief asked about — day-0-2 hires, land day, first sowing, total
   hires, waters, harvests — is dead flat between winners and losers (all p>0.45). The
   opening is solved and everyone plays the same one.
2. *The live levers are the manure fork and the tomato tiles.* Winners **apply** more
   fertilizer to plants (187-111, p=0.00001) and grow tomato (110-56, p=0.00003); losers
   put that tile into wheat instead (160-106 more wheat tiles, p=0.0009). Note that
   "winners *sell* less fertilizer" was significant at N=216 but **went null as the sample
   grew** (157-173 at N=347) — the applying is the finding, not the withholding.
3. *The margin is taken on the goods whose price moves.* STRAWBERRY (211-135), WOOL
   (209-137) and MILK (154-119) all separate, and all three are goods that crash; tomato
   separates because its price climbs all game and three quarters of the field ignores
   it.
4. *The lead is built late and held.* Day 6 cash is a coin-flip (133-136) and day 14 is
   nearly one (145-128); **day 24 cash predicts 263 of 347 results (76%)**, and the day
   20-29 revenue block separates 185-88.

### The sell race on collapsing goods (N=216 subset)

Because both players sell into one shared inventory, whoever unloads a crashing good
first gets the money. Realized average price per unit, winner vs their own opponent:

| good | winner $/u | loser $/u | w>l | l>w | p | base | what the price does |
|---|---|---|---|---|---|---|---|
| **WOOL** | 106.4 | 103.4 | **140** | 76 | **<0.0001 \*\*\*** | 200 | 206 → $34 (d14) → **$1-5** (d16+) |
| **MILK** | 85.6 | 82.7 | **131** | 85 | **0.0017 \*\*\*** | 160 | 187 (d6) → $42 (d18) |
| **STRAWBERRY** | 125.7 | 123.9 | **132** | 84 | **0.0011 \*\*\*** | 120 | 128 → **212 (d14)** → 124 (d22) → 158 |
| WHEAT | 37.9 | 38.1 | 104 | 112 | 0.59 | 25 | rises to 40-42, then flat |
| CARROT | 48.7 | 47.7 | 104 | 89 | 0.28 | 35 | rises steadily to **51** |
| TOMATO | 77.0 | 76.8 | 36 | 39 | 0.73 | 60 | rises steadily to **74** |
| MELON | 198.2 | 198.2 | 68 | 81 | 0.29 | 250 | 268 (d6) → **99-130** from d12 |
| EGG | 51.3 | 51.2 | 71 | 73 | 0.87 | 50 | **flat $46-52 all game** |
| FERTILIZER | 49.5 | 48.1 | 119 | 97 | 0.13 | 100 | monotone 100 → **24** |

The three significant rows are exactly the three goods whose price collapses. On goods
whose price is stable or rising, timing does not matter and the test is null. This is the
mechanism behind finding 3 above: the shared market means a collapsing good is a race, and
the loser of that race sells wool at $5 that the winner sold at $200.

### Won vs lost, summarised in one sentence

Two near-identical agents play the same solved opening; the one that (a) spends its
manure on plants instead of dumping it, (b) keeps a few tomato tiles the other turns into
wheat, and (c) reaches the market first on wool, milk and strawberry, is ~$1.5-3k ahead by
day 24 and wins ~76% of the time from there.

---

## Rank gradient

**Caveat: the corpus had only reached rank 69 when I stopped, so this is ranks 1-10 vs
46-70, not vs 150-200.** The bands are narrower than asked for, but several rows are
cleanly monotone across all four, which is stronger evidence than any single pairwise gap.

Median over source-team sides (n = 53 / 76 / 100 / 118):

| feature | rank 1-10 | 11-25 | 26-45 | 46-70 | monotone? |
|---|---|---|---|---|---|
| final money | **105,578** | 98,346 | 98,817 | 94,765 | mostly |
| **FERTILIZE actions** | **164** | 159 | 117 | **117** | **yes** |
| **fertilizer units sold** | **211** | 247 | 339 | **342** | **yes** |
| **TOMATO tiles held** | **3.88** | 3.10 | **0.00** | **0.00** | **yes** |
| TOMATO revenue | **4,103** | 3,295 | 0 | 0 | **yes** |
| total hires | **285** | 282 | 268 | **268** | **yes** |
| **2nd quadrant day** | **9** | 10.5 | 11 | 11 | **yes** |
| **sheep tiles** | **3.00** | 5.38 | 5.38 | 5.38 | step |
| cow tiles | **8.04** | 7.31 | 7.23 | 7.75 | mostly |
| STRAWBERRY revenue | **32,879** | 29,597 | 30,192 | 25,244 | mostly |
| WATER actions | **1,236** | 1,063 | 1,102 | 1,104 | step |
| PASS share | **0.04** | 0.09 | 0.07 | 0.07 | step |

The top-10 band is separated from everything below it on six axes at once: it applies
40% more manure, sells 40% less of it, is the only band that grows tomato at all, hires
6% more hands, buys its second quadrant two days earlier, and idles half as much.

### What rank 1-10 does that rank 46-70 does not

1. Applies manure to plants (164 vs 117 FERTILIZE) instead of selling it (211 vs 342
   units) into a price that decays to $24.
2. Grows tomato at all (3.9 tiles, $4.1k) — the lower band grows literally none.
3. Prefers cows to sheep (8.0 / 3.0) where every lower band sits at 5.4 sheep, despite
   wool being worth $1-5 after day 16.
4. Buys the second quadrant two days earlier (day 9 vs day 11) — and this row is now
   monotone across all four bands (9 / 10.5 / 11 / 11).
5. Works harder: 285 hires, 1,236 waters, 4% PASS vs 268 hires, 1,104 waters, 7% PASS.

### Family head-to-head (the cleanest version of the gradient)

Classifying every side by its day-0 committed basket, then scoring every game from both
sides (N=274 games, 548 sides):

| family | teams | day-0 signature | overall (N=347) | mean margin vs the other families |
|---|---|---|---|---|
| **MELON6** ranks 1,2,5,6,9,10,19 | **7** | 9-10 wheat seed, 6 melon, 2 cow, **3 sheep** | **39-31 (56%)** | **+$3,522** |
| OTHER (bespoke) ranks 7,13,16,24,35,46,49,53... | 14 | assorted | 38-32 (54%) | -$1,902 |
| WHEATY ranks 8,12,22,25,52 | 5 | 18-19 wheat seed, 0-1 melon, 3-5 cow, 1-3 sheep | 20-19 (51%) | -$1,284 |
| **MELON12** ranks 3,4,11,14-21,23,26-69 | **52** | 7 wheat seed, **12 melon**, 2 cow, 2 sheep | 250-265 (49%) | **-$2,714** |

Pairwise records and margins, measured on the first 274 games (ranks 1-54):

| | vs MELON6 | vs MELON12 | vs WHEATY | vs OTHER |
|---|---|---|---|---|
| **MELON6** | 14-14 | 10-13 (**+$963**) | **6-1** (+$3,736) | **7-3** (+$3,372) |
| MELON12 | 13-10 (-$963) | 150-150 | 9-12 (-$4,649) | **13-23** (-$2,651) |
| WHEATY | 1-6 | **12-9** (+$4,649) | — | 6-4 (+$432) |
| OTHER | 3-7 | **23-13** (+$2,651) | 4-6 (-$432) | 3-3 |

Mean margin, row family minus column family ($):

| | MELON6 | MELON12 | WHEATY | OTHER |
|---|---|---|---|---|
| **MELON6** | 0 | **+963** | **+3,736** | **+3,372** |
| MELON12 | -963 | 0 | **-4,649** | **-2,651** |
| WHEATY | -3,736 | +4,649 | 0 | +432 |
| OTHER | -3,372 | +2,651 | -432 | 0 |

MELON6 beats everything. MELON12 — the fork **52 of 69 teams** are running — is negative
on margin against every other family and dead even against itself. Its 49% record is held
up almost entirely by playing itself: at N=274, stripping out MELON12-vs-MELON12 leaves it
**35-45**. This is the central structural fact about the current ladder: three quarters of
the top teams are running the same losing fork against each other, which is why so many
games are within 2% and why rank inside that block is close to noise. Where the two forks differ:

| | MELON6 | MELON12 |
|---|---|---|
| tomato revenue | $4,270 | **$0** |
| FERTILIZE actions | 158 | **119** |
| fertilizer revenue | $11,598 | **$15,116** |
| sheep tiles (d10-29) | 3.5 | **6.0** |
| strawberry revenue | $32,693 | $27,750 |
| PASS share | **1.0%** | **7.6%** |
| total hires | 286 | 271 |
| 2nd quadrant day | 9 | 11 |

Note the melon seeds themselves are a red herring: both forks reach **12 melon tiles**.
MELON6 just buys 6 on day 0 and the rest on days 1-2, keeping $480 of day-0 cash free.
Both sell ~72 melons for ~$198/unit. MELON12 dumps all 72 by day 11; MELON6 spreads them
days 10-15. That difference is worth almost nothing ($198.4 vs $198.2 realized) — the
real gap between the forks is tomato, manure and sheep.

---

## Tables

### The opening, days 0-4 (medians over 432 sides, committed only)

| day | hires | WHEAT seed | MELON seed | STRAW seed | COW | SHEEP | GOOSE | WHEAT bought |
|---|---|---|---|---|---|---|---|---|
| 0 | 5 | 7 | 8 | 0 | 2 | 2 | 0 | 9 |
| 1 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| 2 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| 3 | 5 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 4 | 6 | 1 | 0 | 2 | 0 | 0 | 0 | 6 |

Day 0 spends essentially the entire $3,000 stake: ~$640 melon seed, ~$70 wheat seed,
$800 of cow, $1,000 of sheep, ~$250 of wheat to feed them, ~$12 of hires.

First-action days (median; "never" counted over 432 sides):

| action | median day | never |
|---|---|---|
| plant WHEAT | 0 | 0 |
| plant MELON | 0 | 0 |
| plant STRAWBERRY | 4 | 0 |
| plant TOMATO | 14 | **56 / 208 sides skip it entirely** |
| plant CARROT | 19 | 17 |
| buy COW | 0 | 0 |
| buy SHEEP | 0 | 0 |
| buy GOOSE | 9 | 45 |

### The exact first 26 steps of rank 1 (Majkel1337, ep 109983899)

```
d0 h0   market: BUY_ANIMAL COW 1, BUY_PRODUCT WHEAT 5
d0 h1   PICKUP COW           market: SELL WHEAT 1, HIRE x4, BUY_ANIMAL COW 1, BUY_ANIMAL SHEEP 3
d0 h2   BUILD_PASTURE        market: SELL WHEAT 1
d0 h3   PLACE COW            market: BUY_SEED MELON 2
d0 h4   PICKUP WHEAT 3       market: BUY_PRODUCT WHEAT 1
d0 h5   FEED                 market: BUY_SEED MELON 2, BUY_PRODUCT WHEAT 1
d0 h6   CARE                 market: BUY_PRODUCT WHEAT 1
d0 h7-13  WEST/FEED/CARE alternating   market: BUY_SEED MELON 2, BUY_SEED WHEAT 2
d0 h14  WEST                 market: SELL WHEAT 1, BUY_SEED WHEAT 1
d0 h15  WATER
d0 h16  NORTH                market: SELL WHEAT 1, BUY_SEED WHEAT 1
d0 h17  PLANT WHEAT          market: BUY_SEED WHEAT 1
d0 h18  WATER                market: BUY_SEED WHEAT 1
d0 h19  NORTH                market: BUY_SEED WHEAT 1
d0 h20  PLANT WHEAT          market: BUY_SEED WHEAT 1
d0 h21  WATER                market: BUY_SEED WHEAT 1
d1 h0   COLLECT_FERTILIZER   market: HIRE x5
d1 h1   PLACE FERTILIZER 1
```

The shape: animals and their feed *first* (before any planting), pasture built by hour 2,
cow placed and fed by hour 5, seed bought in dribs of 1-2 through the day, wheat planted
from hour 17, and the very first action of day 1 is collecting manure. Rank 2 (DSM) is
the same tape step-for-step with a blanket `SELL <everything> 3` tail appended to every
turn — it is a fork of rank 1.

### Labour: op mix over 432 sides

| op | share | | op | share |
|---|---|---|---|---|
| WATER | 16.1% | | PLANT | 3.5% |
| NORTH | 13.5% | | PICKUP | 3.2% |
| WEST | 12.7% | | FERTILIZE | 2.2% |
| EAST | 9.0% | | PLACE | 1.4% |
| SOUTH | 8.1% | | DROP | 0.9% |
| PASS | 7.2% | | DIG | 0.5% |
| HARVEST | 6.8% | | BUILD_PASTURE | 0.2% |
| COLLECT_FERTILIZER | 5.3% | | BUILD_COOP | 0.1% |
| CARE | 4.7% | | **moves total** | **43.3%** |
| FEED | 4.6% | | **work total** | **49.5%** |

NORTH+WEST (26.2%) far exceed SOUTH+EAST (17.1%): hands spawn on the four shed tiles at
board centre and the farm grows into NW first, then NE and SW.

Hires and live hands per day (median):

| day | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 16 | 20 | 24 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hires | 5 | 6 | 6 | 8 | 9 | 11 | 11 | 11 | 11 | 11 | 10 |

The plateau at 11 is where the fibonacci price bites: hires 1-11 cost
1+1+2+3+5+8+13+21+34+55+89 = $232/day; the 12th alone costs $144 and the 13th $233.

### Tiles held, by day (median over 432 sides)

| tile | d0 | d2 | d4 | d6 | d8 | d10 | d12 | d14 | d16 | d18 | d20 | d22 | d24 | d26 | d28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WHEAT | 7 | 7 | 2 | 5 | 5 | 14 | 22 | 20 | 18 | 15 | 17 | 23 | **28** | 22 | 15 |
| MELON | 8 | 12 | 12 | 12 | 12 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| STRAWBERRY | 0 | 0 | 3 | 13 | 20 | 20 | 32 | **33** | 33 | 32 | 29 | 19 | 11 | 7 | 1 |
| TOMATO | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 7 | 7 | 7 | 6 | 3 | 2 |
| CARROT | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 8 | **19** | 12 |
| COW | 2 | 3 | 4 | 6 | 7 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
| SHEEP | 2 | 2 | 2 | 3 | 4 | 4 | 4 | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 2 |
| GOOSE | 0 | 0 | 0 | 0 | 0 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| WEED | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| LOCKED | 75 | 75 | 75 | 50 | 50 | 25 | 25 | 25 | 25 | 25 | 25 | 25 | 25 | 25 | 25 |

Weeds are a non-issue at this level (median 0.25-0.5 tiles): `weedSpawnChance` is 0.005
per empty tile per night and these boards have almost no empty tiles.

### Market price at end of day (median, n=24 games replayed with price logging)

| good | base | d0 | d4 | d8 | d10 | d12 | d14 | d16 | d18 | d20 | d24 | d28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WHEAT | 25 | 28 | 31 | 36 | 40 | 40 | 41 | 40 | 40 | 41 | 42 | 39 |
| CARROT | 35 | 35 | 35 | 38 | 40 | 41 | 42 | 43 | 46 | 48 | **51** | 48 |
| TOMATO | 60 | 60 | 61 | 61 | 63 | 64 | 66 | 68 | 69 | 71 | **74** | 74 |
| STRAWBERRY | 120 | 128 | 155 | 176 | 188 | 200 | **212** | 207 | 183 | 158 | 124 | 158 |
| MELON | 250 | 256 | 266 | 270 | 188 | 130 | 118 | 102 | 99 | 99 | 94 | 104 |
| EGG | 50 | 50 | 50 | 51 | 51 | 52 | 51 | 50 | 46 | 45 | 46 | 48 |
| MILK | 160 | 169 | 179 | 154 | 142 | 142 | 108 | 62 | **42** | 50 | 56 | 62 |
| WOOL | 200 | 206 | 215 | 179 | 138 | 88 | 34 | **5** | 5 | 5 | **1** | 8 |
| FERTILIZER | 100 | 100 | 92 | 81 | 74 | 64 | 55 | 50 | 44 | 40 | 29 | **24** |

Why these shapes — from `SHOPS` and `_town_consume`. Counting how many units each shop
type removes per tick, weighted by the uniform draw over 8 shop types:

| good | town pull per shop-instance | shops carrying it |
|---|---|---|
| WHEAT | 0.625 | BAKERY, PIZZA, BRUNCH, ICE_CREAM, FARMERS_MARKET |
| STRAWBERRY | 0.500 | BRUNCH, ICE_CREAM, SMOOTHIE, FARMERS_MARKET |
| MILK | 0.375 | PIZZA, ICE_CREAM, SMOOTHIE |
| CARROT | 0.375 | PET_CAFE (x2), FARMERS_MARKET |
| EGG | 0.250 | BAKERY, BRUNCH |
| TOMATO | 0.250 | PIZZA, FARMERS_MARKET |
| WOOL | 0.250 | YARN_STORE (x2) |
| **MELON** | **0** | none — town-centre demand only (1 per 24 steps) |
| **FERTILIZER** | **0** | none, **and excluded from `TOWN_CENTER_PRODUCTS`** |

All 24 replayed games reached the full 8 shop instances (unlock every 3 days, capped at
`MAX_SHOP_INSTANCES = 8`), so town demand is saturated from day 24 in every game.

### Revenue by good by day block (median $, 432 sides)

| good | d0-5 | d6-10 | d11-15 | d16-20 | d21-25 | d26-29 |
|---|---|---|---|---|---|---|
| WHEAT | 588 | 552 | 1,866 | 2,286 | 3,377 | **6,293** |
| CARROT | 0 | 0 | 0 | 0 | 272 | **4,278** |
| TOMATO | 0 | 0 | 0 | 0 | 596 | 1,812 |
| STRAWBERRY | 0 | 0 | 1,725 | **17,230** | 6,305 | 3,180 |
| MELON | 0 | **10,272** | 2,387 | 0 | 0 | 0 |
| EGG | 0 | 0 | 604 | 1,232 | 1,258 | 1,074 |
| MILK | 0 | 3,426 | **5,367** | 3,899 | 1,554 | 1,964 |
| WOOL | 0 | **4,328** | 1,266 | 508 | 1,048 | 928 |
| FERTILIZER | 2,372 | 3,577 | 3,577 | 1,767 | 1,044 | 612 |

Fertilizer is the *first* income in the game (days 0-5) — animals produce it from their
first night. Cumulative revenue share: 5% by day 6, 19% by day 10, 31% by day 14, 53% by
day 18, 76% by day 24, 93% by day 28.

### Land

| quadrant | price | sides that buy it | median day | p10 | p90 |
|---|---|---|---|---|---|
| NE | $1,000 | **548 / 548 (100%)** | 6 | 5 | 6 |
| SW | $2,000 | **548 / 548 (100%)** | 9-11 | 8 | 11 |
| SE | $4,000 | **60 / 548 (11%)** | 13.5 | 12 | 18 |

Buying it *faster* does not correlate with winning within a game (land day delta:
41-48, p=0.46), but the top-10 band buys the second quadrant on day 9 while ranks 11-54
buy on day 11. Buying the third looks like a mistake: in the 22 games where exactly one
side bought it, that side **won 9 and lost 13**. (Weak — p=0.40 — but it is the only
direct evidence available, and it points away from the $4,000 purchase.)

---

## Disagreements

Where strong teams genuinely differ:

1. **Melon load.** 19 teams buy 12 melon seeds on day 0; the top family buys 6 and fills
   in over days 1-2; Ebi (rank 12) buys **zero melon** and 19 wheat seed; ymg_aq (8) and
   HowardLeeTW (22) buy 1 melon, 18 wheat seed, 3-5 cows. All four styles sit in the top
   25, so melon is not load-bearing — but the heavy-melon fork is the weakest of them.
2. **Sheep or not.** lingxiaojun (24) buys **0 cows and 4 sheep**; HowardLeeTW buys 5 cows
   and 1 sheep. The evidence favours cows, but both are on the board.
3. **Geese.** 45 of 208 sides never buy a goose at all; the rest buy around day 9 and keep
   ~2-3. Egg is the only perfectly stable price in the game ($46-52 all season), so this
   is a real unresolved disagreement — geese are safe but low-ceiling.
4. **Blanket sell orders.** DSM (rank 2) appends `SELL <every good> 3` to every single
   turn, burning most of its 10-order budget on no-ops; Majkel1337 (rank 1) runs the
   identical tape without them. Both are top-2, so the spam is roughly free — but it does
   cap how many real orders can be issued in a turn.
5. **Wheat buying.** Median 170 wheat bought from market per game, but "feel the agi"
   (rank 15) commits **204 wheat purchases on day 0 alone** and Mengfei Li (18) 124, versus
   3-9 for the rank 1-2 family. Wheat buying has no measurable effect on the result
   (61-67, p=0.60).
6. **Endgame carrot.** Top-10 teams get $6,737 from carrot; ranks 11-20 get $4,345. Not
   everyone runs the day-25 carrot filler even though carrot's price is at its season high
   ($51) exactly then.

---

## Confidence

**Solid.**
- The replay is bit-exact against recorded rewards, so every committed quantity (sales,
  revenue, hires, land, tiles) is engine ground truth rather than requested orders.
- The within-game winner/loser design (N=216) controls seed, town, market and opponent
  perfectly. The findings at p<0.01 — day-24 lead (173-43), FERTILIZE actions (128-72),
  tomato (91-52 and 86-50), and the realized-price race on WOOL/MILK/STRAWBERRY
  (140-76, 131-85, 132-84) — are the most trustworthy results here.
- The price trajectories and the shop-demand table are derived from the engine source and
  confirmed on 24 replayed games; the wool and fertilizer collapses are not marginal
  effects, they are 40x and 4x price moves.
- The mirror-family classification is mechanical (exact day-0 committed basket) and the
  head-to-head counts are large (107-107 within MELON12 alone).

**Thin.**
- **The rank gradient does not reach the requested band.** The corpus was at rank 69 when
  I stopped. "Rank 1-10 vs 46-70" is a much narrower contrast than "1-20 vs 150-200", and
  the absolute-money column wobbles (98,346 / 98,817 / 94,765 across the lower three
  bands). The *monotone* rows — FERTILIZE, fertilizer sold, tomato, hires, 2nd-quadrant
  day — are the ones I would still bet on. Almost all of the gradient's signal is the
  top-10 band separating from everything below it, not a smooth slope.
- MELON6's 37-31 record rests on 7 teams and 68 sides. The +$963 edge over MELON12 comes
  from 23 head-to-head games and is the weakest of its three margins; its +$3,736 over
  WHEATY rests on 7 games.
- The fertilizer thesis is correlational. "Winners apply more" is solid (149-96,
  p=0.0007) and the rank gradient is monotone, but "winners sell less" **weakened to null
  at the larger sample** (fertilizer units sold: 129-134, p=0.76) even though it was
  significant at N=216. Treat the *apply* half as the finding and the *sell* half as
  unresolved. I did **not** run a counterfactual removing an agent's FERTILIZE actions.
- "Sheep are a trap" leans on the price curve and the rank gradient; the within-game
  sheep-tile test is null (83-93, p=0.45), so sheep may simply be a *marker* of the weaker
  fork rather than a cause.

**Guesses, labelled as such.**
- *Guess:* tomato's value is that its price rises all game precisely because the dominant
  fork never plants it — it is an under-supplied good with steady 2-shop demand and a
  forgiving `sqrt` glut curve. If more of the field adopted tomato this edge would shrink.
- *Guess:* the reason MELON6 beats MELON12 is cash timing rather than melon count — buying
  6 melon seeds instead of 12 on day 0 frees ~$480 at the moment the bank is empty, which
  is what lets it reach the $2,000 second quadrant on day 9 instead of day 11.
- *Guess:* the 11-hand plateau is not an optimum anyone searched for; it is where the
  fibonacci curve happens to cross the marginal value of a hand, and a policy that hired
  15 hands on the 3-4 highest-value days only would beat it.

**What would settle it.**
1. Finish the download to rank 200 and re-run `extract.py` — every table here regenerates
   in a few minutes on `Pool(4)`, and it skips tapes already processed. The 150-200 band
   is the one contrast the brief asked for that this file cannot yet supply.
2. Counterfactual replays: take a top tape, rewrite every `FERTILIZE` to `PASS` (and
   separately, every fertilizer `SELL` to `FERTILIZE`) and re-run against the same
   opponent on the same seed. The engine is deterministic, so the dollar value of the
   manure fork is directly measurable. Same trick for deleting sheep purchases.
3. To test the tomato thesis, replay a MELON12 tape with its day-18 wheat plantings
   rewritten as tomato. Note that rewritten tapes drift once board state diverges, so
   only the first few days of any such edit are strictly trustworthy — treat these as
   directional, not exact.

*Scripts: `extract.py` (instrumented replay, `Pool(4)`) and `agg.py` (aggregation) in the
session scratchpad. Re-running `extract.py` picks up only tapes it has not already
processed.*
