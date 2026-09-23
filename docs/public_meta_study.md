# What seven public notebooks actually say, September 2026 meta

Fetched by user request from seven named URLs: ahmedberatozer's v39 and
v34, leoprovorov's reverse-engineering writeup, two of dmitriigluzdov's
agents, shiiin9's order-book notebook, and lynnsakurai's invariant-checked
wrapper. Read for mechanisms and independent confirmation, not copied --
none of this is in J or K's source.

> **CORRECTION, 2026-09-23. None of these seven authors is in the target
> bracket, and none is on the live board.** Searched the 561-tape corpus
> (222 distinct teams, 197 of them rated 2600-2900) and the top 136 live
> teams fetched from the API: aurax7, ahmedberatozer, dmitriigluzdov,
> shiiin9, lynnsakurai, leoprovorov, Hayashi and Tschinkel appear in
> **neither**. The only near-match is "Dmitriy Ulybin" (rank 88, 2754.6),
> a different person.
>
> So the claim below that this lineage is "very likely most of what the
> 2700-2900 bracket is actually running" is an inference that was stated
> as fact and is **not supported by any data in this repo**. These are
> published notebooks of unknown current standing; some may be months
> old. Their mechanisms may still be worth taking -- a good idea does not
> need its author to be ranked -- but nothing here describes the bracket.
> For that, use `tools.analysis.bracket_roster` and the tapes, which name
> the 197 teams actually in the band.

## 1. The whole strong field is one converging lineage

Every one of the six agent-bearing notebooks credits the same chain:
Yusuke Hayashi's ShopRouter -> Thomas Tschinkel's v9/Metav4 -> Ahmed Berat
Ozer's v25-v56 series -> shiiin9's order-book layer -> dmitriigluzdov's
further additions. leoprovorov's own framing: *"Every strong public
release becomes a base for the next participant... the difference between
first place and the thousandth participant may then become very small."*

ahmedberatozer's v39 measures itself at **95.83% win rate against a "Top
field" of 120 games** and 94.43% against "public development" (736 games).
That is not a weak baseline we are chasing -- it is close to the ceiling
of what beats the rest of the field, and it is very likely what a large
share of the 2700-2900 bracket the user is targeting is actually running,
directly or as a lightly-modified fork.

**Implication for J and K:** the highest-leverage target is not a generic
"play better" agent. It is understanding this lineage's specific,
measured weak points (sections 3-4 below) well enough to exploit them,
because that is most of what we will actually face.

## 2. Independent confirmation of two things we found ourselves today

Both landed in our own session before these notebooks were read, and both
show up independently here:

* **Production-night feed timing.** v39's own summary of its additions:
  *"production-calendar feeding, bounded wheat replenishment."* This is
  the same mechanism as our own biggest fix today (+11,047 a game,
  pricing a meal at what it cashes on a production night rather than a
  flat guess).
* **Trim the wheat round-trip, do not maximize or eliminate it.**
  dmitriigluzdov's Herd-Safe notebook: *"reduces the opening wheat round
  trip while retaining five wheat and the planting seed."* We found the
  same shape today from the other direction: a wheat float that BUYS to
  sell loses money on the spread (`_commit_unit` quotes a purchase at
  `market_price(inventory - 1)` and a sale at `market_price(inventory)`),
  so K's float was cut to zero rather than tuned down. Two different
  teams landing on "less wheat trading than the naive amount, but not
  none" from opposite starting points is real corroboration.

Also independently confirmed: **goose escapes remain a real, unsolved
problem even for strong agents.** dmitriigluzdov's herd-safe notebook, on
its OWN selected controller: *"No cow escapes... Goose escapes remained
in 16 of 64 games; winning a game does not mean every livestock route is
correct."* Worth remembering before assuming our own escape counts (6.2 a
game measured earlier today) are simply a bug to stamp out to zero --
some of this may be structurally hard given goose's one-day feed
interval.

## 3. Layer D: the market list is an order book (shiiin9)

**The mechanism, in the notebook's own words:** *"Both players' market
lists are settled together, slot by slot: order 1 of each list, one unit
at a time at the same quote, then order 2, and so on. A unit sold in an
early slot gets a better price than the same unit later, because both
players' earlier sales have already pushed the price down. So the order
of your own list decides who sells into whose glut."*

