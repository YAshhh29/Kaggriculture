# The public Kaggriculture field, 2026-09-26

This document lists the public agents we extracted and checked, and says how they relate to each other and what the analysis notebooks measured. It does not rank the agents by strength. No tournament has been run yet (section 4).

Sources:
- 18 agent notebooks. 17 are extracted to `rl/public/<module>.py`. One could not be extracted (`nb_statma_thomas_2944`).
- 4 analysis notebooks: georgymamarin "what 2600 farms do differently", raykkretzschmar "findings from zero to top meta", raykkretzschmar "rank your agent", and destbreso "x-ray your agent".
- Per-item detail (hashes, line numbers, full mechanism lists, safety scans) is in `kaggle_cache/public_verify/<module>.json` and `an_*.json`. The notebooks themselves are in `kaggle_cache/notebooks/`.

How to read the numbers:
- **vs K**: one game against our candidate `candidates.candidate_k.agent`, on seed 11, with the public agent in seat 0 and `actTimeout` 60, unless noted otherwise. Scores are written as public agent - K.
- **vs random**: one game against the built-in random agent, seed 5, seat 0. The random agent is not seeded, so this number only shows that the agent runs and farms. It changes from run to run: guru v4 scored 128,578 and then 158,146.
- **Turn ms**: `time.perf_counter` around each agent call. Written as mean / max over the required games; a number in parentheses is the worst turn seen in any extra game. The machine was shared and often loaded, so read these as upper bounds.
- **Claimed, unverified**: the number appears in the notebook's text or in hard-coded tables, and the notebook contains no evidence we could re-run.

## 1. Every agent

Flag legend. No agent looked malicious, and `exploit_suspected` is false for all 18.
- **E**: `exec()` of source strings embedded in the file. These are the engine unit/decay model taken unchanged from kaggle-environments 1.32.7 and the E182 planner for the last seven turns; V48 adds a resource cache. We decoded and read all of them: stdlib only, no IO.
- **O**: an inert read-only `open()`. It either depends on the env var `V92_SELL_LIB`, which is unset here and on Kaggle, or has `path = None` hard-coded.
- **F**: opponent fingerprinting or counter-trades built from public state: rival money plus market wheat at step 2, CTRTABLE wheat trades that starve known cash-tight tapes of cash, and mirror detection. This is legal play.
- **L**: Kaggle runs the *last callable* in main.py, and that is **not** the function named `agent`. Our module points `agent` at the real entry point. See section 4.
- **S**: module state is global. Use one import (or one process) per seat, and never self-play inside one process.
- **P**: a small telemetry `print` at step 718.

