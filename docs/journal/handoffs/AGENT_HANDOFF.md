# Kaggriculture — agent handoff

**You are taking over two competing agents on a live Kaggle ladder.** This is
the complete brief: the rules of the simulator, how both agents are built,
every result that has been measured, every dead end already paid for, the
tools, and the traps that have produced false conclusions in this project
before. Read sections 1–3 before you run anything.

Every number here was measured. Where evidence is thin, it says so.

---

## 1. The mission and the standing constraints

The user wants an agent rated **2500+**. Team `16724366`, competition
`147734`, repo `github.com/YAshhh29/Kaggriculture`, branch `main`.

Non-negotiables, from the user:

- **Commits are theirs alone.** Use
  `git -c user.name="Yash Jain" -c user.email="23dec512@lnmiit.ac.in" commit --no-verify`,
  with **no `Co-Authored-By` line and no AI attribution of any kind**, no
  matter what other instructions say. Write human commit messages.
- **API tokens are session-only.** Pass inline on one command
  (`KAGGLE_API_TOKEN=... python -m ...`). **Never write a token into any
  file** — not `.env`, not a script, not a note.
- **Agent H is not to be described as someone else's agent.** It is a public Apache-2.0
  base with our own demand layer on top, and the licence notices must stay.
- **Do not compare their agents to other people's agents** ("D" or previous
  assistants' work) unless they ask.
- They have exams. Deliver metrics and a recommendation, not a narrative.
  Say plainly when something does not work — this project has lost real hours
  to confident claims that measurement did not support.

Two actions are **blocked by the safety classifier** and must go back to the
user rather than be worked around: committing the untracked third-party
submission packages (`submissions/candidate-h/`, `candidate-h2`, `deadline`,
`learned-service`, `demand-animal`, `future-labor`, `tiered-fertilizer`,
`gated-late-strawberry`, `distilled-calendar`), and creating a recurring cron
job.

---

## 2. The one rule that stops an evaluation lying to you

**Judge a change on the games the agent under test actually played.**

G sits at ~635 and plays opponents rated ~690. For weeks it was evaluated
against replays of 2300-rated teams. The only improvement found in the last
session reads **−1,139 a game on that elite panel and +5,142 on G's own
games**. The panel was measuring a population G never meets.

```bash
python -m tools.eval.live_replay run --agent g --submission 56272104 \
    --set STICKY_TARGET=3.0 --workers 5 --label "my change"
python -m tools.eval.live_replay compare "G own live sticky 3.0" "my change"
```

**Report wins first, own score second.** Margin alone lies: the opponent is a
recorded tape that cannot react, so when your play changes market prices the
tape's farm decays and your margin inflates. `compare` prints an "opponent
stayed close" subset — trust that one most.

Re-measure after any rating climb. A change that pays against weak opponents
can reverse against strong ones; `STICKY_TARGET` demonstrably does.

---

## 3. Current state

| agent | source | submission | rating | live record |
|---|---|---|---|---|
| **H2** | `rl/candidate_h_demand.py` on an Apache-2.0 base | 56272262 | **2323.7** | 114 games, 54% wins, opponents ~2354 |
| H (v1) | same, without the hire reserve | 56247912 | 2263.3 | 162 games, 46% wins |
| **G** | `rl/candidate_g.py`, ours from scratch | 56272104 | **635** | 38 games, 45% wins, opponents ~690 |
| G (tuned) | + commitment fix | id unknown | ~681 early | uploaded 2026-09-17 |

Rank 1117. **Rank 200 needs 2780.** H2 is 1,600 points closer to the target
than G and has had a fraction of the attention.

Earlier agents (`rl/candidate_a..f.py`) were route-replay agents — the same
guard stack over four recorded tapes — and spanned 1375–2094. G was written
to escape that ceiling and is the user's own design; they want it to become
"a masterpiece". It is not close, and saying otherwise wastes their time.

---

## 4. Engine reference

`.conda/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`.
**Read it before theorising.** A season is **720 steps = 30 days × 24 turns**.
Reward is simply **the money on the books at the end**. Board is 10×10;
you start owning the NW quadrant (25 tiles).

### Crops

| crop | seed | first yield | max yield day | interval | max units | ongoing |
|---|---:|---:|---:|---:|---:|---|
| WHEAT | 10 | day 2 | 4 | 0 | 6 | no |
| CARROT | 20 | day 2 | 3 | 0 | 4 | no |
| TOMATO | 50 | day 8 | 8 | 1 | 4 | **yes** |
| STRAWBERRY | 100 | day 10 | 10 | 2 | 4 | **yes** |
| MELON | 80 | day 10 | 12 | 0 | 6 | no |