Layer D replays that lockstep for every placement of the turn's already-
chosen sell orders into the free slots (up to 800 orderings), scored
against a modelled V48-family rival, appended on top of an unmodified
base agent. **Measured: 89 losses turned into wins, 0 wins lost, over
280 games; +124 to +133 coins a game against seven other strong public
agents, uniform regardless of opponent** ("what an ordering layer should
look like: it does not depend on who the rival is").

**We already have most of this, and found a place it was being thrown
away.** `sale_lots` already ranks goods by `loss = revenue lost if a
plausible rival batch lands first` (`ctx["rival_batch"]`), which is the
same principle. But when the turn's sell orders were more than the
market slots remaining, `market_orders` re-sorted them by raw price*qty
and discarded that ranking -- exactly when a crowded, contested turn
makes the ordering matter most. Fixed behind `RACE_AWARE_TRUNCATE`
(rl/candidate_j.py); result pending a clean panel.

**Not built, and worth it later:** the exhaustive 800-ordering replay
against a modelled rival. What we have is a single race-loss sort, not a
true combinatorial search. A cheap intermediate step: a one-pass greedy
re-ordering using `price_at` to simulate the *actual* cumulative price
path or the chosen orders, rather than trusting the linear `loss` proxy.

## 4. The tomato gate (dmitriigluzdov, via v55)

V55 carries a scripted late investment: day 18, buy the SE quadrant,
hire, plant ten tomatoes maturing days 26-29, gated on shop count ("fires
only when three pizza shops or farmers markets are open"). The notebook's
finding: a shop-count gate is a poor proxy, because tomato has the
narrowest price anchor in the game (`T=200`, matching our own
`MARKET_PARAMS["TOMATO"]["T"]` exactly) -- *"eighty units fetch 18,355
coins at an inventory of 9,600 and 1,653 at 10,200."* Their fix: project
the market inventory day by day (town demand, the rival's own visible
tomato tiles, our own output) and price every unit with the engine's own
curve; commit only when the projection clears 9,000 coins. Forcing the
investment regardless "costs 34 wins in 119 games."

J already does something in this direction generically -- `ARRIVAL_PRICING`
values a crop at the book it will meet on its ripening day, not today's --
but this is a sharper, single-crop-specific claim worth verifying against
our own numbers rather than assumed covered.

**Checked, 2026-09-23.** J's own `price_at('TOMATO', ...)` reproduces the
notebook's two numbers exactly: 80 units from an inventory of 9,600 price
at 18,355 coins, and from 10,200 at 1,653 -- bit for bit, no rounding
gap. `MARKET_PARAMS["TOMATO"]` (`T=200`, hinge below, sqrt above) is the
real engine curve, not a guess, so `ARRIVAL_PRICING` already prices this
exact cliff on every crop, continuously, every turn -- not just tomato,
and not on a scripted day-18 trigger. Nothing to fix; the generic
mechanism subsumes the scripted one. Closed.

## 5. Trajectory-matched sale prediction (dmitriigluzdov, "More Wheat, Smarter Sales")

*"The sale predictor now keeps up to three historical opponent
trajectories whose matching scores are within one point of the strongest
trajectory... If any retained trajectory predicts a substantial milk,
wool or strawberry sale in the next two turns, the controller can bring
forward an already planned sale."*

This is a more general version of leoprovorov's "mirror gate" idea (which
assumes the rival runs the same code as us): instead of assuming a
mirror, match the CURRENT game's observed opponent behaviour so far
against a LIBRARY of previously-recorded trajectories, and act on
whichever past games it currently resembles most.

**This is directly buildable with what we already have.** The 1,800+
tape corpus IS that trajectory library. Not yet built: a similarity
metric between a live game's observed opponent state and each recorded
tape's state at the same step, and a lookup that returns "what did the
closest-matching tapes sell next." A natural next research task, and one
neither J nor K currently has any version of.

## 6. The safety-invariant wrapper pattern (lynnsakurai)

Terse, formal notebook: a frozen "parent" route with explicit invariant
checks bolted on, e.g. *"the temporary crop is valid only when tile (2,4)
contains the expected day-0 wheat... ambiguous states fall back to the
parent action."* Also a resource-bound formula capping aggregate seed
purchases against a *shared* upper bound on remaining plantable ground,
"deliberately using a shared bound rather than a per-crop forecast, so
later substitutions retain enough flexibility" -- and a fertilizer-
omission proof: skip fertilizing when the predicted yield under any
remaining coverage window is provably unchanged.

**The transferable idea, not the specific hardcoded tile/step numbers:**
K currently cannot touch H2 at all without desyncing it -- moving a
single hand via an unconditional override cost 90,409 against 184,922
(measured earlier tonight). This notebook's whole architecture is the
answer to that: check whether the live game still matches what the
frozen route's plan assumed (right crop on the right tile, worker where
expected) *before* substituting anything, and defer to the parent's own
action otherwise. That is a real, different way to build on H2 without
breaking it, distinct from every "give H2 extra hires" or "let H2's idle
hands work" attempt tried and rejected tonight. Not started -- flagged as
the primary next research direction for K.

## Open items, in the order they are worth picking up

1. **RACE_AWARE_TRUNCATE** -- implemented, needs a clean (non-contaminated)
   panel result.
2. **WIND_DOWN_DAYS** -- implemented from leoprovorov's day-27 finding,
   needs a clean panel result. Note dmitriigluzdov's herd-safe notebook
   uses a much narrower "final seven turns" window for its own bounded
   endgame planner -- there is no single agreed answer across the field,
   worth sweeping a wide range (1 day through 5) rather than assuming 3.
3. **Trajectory-matched sale prediction** -- not started. Buildable now
   from the existing tape corpus.
4. **Safety-invariant wrapper for K** -- not started, the real path to
   "K better than H2," not just "K equals H2."
5. ~~The tomato gate's specific claim~~ -- checked 2026-09-23, confirmed
   already subsumed by `ARRIVAL_PRICING`. Closed, no fix needed.