| Module | Runs | Archetype | Claimed rating | vs random | vs K (seed 11, seat 0) | Turn ms mean / max | Flags and notes |
|---|---|---|---|---|---|---|---|
| nb_tschinkel_2945 | yes | route replay: 41 tapes + ~25 layers | 2944.7 live for this exact file (sub 56269928, 09-16); 2908 after a resubmit on 09-18. Claimed, unverified | 182,292-0 | W +2,429 (102,445-100,016). 6/6 vs K over seeds 1, 2, 3, 4, 11 and both seats on 11, margins +1.1k to +4.9k | 3.6 / 174 (337 with 4 games in parallel) | E O F. The file's sha matches the notebook's own assertion |
| nb_haideptry_2965 | yes | hybrid: route replay + ~60 layers | "2965+" in the title. Claimed, unverified | 190,985-0 | W +4,040 (103,899-99,859). 1 game | 5.6 / 234 | E O F L (entry `v7_hr_agent`). Its headline V59 order-book layer changed only 3 turns vs K |
| nb_guru_master_v4 | yes | hybrid | "Top 2" in the title, with no number; 19-1 vs "Guarded Microstructure v47". Claimed, unverified | 128,578-0 (158,146 on a rerun) | W +2,900 (102,830-99,930). Seat 1: W +5,349 (104,048-98,699) | 5.4 / 240 (245) | E O F L (entry `_final_sell_block_reorder_entrypoint`). One notebook cell pipes hidden base64 into `bash`; decoded, it is `rm -f` of LICENSE and NOTICE. That cell is excluded. On the same K game its parent v13 scored 103,534, so the ~877 appended lines added no margin there |
| nb_guru_master_v3 | yes | hybrid | "Proven 95.1% Win Rate, +17.5M Net Margin"; no rating given. Claimed, unverified | 193,656-0 | W +2,010 (81,004-78,994). 5/5 vs K over seeds 11-14, margins +1.7k to +7.5k | 3.5 / 149 | E F L S (entry `ig_agent`). **Byte-identical to nb_tetsutani_demand** |
| nb_statma_thomas_2944 | **no** | hybrid splice: 2945 for steps < 336, herd-safe afterwards | None for the splice. "2944" is Tschinkel's claim for one component | not run | not run | not measured | Not extracted. The permission classifier blocked decoding one component ("Untrusted Code Integration"); this is not a fault in the code. The notebook reads `/kaggle/input` and makes directories outside the cwd. Likely bug: it takes `_HERD_NS['agent']`, but in the herd-safe main.py that name is an inner layer; the real entry is `opening_liquidity_agent` (see nb_dmitrii_herdsafe_2700) |
| nb_flexonafft_multiroute | yes | route replay: 5 + 5 tapes rebuilt from 12 public traces ("Kawashigi"/"MDgogo") | 2743.3, the public score of its v70. Claimed, unverified | 173,196-0 | **L -42,554 (25,824-68,378). 0/3 vs K** (seeds 11-13) | 0.7 / 52 | F (fingerprints for the R5 and MD opponent families; the MD test misfires on K). The docstring says mirror preemption is off, but the code has it on |
| nb_tetsutani_demand | yes | hybrid | None | 193,349-0 | W +2,010 (81,004-78,994), identical over 3 runs | 4.0 / 161 | E F L S (entry `ig_agent`). Its own layer (IG) zeroed 14 dead orders vs K and moved none |
| nb_leoprovorov_forecast | yes | hybrid | None for this build; the parent's "LB 2700" is claimed | 186,596-0 | W +2,422 (81,863-79,441). 3/3 vs K (seed 11 in both seats, seed 12 in seat 1) | 4.7 / 205 (207) | E O F L P S (entry `herdsafe_forecast_agent`). The last notebook cell adds an undocumented route remap (10 shop pairs forced to route 0) whose origin is unclear. It had no effect in any town we tested |
| nb_boatlee_v16rc5 | yes | route replay: one majority-vote 720-step tape of Nikita Lugovoy's submission 55440039 | No number ("High-Score" in the title) | 147,914-0 | **L -30,700 (85,604-116,304). 0/10 vs K** | 0.4 / 41 | Clean; no exec; 18.9 KB. Cash sits near 0 on days 2-6, so 23 HIREs failed vs K |
| nb_tschinkel_metav4_v13 | yes | route replay: 41 tapes + ~40 layers | None for v13 itself; predecessors 2944.7 and 2916.8. Claimed, unverified | 185,449-0 | W +3,576 (103,534-99,958) | 3.4 / 180 (190 on a rerun) | E O F |
| nb_haideptry_shepherds | yes | route-replay core + ~60 layers | "LB 2700 Sovereign v2" badge. Claimed, unverified | 153,753-0 | W +2,416 (81,865-79,449) | 6.7 / 282 | E O F L P (entry `hs4_ig_agent`) |
| nb_leoprovorov_godmode | yes | route replay: 2945 + an EQ queue layer + a shop overlay | None; the notebook says "positive final-score impact: not measured yet" | 187,713-0 | W +2,540 (102,564-100,024). Seat 1: W +5,015 (103,812-98,797) | 7.4 / 296 (337, seat-1 game run in parallel) | E O F S. "Hacked Stores" is legal research into the shop RNG, and the seed posterior is telemetry only. It lost 1 game to its own parent, 2945, by 631 |
| nb_nihilistic_robust | yes | route replay | None; it inherits 2945's 2944.7. Claimed, unverified | 188,017-0 | W +2,429 (102,445-100,016), identical to 2945 | 4.8 / 214 | E O F. **AST-identical to nb_tschinkel_2945** (only the comments were stripped). Its own table shows 0/6 vs "cha22_2500" |
| nb_arsgorynich_herdsafe_v3 | yes | hybrid | None; the notebook says "leaderboard improvement is not established" | 193,315-0 | W +2,422 (81,863-79,441). 3/3 vs K | 6.3 / 221 (236) | E O F L P S (entry `herdsafe_forecast_agent`) |
| nb_statma_herdsafe_ca25 | yes | hybrid, route-replay core | None | 178,423-0 | W +2,579 (82,044-79,465), identical on a rerun | 6.6 / 312 (330 on a rerun) | E O F L (entry `opening_liquidity_agent`). Differs from nb_dmitrii_herdsafe_2700 by one constant |
| nb_ahmed_v48 | yes | hybrid | None; the notebook says its test does not establish a 2850+ score | 184,287-0 | **L -187 (100,149-100,336)**. Seat 1: W +2,273 (101,379-99,106) | 3.9 / 223 | E F L (entry `_e335_agent`). Loading the name `agent` would get the older ADV layer and silently drop 5 layers. It rebinds its own global `copy` to a faster proxy |
| nb_ahmed_v55 | yes | route replay | None | 196,782-0 | W +3,637 (103,557-99,920) | 5.7 / 279 (351 on a loaded rerun) | E O F L (entry `final_price_guard`). Its claimed 45 ms maximum callback did not reproduce: we saw 199-351 ms at step 150 |
| nb_dmitrii_herdsafe_2700 | yes | route replay | "LB 2700" refers to an earlier version's result (claimed); its local ledger shows 56-8-0 | 152,108-0 | W +2,601 (82,074-79,473) | 9.0 / 450 (670 in the pinned demo game) | E O F L (entry `opening_liquidity_agent`). The spikes are at step 150 and happened with ~17 other Python processes running. We reproduced the notebook's pinned demo game exactly (rewards and per-seat action hashes). Notebook cells re-register the engine and redirect file descriptors; those cells are excluded |

**Timing.** No turn in any game went over 900 ms. The family has two known spikes. Step 150 is the lazy decode of the PREDICT sale-stream library, about 200-300 ms on its own. Step 712 is the terminal planner, which runs 64 or 128 simulations. nb_dmitrii_herdsafe_2700 came closest to the limit (670 ms under heavy load). On a slower Kaggle CPU, expect up to about 2x on those two steps.

**The vs K column is not a ranking.**
- Seed 11 produced two different towns. The scores fall into two groups: ~100-104k (2945, nihilistic, godmode, v13, V55, haideptry 2965, guru v4, V48) and ~79-82k (the cha22 pair and the herd-safe family). Two of the reports name their shop pairs: FARMERS_MARKET+BAKERY (V48) and PIZZA_SHOP+BAKERY (leoprovorov). This fits our memory note that the town draw is coupled to both farms' empty tiles. Margins from different rows therefore come from different worlds.
- K comes from the same tape family: it shares the route blob, in the EXP-173 lineage. The public bases recognise it as a mirror of themselves: V48 for 476 turns, ca25 for 368, guru v4 for 312 and haideptry 2965 for 305. A +2k to +4k margin against K measures a market race between near-mirrors, which is about 3% of the bank. It does not measure ladder strength.
- The two agents from other lineages, boatlee and flexonafft, lose to K by 30k-43k.