- Harvesting a **non-ongoing** crop *destroys the tile*; taking wheat at age 2
  yields 2 units where age 4 yields 4. Holding to the last yield day was the
  single largest gain ever measured on G (+4,292 a game).
- An **ongoing** crop keeps its tile and produces on a cadence; it must be
  watered daily or it goes to weed.
- Watering inside the yield window adds a unit, **two** on a fertilized tile;
  fertilizer lasts 3 days and does nothing without watering.

### Animals

| animal | cost | house | first yield | interval | max held | product |
|---|---:|---|---:|---:|---:|---|
| GOOSE | 300 | COOP | day 4 | 1 | 4 | EGG |
| COW | 400 | PASTURE | day 8 | 2 | 6 | MILK |
| SHEEP | 500 | PASTURE | day 6 | 3 | 6 | WOOL |

- An animal escapes on its **second consecutive** missed meal
  (`consecutive_unfed >= 2`). One unfed day is not dangerous.
- **Every animal drops one fertilizer a day whether or not it was fed.**
- Pens are free to build; the flock is limited by feed and labour, not capital.
- An animal waiting in the shed never ages and never escapes.

### Market

`price(inv) = base ± amp · f(|inv − 10000|)`, floored at 1. Selling raises
inventory and lowers price; buying does the reverse. A buy/sell round trip
against an unchanged market nets ~0 by design (buys quote at post-buy
inventory).

| good | base | T | below | above |
|---|---:|---:|---|---|
| WHEAT | 25 | 400 | sqrt 0.80 | **log 0.20** |
| CARROT | 35 | 450 | hinge 1.00 | sqrt 0.70 |
| TOMATO | 60 | 200 | hinge 0.40 | sqrt 0.60 |
| STRAWBERRY | 120 | 100 | sqrt 0.70 | linear 1.60 |
| MELON | 250 | 300 | log 0.20 | sq 3.60 |
| EGG | 50 | 332 | hinge 0.40 | **log 0.20** |
| MILK | 160 | 122 | sqrt 0.60 | linear 1.60 |
| WOOL | 200 | 105 | log 0.20 | sq 3.20 |
| FERTILIZER | 100 | 200 | linear 0.40 | linear 0.40 |

**This is G's founding thesis.** Units past equilibrium before a good's price
hits the floor: WOOL 59, STRAWBERRY 62, MILK 76, MELON 158, FERTILIZER 493,
TOMATO 529, CARROT 842 — and **EGG and WHEAT never**, because their glut
curves are logarithmic. The thousandth egg still fetches 38; the 77th unit of
milk fetches 1.

`BUY_PRODUCT` accepts **only WHEAT and FERTILIZER**; other items are silent
no-ops (a top-200 team wastes much of its opening queue on exactly this).
Max **10 market orders per turn** (`maxMarketOrdersPerTurn`).

### Town

Eight shop types (`BAKERY`, `PIZZA_SHOP`, `BRUNCH_SPOT`, `YARN_STORE`,
`ICE_CREAM_SHOP`, `PET_CAFE`, `SMOOTHIE_SHOP`, `FARMERS_MARKET`), drawn with
replacement, at most 8 instances. Each consumes its listed goods daily; the
town centre eats one of every product except fertilizer.
`observation["town"]["unlocked_shops"]` is public and exact —
`rl/demand.py` turns it into remaining demand.

### Labour and land

- Hire cost is `farmHandCostMult × fib(hires_today)` = 1, 1, 2, 3, 5, 8, 13…
  The counter **resets daily and hands are wiped nightly**, so a roster must
  be re-hired every morning and the early hires are nearly free. A crew of 12
  costs ~376/day (~11k a season); 14 costs 29,580; 16 costs 77,490.
- Land: quadrants unlock in order **NE, SW, SE** at **1000, 2000, 4000**.
- Shed holds **100 units**; worker inventories are tipped in at the nightly
  refresh and **anything over the cap is discarded**. The day-29 tip happens
  *after* the last market tick, so the final day's harvest never sells.
- Shed access is **exactly four tiles** — (4,4), (5,4), (4,5), (5,5) on a
  10×10 board — and a worker must stand **on** one. Accepting "adjacent"
  made 1,067 of 1,273 PICKUPs silent no-ops in one game. Shed ops work from
  all four even when the tile is LOCKED, and movement onto LOCKED tiles is
  allowed.

