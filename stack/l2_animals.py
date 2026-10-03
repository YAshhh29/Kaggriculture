"""L2 animals layer: drop the FEEDs that provably buy nothing.

On exact replays of L's live games about 7.6 FEEDs a game buy nothing: no CARE
that can still be paid, no bank to pay out tonight, and no risk of an escape
(mostly young cows whose CARE bank already fills the first production, and
feeds on day 28, whose CARE nothing can pay).

Rule (engine-exact): keep a FEED if the animal was unfed yesterday, tonight's
refresh pays out a bank, a payable CARE is due today, or the parent's route
does not feed the tile tomorrow; otherwise replace it with COLLECT_FERTILIZER
when one is available, else PASS. Market orders and crop tiles are never
touched, and any error returns the parent's action unchanged.
"""

from __future__ import annotations

import time

from stack.candidate_l import l_stack

_AN = {"GOOSE": (4, 1, 4), "COW": (8, 2, 6), "SHEEP": (6, 3, 6)}  # first, interval, max_held
LAST_REFRESH = 28


def _produces(tile, q):
    """Production at the refresh at the end of day q."""
    first, interval, _ = _AN[tile["animal"]]
    since = q + 1 - int(tile.get("placed_day", 0)) - first
    return since >= 0 and since % interval == 0


def care_payable(tile, day):
    """Would a CARE banked today ever be paid (ignoring later harvest caps)?"""
    first, _, cap = _AN[tile["animal"]]
    first_refresh = int(tile.get("placed_day", 0)) + first - 1
    bank = int(tile.get("pending_care_bonus", 0) or 0)
    if day < first_refresh and bank >= cap - 1:
        return False          # the bank already fills the first production
    return any(_produces(tile, q) for q in range(day + 1, LAST_REFRESH + 1))


def feed_useful(tile, day, cared_today, feeds_tomorrow):
    """Engine-exact: does a FEED today buy anything?"""
    if day > LAST_REFRESH:
        return False                          # no refresh left
    if int(tile.get("consecutive_unfed", 0)) >= 1:
        return True                           # would escape tonight
    bank = int(tile.get("pending_care_bonus", 0) or 0)
    if bank > 0 and _produces(tile, day):
        return True                           # tonight's payout needs it
    if cared_today and care_payable(tile, day):
        return True
    if day < LAST_REFRESH and not feeds_tomorrow:
        return True                           # skipping would risk an escape
    return False


def an_wrap(parent, env, report=None):
    report = report if report is not None else {}
    for k in ("an_feed_skips", "an_feed_skips_d28", "an_feed_skips_young",
              "an_collect_swaps", "an_errors", "an_max_ms"):
        report.setdefault(k, 0)
    visits_today = env.get("_ch_visits_today")
    next_feed = env.get("_r86_next_feed")

    def agent(observation, configuration=None):
        action = parent(observation, configuration)
        started = time.perf_counter()
        try:
            if not isinstance(action, dict):
                return action
            step = int(observation["step"])
            day = step // 24
            if step > 717:
                return action
            seat = int(observation["player"])
            farm = observation["farms"][seat]
            positions = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
            units = [list(action.get("farmer") or ["PASS"])] + \
                [list(c) if c else ["PASS"] for c in (action.get("hands") or [])]
            if not any(u and u[0] == "FEED" for u in units):
                return action
            later = None
            changed = False
            for i, cmd in enumerate(units):
                if not cmd or cmd[0] != "FEED" or i >= len(positions):
                    continue
                x, y = positions[i]
                tile = farm["tiles"][y][x]
                if not (isinstance(tile, dict) and tile.get("animal") in _AN):
                    continue
                if tile.get("fed_today"):
                    continue
                inv = observation["private"]["inventories"][i] \
                    if i < len(observation["private"]["inventories"]) else {}
                if int(inv.get("WHEAT", 0)) <= 0:
                    continue                  # engine no-op anyway
                cared = bool(tile.get("cared_today")) or any(
                    j != i and positions[j] == (x, y) and units[j][:1] == ["CARE"]
                    for j in range(min(len(units), len(positions))))
                if not cared:
                    if later is None:
                        later = visits_today(observation, action) if visits_today else {}
                    cared = any(op == "CARE" for _, op in later.get((x, y), []))
                if day < LAST_REFRESH:
                    tomorrow = bool(next_feed(observation, (x, y))) if next_feed else False
                else:
                    tomorrow = True
                if feed_useful(tile, day, cared, tomorrow):
                    continue
                if tile.get("fertilizer_available"):
                    units[i] = ["COLLECT_FERTILIZER"]
                    report["an_collect_swaps"] += 1
                else:
                    units[i] = ["PASS"]
                report["an_feed_skips"] += 1
                if day >= LAST_REFRESH:
                    report["an_feed_skips_d28"] += 1
                elif day < int(tile.get("placed_day", 0)) + _AN[tile["animal"]][0] - 1:
                    report["an_feed_skips_young"] += 1
                changed = True
            if changed:
                action = dict(action, farmer=units[0], hands=units[1:])
        except Exception:
            report["an_errors"] += 1
        finally:
            ms = (time.perf_counter() - started) * 1000.0
            if ms > report["an_max_ms"]:
                report["an_max_ms"] = round(ms, 2)
        return action

    agent.telemetry = report
    return agent


def build():
    """Agent L plus the FEED trim (inner layer, before market_front)."""
    report = {}

    def inner(agent, env):
        return an_wrap(agent, env, report)

    return l_stack(inner=inner)