**Agents seen but not extracted to `rl/public/`:**
- raykkretzschmar C92, C94 and C95 are embedded in the "findings" notebook. They are 3-quadrant, 10-cow/4-sheep tapes from the August route-replay meta. Locally C95 went 0-6 in its games against K and nb_tschinkel_2945 (seeds 5 and 11, both seats), losing by 28.8k-64.4k. C94 beat C95 3-1, by 78-650 coins each. The claimed public scores are 2836.8 for C92 and 3085.4 for the earlier C45; both are unverified.
- raykkretzschmar's `v38_low_pressure_opening` is embedded in the "rank your agent" notebook and was decoded to the scratchpad only. It claims 630-10 on a holdout; locally it went 0-4 vs nb_tschinkel_2945 and 0-4 vs nb_haideptry_2965 (seeds 1 and 2, both seats).

## 2. Lineage

The arrows follow each agent's own credits and NOTICE files. "Identical", "one constant" and "+N lines" come from our own diffs.

```
yhay81 Shop Router 0908/0909/0911/0913 tapes + shop-pair map
thomastschinkel "Public State Router" chassis
        |
Ahmed Berat Ozer V25..V47, EXP-149..EXP-335
(Seyit Kaan Gunes V47 layers; aurax7, tetsutani, prvsiyan, Gluzdov E182, lucifer19, leoprovorov, ...)
  |   our submissions/candidate-h2 (and so K) is an earlier member of this chain:
  |   same route blob, layers up to R97, none of R124+/RACE/v44y/E334-E335
  |
  +-- nb_ahmed_v48  "clear the queue" (E334/E335)                          357 KB
  |
  +-- tetsutani cha20 -> cha22 (IG hole closure, CXD, MODELPX)             501 KB
  |      = nb_tetsutani_demand
  |      == nb_guru_master_v3                (byte-identical repackage)
  |
  +-- thomastschinkel v9/2 .. v9/4 "The 2945 Farm" = nb_tschinkel_2945       856 KB
         |-- nb_nihilistic_robust            (AST-identical, comments stripped)
         |-- nb_leoprovorov_godmode          (2945 + EQ layer + seed-blind shop hold-back)
         |-- nb_statma_thomas_2944           (2945, then herd-safe from step 336; not extracted)
         |
         +-- v_gate / v11 -> "Metav4 Farm v13" = nb_tschinkel_metav4_v13     1.00 MB
                |
                +-- nb_ahmed_v55   (v13 + HybridOpening + step-91 wheat price guard + RACE 41)
                       |
                       +-- (+ V56 E402/E410, shiiin9 order-book counters T-B and D)
                       |      nb_dmitrii_herdsafe_2700   (v13 + 578 lines; RACE 44; opening BUY 8/SELL 3)
                       |        |-- nb_statma_herdsafe_ca25    (one constant: CARROT2 margin -15 -> -25)
                       |        |-- nb_arsgorynich_herdsafe_v3 (+ risk-aware feed top-up + forecast4 gate)
                       |        |      +-- nb_leoprovorov_forecast (+ route remap for 10 shop pairs)
                       |        +-- nb_haideptry_shepherds     (+ risk feed, forecast4, HS4: SM/E402/T4/IG)
                       |
                       +-- shiiin9/haodou092 "V59 Harvest Ledger" -> nb_haideptry_2965 (+ "v7" pipeline)
                              +-- nb_guru_master_v4  (per its NOTICE; v70 turns off all herd-species swaps)

Independent lineages (no code shared with the tree above):
  Nikita Lugovoy sub 55440039 replays     -> nb_boatlee_v16rc5 (1 tape + weed repair + premium lead)
  "Kawashigi"/"MDgogo" public traces      -> nb_flexonafft_multiroute (12 rebuilt tapes + v17 guards)
  raykkretzschmar C70..C95                -> August 3-quadrant route-replay tapes (embedded in an analysis nb)
```

Near-identical clusters:

| Cluster | Members | How close | Evidence |
|---|---|---|---|
| cha22 | nb_tetsutani_demand, nb_guru_master_v3 | byte-identical main.py (sha 127ed3e6...) | same sha; same K game, 81,004-78,994 |
| 2945 | nb_tschinkel_2945, nb_nihilistic_robust | AST-identical | `ast.dump` is equal; same K game |
| 2945+ | nb_leoprovorov_godmode | 2945 plus a ~113-line EQ layer plus an overlay | diff; about +100 over the parent's K result |
| herd-safe | nb_dmitrii_herdsafe_2700, nb_statma_herdsafe_ca25 | one constant | diff; K games 82,074 vs 82,044 |
| herd-safe v3 | nb_arsgorynich_herdsafe_v3, nb_leoprovorov_forecast | same payload, plus a remap of 10 shop pairs | diff; identical scores in every town tested |
| herd-safe+ | nb_haideptry_shepherds | dmitrii's main.py plus the HS4 layers | the dmitrii diff |
| Metav4 core | nb_tschinkel_metav4_v13, nb_ahmed_v55, nb_guru_master_v4, the whole herd-safe family, nb_haideptry_2965 | the first ~6,466 lines are v13, byte-for-byte except the V92 library path line | diffs |