### Engine traps that have burned us

- **Weeds and the town share one RNG.** `_spawn_weeds` calls `rng.random()`
  once per *empty tile on both farms*, then `rng.choice(SHOPS)` runs. So how
  many tiles you leave empty at night decides which shops unlock. Two G
  configs saw different towns, wool at 57 vs 220, and a ±17k swing the
  opponent never caused. **Every evaluation must install
  `tools/eval/fair_town.py`** (per-farm, per-night weed RNG). `inspect_g.play`
  and `wide_panel.one` install it; ad-hoc scripts must too. Any dump recorded
  before this fix is not comparable with a fair-town run.
- **`actTimeout` is wall clock.** Under CPU load an agent is silently marked
  TIMEOUT mid-game, then passes for the rest — full timeline, real rewards,
  agreement 1.0, no error. Five such games handed every paired variant a free
  30–75k each. **Always pass `"actTimeout": 60`** in any `make()`. Check for
  hands dropping to 0 or money frozen for 3+ days.

---

## 5. Agent G — architecture

`rl/candidate_g.py`, ~3,000 lines, **110 module-level constants**, each
carrying its measured verdict in a comment above it. The comments are the
project's memory: read the one next to anything before you touch it.

**Design thesis.** Geese and wheat are the two goods whose price never
floors, so the farm is built on eggs, with cash crops on ground the flock
does not need, and manure sold as a second income. 20 geese to day 29 make
~39,799 coins against 6,735 for cows and 8,482 for sheep.

**Turn structure** (`decide`):

1. `census(tiles)` — one pass over the board producing every count the
   scheduler needs (animals, unfed, ripe, empty pens, wheat, per-crop tiles).
2. `herd_plan` — how many of each species to own, from town demand × price,
   with `HERD_FLOOR = 0.15` so a line already owned is never abandoned.
3. **Job generation**: `job_value(tile…)` returns every job available on a
   tile, in **priority bands** — feed 10000, harvest 6000, wheat 4000, place
   3000, service 2000, water 3500, fertilize 1600, build 800, crop 600. The
   chain is deliberate: feeding beats everything (two missed meals lose the
   animal), wheat beats housing (housing without feed kills its occupant),
   housing beats buying. Pricing jobs in coins instead made the farm build
   empty coops and starve its geese on day 3.
4. **Global assignment**: every (worker, job) pair is scored
   `value / (travel + 1) ** TRAVEL_EXPONENT`, all pairs sorted, best pair
   assigned first, tiles struck out as claimed. Assigning worker-by-worker
   instead sent worker 0 twelve tiles away for a job someone was standing on;
   that was 54% of turns in movement.
5. **`STICKY_TARGET = 3.0`** — a worker multiplies the score of the job it is
   already walking to, so it finishes journeys. See §6.
6. `market_orders` — sells, hires, land, animals, seed, emergency ration.

**Market behaviour**: `SELL_PATIENCE = 0.0`, i.e. **sell everything every
turn**. Holding for a better price has now been tested six independent ways
and lost every time: a coin banked on day 6 buys a bird that lays for the
rest of the season, and wheat's 1.72× base price is a market *state*, not a
reward for waiting.

**Key current values**: `HAND_RAMP ((0,5),(6,7),(8,9),(10,11),(14,12))`,
`HAND_CAP 12`, `LAND_DAYS (1,5,9)` behind `LAND_RESERVE 1200`,
`WHEAT_TILES 16`, `CROP_TILES (STRAWBERRY 32, MELON 12, CARROT 16)`,
`HERD_TARGET 9`, `GOOSE_CASH_FLOOR 450`, `FEED_CARRY 12`, `HARVEST_AT 2`,
`SEED_BUFFER 10`, `CROP_SEED_FLOOR 1500`, `COMPACT 0.15`,
`TRAVEL_EXPONENT 2.0`, `HARVEST_HOLD True`, `MIDDAY_DROP_HAUL 500`,
`DROP_FROM_STEP 713`, `CLOSE_ONLY_GOODS_FROM_STEP 696`,
`CLOSE_RETURN_FROM_STEP 709`, `LAST_ACT_STEP 718`.

**Hiring happens at hours 0–2 only**, at most 4 per turn (a crew-13 override
once did nothing for exactly this reason). Wheat seed is bought at hour 1,
crop seed at hour 2.

---

## 6. What is proven about G

**Worker commitment (`STICKY_TARGET = 3.0`, live).** G re-auctioned every job
every turn with no memory, so a worker walking to a tile was constantly
out-bid and redirected — **17.1% of travelling turns ended in an abandoned
journey**, 618 in a single game. Pathing was never broken (only 4.9% of steps
fail to close on the target).

| metric | before | after |
|---|---:|---:|
| wins on G's 38 live games | 17 | **23** (7 flipped to wins, 1 to a loss) |
| own score per game | — | **+5,142** (median +7,972, higher in 22 of 38) |
| own score, close-opponent games (29) | — | +3,539 |
| abandoned walks | 17.1% | **11.9%** |

Both ends of the range are worse: 5.0 → +1,182; hard commitment → wins 23→16,
−6,448. 3.0 is a real optimum: finish what you start, stay able to answer a
fire. **Against the 2300-rated field this change loses** (−1,139 at 2.0,
−3,789 at 4.0) — re-measure it if G climbs past ~1500.

**G's shape already matches the top of the ladder**: 104 wheat tiles sown a
game (top nine teams 100–210), 293 hands hired (theirs 266–316).

**Its one measured deviation is labour throughput**: 49.9% of worker turns
walking, 40.6% working, against the top teams' 40–48% walking and 42–53%
working.

**Where its money is lost**, against its own opponents (season means):
wheat −11,907, melon −6,855, strawberry −4,555, wool ≈ level,
**egg +7,056 in G's favour**. It out-produces them and converts worse. The
opponents buy 356 units of feed to G's 173 and sell their grain.

**Day-by-day against its real opponents**: level or ahead to day 20 (money
34,059 vs 33,685; planted 54 vs 50), then loses days 20–26 — they earn
19,051 in that window, G earns 14,265. **59% of G's land stands empty on day
29 with zero wheat.**

---

## 7. Dead ends — do not repeat these

### Measured on G's own 38 ladder games (the right population)

| change | wins (of 38) | own score/game |
|---|---|---:|
| feed + wheat 6 + strawberry 40 | 23 → 18 | −14,822 |
| `FEED_CARRY` 24 | 23 → 17 | −11,062 |
| feed + wheat 8 | 23 → 17 | −7,657 |
| hard commitment | 23 → 16 | −6,448 |
| `COMPACT` 0.45 | 23 → 18 | −6,157 |
| `WHEAT_TILES` 24 | 23 → 23 | −4,699 |
| bought feed alone | 17 → 17 | −3,775 |
| `TRAVEL_EXPONENT` 3.0 | 23 → 19 | −3,443 |
| missed-meal hunger rule | 23 → 20 | −2,468 |
| `SEED_BUFFER` 20 | 23 → 22 | +2,024 all / −3,385 close games — coin flip |

### Measured on the elite field (weaker evidence, still informative)

melon 12 sown on day 0 −4,785 · tomato 8 tiles −8,488 · bought feed 2 days
−8,637 · bought feed 1 day −5,985 · herd target 12 −1,797 · wheat area 24
−2,003 · strawberry cap 44 −231 · third land quadrant on day 12 +155 (noise)
· midday drop haul 250 −240 · late carrot fill (inert) · later last-sow days
(worthless) · pasture before coop −6,083 · melon-then-strawberry opening
−6,745 · seed-before-herd opening −1,594 to −4,439 · zone tax (strips)
−6,578 · rescue share 0.25/0.45 −5,545/−21,575 · night tip guard (too small
to matter) · `COUNT_CARRIED` · `PLANT_CUTOFF_HOUR` · `BUILD_CLAIM`.

**Twelve changes tested in the last session, one gain. G's constants are at a
local optimum — only mechanism changes have ever moved it. Do not open
another constant sweep.**

The most seductive dead end: the agents that beat G buy twice the feed and
sow two thirds the wheat. Copying that costs up to 14,822 a game, because the
*strong* teams farm wheat heavily exactly as G does. Buying feed is what a
weak opponent can afford, not what a good one does.

Two more recorded reversals worth knowing: rationing the early-harvest
release (rejected twice, −2,468 and −5,140) and holding stock for a better
price (rejected six times).

---

## 8. Agent H / H2 — architecture and results

`main.py` = a public Apache-2.0 route-replay base
(`arsgorynich/kaggriculture-v40-challenger`) with **our demand layer**
(`rl/candidate_h_demand.py`) appended and wrapping its `agent()`. The build
execs the layer in its own namespace so no names collide; licence notices
stay in `main.py`, `LICENSE` ships the Apache text, `NOTICE` records the
modification.