All 15 modules in the tree share the same 94 KB route blob (41 tapes of 719 steps), the same router (tape picked at step 144 from the first two shops, then route 2 from step 648), the E182 planner and most of the market layers. In this document, **V39 family** means all modules except boatlee and flexonafft. A de-duplicated tournament field has about 13 distinct agents: drop guru v3, nihilistic, ca25, and one of arsgorynich/leoprovorov.

## 3. Mechanisms in play and what was measured

Cluster labels used below:
- **2945** = tschinkel_2945, nihilistic, godmode
- **V13** = metav4_v13, ahmed_v55
- **HS** = dmitrii, ca25, arsgorynich, leoprovorov_forecast, shepherds
- **2965** = haideptry_2965, guru_v4
- **CHA22** = tetsutani, guru_v3
- **V48**
- **BOAT** = boatlee; **FLEX** = flexonafft

No public agent has a learned demand model. The only learned part anywhere is PREDICT's matching of recorded sale streams.

Source tags on the measurements: [Rayk-F] is the findings notebook, [Rayk-R] the rank notebook, [destbreso] and [georgy] the other two. When a line says "our rerun", the number comes from our own corpus (`kaggle_cache/top200_tapes` + `corpus_v2`: 2,122 episodes and 4,244 seats rated 2,377-3,111, snapshots from Sep 22-25) using that notebook's method. The notebook itself did not publish that number. The georgymamarin notebook ships almost no numbers of its own, so every figure credited to it is our rerun.

### 3.1 Market and sale timing

| Mechanism | Used by |
|---|---|
| Sell next step's planned lot one step early on turns with no town draw (step % 4 != 0) | whole V39 family (chassis `sell_lead`) |
| Pull planned sales forward, tracked in a debt ledger (R36), with the horizon fitted to the rival's observed lead (RACE) | whole V39 family. Horizons: V48 2-4, then 9 and 24 against a mirror opponent. CHA22 base 2, RACE 44-48. 2945 40-48. V13 40 (v13) / 41 (V55). 2965 41-48. HS 44-48 |
| Glut gate RACEPX/RACEGATE: pull forward only while the quote is at or above base | 2945, V13, HS, 2965, CHA22 |
| Library of recorded rival sale streams (PREDICT): sell ahead of predicted premium dumps | 2945 (1,998 streams), V13/HS/2965 (2,398 streams). A precision-gated 4-turn extension (forecast4) is in arsgorynich, leoprovorov_forecast and shepherds |
| Mirror detection with horizon escalation (EXP283: equal positions on 4 of 6 turns and tile similarity >= 0.95) | V48, CHA22, V13, HS, 2965. 2945 has the older R37/R44 mirror test (similarity >= 0.9). FLEX has its own signature-distance test |
| Exact per-slot lockstep simulation for ordering orders | v44y block permutation: V48, CHA22, V13, HS, 2965. CXD best response over every slot (800 evaluations): CHA22, 2965, HS. ORDERPRI2 ordering by rival exposure: 2945, V13, HS, 2965, CHA22. Price-impact ordering: FLEX |
| Dead-order hole closure (keeps live sales in earlier lockstep slots) | E334/E335: V48, CHA22, HS, 2965. IG: CHA22, 2965, shepherds. VQ: guru_v4. EQ: godmode |
| Hour 21-23 overflow sales, pre-guard, and COURIER same-evening delivery | whole V39 family (COURIER from v9 on). FLEX has its own room guard and evacuation. BOAT has none |
| One-turn mirror preemption with a credit ledger (T4) | shepherds |
| Next-turn price model (MPX/MODELPX) | CHA22, 2965 |
| Unconditional one-turn lead on premium sales, gated on town demand | BOAT |
| Front-running two known replay families using their market tapes, embedded unchanged | FLEX |
| Holding a sale back until just after the next shop drain | godmode |