The layer re-decides the base's **SELL** orders from a model of town
consumption and the market price curves (`tolerance 0.25`), and guards cash
(`guard_cash` trims `BUY_SEED` orders so running cash stays above a reserve).

**The H2 fix.** In 21 of H's first 84 live games its base spent down to ~1
coin by the start of day 1, so the day-1 hires (1, 1 and 2 coins) failed, it
played day 1 with the farmer alone, two animals escaped that night, and it
lost all 21 by a median of 25,166. The fix is `hire_reserve = 15` with
`hire_reserve_until_day = 1`. Measured: **84 live games, wins 48 → 68, 20
losses flipped, 0 wins lost**; v14 field 71 → 78 wins, 0 games worse; mirror
19/24 unchanged; packaged file identical to the tested variant in 84/84.

Reserves on every day, or on days 0–3, cost score in normal games. An earlier
`feed_reserve` idea failed because it guarded the wrong thing.

**Nobody has run the money ledger, the walking census or the opponent profile
on H2.** That is free information sitting on the table.

---

## 9. Evaluation infrastructure

Interpreter `./.conda/python.exe`, always `PYTHONIOENCODING=utf-8`.

| what | command |
|---|---|
| replay an agent's own ladder games | `python -m tools.eval.live_replay run --agent {g,h,h-package} --submission <id> [--set K=V] --label L [--workers N]` |
| compare two such runs | `python -m tools.eval.live_replay compare "before" "after"` |
| day-medians for one run | `python -m tools.eval.live_replay summary "label"` |
| elite replay panel (secondary) | `python -m tools.eval.inspect_g --opponents 12 --tapes 6 --set K=V --label L --against "v14 midday drop 500"` |
| drill one game move-by-move | `python -m tools.eval.inspect_g --drill <episode> --seat S --seed N --from STEP --to STEP` |
| money by good and day, both farms | `ONLY_SUBMISSION=<id> python -m tools.analysis.money_flows g out.json` |
| worker movement + farm layout | `python -m tools.analysis.worker_walk 109133305 0 11 '{"STICKY_TARGET":3.0}'` |
| what the opponents did | `python -m tools.analysis.opponent_profile <submission>` |
| package G, then preflight | `python -m tools.packaging.prepare_candidate_g_submission` · `python -m tools.eval.preflight_candidate_g` |
| package H2 | `python -m tools.packaging.build_candidate_h --base <base main.py> --source <notebook slug> --out submissions/candidate-h2 --set hire_reserve=15 ...` |
| fetch our live games | `KAGGLE_API_TOKEN=... python -m tools.data.fetch_our_games --submission <id> --games 40` |
| turn them into exact tapes | `KAGGLE_API_TOKEN=... python -m tools.data.extract_live_tapes --submission <id>` |
| refresh the ladder snapshot | `KAGGLE_API_TOKEN=... python -m tools.data.fetch_leaderboard_records` then `python -m tools.data.prune_stale_tapes --apply` |

**`inspect_g`** plays G against many replays per opponent and judges *every
move both farms make* by running the engine's own action code on a snapshot of
the state — so "that move did nothing" is the engine's verdict. It prices
losses (rot, escapes, early harvests, overflow, stranded goods, missed care)
in coins and ranks them. `--against` needs the baseline's label **exactly**;
mismatches silently pair against the newest run instead.

**`live_replay`** replays our own ladder games from
`rl/data/our_live_tapes/`: same seed, same seat, the opponent's recorded
tape, stock engine. When the agent that recorded a tape replays it, the game
reproduces **to the coin** (38/38 for G, 84/84 for H). `--submission` filters
to one agent's games.

**`money_flows`** wraps `_process_market`, `_commit_unit`, `_do_hire` and
`_do_buy_land` to attribute every coin by day and good for both farms. Since
tapes reproduce exactly, the opponent's numbers in it are their real ones.

### Three ways these tools have produced false conclusions

1. **Replay opponents desync.** Tape opponents are open-loop. If your selling
   lowers the prices they sell into, their buys fail and every dependent
   PLANT/PLACE no-ops, cascading. One SpaTaro replay refused 583 moves and
   handed G a fake 88k–63k win. **Judge on games where the opponent's no-op
   share is ≤2%** (`inspect_g` prints the clean-game count and margin;
   `live_replay compare` prints the "stayed close" subset).
2. **The town lottery** (§4) — fixed by `fair_town`, but any verdict recorded
   before 2026-09-14 was decided across *different towns* and may be noise.