What was measured:
- [Rayk-F, author's games] Among near-mirrors, market play matters more than herd composition. c18 and c16 differ on 20 field turns but 112 market turns, and c18 won 35-5 over 20 seeds and both seats (mean +3,161). c15 (a one-turn premium front-run) beat the raw Senkin tape 14-2 (+2,250).
- [Rayk-F] Ordering premium SELLs by price impact, C71 vs C70: 31-9 (+231), and 83-37 vs 57-63 in a 4-agent round robin. On 88 historical live tapes both went 83-5, so fixed tapes hid the gain.
- [Rayk-F] A fixed long horizon lost: H25 went 0-6 against C45 and V14 on fresh seeds. Inferring the opponent's horizon during the game (C68) went 342-18 on untouched seeds 900000-900019.
- [Rayk-F] A debt-conserved one-turn split on wheat and fertilizer flipped 11 near-mirror live losses, each worth 5,300-5,700. On 900 held-out games: fertilizer only 174-6, wheat 10 + fertilizer 5 174-6, aggressive 168-12. A difference of 1 game in 120 is a tie.
- [Rayk-F] Intraday banking pays in only one narrow case: an idle or moving worker carrying at least 2,000 of premium goods, at most one move from the shed. That variant went 7-1; every other variant went 0-8.
- [destbreso, our rerun on 594 early-September seats from 87 teams] Selling at the price floor (quote <= 2) correlates -0.45 (Spearman) with rating. The winner had fewer floor sales in 312 games and more in 247.
- [georgy method, our rerun on 2,122 episodes] The two banks in one episode correlate +0.90. The median winning margin is 2,787, about 3% of a ~100k bank. [destbreso, our rerun] Bank vs rating is Spearman +0.03 (early September) and +0.15 (current).
- [Claims in upstream code, unverified] RACE 40/12 won 73-7 over 80 mirror games. RACEPX won 35-13 over 48. V55 says horizons 42 and 43 regressed in 10 paired games, and reports V55 vs V54 as 91/15/4 against 75/9/26 over 110 games per arm. Tschinkel says holding premium goods back lost $7.5k-$34k a game.
- [Our extraction runs, 1 game each unless noted, not significant] boatlee's one-turn lead was worth +315 to +2,327 against its own lead-less core (6/6), but only +40 to +70 against K (4 seeds). CXD changed 3 turns vs K in 2965 (+64 modelled) and 2 turns in dmitrii (+24); assuming a mirror rival rarely finds a gain. guru v4 scored 102,830 on the K game where its parent v13 scored 103,534. VQ changed 65 turns; IG zeroed 14 orders and moved none; EQ changed 51-55 turns a game.

### 3.2 Demand models

| Mechanism | Used by |
|---|---|
| Engine-exact price curve (base, I0, T, sqrt/log/hinge shapes, patched by `market.params`) | V39 family; FLEX has a copy; BOAT has none |
| Town-draw model: every 4 steps each unlocked shop takes 1 unit per product (2 for single-product shops); the town centre takes 1 of each product per day | V39 family; BOAT uses it as a yes/no gate; FLEX turns it into an urgency multiplier |
| Exact recovery of rival sales: rival_sold = inv' - inv + town_draw - own_sold, exact above the $1 floor | V39 family from v9 on; V48 has an equivalent (`_race_town`/`_race_lost`) |
| Estimate of the rival's unsold stock from public tiles minus recovered sales (ORDERPRI2) | 2945, V13, HS, 2965, CHA22 |
| HERD2 species EV with a zero-sum swing term: delta-price x (our future units - rival future units) | 2945, V13, HS, 2965, CHA22 (turned off in guru_v4) |
| CXTB projected tomato book: drain minus 2.4/day slack, plus 0.75/day per rival tomato tile, with our units walked up the price curve | HS |
| Posterior over the hidden shop seed | godmode (telemetry only; it never acts on it) |

What was measured:
- [Engine, checked by several reports] The town draw works as described above. Engine 1.32.7 added hinge scarcity pricing: CARROT base 35, T 450, hinge 1.00; TOMATO base 60, T 200, hinge 0.40; EGG base 50, T 332, hinge 0.40; HINGE_GAIN 8.0.
- [Rayk-R, checked in the engine] Shop types that buy each product: WHEAT 5, STRAWBERRY 4, MILK 3, EGG 2, CARROT 2, TOMATO 2, WOOL 1, MELON 0. With one shop of each type, daily demand is WHEAT 30, STRAWBERRY 24, MILK 18, CARROT 18 (the notebook's 12 is wrong), EGG, TOMATO and WOOL 12 each, plus 1 a day of each from the town centre. Real towns unlock up to 8 shops, drawn with replacement.
- [Rayk-R, one season each] With 16 cows, MILK inventory ended at -148 and sold at 266 against a base of 160. With 16 geese, EGG inventory ended at +104 and sold at 42. We re-derived the prices from the engine; the inventories are the author's measurements.
- [godmode notebook, claimed] One extra empty tile before an unlock changed the next shop in 98 of 128 paired games (76.6%). All 3,136 unlocks over 392 matches fitted the reconstructed formula. An atlas of 4,139 episodes shows the first-two-shop worlds are about uniform (chi2/df 1.05). [Our check] The formula is in the engine (kaggriculture.py lines 865-891). Given the true seed it predicted 31 of 32 real unlocks in 4 of our games. The live posterior died out by day 2-8 in every game.
- [destbreso] There are 64 ordered first-two-shop worlds. Covering all 64 takes about 303 games; 73 games cover about 44.
- [HS code, claimed] The CXTB constants were "measured on 96 replayed games". Against K the gate opened, projecting 16.7k of revenue.

### 3.3 Herd and cash safety

| Mechanism | Used by |
|---|---|
| Rewritten step-0 wheat trade | 2945 and V13: BUY 20 / SELL 15, claimed to keep >= $1,050 after step 1 against 6,648 recorded openings. HS: BUY 8 / SELL 3 plus 1 seed. V48: BUY 7 / SELL 2, plus a BUY 30 in slot 0 at step 1 that raises a same-tape rival's feed price. CHA22: BUY 5 plus 1 seed |
| CTRTABLE counter-trades that starve known cash-tight tapes | 2945, V13, HS, 2965, CHA22 |
| Cash shield (SM): put the highest-priced SELLs ahead of a BUY that would otherwise fail | CHA22, 2965, shepherds |
| Extra wheat pickup for animals one missed feed from loss | arsgorynich, leoprovorov_forecast, shepherds (fired about once a game); 2965 has the HR guard |
| CAPHARV: harvest before stored yield overflows its cap | 2945, V13, HS, 2965, CHA22 |
| Species swaps (HERD/HERD2/COWSWAP) | 2945, V13, HS, 2965, CHA22. guru_v4 turns all of them off. V48 has its own yarn-store sheep swap |
| Skip FEED when the care bonus is worth less than a wheat | V48 and later (62 skips a game vs K in V48) |

What was measured:
- [Rayk-F, live audit] Opening feed denial: in 4 of C92's losses the rival bought 14-19 wheat ahead of C92's slot-8 buy of 5, and a sheep was lost on day 2. Those losses averaged -13,606. The fix, buying five wheat in slot 0, went 173-7 (96.1%) over 900 held-out games on 6 seeds. Buying six went 0-4.
- [HS, claimed] No cow escapes; goose escapes in 16 of 64 local games.
- [Rayk-R, tuning seeds 7000-7002, games per configuration not stated] All 32 goose configurations lost to the hand-built "Rita" farm; the best lost by 7,569. A 16-cow herd gained +4,450 on the tuning seeds but lost 3-9 (-3,627) on held-out seeds (12 games).
- [destbreso, our rerun on corpus_v2, 2,202 seats] CARE correlates -0.45 with rating: a median of 369 CARE at 2900+ against ~400 below 2700. Geese correlate +0.31: a median of 7 at 2900+ against 3 below 2800, and the winner had more geese in 325 games against 247. Cows +0.19, sheep -0.14.
- [georgy method, our rerun, pairs of seats in one episode rated within 50 of each other] The seat with 10 or more cows won 63% (n=185). The seat with any geese won 55% (n=172).
- The goose evidence conflicts. The hand-built farm says geese hurt; top-ladder seats keep more of them. The contexts differ and we have not tested either claim.

### 3.4 Crop mix

| Mechanism | Used by |
|---|---|
| Base crops from the tape | 2945 family: ~163-166 wheat, 33 strawberry, 28-31 carrot, 12 melon seeds, little tomato. guru_v4 vs K: 145 wheat, 50 carrot, 33 strawberry, 12 melon, 10 tomato. BOAT: 143 wheat, 37 strawberry, 19 melon plantings. FLEX: wheat, strawberry, melon, almost no carrot |
| CARROT2 wheat-to-carrot swap | 2945, V13 (margin -5), HS (-15; ca25 -25), 2965, CHA22 |
| V219/V221B finite tomato block (~10 tiles from day 18) | V39 family. HS gates it with CXTB. V219SKIP skips the tomato crew on days 19/21/23 (V13 and later) |
| HybridOpening: one temporary wheat on the future pasture tile | V55, HS, CHA22, guru_v4 (3 wheat each time) |
| FERT, and E410 (skip fertilizer that cannot change the yield) | FERT from 2945 on; E410 in HS, 2965, CHA22 |

What was measured:
- [georgy method, our rerun on 4,244 seats in bands 2950+ / 2900-2950 / 2800-2900 / 2700-2800 / 2600-2700 / <2600, n = 122/155/729/1857/1224/157]

  | Median per seat | 2950+ | 2900-2950 | 2800-2900 | 2700-2800 | 2600-2700 | <2600 |
  |---|---|---|---|---|---|---|
  | Total plantings | 266 | 273 | 245 | 239 | 239 | 239 |
  | Carrot | 60 | 50 | 41 | 40 | 39 | 40 |
  | Tomato | 10 | 14 | 9 | 0 | 0 | 0 |
  | Share planting any tomato | 76% | 91% | 76% | 40% | 34% | 20% |

  Wheat (~150-157), melon (12-13) and strawberry (31-33) are about the same in every band.
- [Same method, split by snapshot] Tomato adoption for 2900+ / 2800-2900 / 2700-2800 / 2600-2700 was 90 / 67 / 24 / 18% on Sep 22-23 and 79 / 93 / 83 / 42% on Sep 25. The crop that marks the top band changed within 3 days.
- [Same method, pairs within an episode] The seat with 260+ plantings won 66% (n=283); with 50+ carrot, 62% (n=220); with any tomato, 59% (n=292). Tomato drops to 51% on the Sep 25 snapshot alone (n=156), and to 49% when both seats are 2800+ (n=68, median margin -623).
- [destbreso, our rerun on corpus_v2] Below 2700, seats running the day-18 fourth-quadrant tomato program won 0.439 (n=198) against 0.470 without it (n=1,151). At 2700+ the program appears only 6 times.
- [Tschinkel, claimed] Top teams hold ~10 tomato tiles by day 20 and sell ~71 tomatoes at ~$114. Tomato overlays on a busy tape lost 0/85.
- [Our run] ca25's CARROT2 margin of -25 scored 30 coins less than its parent's -15 on the one deterministic K game.

### 3.5 Hiring

| Mechanism | Used by |
|---|---|
| Hires from the tape: ~260-290 HIRE orders a game, 12-13 hands at the end | V39 family. BOAT: 264 HIREs, up to 14 hands. FLEX: up to 12 |
| Cuts that account for the Fibonacci hire cost: V219SKIP; R53 (no hires on days 26-28); VT1 (day 29); SL2 (one sheep hand) | 2945 (SL2/VT1), V13 and later |
| Dedicated project crews (tomato, sheep, inputs) | V39 family |

What was measured:
- [Engine] The n-th hire of a day costs the n-th Fibonacci number, and hands reset daily. A 12-hand day costs 376 coins; the 13th hand adds 233 and the 14th 377. A HIRE the farm cannot afford is dropped silently, so order counts overstate real hires (by at most 2 in our re-simulations).
- [georgy method, our rerun] Peak crew is 12 in every band. Median HIRE orders by band: 291 / 291 / 286 / 276 / 270 / 267. Within an episode, the seat with 290+ HIREs won 60% (n=313), and 53% when both seats are 2800+ (n=111). Spearman: hires +0.13 vs bank, +0.29 vs rating.
- [destbreso, our rerun on corpus_v2] HIRE orders correlate +0.39 with rating: a median of 301 at 2900+ against 268 below 2600. Median hands on the board at hour 12: 7 on day 6, 8 on day 8, 11 on day 10 and 11 on days 15-27; the 2900+ tier holds 12 from day 15. The winner placed more HIREs in 528 games and fewer in 414.
- [Claimed] V219SKIP is worth +$501 a game on 232 replays.

### 3.6 Land

| Agent | Land purchases |
|---|---|
| 2945 family | 2 BUY_LAND, on days 6 and 11 (3 quadrants); SE comes through the V233 six-sheep project in yarn towns |
| V13 / HS / 2965 / CHA22 | in the K games, at steps ~150, 265 and 433-435, so all 4 quadrants by day 18 |
| HS | the CXTB tomato gate buys SE ($4,000) only if projected revenue is at least 9,000 |
| V48 | whatever the tape does |
| BOAT | NE at step 160, SW at 240, never SE |
| FLEX | steps 148 and 264, plus 288 on yarn routes |

Every public agent here buys its third quadrant on day 10-11.

What was measured:
- [destbreso, our rerun on corpus_v2, 2,202 seats] The day of the 2nd BUY_LAND (the third quadrant) correlates -0.70 with rating: a median of day 9 at 2700+ against day 11 below. At 2900+, 131 of 134 seats bought it on day 8 or 9. At 2600-2699, 738 of 902 bought it on day 11. The first BUY_LAND is on day 6 in every tier. The Aug-30 leader (245 embedded episodes) bought its second quadrant on day 5 in all 245 and its third on day 8 in 196.
- [georgy method, our rerun] Seats with 3 or more land orders, for 2900+ / 2800-2900 / 2700-2800 / 2600-2700: 77 / 55 / 31 / 27% on Sep 25, against 40 / 21 / 25 / 23% on Sep 22-23. Within an episode, the seat with 3+ land orders won 59% (n=290). When both seats are 2800+ it also won 59%, with a median margin of +2,360 (n=108).
- [Rayk-F] Bolting SE onto a frozen 3-quadrant tape failed. Every SE variant lost 10-0 to C92, and C93 went 0-40.
- [Our runs] K and nb_tschinkel_2945 owned SE by step 300-480 and beat the 3-quadrant C95 by 28.8k-64.4k.

### 3.7 Endgame

| Mechanism | Used by |
|---|---|
| Shared endgame tape (route 2) from step 648 | V39 family |
| E182 bounded planner at step 712 (64 simulations; 128 in HS), which accepts only a strict physical gain | V39 family |
| At step 718: every unit next to the shed DROPs, then the whole projected shed is sold by price x qty | V39 family; FLEX liquidates from step 716 |
| E402 late seed cap from step 624 | HS, 2965, CHA22 |
| VT1 (no CARE on day 28, no feeding on day 29) and R53 | 2945 and later |
| No endgame logic; stock left in the shed at the end is never sold | BOAT |

What was measured:
- [Rayk-F, engine line 960] The action at observation step 718 executes; the one at 719 never does. Moving the terminal controller from step 712 to 717 (c27) went 90-10 over 10 seeds and both seats.
- [destbreso] The Aug-30 leader leaves a median $442 unsold at the end (p90 1,184, 245 episodes). Stranded value shows no winner/loser signal (239 vs 267 games).
- [Our runs] Against K, E402 cut 76-78 seed units (about $1,560) a game in the HS and 2965 families. In some games E182's shadow check rejected its own plan.

## 4. Caveats

1. **Claimed ratings are claims.** No notebook ships evidence we can check for a ladder number. The 2026-09-23 correction in `docs/research/public_meta_study.md` also found none of these authors' handles among the 561-tape corpus or the top 136 live teams, though handles and team names can differ.
2. **Strength has to come from a measured tournament, and none has been run.** Nothing in this document ranks the agents. The vs K games are single games on one seed, mostly in one seat, and they were played in different towns (section 1). K is a near-mirror of this family, so those games show near-mirror market play, not ladder strength.
3. **The ladder evidence argues against the whole public family, but nothing is settled.**
   - destbreso's per-team classifier, rerun on corpus_v2, reads every one of the current top 30 teams as composing its plan per game. The caveats: most teams have fewer than the notebook's 8-episode floor, and a shop router with 41 distinct tapes can also score low on that cross-episode repeat metric.
   - Plan agreement is about 0.01 at 2700+. There were no mirror games in the 450 games whose source team is rated 2700+, while 60 of 510 games at 2600-2699 were mirrors.
   - Every public agent here buys its third quadrant 2-3 days later than 2900+ seats do.
   - Tschinkel himself reports 0-36 against seven top-10 teams on Sep 15-17 (claimed).
4. **Seat symmetry is disputed.** The Rayk-R notebook (4 of 4 pairs) and the dmitrii ledger report identical banks when seats are swapped. Our games against K were not symmetric: V48 -187 vs +2,273, guru v4 +2,900 vs +5,349, godmode +2,540 vs +5,015. Always run both seats.
5. **Duplicates double-count.** guru_v3 is tetsutani, nihilistic is 2945, ca25 is dmitrii plus one constant, and leoprovorov_forecast is arsgorynich plus a remap. De-duplicate by AST, not by file sha.
6. **Loader hazard.** `stack/public_agents.py` line 37 takes `namespace.get("agent")`. For every module flagged **L**, that returns an inner layer, not the agent Kaggle runs. V48 would lose 5 layers and V55 its last one. Our `rl/public/` modules already alias `agent` to the right entry, but any other loader must use `kaggle_environments.agent.get_last_callable`.
7. **The analysis numbers age fast.** The corpus snapshots are from Sep 22-25, and the ladder turned over within 4 days. Correlations across episodes are confounded by the world each episode draws; pairs within an episode are better but still not causal.
8. **Noise.** The random opponent is not seeded. Timings come from a loaded machine. Several upstream "wins" were measured against fixed replay tapes, which desync and inflate results.
9. **Tournament to run next** (not done): about 13 de-duplicated agents plus K and H; paired seats; fresh seeds; `actTimeout` 60; our fair_town handling; count only clean games (status DONE, no hand desync); report within-episode margin and paired-seat wins or a Bradley-Terry fit, not mean bank.

## 5. Most promising distinct ideas

### (a) Route follower plus our layers: the strongest runnable public base, with our own demand/market layer on top

The tournament picks the base from the de-duplicated set. All the ideas below apply to any V39-family base, because they share the chassis.

1. **Our own book model, fed by the base's exact ledger of rival sales** (`_v9_race_update`/`_v9_town_draw`). Project each product's inventory from the shops actually unlocked, the hinge price curves, the rival's recovered sales and its stock visible on public tiles (as ORDERPRI2 estimates it). Time sales from that projection instead of the tape's schedule.
2. **Infer the pull-forward horizon instead of hard-coding it.** The family has escalated from 40 to 41 (V55) to 44 (HS). Rayk measured a fixed long horizon losing (0-6) and a horizon inferred during the game winning (342-18). Sell at the rival's observed lead + 1, and only while the quote is at or above base.
3. **Rebuild the PREDICT library from our current corpus.** The shipped libraries (1,998-2,398 streams) are September snapshots of a ladder that has since turned over. Wrap it, and every other action driven by an opponent model, in the forecast4 precision gate: act only after at least 3 hits at 70%+ precision. The gate correctly stayed idle against random (0 extensions, 78 rejected).
4. **Best response against a predicted rival order list, not a mirror.** The CXD lockstep simulator is exact, but because it assumes the rival submits our own list it found gains on only 2-3 turns against K. Give it the rival list implied by the recovered sales plus PREDICT.
5. **Plan for the mirror war.** These bases flag K as a mirror for 305-476 turns and front-run it, and they will do the same to any agent that mirrors them, including ours. Either break the mirror signature on purpose (worker positions, tile similarity) or win the race: T4 one-turn preemption with a credit ledger, and escalation after a lost race.
6. **Port the cheap, measured fixes the chosen base lacks.** E402 seed cap (about $1.5k a game vs K); E410; hole closure (EQ/IG); a step-0 feed buy in slot 0 (Rayk 173-7); weed-block repair on scheduled PLANT/PLACE/BUILD (Rayk C92 vs C91 +446.6); final DROP/SELL by step 718.

### (b) Bespoke agent

1. **Compose the plan per game from state, not from a tape.** Per destbreso's rerun, that is what the current top 30 do, and it keeps us out of the family's mirror detectors.
2. **Buy the third quadrant by day 8-9 and budget cash for it.** The day of that purchase correlates -0.70 with rating over 2,202 seats; every public agent buys it on day 10-11. At 2900+, 77% of seats placed 3 or more land orders (Sep 25).
3. **Money-curve checkpoints**, from 16 seats in 8 games where both seats were 2900+ (re-simulated exactly): under ~1k through day 8, ~10k at day 11, ~50k at day 20.
4. **Crops.** Shared base: ~155 wheat, ~33 strawberry, 12 melon. Aim for 260+ plantings (66% within-episode win, n=283) and 50-60 carrot (62%, n=220). Tomato is now part of the base at 2800+ (79-93% adoption on Sep 25) but is no edge when both seats are 2800+ (49%, n=68). Time carrot and tomato sales to the hinge curve.
5. **Labour and herd.** 11 hands by day 10 and 12 later, about 295-300 HIRE orders. Size CARE to the yield it actually adds (CARE correlates -0.45 with rating). Test a herd of 10+ cows (63%, n=185) and a goose line; the goose evidence conflicts.
6. **Use the public market code as a library, not as a base.** The useful pieces are the exact lockstep simulator (`_v44y_lockstep`), rival-sale recovery, the R148 overflow contract and atomic PLANT repair, COURIER, a terminal planner that accepts only a dominant plan, and a CXTB-style projected-book gate for any late investment.
7. **Judge it by within-episode margin and paired-seat wins against rivals like the ladder's, not by bank.** Games are decided by a median of 2,787, about 3% of the bank.

## Appendix: entry points

Kaggle runs the last callable in main.py's namespace.

| Module | Kaggle entry | Note |
|---|---|---|
| nb_tschinkel_2945, nb_nihilistic_robust, nb_tschinkel_metav4_v13 | `agent` | every layer re-pops `agent` to the end |
| nb_haideptry_2965 | `v7_hr_agent` | the file's final line, `agent = kaggle_submission_agent`, passes through to it |
| nb_guru_master_v4 | `_final_sell_block_reorder_entrypoint` | |
| nb_tetsutani_demand, nb_guru_master_v3 | `ig_agent` | `agent` is an inner layer |
| nb_arsgorynich_herdsafe_v3, nb_leoprovorov_forecast | `herdsafe_forecast_agent` | `agent` is an inner layer |
| nb_haideptry_shepherds | `hs4_ig_agent` | |
| nb_dmitrii_herdsafe_2700, nb_statma_herdsafe_ca25 | `opening_liquidity_agent` | `agent` is an inner layer |
| nb_ahmed_v48 | `_e335_agent` | `agent` is the ADV layer (drops preguard, v44y, herd, E334, E335) |
| nb_ahmed_v55 | `final_price_guard` | `agent` drops the price guard |
| nb_leoprovorov_godmode | `main.agent` = `GodModeShopOverlay(base_agent.agent)` | 4-file bundle |
| nb_boatlee_v16rc5, nb_flexonafft_multiroute | a one-argument `agent(obs)` | our module adds an `(observation, configuration=None)` shim |