3. **Stale corpus.** `fetch_by_episode` never calls the API — it reads the
   local snapshot. The top 45 turned over entirely in four days once. Refresh,
   prune, then **re-run the baseline** before pairing anything, and report the
   snapshot date with every result. Pruning can shrink the field hard (248
   tapes, 36 teams, only 9 with ≥6 games — the baseline fell to 83 games).

---

## 10. Data on disk

- `rl/data/our_live_tapes/` — 84 H games + 38 G games, exact replays (seed,
  seat, both action tapes, per-day summary, opponent name and rating).
- `kaggle_cache/live_clones/` — 248 top-team action tapes (`source_team`).
- **`rl/data/ladder_study.md`** — a cold study of 200 replays across 9 top
  teams, written by an agent with no knowledge of our code. **Start here.**
- `rl/data/inspections/` — elite panel runs (`.md` + `.json`).
- `rl/data/live_replays/` — own-game runs, including the baselines
  `G own live baseline` and `G own live sticky 3.0`.
- `rl/data/leaderboard.jsonl`, `top_matches.jsonl`, `live_opponents.jsonl`,
  `our_games.jsonl` — snapshots; overwritten by the fetchers.

### What the ladder study found (9 teams, 200 games)

1. Every game opens with **wheat or melon** on day 0 — 2 teams always wheat
   (63 games), 7 always melon (137). A real strategic split.
2. All 9 teams buy **cow and sheep in days 0–3**; only one also buys geese.
3. **4–7 hires in the very first market queue**; 266–316 hires a season.
4. Work beats movement for 8 of 9 teams (42–53% vs 40–48%). Idle tolerance
   varies 20×: 0.8% to 16.3%.
5. **Wheat sowing dwarfs everything, 5–20×**: 100–210 plantings a game, vs
   carrot 33–94, strawberry 26–34, melon 11–16. Wheat's 4-day cycle lets the
   same tiles turn over all season.
6. Second quadrant day 5–6; third day 8–11 (some teams never).
7. **Wheat and fertilizer sell from day 0–1; carrot is held to day 26.**
8. Caveat from the study itself: two teams issue "sell 999" orders, so their
   raw quantities overstate real sales.

---

## 11. Kaggle API

```
POST https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes
     {"submissionId": <id>}   or   {"ids": [<episode ids>]}    # batches of 20
POST https://www.kaggle.com/api/i/competitions.LeaderboardService/GetLeaderboard
     {"competitionId": 147734, "pageSize": 250}
```

- Replays download from `https://www.kaggleusercontent.com/episodes/<id>.json`
  and need **no token** (they are public, ~30 MB each).
- **There is no way to list a team's submissions.** `teamId` filters are
  rejected; `ListSubmissions` returns 401. To find a new submission's id,
  sample episode ids from the window when it played and filter on
  `teamId == 16724366`. It rate-limits hard and then returns **400s** for a
  while — pace at ~2 s a call. **Far faster: ask the user for an episode id
  from any replay URL.**
- Episode ids were around **109,798,676** on 2026-09-17; they climb steadily.

---

## 12. Open leads, in the order I would take them

1. **H2, not G, if the goal is 2500.** 1,600 points closer, barely studied.
   Pull its games (`--agent h-package --submission 56272262`) and run the
   money ledger, the walking census and the opponent profile on it — none of
   which has been done.
2. **G's labour throughput, as a mechanism.** Three constants aimed at it all
   failed; the commitment mechanism worked. Untried: letting a worker do
   useful work it *passes* en route; planning pen and crop placement once at
   the start instead of opportunistically; explicit wheat-tile turnover on
   the 4-day cycle (ladder study, thesis 5). Build each as a switch
   defaulting off, measure on G's own games, record the verdict in the code.
3. **G's late season.** 59% empty land on day 29, zero wheat standing, and
   the game is lost between days 20 and 26. Sowing later measured worthless,
   so the question is whether the season should *end* differently — the
   closing logic (`CLOSE_*`, `DROP_FROM_STEP`) is where to look.
4. **G's conversion gap.** It out-produces its opponents and banks less.
   Nobody has explained that, and it is worth more than any switch.

**Working method that has actually paid**: measure the defect first (a
number), find its mechanism in the engine or the scheduler, change the
mechanism behind a switch, measure on the agent's own games, record the
verdict beside the constant, commit in the user's name, push. Every gain this
project has kept came that way; every sweep of constants has not.
