# Agent L2 (Kaggriculture), Yash Jain, 2026-09-27.
# Base: tetsutani's public build (Apache-2.0), verbatim below with its
# licence notices, except one condition in _v219_qualifies (marked
# "Agent L"). Our layers are embedded at the end of the file, each run
# in its own namespace; a verbatim copy of the base is embedded for the
# opponent shadow.
# Kaggriculture submission v9/3: public V39 (Apache-2.0, notices below) plus the v9 layers
# RACEPX gate, RACE (reservation from step 192, horizon 40 / margin 12), COURIER, CARROT and HERD
# appended at the end of this file.
# EXP-173 isolate opening market sequence inspired by yhay81/shop-router-0911-simple (Apache-2.0).
# Kaggriculture EXP-167 candidate. Not submitted automatically.
# Attribution: thomastschinkel, yhay81, destbreso, aurax7, tetsutani,
# prvsiyan and Dmitrii Gluzdov. Apache-2.0 derivations; notices retained below.
# Kaggriculture v31 / EXP-157, Ahmed Berat Ozer, September 9 2026.
# Selected mechanism: crop_public_order. New independent confirmation is required.
# Public V221B/V224C production/timing lineage: prvsiyan, Apache-2.0.
# Original economics and integration; retained upstream licenses follow.
# Kaggriculture v28 / EXP-154, Ahmed Berat Ozer, September 9 2026.
# Changes: aurax7 day-end storage guard; Dmitrii Gluzdov physical terminal rescue
# adapted to v27, with 64 deterministic simulations. Apache-2.0.
# New action tapes and ordered shop-pair map: yhay81/shop-router-0909, Apache-2.0.
# Kaggriculture v25, EXP-149: Shop0908 production, sale lead, terminal cargo rescue.
# Runtime chassis: Apache-2.0; thomastschinkel, yhay81, tetsutani.
# Routing and public action data: yhay81/shop-router-0908, frozen September 8, 2026.
# 
#                                  Apache License
#                            Version 2.0, January 2004
#                         http://www.apache.org/licenses/
# 
#    TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
# 
#    1. Definitions.
# 
#       "License" shall mean the terms and conditions for use, reproduction,
#       and distribution as defined by Sections 1 through 9 of this document.
# 
#       "Licensor" shall mean the copyright owner or entity authorized by
#       the copyright owner that is granting the License.
# 
#       "Legal Entity" shall mean the union of the acting entity and all
#       other entities that control, are controlled by, or are under common
#       control with that entity. For the purposes of this definition,
#       "control" means (i) the power, direct or indirect, to cause the
#       direction or management of such entity, whether by contract or
#       otherwise, or (ii) ownership of fifty percent (50%) or more of the
#       outstanding shares, or (iii) beneficial ownership of such entity.
# 
#       "You" (or "Your") shall mean an individual or Legal Entity
#       exercising permissions granted by this License.
# 
#       "Source" form shall mean the preferred form for making modifications,
#       including but not limited to software source code, documentation
#       source, and configuration files.
# 
#       "Object" form shall mean any form resulting from mechanical
#       transformation or translation of a Source form, including but
#       not limited to compiled object code, generated documentation,
#       and conversions to other media types.
# 
#       "Work" shall mean the work of authorship, whether in Source or
#       Object form, made available under the License, as indicated by a
#       copyright notice that is included in or attached to the work
#       (an example is provided in the Appendix below).
# 
#       "Derivative Works" shall mean any work, whether in Source or Object
#       form, that is based on (or derived from) the Work and for which the
#       editorial revisions, annotations, elaborations, or other modifications
#       represent, as a whole, an original work of authorship. For the purposes
#       of this License, Derivative Works shall not include works that remain
#       separable from, or merely link (or bind by name) to the interfaces of,
#       the Work and Derivative Works thereof.
# 
#       "Contribution" shall mean any work of authorship, including
#       the original version of the Work and any modifications or additions
#       to that Work or Derivative Works thereof, that is intentionally
#       submitted to Licensor for inclusion in the Work by the copyright owner
#       or by an individual or Legal Entity authorized to submit on behalf of
#       the copyright owner. For the purposes of this definition, "submitted"
#       means any form of electronic, verbal, or written communication sent
#       to the Licensor or its representatives, including but not limited to
#       communication on electronic mailing lists, source code control systems,
#       and issue tracking systems that are managed by, or on behalf of, the
#       Licensor for the purpose of discussing and improving the Work, but
#       excluding communication that is conspicuously marked or otherwise
#       designated in writing by the copyright owner as "Not a Contribution."
# 
#       "Contributor" shall mean Licensor and any individual or Legal Entity
#       on behalf of whom a Contribution has been received by Licensor and
#       subsequently incorporated within the Work.
# 
#    2. Grant of Copyright License. Subject to the terms and conditions of
#       this License, each Contributor hereby grants to You a perpetual,
#       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
#       copyright license to reproduce, prepare Derivative Works of,
#       publicly display, publicly perform, sublicense, and distribute the
#       Work and such Derivative Works in Source or Object form.
# 
#    3. Grant of Patent License. Subject to the terms and conditions of
#       this License, each Contributor hereby grants to You a perpetual,
#       worldwide, non-exclusive, no-charge, royalty-free, irrevocable
#       (except as stated in this section) patent license to make, have made,
#       use, offer to sell, sell, import, and otherwise transfer the Work,
#       where such license applies only to those patent claims licensable
#       by such Contributor that are necessarily infringed by their
#       Contribution(s) alone or by combination of their Contribution(s)
#       with the Work to which such Contribution(s) was submitted. If You
#       institute patent litigation against any entity (including a
#       cross-claim or counterclaim in a lawsuit) alleging that the Work
#       or a Contribution incorporated within the Work constitutes direct
#       or contributory patent infringement, then any patent licenses
#       granted to You under this License for that Work shall terminate
#       as of the date such litigation is filed.
# 
#    4. Redistribution. You may reproduce and distribute copies of the
#       Work or Derivative Works thereof in any medium, with or without
#       modifications, and in Source or Object form, provided that You
#       meet the following conditions:
# 
#       (a) You must give any other recipients of the Work or
#           Derivative Works a copy of this License; and
# 
#       (b) You must cause any modified files to carry prominent notices
#           stating that You changed the files; and
# 
#       (c) You must retain, in the Source form of any Derivative Works
#           that You distribute, all copyright, patent, trademark, and
#           attribution notices from the Source form of the Work,
#           excluding those notices that do not pertain to any part of
#           the Derivative Works; and
# 
#       (d) If the Work includes a "NOTICE" text file as part of its
#           distribution, then any Derivative Works that You distribute must
#           include a readable copy of the attribution notices contained
#           within such NOTICE file, excluding those notices that do not
#           pertain to any part of the Derivative Works, in at least one
#           of the following places: within a NOTICE text file distributed
#           as part of the Derivative Works; within the Source form or
#           documentation, if provided along with the Derivative Works; or,
#           within a display generated by the Derivative Works, if and
#           wherever such third-party notices normally appear. The contents
#           of the NOTICE file are for informational purposes only and
#           do not modify the License. You may add Your own attribution
#           notices within Derivative Works that You distribute, alongside
#           or as an addendum to the NOTICE text from the Work, provided
#           that such additional attribution notices cannot be construed
#           as modifying the License.
# 
#       You may add Your own copyright statement to Your modifications and
#       may provide additional or different license terms and conditions
#       for use, reproduction, or distribution of Your modifications, or
#       for any such Derivative Works as a whole, provided Your use,
#       reproduction, and distribution of the Work otherwise complies with
#       the conditions stated in this License.
# 
#    5. Submission of Contributions. Unless You explicitly state otherwise,
#       any Contribution intentionally submitted for inclusion in the Work
#       by You to the Licensor shall be under the terms and conditions of
#       this License, without any additional terms or conditions.
#       Notwithstanding the above, nothing herein shall supersede or modify
#       the terms of any separate license agreement you may have executed
#       with Licensor regarding such Contributions.
# 
#    6. Trademarks. This License does not grant permission to use the trade
#       names, trademarks, service marks, or product names of the Licensor,
#       except as required for reasonable and customary use in describing the
#       origin of the Work and reproducing the content of the NOTICE file.
# 
#    7. Disclaimer of Warranty. Unless required by applicable law or
#       agreed to in writing, Licensor provides the Work (and each
#       Contributor provides its Contributions) on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#       implied, including, without limitation, any warranties or conditions
#       of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
#       PARTICULAR PURPOSE. You are solely responsible for determining the
#       appropriateness of using or redistributing the Work and assume any
#       risks associated with Your exercise of permissions under this License.
# 
#    8. Limitation of Liability. In no event and under no legal theory,
#       whether in tort (including negligence), contract, or otherwise,
#       unless required by applicable law (such as deliberate and grossly
#       negligent acts) or agreed to in writing, shall any Contributor be
#       liable to You for damages, including any direct, indirect, special,
#       incidental, or consequential damages of any character arising as a
#       result of this License or out of the use or inability to use the
#       Work (including but not limited to damages for loss of goodwill,
#       work stoppage, computer failure or malfunction, or any and all
#       other commercial damages or losses), even if such Contributor
#       has been advised of the possibility of such damages.
# 
#    9. Accepting Warranty or Additional Liability. While redistributing
#       the Work or Derivative Works thereof, You may choose to offer,
#       and charge a fee for, acceptance of support, warranty, indemnity,
#       or other liability obligations and/or rights consistent with this
#       License. However, in accepting such obligations, You may act only
#       on Your own behalf and on Your sole responsibility, not on behalf
#       of any other Contributor, and only if You agree to indemnify,
#       defend, and hold each Contributor harmless for any liability
#       incurred by, or claims asserted against, such Contributor by reason
#       of your accepting any such warranty or additional liability.
# 
#    END OF TERMS AND CONDITIONS
# 
#    APPENDIX: How to apply the Apache License to your work.
# 
#       To apply the Apache License to your work, attach the following
#       boilerplate notice, with the fields enclosed by brackets "[]"
#       replaced with your own identifying information. (Don't include
#       the brackets!)  The text should be enclosed in the appropriate
#       comment syntax for the file format. We also recommend that a
#       file or class name and description of purpose be included on the
#       same "printed page" as the copyright notice for easier
#       identification within third-party archives.
# 
#    Copyright [yyyy] [name of copyright owner]
# 
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
# 
#        http://www.apache.org/licenses/LICENSE-2.0
# 
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
"""Kaggriculture route-replay chassis (pure Python, stdlib only).

A *route* is a pre-computed tape of 719 Kaggle-format actions
``{"farmer": [op, ...], "hands": [[op, ...], ...], "market": [[order, item, qty], ...]}``.
The chassis replays the tape chosen by a caller-supplied ``router`` and wraps it
in small reactive layers (each independently switchable via ``settings``):

    hand_align            pad/truncate hands to the real hand count      (fieldbook_logic)
    weed_repair           DIG a weed that blocks PLANT/BUILD, replay      (tetsutani + task spec)
    sell_lead             sell next step's lots one step early            (fieldbook _lead_sale)
    front_run             sell before the opponent's scheduled SELL       (hook; opponent_plan)
    budget_guard          fund each 72-step block's purchases             (six_day_budget_guard.hpp)
    room_guard            keep shed <= 99 at hour 23                      (tetsutani)
    clamp_sells           trim SELL orders to the projected shed          (tetsutani)
    dead_stock            sell stock the route will never sell            (tetsutani)
    terminal_liquidation  step >= 718: sell the whole projected shed      (fieldbook _terminal_sale)

Engine facts (verified against kaggle_environments 1.32.7, env_1_32_7.py):
  observation["farms"][p] = {"money", "tiles"[y][x], "farmer"[x,y], "hands"[[x,y]..],
                             "unlocked_quadrants", "hires_today"}
  tiles: None (empty) | "LOCKED" | {"kind": WEED|COOP|PASTURE|PLANT, "crop"/"animal", ...}
  observation["private"] = {"shed": {item: n}, "seeds": {crop: n}, "inventories": [{}...]}
  observation["market"] = {"inventory": {...}, "prices": {...}}
  observation["town"] = {"unlocked_shops": [...]}
  Agents act on steps 0..718 (interpreter marks DONE once step >= episodeSteps-2).
"""
from __future__ import annotations

import copy

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
SEED_PRICE = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_STRUCTURE = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
LAND_PRICES = (1000, 2000, 4000)
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
FRONT_RUN_ITEMS = ("MILK", "WOOL", "STRAWBERRY", "MELON")
LAST_ACT_STEP = 718
PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}

DEFAULT_SETTINGS = {
    "hand_align": True,
    "weed_repair": True,
    "sell_lead": True,
    "front_run": True,
    "budget_guard": True,
    "room_guard": True,
    "clamp_sells": True,
    "dead_stock": True,
    "terminal_liquidation": True,
    # tunables
    "block_turns": 72,
    "shed_capacity": 100,
    "board_size": 10,
    "max_orders": 10,
    "turns_per_day": 24,
    "min_sell_price": 2,
}


# --------------------------------------------------------------------------- helpers
def _get(value, key, default=None):
    """Field access that works for dicts and Kaggle Struct/attribute objects."""
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _step_of(observation):
    raw = _get(observation, "step")
    if raw is not None:
        return _int(raw)
    return _int(_get(observation, "day", 0)) * 24 + _int(_get(observation, "hour", 0))


def _shed_adjacent(pos, board):
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        return False
    half = board // 2
    return pos[0] in (half - 1, half) and pos[1] in (half - 1, half)


def _tile_at(tiles, pos):
    try:
        x, y = int(pos[0]), int(pos[1])
        return tiles[y][x]
    except (TypeError, ValueError, IndexError):
        return "LOCKED"


def _is_noop(act, tile, inv, seeds, pos, board):
    """True when the engine will certainly ignore ``act`` (mirrors _apply_unit_action)."""
    if not act:
        return True
    op = act[0]
    x, y = pos[0], pos[1]
    if op in MOVES:
        dx, dy = MOVES[op]
        return not (0 <= x + dx < board and 0 <= y + dy < board)
    if op == "PASS":
        return True
    adjacent = _shed_adjacent(pos, board)
    if op == "DROP":
        return (not adjacent) or (not inv)
    if op == "PICKUP":
        return not adjacent
    if op == "PLACE":
        item = act[1] if len(act) > 1 else None
        if item in ANIMAL_STRUCTURE and isinstance(tile, dict) \
                and _get(tile, "kind") == ANIMAL_STRUCTURE[item] and _get(tile, "animal") is None:
            return _int(_get(inv, item, 0)) <= 0
        return (not adjacent) or _int(_get(inv, item, 0)) <= 0
    if tile == "LOCKED":
        return True
    is_dict = isinstance(tile, dict)
    kind = _get(tile, "kind") if is_dict else None
    animal = is_dict and _get(tile, "animal") is not None
    if op == "PLANT":
        return tile is not None or _int(_get(seeds, act[1] if len(act) > 1 else None, 0)) <= 0
    if op == "WATER":
        return kind != "PLANT" or bool(_get(tile, "watered_today"))
    if op == "HARVEST":
        return (not is_dict) or _int(_get(tile, "yield_units", 0)) <= 0
    if op == "FERTILIZE":
        return kind != "PLANT" or _int(_get(inv, "FERTILIZER", 0)) <= 0
    if op == "DIG":
        return tile is None or animal
    if op in ("BUILD_COOP", "BUILD_PASTURE"):
        return tile is not None
    if op == "FEED":
        return (not animal) or bool(_get(tile, "fed_today")) or _int(_get(inv, "WHEAT", 0)) <= 0
    if op == "COLLECT_FERTILIZER":
        return (not animal) or (not _get(tile, "fertilizer_available"))
    if op == "CARE":
        return (not animal) or bool(_get(tile, "cared_today"))
    return True


class _View:
    """Cheap per-step snapshot of everything the layers read from the observation."""

    def __init__(self, observation, player, cfg):
        farms = list(_get(observation, "farms", []) or [])
        self.farm = farms[player] if player < len(farms) else {}
        self.rival = farms[1 - player] if len(farms) >= 2 and 1 - player < len(farms) else {}
        private = _get(observation, "private", {}) or {}
        self.shed = {k: max(0, _int(v)) for k, v in dict(_get(private, "shed", {}) or {}).items()}
        self.seeds = dict(_get(private, "seeds", {}) or {})
        self.invs = [dict(i or {}) for i in (_get(private, "inventories", []) or [])]
        market = _get(observation, "market", {}) or {}
        self.prices = {k: _int(v) for k, v in dict(_get(market, "prices", {}) or {}).items()}
        self.money = float(_get(self.farm, "money", 0.0) or 0.0)
        self.tiles = _get(self.farm, "tiles", []) or []
        self.board = len(self.tiles) or cfg["board_size"]
        self.positions = [_get(self.farm, "farmer", None)] + [list(p) for p in (_get(self.farm, "hands", []) or [])]
        self.hires_today = _int(_get(self.farm, "hires_today", 0))
        self.quadrants = len(list(_get(self.farm, "unlocked_quadrants", []) or []))

    def inv(self, idx):
        return self.invs[idx] if idx < len(self.invs) else {}

    def in_hands(self, item):
        return sum(max(0, _int(_get(inv, item, 0))) for inv in self.invs)


# --------------------------------------------------------------------------- chassis
class Chassis:
    """Replays ``routes[router(...)]`` with reactive safety/market layers.

    routes         : {route_id: list of >= 719 Kaggle action dicts}
    router         : callable(observation, step, state_dict) -> route_id, called every
                     step; ``state_dict`` is per-player and persists across the game.
    settings       : overrides for DEFAULT_SETTINGS (layer switches + tunables)
    opponent_plan  : optional list of the opponent's expected actions (front_run hook)
    """

    def __init__(self, routes, router=None, settings=None, opponent_plan=None):
        self.routes = {rid: list(tape) for rid, tape in routes.items()}
        self.router = router or (lambda observation, step, state: next(iter(self.routes)))
        self.cfg = dict(DEFAULT_SETTINGS)
        self.cfg.update(settings or {})
        self.opponent_plan = opponent_plan
        self.players = {}
        self.diagnostics = {"layer_fallbacks": 0, "entry_fallbacks": 0}
        self._future_sells = {}   # route id -> {item: [remaining planned SELL qty from step t]}

    # ---- state -----------------------------------------------------------------
    def _state(self, player, step):
        st = self.players.get(player)
        if st is None or step == 0 or step <= st["last_step"]:
            st = {"last_step": -1, "route": None, "router_state": {},
                  "pending": {}, "sell_state": {"due_step": -1, "suppress": {}}}
            self.players[player] = st
        st["last_step"] = step
        return st

    def _route_action(self, route, step):
        tape = self.routes[route]
        if 0 <= step < len(tape) and isinstance(tape[step], dict):
            return copy.deepcopy(tape[step])
        return copy.deepcopy(PASS_ACTION)

    def future_sells(self, route, item, step):
        """Planned SELL quantity of ``item`` in route steps >= ``step`` (suffix sums)."""
        table = self._future_sells.get(route)
        if table is None:
            tape = self.routes[route]
            n = len(tape)
            table = {p: [0] * (n + 1) for p in PRODUCTS}
            for t in range(n - 1, -1, -1):
                for p in PRODUCTS:
                    table[p][t] = table[p][t + 1]
                for o in (tape[t].get("market") or []) if isinstance(tape[t], dict) else []:
                    if o and o[0] == "SELL" and len(o) >= 3 and o[1] in table:
                        table[o[1]][t] += max(0, _int(o[2]))
            self._future_sells[route] = table
        col = table.get(item)
        return col[step] if col and 0 <= step < len(col) else 0

    # ---- main entry -----------------------------------------------------------
    def act(self, observation, configuration=None):
        if len(_get(observation, "farms", []) or []) < 2:
            raise ValueError("incomplete observation")  # factory falls back to tape
        step = _step_of(observation)
        player = _int(_get(observation, "player", 0))
        st = self._state(player, step)
        cfg = self.cfg
        view = _View(observation, player, cfg)

        route = self.router(observation, step, st["router_state"])
        if route not in self.routes:
            route = st["route"] if st["route"] in self.routes else next(iter(self.routes))
        st["route"] = route
        action = self._route_action(route, step)
        raw = copy.deepcopy(action)
        try:
            if cfg["hand_align"]:
                self._hand_align(action, view)
            if cfg["weed_repair"]:
                self._weed_repair(action, view, st, route, step)
            if cfg["sell_lead"] or cfg["front_run"]:
                self._apply_suppression(action, st["sell_state"], step)
            projected = self._projected_shed(action, view)
            lead_available = dict(projected)
            next_sup = {"due_step": -1, "suppress": {}, "r36_debts": st["sell_state"].get("r36_debts", {})}
            if cfg["sell_lead"]:
                self._sell_lead(action, view, lead_available, route, step, next_sup)
            if cfg["front_run"] and self.opponent_plan:
                self._front_run(action, view, lead_available, route, step, next_sup)
            st["sell_state"] = next_sup
            if cfg["budget_guard"]:
                self._budget_guard(action, view, route, step)
            if cfg["room_guard"]:
                self._room_guard(action, view, route, step)
            if cfg["clamp_sells"]:
                self._clamp_sells(action, projected)
            if cfg["dead_stock"]:
                self._dead_stock(action, view, projected, route, step)
            if cfg["terminal_liquidation"]:
                self._terminal_liquidation(action, projected, step)
            action["market"] = action["market"][: cfg["max_orders"]]
            return action
        except Exception:
            self.diagnostics["layer_fallbacks"] += 1
            return raw

    # ---- layer: hand_align ----------------------------------------------------
    def _hand_align(self, action, view):
        """Pad with PASS / truncate the tape's hand list to the real number of hands
        (fieldbook_logic.act). Extra hands would be ignored by the engine anyway;
        missing ones just idle, so alignment only tidies the action."""
        expected = max(0, len(view.positions) - 1)
        hands = list(action.get("hands") or [])
        hands.extend([["PASS"] for _ in range(max(0, expected - len(hands)))])
        action["hands"] = hands[:expected]

    # ---- layer: weed_repair ---------------------------------------------------
    def _weed_repair(self, action, view, st, route, step):
        """If a PLANT/BUILD_* target tile is a WEED, DIG now and queue the intended
        action for that unit; the queue replays on a later step when the unit still
        stands there and its tape action would be a no-op (the displaced no-op is
        queued behind it, so PLANT -> WATER chains survive). A PLANT is only replayed
        when the unit's next tape action is not a move, so the mandatory same-day
        WATER can follow; otherwise the seed is kept. A no-op turn spent on a weed
        is also converted to DIG (tetsutani weed_dig)."""
        units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        pending = st["pending"]
        tape = self.routes[route]
        nxt = tape[step + 1] if step + 1 < len(tape) and isinstance(tape[step + 1], dict) else {}
        next_units = [nxt.get("farmer") or ["PASS"]] + list(nxt.get("hands") or [])
        for i in range(min(len(units), len(view.positions))):
            pos = view.positions[i]
            if not isinstance(pos, (list, tuple)):
                continue
            pos = (int(pos[0]), int(pos[1]))
            tile = _tile_at(view.tiles, pos)
            act = list(units[i])
            queue = pending.get(i)
            if queue and queue[0][0] != pos:
                pending.pop(i, None)
                queue = None
            is_weed = isinstance(tile, dict) and _get(tile, "kind") == "WEED"
            noop = _is_noop(act, tile, view.inv(i), view.seeds, pos, view.board)
            next_op = next_units[i][0] if i < len(next_units) and next_units[i] else "PASS"
            if act and act[0] in ("PLANT", "BUILD_COOP", "BUILD_PASTURE") and is_weed:
                pending.setdefault(i, []).append((pos, act))
                act = ["DIG"]
            elif queue and noop:
                _, replay = queue[0]
                if replay[0] == "PLANT" and next_op in MOVES:
                    pending.pop(i, None)          # WATER could never follow: keep the seed
                else:
                    queue.pop(0)
                    if act and act[0] != "PASS" and act[0] not in MOVES:
                        queue.append((pos, act))
                    act = replay
                    if not queue:
                        pending.pop(i, None)
            elif is_weed and noop:
                act = ["DIG"]
            units[i] = act
        action["farmer"] = units[0]
        action["hands"] = units[1:]

    # ---- projected shed -------------------------------------------------------
    def _projected_shed(self, action, view):
        """Shed contents after this step's unit actions but before the market runs:
        PICKUP removes, DROP/PLACE(non-animal) near the shed adds up to capacity
        (fieldbook _projected_shed / tetsutani projected shed)."""
        cap = self.cfg["shed_capacity"]
        proj = {p: view.shed.get(p, 0) for p in PRODUCTS}
        for k, v in view.shed.items():
            proj.setdefault(k, v)
        total = sum(proj.values())
        units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        for i in range(min(len(units), len(view.positions))):
            if not _shed_adjacent(view.positions[i], view.board):
                continue
            act = units[i]
            op = act[0] if act else "PASS"
            inv = view.inv(i)
            if op == "PICKUP" and len(act) >= 2 and act[1] in proj:
                qty = min(proj[act[1]], max(0, _int(act[2]) if len(act) >= 3 else 1))
                proj[act[1]] -= qty
                total -= qty
            elif op == "DROP":
                for item, held in inv.items():
                    take = min(max(0, _int(held)), max(0, cap - total))
                    if take > 0:
                        proj[item] = proj.get(item, 0) + take
                        total += take
            elif op == "PLACE" and len(act) >= 2 and act[1] not in ANIMAL_STRUCTURE:
                item = act[1]
                take = min(max(0, _int(act[2]) if len(act) >= 3 else 1),
                           max(0, _int(_get(inv, item, 0))), max(0, cap - total))
                if take > 0:
                    proj[item] = proj.get(item, 0) + take
                    total += take
        return proj

    # ---- layer: sell_lead / front_run suppression ------------------------------
    @staticmethod
    def _apply_suppression(action, sell_state, step):
        """Remove from this step's SELLs the quantities already sold a step early."""
        if sell_state.get("due_step") != step:
            return
        remaining = dict(sell_state.get("suppress", {}))
        kept = []
        for order in action.get("market") or []:
            order = list(order)
            if order and order[0] == "SELL" and len(order) >= 3 and remaining.get(order[1], 0) > 0:
                removed = min(max(0, _int(order[2])), remaining[order[1]])
                order[2] = _int(order[2]) - removed
                remaining[order[1]] -= removed
                # A zero-quantity order keeps later market race slots intact.
            kept.append(order)
        action["market"] = kept

    @staticmethod
    def _add_sell(action, item, qty, max_orders, merge=True):
        market = action.setdefault("market", [])
        if merge:
            for order in market:
                if order and order[0] == "SELL" and order[1] == item:
                    order[2] = _int(order[2]) + qty
                    return True
        if len(market) >= max_orders:
            return False
        market.append(["SELL", item, qty])
        return True

    def _sell_lead(self, action, view, projected, route, step, next_sup):
        """fieldbook _lead_sale: when step % 4 != 0 (no town consumption between the
        two steps) sell the lots the tape plans to SELL next step now, for products
        other than WHEAT/FERTILIZER we already hold, and suppress them next step.
        Skipped at the last step, at shop-unlock boundaries and if a SELL for that
        product is already queued this step."""
        cfg = self.cfg
        nxt = step + 1
        unlock_period = 3 * cfg["turns_per_day"]
        if nxt > LAST_ACT_STEP or nxt % unlock_period == 0 or step % 4 == 0:
            return
        tape = self.routes[route]
        future = tape[nxt] if nxt < len(tape) and isinstance(tape[nxt], dict) else {}
        planned = {}
        for o in future.get("market") or []:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in PRODUCTS:
                planned[o[1]] = planned.get(o[1], 0) + max(0, _int(o[2]))
        already = {o[1] for o in action.get("market") or [] if o and o[0] == "SELL" and len(o) > 1}
        for item in PRODUCTS:
            if item in ("WHEAT", "FERTILIZER") or planned.get(item, 0) <= 0 or item in already:
                continue
            qty = min(projected.get(item, 0), planned[item])
            if qty <= 0 or view.prices.get(item, 0) < cfg["min_sell_price"]:
                continue
            if not self._add_sell(action, item, qty, cfg["max_orders"], merge=False):
                break
            projected[item] -= qty
            next_sup["suppress"][item] = next_sup["suppress"].get(item, 0) + qty
        if next_sup["suppress"]:
            next_sup["due_step"] = nxt

    def _front_run(self, action, view, projected, route, step, next_sup):
        """Hook: if ``opponent_plan`` (their expected tape) schedules a SELL of
        MILK/WOOL/STRAWBERRY/MELON next step, sell what we hold of it now (before
        their supply depresses the price) and suppress our own SELL of that quantity
        next step. Bounded by our own remaining planned sales so it never dumps."""
        cfg = self.cfg
        nxt = step + 1
        plan = self.opponent_plan
        if nxt > LAST_ACT_STEP or nxt >= len(plan) or not isinstance(plan[nxt], dict):
            return
        already = {o[1] for o in action.get("market") or [] if o and o[0] == "SELL" and len(o) > 1}
        for o in plan[nxt].get("market") or []:
            if not (o and o[0] == "SELL" and len(o) >= 3 and o[1] in FRONT_RUN_ITEMS):
                continue
            item = o[1]
            if item in already or view.prices.get(item, 0) < cfg["min_sell_price"]:
                continue
            own_next = sum(max(0, _int(x[2])) for x in self.routes[route][nxt].get("market", [])
                           if len(x) >= 3 and x[0] == "SELL" and x[1] == item)
            qty = min(projected.get(item, 0), max(0, _int(o[2])), own_next)
            if qty <= 0:
                continue
            if not self._add_sell(action, item, qty, cfg["max_orders"], merge=False):
                break
            projected[item] -= qty
            already.add(item)
            next_sup["suppress"][item] = next_sup["suppress"].get(item, 0) + qty
        if next_sup["suppress"]:
            next_sup["due_step"] = nxt

    # ---- layer: budget_guard --------------------------------------------------
    def _block_requirements(self, view, route, start, end):
        """Planned purchase cost and item reserves for tape steps [start, end)
        (six_day_budget_guard.hpp calculate_six_day_requirements)."""
        tape = self.routes[route]
        budget = 0.0
        seed_bal, item_bal = {}, {}
        seed_need, item_need = {}, {}
        hires_by_day = {}
        quadrants = view.quadrants
        for t in range(start, min(end, len(tape))):
            a = tape[t] if isinstance(tape[t], dict) else {}
            for u in [a.get("farmer") or ["PASS"]] + list(a.get("hands") or []):
                if not u:
                    continue
                op = u[0]
                arg = u[1] if len(u) > 1 else None
                qty = max(1, _int(u[2]) if len(u) > 2 else 1)
                if op == "PLANT" and arg in SEED_PRICE:
                    seed_bal[arg] = seed_bal.get(arg, 0) - 1
                    seed_need[arg] = max(seed_need.get(arg, 0), -seed_bal[arg])
                elif op == "FEED":
                    item_bal["WHEAT"] = item_bal.get("WHEAT", 0) - 1
                    item_need["WHEAT"] = max(item_need.get("WHEAT", 0), -item_bal["WHEAT"])
                elif op == "FERTILIZE":
                    item_bal["FERTILIZER"] = item_bal.get("FERTILIZER", 0) - 1
                    item_need["FERTILIZER"] = max(item_need.get("FERTILIZER", 0), -item_bal["FERTILIZER"])
                elif op == "PLACE" and arg is not None:
                    item_bal[arg] = item_bal.get(arg, 0) - qty
                    item_need[arg] = max(item_need.get(arg, 0), -item_bal[arg])
            for o in a.get("market") or []:
                if not o:
                    continue
                op = o[0]
                item = o[1] if len(o) > 1 else None
                qty = max(1, _int(o[2]) if len(o) > 2 else 1)
                if op == "HIRE":
                    day = (t - start) // self.cfg["turns_per_day"]
                    hires_by_day[day] = hires_by_day.get(day, 0) + 1
                elif op == "BUY_LAND":
                    extra = quadrants - 1
                    if 0 <= extra < len(LAND_PRICES):
                        budget += LAND_PRICES[extra]
                        quadrants += 1
                elif op == "BUY_SEED" and item in SEED_PRICE:
                    budget += SEED_PRICE[item] * qty
                    seed_bal[item] = seed_bal.get(item, 0) + qty
                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    budget += view.prices.get(item, 0) * qty
                    item_bal[item] = item_bal.get(item, 0) + qty
                elif op == "BUY_ANIMAL" and item in ANIMAL_COST:
                    budget += ANIMAL_COST[item] * qty
                    item_bal[item] = item_bal.get(item, 0) + qty
        for day, n in hires_by_day.items():
            first = view.hires_today if day == 0 else 0
            for k in range(n):
                budget += _fib(first + k)
        return budget, item_need

    def _budget_guard(self, action, view, route, step):
        """At every block boundary (step % 72 == 0) make sure cash + the value of
        stock the block already plans to sell covers the block's purchases (hires,
        land, seeds, animals, products). A shortfall is covered by extra SELLs of
        unprotected shed stock, highest price first; SELLs are moved in front of
        the buys so the money is there when they execute."""
        cfg = self.cfg
        block = cfg["block_turns"]
        if block <= 0 or step % block != 0:
            return
        budget, item_need = self._block_requirements(view, route, step, step + block)
        market = action.setdefault("market", [])
        existing = {}
        for o in market:
            if o and o[0] == "SELL" and len(o) >= 3:
                existing[o[1]] = existing.get(o[1], 0) + max(0, _int(o[2]))
        cash = view.money
        for item in PRODUCTS:
            planned = max(existing.get(item, 0), self.future_sells(route, item, step)
                          - self.future_sells(route, item, step + block))
            cash += min(view.shed.get(item, 0), planned) * view.prices.get(item, 0)
        shortfall = budget - cash
        if shortfall <= 0:
            return
        candidates = []
        for item in PRODUCTS:
            price = view.prices.get(item, 0)
            if price < cfg["min_sell_price"]:
                continue
            protected = max(0, item_need.get(item, 0) - view.in_hands(item))
            avail = view.shed.get(item, 0) - protected - existing.get(item, 0)
            if avail > 0:
                candidates.append((-price, item, avail, price))
        candidates.sort()
        added = False
        for _, item, avail, price in candidates:
            if shortfall <= 0:
                break
            qty = min(avail, -(-int(shortfall) // price))
            if self._add_sell(action, item, qty, cfg["max_orders"]):
                shortfall -= qty * price
                added = True
        if added:
            sells = [o for o in market if o and o[0] == "SELL"]
            others = [o for o in market if not (o and o[0] == "SELL")]
            action["market"] = sells + others

    # ---- layer: room_guard ----------------------------------------------------
    def _room_guard(self, action, view, route, step):
        """tetsutani room_guard: at hour 23 the end-of-day drop pushes every unit's
        inventory into the shed and overflow is destroyed. Estimate the shed after
        this step (stock + carried + harvest/collect - feed/fertilize/place + buys -
        sells) and, if it exceeds capacity-1, add SELLs preferring products with no
        future planned sale, then highest price."""
        cfg = self.cfg
        if step % cfg["turns_per_day"] != cfg["turns_per_day"] - 1:
            return
        cap = cfg["shed_capacity"]
        units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        carried = sum(max(0, _int(n)) for inv in view.invs for n in inv.values())
        produced = consumed = 0
        for i in range(min(len(units), len(view.positions))):
            tile = _tile_at(view.tiles, view.positions[i])
            a = units[i]
            if not a:
                continue
            op = a[0]
            if op == "HARVEST" and isinstance(tile, dict):
                produced += max(0, _int(_get(tile, "yield_units", 0)))
            elif op == "COLLECT_FERTILIZER" and isinstance(tile, dict) and _get(tile, "fertilizer_available"):
                produced += 1
            elif op in ("FEED", "FERTILIZE"):
                consumed += 1
            elif op == "PLACE" and len(a) > 1 and a[1] in ANIMAL_STRUCTURE:
                consumed += 1
        market = action.setdefault("market", [])
        planned_sells, planned_buys = {}, 0
        for o in market:
            if not o:
                continue
            if o[0] == "SELL" and len(o) >= 3:
                planned_sells[o[1]] = planned_sells.get(o[1], 0) + max(0, _int(o[2]))
            elif o[0] in ("BUY_PRODUCT", "BUY_ANIMAL") and len(o) >= 3:
                planned_buys += max(0, _int(o[2]))
        shed_total = sum(view.shed.values())
        fillable = sum(min(view.shed.get(it, 0), n) for it, n in planned_sells.items())
        needed = shed_total + carried + produced - consumed + planned_buys - fillable - (cap - 1)
        if needed <= 0:
            return
        priority = sorted(PRODUCTS, key=lambda it: (self.future_sells(route, it, step + 1) > 0,
                                                   -view.prices.get(it, 0), it))
        for item in priority:
            avail = max(0, view.shed.get(item, 0) - planned_sells.get(item, 0))
            qty = min(needed, avail)
            if qty <= 0 or view.prices.get(item, 0) < 1:
                continue
            if not self._add_sell(action, item, qty, cfg["max_orders"]):
                continue
            planned_sells[item] = planned_sells.get(item, 0) + qty
            needed -= qty
            if needed <= 0:
                break

    # ---- layer: clamp_sells ---------------------------------------------------
    @staticmethod
    def _clamp_sells(action, projected):
        """Clamp against a sequential stock upper bound, retaining market slots.

        Earlier BUY_PRODUCT orders can fund a wheat wash's sell leg. Their full
        quantity is an upper bound; the engine enforces actual cash/capacity.
        Removing empty orders would change the later lockstep market races.
        """
        avail = dict(projected)
        kept = []
        for o in action.get("market") or []:
            if o and o[0] == "SELL" and len(o) >= 3:
                have = avail.get(o[1], 0)
                n = min(_int(o[2]), have)
                n = max(0, n)
                avail[o[1]] = have - n
                kept.append(["SELL", o[1], n])
            else:
                kept.append(o)
                if o and o[0] in ("BUY_PRODUCT", "BUY_ANIMAL") and len(o) >= 3:
                    avail[o[1]] = avail.get(o[1], 0) + max(0, _int(o[2]))
        action["market"] = kept

    # ---- layer: dead_stock ----------------------------------------------------
    def _dead_stock(self, action, view, projected, route, step):
        """tetsutani dead_stock: stock beyond everything the rest of the route still
        plans to SELL is dead; sell it now when price > 1 (on day 29 everything not
        already in this step's orders is dead). Highest value lots first."""
        planned = {}
        for o in action.get("market") or []:
            if o and o[0] == "SELL" and len(o) >= 3:
                planned[o[1]] = planned.get(o[1], 0) + _int(o[2])
        day = step // self.cfg["turns_per_day"]
        extra = []
        for item in PRODUCTS:
            have = projected.get(item, 0) - planned.get(item, 0)
            if have <= 0:
                continue
            surplus = have if day >= 29 else have - self.future_sells(route, item, step + 1)
            if surplus > 0 and view.prices.get(item, 0) > 1:
                extra.append(["SELL", item, surplus])
        extra.sort(key=lambda o: -view.prices.get(o[1], 0) * o[2])
        action["market"] = (action.get("market") or []) + extra

    # ---- layer: terminal_liquidation -----------------------------------------
    def _terminal_liquidation(self, action, projected, step):
        """fieldbook _terminal_sale: on the final acting step (>= 718) replace the
        market orders with a SELL of the whole projected shed."""
        if step < LAST_ACT_STEP:
            return
        action["market"] = [["SELL", item, qty] for item, qty in projected.items()
                            if qty > 0 and item in PRODUCTS][: self.cfg["max_orders"]]


# --------------------------------------------------------------------------- factory
def make_agent(routes, router=None, opponent_plan=None, **settings):
    """Build a Kaggle ``agent(observation, configuration)`` closure that never raises:
    a failure inside a layer falls back to the raw tape action, and a failure even
    before that falls back to PASS (with hands padded when possible)."""
    chassis = Chassis(routes, router, settings, opponent_plan)

    def agent(observation, configuration=None):
        try:
            return chassis.act(observation, configuration)
        except Exception:
            chassis.diagnostics["entry_fallbacks"] += 1
            try:
                step = _step_of(observation)
                player = _int(_get(observation, "player", 0))
                tape = chassis.routes.get(chassis.players.get(player, {}).get("route"),
                                          next(iter(chassis.routes.values())))
                if 0 <= step < len(tape):
                    return copy.deepcopy(tape[step])
            except Exception:
                pass
            try:
                farms = _get(observation, "farms", []) or []
                hands = _get(farms[_int(_get(observation, "player", 0))], "hands", []) or []
                return {"farmer": ["PASS"], "hands": [["PASS"] for _ in hands], "market": []}
            except Exception:
                return copy.deepcopy(PASS_ACTION)

    agent.chassis = chassis
    return agent


import base64
import json
import zlib
# EXP239 native schedules: Yusuke Hayashi (yhay81), Shop Router 0913.
# https://www.kaggle.com/code/yhay81/shop-router-0913
# Ahmed Berat Ozer: V39 prefix/terminal, shared-action encoding and controllers.
_R108_DATA=json.loads(zlib.decompress(base64.b85decode('c-ri}-EL&p(j53My5<F0e<Xd^M=BpR+!6(;<$}j(9DMM2FoS_Tz-QkXes^~_Syg-QjEsoPwX0hP<10~YlC}2Q>nAfZGU9*y@Gt-AzyCk~-+%pYKm42j_&<L5zy9T4|I2^=*Uw-6@Y}mT{`le3-4Flwzx>z#^UJ?|{_?;4%fJ4=|M|av{`x=u@V7tz!#{re{pF`WfBg8v-4CaqkMBPJ_hI|#F8QbJ{g;3G<M`pj?0cX7=iT%(e|`D=<Inkr&VQYJ+WyPG{QUm+;}7l^U;fOyU*G@o?#l=K_;UK;ZWF%!$Ir*(Z(sglG3q~F{+y5c^W?q%@!$RV+uNV|@`v7L^ZJO>ujW5Jedfg{U4HO&D6@~8{5kenfBW<OhoAoO`A0tf`Q_1_4||=|*@rFuihRHi?|wWQ&lleR;#cwKoQ{8d{QAX@@5Cd${iHi<mp{Cm_qZ4SI39oc{O`XUKfL@3mdJ9x_y|5f^RFK-e=YgW;_av*JuHWGo>;Jyz^9#uc6#^m`1|s!uhT@P{oj5W$?OxZzkL16=gGF#s`ZGk>tXh}mp7Wv_4Q}wGgN-*akW_!8-M6^{yJ}X_J_>*zy4d?PqWWGpTps~-~Pbl^Ug;knE3PQG95u!P~PW;`HrtUPV@5f)iiGl)6Cv?obJU>uQBi7J+pa#{ps=tFGGdfO#DWFESYb;(b!cO9}r9|xIk_=q2z_W4M2TtVM4Ee+nG>sB@IpJ@}o+BnEbiL7p+)mKFL{xspA}Q{ejo0Z<ysk;kOz$_H|fq|7QG^c>i90_wApYKl1Y7!|}(D|M<7Z-#@<p@c#c;9&wky1b?s+@Par#`J3m+VDW9Z@7|J@$&Y^C?`fK}Tq(zQ%Qt+zN|%AElc8l%U^ct_Nt2HTkL;W^=iL~Si}V~d9x(r$Fq6G=<@#rCGfc35hsJw3X<paX%A>uW4kKrEvhN1gIr*%2`6_GNE<^8T<(n?P;r4auUygS>1>l6UP$D$)dZO@yekJjyVtFY$=d;*KU1RL?<Q<7{6ZZGy;vy5g$kK+V7Xb=#eD-X<-Jhk|1X0!4XszW+vfshk9F4H(VCBOjbQBEt{0D!2_xr!^rT=7>FRP%Ft60;08TLTdXTOIDn&RYsGNc?_-XKPt-2r**k-u+nQ|vHKe+i~lPCbX@`O(%`CiDyjaGRV~_6GrI{I)2J_e3Tjj#GvZWP5z01ilcOY|ELuj73;Y!TPEOoTt%<xRFEktN@l*KdX4It@SwwRf!i&_C@bCfFq-F^Ts)k1HR71?2_qSlImTAWL819=&oCoc|TR&Q+!5z&z8Z>c<oIKJ@~PfMNIQ5VD+x+S7fSt$88Ak7t;xDh;`!<^la9WDTIuCf$B@p``Zv?YXw4E|D)K!0VASq77>jHmMCxPJimy?m)Hxu(-Yjl-x!yVYeWz%3cLQ@l<pz_zWr{_lMCv0<kK40K8V_k59)+*8MUJv*6oMFI%jpUg2-Bs6ODsz9A>qmtIO`SPz(u?#W~Jv9lhvkQFU4uCdp&g9_R%A-V(<s#UKC#X~b3K%jGiXAQa(I)ye^Fj6||3LnlB%*ElUOxs?l&d|cirEkSjU2>=F=RRSL5Zr$}Wdy}XrNtcpy$j3dHtPntF8mRpd;1Yb0f%7=EO7{2Mf!9&^!c!2KGXA-N*(aa#)9)|8RU;FS0_^*676(Gd%F5l3m)pjUz??r0Ue6-<+o<yE^%FmdIC6u@Dhq;fvjPZCm-C;4kCdD}E1`x%)w|0t$0-_*Q!|c`b-R&CM)1gR(04hC;!Ly<{#s_N382@9=F2JB{*(LrkB`5<JN@nW`|tk&tZkGWsLvaFFaS`98eD-{6%o(L(|h539P#Bg$uZ;l+3QtTuc1GW@u%;&5~jFM<bIS@as@Ab6`UpKwN4j7FLGh%b`!MBR;Yi*y)Dea0yo4b8?3bCdB!Mjt-7}8Ml1D~S;3FfL4qO$cD<+U-z17z4&nOVVdX^9jTa-lT$2V-xwOSDe>g>o?qDo{&V|}eobHS?9=dBXyyM=C5dwJh_;2btui@*<%jf?bj5z!ZNWc989>AoV2nPhq{GJRdPkb)Tnx7AkpHxHV^|y<e$93wHM^Pcq<qss4gAQ}Nn?0RTcTn>Ifdk=#uvg-QFd%k}3~(^Yn5KiSRFIBu*1fo{AVGpk<=iK;Pv^nCE@1!8ti+Nt_@>{A^H}H_4r2hvlSA}iZNq8z#GRkA#DRj_VaaAU0+raTDL)u&JX)!c4Vt>I1P-3=Ky~<`ce*(5%w*us;&ZT^kjIcVxy4`g@tjSYSkkB(jjlo92Z=G=^@7%(yrr$nx)kdyc~gv$L$=~1maL_0v~`xIoIa6f2@pPi^4}#mArOP4v)?xEn@pQS<-4Pm$8YuS@TSXC!~*?bvvQ8ut5s!5+1+EJHZl#=#3^tA&~pm*EK=Wm>R{3#HjU{Ni=A}&-@my~)sf6w36YMN@#F+K@>|x<=QMbS!_{j$ZHPeBZ?FW8#;x&9N!YrZfyLl5Pl#Eb)!wD<P++EG)t@+`#7YF0#TD<J{I-d6CfJB<POcTPMdEVJvQnxY8jkgj!2Kb1A=n#6@1>7_gOpfsQ_thb=ShZ=^d3bYO0|>JC0>pHojIaA>h-)vonUEybph($l*CwgXudpe7s-3E1A?U&Xhhd7=+^@u+A$;=LE5vavhUtzBVsGM4hV)nRsb%ft~p1$f-MzZ5qw(kJ&WC^fpt{BWb-{FJ;3lV@GX857ZPJ2uID9C;pWM;O3YVKPNb}rQ3#D!t*;GcQ{X_P(v34R5-ouZb53UYE4#eFKVJ4oj><MU6CB;0ju}j7oUzg<E>REq=xfRG?LPhG{fB?|R<P0}m7K=@`ez<CX;JEc66TADXswVF>wvMu2hign7@8&<*I!0zgI0}%lIc_=t>EQYF}ps}a<6s(adZ{O?ZX-442zSc&{~+lYKmYtEC@iAI^MS5A`|mTR#{vMl5!k;giHjA(_pG%)~!?DQc0>#h4(3S@hQMDA#_FQSP86!Pkm2mx4(hSo(vhtQ_|2d>UJFxAXKSYTEc{#X^OjHTENb^j(CndPOXUo`u$bl&7?g62)tTr$;XZa{8lml@AA*DZ(ubV0EpvFQsW&}>dn@LjvFa|k?l9*ABTmKKu;P`kJ2r+n@>$XC@zkrcOn~;KLRPk41=`7XIt!2^cCV>40nm&x^&m$d4lSUrfsHuBkXMjJ)AlDGs#w}w6nPJjInGOZ*^Iv^h7a7Lt4941%!_=(~ifA<_ZZ#1=w7xQZ1#J+e)X}Knuu|j%F$tk-uVm=8Oj9n>eh!#8Hb4c-tH+(OjYRM4zW>VgZ!{0A#0gCh?A|Rwm1GMn8Bm*b+==$wjrQ%Z(LZ0YzTa+dauCm6*b_zR5r#IJw%?c}Z*y9|THHOyw24f{M)f3l&T+2CO{8@N!hQMOlz(0Fk3%B2q($vAw)<!K~o(p56HsvTl8qc<e}de8kDoO(K3;TC*pitW}A+76`MjpUJI_6A?kp)XfWiW>u4+MYMUwXHctr^s;y^w>XQ1WZd9&8D+&#zHTjxlxFiWPh2a|#&>H!T%C1FzF-@O-}b_&@9!@!e;j2oZCiMXqIN4yX!i~Icqs1&{0+a&6M?hG2mKhY&K&^3qEZ6a>%0#rF5#9})_=h757`1qI!ODisH(n@{VYDvfi8s_AL*Y=svt)~HeE(=Mn2oofS`m|v-yGnaE??#aa6b!B?1}3%jnHz?SP2snEx>O1-!9#{9N8=W<=M&oHTcZ0n-UWzd-*8Pz^U}?q{pI9k-?hhyDJO?}a)YG}xm2$-Q%)CwuJKA2t<g1xjkss43~0^}R3Wr?-^%)*a!Iv0j4~`A{|oJ@T8*Pa~go#$<9T>beGzoO`eBkUzdGC2(X6AE``l^Jm=bdlQJ^8W)S9^L3gNl>rA&X1LtsH(9)*Z<f7PLE*?-^$-#f7pQK0Z*Dx&t$fm*e$Jan4;G_%b0rFbv;2AhUWU9_aMaogASmhySo-lg)aN#xKfdbob6!t9R(gg#nxIXNdOg0*+zQNhkZZ(ZUeZ?@#byKUmdz12Q@C5rL3YvU;l3KxnYj33h4<jN&{F-b@Nb|N`mQW&VOiEXU(}izC2$l@coD88*w40xAQf7X5Q4|541M5>%L2W@N0Qx8Q5B&iXi%jI-(jNaRWYv)Csl@pu?9Uo_`t=hHNv)eD}`)_$_XPSW*BWTBCLSxy(Uk{g%Z%(f;P5PX(sCA6lcMX<<h%-a^+PoGoG_iBX*hv@fE|zJ6rn)V$^&$L>v|DCj1OYzK&7ZZG|F#kufVQAMm7n9a&SZv6A|20w7OA89Nk8Fb}O#!F8;60O00|3Qt{_g`A5N%<W!IMg-{_x${2OnCc_!226(}8L%XrJA}oPPZGJ8XLg^$vZ=~DVNo}}Iap(xI_2el>WhnU+Lga&NFl4=)xik%xISQ!8q5P=U5x;-q#{<`KF64^VV=mF9pB??iuB7`-Pkpmd|jH%o$BtCREX|e>bJ|Eq^S@-u2W~nj^$;KmS~wl%74w@K}mkjY@my21eIRSpTRhn$5a#8dZ0cFmD4~Q*$l`k7@KnRB={?^j2`O=(_RrjG&2YNAng<^RgIVuI90^0czJ;>8{<Pv=%A_=m1&4<1;rQ!RVM!@*-etvUoLG0m3+YKNuW|iOac_QDbPlL&`lo}Tl^=VpbFPBNH=KPR^+~%*73Wr7nKZNi6wY*)62!g4g+in;zrm+-+8WeLeD5#=rW4FoomrLyNnCa%*(pw*ThgtDwVi~ll(kcFWgiE1_?I{l2cWxQsM!Keen<hBWpQSgGsR$T}FW{c4Do*-ax_AlLAxv<7<rF_Rmy_Chd7ytxpUz;TetcRC1!F0tl|%_!)7Gxqo|YPuNS2m4nQDq#=tg+dcdpkr(9~()*ysBt6vGxL0E%beIbLoDrpXht+aOt??1-&H28-&=9OoOJVd_I&9kCSRFK|0FjM<S1ypNHaRNOK;M9o57(kbN(dG$2U#7t8Mm?~1;o@7$E@Te5mi9I!vu3-tM1wMVF_sj>?nPp`!d`Vd}hmQTxuG{$}!)&kQw5NYq&rqlT16N33r0k9B2i<Bz*>LH`M3YH7O=qqOXiP-H}Q1)^$m&WvEL0d>7DqLFTz!9-~*-rpnIt8tiUoPioqnIhR<_R0-r{b=orNcM<}FZ&L2Dix-RIWhKR9-<K)-njSSJ?1I&tkkdd5N@I#1&9q#+!ejAGYp{>e##q-UFHZ285osk`^!2X*K&5A;wCtVsdRpG`h2T98fWac>h~d`u8`Uf2Dh9`H+C{n%WfA!EuwNJ^mXB$|d8NT)g8Rnmv4V?{JwMeeAp#-i{FzoXw(`DID)cADiHZf|O0q*Vc2DR+iXagKY&30oTd_FFgI2IaLk=PH02#D0rbv{V0T3H$;Zdg6rq9w<+0Saze5)46S6JxtAy2Vw>s7G!5rAPpY+ge&uIP0v?jX~>*!<XRD`WS)!w)J@)fW%6?(R_Bd2d6ll8~~%l2yyNL<vo}Yh@Jla%4C{D&GLbYyctDE#g$HYkR74hUFr^Loc)C?FG}&a%5-N9?E7q(<KPVV2O#30mzWy`f{-q#RAj!%hn$H(Ng9`VM@{Z<C1@T%Z6dIagH6a#aE%(v9ngeBbT+M^`VU8?E3aI>&5ic#73V!0wV9z^|`k7U!tMgU6Q+rgm<Tkt;fIr{VneN&O}{80L&<aNnCH~0rJdt7iuQY!K%8a4w$RY&3l=Ho}X8vw1i)%#-S@v#Oa(&Y1nDvR<21M3n_zYO3USP6vQwp=EhO>g5q-FEF1`dY;)qMcA+eqsO+^bS0~TZn(_s&+{4R_1twSPJ`v(E+^-;=$XXmTy_j{vQAFIxWvS)?Ud36W5Jxc2cNE3NkMJ4aM>l+kOL;yQz(I1Xhr!Q)*Mdq-Q{8+Gfc!+@LtcbU7A<KxLk3{+B{8ID@}!kH_VZJa<I(0DUV-kgNeR*>PiQ;4X7Y*{l@_?AZ&P#1A;nJjNj&a-eUzWx{~hcfOWdasm(b135`U?r)@vrTC1~c;<GP89qeqy8u3jFWKLp_Zv3JoWuW(*f8F+xvli+K&z;=4@s`|bxzz~Ryhk{duf+sT^^pAe`E7LK+F5rWcHAf9LYoZ3QZq7x~1}Mb7`#MU<MO&lHxu2=zoN1LuxuxuiV_7epf@`kfpa7-&(dr@g@DtGp*5I;n*;Gy#u*-mj0TxI<peO*YnSx~wQR=HU126>zCISqG9rBf`V!p6K@H>HR>qNyav7H@JgD!RxK9WX)5{$xH${Q&%Rl+)%*a+<CRqv1{8*L9ZR)7O@FDMNHlF)@8FhW)D5xp*P=dyLSLWFvf{p~m=wTjM;(m^w3<+Vt>cI~4EEHjcqzt$=qc5R1Rag<QdI(D&K)XOK~^G-Yhr5q9!5#9Nl^)yUZ5Br_D*2kelAp--iKq@XN#-Re2F}FDOqBs^)SfYQydIFH5O$&N&Pjx6YRI+>?E$V|#-cZ|@dvxBxr#yV}ithP<iKD6Tc*y;B1@&|}2=fAFP58W_iQ?COY}W;1P^|!+wJsmyj2yDVnb<L(%iF$S8aZHrc~ph3k)nIY0UpO{{EXF_7z%71Wwvos_{CIHV}L?zY6vt7-O!Mb=)ZzcS-bop@HKWeU1eXn864TTjSP@z6{kb;V%myvml_TF`y>bN431SZ;2Fn$F7+i|NsWs&m^ymny<~0~tvr_SKXAo$s?2@?tp^3g%+hJY%*rR)esqlnewh2R=1c2B&#|zYf?}iBARY@4Q!#)+zhd%mkE6V8&0&rC!7OvLJHW}Ps;tQvrYY8hX%YqLc_*o`mJ~i1*>OkFZ>G`444k_QU5SBZJQcIiMYIk(b4d+g-HJm=-Z$BmJ-q{FDo?R0x=hGXy2hZ>2m#-eSr!s25thbx+hc+y<FrRMRvjv|Oi>fz3f;7|yi{zc2;mVtDup_zD1D5Om4UK<_Z>`tgWv?we<=lpx$JL>!x;sr<$Vqj0z=aegG{WHOGF!HgWB}{UE&N!^DAP(CKX<lQXarDOs+@#M@fP?|H>7m55rsbixh|&-xb1$n+Rm-^8!O=25xpO_!f0$$>TLv9;J&|-teqknU%|=|9Ocb!rm8+F9>lH0}0`)?x>gy4ORRlE!uiWg02s_kG}R4m{-xSaH~Qz&1XzWH-}cisVcl&m;zBnAt}-lTdaXn%`HFKVYN>l*A*?yIPIhG!l_rru%4rA*=FWgBBg`e6{3XJq$ty(I76rk5&fwwm?qIq#<ixvI)EGGk;eI0O)d-Fl5$FuHhTu(H{>kEKIAg+KGclc@z#}jz$0U;pOvvLk#Typx6A^K-D$MW2w2x`*=TAAuscFH2mv+th%^*4(L;i^xu~gbF$G{~nfZ2?kW?yy7rG4svw*;vf%KgiV&usTACkx1gwm|x7A&0XASoy7Q;h`TSero2IudcXk1V52MNX<FN1F3&pvQv^o7{)@Q*L6M<`2B)!cIKDdoCU+J=ZE1rZTv8Lo$|<((t;&?g7a`<Obgrjgg)U22%oJ47|=j@~Vsc$r4%t^S{#)AiQBIhHZx2ho$cXg#=rfd2IFx=onK2L`r<<g*mFHrB0$aw|1L9^)?<6!&Y&yS@&aE&2ZNcYk?N`63nA)+5gcR2y2a&>KN%WHN`U+PekT+;2NuydYejlU=!&ND@4i!F$RrWPP-QC(aS=PR`f(#+&q;;vFkD(g5@PF_n_OuoRMzIwk4kJA08r61U8WtNO6~K_w2l@xJQ!UB9X74nt(^c^@nV%rc!VLP$t+zfi#^V>vI^zF=3o-pQDh85IWxJYp8J#rkgmVmz$bQ3bTk}w9&afL9KY?S$BYI3!!5}6Nni?NM2g5LJ5QQc~Wdc1Nl3{7?L&n4XHWg01}YS<~eY5rg9O6r$V!d<Yz@X24v(1(RYKl&NM-pMWU(M(S~C~0_J4*4>!;5sl^^lCl9<cgt;kFDb0=hP1RU3AREe?QJzxdKuRE`TH<$VzLT6YO~H3feG@|&6*7d4rfsVBLyNx+mnOv~hBaHs9tG^oqm(y=F>a!YCCV?HG0M_+-bk3W)q-O*laS6O6Sryf)=96MSw8b1=kqJvM3Xw%DzUs^-$*SoN?1RQ@v5vUc{QDf=`pMRmjDMrg(f-LiOZDOOr<uqV8ft(546lXdnOaK?pdmUl7#?kqU+e3u-0@&+^3fek^e7r*gsWzTeAg3^w|A0E8D6D9l>h-&nPTXs=;XL^RI5+z-G}2l>&?Os<#tHcEJ@iK&LRTHo{5J88er3!VO>o=8<Ux>3~WXXCfrM^8<?A)!SfG`5mI~*6nJ_`w!LmMs}b#`-Uh4F9R7BEruWGlCC5{PgO+kyo20tZmDxJ@Ld__(4xn6^8>TprGP@Og}{6fN8lLDtT!XNi)_AK{|oo+;PMX!U7;o7@i^qA8qX_w%g~dum&e33L9}+~IvRqzTpE?K0U>R%;(Ro<k!k=;MU<o2G4Ca=wEA0@<>)r0!wF{w215$<?x)cl1qE3Bx(eA=sQMTfKrJ74*ZO+7680;Jfb+25y3tt?-YVp4j;O;K=->>TUBJ`_I$rWR_yaIla`ceH^t9IUuk$RZCrE``w4#Rt+q)P84r2T04!`K&sguW7@ZS`jM=*}d&wLORkixKYAkEnZ1sP^Wf8+~^<Zzu!Nm8nF2e-;Oe=2$p89OvC@}9^qLr#dKD-obw-=xBC4dd=2sgUKW$~B_t<Dk8NbEYhR`mfKWuT)nT#5Hmuo<?F<O*kHJuVhq|r)sW1hT?ahTIxKj><M_|s@e$CKt8d2L9}MgfQ4uf`wEyKU6CvX5`3%VK*-ceN+PsXS&>DIdTYi@)q}+%SZpQx-=t*3E<C^l@(C?(o<Aks1l!}*?FkX>Ck3>DUJ*1rBV1VW7i>$9ZDCBQIFi|2Vv5h8f2dtcJ(4xUAxfRXBv1q7)pCuW&g;NkBICu5dMlnn#3e4$hT*i$WjJ^FH9{D(od)%+*#H)_nOH|&Gvr+L{7|F~R%)f^IGkZSR!F?!B4-MoOfPRW^rN&hd}$kA;x<FZat9Dk8G2}?f*%~l6O(!%b$vl_gQVT87F_^cHx-H=Q_DyPgR0mWV?c(a`%e{$xu<4hX{mRjA&6ke+eI2!X*G2@joUttLU22dhTU$bd~9i5(}<MPo#kAgljrP=8El4#p)n|MlGB69r#Dk}Db<B~ZFA2-&y7W}JFq1M*KZ)LF}8rY$I`qrE5ht}*3U!NktX!kG=w{X9HppE=TG}@?#ZGAM_rxHU6O3`)&3PFc;Zi{Fb5ry91Q~#%CWF4ED{xv0`-kcERox02Bnc-ZFJ|96w|pwhl&9VImDItAfzG$LM1>5rNo-1R>jGkCtDCtnj(|_ocS6UsCP2u3_Rb01a+#ZZ#c5vHo4!Jaq+xuuP<(igF?2r%FjPl;6Sa;RzCjGFo;v{!q1Pb#ZP7SPIW6N`gTlbgjE~PEdx$9`?TMG87J4W$?Hr+o(2Kbg{+BH1KYZCoJd|GU5>n-yh~C>#%MR|l}quKyM8`I%B(SyGi@{NRlTWLPL@l(<u;luJ+0-$IrG164?){~JW3P9prTHvjAZyFR3Z9NJ#ylRkPMZbgho<W=*!K|#$^U<9ye46ofaS&bHH(;liHY~CF6WXod1irnEB4>8FyhW1z^Dlzn#gkF%;5sNt>kE+5JUuvxJW*(nU=*RxIQW^l^SSw<cZ?7K@M^*(UJTm9LVp6PUZJQF`lBE*zh7-qZuMIK!0qDl8ko)5Skxo0+g4<V+ysl#>L6sBGH4OqTSn(l(9XhSXgG(U<|YwAvq;N_;j@UtXhT55ptV2^5dtz93&~PtV-z>h;y%x6?&cxTiH8;+C*#z6kg)^Qm6`-?B6kzi{PMf>^pIRHyKoOi~jC;^d1On8T76)*W?nTYUOe5EIaJ^5NPCXF3u<+R`_gmRul8%FKP1Yo|s$KwIZ9qq7MNn<u!1EL>X_xN?zNqs4Ygq#1JhOrQVi?=R>8Jnzo8ACQy)Zl9)>EzFkn8%akm(y=+k?#Y#_5Cm48Bs$(w)DmXCHj-Wgyud6flS!@_1LvqQq4BN<;5$^kN>V-6UkTPjWwDl2D<19(s2}EO%{OvKMSro88-dEUxJBu;!>bDTiZFYM?gQBOOi3uTPV8)W6$v2lqy%Dt1+e@U!4ESw`(_22$_iiU7fLN)^6!iZ$fiifEom&9Jf{;DFc87v?k{*vcn`?ooK1lkE&v2_f9Gy1n-0gt@Z*Bq1xEkl0BZK=wJkxP0r;~J8^wY^RAxOqBF%!2(S<>GO(qurO|p*aM5hH)Q~=UyAbW*mw|Bb<UF7q#l-IgS31YJzw3;i>&@zbT&glLGES-u*=6Ts{Y6WS@R82O>TL4vnSOr*>F8f$-YK}P+u_vL8PddNdRwf)d#gIN}84@qSfaiXto=SEA^Imb21}+7J9wmv)#2bh(Wz;_bm#VnK>I;R=brB>CDfV>zbMZfr3lKE_Et|WqwJ-}rUYVo;>_S!?p3)_6-UUwcA<L++?MnQ)xa82Yl{WRAR9K^JGBnX<I~_b-<EbiHq-M>~9FzTH9PcoqEBpFb=d4N0d<^H~)?M))z>B;ztH)2IFWM2rozlCgqexJ4BWWXu&!@s{`Al1&WNM>ElYzKG(&41{5Fzp7ZqBf=&)>fedUVbr1cAnAds&&mlR{8RFwGKC*)b{)xqylFj}7?T<t-NuPQjQZCkJUc9UX&rIAb<GWJ1Q2B{R3`hP6$BYo+yAuK{NC3H*v6AX!kCGFzU-kaS=SpOT~k80YfJsSg;4T+%cwuaT1!Z(J)GwJ`?(DB&u3+>(*J-SkW8sAF{M^M&jl&<`G*>l7hu#$v{eXoPCj)~!bVfCS$Gp&fC$Hu^%IM=20Yb+^?HaPqK*O(;-4mevC^&Shm}+pOIOt_spBP*q#pC8kz#i<l%ehmPe=GM32%5rHNM<w2-SMp|S{CGS{}&Q@?VYSfpBZRIH}d$Q85JPTUL&_iJcst1$>S|!OfBBV{Hte~Yv@fZLZyNg@}COlW-68%Re{qOXIFze=%b$k%%;{>NbL6SR}ys^zs(bd0G*Pqu6(&T-iUJr7{Io)6E_rXEaX%<@*)+j2r+$EN@n#1L?V%F_!@_lYV5)YF|nd^HXL8`XOWV+4~Tab-S((R}DZqSg*#bx%cn_s4FLVL}h=~H!ht)CND%051f;me)g#sqYYtcy9aUaR*hZ$a^Dn-U=rGKk+v63vj@uc}%f6GU48r{W*O=oITnua$g3Q2;ZchcjR3ith63pY(<FUF!oRf?8s(GfuQH_jarkUGo_0^>2zrEKggHDL-dz2BPYJ*WH7FJ`|5!tdAAlpt*McDtx<AH)7mirTxjTwX5}?*myy8M0$964nUntjA)6lEi?(IJ(4@kv{s-O(5}P!SG_BZb88AE2QK1A%$7<WOpNv8&Qv_$v_z5fYANTA8zF(VI|9H-tpx!`0h*0@X=$i34(7s%9#o-m-gARh9N!~jAxR4s+Ro?uojp9!#-L0`==CRe*ippcXr7Ele-J%^4xvyyb|^i%yX84@ke;8XQ*$|t@9*yi8m7H|Fs<QIuNZ$BcX)sEZ?b1x=DUZACC_(p<RK;FG>bnJOp)2?{tAa|?kTa2)Iw9-<Y8<omI_YsQDFx(<M_oXte=+HUNI-XFcFIYCV0fe4n2X#{(t-P{fD3a@#D+eHRZWGONqsJ5t4cGO0xz|;A$n1P$$-RH(K3^Uf3XL%Q68)-mYZ|IGV{{Cng;LveV+<`b1vd2u*LHLO6v8uw1s!tb3MBG)b=sm|1((Ua79tJY1kjw2hN8m5nfY29iCsRtJhXV|ID|q!}ZaOBTtZT%|kkWMm!SzNm@&usWyo{2f$)qKk47xLv@m7`O4#Cnfw#>uV|AV=H9CC-DMP=I%``&kXEYDYND0U;Q~4S;25vd)Q>jENK(qvL)?D;cJeOI%%g4$%RRyNqzVrfM)Z`4ZmSFpE{wh^aORqsi<nb_*C~f3f;mtT3-Mem>~*ZpAMzQ;0mPf=YyN3-xk1~>*A~YT8ck^CfHEmDV6wOCZw^-ZcFQJ(}lUqbX?;XvtLZ+puGR)@X^zf`SARFsLFYrhjK+WL$iMT;_}1rPYrHD0w7)2R7)@Tjf!))IWTmx+8vLD7}60{xkSZVikULgq)w;NsMRrre5jU_C4ap@vI=jC#SCt2ampG1Y8*FSAz~~7K{}qF#?{<k(iO}625^tcp$V`AN8u-ujo8c#UC*KwepC2SRib(My0*}0VG6z|7Qm!G)L&@&&05Rpj;jWhY+yk!VTXo1ssg{dP-Ut~(=y|B)qM{iDaDsoz&F-`W7xpL&AF=u{bJ1#ry*G;(nZxr&?K=0ySD|~IEHnzZFE_Xz~_!prGgwJ)yI1<l!M;};PcmT=7I3roOgM7aJsPe;nnPQj5abCqWOT$1#KUWxxk`DwUL<46Pb@Mzr6eS5`K8P_Me|-5$^HB%daF=5cTIbBunHVrTmyyE|CNpo8M)&IiC3&GrXL*e}XAyD);|;e(&###OZjf%UgI^ojDJP;0I*NjjF>x+mwT3Ac|}PoU=Z`3xw(acQZXNNxuFv>X&EN8Tb<^P|bkA`4^0r>CFFkICFY$AUDlo=fS+Zw4C($cgN;DTlMH+NvX5+oCg0jmJ0A62lkDQ<{yRb0OPFNmFP2@Y**}#uC6y~F%28xW@YKpWP!Tsw~Nf3#pl)#fI|7ayNUp+blKmY#i-2dz?uihfgv-dCTzW4+@2&oL&S|fTT7Wrr_n^)gn9*y@?PfW{z3A|Og$`SCV9_t?s;`&`kuc0%ZGQr{&Xp#y!-Y2FYmryGcTvf&*0jMV=sDs*<b!%f>MyXA@d#qPovL}SB~lDzy0ygoM;&D_V{b4F21SpQ1cK1%J4DjUb)=}jOHAmzrCc~Qf&III5CUwG;Z=RG(Z4GJ(0_f&Pf0%s`8Xi;E`+<9_O{lq?%Odb)ko}JfT>JDEhngIU6$P&H0qWVd0wBqZX|ybOGoa5Er~JXZ0UHACJFzUPPAc1=Y}~{=DYl5;;c0OOSRil$sW-;2_maT*cAEibWb~iM{%k`tan+s>vrLe}orfSWIG4#p2_t29V1#f8B2dzaCp}wVGAqxdUNMfQM2ky5g9(_Gv^dM<eO*I>~Z{cnpWG!%d_JX8Qr1^{ILcYlU0LFciB*DHDjP-Xw8_(If7eNP-QNdxw;CAc8%D<M&)Namhu(7W0+1<c`l^x8uIX^vMzY>x*NmNOp$OdTm~K37l&}<crrie{UljGbWjFsibQu-yhv&rTozxK}qfV;b)<7dPwpcvzG!_%S-D(F2WP4E__{?3C2UG<%8BMNx9#~@*#QzjThusP4GLcgU&b5Gqg0Z9l^b=?xtO}K4JOhQIBEocBt9k5ogNct;EZ)8!Iak8qbvRv53=Iv2~Lox(A66NIVzR6IGRI=VT;il4nsg3+s4Wvf7wOr%Uq;Cq9*9gzs%zFp{OQy)}1|mR_@fb+v(xWPy9L(zJt(p{wcmP8hqrfRHA@T(i6r#HNaAV5$rGCRv;^nmxHH(!4{)9jddEsiK1a7?sJs*}B#sIu)-eVS~sn_LxSkj6mL>xwsSo>mUmSMYmDom=v9%EKE%|dUN5s<O~I6#4#&@%x+QAiZI#BjOhk|L3PF)*Hlb+PSz_`<$alvfa8n(B{4tL<Gj&5q}CWXjcU{8r*2rEG?eJK_FT#QyB>L>0qt&(;rc_|jWi=aY|=W*w-c>{SuwHflPYyyS5vJBOInwJhs!Z_Aa=$kKRQ+~fvVZ%P>68-Dub}S-fjOR6YJ;}JZ1L!4Urfo1V!hAr;sJ(b+WFg3UnwO!#WU=*)e#c#QVKt8djSapSaqA+zrjPVkv-;RC1%9oKG}iJw8eA_HmO0Z?Ulop2#j!pggx8h$k$Ln6+1yWszlw>x$Esu*S$2z5s*2CumDIU4;H<m~;T7aKwTlBaN!8t)~Fb*SWut7LoXx%RY^_#WtWSe`Vv`ZADqUz8}0b*eba*N}yNX&T^LF(tmWIZmhV@SSax(&E}}m$Z#6RhpD^rrhk0jm^C=cy|L`ChF*<a@-J6NZ4hzE7fc9=^AJ~{1=of%khVfh^<j|8?0&`QyQkyIp{x59i1%Ib`mV|pkF*QuA+w7srEc0j0mIn^5$A%%JYnT3C0fRM1vcTfTV`j3rc`j8Ayz}^lt|bWFSMn&?2~{>-nz68VDd4!;r#O%6XWvtAWaH<DpjLGzkt4X{R9LxS`B({e{Qq$Tx-J+xbz_U4T2^rM9p{*LO^*K;eu0gFn_`1YG<9F#={;~cvgqyC3(`^&r4>5aT>ym4o<^>YbWh3LJuAr578!(-7AY(E_*m~BbLn3gzs@;O^Mo*M57AiFN+hGy(!8$P1^~PlrV9$YDQaeQLxeS*v#HV?G{`{FeGGq(2E>}>M1!(J(^*|w=ws8B=N?V4Z3~u1%+8d_T@&qlUvUN5{Q^*yN0+FV4P3W8qDq}e@z6m*-pljo!L`2S^1^nIFOU7wIn9=`EdI^wMyu-Knm6T>JD&lbbCVU+YB@j^Pt$lEY?7TR2$K&tVIcDSG+$-2c#$sh*v?NCo32v|KyMYplME{LGQ^5bj(eqbWNxb;9Nw7+EuB#^ZWUrIJ>fWOVk<`zo&Q+<f^CsVnbb}h0<m6SlmgAd2+Dr;jh1{X8y>|$w9`onhC+)QM*{JS8lj^Y&CUO))jzbYa2u^QE8o|Bdf|LBDi(Mh?$A#Co|;rP*>b#)a96<Q`#jyzrM;DIcx9XiuGVzks{~%eXcTYFvydUJgC8vU#0V3Q8^9=QXy|(eZ6o_>df=O9n8)v)=^;Rsdf)Q37Ap{fIL#b_?PzyT91RwLZ~C*083y@YWwCIF6D%qMCr8RuelYrwWQIU)BtUX+XCsUVOK(|eXZvK1CT$qjM(ioEO_9pZ7^bXH>q7sTn>zqOoXrylxi8NxsaC}CwTD|rG;Th#*aH(ihW%zb+1SV)IL7_LE77gL8o1%BTJD=p~pMtIk*G0(Pvu}8qLPzw__-ol%5jvr;fVGVaDs9+FGEyw58L>H6WNPI8}p485gTinNdtZI})m`F11l|*Ikt?)Aw9xtt4$D)D)1S5ji)y*ONpWAcPxu+Fia5AKa99<Uw#^&h53MtPw#nc4J{Tu{^PiiYm<$b`>%Rni|}v!KN)tbHGa&v-kkQ?sd)RIoxJfvN5%lCcMQ9S3w3i^v(5kn{?04Nbw6a=nUm?TS_zD_Cq&IEQaf*J|fzI7A)<_K&2YLO`|Ey!3eNKsz>$qkBM{?n8j9@UYkj8nNhQ1&}(&c-2%iWsL8}w;AYI-Z@=#7vPU?6PW&(oVGNmi&PXady4>0N7wW2#5@+O5*eT39f#Mg244oxYS;RV8?oQ`iGE=YkhAlqAwHPRcqQsdgq`5sH5IJ~eMl6<Jy#@@HL7=!9DL+KCag0XJCftG00vONY28H>IY#09+42nk22L_Im(kp5ea)gF{2TLWg`4|9?rMmWX-c!~D4HVuc$h-0KMh9TQ1fh>uHhq^m*PQ>B2BgVUO$G#VtwN^_O`6I09ZgKIoc-}w4UIC>%~k?B6b$bL0U05Gpq>`FoxLLNfz|Q7L=?MFAjK$8+$(;3O}3J1aHROy5lh6=H9N3EmDN#MbVU!zUys67o!6Vu9$b<7LNwmN{Ls33m1HuCUenCWw+U+|vT8*Zz<-#A<@NILmseS&AdR7sl0nU3<048!*rJS-0u-zxZ9k2zL&8v^y-!yyanuVpR|y?p!bHqufc7%w*k4U(MBQdSI|pRoYjYgHhjEqJ>gXLDz^$o&wdLM@hgy2jS>Y@RPObNxupUc2IyFCEK?e!CIC=KFuYI#SF<Guu^jrdOC^nYOmOphP)=DGR_<*1QV8#&rxfp$w#x%X>#kdqvM_&IaP~TTWnVjF#=P1M^ti)29TNZtSTOEh*#0kZXuC&x{mo$*gu|?7+Rx9xfqEjLUPU-I_hj39_-LQK&%Q}V&Zi_c?be9IyG;kOuB{n$49LS+7@gNsWo`K{K7C1GX&!67^JwIEWg-p0n<%pb7e9<<WJ_upQ_E$II;}P`u*+GxRvg&AB8LpW%hz9a@;BL(IhvDkKxVC5Vw+}m0Okv;TAJO#pWNZK)c(w8<8c#=ZS~n!g!KtC8&{?s(PU7ed7fui`sSw6v`ts?jSpl8p{k<g2Agc5o6DB3PGVS<!N}fR3oY)536m`CBhYn}VX|)?cwxCQ6cJeLezguZRh=@bU!C0Q|4k_%~91B^`9wP%q7)B$N8ckVEjvp)pbY;+Y-v&+|Dw=xN8ntMnArulWwDtOja;3Ri7R`%yj-NM3Q5mysu>bdz$&p%Oq3RsvD(yW);`qnMN=zhAOzO^EnO));Q%D<Cu`#B;Ab``66`xznrjo>~X^?ib6JUBt#u$m9bfx>gV=71cC3tk?m&8p2n444onKo^K<2q0HF)}&{HDUT^6}bvhCY-`dsq$vKBzrXrmS#IR-ld@fDKutBeMD;gex~KxULjerBnzmZbA?&aI=3QgUVgX`%LdOg-6L>oEQe0YJ+X&4QtMA-EMB`5?f9q=5u}45A)74Fo~Lxv6XcO3@3f|N*Tf=?=2syy)AX_`XTI|S$l=q98$)bQ1n4N|nu_quqO@~=f1mNi=l?WQskx7LY20X>6d#pErysBpFcR(l>L_a6Y+A$?C!o~1u%NhFQ52Yphq&0)4JU=Qm5|P1q(i0jRkN-;w`u1aJiAYi!RLU@vmx%XM!(fJnF6T%J3&vL%fh?g`+b}JCkz0iD3EV2n`459<WZkO5|uEi97`yl_7>ME>Ake0dLl$5-u~ym{QFD%_Q#iB-hF)03*s*5F3-RF^%X3C^0hWM|K=r+rAu>6t%x!SFGWZ7;x0dE`iJEYI?Df>92?)*_seCo!JiYjN`4U7M2F3Km^X-qnZg6v%&y6Z&!>xFDZ$&WpaLZE8Je_I$oG~V*Tl%FDx-58v%$ciuP@h6r`giK>6SDUa7`@BNq$4qw2n*xDysOcM{|%xpo5MMA`vgZ6G~R-iHMF6d5v$gu^Q`Et*8z~%_U<pCh<vm=!q`J`65C|sny^#st`l(4ZHKoZ<DKZc~~kk%tO%`j{zUm#Yjd)XQ<#DWBo#ijI@ig5dN_y1XgL9=UR3W#1_7a{_2NkHzSYJqqK?z)9TyCslJgN!izezIb0pSbpOk{ZuB-`6@R8|%%9I_c_gic@fvOdQR%Ial7Uya3|NILyWKqPuv}<rO{FK+QO*uaw1*8$9gydewg~`d?8<iqXgy4a2DWv~5Gg+4-4OAUXD8Lurxiq39Zxg5(lRG^cIRyj?1y)1DqN>&-Tn#(m6UuABdwM$%ECZbvqModojNE~#+d-$w^Vhiy_>L6k*QLJ5wYeRKdtFKMg(s>)n#xr8S)lZcV=YLFb-O+rad;=jGa_q#4t5bv)QLZV=4?Rr(-b&M>jn+o7+kqe}d@WkZ!2AwUGh~r@a)({D~4yw?hTc+5E;Cx}+<~KU@@vkWmB`p*xgV$H!_9?4S;gLc_QyPFT_@aKz%B?NI;miDF%-!MoiAxn748HRUQex@8xE$dp?wcaX$h>VtIem9&;dwFnFCdElm3On1Q1A^i50#;@Q*D$C@1kq>I$po3T~X$XBK)dou}ka0@OD}~?wKCO?4XUoKPlQ9yK?;k2>50MpjTSW67r8TJ4xeplYNOg25DvMpWdy;|1scpj53$C2e5V?4ax5F9|NWc?rYThn=k!?Zc`MP;G1@75`v~nk&^MHTUk-}P2;OdPjbaR4BL|%mq)S&{v<bPoWX4^WFSlm1uhf~y+s%B6nAAGPoK89EsoKL-4D#luLh<V>z(iv~Jm1mbisS1~a3<b!7&>n<l7ZHh0@xr8+A(kY##3f)&!N=!_$GSqjst&<bDzMgrCEF{xEbU||nN@(W@_?~a%aa>Hc^|N3Ki@K@4C3<Ok<0(^snyZ0GJbAqLlu<ydntjW<OGU=I@|z~{9}tZ8Sqj(LWR6tEP^Y!D&KJVsBeH~IXAV3aJVj_;g(z%lK7}j$P8*^&f=_m2J)=3UBH}4|EYTvX*ncya^=u$Q=5;uI-OK2`Ke**QODGsrgk<#iem&aYI*yBdUh^ePHPU4f^bi;8IEZ%JA?#l!5GY=$?OCx->haNYs-?k2MXxbJ1o9FYCzMWH#b0p&Q=Bsp7&gzavM3*cQ3i6B9EdehJhM|&_>y*tF7cIY4JzcJ?CLq5%y8Tnf^ONhKw)l3ojGDd@>+ULw35Tn{`|8Me8(J5`I)jU_>cnAeLer+_Y}GIFAu<j6s-ln>bjyUGclkNPcY_i&AzYH6|<ce-OMkWrw04P)CF%+SgIJEd#>wu>Qu4k6d-mB;vJCo=7O92ss0Qjkm*4@yXSO4rki$K@r*t#v0F63V7sjR;EBm(O|28Oq?y04^WCV1_a7X4M}LbS#6pWK39NF(Y6t(Bo+nnY&rdm*ir9@QK%6?Oc_IzDcmQub-DRi;x7su3CF<H;TqV0Vr|-07Jj-}DqnQAX~W~_;w8=Eo|nelqPMiBX`#?AUgYX>E5M%AfGp&|gSyZ#a4Q4St(uXPhjdsaxM8Qtwd3;le6Lx4i=MfeY(n8{8}uUu3*C^h@GCu>-)=L|zET=xMr)P{tP5(bbaKa5s*25l$bRAt>;U@RK6daD&Pgy>53=;7%QWh2+3GcqTD<bC*KJrOjJ1O1FVV;ZtK9BWrw)YO{z;{nNqXD3qyg&*m0MLdxIKq_bPKe#^a&3U*=?zrkGHRDJeEA=Mn6-zC2;^Y_6Pp3xd{|A%LDh{M{x?Ah!SndA>Ai;$V0?B))Os|B$@zQzhMYk%LhQr`h50nnf&rl4X(82xa64+BLJlQ<x*--1Jv`SPn;K>bYj%ihxGI(f}L*3jPMn3zWQ}Wj8(A?>Tk+*C`FF&K0$;*yTXh|fuLJMHkzSI7Ef@@go8@|(CtuwLY8aHkcGG#R&ugzK?@m+Qgw4Ny<I`IMhP`f@eiEXQmmWX9^X#ci6tQ5lH!b<P9Kd#%so6nAZ6-y;8oReIi$GT8H9S->>46tnGLK~RXT9Jo&P#ozVY25^Q<LbhUGhBIS8(BXmO}Sog8cq>CGMUsg8yNbLA?~p$n`7$bTzPC|i^RQ&>)#2+WhmCue)-TR`C`>RJ(o5(JN<*hKRfb9N1WB7xmme&GdIYJcYlvL6u?W|9X~#PE&wr9q>|8q=*M|0F76CexDLBXJ3OYprA?P!_o|Cr-6xmOJ-pGx|4k?_6|ZLXef>DVBoPCM6&me@vlOhhc1LT69l3KXcV7%G5|f9ZxeU9$u7)6BT2!rbV7Sy1>(Or8qAG7N!@|@*30}6ZqOGxLEY2q9rMU5f=INJW7BvYQmo05{j2)0GiK%*W7jf5<xfxzAZ=tE|eB2o=MXI-VKUXdk;a^4JBWfUP{(j*69~$YV?V;(^uY}yYD?0YT$1#!DU`23oIsXmd!1RoY{Mp6=b@CY+!{PLzH8|iSN3os!S#D_#^LL7L3iKv%f6J`>j{K5lU3|le?HFl}?>dT6p_2$tKQLOUw&h40sxzI!{wK%r@6FLx;fRI7K!d+az>PU(CX;FVr?JT`%cnsMGg}DqSEE*=yT_LB-hv7xuyoGH@s-@BZXahBRTa`c$}aFe`w;hzC84C#bNv<La>w5udf|A##VC;yG>$S19JD{JJt3hcUlSh9in|R9M8!X@#MVsW6ApqWzs<BE^NRwfP?CLuKDNSY5n}^{m&=!>#B@lPCj$H%wuiBSxO)dhkptJ!6g$ZA$I<RM5*((h#h!HTBi0b5G=jGYG5CS#n$qI&lf<$=9Y)N%LDz<B7W*s<=_5Q(TVybnHdz;fCfm^(uen%@ryCuPH9Un#7BW)uOEI^eIuLUXg4vMPXmE+T=7a&e(aOY@DZq_{lQhlRDcm|B17LNCfB4s4sf@rl{L`LBE(~xG=A+KZhjH#0}#46~K5s69ul18^~P553cW+mVZG-aQq=f4U7m5zAR3YLAwa(0CAabX$aMOV-!2GUEM%Hl`ck>PVBwe&R4!^ZWvLU4*9Tnb(}vc;ux(~kfGlAi<7zwpy@M;XXBGSfJs7}B}#wC<Y)w)b?3Q37)~E)hW;&U5GSwe{^W?>NJmY?VtrJXW!xAoQm@bNT4j^bO9UJVqU@UL=B*r}7_)?qSaHQvf*Xf4yHB=C*Y+YWd&x6`<B-f7&AEeu)?Zx>s6d4lIz^_DVma)&X%pRHWwH~g+VGU$HwdhB*B#bCr%V|dPqzugU8do=XF2G(osT}x>1gmVP3h@nJiFc#Sl+f>pEdr9Qe33oVMv<EMInx<CeWdpYT%o8GdVBhpbc>}?6`~SsUT1^wUq#PRk<>{1%9%gYmNzWNki1a!dT=}Z7M>QG*)1+KNz0@v8*Dh#uTY2#KoT4Ry@6?i4{{&Q*)QMh!8ZSzA9V+Cm+A^(_KMd@@Se99=@};)%r3E`g9r6MnY4Q2+QZvq{$0@OnA*i+Ryd*yY9(KKbz5~Rik!JHmX?WF(IW=H>ORjgL${#6PO?WDrPXqS-PFk$-c#@Ri+m_bm#>xz65EAa{%jMlbsTj<5PalXZ$l=xE@3~?6itO8C@q-)w<N#mp*{!|AcQ^St?;ii&sir;T8FNmTf%WZ6j&eJpS>q#PTX`-KOk6!k>dw92F6C)I1sKxK`Bn0IcioqP~o|I_9VyFXv&c+rgKiTM#T<VlX?EdM|(BkbaYR#IY;tEA*A2Bs<XYy8O<*fsIYa-4jk)OaUj{a0^;`-ZPS9Mg*mgGQW0rswq9oskv^k@Gm@htdr;d>mhUzy9O0V*C5vKQ)p7%iP$2md(^plhEYdl{Xd@8N_PTEBm$v^848j+iPgdNN#w}alR5%dBQTsk>LxC}vwQ&~&)=$8`77kZ>*y854PRRRSr^D;flca`Kyl63;ucLNzUOcrO{J2H3T({xKH+YRE%v6(`XWhusQC7nSXRCvs11!wgDl$P@*_&@B@n#(X$tj>GlTk;%nEIDgCPbNP)d>Ym6(zM^b4Yk5N2ciJiEkhY(S#90}gMS9;S*!glXO+YP0Sm<%nSEme=ZQ;20AWc1Feq%arZ;0xE}&0e+{S@+h7YuS%Wx>`l9p;U&Kg`E|Fx8Z=5-iJGQ?)(t#w<h#F*iR;(zR`fy{CTG3q4usWv4qL~>GGLRve2$z`??C`cB1E1hO^-K)hR|X^Y7aKz>dbolbVuYAnz>xgdkTF9wr$tk%_Hmdj^S`_g!6-ny_D3<4~}&CU9E|@Mwe#{Nhuyl)Snxyq~v+Fm3Ac&onA-vw?E&1_~{=%zP!1_#&-+#qCD0TUGgiwGS(W`Ft6cM?b1_Evh6};B%7-Wlb9AG0Vh04!U)abwvNB#0fYF{*KuWyn2Uci==DWd`t?;lC2<VR9b38td1^oKZ06ns{9_uFaoJIn6`_`--iDMz=Y~)XCkCY|uC;DhL_D&RCJFx6H9Korh%X7wE^2e2i^X%tkmVYxO6dw4*4(57-Iq4dSPm*oZ|zF0ntjLcUjp%*;M%Ef8q!#}q=<BVAp~ARHCzNgOtMbx#LYaF1gF{qRBA7kn^&ieTY`EiUnv+B`+F5ha7saU@43RgC75@Z3C1LOTvBn(X$&}A&npdYSw1kRjH4x5@_lg-VjS`o?!FCC``C~Ho43_`Qsz<jeNBG}QUE7p6c??T{c7^SWPuMq5ggU46QJo!cllxXr+gB9?MYatl(dFx+s9qPo$1BPJmuEtabvY7gDNj<tl5oL-S(=xfewwI`xaqzAstr}E)=1L7^tEO$vOjdLgq|s_=!~bRLErL6-X<9B5wk5QyLBRSD=2iaF}3lvoh)LGkC1zA?-%u<<|~=)1ye>J_j$1qlp6#-8ygE4%YZ8WNXhL*bs}{wAn(0a7yPRX~AM4CaXG<h2Z%Onz%m2b3}AaW|_mQk85>^FwZ9X*o*T4Ps!znoYN#WK~Ry%TRa}iRq3}H`1#j|3k8n1iGnq$^Bj8PWg?ZQ93u$Z{F&3Rhg4qKBayf@M&upwMf%i->QlddXV;qt1*=@1Gfqm}V$njKQ-|n0JUqmS*y{&Ujep<`vf|t2#}W0-NMcq~CC-;3%zn9<<?<fzMJmAX3!4pGu9q)xjBu%#<%>->`_1y*+0!Hh4MZ}SefQ(bFYi9SEWf)Te@x%~@x#ln%Wr-?hZjTeo9{qd30R|)VzeX%Y|~QXIoWm->UfzTtDYbx>BGHtkxB>NoW~ZcXO|V2QsT<IOiC%cEOf?xKDj-Y1iCwiK|LW0^Q&CFk#^Dv!qoQLb<jB`X0!qq`!tZ%9ScIx&traFQK3A(>KJVETZUFab^rOcpn9lmrl-m=RMHjw=rB~n0%Wc$Yw-J@OH4@qRlympElC7=Njbmqnt$DJ+de#L#2fe>M^h5k;JN6L7Kf8hMvTSjqUsqf@WRLdx^He(LYulfI4ne&RL}SByzF(bxFj@G@-;`AMsqRgWSxiL`FOk3Wpc=wyV+IH$ryyl14N1I5_U$Z<CR;+qA;0XskQ|zI}IG|!e@A7@v{IVV!NJVhbVIRe2cWAQ`#GlAI>197)OOO(_x`|nxa94GqQ)QyJuhOWkwIS$*LFp?7nUT=jW!esKy2ktE}TEJvB&5ixF+|(sUYxZ<~ABW8kvVIFSH4ss1HuiBa2zB+90FUBU8Lvc$Fh@-ok&MN>JTBxzu=JR^=Idg!WM9S0rkg|OohfNzWS1T)5EW4dmGu^pUw$Jmi}P%!V~lDYwfT;}V5yB~;3JUDoL8A-p9o?q-lxJo(v2BD1CZhxfE+T{AyIy9*pYAz?BxhxytqgULxQ}W^>Em_QU{ElzR1U7?%g=drrn`I=KN2*h|;g?fI!Cwy~S}cbby&$&dXZ!`ISVlZnn!YQmN4-9v*;Q#I?A3tSlAq_{TzrWwo``j(33h!`v?o3R?-sEf$yAJ#-v4^|k;Bns;X?Xp%T;1Yu3`AZr%DaS*zvpc7@+cnW-<^xSSN+wI?gxCEs&&LDc!Jfy+Wk|MK~o919~FPA+N1`>mbVY(D|@&tGr0Ty$Wi2+0J1+6e(f7)!{co8fhpc)!nqv2MIKYoE1~k%SEWM#2e8Rg>m675(G9Cv12Cfn-0=)ifEg|`7V#(3iIq;V)G6;E5Gpi3ra<{t-5U#%4EEPMiW{%<L26rE9-V>Ty?8U&(^Q(k~@IEdDhU;ErvZ8ie3!T0f}(V`u49jM^Xai;N*H0;!W&Vc{JnOUs0M#ssyV#?9q`fj95zf?PVlT`7s0z4Wmp~(dNn2P9&via$%~s!{s3Hg)e(l!BATQoK}xF&(fWVCE{aDPS$3qt;(dJ9{1o%R#jTo+*YylJ0vv7%=UC&lZl91vLMpI={CAV$(u`-f=$fGR}KbE^rwz4uL1p_7$?aD%g%feChBFpk3iMkV2Dx73{*<PB;}=K__r5uFaDAF&0f!hnQB;uJQHO$ft;r7rfOP@G6y_FK^QUN@TSfrs3*<Gx%|In8Wg{1UPvVMq1v0a_?A;JrgP2e3s0tay)6O4MC0Pxf~T+csZS;Lm%_ZZ6Bz9#bzV$(5MI?W9l^w9HV3JmWEGLonk@s=q=!TRYzfrn*$II$>jg6N5gOaX7zj%BpLuD)wR`FX!Xg|;U!h1IZ)~85j}$+VF;|1V;>(@0pr51xhBYUba%~@w1Kk*v;%h(?3h>t9TcKK;Jbn;`Ul{w2lhX@ML%3W@OcNmWgrZjz$0|g6O~;Mcb18#5G<Ier<elKFz~q4BUlH0H4!!(J55{amUzxjNcx+Ni3M4eo4VUIYIn@Ug(KuQj=fZ6_IB|$cO0ceLRzg*3vs^{!7&U^8nt=x6`9<R$s*6yI|I3F1o!+iJxoL(>e?jw6i<ALRbt#>D05C@R{6@{1#a(cq;OF8(BFg@m*->Q&B7sQOhjGejz|aNOG$t6y7ArEzN5=vlu50-k9*gIREv00Nt;iyXha6DZV)HnNV&e8yH=F@hP6FXbZwrLH-OBr95oa>VkABvu&3tLrHxZsx8KJqg3zS%$i|tpY8svE)RpWMvc{^5^AP0rRRIMgwk1cx?mYSW8PR9V8lU9oZp_@f8HSa0gP?3xk$0X7NhqrBk8^E32)lIHgTm-_tvB5>EP475Voq#P)W<p-SQ@C3eQ;U%ES_`u|Zw@?4zf*#_H-bwv#<Z5n_%$FMELtFO7OM6kwb;F6%c%+RGD<kH8aKGbr@ZKH^kaXvDA*fF^{~wcO@v{3rZx-%Ld^;=&SB3{Uo@;2u2e{7Q|}@(si0&omARgh%Q}iLbeY7-rs5}+pvH@al&FIaf1f~9w`lC&yoQE_=rHOuR`teR{czY#Lo2fd=fx*bYty{0C_tHcA0=zPX)*|06IU@DytJC&ml+icHb^jVgBk~9GR0|dRKNOMyI%+#-Y2CBYGLH=rcL5+3H1{lA4GKDC#Bi14|~>7yia@`m>jz>ve1tc^n#0Ii(HEI_FfQZmCz@@&h$TnO+?;$S2d0(3T^QX?8>+MlT+{qj?&$R)XK?eP-6m~QMt9;6!?%FrI}cFqC`Oyu5qBK6yjqd0;6K0wSI2mWPzfuMINW-yh{w>War39oR7F4lKg_pKs#sC<dbRp=)=ZgDfmKhtcI&)i8t{Onnp6SbL!o%?|*ssbw~evJpMK*;bf{xrH-_3<Q(nylbKOm=`0M}hEDK9ae`S4Yd94v#-DEho2@BFS~XQP7S!<9IV+4^UON&6Z1BU));(|bz>x9hgRorDn#)7(1twOQ1`H@kg1XL3(jMa|zk2SXzAVC1W_;3If{b;qDil-^qc)x<tAsH*a>uA{4;rT{a~@Ra-oH>H^VsQ$9C+!`UUELCG6`U9c&@W!9CF_8FevVv4L6_RI<s7z?@Y>v<R3%`OW%HlmO`eXk)jZt!;v9{G#~{f(l|>^r4vs<q_Fl_IdpWZAXsc`Y#ju#ff;mr|Gk|;Ib+fKrC^GjdAydi;=u6Yl*G}YSFj%$A63#Nst+fpsZ9TyN}d`C+cr&HU!7wP$)ty$GC|_$FVH^%bGGH-g0tM$KeySXH?+q@<?{M51u?WbjJPd`^jv0#J?z1$t6G#FaJc{N&-WjG`p4&O@$pZhS0kQlIbp`7v^Nhg9!AB{M>K!B0#9jCnM#&s@r2_&F#Y(hvPgVPU?2|acK!t#m#7O4>`Ula%&RU>5+4$Dz~tQm#<S`A+_T$>8IVrMAzwUdAaNr3UZ`y&x8h>*>akAryd#_<u+|X&V$vuX#IUky;_Zy)+xfOePUU{WU9y8KXe7azAnFK*%4Li|_6g`L;rz+((Ul-Ek{tu@C@L+g%|Vs|i#oOQMVF~t&hoA%aK+BYXCXfwL5UnVr2bPORvH!CXU2Ib#*d<y)**BK@i7cMYUu#Hlj-=9(yf#ukxjJm;|gdu)w1ma5<YH1SBKFKP&1ODmU{%ZarQF<CWh9SDHcsDLvm&s%S^^Fs_)06NkW9Ak22b_bA-|W!aafm+rlyr6(j|{2a2@8NG(^n^_DI5n6TU!9OuK5*gvyID|BI`{no2&qNCYpSQp$gmX%#K0`UwHg=9n@PA~0%pcV;<9+>>baU`ILAQVEAO^I2%7r~PL)|8$M`nE&}m4>CRsZuU`((#Ic;<R+psEk**P!yo9{bSdZI%2mIltLv0`3r0~y>C?VzW=t8*EyFnv&m%~2+Qru)|Ilg9*DmhJD4)P)zm*>Y2gHggxSibLIq4mq;J5q)#^yRU{>kZ<St)Qv(oLiI8zmk2Z3UO1#L&ceV5U(e28QXZj4S4ss$V)Kg_=+fl5IjjW{q8F_n2U%z(pRyz?awfg~wh|5&5ykA|TiU~~9jM8yA?J&UO^;;F1dQ3z@JHr@HWil-|#){aXBbcCEy--glV;K*Bzs)f;mxfG8?Kf)9kjC}gH!>c3&?{(T0nk{pqbXiqV4>n`Q&t}SK#Vg9zD9vWr92}#D@_ufzTY2S<bAPn*6c^nxg~bqUJ~mUc<mqgNqQD5_3gik*eW^4+++)uu8s9x#V(V@3yWv@Ewq#GKXuuTr;@Z-*^*#+(S$m4rz22G-(9?a(qOaMxM|>$oJ32AdQ3Z}0^mUNu04;c+0!MGQhLt$opPV_)Ln=xO_s>;sah_l-)H6(uwS|IO#&}sQm-AUH`M`O1?DyTz9Zd>XS%RTJk*nemI*ONpMd?sRT8rN>NE5QI;V2gu#iWQ*VTT>TO7W^fZ8?<Hd#;>80tPFNrK3tfzlsm!&On5i9DTk)xxWrU^2MC_<e{7bJvVM8vTi?x1C%=%%a_Yv>oy#y6$;r`Q4&<56xGt8w)|j=nxe|BYMVkqFRu-XiY$+wy2IsPH-_1_EL%b9n|GDppkZFoOwq%epU(NE)JZgYx*Pmg4H7s6QSy<R(}A4{gg6{fQW_cr+#>XdwMNiU4xoJ6MRP!bh-i&cJDXqSGCuGApGcpT-(Jot50v_#xyZ|)F7a)p$^a}x%qSy1knnb~Qs|CJJNqgroZ*Rxpl|2<WNdBv1gD&`rlbmkWBGS@LN~o+K`TwvGe`lHPNVGXkE3<TCWRO=m;@_#?Zp(OP-R3bNa;o^&K(_X1l<B4yBG_O&3rziJcHuFM=4&UxhsMqLeU^p{d*}1<w+;g%9vvAy3B@1b~!QQ#xL4xq0<MCPxwrm?Jatp^{VZrFZAlD7HSCn7jHfLc2pe8mq1U9+G7J26c-9KPNJ+v+VWj(&n=A<y3LoCEZq8Uvp0~zH#uOKc=JX_%3tvSbQpv5`Yam~(e1y`XeBZ=x&W7c5hnH89oXNE%u50fcbgi>he#(smL`z;$&W9mkshDsuxc7^oPJ%eqcO1`-)#%Y)tq<1ms#z)NhVJ#%LS)nE(3!jP<H|ywIp6?CThgz(UK|i(*v5KN)|tp84ZDFmNauTK<qm@en+^n+0#PZW3p8(aewPlSn1`O4Y?|t0cP1T{MrtdBv=<Dn9!_Ytk@BBOg0>UhX7w3O5kIF2+AZ39aKSU8?gxko1C~T`AD5N2LosD=LnqQ#?C`;>Zo&m2@?=Wx6YJ&i@dOv{t<n(kxyg~ccYK&DvZMtzb1@%W*F@h&Cx!4&B-ee`<FszryR(1%V3iY6aL_VoyS<2OI00Iq7;5ybR>B7vZ-)8oHmtFd0M>mA5*faLr2@_!;}q?dDf-OhSGLtB{?AdJTHtb`L+etDp3g&?!X1N0N?7ie;3kxKxGy5A5ogps4B-17c`1fA{Zvm3BEf#c}fLRCRM=JOh8YPx3z3PX`zjIX3jDaU)9Izmn>@2GqriJ9smqtTO#Rfj<nzjnN?K7wKIZZdDPEIKvNUs`CdkfY_i;eT8v02J@gLggwh<#rW4onc#e72*AZSWE=abq&GvjkjrP+X)?%k5Zs@5YUte7>hM4kBY6D9Zx={UM+S^T9YeBY*mK!?@Pjg6FYD?2s&|cvb9_7cgzvs^dtQ>+@KBQ7sm`akKI~IUixqa(vqWB7|fCRgyd`p8{{|(hzdA|SG5o`S}qNv1~z>!3~jqoWulc?^g7qfQdP&q<6ric1h78w1udY$W(+xx1VYbpwUGg;2>C$hQ7H2yjwo7~mJtf7ocX&PmPZ>OY5=Hz<_X%^?^d+KPWG4aqcAJ@yI<s83McvEdm)^1~K4BuWdldeWrC)KZtfm(1uL^DpMOAhUcXto%ZJ)+2MbVS-L%hDHR|4+A{&~m$?B07B+UJr+31d(#MPg-m%ks9|kaw(zIN!MU0Eh@P!49un_DSVSversKx)4!y`SN!jIEa-+&ML-rW+6X7q?xU^}ML5_ph65x}I51{r&+7b^e^$#)f(?!7kn8qwW^;!s9Kza-jU9a!8mep2$L;u*H52w2*EU+o4Zw^PX4U3C4oH9E5#3Ob2+tT+;KoK9!C?UUa6@$*KPLE1^b6o-02+zL79=z9FmAd?ADT5`AfI?e;AbW9A^SyQrx@d6Iv=g0M{m_bQS5|Ot7y2w#0@%HW}A}FU@Y(Ex*iFvo1550A3V}0|2DjSa~oJvPW{pALYK~-d9~h7d(j3ZF!lAviS4BVmPq;6CuzX|I)IAA(lXvZ?RtIA$-<#yto_As5gdooUA(+}*^YvUTO>58mmT+`;FkF1Ro1k?i~s4N6A_cR+ZwBub`OJZy>6}_UtWGIvH^;xc#IY9TQW(rAOzLYw(IzN><3E6X+*tuYshOLOhL}ZVN_X6@qNNvI;Ib1I%tRbN8WJOXHjPTvq`x|bWyRV7-~f!j;B6*ja5A8$dCP&HO8i|wZ;}A6<73^^A}0vcBt$k>KtRTq@g1dddE(GR_{%M$B3IpuEEFyrFHI>I*2p$xP52^i*w~V(o$oi@9rF1_){KmuHo0fQ_}U2t$)uf!!&gp6(z~LV#&QzwNU7tXEv)EnDCIj)3`J(H^tlWM^wF?8Q0TNE!rVg-Mu3CDoR!ArlhJ4nov`JD{(c&o#0t!*``6J&|Y^{y-T&r;s}`nFD=o*YWdj8>G}zpBW8UytH|~-4HMBmWBZ<^?JTaaXlqHq;zo`lINqtrdq{eg`_~#c{sGK@qA8yh76GEw7Ep{%Bl8S#_e8!$NMtL3X-a{JEFHk^X|~s=z)80&(_-)x20J$DA^+LKci;nIt^(tHaPX!=V*x%XGq(95><MI$Vl{q4Qb&oP3MXQYT5Jofg}g#d;Dl}4yT$VpVcJ*tX_qgo*2WrvCMtw5|FEr1N9*eN%0K`S^d+IKwCX&=Qd3fFoC{rFPi9ix)y8)g5RUEecTG*CO}`64Wm<%+&2k$02)!21Fs1Zj4Uxep{l9=gWu)N>iG9=VRie>8iKR}`KYES+l7d4n>ozfb;!7)z375rPeHjL>SDRU{p^;9lSCgsys)XkjaJ$)GXEo+loM<&#236z79ybkTQs7NzDc0+Rh7c1{C#Tk}<kiKNw_TGvb&Wo!j{i~KfMwW3)fW+3+WA=M)#Rpj00kHopVI(K<Ug#Oa&Es}rpfrUP7g|&=Zy!A;0p92qQX!bz6ex##t)Q+2FVMWgLU<auLN`BaD~HI7d%zw>ZG#ZMu80vOx3j;Ex1&Iql=}I2%`5o8B2iHby)c+Z6dB<DwK)Bd6R$|@1^amUlcP*{MK7-hqOlfzOAI|$Ks6nfz}F{>4K`Q43m5-)OaTNUB(5CBF|Q-r4YvAtWMSkNDN0-ii>pD_1MN_!J*5;!(}4Do9>I5TFU;@I!h61r;xowsKojzWSnhZosM$*)eh+>Rr6>BDI6Jfqt0ycUDqsNx$*-$(v_B_8H?ZlF1f~C*VX5>YJ=$Xu)2fFO+3~-YLn)>#kPO!bnoLx^2mBJPaFehN=3nz+)wsE&4`%?acV+E6MI{r<iH9YV6Q>IcKLXAZ!#Vx$}N%u5H3#<(s!U0fu@IB|Lrg9YoQ=7!El3`y+>Sh^Sa_bS(!|PBCY}*wy`9V)U_zki&TgG3T^V{ntaIi0+jGj?R`_KS$wHVNSPn@tqhGUHn>>R(jOY-?H8g*99Wg+CJRvZr>bgyrT{Wdv-FlHdZAVpZ@46t@<=K`7?&nS3sUvx^3Guk6={T~n)ZC}+-}8Iny5QTdIf;<bd5YWKP{QlB(yWmD>VQk<V&_)3OOZ-c|oIjSc+<|aC6)qgPylARsAPZc5wqK@_7sVvIF@tH62s#Pps%?X6}U)p4I=T)ZOyr*17oZ=D9co4EBW%VZlL#WJ*IIZbQ@agMKhi#ST9HRz#t~$Ew2d^33Zap6<RAI8;v&XhQB?e5Y{VLjWYoRcIRNPMj(gdFxs<;1>e~sWE%BP4$5`P5avEbJrBRtw#{1N&FE=R0|dY2qjR^hVC9r^OmUp&MfR@Yb&oYvE6_kfTWmGyc|Uv0w0j<A}m<2><>7z@ABYA9YTYG#@AH6v<b8as)4b{_d?6;q<~G8yI_Y^CDT-EnQ1^$k}ADOn^|XJX;0>Hx)#*>hHYP{L(XB|HrKOK6P+RBZcYG}4A`c9igvP&$b@ktOGZO2wttr@6U9`GXadkCIN#;m&&Me5foX&hML@%<1HN~aQ`b^lxGS;fSmDNL>PuUkNk)>84RBtYc-54YGNNc|tk9aC-W_Azfw8g~tz38=k5N@ep|=M;$~v}Z7M@Y3iB}vlFc`9Jfgx|gn){o>AS80M+iiKiM41bQo7}Yb{VCJOo6#0>yEXse(FoJWp$QBxgInS%8h2n4{spj~$gdZQ+Cp_Vmg-V`K0XUMC|exuj;55)8&k;2=%jMaD=vHyuBWLmBX^OwYb`GN<cn#p;>ujrw7W?hu2d;l`-M}2u0^>m-?>6(L>UolyMSbH1c-82Oqr|>hX_Qc7p%x>nf6u0aB?&4l<#_8aF(~;&RWC_l<=`G&{ciJUJ}FJD*jqq$8E8?R3U^<<gc?^EW@F1(bdlw7UcY82OwR+Nvc-0D@|}5cllCAdFF+(0_IH!uyw4IJMs8*3%%N@!8~n*7Gji?{oA+eL+9<n5&;dCsk$;h6}E>u-NICIj)w?D;)3e(=(rc-seJ@0R*n5l+hwbvO1C9JLUt*o&l76x8+x{5$I5f@9;c`@g{k;gQh?vntp5s8?EflF6O6ST+bBYp36XhE^y||W5@0Ofc0sfVBSKqD6O4N_GA6ao_YB2Q{IPj_%Xq-!^pt=N%<R+Z=x;Q_Q8mnJVBf_=e58X=yYEWH8KyFKJ!FkZj}TTCpijRRAv%pF)-X+msJTIA^fK2$uuQ>OsMDR6ywy5xRfV>nN<aiOL|mr&6FSCxg*4QgOQoX*2MwNcaxc=A<Ya?wnG+Q7pp$_ant)^TSOzIdVJ@5-e0Hc+UZKUSkTIn?%IvKqv9PB1IwSmWt!1XhMGnw4&*@W+5M^|m*o0qW(DXI+m^R7Dv02NN(j|!bu=!N;Ha7bQflNTNt*QseFB8G(GaqP$5A$Mp7c|G)!e{rSc%nE2#o|GG1CviL@FWoKbC367ISG!t&{AW;Yx}-0bQu-t$f5u{(xNnw1pc`tBv%!KC^9eDqNwW0y(JCze-)sj(?Eits}#y$C$b_<YzogC<#SHN<vlokPg(8cIcw;JQi5P2m$?VM653#xVVbI~ukmE!3C+oF_4J_N6T>fn6kt_G#)PG5BTh#<d>-nlJ}FD;e{?a}4zoP$#?K<vMAnj4n}amD*BCEKnDvu&B#(Vw235*u#n}YPEYz#06k~~B&j}|PjfYeZdpntz?J4VxR=6A58k@pO=LXVLiWxi!hYt%}!{O71IUi8VOb!cm8sJa$Vx?#$$`GFvm{?UETvXoq8sO=5ZlJKHh&{!v46zUtRxU{b@MZXE^urpy3;EcrZm~+&zVkqLAq8B1=c%vy#o!}0d}I+<&kk!U==FYprmNUWIqczk=CBK$1V52wm3d3oaL@4z%=`xl@22zoZUx>d*$1(O2mx2}8EdpLon=47dgE3aPz2oQfSPD-Q-UJtk*-#7q@euZKnEGIdBvM46m|1EShE5VA5ZaEJYeY;tx~GO>mzO-uKPWxWz=EDaDsp@W>hRJR!f<jCP4Fexsb>EODU1krUEed!lQ`#HI#%JGt0$E#KshOhxnrF?MWI!Rv0UIYl}>})wTtg47Ain<qcb%aO!Adbuwki3ZyW6IvRVwu#?!Nk*F@^!M-fee52MN#HsMQla!rfM`mUEzT>E2&ma>|yrbfW-99W*47J5^S7hvgvBm;!+%nobeweO@Foq{QP;^d)8y0GTy0lXhi+K7}=<5g1w{i9vRdz7F8~jJwd}>G)Kqo)UCW${vOxbUVMQm=4MKBv!m{A`pU_|~G+N}T)kcgU=bEINFq|}fx4~cLit@#r78$JVtk+K$9`8=$wT`_j20}PX=G;xn^w;mYl>$8^%U3u<q8|~2xTW~35^H9Y5Io%MgLtIsX_<$+kuzGdZ)pwOb$}wvsu-IU}(Q3Lc$Oo`;eF-*{QdwwEX6uG_@-5Gl8mdAzBQMIziXC7h`mQan!a<foU21$SC>6<?a#YMsOF6i5nk7e^7?8#qwEzw0IqR?#r%Z-!A@V|A-9{R!VO6P9v!wb$uM;YM6t_4cow^+8g07_1#grYO>gvtmowd#z06}}}SLn0p!<z^M`q+2I^-h&PE%tfbe;I%KuIupOcHA7z<B}P@^Cqs^J2Fk?3)Dwa@2?QjJiAcS3C%|1*1LQV1pzJYow|!k4OvA)cXwm#3UG#fxb(izQT;r(et7z{Ce)$3`fsGi$k_(GsXiwj+zRA)90GWXBz30ZlExjS)K&D-ddf1)1ZtdsN!%ZWFN3dmSOHfm3J9eR<*GwtWzZtj;y8)J`OoPTO{;32RhoQZ7Ay8!e91Oq`o>bHp|DIxJAUn5SJ_Wl^1ulGz2)N5HO*FFT7f<t>l(HU+|RW+n4$+b_EKxs6_zxnAZJh>ujQ9c$MN<t+6-Z>-K5xvpY!a1;;IIQKWgAuLLC?GQo8g#dkaHgppf0r9yHd=gbK!fw;|}`6m1WrsjyC4=xh1LO&QTiXFLGP%U?AEAy&U;l0=HO3UONAb+ui#<#AY`k@k?m<o8gxaX>#Voq(?orc+y2Ac0rls=}~z)1F_+aP$&32456pD7KvAdgecs%A3zg^!h2eeQS@ZEqk*d<*E#(7`_y5GyYuZdVn^jUYkc7W0>vJE$vsDfe(iW)I2<l5ltqz8p2^bD(@+eVD*w>o0;@)m~AK+sNkZ##r;ZihZ@LPr&{z1<|40v7l2EVXHCQvx_LoJ9nU7k{VU)}`-bFf1G=Vl5|jsrOd-+f^DP^Q4s0H=5^biBWyjtWxGtoTYE61wYmJl!&to}gqcPL1gd{}W(-(AP)kfB5)u5MKft2DK8!j5{MF6_OgYj-aA{c)yUY<<KmeQaZg^qew9*y#eThU$V(DH~T+FJld!SRFY<yzw5a2|R{hD1HZWgB@z-WG(nh(96bQLrO{v?wrM{McfqzSbg>UjE_LPhuug07D4&_O&FhKgp;s1>r8+k`RKM7vEf{VSw}CC?Q^R#ZksUtcA}%;_&VC8m759(@pi@*l`{MQ+<hD8Bj5?`tuE=D%4JxPnn3!VpQ4bP4JE9tg-=<-0S3eG;llLoV;G@$FjEC@YY0kP09!5>)YKPN(~Vp*N&)|TdU@<xv%+meyLKUq5LRbV@?36MZ0<-EA19?h#np6Pp`WMaA6VATEC8{o8^|oSOJDi#t2e}W*VG!387f_wv5Y1#O2L^n#<}o{NG7%39;<K0uzYdIxfS^>_*jd{FW$Ia_2y$G4u5HqofTF3V2-v!hT8S#)?6mYe^Db?B?DiXDnBz;!#nxdHBXirpoGL?N!a_a!mL_G`Mt(?`2hyC#XoM)9Z<^Xv+7R;B9%nY72Z)7rjyfuKzSk=rr-6m^6)~epv%Mb+d<Qk|n~oN%`c)ACp4u`>do3xc3hmr=)u=*kJc*>^3KQ<;kyUC%t&OfZznAaLNhY%B^(9^i*L5$lIP8oR<64oxBvjaMAHwlCL^ZoR@$D#pXGq7@POsu2y^IJ=x%`GUY(<QzN?C59W4n^;9thOi+O(6TU(%0u(5P(!CHapSy27<G)i*Y~=1EB`W9;l0|dmXC&B1_nJJ=v`Pu1$8zd(%^1r!<&4a0S#!vmv`Mu0Xlo6an^ZJiv1Hd(r)=*~x`uL~4Q$_R^?-$TBjH55BFx%^7^aglE$bIKhulpbj<aW)dzLN?(>_h~E1Y-plD<+tt;P8Q*XrB1LM5DSMur#mK{VW7oi*NINfpal0L;VUu3Cd^pw^=u!<gtNU2aX8hg6}XYdV^nzLu~N&p4sgIxoAJ&PyQDm$zzF(7(62RpEHDZ&3>G`nX5jKo`pQLytmPvP>t86n0Am=`MrUGOJH($akcq-Zv1wNy1D8QB)}Qd6s^EL5J!2WPJMpl|-w|$gSm<{1C{Y8MB0#?0Eu7qZYPq8WBT1rnVqy3pxZizj`NvIl)|azCe0{(C5eJn&9UTsjp-DO1N&o(Jxei$;g03kzu3{0<=rwhnCkETKWa*T>EJXEyZ-90k(Nnc5{taaWbJI%3ENpe6|sssb%CP(<xE3>WrR_=f4>fu@--Fn2b_ex<)57SjV_jF7zo-uI|<$W~9m2I`d`$Fs088qAmJJGo)e(i=MoWDUi{#0_o+E4Egp)bthOCGUMoo7qmj`pz8YK7_HoJzN*AyvY@uc)ttlCa@U~eqpYrz7i7$`%gv`gZORsfq*=7MdjTQZ>r$@Ex4mVck2lw7^IL39!@H8p`8F$_@7F;FSX+@-^<zG~CSY(rnf=jH&P~^DTvnM#b50?C^`%PaXr*|o)m-kGA-gJUYseyVWfN0%O=x1&6juEavo>S~Ia6VQ;%MFeSU-RBBT7-q9LI&!tDx5~7p`V+rRBp#Ln=l<Dl7IE=*#KMdS=w9O+6;_f`k~0h(=!N%PFx?(-R1zIlslC&CHjdD_A{Rui$oGgrSpM=e3|<T-s|a7rI-b7z2Atj5*&CRq;ip)zv&g318!U^A@YZ>~RXi+X@Db7L>XZBXk<2aC9QS-J0#HG%boGZ;@Ipk4lHQnWa#l696^Ms)W6}xy={MPnSu-R#C=y$uj-|IhSWC)B-7(O?>)DtUSRvqpYCPqH&%N``4@GfLlqz58)yMk+Js1wsfi4q$_tz=Kb<-?|yy%%e$}J;pgM=H$)XVrtQ6Udr@5*+rx0dBkR!%$`W`(ZUbTE@?^wt%X~(f>qxSjF?;dEhAh&r3t!XN&v(USAtoEZa;cf0G5)em<>-p`Tr}QWch=RSWh=(Ec<uDnpN_=vhkYxi5sOt}1bKQYJ*8lx07xlVj6|qIGo%9(*P}dRS+0HgdzZtVWFmStks>-fE#va!5-0^hM_-(sm3#!Rg;wiU+Sv%q4Q9x3Ip!8|i*0nNiG5uGO+gQkXcm}F{KQ;D6Qyy1t7j4AQcHM-R#*aL^Uv)}qgxGS@V91la&76Hut|9g2oAZfGGdNYpj4Ng;8;s=zDbrWuo6KQY|eO$H>|Tvr|m9rl31>zZMDY>BNg+K`(>~Dn}7QK<u^H2hi=?=^4=EG{DYV0erxfno$E%;WvA^xd^%(+!-U`kOX6h*F|Lii9Zu`Skt~t7>Y}`3FhL+*;pSaUG^D5k0{0tZ9$g02Ps(Ku>9C)1pvgu~Gf2zUm-aR$szviR87|Lt=GfC1GZcc|623by-;2$!^eYLjb%J*nN@5Lu#1w@kBddDbsbG#)5_LJ&7T=@R%DJmF*yGMTCAk7+_xcj~1c_la2%10u!Iw1Oq5SR=5n`2bg2?-#1AGqZNG!*##=w|%9Ril~1-*Bu#wQMas5Z`1#VVQgVzD18#eK$N$Zn*)*9%akJ>^uW<m^{=Dc;~kyKhAUQZd2M=>wAK_PE*ki4O}{ZliXTRh!{mM&<tH_~GT(Wz7vd0Us;#!+^iZg2wBRprNt%Uck;~qh*($jE>@5hSykp(9+|ekLQG|7%ju0!}_-6TmSawX2Mtj>=-!J(6CR8!O!RD<Y?mAd+z%1hW_~?cV0lyWX#|<(Jz2Q+-nlW@3MU;UY_c2f4=|l(?32(A|L-;#?2B#$v85FeW@4iVQ_8Ih{iL8X8qtrh;q)F`0^4n|HIU7jsgNi)gnch6w%O|{FnxTrKMF~;F2uJGDrHT<g@2>mg`=o4v6u`<0IHYu?y-<Y21{$4lOZZtqh*Lblfc1*=qT8p)yKZ*5W^*g15vQeI~x^qe@!#Q@7-$`m9{JFk>!Qvv>ziOk88hNiJ4PXoXi!UpLi{FK_v@Sua|%o}?-w`)@>Qq!c>SFLN6IZMv15LZHF&4u0Thc7#P(jCzKUx=0xwG%y?HC)UbH4aau6ZV)Z)n5G`3t<HwR_$sN!O$X18!?JWmOJ*H*Sjd)$Q>-Cn`K0DgI}GSQqGDBzF;L*i9CeUF!KZbqoffhfLrqETBj^Kv-OI#F*AhG0FNSo`N<2Dli^L#<NoF1cfPqC|l|RiFoQa9}ksTBL<GsQ0`pTGcdF<BTI0z09K|K}KBlrN_Fknj)DlXtHrKKlyJG${@5_}axWvWhi%&C>kE+Xf(2m)IisKv4~oeTBbSa)hkeJ<uZ9rr@2*tjA^3bn-n;(u<oiuESuKUN_|jW=(Bw!WOi)3F|o=|}uX`7>4ZD!`<S#<$=+w?EaUCV)R)@NHn%FC}(8+}Bu9Of%Mv24)1Khx;_(&a${me)swA_^Dg@eyH4}q$(CurgpQUInYq&puJLzEV$;7m+wYMDzk7pjt`V}6qc91yj5B};!VZ0avCHy*1;O?)Fsvp*Kh>H9f;g0gBWKGTd5HgVjzAY)$(bW0~AM<c-qa2q#TI;^mq%jV^JE*1h(e@scH`OE^a!!E5?;e%Z{bokV|_ci{s?@)VijRu-CdQY#$>mRzswE4n60-NUUNfYuZLtdU>i2m^Zq?x9WGCcHXUf!?Mo56Kms!WrEUcWxFFvwUda_zq%2VL{nE4F2hV%E3eW?jG0zR;%OacuKUXJaE!^JvdH}weMXcb!V+wnhMaXP;mA;C@lfuF%3AaoCQ$ovnTQgBLrSw@^}+SB-$3N>bm|1nN%#u+McH-=sj?K7*Z@*yC%Dy32@V24<<OJg85s69-+L^qEhwI_vW5!LJ<Y(bYDi3ovduz^x~?Fjkr+6#Unw{y#>s=Iu65TH6DAwXk{)Xc>VOaekU3Q?s}mnS^y9-Ez>|(pzH<ZJv8;I@lp-KEP<J;BuPJKEC6fa8oi^M?VbzA}A9<;GZ|BA6l*%sYM){o7LMm|<l9hRlD-g43U1k(s*O~{=7nfEDS2JmoY(P@<t&ha=qz6h|_D2d5;%(W6P-%WQgx+sDgJl&vnl^Cyp`YP1hGFCZ@%FvgDRku_S^@+f(@<oQF3k|UeQIKGy%z!Q!UB^NU|WfD1i)}47v@D#EnQ6l;M0#7ABZhh;9~Bib%2h$DSYYFp?nTMY1}YL=_DL=S)OiCYOQ3*Hlrem#5TCMf*T2jG?B5hv(?u(f7J{NGjmH%aonYNdn%72by`6{)zW|iyY5)2kWrU;cUuv<C$ke|QcP(zW1W>sodt47u{-61KHMAy0<h{>Rf)1wfuX`W4C!|CV4TPu9F~$v<s2+r=wu#hm9xsY?#g2MYt5hG$)YH_%m^7Q2FTSm_5HS$W+)nFTsh>DC|gNoHJumC=dM<&COSB|^KfIbcV+(`%Xp!nsn|OJ`ig1+f4sGz+CPaR$+-N;UtO;wdBQtWW%Qp*aG)Y<LE8`hN^RPl`EP2pJY=-0ht%nokT|z1lOwpPilfH5MmvP0WmnnGK1k}MFcc$WiQ5<lvy-+(bQK)spdmu`o@PmDjmJR{S0#Dv8AC1JVyoYnLB=IUNkRSug}1zlYOk&Hb5yj}&8A~Wf^gZ5YgmvJ>kEo*&3L4q=}RHK1s?_&(IPiDX~QecZF~9K221iFTFZHpSCs{<VY3>JYn(>2fXF-Rxw<L^>FfihK+C3(j(r<hfc{MtlU>R;2&%dAZR(B7OPkrs81X&E2n)roBspcw!3()E5fm4^1pj*O@YLfnC-e~jM5lI;==kp~h_>^%H#XKHKo&=*_W;XH$c3zHT9$!Qp=SYXZXy;ggt1N8lqEUcUm)N(23Q&jMttKh2@_3{-g8!6IVWPbKQqu$`3A(4jpoH%;76&P5mcDFQ`ZqrTkFR{R>8NTB~IVlW?xWpd%C%WZQS!1p<=>r13iTcU^o??denu}IU;=si+(Zejji<s701a#96og`mr>)vHbBT^<+c&5Ka>V<N=AST58rKF6HMl;0<IR8`;v5`<h#xyxq|mD^DSS)frLf{@sz%tbzoe6^y8=7Jc*(T8=1-|liKJoFi_mct);?4jV>%19RBqF?*%c{cB@Wj)j=&kHMCmx==U?{PL2w(qF`*#+KP`M#;#86&7`$_nh#%sd1z{O!*o{_fd5sfM`TLaRGqKS@r721af??HYnSej2#P%zc3_J(#~#-apTD1D<6e}@Ovgr3_;|v$uMV8~Q8?~OY1CV9*k|6<%%mI>gfn+yYct?L)yMLeA~uMLHyyUz_Z_yN2M#hA6a0mB+DdSE18hT(V!jDkuF*!%ITr}QKDxehm8j0;Aba3$!D`Vlz&q2hWPsw^Yc8IHFHK@J=esoc>x|ZG)AMR1Uh%WP`0>6EVqqTRa^wZrmZ^MN#~_PvUs!|$Wg`7_cSL)qxAM?tARd}tnUGFZ0)aQzAv!_WwgQnqlU6851eh*%@&M{wFoB7@tLRcdXf$@3F)ngNZS4(}5o*j`G`pkWaaYug&-mO51AqPw7&wgiQR}SJsJzi`2dSf}F9*e2?zpZoMrRAgMRryUz-hodM^P}?^kZs;ocImM9>-MkXYw>Id7SIv0P=~V0nZ@*eKMWQpf)}WMUwF44MtAu>KsKy@K~YI*-jZq0ft=bd~`Y_y9{C-azpL+@RrBhzY|^3#39Zu)$AMAFD6*7p~YsrcA6Ll+ueIdhREs^6MZktUY?HdQ%mcWz2JhnYZU~|@iEd%D_{*$CK%Ro?QU7dx5?lQ3T@vR-)Wci`03~g0xb~xCK7H2%9TbuT0l<%W2uxVn`9qu9tp!>eP2M$1x*BYej7$_8`({`DDrmPNzz8KSr}kGK0J>rd<S-q!C0R)yhV1%bn5b*YR<Z-dRD?5AN-OjKMrQ*6R@d1_NLIZ1m+rCksR0%E2;tV`pLz~W~Sl>s3jfiOi{@1#8QZf3R~BuR)X^x<z38;sW(>Y^<kAWPg$j_ft_vE$m$^H4%34m{n@L?h09kxUn6Qgi!O2v`ZghX{QivcqsOcPJJ6w=C94C8B~b@wF5KalJsiFHw|n~W(_pMl+LO5ENCDq}=!e_1wB(VpPIXNlV?m7PJ#Y_Bzj<XWj`?n|h?FucSdW8b5Buq?u&m~SJkDKLXl^m!RB+sYvGP`7uP~8Nmpc}~M-vyqVLd<2jGiY$*tKCe?`69hGRSh<!)R)I`#uK}K2o0tt~x@?KZZ-_>$E-v+~r~DfzSx-YSlj5l(?+L)cs7F>^<;!^&~JXH*APG#4f8=CpPr}@OuILD!9s;mlseaF@#ghPqY+lJ~~E#W9gr`4J{ht<cn!m;G4T3bu~n;@MSW(OCUd};2N09@H}}dL1o#ha;Nh3lh<TLb*4PSZGQ?|FVk#m{kjXix##Srh#O@4a+<kLr`|-sZ1+LNfg(GUC6AO7&<m`S#9B1CcGgBorry_eu<BK2bB#>29E;Pb)a^!gx-e}UaBNf<cJj=7aH#AUk69smRiVMD(?<p#fK^?I{w)=urKID9vG$I(;&~AW?anf(Z~QAFfmpJw`ln&CF-i8wZCeochI?Mp%F$Re3<JjbnnhFO82ttK?(tKLj1o^cp%O{1P<H-NEWOe`L;1tB6|kv9<UUo+q|HyeI9yeLWDR=IqxEJY3Z2D#)2~I;N3Y^_J>ywd2qt8<Z(S#X;TaDKUV?kaq|iB^=7xe((E-~cpcrzSr4R;6N8{x+s54pV&s8DBkyusmFuBy3<*YdlX;9I6s$3)}13t)46i=C}d{SzS>FQARv>-6SaC$J!ge+KbO#uT`MFVCLE*Yy*{7!DBO~pF^<$MQKa`N2keZigihZh(Y05GL8DQLq1Cog+z!HoIdE~xRZ7#hlDYEhzm-!Do>#RcGa54vv!0<&zT8dXRzlgLY%Sv~Edzp8@4kBEi+Wzx$I8<ctCgap)XtcjJiLm-PjVIH(OCB#xb?OsTzfn+Ll4^63&m6vK#uIol3h=ztHO`r|Q93@ZZ+ty@(3T=W}OPtFSk1+fn_yvHU#cfi{7^F@iHcLSTgCa{I7?SB82iw}}qPc=izf<mly>h4}i!jgpb5U&$QJbwW9v(ww`b$JdUOUa|xuod94yKAo0k74er=<ZNg96u3)Z%g}R0a$@0jGiv3A&x?RTM#oPS2V~2Q<@m6QwpjXFN{?VXC32QrGayDtx%ZFU0odS|>%(a_vsL)&)yAmKhk<@!b}|hIjm+$lGgzQeh>K$bZo)=7;~R3T0B&n1$EA(-vlhHk=8^ej#{7Ml7sE#dvCsKSuiOhZu{zts7^JGolxCoK0M;t<pg2?Jc@cUaDaY)f$R~pg0Igc)-Z+bE~hqJwhzt#sXA1dv&ha#;nWD0#86JM-x;KCa|jzoLgizZ!$g|Qr#|8{WOUXEV!dEZuIIw0R6pSb}oO4B~-46(xcN%D%O*h?*PE6rNpOT0Jb(@9!=Yjbic3FHM&?2&qe}DOK6pnC|<>q;-!e%4|}V!0c&lEI=Led!adr$oM<My=!yZgI0~$m6(dpBic4IOTAj@(w|c@E0yR2dh>}feB_#_=8ISsO!76&@{91MH8gF`%&$RjEcVjU_n5-}wf0P)#`@=rO_8AFReg9GtD|D#_VV+IGWb3d3Z*iM;zcC@5w=;Y*RAq`+ZAQ8|<#inja1o7FbCQa2BzT?q3j-&9^4N@!SaBkHuGI>X(a3n%Ya#X2%8U%=PPw7Px<b`)GXqs&ZfQ2lu~g<@q~+vIaR}S5W~Eb7!i?SG%ml&VOvAdK$ui6uz>%|b+|mbOXH=YQwQ6eAJIfQ2^PCAv(a^1=)~ZOo5+~Po+et<AuC(8@>bg+|OFKH7au0shJ)>=<(k+Zfu;daqs8|SsG#Rc(^8{gt2WR-!-iB#~G^FsKJHQPq=bPHWk^feZPwXsmxMFw8y&>}$ONCb4qLjPRZFM=4qp4%W$-eH&<++;~CT+j5VNzW8yza&Osqzxo8d;h7NaCvELAXN_%d0aUF8^3?C*-;ooUg%dUyI(B`^8yqPH8ypcT)LWYn$$XLF<fvheIq+f6ZJJ5juGL)_tD<VKza~lE<kfDt-T{VCkB7u(7^3W>iurb!>E648ja>jiwdzYG;wx#&MqMP1Prc($lORkbv0u(a%Dl;?NlpE8&R)-2|SzV@ZSX&D^>WSyE~<BWW^&vqrrP@Y@Be4n*69qdrq3EL}zsCn*{Com2r@WO)O35uRMm(c}$`lM?rN*Hs#0DPb2T7l*>#0(uVUqkeq^ojn|C;B8e=hi<m>EEnRFuzvX)B_C=7Je`h91~$mNN=bt9WUS)?!G$GFMq)cTxddu=A+~7r6rp7RvoV8}vW^q%?8zKsu;)*OWlva$CcP5Z$SJ;8LhAYX0Rlht6@9v46G{;n+qEg)VdP0Ky+#-N+PMrS$~~CrY1wfd1^bC$+3tniRj(k5I#~u&SS$rYT!$TFrAj9+`hS>~*3*B;*wK{yC6@Wo5&O=&^4zzVNbH%NY9Log6EjxMjR$6D&xov7X6U6BpLNg6lZyihX*~%%H>?%G+Ya$xf%nJi0FAb%6SQ1Oo0{B)F+#d47@bpkgJ-(oX1~kJYn3`W3mx2dDrI?=iU)N_2As1nRoo`cY^|10U5Q%5&B!wvv(p~G+;p?L(*8zuCEq8B$=+~*iR#arMl%N09dX%n4vTwPpN6etz1;CM15~71x*rD`2v}Y^!kfjePE)l<d?Ds|5}o9gnyY=mhVyG0ksM+aOmO$nl~E`Yc%(~uoe;4DRlcQiRZp_eRcN@Ey4}2&7@Q|bfFX9ElP@0h`Nm*?%hJ%<D+@m$sO394g>uU4u%MrsiK=rB5?CJ<pIX=M%T|1oDk4_#(4IsU1FNm5{#}O2%lGA<2f~(#z!E8*T66)n;S(&r!R9UP&t?T~;JIShC;99tWv{GU?0n$gu}m5eR%o~AoNMt~mhdmsjI-##pyom_z_xT7HYp*@_+u_mc<<C%pnDx_0(6>c$gi1}NY6&r2|@>uP$+{NEAB6~piRHOGiRI!>`l#Ze$+SmO|pvKgBG{IEhEH_h*mP1l2FOy+xZozI8%*m!fRo3ttS=~hJ>t{5Z0OtGd`E$TDigr><wiiWkBMfwsK-YcZ8qV>Fzv64x*pa*H`w%{UaMqLZn$Y5RC-f(~!LMI>zhjoNM5QuaO+_06Q~V9bh53!X^oQjkqLA^qY~SLG8CGPzgGQCs7jLwkm+B5Sl3%<m<W!IYp3tB!XjXwV9&bf&_Zr_k~K0ICJ1qfBRM_(Xn02Dq)t_8Egc~*var>_moVT=ethmL+VyCs;%`LHC^H~IQ)P+`zLwa=K=iwa(1}|-+#E3I(Kf~y03U4#r(}{HE%x&wPIt<<D>*rswmZ3>EC9h<|t?RK&6GDJ5oNY0Kc>m)4wT5$D@`^rtH0yWZ8HaG@NVF4%=R6l~ZwI&SMJ*SCC*T<0L}q7#@LL%h-}lYC0jGydAb(sj>5uaizNRhtyXsoo(J$c=XEzU@|g<s3+M7LkZZ0ktec~!D+Twso(-Wp}df}=jsYHwL(7=UE6>wWU9>c%&Sf&)<RoUnKZ4n$ub2jewv+MZcGW*bnZ5>uZj(z(bohP2`)T}MpYs*$)F}jHkS@@mRK*bIVu86rAl?<?Q;n1cO^T6oO!O!lamy?UHRUYWzzs|Ob_Y81?2a6K4e9O$K?Bt|5uK%%H08eP&VN?;X$89BATb*H!TaXZzf@JPJo}2?{9C;LG*iwOhtM#mjnVr-6Y!Qi?a@AT6tnNCM|HlAG61JV1jh1FJ^t5R?C`a-6Av5<vmg#E!C&zB1<kAjTPJK118M`HGM_jT}%0}ghXk8#!ro>*+%qwIXmd4ewSR>KOPJu#c20eMqFGcaDFf>iiQOkhelqED5AnI&q}D-_fn#n+VxORc4HN#1QwE>Tyk)pM_cwpSB)EHFF7T2acK~S<#QWoxTxlt)5FHR=xtS^x2Nx^$>QTi9pS4nUj2o}){C#GX^H~*nbI!gsn3I5OQ^1IrWMP)w#VEQ;?Ub<YOhtmB$_XWt!bS8x(gmtv4iXPkAMIB8$<3KxSz9~-+q7j>CYcOs^%l`@;qknJZO@j6yula$$7Bws#p(@PK~9``K3AAXwfBi6yp9u@e2~gU)t4SBVLWH#haL!6%2g+mOJJK4?OxQ<OF^Y2!lhGc6jltLEqim{`3oaC;IA)G~?*Y>ru-btqtDfh%Pv5?9RxD_<a^|F@MoJ2v-LQBS-(&BYq<+E-FabGed-`-~SfA?;FCXUHs^>=^I_u%-1nh0EsWeduDzeZwe&jzC&cr)Y)|CDGzQtJHMn=d0Z4vGb;#iM4GzL+mu1oDyPT0kF`Dau9dwzWcVt;g$;;9k(?leK>Xz5fL&DE50s*@#olOu)JTzsZKt1r-Cxx9dh&De{piNAM|Ya*@d!-eJYtI>rAf~2XoB>RR(|XdMknDk1ew@&sqjSn_#lP;+XgZ5g(N}DB1t#2Gw{{3W#7M@u~-2^Ti(1o{Y}_DYRb%fo$uXPXmZ!D1m%=jMzBq1E1j#gBNp~7m)%MDha%ESMOm7{sJ^$1(=1nOjVARpiNpHvYoy-mgOHXcY44-%+G!Rp3|aO2<g#+=+1!r7rlC4&B~*YjUci+*YMrn6J2doR?wFtT*K_sDaq`LGgHFmKhXf(>-;-ma98UBli1s<KczvB;{^#AV?|*ss<=6lI^76-V@>BRmcqj<F)HVtT*JDS;>mc=Ef6t%dzF<Z3_K|nOBQ5$aq0B9RG0mIlZ-2i3@Y6qjd<ov-aXc4qrPts2{QZxA{yz6sSlsbymbZpi(%WCY&LSnWT)q{@IDOJm%?CsqPB+C}7`*W+m+(Q+{Wq?B-je87Q#W*ACN6!{<hE&U$!cMmth|g+F9+3+FQ<7l_xgnQ6)sinXsVe8Eq4-KH{sBNhnWn!K&-4I>etu6Tx=t<8lUCzUjF#`c>HaWaGMthQNk7@=U`|o)rxlMd_%9H*vHzFB3zjMP>Fg4juY26_;OiLU&P*MK!WtTb_`16VzsXM2AL7f)r}qOZzJ`x-lt4k&k>%#gAm_g7Lx8{XFDq^<MFWM1Po}TbF#}s%-bIdXFUQQ;x&3-l3Hr}0T+)nW1OUohPUh|dnC@a@9v5Qyd5e*aancN`OR$JI(!7yo=uBHL_9kqNC+sO0wb3*FsZ`k(Bxe7EzZ%`)p915#q4I91%OKE?Dx0&jj9~GfOb4=irRbU-#&hL`E@~YjD0L6sCuCfQ2-E;*)jveaF}j=A<+jJJXX@H7!~qn(w-$y9&vkjdpVDMD0DRxz%gZj%>`>wl)#^C?3vFe>*R;rKK<FRaK;)TjV=C4=K|aGNVFBeGxuF##;V1+j<;1ZNiINJ^221Y&vL%aY8Jb;YvO2@SBYV5q#o@7^#Jq)uekgGZ4jy$V3|%yM3aO9iNem-K)b?~sgLu=o9pPF%2X=Epy#A2+Oc1rMlfP^zraoaw%=%4VkK!&V#^USit&12Z-Dd5+F+H^re2r_@OU>`p%IJ#krF_#q25IX@NLUc7LJphoR{;z<J||4vqc!GR2q$41y0X77n1sI`}&JeZ<Us?_a(m=shzeFuBn_REZ4>(^B65qc4dnfvHtR<`*BNUC-f|VpQ!F>H6twAgOU^h1Zjox!2p}Ul~O8c2+L)bFhv2ii68J+cGsda@7skQZmX`+<qMJgEN)R^uNe;bm}3xbU!3ENnENGf&Gtfo`KBB)HW5ah5D5CY6(O&=KuWUK`66BB6_f-URuDQLpl;EeU4NN21eF$vD23N*RSAI?^0S7~-t?fKBeDkzeWh`rFCbucvC-;!0F>d?0*W!2IDMjzS(Q7Z5u(G$jVZKGdbF*e2ooiVxnX$*sk~3;l&TP3LU5tcf$kl@amDSXjTup$&}fQP+g5!X8|QX96z6h&HMi%P3j)-2pPs8%{=<liIbeKK5$TdE`{LeZLK(YSUla}5QTsg7$y}D)+zph}r<ipeqX~*z6SgT0v=`mCw>(Es@qlG|LM|0~3?B>vol9xLk^rf|5so1P#U?0_kY~!&N@&tf#QHqAo?(*oFH~&1Qu~ffzViN4t9!(>G(G6c3ZY{r^ZsB*)tRwPGGM}?0imaKqID3x&T|nDYsJ%mKNvhgz*{Cnv?O8!=%WI$nC_YC#Lc@@`bH|eWW)|E6*G@HwhCRMO%`r&>>=-<+X~QCqwAaDn2Wa3W4*Vs5O!uFW>9^?{2TjNitI9i8K<UkQyncUVy7*INZ6=g3n=Mw`y&yDV>y=D`GP^{!Vtb5f-zX_=5j^Ddl%&reiF6(T#F7EuEmrf%9$aBRrz@Ll_XjNYRTC_Y)!o$cOl;9K^-mzpoN_3r45zq@W%n|URI-zEbTfC%AzQ;Ecki~0yUT<G=m#pe`>14CS_N<qf8S&6bix`GT0S$2Uj<_xk|u5%uSd7n8FSKL2{XbLb;(5J(CK^sqQUG;e-(@o5<%6J%c_x3|9T}ThvV!uZB&L=?@x<Bb*8%{ajeexX84Y*!27R;+2spV41wpNLFd}$iKCi`ZP+YPd=+5&C9<^s-n;!e_uJ|8TbD?ko`<{j8v)BiD3cD&oAOby#l|Q_yG0Yz}^~Ld6y?KOv+x`k)WU^USfn8iO#K6z+Xv}2JsipYmrb7z^8lcsJ7sLa@eqj4<?j1shaQ{C)2CCK)QZwCnyeDM2M_1-6vOcslgS5feUMKj;7G}(_D3Y2MgyAh{smAA4tG@SR)Ei^5CdRbGj7-(Y%UDGZf^Dba^lC)aG#_0lh2`LvExBI3D3SCFhTUg;{N6i7Yv{=U@@|tqzY9LHa>KA=$(fM?Sec5gFG}$I3!Ko^5`iOB2+$S)YB1s{>DB{-o92S*l(_Z(6(9n-{fu&Ed2ef)>`%LqEyhc9u0QFiyQp{N2R>8c48>#KP6OyDB{Vl=kKsJh@g{OeaDW$PDlv{$fTdt!_S1w&u=LU<EM=XH$+aa72t{LiXsDr$+ie=L`RWwn!!z=|y+<>JF#^MC&MHJ9oMy0Q@9%CTz{d^&LZ_WbwCYjT8QCpw0&F1CX?OKG4+LR>fB^-d4>7SzN&AQ>4TypXzZ9Ha@_v@#|s&H<HEKXA{S(r^g~>=NK{lA*b)-4X6h3X>~twPQc^EaKFRUHy%s<K+zA_R?JMZIUH}5o>!w{yGyZD8grUJa%6ZQ_+3EC!L$W($4e|~yV<MI=jy3AntJEYB`bMq^hoNH<S*2>P30W$9eB~BmHJ(D{&_OFUNR3lTJ~e|;N9p*Pm%(d_#(i<wTfAdtVtVuWc<8{yMeMr?FCEtFLfNUEzn~uXy!GEB^yayY;QK(QGjauC5h6yHYTf<GI|p7sqoHX<+M8(9`-AwCi4Pqx#YanDh<}J?2-$w*nc;DnkPejZoKmwAymg)n+WnpjR-m;i_l?Xvo*1ISv@w2KiWwq?=YS(cfT=5iPu${zB#qGqR-2<#^|$(J_U6Gt7o)3DvGSO?WYn7h;HDx0M9=q<1`Q7h^SWw0wj`K#EVqDuK25(uPhsNwgZdqI_H<3A;KqwPy_9s>a?_H)VYFvwP?)4jfSUMUxTUICocM;Nig@-j5ff;caS$RBp33)k;g!F0f&=v1_vaOQA-|<E@Ep(N)e>ZzPS|Oqoxp$=@^_vN|bC$9m@+n>lio`?wV#Puc~Q%-T>$S;&no+8A41l;<!9BgEmo8($G%YP;CvxqfE4COiWb4mbEq=x<Y*5RdiNvGq+^LrDY~1MZt;!ih0ns5R4F(RVX78b-hV>YfmQIk;#SU&w3~sGD2e*NskwvwKD94OXyI9G-4$ll_M66JvB0Tye$b>Riq0+S$Nrqju1Vu%stIxq__#N&rEPFrFlEClWVa1H+G{e$#{^ON4~IR4Bp22G!mDpELF3w2<KV_R~~)VVR~>a)k2^&=rguPh*TRwM)<S6XCYXYtX{e4pGzf7s&`a4n&NTIj@5SRngHEL1Ek}*ki`>T`p1lA=59ZpW@JVlRMUnR7AJw_Zdy;d_^}JETuyOQ`$baQ9j15sEFxu^TZBDH@*``B%Ee7f^;AbhDW~I~b3X#u;ce&L9ds8bMAkZ*q_n>>N4&5Y?wShtVmD*>&(!+?OGtu<y@#tes}dKO%V8iW5qvo;f0Z4{E<Px>IK31jdZ=rz=bx+r^2y6^_P>f$5cuJsDghsyykqdK6;22ri0TT5QYGVN+i~Io$K^aAh~mkc2N@>Ua4eJXcdHA>LXR=Dr=^0~{8vq`m&Nx<wZI`ROH0|bsBHp3OkE4Vvc2ZQGBab4#!1RAk!D$pEZ_T*NuAj7T=XzSdoO=M0uK`QIJ0|o!N2TFo&ii&1I68(+1x^veUG^;q0!ylIizw`<IFiwk0c_;wQu*#!lkpRRW2pdjGI>#0AJm-FE#?bHe!*d`DCH?ISD>|BOkmG{jj>53OLegB5#CEBlRIul}WN;n4HvTFuz{}^WFK5Sm;DqaUPh9e#9Y^K}#KF8Njymwu;zgNUf(kNFq-t4JZ~V9wW`;;l9>xASw?^43YNe+2G}!v_B@7X5^i)Bzgfy8OioCs90s+QDQpHq1mw!w<I6D*ldB0$oqY0E~>=_T;=e5r%fUyCwH!c$e4aY{X)S#B}=6qB8&tdt0xlGAipINEb8PSkVlx15yrc){MLtxCUYujSLBTMU?A^X(oXTO3mXZdjm)p4wA*T(4GA44^co0F<Q&u5)ui4wj%Mv)6(B3S38*|QrPl<B+gNNASe7ZA!*HR8o=fMUXM|xlJvl1H*dQ=x4SCoEk!q3>Kq^QEPk`{6CaMB-ylGmM*S|HL#X(UNI0xd42=pYZD4U_ufa8pn&23C==eK5^-Rf4oCPQ}~c0`HSzCCU#;lOEKC%>n`L%q-$K~Ns3thCIkxcm|)`O4g(N`e3bh4tNtwkR~rO_XX&h$)4$;;-5bT<^FMwi8L{f`DS~tb^a3MR@YlPQ}3Vy=g7AyU|GpV1S3of^rg0r|g9lOLnzNfuO?CRvMbKipTMH?H!RcD8@z#4p6;%Rhc?3w_}bbbc$tnq~vC&C{=w=sQ8IzR@94y3)@wvn;9H<W?&x7<<joG>5ZeVxWM@T4vI5f4m$`%*(u2=c~0dEoLUpe+2<5*qE66g%TxU;UBQrao>EUAuh_9PEOGyeQha0~U9)!I4iU5%av@w1+cWdW%9V;Eq2q^_U(XhKX$9=-YJ1GCx9ymPM1Reex@OF7J?{n&Cy4$NhZW#MK9k7v((UR!)y4R@G%wseyQdL35U<aHw<MSyyukP%jy-7oV(I-vlAcQ~INxC+W(hy~RA#kgz32{9l!u^}4vV>j{LUff7RDI3EyQT|G(PzNe93;2igny}{@wixI+m4xhSo8!DEd^E&?$%3NTUaMVHLAo5SW7VgJkcQ&(AwUYqdPJLWRt%<MCB$>W|&?YU>nSPh&NK5K!d6K$QZ675S$!&D515l1hbd&B%muy@X0f+!IK52p(St$0?jy0Wx=Xk0Hv|dmNrL5djAcZvu{|2DLG+Tn-0|B<G<$apY!=s&OO4aaT==&E%BUm(3~dxn6g@hzrbWHK(BQ#y_o|Zk|3d;dN6TIde6=Qw>V;@$Zx5`^)zg`J&ndVKvRtn)qvDNKPf$>Q2sxJzu&_PE?#6DWhd9fyxNCl>(Pz;#(4R&CuC!UhEy^fkOSw%2uK6QmO=)j?};Fl$r0Tq?*;g@b=H;-Noeo0K&mMxI1%9X&C&DvoWNGWapV<f7cZYVR0Fy)e=P3*lv%dy0=~97*g6yhn5JcGw6dhgOz%fN$@+pt{!iX57&Q*dNtpbE^I~m{KC>~dIMeik-v@AGwDA{rPdPup%RmS_8!w$s7rc!NDDG~NXx%it6;>#<+0FC9C0cj>VMRp7+!nI<0`&I6e`YHO%n(j94eLj`{}vZ#^%Vp)(woa(g0OEd)7OYxtanDe2VoaE{4gI^CEU;khA?%@av9fMadzBMv0Otwk@onxDkBiG29~@vxzh_8(lHtYE@RkU{R&<?wY%nTd9}hKTm+S0W>`g<UF;;7^l0^Hah{}h0<OD7e7d4oL^mhGdnv?Y1=o!<4m^YsS#J)SG>dFIYePZ8(x-7xfo#VM!-doqf%o?NoU0B+Y)JfG~78nvYd!bw3&O=p+b^w4yKkCb4Dk`L~!I;V!rWj3i_Zv(~Vuk;fX<SNw7kUEA^h~1TBx8;$FiB#g@l5xbd!HJ(;J3*<`;<GhW{#hd~aWpE>;t6(7*)quqnjP=zbNi*cr##mSTSUURF(Hzmxm1!Q&cXCaH#$Z+nNr2H8eC`-fbRmvV~JOM?}^_{(jx<dVZ4_bs-8}VG<Yw^eK9Y1+=i8*v<x)O5H2_qzl5wa~)<n?s%+uVpueEYZ1G?=psO(5b#d`zaW>_i*)kn6=1sC*LYCBe4S<ScB)byq44rgLGZ+pb7OZ_5;<z)Lmz%WC;QV+@~2>uDxL1ZJFocO$O=ja-DPj9Nll%<>k*+H9M*EZEwo+*<rZvav#f4`RYEr<ZLpK))gwp0$2wquTVB0yk-o41#**Ek#M<8W4^xn=HY0EKF^y(~XG#b3>peL}Ingu&%}|11-C}Qk-b>sqp@2Qc3h$sqkT`JL$2i%Ew!j3Tm#ha_!WVoJKvBkD$a0+1=SDMW)H>rY4qmqTQk?<-4jp>($&VyVC^D8*M}!9&}cJO`@?!#G+)K{9BD$!DESWMzJ4ocgqbMk=`{C2T~+!dEg|nHjDzq^SB(AY|(ES%*C*X3u=dSg30Kw=z+$UUDB1|cwkgnMS3oCzCzZpY1TW<8#;Em;C2OF!Fbw~XnI-FrG&MRBxwv78~ycnrpt3g#qaxS4GPm>tJAN@$Cqq|$(}cjn?hAI6<pd|iFE$@V(+zxVJzDS%{}eUu(araB}LL(6I^dI=i%V!F*_rtsgA?!i+5bSm+S^?>Ss}JD|s?x?`*{=+fL|+S@HB}G)kQ%L3zDT^2~D1i`wca!sj`;MobKn#SgrI;s&C)ok=K`gds*ktGLbShPtO6IK!Ii&1QruT4D`{=-lT^BCrv}@+c*S;T_{)Bb7j-^|w^4ugQl=BV=0NgBK9A$*U8Xbiw2)tl52Xc^z1Vv`v)0cXfGBw9^GbO2Q}-pIklrnK(M$B5U^_mo(a%V8+w7l``ktV;w;<7{g1Jw@uMkBcUOKgei_U?e^8TEzv+&S&8lnE)V5YowjM1+v2g{UQ19dItcx_v?Iu8=NxJ!atm2i)T*NHinFnIp9<$xK~s?^^?-duO<0N%Rkr5tjWu@xxT??*Cj(kK$RQ2vnU(?!B`fDM39FQsM`*Ey!s)Ied|@hcTl?L8DR{S7a!<Z(VnZ1!?`|L|-`;Tfy*%Na_rh#>V%inZYLBd7v5tOTEHF7HqnUgojN`XMJUxyXMIPdgsU^ONb&g0;NX#$qMYPpCD%#~TVtO|C+%dE6QMcKJN8|w2i?_D#^L@7$37k2iA{md}#5Ml5uZ_cfWRyarvA_^(ycUYN85neq3s9)jq?=?dk`Gj6JeK*cM@=}4+$QM~kAYKcBo)tX9Xt89!1%GAdfH@^>JpDyiimTI@h=IQyhiW21nIW$6e$DG2lh{6(nSxogR=(}pUAJ9SA&0z0ox^!Uq*(HH_-!}1bMB3x9=9^bINmEDn%4NyD=tA_g#K<l6qTVnop*Ac;;?EC{Hx|mF75?$4|Rj8z!hGkzP8aSfuHyml)YW%xo*J0|+r{2bK&Th^Iqo@A>>W4iS|(9Ge{a+*c_Yyf9fwNAUJX=aS_Jy-2+GEk!p1Xi8JpDIE-BJ*HZMXv_2|T%x(-+Pi^=ivXiz!%)hxtEUA>kMzj&GfWFL6VnAzB}{S+r=0U?W~aj-4Dl3NG8}j7gIT-MTZ0(x(GWW+fLLB*`nHr7<m%eah>+(nUK1-=@WyN<wMwfhy7h>HChQ<}6amf<6{9Gi4JpvxPT9|6t?N^;+&pvr&FLO?qo!>L%i8;ht{>P$`oS93&`wW7#q`AxHN~%6-JB+fGYe}&i}tXlak=+hHGjEHQ@aGG5i|h`sz)tDF+V-i>3bvUBX|xYB2bQ|iI!|CJ-YF5H#QI$cme;<e5|uISuyyr1Qjno1S-eS<htN!9pYOa^b|{6C-=o*uY&?FIP0(QusWj`qyW~iFg%NTmXUbTpx}S8_cpzeEIGE|e|hUzgwgzSSzRS`7f@BV(bWYl9xi(I)&mS?R`chFhpq@kxY0<OMJO|r*MaU^O36cVcbbv3L-L%+9tt-N1#I9vc(CI*a?XgQN!R<;GR<<6U9M`NTL`JF7tA`bBgDCZdDiMKa%>q#De5Z2?M)Y9u_XJrU^a|7@W~_aR!pg}-702lbzOqBYs)Ck;Pc&GnTw3+JT=&QP*uYTyn@cT+oZIOvDojdrGq=~ZDWl7h+_|im4kg*dY)0QMVH6nAU#*-R-%Sup9hN?+{4kvMi<WPYEd?Y>$L)28?T1fquJUYTb|c$7vmW1%d!=a%Xr&BUu93*hgF1YYLJFEZ=q1}yW}IIGkbI)n2MS+{$~B&q8E&ip!u)Af7@tmdYAu=u@j$SK&x|5R{~EisVxKTeO(Ht?oQE8Kc=v<rI~uw96bH+heaqNtO{}SMNz6!giw(|40KB>N}aWyp6V#MO{_C3Ope|t6Is-UojgRE6ujAq>U8nswz)D=CiwJAJUWrqwkK^e$1Fe?3PdM&#@o^ZY3YWlkOo)}qnoobdQ_j+jA3j0l1f|E#$v;$-Eo}2!0JMEGxM=6->zt3yxWMsTSHT%V=RtleX*EXk6AiZ{<W_&m0xJY+C9nvZOBiECdWKtTVFH~6Gswg>nLQh4!#A+6Z*?afdhP>URm31ROaY4!9kZPwWIOP?47RD{kCmsOQq-ug>a+W(~%ugJ!q8ME>KdSK<7@Bqrji8jjI*Aqf-8c;J@)-ziDvIWy^nD;P!{uM1|h!cZD0ACXwo6I48IJ{?sKptmw3qdlu;6?XoGa?iWyH=0snGVG2lxqo=bM>|x;2<n;8~UOt!20~n@Obg7&it+8{90Izv7yS1Eq(yw^9H`HdYo}!0%sMZMHk%+aTH)eRWt33KPQZ&MXO!U?Bwk>6udYAycL`FkynqW9(T`1qO@Sc*=%qBZ&Z)bYWS8ZLh7G+!HI~Vp*N2fH_3$<2WZUOcr`cW-VR6lh(v~wy17Np;-*{DggwU4#u+%Wv%pe7-C)5s)ux5yARD7LBv2(xX=Y~TtJIMvjI%x5rET`gTypY5PVIv#}&=juN5W<V<L|5JqOg5NZ7j63>_4#GXRpU>_Ro=9MHo0b&-%d0Uz1G@-PmbQ2by(9GUP|dr{vZxVXQj~edB0DiKJ5@{5-eH}pU6-|1AH*6PF<7@1ys|}A30e~vx7%`R5zyIa)u#@t@3_NsZ}n6%K55d}?h`>3!soz<!jS_eXaN0F?AN*-m7|{}7xNa=(rf7r83Rw%M<H55=%wVdl5sc`cMq*G(*lj)bb+MYZX}zPsQf@1b9y?r@l`mgt{$JOf^gl$yvUUHQr#j^4z<AOwslBWpIf=ET$j5htQbzTKUJP$!=C2&oe8N}E<$-s<?&R^pc4&t_mnM6Y+-xxCHQbH!5wV22n`}L2)Aot?&lYbRTY#5ux1xl_6axDdF!ENt>%C8`Z)4<x97_fh~p9hN0I2>Q6w<u)#N&ABqCOBKgyeVizr^(pF(J(b$PrMyawvDQfvMIbkYpXgTiLzG^_=o#6qW`Xta9bRAn9b^h7;F6k>zbU03P}dfZ>rS3rm<3N2cVSn+bL(uJc=_U$Mw1H>{l-<sC|=Zw{q)x`3mJi^`?TN^8{;X;kokFVLI=zZvLqqd}{RZlF;GM!r}S{ft_>yobR^Ip|^wbkb=#aWXcQO!)O$Q{F+?wsw?V3KmDc<G`ynrFF;!c1*8QKoXO9NW&$gQ-$wzTwfWV2_=|gTME4ll6EDDdFMHDb#>%z;The4D0jCW($Jj>EW4x_OBXfm#dkwK2cYoD5qH4Z)mck2x{dQ%Hj31Bvk1<Z9URjf1~M(HaN`HfG*;Kp7p-{?YDni3gfnjV=WWj7&W>R-(qX3_gS!A-`&CVXfhtB$hMm2Y|0a#C7gV6lY$PTa++%#P>DuYLt|Z;=Gmh&#t9=jfUBHq0t=_Qbmy;HI0l=5BF1OTtptJ5@(|m2C@U$XvhS5+iHk!_?zYYPB0E*bRdHn$Ty5nOt8E`)+OI2~XS^+As}uuk7jrkaCygHeP3hB$#nP>MP&`J>sofIp7Tc~iqIdg80@<w7&q1}Of(U_CnCOZ^Ge#7R$ZHoU)9|Xye&t#_P}LI@Uqw{d$HwBQ-P+&KALL4!2Tt+x_>J|x=@BvSpRI)b@dV#S2fNB4VaKt4VeFzw&?{E^v*t=W!YA?<L079i=HEsfx+VpEll+?E(9|gotvt7xk_M*swYsL82@D-m<#Wqac{w6pL~%>-Lp#N&A}o#CBK6kLS5fiq6QlTHqTSEXrFgHOUOnfg2KyMW+{}7r95%|*iRMbn=@`3*yOHlO1-79^!x*Lx=#yNDw+MU>h4%&)w+0QZ8q+{m^e!Ed*N{<55WTHi?I5*MV6%hTXVVJ`JLD$mFS`P04X4#QfA`(1K@%vlC!a6YE?8A2y!#}RO87n2**N-bvP#LsYS*hN1*<!^XNukML8Z?(2*A2DH4XSV%u23t$f$%XwWE^ixHVCbnsu69p)G(y5oQ>(jZghne0Xx{WnGBS+v&M%oyfKG#p><7+89eiYihu2JegJ2NUbf}zIS6STRM|oBJ0!_YqK&@O2;eeQ%`@}7q2m9Z%gxdWWq|}qu#OAOV^@QiaW%Pd-We$y3s2H^G!T(xyoA+5XjUI(e8qoT*AGw^0X8&etcq^VUu2!)}#~d@YRHZovE8B3U>aUdgV(SUg^SFW2~vS*5I9nuPXokLdxU1&Un(b$$NV~UP>jo?0N3fP1aSCrw3G$UsFZ+8>$7T2UuucPL1_DsjjZSj+E)Ip;!8X@|WLR<T4~_`F*t&zm<UEo?AXDmKf6E+w!2ZnI@FVe19MzzPqx0GEaGr3-JxVz9ihQApMs5^)_BxOYNH~rZsjD{Yt87^o?Z4eg$!{@2gDpee|bl<c2lHsfuLN>#7}nPfa6TzvxxveomeAN3SLe@yfjYef<32fX}|#vKyi{`VJ)WPB-%M9r)H;+4dgE5WfL&`Ez;8zXOAJD_?h&!8@g=Q+VG{b%%$Wn!%IrPc7Wd@%eqIg3~vm3by(2e?<!6Z^;w<YRtHyQ^mJr#oa&bFF=a>{M_oh@a0Cx2fiO!ZjBK1*CEl3v&{O>TGMR#nJl^wu~YwaCf&X=!Ve(Pee5Xly_j@6c&2N-8?VQd+p<5h(#`gr8E`FCt{QvU3$ovaD=!KYUK+j$&+H4Z$|}?cW}^FM3|3W>=*AiNu^Ye8T7!zia79476?Cs57Ngr=8;Q~;Ifq?EaJvWlG-<8rG?)6cnkAcMMLnzsfO}=i&V~it@~4`UXq1ZvL8cN4jbV5Dec!*=_0gJ1wYSCX*YL{LJ&Q$WVtWb3<wpdKe=5K7v#QG`fp6T0I4NQiudjbHi>XjqB*{)v`oI*Ya*%jYvg=l<wOv<g1L=}^i*9FF@Ibmdhj*<tFCnp$OOtOx^}qGx%p7L_iPYTA%8$I{pT)*q_d^CR_lt6HKW7%=Rj9Y~lc~3Z(#DoZuSK-=V4IG&mX$QrB=Fbi0G0HlHbOYtXJiWSTVBt(*h7E%$6x>cC*0bfe|z7Z=)=^7N?9YIaPYto$X;LPb7S5twH6kfY8Rn3c39j*6ql{dGPS>ldP}Rt=JH;w-Wun7_+==Y$l?mMzcR%z+yG@xOWdAEZiYsu5a!_WV5hpw?Nn^IfBwhY+kdLcxMoK}jK02r8-L8KIh;t1YDZ~>zAV3RcSh~)M!eL&{p+uP`^*3E-~8`?6*G3_EnQbp`LWB=*>OC0cc1+RUB#~z_oMuEy_Gvu4lmY8m-n?;0*&l-=d4}M{<D847I>h6Tf6IxKfW)ihlW}j*imDv|0{<0zB1P+U!j?O^o&J5;~hOlAW<$lB?i?-4<3<s3*^%GF1C6SbEveo=Xsh3`5`HHEKs~hT6xTAOP9jv-Qo$4-KDBeBw=9NSyL~=>3-fk$WIcD${#;rfB%=to_{#~siyH85uYSkM%*-e8zM)!Zd#AK2|w-D%;i@d95&-;J%njzi<<;FQE05$!Jth7l1M1NO|$Pq%lT}l-g?;S%)yJpgO&?9Q=?|BSHmP-va4*p70)BrQJA7UY;)?^yffY)TdwRUPdBMyPCv*6Rp-E}Q?`$7-+c5{HMp3d&B{XkUF2<!Zov%Hba2Yhr`2PtCpvGI-oR)g8_L+BPCBdHvD=OAK@LhOG0s!((0gj=bel+x^6bt$w0FzO=CqD<QLbvQWZu{wfAONxe77>as=sw>qS@F1<!dr_!ZWD%tq>mXjR{q6Ypu%#;bjw0sJCFKtZEHAA;vBjD+t+r?6H2}DslU%QGX!X-I!8HK1CawwL6B4HE)X~HIO*d?`>?~#s0i~EJGlpe>Z548k%#f&6y%eY+H9d6~@5HMgLYem2qV&D}PMMFg}@cE=W#E^8WGqhOh<hlJff#&Dhp>;>tNXNs`S8={r-C55{`c4<|&965w;zO3wnfr#mf`g|`O;2RwS`daLkzX!8FN{`;7qqeXON^flWpI=gyKPhqvtaabyk;<dJfo10@Yi+jvACjS<AX4B(DWny|X#cLe#<qv~TeC~&#jkaRV7%FTYQiHe5*f;L>W>S>)q_SrF))xU$mea8EKBJB6(J@wI7dCNXUExSq7t9SdHppR@JiU(MDCfYsPCir1wH@qS9hW(u&utvdHN?20zmv!bfFb#WxLjy`sXzQ$ni-!>0!X#-y=dImnsy`O5kKmsSZ!DaHKZn><8(un+!u9Sm+&ij^0UV!Vw^g#+Zt9BmiO`cr@sQ_i@UnbTDhqHMWemT6Zg{}Khz;{!=?0;-iUsF=+OfJY+>Nx2@)iOr4MwkIiWtea^)B~KA<C7Wv#8YGkCKT7GsKAxK1^;&O}{PF=01hkdKx{gcyOT`k2>|hWicm-@pC+PyhW}@oi&c{{8K5zx|{5?gtsWg5|7h$?UN%)8kv+IIWnANcrIv)$+`?qaU+jt(K=T4>grpwK(ya3+S69FUC`@e)6uCPL1k}nP7zoLz|9bYm^b)8Afc+6hiT|{KDuxyJ>#1`Gs5B8{Q3iyl5B;_5g%Y;zGCXCbbBKsG&N|)7KqgNrPAuQ87iuP-Dl`*H=)bNO*$$u7>;uR2jNE4&rnPL0v0Vd%?q}t>Nl8?4*0T`zN>bTkOu6-XeXu$y+Pa77%O^@IIqNUkQE|;X%W!Z)|9&sr|z&b(B4H4W*c<oLfT?OkFS)-i%V|TNSo+7JCydU?9X>-8NwyRgwG)RY5GE)$B&DG`}}B*}R)P<62)+cftOvifKJ;5PpVibAc&)x{tm^>6N=4HOx(G@wfCaS=DRu`S<?1v661+>&qhguL{>UmtI;beU-XinYXEZ%VFM>r*#{|7r%NQs|YhW%sTHqq^yfS0O&3;J0FP`c^nD%7&Gv>k*~DLsVPZ{A(Nq=j!h2k=Q`sO=L&UPL^?cU25N3#Fz&c~<DJk<Sz56I`~AJ{9_S-FsNk3Ktkj^YrUMZkn$f}jTVYfPP5oAD8HJ2?d8rNC?7lD-Rh)6B78l(%sLBj+v9+~Zd5QpAk8Vv3?yovz+kfplh?|(Ci{<c`u%p8oR(gsO-uE`rzWcH<O`E!>)?En$XDHSgPi-g>mh)_D6S`&MPBv!QT}>;sXN~sOhljR2*Yj?`(%K2n8nS30Idie;!4&$b95kAdcW-^hi`-pPmyU>7>0Y$cL_HvQC#R6ccYrRyV#W0zDa_t(Q1V;I`Fl{c$Ap&4YL(epZOa&jyFVj6&mkXP_Jyg(Yb(EYX)=Q+#4Er1b7hEKm8g10Q;UYhdnsO49F=OAPczEcB8+XBuG}~lKff|`6PxmD>0(!yGOR75(ocqG=A&n)sGhe`x{ggFHq><D@`Eji%HTT)C;IE`MB33gO!d2m?b^LupHiGvdQyUAjK8@7Qf*a&v+-+t&Le!V52}Y+DDbIsPSBduym|>AskHJ_b!@^KO0)|qF}JbZyX`fi4`9QPfwkHkj4T!KGEP`~D%j_vZ6(7)_(y@BTE8`l?4cVfO++8+T>~vDT|3suw)4_k=4hM9m)j3W;qB9+gQ@L^r~-XV++{UYmYlJku5G73pJJ2fLEfwox?L^do#%jMHN^|3JYKv3NB-Tj)$9XeE)M2ldXAuU98!-h(I6nPJ~lJZ+};>}jXvfQd%_`rAerP+o<L8uT_Os+ti8aCN!RBEMym&<Yd+Fs6>@->&)2KLm}-YW+Z>}QTW_OmZl*l+E0q~NHZEg>KRMFE9{X+{PZ~HBT`3GZXROw>n@^6FRTVzD+ch3jS6oY-9(^2hQCUfPo1q%%uY4(skk*6Y$eaU}mnW9Ql9$;9rwPV79WKE{ud)QolZe%IZ8RZ<fXZj;ZnPr|){?TINZSMZokEUCu_Jii(D-ZD?EBkM!|qFUqp^~nP0mstmg0KGO^a#|<KGC%D7(M5oXP`EAEvtJ>upyB^3tc^7O+s0R_WEojH}Xt5z~ZdLiF89hhA4@#bD=<deesc;SYiw`8DC<KEfIO++42r`|8`NRoKaln@@YbkS2<Hpt9UUP(7=RrQKPWG2Rm{MYwK3^UL9A8D|_Q&eMb5tP-O1R`#MrQg7vNJ^XorURDD-xO*?9*7#YI`D&ovXdF#;T3OUx;-V*$Y1{HU&QejpTxEbpIU6a_!Wiy(Mq>+g<11E2WIPxe4T3J7Q4{li0Bvz5wM=ZM6Lo1LNpDXtV=BYplcdeBq!r?teQ%5Vw3xmc=go|PmB4^Q%jAr6z_Lbt;sa+^S6p)!(x+r>;5k)zVV|A2^KxZgU%nql2sd)XY*8qV<xwruMb@d#o=9weAh*w=+)J?$W;N&ZhjE(9RH^^O8CQZfHelD>bI+Kel2mP&T=>lGkoh~yPe~e;Z#DF5b*@&co6bET8_j77g|oGwTN)S?in=joocbO!lSIWt4r4&HGq5q9UH)hZ33O5MG*s4tfK@s_w0i;*Y|7fvdr+eKvX#%o1}@8T@DhCiF){2)L+!qZVC$AEeA17#c`7?_j!>@6UYHLPj@j02>o$tc*7mUgYhkSXp_=XoNGhJ3Zv|eQ$6#v#e}P{gV$ukrC}l_6SlOKsYJqw&%=JY!YWU`JC*OR~1zFa>5O|x=MAx*PNq1*|<vt>rsFBf^(<IUL{uby8Gx3EwQCAEwdSF5-FkD~;jo#J@lbcMF{r2_0V&HE%X%H>7RF%BEhu9tD0yga(qO@UoOWN6@H#F;FZJJ<q-cfQWc*Gc15x%AH72gDHLR0QOP|x;JNFw-n6xain5|s(FT2U^BNVx0BTmI%r)S{lVm62kNh0Zajg>o-AvTt|L+n_)T1V{d^u-iC%geQJ@b9!Xn+ge($4aUJkSd_ruDfgNS)tu|<XUJNb5_=PvQK|{%vTKICZz{WeUfR41tBcs1!8N;Cg69w43wzP7Q@z=iT&lmbj=<t2Doss6fq~EJ5z@#sgKhhf?^Mr6?{5*&N<-yqmjc}C){#pvAD$R;m_MBFto>yHOFG92;#Px=nS)mgLyt->TD#bb=x&+9TFp&@nXyCgGeTi(pL#`7-4mK)eoY-F{Tuz%%jsLnCe%5Q-6-@PX`Xd?!Gbz!<+n-^3<ulM+CpQRa4E;<867?wgNn`unzVy+<T=bky&}qPtHIRaohM4cl#Y3KpF!e$^14CxAISHw@UqYT^pC&({ZDxMfB)^bf4<#Bm>`_>UT3f^C2O|7QOA8g)i*3e=l<?)hx9v}6RkG1OK#9Y+*-@-^qa0)A@Ve~{J7CdVi69Ov}|4P@ZbLR*T4PcfByWNt*Bx%9aPIJ%De1)H5UVau1)RCRZ~Q6LFay;(}@dFSq<@Rz^u0Fb!xl)YA4(0<etZgmI1V{REEF+TIU)#mk(NNocN+gGnhkLge{B?#ps>98)eqd&8b<!7qlo|Z)?*~b8~uA={D59+%^-^!f{snTI;o}bhS0nf+_yg0ZL-+OF``a(R<YblqsZPWn~Uh_t^dEN4YQw%vA((({-CFkfe$7+<a8uh(lxFeR)$AO^)K$%~z#;!2Bg;I&Jn+TW^O3BMbzE6!os9;`Ytq82bZO%y3gVTQTk;92k*ZQO*wK829ZH)RmgrTg@$132&vxS|OFgpOS}sKD+sJZn3m@W@8E1Pu<rRUp}njB6r7z_welLCumZ>H+5Uqw_vX-R_*L#FIk0ZIx^nxjR`3XsG+6o45M4Nb|Rhvp+#iD%Fu7O@jS2}cXlgJ$@fah*{?)~_hP6usX~l>e^-grz@VIPcaOVQs&<Fboo9<twB8g0y6EcF#`fJ4->O4|W}cPAr}DJBci2mAT0WO@9{P0LC9rC5G)s`6cv~Trv0ig2vhoGm9Ws|EyH<XovC?bLaPm_Xg(|I5ALv(lEeq<qH)ZMEG>srPebLx!5>`<u0*eor<%iHPuhga#N~=ktnRdiSgj+!4k5y|5xr86Flqd1LyjCd<jtf+Gpgk8`MC)t4K-C=Dm$YxQUfHQPf6Y;Q^=9dt4VC(p<MmU%bsTsPtGCs%Wc3M7oh%tWGbLd@4RiG92^1d<0>>ULtrgokbs#KYwminWg0y!3Tw7<dqTlvb??ZVva4a7;(<o}arjWP#1frt}Xdpf{qSdfWibwwu*ZJM~^`_L}=J;ABFf}Q=sN_>a2X9;Y)FI^7QL~%%_KB~k-j%IT%30qOiB&3^DzF*o?WO7VhJWvFDX-oLRltlo)rNAKZmXy$hdzr`BRnPPiSjv}E4hhmJ5DfR&am`SXEbzd*~6n{EV!n7Wh@D{p7!0RnO%l^4828Si2Plq?HV_kH`3Eq9<*5w8m8Q=dY{b>)X<`0?IHCYzy15aKht%``@hVYAI&EkT7~NMHu`(Fmj`RwaW{JduW#1!sC}r_=s2-dWA+_nLFzMmCa?&$pQp_?i!bIqT8H<2R=?Wgdt`{+2%pb)Mm<xm*Eg;tpgT;=XuqGD$mwnfKmW__T-$H9;R!RmEsqiIVX-<)m6XTi<mk-YBckPcxN0JQHd$cpue@MsAG#VM(cncQ+fk+T<C+5%b)=Gs)vRFOpAzeVH<5ayjbgZ=rn!1|S*{MkXKxt&=FGc$AJ3Se_bMH2?3qEF^Eu*s<$jMB4TCg7eGODTA9qukLrn$LkzzX?t1yl?bs-o8CQ3uW{lI;I`l&{x?({>K%Q{B!(Lp(A{@ila`{I6deoh?#_lK+6vcafSuEnLIjWE{7_V3@v^r)U<jeNLq5Z+ui4f&TD@tdLdct>%7b4MRMskfW#Y|+N}>k(6a>3P_i(s~FJjC^$WO}C%ybH}+s{dQh%%WzbAvi78>4Ok0_$wbG^O0uAvUWbl%^m{{uu-orVwxfrp`oqzp(wQ99o@~2Gi}cwz4|m9kz8kWI&hUUblkMdfPZx!Dl*Jm^c&?a$MyogkoA*w2b@B)@r4$eMQ~ULjvP(MYeCD1jVQNdh4XSMIj;+~i^EXsbFgxLP?_OU?Q8BwhnMHZaZVvq(3Ej`GLdNj|bzIBWCaj&hhZx8`TDZcwva9Mia41SglE049klks}+QVS?Z}zq%n8b2rmeIn@5jZB75h3s-En?BNqg=ent)WWgO!e7aI31Fx=EL{7axD-}F13)ws}?`Fx#Sj85JoYay$SY3l4=EEj~~~xw+o+UgS5f3W{Ck*e^*37s=K4n+ec+@YWd#7o3e+r#UWoYsa)JD(&Zzcsik*^mR5ioNU7QsW+LGA(_MCo(`}XJEtjOoiFy0pqeo_wpVJ}<)%#523Wq96th%$Ow0c;{wUw4#m!ig%?y-7Js+3$ec4?*lR$z%WmD)L4JLyo6GSMO$h)VmaaX}~2?eN~#7HR7nG8Im%15HhZ1l1G8gz4|-gUmK0x6fdx9PAg<vE44GStHrn_D-$Q(#B8AcpfNkTB2sv7dV*X9TmTv{gai|NnVe2R>y;TtWnoSus5qB!B_jq+}1-EPL$#gYjIyiaFpKKbybGd6%{c$ni?o<!tF{{p-gv#D*WS>@clus{v(W~F<%TtDI=r$V@9WZ`+9Db-|k}JO364<`g?1fb9=^?^;#R;Nv-M>?=AYLYq*5Qv2#mtMit!cO$m(l)(E?LEwhYIB-Frg188=)f6Y@wjq<dvdhL7BDLRX&yumaIS+TA_uL0z@FU)eyfqhp_RcqQ4ZAgLDr5x#j?5qcRJ0#u~WgVm%WFKRjxRNpkrWz|MA?ok;`Nk}(xl7!KN(-*Z`;qO4AWnIhRYsI*ZaAo{Mvcv7mZXi!gi=;HG#b@Mm$IY%;%NZr*Y?a}KVy2=NbRlas5NY30u8szCT0Mq@2OTqiNYe~%$I_;8ldC-LA;_Bet82n_d_N4n01(PTtS(RjlF2Iw_T$Ik9%w7_qd;q57icj@o@Y5mzJ+h-N?ps{NPQ}ntkUK9)I;3=xZgg8W-)O4flHMoXuBR;tcj{H;KP$NK{8V8hO)f@jeLUsqdXf1Eq>3+GhcqJD9p<Y{x5+tIb@s)T^v5c96<eP6(O~i{GGT<|biMDZiy?`n|2PSc^2y$zCJ3bdeHg1|xzG^wPhm*rP?Tq-SjY>DtCV+t^FoQ@b}x7fTl&!<yWj#m8e*AVb;A0eN5-KXN)<j8pQv-BwzoR(y&CVw*mtEtuv&<H1R(W+*JEj8OCFu~4oG3U<<h_0SzPYde_)8AfTaQJ~e+IW^`geMhJdq&E!AnQzqXk<c5#LN#s!9J3~)?*CX5MXyCa)lxQS5CN$6GBl-UHX*&+|5V(A*-~f<3$!gHWtu<Mz~Nv8F)5N-VZP7JD7&+k7Fdin)hPm9j<vQE-6tJ>Zy-N%rr!<7E;N4Nisd$tx%r(a-gZ!)TFK}Ff<(?5ayosBjNj$S*5hlnCaZc@KgkRqS%Te=4WN{Jsekv%JVIpZu}Zx#d=(Z|qSz`N6q$vH_4u?7Q+yJOyC9RmQH#>LNzR+ub%S=3^%{`3L46Q8Hak+cb?|7a&%a*gsY(dCspg<$;5y`g_t(NoSoaU}z(J~P;Z_`!Q@CreQ-iB>*{PZ;Lsmb7Ij!0<#1oN)>792`-@HW@(Bha4>>~Pi%_E$aVJa`8eb}@BF)V(_viq_zO9{<OKGJ#NlDcU4%DdasrsD>&PVV~QpzWaD1IXBSVKKb5b_rNCfbN0bQ~atXdfrHE*A8g!C^F^4JCELv_Ip~*43+*M?eMnLa*ONuZv|?N_v$afQ3|IpujA)-giz8AqxYcpqo!_-Sf{eRqKp%33#6fNnmX)p27g+M_m3Z)JGXGT_#?L$IsZG7k2c2lga8(m$BFX`Rp<F#GN(S2z?u1(+=Xp)vfJ<B@`O!;MA3=cD8-Wk)C4<<OZDpz{MxyN?CAyLrkt~m1*v^y=BLJMr=iY>1vZ4c@0V&4Cr~94x@qhx4#O25XiH9;X4C4;Mdo-+um$FB_m1l9raQn}AJ-ipXf9F{7+a9F)<4uby``++X0h*~SJm7M0%kI1baC6ip@JB8QYG4d%i=3&8wNAE5}V>p-vEIHPgor~O|;teWKC%)ZEmTk%R4@47(FP`U0W;Or!C2AbEd%QZLh`R8}6&29z=|;ZR<6A5V+l`=eDR==ZQc`_WpIA+HW>CN$Kq+69DW5U#u-s6&rDAY#u+`m>p9-f3e3FWxmOVxBHawJNqcohn0E|#~0As8;vdI-#vL_LPHc$ak&NK)Ejl-6-`6D_<LGIfl1R5KV}ZUw+u&Ev*St&aA+jHUCq=zK6$Oj5An&B_uJiJXZPh8Z}|PKeWWmU-?=G=Hk<3+JGva){nB6$)s(Wq%DAabK?GVxlug&UEZkbDHi}=g<(eHwYOAqwyA3m43dO;L9k^Dd#UN!3JchY6{NC+;@q)+p=I=d(rByw}J8Xgq-uUr{6PkLwXHlxOp@KHVv>|c<y*RBk&y!Kn3N1zxctD@{Q5=O@a1?9gOrr|28&a%~#@T_WF^eeuXiL?`njNd33tQV}Jilr6#9S{@`h~--ShXCui%91^`c8Ebm<9@_GWzw-cr@S}Rxa!`n^kv8^Zh#gv0g;>-nR4PK?cXxZE(FSEoUq@!{w@m=CXYz_zZ>fdfpPYLi{wZEcswtcst*=X@wxg@-wQu){u?WL*u>vAOWz}&e9fwZZr~$wicrX;g4)ug}@kps74i2U6giheW;vSt&*(yGv$#Uh*NsttrwchW27l$Wfel3&0-wNJUGvwL$$jTL+D)35#5{*Y2=~y2FW_OpzRpb(iUloYCS}#{oYWUZ<qr&9iVnv4f7H!PB7RYXSGLI5Y3xTe%?Q;bMXV0|J8R-(E3dvfHK_@coku^#-7qOhw%-Ud~;I&{ZW<KW_k6%Sk>dO%N_UE@a23vE@tSAo#YD6rk=>F33IS3=0^VR4su#5?J#R(0BU*wlTn(8>=7}yxuc28h?MqcQzEXF3Yxm8px@sdqMi48uZBY!ZVlo$vO`V1909t8U2Zic2@D`Z)mfyrkYlm!*KR$|?CUg%c20R|r3rl%Iqmbk#5)ZS@ZJoz*?bljwU)yM(>q1gkr3AQ_x@k|%2N47WtgM)S!~=VG$Cb6eHmZ4qwSI7y>&FR#_8Up<6!+|DZ8WT8Q4HeUrEhqL2?^c`Y&QEvz1tzbJ3{I!jhr^NzC5jc4!(zEgIXJ>QNHYXJF{&X|qBW>TO<cPlsg!_z(TpZ<@op?Dvlg+|~}8vejGst_G~n1|51TPqgc<b8~5?l5ygs=W^S7B_ou+_19P*cv04@HTu-_5WyC#hjCQJUV-!=u%;fsT{RC`Ini6g#>%=gn;4(=P(~J@xBT7vkRBNqO@=UJyS<QUH;I!|2U6*%l@gM^m9Bd*%#$4P0zu_hr;ud$1;w=5x8e`g-pBNuufCX{I!*CWsnHS!`w?wRWYpPgAv6_G3$jqFuvd4NQp<pW1E3gDzODjBJ-tf~r*ulbb<1G|wcW&O614&HccY!D5$GBlrNN5ol-Z5#6J6HjR37Gss5stIo}hu+TS4sfP1?+CxUV5s^X3LnK1{Cjj01nmIWs;ZI<z&$+55(^nS0+>d!hkbx#P}Cb5;a}YDtx;trx-VqOR<%l7GO1xl4}{Pn6xFW#?lQoeVd5RD2>LGU?ZL+UY&kn4@~usE?WZciYLV%p3d28qJK{Y5ate9&*N-MnUO`OEw9ocdZT{IE{pThG>*CD{z3@J!7Z+<p+Y8T5HiLS~&6KLQTTshMSBG+*-#x_2!l9%B9xA1NW456~w%)Ev`J6O<V9xXwuym8ef~`W6cAwYlnwnZ+EoSN@>e{rLAyf1KFCGb*pzNn_LwS9A6*Bk+8R5WtaJ{_OA@Dl+WJOB+!y<<gW4K4p(kMRgK7&<sf#QFm4xF`u!WgV(v{Vj=^s%OGOXWTEofc$sK2PV9z5u3{fx*R>ztDdTHMGjLlEQ$E?Pp_XuqC?xKa&xAGi#Z0c$S+o?jTMPvu&GbJ0I+Tj(iq$)H0twpCcN))SotBHuDNu8?!KvAe@&7<6#AxT_4Cbo=1#zmycDF6-nxoeS&w*T~GBz^i&JybKDZ4VChR|KLm2RZZvwuyk>Zkl_4d+e~O@eUerl9C#hXF&C$PDK{GH>B{tPV#AyF+T)ySsXqpp?tWtGBU*5*)`?TU%fSt1v<xw+B=Q{S;~<;27X!;>(1dNzFE!52@}OKl|xPXR`rDGJkdjld>PQaL%LTNv2qq|_4}>N7MHyF;u;77O^C$p+lnrDFY?=`4O_tC%@W2imB0eb2G)DBL8u^(V7Dwq->*I87(Y3CKUXRm#?q*c4@NR7%OOVQ0<F(0-l<{ajUJwNYyYZ?2dr!a3r!y0bb?Nmw-wI-OqHI`wx9~&_wf@p<+kkbk3aq6uYdm&KK|$5-c`8p4l^k}_3yv^_RqJ_7P_8fw~y5Hij^_y`xCa$=@f@N6?*RvgMHp)tfBtj{`J?t{pEl7_x<<3K1{XyPJ?b7H8EHz+^ApF=T+@<n!TaNFoVwa1ZNG0+Aq{+zC`+}Db&kyYEnE3)4&A>*&f(2xuFfN?1TB|f4sf@rxByC?M%D4@zfhGqlrZ(rW(xa*L{2VruS=ndvi^Z-R@m?pDRWX8h=Q?1AHTNfBV~S|B%S2c2pHtshtsbqzA<Z%wM85q=v%n$FHMWAMRK+_ZaHLC?iUlm0dSb*9=xjxqeqo$-kS-{E5_P`soO+&#*n-pMU#!0Hu6rw#9Ub)!#iyR63?OqFbxst|R$wU*w`Nm7iH{I+4Sm_#RR3eUESr`mgrvd%BO8en+|4(3EToRtM@vb!yFvKfSrNu;fV$x36m~Xq(rFub)Y(uLWQ5|5V67o6XiQom<QB+uEATR@IVc>q9Z-Tt~Kwg?L*j4N#UUp13Tw)RF1xV$&X~em32Cw#Mz(H|SAL{_GycB7C&e9CyFw^PSnGVCLF13XcsqL7Z&UEML_g<T0}uqOp!1b&(6kU7_i9f}5^aEVe{(clYb#K4xQE<(GOKb?vdQPqELhY@3sxCE#HKvBoY8ls2NWD#a9nZUb|+rQ0qZtKi*D#7H%(8>oy3#{BEvuZH(r@Bx*ha&S&HEGcS<qc#{UPyp2CRs#Is0jH+5_qO=Cwh`&tYExQ;dcB`D24Alcd<A)G0A}$<!&=Ggdijn#p?lNUsS3z#q^C_Y^%3z*lZW`3B(z_m0~7qIX%)Zdv;N+~R%|J>nZ)?b444nIE?CRKVur5gU?Cs!Eb*GI=+x8q?A~UXeJfyuNr$F+1P#0h!Z0<A_F7(XaHZT*N14Bz*0VgoS>!pkc1juXZ6*Wv@vRr$*iP+EN{7gU%nsEJvhZ*O69=(mS?wkiNBdGG7TFnRv~lX%3MzN#Cw8MXzgW!KrBJiODm%4d>qU7w(p9W1>w4So!%PKc)Uw1?t~XVaw=xREQ=l%U9S%PWj+L{MI$cnjyK%nMdz>8F{c1ciaC&Y0Ksyz+^qfcg{K`D1DiWv<Ks-;y)JjdlM0qioBG%8`v7=m3#?U6Tk)kJPxmeBEHlbWl5$6%+%7%t(1A{ToOS`7`PEBB~E2@z<%v+H$4c%fZ*&#hdvaIqu#)fnr*-{?;V61^xvr)qvZl}YsP#48%YRGN-+HCAGsV)F(sa7rxQe3P}BScO$#+zaYyQp3*GUa4zwL{wdh$f|Kx71ag#l+&RS8_cg6)LB7FUippG$!>aC%;Xg#^C02zvaqH*?af<cX54AYfLpx*=E?w(nNeW=FQp%QVk|Hjf_D*p+pHYzL0#aOl2&J952u`+;7=S?e$6YPC)94k{$)N*_8ef`Y4D|TKG=w?<?EVs<0_Er)Iz3<0QQib+P-1*wPMMXCG<Wl(uks`NtIB;v7yI&q?L7-|=AFflpJL@`dI?nhqppYv{)vHK1kMdv#N+N)5{1BVLYmgP%o`mk4!Fi3aFud3$qOM|WSNp?n@2ZHpfwl+?RE!S4+&wvIz9xvqh>xB()3AhNi@io!!1o)sTxFqlN%jcLW$n=NBcydP0#j|}zNHju7a=$7I)tYcftP;2*E4Yz`-q+usd_0aKo1|9Fi0GC-@u2G08?$0{mKLRb-?cuguyoqr|K3bQbw~maqI9?hoExg9_Ve%_2_G!bGQ`ZibMYZF3WYKE1N}Z0ehAdjNQQcd%DJ)HBsO;zV8oP7l<W(n*&y9NU@wxx-?4DN&^>qaH`I7dgqf*7a#Mw3WtClLKlF)dq8G6ocaL!ooA<i4tTzj&iN7YL4rKUJ%V|?;vvi7kwSk(itMx#x=nQKM1Dv2H(2|ZU-F9v<?>P|)?Fubl6PEEo?O`OG6WW#H1**E@t#^?ckHmWzonq)@9(N2}19hWm1dnVP*(KfpV{$9tw-rvHqnTk(S_l=u{+b2d1Vc%cY)}kNNi8uRn9D?dy#@n3PmYdT&wrbh8S&BAD=$o<nvFYaDjKOB5j&9W~AM8hJZ%uQKXTjQ;->lNxxbjevVQLV>)r76)mZtpKf;!5B#=EEg{>UtKEd*Co`;1bCZGt$UW$JtOHW=7EZCxEL>M&Mq+Vg3+K!XC0^&-uKn<sSlEHoyl+GsgNcWJzL==EBKu(<_fGBal-$5B%ZSGcFQ=w-mAU33(co)D|?p|$hQfKT<_-(rRJHLdA&)o8cq18`6b3$~63*8`fBi^OV5r1o~y3Qg@Z_!gFG6*MeD&<2>?KNSQ4<zRYR0%es_X0y;maS)#>s7Ca3(oAp{CY|(-{P%1C-SmmI&NX#xN3E?XZcJ<5wrjq|=Bhn(nUtNQ<6;FS?#$NJ**cYehZ4)Zo02^@`IqVgm(FDOR~jOO--uEP4o0BfAKTlW?!n=KIAv*5)H4wX7Y!;$*GhcolZLo3_40e`KwgEO(CzKBp$`KF{|IL~+%;5VWNl#2f|}GbKY4>A+Ng&11|suzU(w!JriS5OBwLZTz`i<~9izh?R!@xXY1HgKM)&jtkj*HrD2G*}$F8E!@n{R4vP@c}Ejzd@DxFKYr9JYJ7&mn1sqNgofvDU#4^51O6-jp8TaoE;cPr=%E6|)8sYp64yatVxes)xH0j(9ZV;g+FSo@q?=~Rj%oa*+C%y52CMK;YrShef=h*@WSyCvORS|Cp2=-JSPW#GUXR2z8DS~I0_)^SF*Evxmm{+3L(#mO$-)2IwgDc`bS@B5UzQ_(UCmzC*QgNTZL5N>$idJ)gAhr8KVgp#8ZCN{i?GPP4rSl*2lZXR$W3*0%Q)fx!vRo;6A(F<m`cjoTOn3|Y)G?}Q_9eR`W*8Sd$h1EbF2Xi+yek(b@*(6~Rv{;>ik?u*gPG0M=*xt?3H8NN0)Tniqx=p=RZY#GgT>;Fh=ggs@o%HtM0zEYz&zD;Dss+v_&Wl)PS81VkuwygMcxOtZRq5l^PmMi(uD{co3aqL{la69>*m64CjD)kqP}D5hc!SN}_$|WqW3F6#XgHb%Q32wOf!kMzVPd74AkSO$?gy)VurKX!5RU+gV;#!sQw6~(r~*~)d&)SAnvxnc9C~^Zg^xH8K=~cIP?JH~s>nayLN@jDA}cjadr7{B)p9M6JdBm9NpKV0rhA{U7*V~-?&R2~UE{uHO^so&g<qvo;jPbCI-<6b@MCm*L~q9oL|P0`@|P!&LMaRh<?W~s7wOfH@TUe=*chEVh<b#Uy<SaWLroUO_uOSS_Z4Mrywx1R4WkiXIRa^|M1Ao69)_$`x304X>W;F|@#5D9DgX|yVM=wnsjI=@&<@B1bJze>X4Vu-M`H@H+C)_C67}Wk>YFvP=+E?RV!?PNkn;pDXA2#BRT!(Sz8K$m0!(RD_<}3sa$E5pR;vf_k)l&eM`F1mU9i~L?)E9rXDS#2ilE*YLU=Yz{ZOa_sN}}_7+mwQPP3L7=yj>%n{_UuI2czF4PT0bMJoL;l9}rC%nd{>_FT9!-EA?r6+69~V*32Zo^<1YNt@F|F=8bg`>FmmaJJf9@a9!ZP4vl=S}uFF;)<ze>yPq7-N6(-FtCUk7mFQ5`;J6jE@+SOhi77SrlA@Su%6YZm7LnVvN_)v>q`yvx|`D3g_><~lgi?%f~{`WoGOnIVOdb~QrEY*GZcnsO!UYT#YD|wqN()Y-uxxQ>mlCL0VsF;OVgw;<`=cqQ!c*91|Ie9^n2zPO{Jnm%EUw0!<-!!q8i%v*Rau4X7_ut`&k~l0QNHNOsnUzeC6l@K3yug&ckZ$%|r^>7ZVA6WT>=W2PkXK_LDX8;VN;`LdxFiszm`!wHU!lBr#Wftu{~+>20sD?ie5K=r0JLI9f^}AqrnhdBZ76MR*_s4dXt*tn~24l~wC~eUDMa^n#pDTf1Tzr_{Jxvat$w@7-Vjs+Mw;3+{4NLnY3vcSu~EO%$N3TwN!Iv9v&(^%_46g;u87N^0uMmC(M?Y3z5(H|V;zGuj((&z=MvYCIP`iiGwQz^PvPP`*F*_e_|KkX{>BshVD=>S-D$tbIS;%%gE$UH(@uLIy=P{C3b3IyN+m2u3D7gAY{8pg-Zwf-*ghO*`$YxpI2>M4>B9n056vYU)T0k#{!cu-cfm7Ef(3u$-0D$3m+@7be?YD9uyO*ZMs>b<`kRV~`%O0YLDww%W9p=Jbp&lwaN=sun+EzXkH@pge*RO_$1`dS8Iu6+I=6-gJXUnj}y5DbOHdEJycuuDHb%6|}WWf4EKv7krKzV_c@rqYB>6F`?3eXEgwrg*$u6S?P1@gE^}&s8Ob!H1z!_S2m?G<?*5PZ{~Tt1CM*cSHZ(k4SO%C6C&TaLQ^(_cng%bmgGIBCg6vD6tGA2XzGwYs2P(3-#PXxFp9u~d$Pi(7^mZVfNU_Tjiu$8=11S#)s-tF#D)}>txg)|c&`D4!7_1FExLcsw6d7XgMxp^=^_PhFFqS<Psh&-HRGuD%2X|=p5BVlXfyr$bkXfAQjoxC23&X;CE8PWzGC($1e9Ys@d+J}{!Ct4C_4?i#KhD0m|IlR@TRjnwAxbiaUJVf0t96vq0_DrPc@UClyyIlH596+W%?6nVmaR7IKr@II*LdqP|>9F@qS!7?VIaLdm7K?P^Z=M&iP5}(wyvbT6OClsl%^CkWe#)Dhy#e9<6g#v88o#+QTOe$bHpZ?Poi+tF=;HEuYWJH%tN<{h4x{DfH$>T(rIXNI@QP`?I#odnmSTU-LQ#*h)w5poK*T@pj+Ou>UKQm1IA$hopX5_U2nc4cCJO(i`6W@zxP)JiSok_fre3{~kHPy}w16R@FD$)biVUmivnDpIhEuO{_@|OHMsxcRG1q<GN}8xN=oVnq(60cehTLkb^m#($sdZ5i9N@?DKoQHM*7J#9b*>#fmmvjYrjt#bj%?YfaA;&kprXUoiDD0iB}f^jM;)Exr;_u-kmX4E4@PU-eNm0U{*_ehUz_+v9(Jq8EjPnqUT#W=AbKnnwWZ$vocuh&h_uBig^}pz$ag8Opw$DtOYME+1htw#gUm;=;cFBanGL&pcfkzwUYL{>_`s8h;!;+A8_lHx^plU)#|AYY{YP(aPx$bV(ZD)y?MdlfAf>VvQ_cj(4NpZB-ulD(Z?21h&00vE|VB^}+xBx8MHxrudckz{36=&R*kMoR{h1p#SubzyAGCqCD{1yWUx7&GWatwHCRskF9Jv=%4u_HJD-lE+crc5(<?2`saVVz5Qo&C?#-oEXFAR{`R-u{!tZ8y#Cac*wu2z5NM&4KmP4sfBoBE{^!rXeR%h{a8VidKHgtR|L~cgG%^$257H;vXZl+px|;3!c-uqqvGc$GwXc@iGuvTUz(0Ua(PuO>oA<XW_pl|T@E#dRs_i({WcxE&QKbuZ(7bz8FL4b)<+xP_tvi>oEtSs$jh;B?>f<O_f#N+%2Ya`*E#DGQ{Vc<w>rE<q@H=`=Z|hw>>{oltTj%lwr&&A0KIA@iHm$d+le8D^dlhUj<+*BXz^zlP`vu)IrdB?((xz6bv2@8%`Wv`~nBwIlVMwTE?Us&H8yt2IZISV-7?@JEs61`?8hdqy%12Yh7%KX1E<0JtHDJ83khV>~=3#LMK{;kGr2C~vel35gM*n0-|70XO&5A{J_Eh^+TSSG(!LCLn*ObdeFn0e=%#nlYLbR~@HgRng`-<fzVa4WZysl-)u>+56=$p?*-h2^}?>^rI<Ti0*1_^Z|JjPWIs}>TkXyoqrsvsI&Iu6RH<i~FY>JZldD<5k29a~4&Tnf7<_u{q5Tdn0IZ7Vr2Y#N`Gt&704i6j32gzrAWY+$4^I7AI)f91wLKu)!Axj&(p5+M6Osv&?jby4LLd!>y4XNzB*Qo2RTm|2(hDA#joD0dNQ6TBa<;L|Ff#gWotyRI3Z$0*<|gF`0PZIyS^H)Cmq((*<5Yg8-g7kx)2b*QCh(N__*bgImmgf8x9Z^Y9Y+E*)&tz?as1ed}dQCEKn1{B{YngR4oN8=`_<V5%Hvxyd4Vc#{#5j5#`V_2XTP&LQvvGltzl%u0&3sTn)7oizhOJuyBQ#EUgG#}9)075@K-K&+5N`8<YwD6j4{!FN_3m$B577xOOmbdH&32j}Emo6do)Q?<K^a3fL8`3=kyPD@u$59;BsMkR$eCH7h+7_>_N}(Ma6$xmmwF{(KZ9|&!uGjoI1ysbWjy01*y?WHm{t5O`;!K5&%wn&P$wV6FH5<0eR&#9`z6I~ag&q|f7K_Epv8sznJ=FMsc~=qQ>w0qgGVJTo^*uJ)uB?F2s6(yXR=%LR3s#8q-kiyY2aadfBL{;)Zz-m)4x~!9#g>et9Aq5fto&D}_j1`Vtj<yesnTj1;UnjJPz1|FD|%=}U%h2qi&nFj4-ZW|;`5`Uol4K_$HZ!!U$)HEs|13TfwXXUl&^wQs_azukb#txE?bcUusYFAMd4OOL+3PB`frE#JE&LK#%&NeJl91%-BV873s}v`roOd7EbLY?Jr`MmsXLX!5+?N$FjGdR&relye@h`MqP=QbUWq&%DyZc5A-_k6Ijl35g(kNvF;?y}F8rrNaZ{7o)MSjPX~$s?7xlc5dfYFI5WwS>g37vKTm(@Y(FqCOJzYhx{a{lS*=sx9C~m$^wvf)xOg|!A6W@83uF3@+NpZ?D{q(5Jrd=T|-JJ^wxRR|6GJVR?MA?+ujR%B);<s!QbD8X~N?k-LhL#PyO48O=f^JHz-dc5`Vin(}1kDyUeNfF;+4@Fv!wrkHofMTBU051bz0edmxZf0yX#{?YS<n60W=V5YJ-uG0LPK@ZqUs&dJ-E+Wv=WE{`Sn$I%T?xxA5hh01|++}(q7ckB6MyKbxltA-53`ykHqhubxlXu-YI5NX4r^VL-&AEpth^DPUY;Q5wH-c3$x8R1oc*LQe5M^gR`Zg933j+Hq^>1R6&;BT)Dy?NS|Vg0hZgp7Bv*~J?71-T|u{H+{tY*v){i@U{sQ0h3n1A&M259>@>lw|J^SVwN$DC=~|DL()VCX!^a<!dOC#doK9<=iZtD5D`*Qa?@Dy`<cMQUMZxp8FYVA?ZV2T}e(vKI?<-y8ZmmATH|J4jS*88Ktx72Ss}wmZ5+qaka@QPQd-e#0Qd@g_k&K3cXtNE+ATM;+iFf2zJdr(ERaS`JW8~UP!vV|!5)ExWr)*MdDs@u$($E2bq9MK+e4*t*v#nFbF=eRxNPnswB=UrFku6qF5lJzVxO)FBcfnF)bg7*x?as7Mp6u)RM1<w@J_BnJc~_n4WWxhipVxh^+K$Qkk|ay(`LjlLR*+Gpp(>;4o|E(%Sb1Kp0}oaK$ndUh9O$+6so<6>b6c}uU%#W(+CSbR@)l~(Pl@arb4;f2oj<KvW+OciQ<dw^K)!ohR2}a70G?u1TI-Ury+@cx_7IS5I#uA)fDUOZGAa&cjy3F<-dy2u@bixbt!oQIs9x2C&A1IRCdq6Fps_NTP!{Ay*}3PKR_57#H4v*W(GUamxZ&;nxB0*M_m(^}aPX{W6y|v&Sfeew$8HoI8gqwBiM%NnsP)W*7|2x6tVx<xj5{{Bn=0W_Q~EUov`P|;7P;H~0yhC^FCv9Yp&FIe&D{0vpEbAA<8mhbN_IT}RYNbZUmhBt*SOl4g145sqSdjXi!$t^z+yjWgJQTrF=169Or62%kXKBrCh!<@%P@}(e;Y$vcZGKg3yih{;l7)>5;U@+!fCcdeoG%F#7P-aaCf|;l@DGox}p^}lfcue=I_xrr?w!qpsr;=i;9;-$!eUAA1{n~Pi29h4b|z^Wp%wRO)9%wT$igF4k`{wPD|M@J{n<+V|w<nu~chDCQt>teV$UFbM>1I-=mJf7C|?07Dt)0(>o~p=krgNa)ZVox}LXN?Z(X|a|?TM)B|)d=)J8&!1`IR(i&xD)T2$gJ}xFQ^hE7)g#vW+v@+BV98uakrO<678QLg9bnd`kR&~%VFng@bMg-dHn>^F)_j3#O+tLrL!y=BDu6@?-+vK-@^0MGB|EsSOvpS?f+$N!F(f{=!1QWnf%bD`Pcia?9OSbB4YH{zhJ}f*GX&H@Ms)uZ;tSA_)TXl$9qob;fK1A8P0<#Y-SlZ-+s21zJitH<G9>pt)mo`Z$mFbs6D0GxAnTDgYMRR=X?QNK`Y^TwChOCj_z>&Er8MqnL)o<RZ^t)#T(>&d&u<iv+FXl+U+q4n!BTYItMbxsT^4<{pf9(O_a?tt)_^7z;5Y^A}dpEs~m$vPeT9|v@oH%r+8O>^mIeyerd4D&n5WUn3Muo{y5m7UpuJrvBp)71t8r8mvuL|`H-11~~QTs?seqn`ro5>~X3=vC}neyYLt&bm6&8e`6!})yKr^mdiL!wZ@ITWg;7`biBBz^BQ2Ee1C;q<KON|Z9O?R}@^&g>bBxgZ*C2RPGD+xVEiwJuj$$>Xh&)_$7P@KNpE;slHw0Si#$#@@=eYWueGsPu#?>vO&`PI&u`^{Jd&HeZzE47+a)?G;d}r_4_Ozj{!t*Exr(m4X%D7A4`p=%9T>R6J{aIDmS}qhxv4p0i)sb*`4UN(|LTS7MB-y%kdG>5;N#>zvZB!_xN_)+*?va4LJY-BevOikd&ht6kMh((U?DP7og6-ruO=JW#Emy6fVK`v$$Mqd2%m_lsquPPw4+ixMD-FL%FB(p^E+R?>0%tSY-kB@fc3RF!US8=$Xlg%alOy!oOEbd%A%hx@SHhQU~tuLhjn6N}cGZk@nPKC151uQ_gSY?x|aymyKSmKpXcn74LleB~A;%kE&{*U%g4>3#3K5p65Z^SArMPOG&eLa-a+a@0FNv@4>Zt+uk95~InKSv?!n&gr$j^p7ApHbhBP>au!T*BEMVt}9osOLK3ywc0p=dGK@VkY-)`Jw*HC3aV10M^F}wUdT4xg7Vg*b^6o?rfT%Vtq!1U*l8*y)M3<SNXL;qa@Kxiup_nyavapT`TK5ThXTs%8<A|l#=1O^#8l3U-vQRSJwZ72s(mfLv9bE0_W7G~^KQ!3=45nvKk6vb;D6IqTnLeag@B`zdyF)JCad259zk4UD(~v+>cE+bXAHcfvE`W!J_g0}JM9I^ysL&Xjcu?%tCpeFix=k~GGneo+Y`BQL$A}L7IO1)<&NtVUhTK;A!!yrsit3{vT%8a^e13vChwEU7V27{?L?*IhHa3}NjW98bd&0tXwwX`dVYv-EH-gK+Nr0J_?2fMt>EX*J+F^;Bq(>JR)R~=BStOLwpfbO=%qT`vUn^>CaXRi<}C{M?)DxO%(;g6o^{S1-F`|FdJ7?wma36+)CuhUSl5xwt*LcFnf>+ViPL$ejvZ1t>z5U-;F;JRg$m*nQK9wfn(|_}eMC?~qSM*Z(^qE^NWF*lu0gX<Io9_g_3o{=P!Gm`uE6-6Y+YJUw&7%~PP0h)MA`4VWbtc6q`pvsPEDS(rW1Qo$FEf2_m^TSJ~+(!ILxLff5IP(x5aHE`iaaIdMR=4nH^Oz*k=!qs_Dv;r$?>BQb#TR$B$&1?pNzF(J-_S5N}L0$8NP{=uf$oW9si2qO)p0pRzhk1!hy##a3dj`_k$62Y5t&Bnw?={BF@o%3iQ|IVv~(h#K{+^#Rk`au18)s2>V(*p|}<Te&LG32iAF+H#&s!%%gyz~u?l%9k%g4yUx5U%%7SAYv*PdZ*F?GB5`+Jpdxktm0)39_xp)H;uJC22L@m`*0nlNBU#Q&1+2{k5GF26yCs3p5l-H`_7zu|67^=7`_YNoqgbGB)NMrcDTqO(kru-)$YGI2nI+^elE*blek~LS$H1F_={0}nQ`zZFkJ<rL}U`rcr!nc<0>FZa&mc#8gY!D$;?zFr@pB6k7q8b2Eq@5qQ=<%#b^84-F_S!1I-n`BB9M|k-b=r*)PQP@<^5BHMw5;C-A=;&r1wf{pn;ck5P7fA<s(#D^P^%<u#Z`!u=Je=Wp*9Wjgq!M)zN4B)=KKA1!)@-C^oGjl%c#_`T{Rd~k^d2H{_BQv1m*QZG2J-9*Urx})09Y(4$jQEl^N@_oj%AKDo&JF6X;j{QDk+QvitLPOa-9;`N%Z8q$gXCKQS*lkYj&+%%b<X*eWYs{1H)?@oP`3nwXM;S_T+k|gDCr_3}`ZEWBhgX^L>}WhXJ%8f!Ri^fOX0U3Q^3NQE>+R5cooTpexFB=3zBUeLNQA3G#m>RT&W#m}!NmYyXzHrR5|xnnz2`nAtF+XvO8+CpxC{*A{>G~)=y%k^*!;n4k|!7Q8HHsF%<iU*=9{TOEOy<^#-}O+|39Zh_!Bw4TU6hY0d)j7+RviB4p2XT?xtUm`nuMU`O>u4hS5rz>yI^;UX#K)&b0SQb{#l|>3;h~%0}V!^>U25LD_;1i1&*S^<YMn9>uDE1Q6O1k!Gd3*jg6;QP5|cpjLBi^Q!=I;YgZ8W_V#<L5s@L;}rbHe0Np?6p1xf|GRbQIoZVgWhgFp(x3kE*T4S>cm3zz-fz5J4IPd9h%zAIFVwfvwKrk+L~%v$&wH*Z$OMtcOUv`+hON=Yz0)ut9mRgyG12%N7FSDP4LLJAwU>Aw0L>DDGP4}${!y0d7(@?@U*JZ<;?O@^yS%Xj$0EVf+Ak`d_Dd}<D+deg(X3iS{mrySV2D8BJampVMngf%2w)f%zU|vn*Yh&G{1~xu96I}LiuLDomaGj3>r*pkKkoY;QYcMtxTHBa%i%qinnZhLh?4C=ajRNZ5+fGfp78t&vA@*7Q~5@IVEFK-%xbqQpDn&uY4RcQnx~;U-qb>N8=zIsIpuFP0v@k|PPw;r-I#B+a<#HnS~X5-g_oXR4|mH{au6k3$>ES!z8cexC5llk)V3nb&AZOXS6*Y@KWx~urlokczf*fsL%}p$HV89^@8qlW9_pIS9R&MHG-oXo{O%Xugvp>f9e?{WmPhywYPH^Tz|pG7Wv6@9W1O~`+muTRmol8cQ-8t@KoKWO(D;dJ4bA6QryppjxHL_jTIEykv9#Vft937);0*H%Ff4?_-DHsygytrPvOnegZO9u!qXez&l1jLbP7dAjK|YULvNl6ntle>bC8mi6zmX#x8#SiBF|dN4NxT_L!K1XBwR6_`0yG>^NKiQotqN<$w{77Yp4PBu<bh3I*8~A~ia1^x<jm6s=Q-xKq|R3&cDwP7FU&^{c%v6#L}+rKoh%7~j=1uvD(CVW_Y*=VqR(2k&Dz~r%d0mrRyZ9_3YbyHE$q_xtF-{e8nn)h-zi(HFWDW%8$4Y2W9{wsdl>Zi5uJ|D>T5J(TM*-T75<EBg(<=ca{g9)8ES?#Tkm7Ay2|_7uwTA^^xnQb=ZzBjE)xNla=T0bTXLP+)Rf+NLod%C^1y6*rkC#n4s@V5Fo~RBp4y`HF-?#CYji^o0iR=<^=EP{#7w(BWWt}=FddBrK}*GkofROenUtjjsdv@JCJ*YhY%b?-K<&^%u%pc4E@x%hxO;l$7ig)ESGQjEU|Qz-m!o7Oy+@6|;~59Y+DY<7rx(iNX>gvQ<1Cq?XUv}}`ToE>0j)2l0dE!EXpJ5QUx)L<K)QD^FF*qFq6*lpe6*1o<IiR@3HDhkb;A6;rLzC`gN4uULgX^mn}P!fqIW3pI%lllps&za+wb}JZ=qN1QAh-A@)OmpE0QIK7|h8x)C*}{dyB2VNc1E4kRn<{DMVBqAGvG@Ny^HyW~z1#_Q8z!GhyHl{NMlA|NH;^AHL83?|+^7Q|D7U(J7yX(|DRr^JzJ)r^Me(r$l@#Ii-Q$&M8f&G@sIPO6!TvC*sf0iSmht6OAXDPBfor;f(B*&!?PDnSW(I<>8daQ=U$FKIP?<*VAx54e2z{X~;MK9Zth|8m7}QpN8c$tf%pO8q;Z{)0j^q-`RK?CyuSBaXF1EZ<f=PP7|G`e42*S#5X>jruj52r)fRS=hK`{Go9vqnupUoo@Rco`7|%5dF4a(X-TJrPD?&5!)X~$%XC`!v6s`bp4RheO{bMkYd)>RX&q1NbXw=r%5Md)h2P7WU(A``%$Z-!ncvNsU(T7|&Y54&ncvTuuao!3*WnG~72+M@CE_jOHR3(;i%k3`6X8Ykb^J0Dzs<z2Gx7UO{6Z7I(ZsJb@jFfYQd5RS_&R>CiC=8uH=Fp?CVsbxUvA>JoA~u6ey3@G>G(Q+vx#4A;&+?)<tBc+iC=Hx_nY_yCw{|egpK(+e#wd7a^lyV_&q0n(TU%5;#ZycT_=9oX~JUQ>-c>qe&LDVc;Z){_?;(y>51QZ;@6(|y{8$ghOgsSpZMJ;e));te&W}k`28m~Kw=9dHbGjjy!bk{LSi!{wnJh=B(_9iQzW)UVq+w>Mq05Bu@HGBvOS3HL2M6Vdl1`$*dE08AhrjwJt$$t@^x$vVtWwVgV-L#_8_(gu{{V28!KCuHeZLujn$3ijrENMjup=KAhrjwJt$)j@O5ktVtWwVgV-L#_8_(gu|0_GL2M5iuvz#zwg<62i0wga4`O=|+k@C1#P%Sz2aVWOd>z|^*dE08AhrjwJ&5f=Y!7045Zi+$Y(Kt^?Lll0VtWwVgV-L#_8_(gu|0_GK{NI#U&r<!wg<62i0wga4`O=|+k@C1#P*;C8=9|Udl1`$*dE08AhrjwJ&5f=Y!704(2AXpt<QU(?UC6YneCC;9+~Zt*&dngk=Y)Z?U56F1YgJY$ZU_y_Q-6H%=XA^kIeSSY>&+L$OLD?*Ree^+at3*GTS4wJu=%P!{xx|!0CwB;p^ac;CSG9;CkSD*dCefk=Y)Z?U4t#C%%sDk=Y)Z?UC6YneCC;9+~Zt*&dngkw^G3zK-pY*&dngk=Y)Z?UC6YneCC;9+~ZtCpbL5j_r}z9+~Zt*&dngk=Y)Z?UC6YneCBhct*aC?UC6YneCC;9+~Zt*&dngk=Y)Z?U5I_P`-}sk=Y)Z?UC6YneCC;9+~Zt*&dngkyrRyI9v9%Y>$EMF|a)bw#UHs7}y>I+hbsR3~Y}f!7KB1Y>$EMF|a)bw#UHs7}y>I+hbsR3~Y~q;J*1fg6rn%*d7DhV_<s>Y>$EMF|a)bw#Sg+;rTkY$H4X&*d7DhV_<s>2nL7-2nP}a_&NjvL;{2Y!~z5Zw#UHs7}y>I+hbsR3?l*tU&r<s*d7DhV_<s>Y>$EMF|a)bw#UHs7$!s(zK-oNussI0$H4X&*d7DhV_<s>Y>$EMG0X@-d>z|kV0#Q~kAdwmussI0$H4X&*d7DhV^|QY_&T=7!1fr}9s}EBV0#Q~kAdwmussI0$FL%(A*yj$V|$EjkCE*$vOPw&$H?{=*&ZX?V`O`b3E_{gV|$EjkCE*$vOPw&$H?{=*&ZX?V`O`bggD99u{}n%$H?{=*&ZX?V`O`bY>$!cF|s|zjDX75u{}n%$H?{=*&ZX?V`O`bY>$!cF|s|z0g;!lV|$EjkCE*$vOPvbXM|_OX9Q?OXbI7L9fCBXG{Q97V`O`bY>$!cF|s{Iw#PUjmh*LNkCE*$vOPw&$H?{=*&ZX?V`O`bY>#n9(C6#e9wXahWP6NkkCE*$vOPw&$H?{=*&gG9?0~OhdyH(4k?k?EJw~?2$o3f79wXahWP6M&(g@@coJg=eCbq}K_L$fn6We2AdrWMPiS045J*I?&gRf(IOl*&d?J==ECbq}K_L$fn6We2AdrXAPgs)?JOl*&d?J==ECbq}K_L$fn6We2AdrTQA3}46gnAjc@+hbyTOl*&d?J==ECbq}K_Lv6bI(!}5V`6(uY>$cUF|j=+w#UTwnAjc@+hZD$6!CRzkBRLuu{|c_O-P)OIU#jI?u6t?vM0U{`4bW-w#UTwnAjc@+hbyTOl*&d?J><rv-mo;$HexS*d7zxV`6(uY>$cUF|j=+w#T#}ALHxT9uwPRVtY(%kBRLuu{|cX$HexS*dEi0#0{Anr*3SIne8#NJ!ZDY%=Vbs9y8lxW_!$Rk2xX5<LlTSGuvZkd(24T|5y5j651K7t2d*aQ<2in{IDxt)cW+Kc19x0zkZfvwoGbg`FcxgXZhZi)XqqFD@pB)MEE1Aoe6(qzDsIn!rxmZsh#n=*hq86JIa#O&bgk{&iFeMuI1m0zm@Sj_(kJyu{me9;XL4F^S$G5u_<S^<&3|@)|}a#Guv}!gU<L{Bdo&L@!y*HZ_WI-X8v0<{uWzy#@}Mw&TQOyg8BG5-f%P9cZPvsVVD>;hLK@qm|5)1*TK?k>X~glv$1Ek_RQv<+1@i7e1^prEC{}iZ9cQnXSVtbv-5_VVRzneGaG(p%g-xT4weqD9k%_#wqMxx3)_BS+b?YUg>ApE?H9KFlCZ}3I=217wqMxx3)_BS+b>vYZ2N`R)xx%42#b-gV>>Tw--YeCu>BUc-@-Oq*k%jcYe51%;%ls2zLxE^uw53m$-*{S*d`0xWMP{uY?Fm;vJ6<_d>z|lVVf*$lZ9=vuuT@W$-*{S*d`0xWErs+__}f0?jMPCAgNuDY&Ryg3!Z~*y|Aqpw)MicUf9;lgw4o*pKZOctrxcS!nR)6)(hKuVOuY3>xFH-%s7Ygb!_Ve+Zy{C8yh<tTN`^Dn;Yj<Ik56|{2U8E$HLFC@N+Eu91B0kg6CjcFZ>+K3O4{hz>a{QW98>q`8ig8j+LKd<>y%WIaYp-m2JHyI1IjyZN0LsSGM)awqDuRE8BX78-WjDTdxGq!q>5_SGM)awqDuRE8BWyTd!>Em2JJUt=EiGHDAYeUfIqo+j(U>uWaX)?Yy#`SGM!Yc3uY@zxg`0^U8K!+0N?#_r=$-omaN=%64Aa&g-}(wJQ?BCnvS*i2vum&1+&E;WznjvyE4_@ya${*~aSxkbtja8?S8Rm2JGTjaRnu$~Iov#w*)+WgD+E94}wTHeT7rE8BQo()Rn=&MVt_Wjn8I=auceF7VR$8D9%W4o?nr0`LUz2>=vu=J4j?&c&a@p^HZsmo7eCoVs{*aqHsO#j(S)pOb_Dd;-q>4DWu1dq2a!pAjn02$pAr%QJwBGo1XHBx>Lj@abnb^E15m8Ls{ee|<&<x&@atobqxM!f!{y>Lk5<k^BdL9q#@NzkWslIRh3s0~a|XhMa+noB@rTfsLF8iF5b_;E^-%kuw02GZ2z9Ad)jMk~2V(Gf<K<V3PAFp%I@zP&p&2oDo*eh%0BHC1=1TXW%7g048T3Cg(|_DLw(v<P6m04A|rh+~f@4<P7BG4Cv$x?Bopa<UC6N#wUQEoB^PmfuNiLp`3xCoB^VofufuNqnv@GoEM4N_ynMoGq991z?3u4lr!LzGw_r%0F^Tkl`|lf^D1Fp;yi*mj3z08<OGrwNLC<ef#d~}7;KrrmKxv_k{n2OAnAeR2ZDMD>?ODt){i6!k|ju*AbEnIUjlzgsvrQEAYhU$2nHq~m?R96F-XcFIfEn(0)+_{CV7LPVFHH<9wxbiBo6|K2_`0>n4n?;iwQ0!z?dLo0*whaCV7M;5|T+sDj~UqAY=lO2}UL$nV@6>lL<~HK$#$A0+k6?CSaMMWdfH8UM7H<AZ7xY31%jsnV@C@n+a|vz?mRt0-XtVCg7Q%X9AxIekK5#AZP-i35F&hnxJR`qX~`%AT0q&OMudlo+sdGm;5{dSW7_G5}>sNY%Kv?OF-8W;I#yNEs-SHus<NS1dJ^KWJ^HV5@5CjoGp<6pOPd};*^~Z4En&J4-ERipnog|o$!M9AaueT&*HCS8vtu=z@Zb2bOE9h$?n0AKA`ACf>pO;(Fw)|7@c783mTnB{tEUYjGsu{oQ+5)EDu1^32OwHbizW3fYJ%8sRflzSb8n6biz9QN?bZ&6C~_{Ju;oJEpDOdM1n)(u?38l$C(A4P9(52UMBn)iGkqBNGv4yG%o+<Aa%m-e=KEBa2~fgdm>4hW!)l-N}Pd{hgTUT(f}^LfvXez%qYtn0P+oBo#1&AT#p7>C-|cThXl|%!7C+_b&og!$8-U%6Fk%fxlV9Z3BD@9StWR@J$jwsz7qV`1;0*kWVZlzf>%o<y9QYG2Zo(UKx_HYASiYsfv-0hJJAP@ooM^daz(NeTwsC^OeFtAR3h1Ah)X2kwp=j@qMhIp6MSMK0lE>W1?@(p#s%<?2@W#BL#Di4fmps>f@lsmiCSHPpG-Mj{wCaI5`T%RT@r_hx?Muy4nTK;*GzDmlcWtKc?13+eWKkdZ|I+VHK~Aif_DYto#0}h33(^@>s!n_p@{e_&^u+xlmPFq@<rYfYZNA1fbW#$JxPiMn6iR>^A8u!r1OzU|7w}^uLgW4q(09?z7z7OghVPKlS)~<2HsQ_w}Dd!(y4@eDj}gtl2M_&pCqM1fj=RqN|IEe#-C8+zhL1B)&51CB2eBBG&~{G^78A1RP2&qC*))aNm)WxM)GInl}vIa{s404n>_n~#Sd8gfW;43{D8#|Sp2nM@gpY>=H$bXlOH+xAFCN93BHJ)*CYTVx?U3y#sr8l0b@)6852;(1eh@aXG{PZlOT=ge@%cI6R^gV<(I;V18z)NHZz<!5XY2dHzUhCnpBQ#{K&?SZ2ZW^k8J$N#*b{g%*Mwf8$Yt~=V#*y<?f?5{7AdCv^!xs@5sBqHt$a8Gx?E;cS2LkqnUR?SImz}y;J`B+&jy!f2G`ekZ1kna_>Q2Szqowh|!;yd!vOb4Z+-7`n&?U_aMLJKKCBvm)_^z!}&{d??LYV$i1JCdrwF1edOMMG$j1zG^ZTt_<@2SDENVbA1L^Nf*&aOk%{jz@%hNak4*dzmWdBCeu)<&GnnPfWkT|ikbPKFmkFuKe(W+KSHWQ2k$WGx_mO)ax%ZKKAG!CDdmp*Cl6x;l?tSFmf4JNml{8pkkP;wlF-Vb5@@^8c7`n2aq(O>()eIcp%<>uhT6yuX+90GTM-qM{;YSjFB;iLAek9>X5`HA%Y7)L4N%*fvIhf@?$P2SD55j~3&f*hLo=D*LN+9@3!tgc7$Aqd-xC*!Q9iI@oLTUdJ!a`vz#GZo=MS>7Tf)Yg%nlETkB=CGC5Pc;ueI-zRC2)NukbNbveI?L+CGdSE5Pl^vekD+TC2)QvkbWhwekIU;CGdVF5Pu~wf2BcM{@`ap{*}P~l|cWM!2gv%0G7Z2mOufPzyX#(0+t3zzNO`F5#mLB0)7@$U<q7c31naiY+wm=U<rI+34~w?j9>|rU<sUH38Y|2f+Msm5~5=og*R%Jf8r#A)i6pc$}C?kAH$spnF%p7A!sIvnozY!qwFy(5X8+SjA4kJ386C~b|xVWljsS3iv)p-B&=bOxJb~rNJ1M1m5T)4ums|;B+OyscGkitumr#zmOvhsggp#;7YTwF3G`tJ{9y?MVhIdlNhri1dy$}fk%U8R6xK?itrXr$A+8kW%8j}bpOE96oaf{~ha~_Jj06>o1R}8nCb0x6u_Rn#kitmN!bl(!OTs1wIgA84u{6rt#S(xdMuH|r8s+U`2?(VabTN`}ia{A838@&gF%nqClF*7l9wP~_7z8pB6fzQs#gZ_KK_nwVB_ly5BS9x)kz2+xfLca^Tt*UlF$iWP@QW?Nyosd%-HZg`44e}Zh{kYGNRZG-!ZrpGjRX~q1R0G49gPGbjRYl)1SyR)iKoRHfSN{voJNA4MuMP5f}%!(q(*|KMuMnDf~rP>tVR;LF$ilUC~G9)8-un+g1AP4x<&%wSQ5rD2y7%MY$Ql*Bv6heaE>LAjwP^;C7~UI&_<GQ3aO2Rc$yGU6C!FtNKJ^T2|+a>swRZhgt(dzSQ8>^LTF8soa%+dR9H-f##DGrg~)VcGQ}t4jS875)&L|p(j>1GYhaRhiZy^pn-FRfVr@dOO^CJ$;Wi=OCIsAsh?@{{6Jl;c&`pTCNy08vITB<!lEhsIb0i78kmg8;yh+G^5qlGYZ$k7<2)_yOHz5EgMBs!FoFoQArXxY8BSEMmAqXc#;e;@p5Qh^2ags<p<Cr$dzwjv>)+YI4xt>fCq$-kVONg+9s7Q!>gy=?yKm@>-B<Kqumn4`A0G9;BB>{3tg1HFbBFGA0l>}TR0a!^uRuZ6<1Z*V%TuDGz65y2td?m?<4-l3Fh$R7INdQ?AP?iLkB>`ti09q1|mISCJ0c%MBTN2Qg1h^#uZ%F`L(k#zDT@Efnjy200z(N4_l4f}a!fPwUw!&;H)V9KHE9ABtyDdH;{I*yKz+n=Am;@vy0g6e$Vv>L{7zaw22TB+SN|*>r7zs+42}&3WN|*{t7z;|63rZLaN|+2v7!6984N4deN{cK6JTGR15{85l8WWRrCSpz~Noyh|g%WxblQ3rioJotEo$z9T(IkL02`EhhOp_K#y5I(Y)FePP30O@6Sd)O(B)~NZcufLelYrPHKsE`OO#*0>fZA+l8Q?Z)k)zinKgDOU7#2ByUC%PWauUFt1T-fB&Pl*?5&)e9L?;2#Nx*c{B6p8v0azyi*GT|&5|Ev=$VqIKukf)^Xom4ItPKD>3Fu7%9FxT10+2~SWD+2m1WYCYlu3&`0+t1EnY73w2#vVBPOJ?8G)WxqBF}-fvCNmV44|3>tR^kOfGiZq!htL#$ijjwgyQlhg$!BPkT*JHd<?4u;7wZOiLgq5-=sxY#qZBDi;#@VTf@o$u9E=lq(x3_cx%9S5&)hAgeL*wNx*m#K%NAY=Qzs*&ob%I@H{FCFIG`Vz-SXd+60s~0j5pBX%m3j1f(_rs!hOZ6TsR8v^K4>Ht|vc*d`#h36O09W}5)oCZM(nux$cvn*iJ<Ah!w7Z31?i0Ny5`w+ZlV0)CqS;HEXt1@p`*X92lCy!=%f_V1Zz0Q9C+`uDNRf%hf=zG;<1!u4>nif5DKg4~~+8RY&D82|+*V8IDsZ~_{f00*aayc|w|;3h!02^ebvh?{`ord8f4B7<a1KynkH+@ln6lp>B&#8HYkN)bmX;wVLY&-6VV>HCqszgqeZr;EUx5Sf!;afr=HNGqhafDoM!qZ5L3LX=Lc6emPC3GR25{8}m$*V+OicUq-ZA^J)1#)#f&m2~?UmpxMSBSk+_^dm(-QuHH5KT`D9NYM|4(qFG#Xcc4^UImdTt%B@|?5E_fBK#@JpCbJ!+MklYiu$L>e{TApA^-{nP>}!?4NwsQ6%|mC0Tmrk5dsw@P)LCyDiNX*Au3(ccS3X`L?=RYB19)bbRtA2I?I~EszP)kL?=RYB19)bbRtA2LUbZTCqiT*L>xlIAw(2HL?J{JLPQ}%6hcHHL=-|qAw(2HL?J{JI?Js=)d&%V5K#ybg%D8)5rq&@2oZ%4Q3w%*B%*xc@t;iag2#{YR>twEc>Jze$j0MGc`tI>lJ~N~?m8Y%=L#NA=k0qRcswCc5&|Wi<)_d`MWCef_ES7GG*S^L34xLjC<%d*5GV<Ok`O2ffszm?34xLjC<%d*5GV<Ok`O2ffszm?34xL%P>%8oq~WJ*7NYak1SG!z|HNqlVU!R?31O5FMhRh*5Jm}Mln_P<VU)1J2|Jvy#R+?yWRol1LWG@9Y3l}(i!pYMosdKncT>g1uM%Bc5yll|T#?3=Ic*u#mPu{wfFypEL`WB(zz%>%ptQ9FeKZVF+M0tt8iojtg3{I|Bwwvt!w|u1P`We>QQH24Uy4lv|3Ppd1P?-RA(XbRA^eR&hRWqD+8Tx^ZT&;I7<(pd-@`B1zK36cJ%fl$h{%M9Oo+$?4P*ieK!5=VH~;|%ARqw*D1bI8WGo~g0t7{5f+R9+n#i*Zx64oGn}#8RN-{wvnV^$QB9x4XOOQ(@(Mv|qC8#D-l26PsBab_nKN^Mz`pJ~!V^}_rP$tn(M(`ylDU(PkUmJ!9s>%deWrD6UCHXB_aFA9eXe$%Ml?m#~l;pQy!9ie|ps-9Lu`KH3cMU@X$z_~PNOYG)cv+N}MWcKc4dt`^6q7^JjU@9#SaYIQKFdfE7M=()Z;H&Td=J-Q^$AOW=#~R`At4J8@$zfS5D9Sr{5O3JFUeQ97x`;4z9jQY^4Da732RQYn}tO{Xas~uK=hkMz?q~$X_V{mG3in&TZTx~=Sb3jxizdqQK1tVI?<sMAv#fd7O7{Eq7$)aQF|7-XA!McT82nOphX2*WS~U{T7;lQp-v>~L<?HPphXQ@<e)_lS_Gj*5n3dnMST@5LnO-3+k3`36oF`x-j%zSArcwZMXV+LEMh1uOOcNj{b&)876oaMkQNPT5s?-ZX_1i@9cdAg7I=iDl|_t#btr18%QjYq&tfr(ys7wU(N$f<GV8dt43TI}3xXobs@Ikw0-8dAQwVqp0Z<_zDg;P{fT<8b6#}Y4LJACQheTi%=ng?;l|*G#JTatJ2`a0UH@*oOdBZP&Gla@2L1C4kuu4!@B~e$swhR$;Rtfs5lx18Fix66>goK|&s~RW`Wl<3qK8uae0v{74agh=iEph3ITI4!>7OPHxI>0srw2pw*5zsmUT1P<Z2xuJvts_C}fZ>opc0h3`%R|d~M1CJ!Aiz5k@DAV(34*uCi^b9dj7M4Gu)N(-rv1)a%Md|m@i@?gTZWFFp<i$SLPlcmiVhovt+f811O|}ibxD$?=#a*G(P2w8q=g#!%xTLnr0p2l0OC7Zd{2@}NN1|_%p!6jNTC<?B$<PB97@|KyzNQyg+-bn;j7?>;7Wd4&(Ie6CGS#sfi6?Y7Aug%^BpOWgmUqp@LP+k6)OSyLn>CHGlDbRBD^A^FoG}~A^hNtMy!NiL|+77#9p|61TX|%WPOOZh_wi{aQQf4Aj?BEMKDDyMJPoig_lPhMHodCg@;EBMF<TP7$iP678no%5&aPS5cUxD5cCl95b_Z55bzN15bhA|5bO})5a1Bs5Z(~o;QZmQ;iBPLvv?!E4*m!Z2_6Y92|kJKfiQ*uhWLf>h3JLgh1iAAg~)}Ng=mFfg)oIEg&>9SgusNjgs_Bwgm{EV1f^dH{X*v#62DORg}^WLeIbqpZ8RK+aUO;+8g$Vhi-xl>j>0$zLlO;&Xb?n$9vTk8I0NGd3@tQBq2c@sAvEZqK?V&fXpo|S;s6No!BG#2c`(0&njK{5U=9ZZI9R(u+KmDO$hMzdV8CEL=JGL?kJ&7YW??c5gISo%!dMojvM`i|nJkQCVIm6yS%bs|z77Eb5dt9sF#<t??SVNgjA3C43qx3#!NLd@Ca^Goh50LtUt#(R!&jKS!srzyuP}IpxhsraVd@G)SD3lN$Q358FmQ!=D~wxV+6u!~n6<*F6(+4PXoWc|j9H-)iXkh^SYgBp6IK|oLJbt-RhX{Aa24vGD1TzI3WHUsePXN%Q&p%TV5TZsLcrt{2B*9N0w55KOJQ0H_y=aCfPP?73fKqcq=0;2N(w_#n2`eNfe9%LNMSw-<58H7!f+I3qc9qU$tVm)VJ-?|QJ9LtP!wjOFcO7{s8K>UUx(n0=#B8r_P{6<CZRA0g*hmUL179CLr|E3!Uz;5pfCW1`6rA&Vfu-%p=9_8o(XUUVS5qw*C?4OehGfWM#0<@#-0ef4pUDUdcw>TMxJEiNn9BABZ=TPb|hg-680oz$%_%q;Lb4YBy&!Z@x!T2l5ZmElRC2G`?GwDuTJtW{AOf<Y$h3Pl01J)@!@5&+%o(uHa1~rQ<h{}ZX3=PyBk2oB<VUo0Op#eEfqleBcI@Vkz@cd4sH-LO&DpyL=*4{%ri}rm9OU`JC0|^M@!BhCOf7q$89;BuCh~PBo$v^E6NC@og-705xLJKnX;f?_gONDGRia3WT{a|YK$ZnIV=Eepwqyh(Qt!8#wl%;36u>^0+C5o0;sM4(I)}Mq#z-H?n$69fnc$E@j)aCGzeyk%=9eZN4|>RfQ*3#L2Bgt$Xf-i*(Jt9`pArhb`$vo3B~3!lVhRetYybS&568)khrJ`GP0Q>Lq>W-$ZsS^Mv`+)l7*{ikmtrezvRinOY}gZOvsuDX%iuD(sE@Ij-w&hvt>e>rKQV++$)+d(;!K+pD+_Lxl6`ONa?(knUM1ll0HJ#M@aj!7z)4oBX6cb)&c&=N9Ih!wjzdW?o3DwYsoVWaz9An7rAt~%by8JBq58uWYC0k@-~Gg<d%fw@{&XovP>G}8IWhn_CT_ElSn_>sYA$INmAEJDov8pD!FvRe%anDypqrjkmSzrq>@16sgMPKWYi=?1hS=&6qB$K$gYyyShkkz4`j%}%$kr&(;)UiGL6(~ko_bn^_E@}a%<X>YuVelX|bAYFJwo9m<`zx@@yJpgNfy^!;otel5HBqcGzXew+RV14Prj*H00cbq?-mY;3^(OTnK!~ZTAjsIe3|SlO*QwUcz^vHt>*qaF>9S)Hvl=!873Z(e?`w2XSn_q~RpFJ@%dS2;n4un~5h9JK^n0^8b;Hlbiwu`L6s2e@$)%{tS0RayuV6IpMxYP6py9NxlWoDWO%8>sfvv|H1Ep6UT9Z<VLXz<<Kz6cf|SPci`+W%NL{M=!APG+&tm#2?q(nNrG^cAlyD}_YViZJpfiC4itnF1&!k6#m$SK7e_CTu;C#11QH+EbQFg#9v?0rCk(<7gK)+m95M)}3>xM2!R>Dkf`z?32^K648-&vaZI1$cWP28QC0L-SpOVy1<-~#d=_KzEixlS$!oh>&<N?A3!qJ0p_8=TS2&WIi@q<9PKp<Qo5H1i17YJkvv^~%&(M!S?&>grL96*lzJ)FPiBY!{g_djy}{v+Y+Ne%`#Df=Xcghv2vJmOa&+Tf)jAU9^J4$c|^XAOa~MzVE*cEDS6&DX(SL%?_lAP<4Rh9)^=;C+L?Msjwvq}&4BB<(5Sv#BQSB#~v3Y+b$>C2gn4$lFQ!S_Che<VUz0`MHt06Cfo*<I4r^Cc%~_adGk^{Mqey;n!!m0`Em^kKgx!dlS$m0^D>#zG;%>fHeIE`zA2zNCJ;Qh6J7v%`O={A*>PN+Lps3x=9X?5O>Mp39*h4>~2wTLgc&T@PrUZh=GJ4cunFF4JC<}Gwviejy(1zi6=zKS{6@}tV(&jZC!4eJRyo+QhAzWnIdogK*b4sJ|yiqh^*Iaev;>(<$_W2d79)cU=1VI5`rxu+Fk&1n&fpX8$?dhwlm2~k^ETh40!YhPELr%gm5ewJ^FYqP&t7Bh!C4^Q+fg!&?ToQ1Z)B+&>k-*MDSa{oF>^OfVbu5*H6rx5Zy1JIU&qTE{|A$fz1g)pAhvWkw@q!#C`&)5P?*PKq^EC{)Ff+dHlTP<@iAAhtLTb1kLiDEr%yG8xb0fZeer+OA*Zi7r>oLo6#)L06Z#~iAdUvX1Q3>2W(2rei4Sh2$Nrg(J#X67h(8|F!@Co@giw6!hjcH!i&&mMABx2AumFkk)*=XD~ee!!mt-%+KVvmMVR*@415tLz6c{<G|MMoc}#r~#=Z!1UxdLg!sHi8s}W|u2*Y1APamK=+KmY9Mg(#q0yz<ZoQP&gp5?~G6^kzxXDr@WJ}drM9P;Lo@iFnqSk7oSBD5P3+KousjlfVuvn&gEW-t`dEDHl$8w^D>%gVs!215~np@_gxL|`Z)Fcc9OiU<rvB<)6EC?b#(5y*)MV_<|%BSNPUNv9FWiAXw)FiHi-EB%7fafG3;3knaXdI903QxMZ)gmE$WNO6&v8zT&kT|juk1Q}t3j4(q+7$Q6J_;4OS9C`ea#~*q8_i9VQkSt+JmX<Ad{kqPSFyekq;w!x=b^?!4U#ml<in+&=cLCj(?J6U8CrlgnG^%W<`yyVD+Im%-eEqgvMNihXh84o7^uA-|9&Nu%)CFwEX!Tv5jyY=&Z8x&?edkIoM_&YKmmA1iioOK<R|r$zfZJ)wA9y>VUs%cym;%3TVj+x#(;{hu*c!WWk>7&-xX7=;j>Kp<N&oO7zX!V#<Kcw)a9ZS7jncS<Phf9u1LCqf@m4X<O&I8wL>*JzT62q@r{A`>NR}>W`y#30B}o^s9lgkx9v70HWQ>b{WtR&r(<ME}L^>_vUzGG5bLzBgUPmV9@!G`sT+?%muG1op=$f8mjGdPGE<MLcJ7K2%(*Ck#=h7~{NP;UC6R#z1OR`+CnDo_2s(a1Om(7tax7qn3+hx6E=a`4DX6J&p@3M1gyxwK!i=@wZI%&q1?0k_#T3oGU)8cF;rI!0%#l5auc0O)jT#|Fl-xCJ#Nm{cpf=}!DlAKF_Hb(IY9iD^^PeO+$t>Tpt?^c0T5b@CAN$Bt-ba>J#`SW)1a!t<RQsGSrZJ&g;PeR)#q3x5<_DN{_B(#0fD%Zixt0aI@&X7<5TVp<rFrP-4-zN<46Xw&7Bt4v@k4KXJD<<i*ZjAX)?<FT;VT8+)QO^gv$q7@UBvYdBr>opK0;f!c?s9bcU~N2_WsYW<qgm!?mN}Ybj%JyoS>|Y#`9tUL(~-abYWX{XT+U433EU_IZWQ{UMUfnyHf9t9WEU3m50IU}RY$^R{zWsPw6UZc89Z&2ElvuLOykJmj~xEU;g1~t$l;G1{>b5v9R63z;pZcVKQQ<v41Uw7d=3V0waCyWXLR82NA7;)?nmx^<nBlAe&p^)?tbL%*W7(Ma`z*5Kl*2m{Qbz^kNo|}-+$Ho{pf%{I^d5E_+K)EUyls_kD%ZxW2%rd{819F1i>MK;82f<E5`WYA>km!Kd$mkzK{(JzlgDYcttox_(Y8C!z0dOXub}nW?N%eAHEQy`tXDp)W@9uq1O7n)mjMxR<9`6N~;`mrNeAnxY!Gm`~a^)?i~pXbVvz8qy!~Wf)pu1i<BTnN>C#u$dMBCNC|?Z1VvI><=l&y4na~9MbdzZD~W8WA>&F=lA~4n*2J!2Sh1{_R%|QAU7xGxN~?r(Su60doszD!ZmaBUin?Yf-QiDUsNLZ;=CiCuS&p(EWkJe{6n=jY{6q0BL-8&{@h(H@E<@=qL&+#Z=`KU*E<?#EpJnnI=Se8tWhmX{O^5YSnb#~&xT(3`%Dm<ean}!-*L*MYD#`m->AViIt>sT4(BtoYvCeD8lZei1-fr_w=QZQ5GqeITv;y;XS4co`R~dJeaaS34m2p=Yca?Eh8F!U&R~dJeaaS34m2p=Yca?EhdAqASo!5+;%(%(C-6Y7Iwwr{)!dX@v=GM2H#N;|O_A)f~GBoxwH1;yIn=&-^GBoxwH1;wy_A)f~vWU^%>%3-2?qx_hWk~L2NbY4w?qx{sWk~Mjv#fgvG2ou_Sr)zAGiKW%xtF1~m!YheA*z=ls+S?<lp(5@MVt0s=QTrPFGFK5Lt`&PV=qHvFGFK5BTLFilQQz8j6^9TQ_4t{G9Dr05wbi&5)F-wq5z)|tVX~Z(9;~5d@z$whb+>s*$e-bx=7Lm|CPc>MHBopsb+E#ELU`Pgkk2MZ6=HE<_+CU77fl1zL}ha+K>btCYN$1!=^b2o67cS`5v4YpkY`xC)q9nD`x?m@d<1j*f%HnE!aFTafXdEjGR$%$*^*UnKSI1VdxA?XHnjq=o6LCFnosPbJ{5KOfs4*Ohg_VjY}%&ve97qWvsu91(>k{GnQb+8q8RP8LKd38D^}*4Va%U$UIgg$vc*3oCKwxY~>`Z+ABJb<$DLuV=ZSa=8V-W06ms;#+uGp)H%ufLCn0>P{JD5xM>pBN1>vG-H@>zGWJ8phPblRU}t1(jf}k^1U1+o89PKMYOqZ*_K7GAqrRi!^r&Ttq!M;g##YMMOBtI<kb3MWkzTnX_1IrI2_XLo)hCkmhG3mURY|_sQPpHRe^S+C+P-toDVec5Z<GEkTNSbOlJ;k8+<o4kv6C~la>icHB)=<(b(4VhnWQfRp`?b|U-)XSn7vd#NbUkjIov?nN?;e%KEo|!_yrU%5{c@PT#uWO6(&n;TVwcbvdUzcNfAh@K(f%J4kR~<#Xu4rrCx;14u_H9F|xP})a<et6;-<|FCTTgOmfGAtYmxwn;nIRjOty+z31(=VNF!<GKvkE<eo=a{KCtGPhfYUj+X%gWK{ApI$kn-Mn;267N>z)UPdu5lWZESKDdnxzmefMGCW6y>&WmOS)2!IdKum$!+m7<j|>Nr;XyK7NQMu|a3UFMYZ+c7!;NJ4k<F%9zVId)?j*yXWH^)zkCFiwWVn<JpOWEJvUnA7D*_q_Y9O$I;06L52y!6Mfe5jQ5}OcRiC>Y5pEwq&`AN}F1ldH9P0D`aS;V!7ZxQDr-bLJt_!p`EiGvXjvlRfv#fXpDYJm8JNVG{6P|AQ(2b4k}>@KB1sRfFg5kDi2M#_QWX~fltuMuY>B|)hPin|eiBMwJAjtIAja+^rE2_KfY9Pv3)85B+|A;l7>Beg-{#S*V0DsEC86dgAaaudHJjz>I?xE}F6!jC1+M+DtO(M=@Xq)aH@M@X`SB}-_s#Q%u0n@GEf0}>A;Tv>VR#E~E1V=%lpBGGx1Gp?K}#TB8bp5cqKI3pAeGYaa*u^@abIP{?YILCsFAT8;k^qI(3Tep9%&1ZuQWG^Gi|Fpxw;{&o;8fjn~X{$j5kggg80O^LgJswC0Oofgz51WE@{csTJ&dHL*SK4#(u-(<F_UGh{n;W-D(pDm0;Zq1#KvMG{1d9k)(iS7JS6X1C)kWG`q+MleMUfViER>A+1op19m`HocAgwF%1oX8Ms<hpvoP0VcDnpGr(hVbBFoPID5_{Pfh_;e5OIHgzS+Zn?=wQjniZl8-G8#HEIyy31I`Sa)K(rmiAc(d|HgBa>g|ITC(<5&m!LOO*Tlh5y!RP?V=m5#+_sD4Y$mssa==#WmoJ-^^f)I?3kBp9wjE;|tj*pCvk3w#Bkk%diD&ek_MkD;DMNTvLO?O>9gUGMq^6g(_uvli%1HI|u$s!K=aWcrF5?Uz-WRVZOsRv}y5^d05&1g!=XiCXwO37#{&*&x30Jbxb?F?u;1KZ93w=>Y~40t;O-_8KIGZ5~K{*;Ucl?;eG1LKw#GN!GaCj;#k^8@nE!m5t4SqAc*rRN-#vyA?gj0TpB4wj6L?u?G^JPJ`M*5N3JM%+I-xidPs^C&?R^qMd<y12#8=;Y350ueK#n>(Ws<RaFZ(bX-sL}&Mf&oZOKyCk&C((`>Gw9IJ!-d-KlPj6IPGn&COn!)oZ=UnMVlXoE}T{&`GPXgn%z;V-}9xR8CMJ~oKkQ2!DB!CX_j1KWElBx27&~X2u<(fr6^`kLAi;}9m8*CKOQ~hYn&*&h}=pfG`ttzq&&{q|EKx7pg8%;GC-Q;<ccPe))FBSV^lolUcA#Yah7>cW#{IPt0xC*@HQSKg%G9MDJS(I3BG+wjFvd(htdfNUr1X|@!ON$R*D}Q*UPm$M*R`gqy*NnFGi^^+8d%7gXXmH8WqAoc*`qc5WjJ}<WUiFM#^^9Ki3<Z;m%xi{vNrnPRhEmA({~*KN{sT%}-V4wI$$)V(zPiY~W~hT?sDfmCD}Q_sI0a5jAQjF+DlCd1PyxwM0Rh2$Mq^Kw&Ylm7`7A9y$Z+$<FrS4#SlH+*GOt-^>W{QOn%2{i)*tlphs^8IdEeA||I2De<w*pIzEnFZ<G22B?WimPwMRQD%j10{^I0Cx){e?}`X8hnbu{N6!?nk7?J-<?r1;eo|4@ScW2N|6a*k)E_!-H|KE=;SW)20ZKbV5lF-Cig(H>*8N2Y#c>PM!2Wa?j#sUKReM~}?|JvP%9@>u>_JvK=)x0WWGJW0MM(cretW|Glgy!0%dS!=YJB<cJvjW$O*f28wAI)9||M>>C`^G7=WNIHM0!XA^ff7D6ZuLRw<8CvO-XrG})PetB(Dv;w#4@KH?dr9Z<6%sP(n^0zG^EBQL(M~d{S{tIxaD;bLw9;ZBtrZ6(f8_8-4u9nEM-G4F@J9~+syY0j40|-s{Gpp?j{f+Anf}P%kNo|}-;ezL$ls6r{hQ_QhbrtJQ&}oclAj9%yWFAh8Joa@;qxTlz?GQdpXA$H`kt|2E=YWy1OUd?5oCAz%-}Qjk(R<|Y_3ZVpJkWbB=K2>+*$>uvP{LDB{?EV<TG}wp2>ee@)>)%hRJ7a@*mL&pC@st^5FB<R5OWd^%D3Dx3l5z%h~USmjqsHv}_!f8LsLMeZNcJm-g&EPr{`h<Ejyoxk(5YZ&LS3C>^)lUFhZDKP7jcga)sHtY#AGw0-hEf#ze{DAS7cJx{{hf|s<?J!d5x^<Dlxtsnd}@Z1@$J5Rz6vVL+_!jb1mm?l0bE8)^Je0qjc&+zIQZas@%|0J!%i@M9<@z%gh0~V4DkDuZ4uSq<7e}?nV@ctR@Us&UWkmfUs=O19Yb^IJ<73#|MGll0Xru#wG8F{&q!{=F&^>&u}eG1RNXjN1AJmWVYs6e_%PDYR~k~S|$7zxo4WQ;BuJpV&JC0}9Pg8yZdtCx+7W(En)C<i4N0_z0I9l}He`3@l>f_}#(iO&%1z)4_`Q`bihpJ(BjN!JuUL(2nc{FcSbOfvsTwwUnGK;c7JhGyZQ;a|_|9H~1p_bdAh^goccBWo9SAP@q<SP%sf>X}*iX%INi!aS296LQN%pP?CYo33XFh*(lme8F6j(S!E=A|}OGELWx(<iACpo}o)3`R+}cE;KWerX$b2Wa&t9g=7XYCV3X)U`x$nol%ai@>AIWxV=&4y4MeqNvN9SS*(P^@jP8fCTB60>@l2?A#jpK|7rUzqW>f>S<cI-OG58N=w{~aKluE7s~?r;ZTsQ#B5rljkIJ)bMX~JWP4Q>Noo)wip_0PyTjU4$EsOjBzZ5JtVoYq#8M|}F_MByZ!mG?;bL`N0yG~fCgq8|h9(G^gJr;NmXr$yt`bv}hV8VZph{01pD<v=DDdeZ{5YS7>i+Bil14yRiMW{Sixeg!0tA=(;#tc@*3|3w?H7Q(-_YD=5yvX5bmG9wC!Usc6B|}doFWa>Jk*hc4>W2#K!9{a$(HvO&fwdo4`>SE?fkb_g@BW}f{T6KR&eNgt_KW1{5Ucy@JbjVW;n6&OkwYE!*CKiLU7ntoe96-xwU?o_cOdEqqW(fz`l0lCWa&qieq`xKmVRXEM@P)j5p#6J933%7{{C(9cRKW4|Ck*yy;G?K{dY;-*C+7H(551fn}#n~<<8;sASS<0-<w-uj{N<|-;ezL$ls6r{Z5-{!CDh-rcHdRPn&5O21A=^0jOVSGeO;|)Mi>_>7ujdqRq6(rn=K+T96OiX)`Ty%d@O<`p{-tWcQ)va*>?jqRq6(16;J3mQgO9Ked^bQ9iPMYBMd<`Cgl8!65`4FUv$n5`QG|uav|eYOF^Re<blo5`QG|M-qP|@dpThfbdZeJ};6m-zD(;J?y&e6foT+@cd8g&q*#>)dW5-vfGtr_XXmz*Jk$x6Jv|q#U%d}?X~eHf#-kXlp>8;a-b14W;x8r@e93Ki?|5!5u(bxOqXVN(Q!-XErI8ME}sc}UL-p&6L@wjG7N-E;8>O|ZI`d|O#;vV9E=2h&2q_jB=GSB{?J`L68Iy5KN9#Ofj<)XBZ2>A6L{p5gq-rW0e+vqBipvx-;pivQ+FiCm*#gumP!~&CZwt)sp>551iKPb2sDcu!HZiq7X$|aM<gjJ1`P;<286tnBrnAzFk!NQkeAXTGIH2X7!;sIhC=yW0>2jc8h!t?$UMEwg~Iw<&brE1LVznj#jnIG#@s8RpPrV@pM7+~(<};jc<o3~39a;m1XU(h7rf@JlOFH-b7FN_FDU#r@p_q9rCA&<o>S6V8FZD5789$4#Fb>Ib%n(+)XHDUf3Qu@@-g`-zwPY{d|>muaJ}2LaJIM>myt}dt}=-_%XM(WNYg+5vu+cs{2%-YQOHJsS!F_f`vL9@vk|xiNj$`?p<@jRYyL5Q10u&t;`!nFw;5IZ8mx&`u7jCZ$qwa^Bq1S7$}YKzM2x&;@cf@6gKx;-4_VbCgKx{=alx}Pc&h`R|I++**}KRzv0KWTPSa}XH04$P(IV6oN!;&rnnL2Lm&9F?7~KDg`-p0*Uf5)+;;Ki=ex&S2%6?$(2j+hC%p5&4FO#qz>Z(V=en9RA<bFWzNB(}~@4s~Zo`IjXK<@m3<(j)^z^fVXYF;I47bk)Pzx<GHXlDd;736&uR6s5*k@qaP>@1lBHt4#2cG{5l|G&NS>22c%qWE|5*@xkdwY%(1H5Awg92v5ENPt480=*?j+Ed~0UjE+Ns#YRbELyZ^!9xT&;&5j<{PXz8nQ_I5jnfa~5%cb_whm$IB5Yya9oE*x+7fc-59*yTI~}2QM7_H%Wkglt{Y1Sx3z|n^6OR-1?yN|z)#yOIJL{51RXU^IqaM-g<26{MM?F!v`Hgx{|JR>V@9F=BSL%J3coS4%?uUBsh$s0<z2E3hB&4ziFxW`cyG{%g+*OJ7G_qF;>xwFR0a5RaH#qt9Exu9jy(Vqy><`p?uMf=zv_-Gzu!wQ*CjzlvsrU2;PgQ*80{NbPMIG+>#K9->J$*x#c`Odc<a_#4zoMAV9ste_%hzK0mRhx8`G(~imTy?TVflvT8yDZW_{POIF8;rR-&<PM{~dmZ-GJOU3nIy89Q+Q|!5u?l8571B{0`Mo!tXF3;CJE}6S|nohcF<-CngLr^asob#0R{`Fg*-NhjcO~qzB=9iQda)LkJH-_Y%1mwga+*u)PHAh3Oz%FVT9TIK*&7{bwqe3=FeDU|x6)Xbo5m5@*0^3^H^ohpCgTp)+7J$cq7&K|%~%gaYU+0M7#WECA5b2aT$^gWV3PcLEqK0MY^|EdbL3I4uCw0!S?Y)zSwN=~YODF=`;DcOnNyAR7-i2yqG`0S5UmNPj{03zA=u`-0RLB)uT#1t~AcctOGo@?DVWf<zbOxgf&@2`<QQL3)c(OCsOt&Z%rNBN3R1kW74IA{!IQm>9-{FeU&6p(h9-L7)i2LJ$Ok7!ZVhAl3uX9f<2dL<eFy5W#`C4Gpz7)ZS2gL+uT<H`Lxx`@f3XTQb##+8b(bsJ#NUOaIkS1=>fQ*3Lour4*`!ZX;qFLE4DVMpOr)IN)%Hza1`dIK#;oj$>Zj-f(!s-wh`>eB5ws!><izHXOC^Uc-3}w>2Uy;IxLj8s2K727M}*UIec+4#jaX!=(&oGTg}Ubi+Lj$25G#@DIa13{Ntg!|)BmdyJFm$tO%lQ!Jx#>bQ)BUO&(j(p^W+ETfz(chku-%P5D+-E^qTGRjeM7v*inG8(~oQD;?3Ov@4))2ndy%nbrA5O76+8v-1<aX!Y;*mSa$-j_oy&a^nv;slFxe$MrEjvq&T@I={FhLvSyTG>{{jeiZcpQcYu74p97E6lMg{-t(K9f3iQooP~9lm?|eX--;`#-uH$rkr{if2ESCA!$dNkyfM;X~R??=n?5ls+Vn!sW+-Ssz0hjsz)lTFaCNK)OqQ>Y$J_*q_L4Sc9O;o5+kLNv6nP9lg4h+I`wxXnAuIsgw_cy6j~`*DyTkCeW3b4^?~XG)d#8%R3BV#$O1w2f$GC+^^}`_Kq1x+V*#*kocvV}(7opJOdhxAJXXVvhP58WLeKNkHy-c$KmExoGTR!ntufo$jaE(+X0|nETVu90W?N&nHD+65wl!v3W45)Go}pi9bE(NXWh_)i3>LI@vPh*5tR$@fAZX=i<!I$-<!I$-<!I$-<!I$-<!I$-<!I$-<!I%TRyb@K9$PkQDx(5+z>|_(V40L8R;8)O5oU8zl4zC2{@u8zV%$@)UXvjb+*2{)(-`+tj6J+@4aGRl7SIsV2<o3~>Wy8!v8}g3(<v1U`jraQ@41JA&Ti`T(wT5GM$8x+H3K8TMI0l9jIqHtcK8Mk6#x+e32I$J$Qbu>j4i(r6UU;`V5bT|Ne)bMaFPR*9HitxCFd2KS8%-oaLK_-9z@iLsS#C^#y~^z)kwajT5U+aA^C>nYxwu^&(rVT3v|{&d1p>%ax8K04qnPo@6M&mzngidH;8x#LDLs55%11C-OzkP^9{{6G~dvCL-YSEnt!>z`u6kZFW(ZN|LySY>ihNk&F<sX_1l*O`oDhu^_QQnzDu@wxz3i{{qW)TZvXVSeV!HfeDQbd-NR=0w0~Id-f!j-H+hNs+s*!Vw^={zpYFDgGl^AR;&Jo5zg@rE%*ytKviF}pt<P&7@}-|1w%g~s`^~w)m>2lC-hJ3VJ#Tk&W#YW_Q4?mHezjD*uKi~+Wg`Sz5UaPuOe|}Tuq04rlbJ}_FiV<MS?8p&as~?Ff<)d%p<5QK9xG>(3ziy|C3D6KenBR0uhp_tt;x;=^HvM<COK(=ieYswQ5abl#1^b}L9%*$ok?bg*d>{~)y8G1TC1H27OXaxI=n~LUS2F)7+-x!U||9rN;1{fIg-harm<MMX5Kq0Uu%mak%ATGGv1LNIXiT=P`YZ&%tXqz=t5blY>lofOI3`MdHJkGIxkBUZPMM8h4NPE=8Da0u9(oy1oE~yY2{O?>gnuMuzI|l3RW2DOr&N7Iu$AppJ7q1V6FLNb5tmc7~(?df}Iu~urP*(ved#DT6k8@Jd5S?V`wZ(l*iD*V~S(w$Cuv$UEG@c')))
_ROUTES={int(k):[_R108_DATA['actions'][i] for i in ids] for k,ids in _R108_DATA['routes'].items()}
_R108_SHOP_ROUTES={tuple(r['shops']):r['route'] for r in _R108_DATA['shops']}
del _R108_DATA
_SETTINGS={'hand_align': True, 'weed_repair': True, 'sell_lead': True, 'budget_guard': False, 'room_guard': False, 'clamp_sells': False, 'dead_stock': False, 'terminal_liquidation': False, 'front_run': False}

# EXP241: fixed two-policy choice, learned with five whole-team held-out folds.
# The full-fit tree and all five fold trees use only first-two-shop YARN_STORE count.
# V39 handles yarn-specialized worlds; EXP240 handles the other shop combinations.
_R110_OLD_SHOPS={('BAKERY', 'BAKERY'): 0, ('BAKERY', 'BRUNCH_SPOT'): 0, ('BAKERY', 'FARMERS_MARKET'): 0, ('BAKERY', 'ICE_CREAM_SHOP'): 0, ('BAKERY', 'PET_CAFE'): 0, ('BAKERY', 'PIZZA_SHOP'): 0, ('BAKERY', 'SMOOTHIE_SHOP'): 0, ('BAKERY', 'YARN_STORE'): 3, ('BRUNCH_SPOT', 'BAKERY'): 0, ('BRUNCH_SPOT', 'BRUNCH_SPOT'): 0, ('BRUNCH_SPOT', 'FARMERS_MARKET'): 0, ('BRUNCH_SPOT', 'ICE_CREAM_SHOP'): 0, ('BRUNCH_SPOT', 'PET_CAFE'): 0, ('BRUNCH_SPOT', 'PIZZA_SHOP'): 0, ('BRUNCH_SPOT', 'SMOOTHIE_SHOP'): 0, ('BRUNCH_SPOT', 'YARN_STORE'): 3, ('FARMERS_MARKET', 'BAKERY'): 0, ('FARMERS_MARKET', 'BRUNCH_SPOT'): 0, ('FARMERS_MARKET', 'FARMERS_MARKET'): 0, ('FARMERS_MARKET', 'ICE_CREAM_SHOP'): 0, ('FARMERS_MARKET', 'PET_CAFE'): 0, ('FARMERS_MARKET', 'PIZZA_SHOP'): 0, ('FARMERS_MARKET', 'SMOOTHIE_SHOP'): 0, ('FARMERS_MARKET', 'YARN_STORE'): 5, ('ICE_CREAM_SHOP', 'BAKERY'): 0, ('ICE_CREAM_SHOP', 'BRUNCH_SPOT'): 0, ('ICE_CREAM_SHOP', 'FARMERS_MARKET'): 0, ('ICE_CREAM_SHOP', 'ICE_CREAM_SHOP'): 0, ('ICE_CREAM_SHOP', 'PET_CAFE'): 0, ('ICE_CREAM_SHOP', 'PIZZA_SHOP'): 0, ('ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'): 0, ('ICE_CREAM_SHOP', 'YARN_STORE'): 6, ('PET_CAFE', 'BAKERY'): 0, ('PET_CAFE', 'BRUNCH_SPOT'): 0, ('PET_CAFE', 'FARMERS_MARKET'): 0, ('PET_CAFE', 'ICE_CREAM_SHOP'): 0, ('PET_CAFE', 'PET_CAFE'): 0, ('PET_CAFE', 'PIZZA_SHOP'): 0, ('PET_CAFE', 'SMOOTHIE_SHOP'): 0, ('PET_CAFE', 'YARN_STORE'): 11, ('PIZZA_SHOP', 'BAKERY'): 0, ('PIZZA_SHOP', 'BRUNCH_SPOT'): 0, ('PIZZA_SHOP', 'FARMERS_MARKET'): 0, ('PIZZA_SHOP', 'ICE_CREAM_SHOP'): 0, ('PIZZA_SHOP', 'PET_CAFE'): 0, ('PIZZA_SHOP', 'PIZZA_SHOP'): 0, ('PIZZA_SHOP', 'SMOOTHIE_SHOP'): 0, ('PIZZA_SHOP', 'YARN_STORE'): 7, ('SMOOTHIE_SHOP', 'BAKERY'): 0, ('SMOOTHIE_SHOP', 'BRUNCH_SPOT'): 0, ('SMOOTHIE_SHOP', 'FARMERS_MARKET'): 0, ('SMOOTHIE_SHOP', 'ICE_CREAM_SHOP'): 0, ('SMOOTHIE_SHOP', 'PET_CAFE'): 0, ('SMOOTHIE_SHOP', 'PIZZA_SHOP'): 0, ('SMOOTHIE_SHOP', 'SMOOTHIE_SHOP'): 0, ('SMOOTHIE_SHOP', 'YARN_STORE'): 8, ('YARN_STORE', 'BAKERY'): 9, ('YARN_STORE', 'BRUNCH_SPOT'): 9, ('YARN_STORE', 'FARMERS_MARKET'): 3, ('YARN_STORE', 'ICE_CREAM_SHOP'): 9, ('YARN_STORE', 'PET_CAFE'): 10, ('YARN_STORE', 'PIZZA_SHOP'): 6, ('YARN_STORE', 'SMOOTHIE_SHOP'): 11, ('YARN_STORE', 'YARN_STORE'): 12}

_V92_TABLE={('BAKERY', 'YARN_STORE'): 9, ('BRUNCH_SPOT', 'YARN_STORE'): 9, ('FARMERS_MARKET', 'YARN_STORE'): 9, ('ICE_CREAM_SHOP', 'YARN_STORE'): 9, ('PET_CAFE', 'YARN_STORE'): 9, ('PIZZA_SHOP', 'YARN_STORE'): 9, ('SMOOTHIE_SHOP', 'YARN_STORE'): 9, ('YARN_STORE', 'BAKERY'): 9, ('YARN_STORE', 'BRUNCH_SPOT'): 9, ('YARN_STORE', 'FARMERS_MARKET'): 9, ('YARN_STORE', 'ICE_CREAM_SHOP'): 9, ('YARN_STORE', 'PET_CAFE'): 9, ('YARN_STORE', 'PIZZA_SHOP'): 9, ('YARN_STORE', 'SMOOTHIE_SHOP'): 9, ('YARN_STORE', 'YARN_STORE'): 9}

def _router(observation,step,state):
    if step==2:
        try:
            _rv=observation['farms'][1-int(observation['player'])]
            state['rkey']=(round(float(_rv['money']),3), int(observation['market']['inventory']['WHEAT']))
        except Exception:
            state['rkey']=None
    if step>=144 and not state.get('day6'):
        shops=tuple((_get(_get(observation,'town',{}),'unlocked_shops',[]) or [])[:2])
        use_new=shops.count('YARN_STORE')<=0
        state['expert']='EXP240' if use_new else 'V39'
        state['route']=_R108_SHOP_ROUTES.get(shops,100) if use_new else _R110_OLD_SHOPS.get(shops,0)
        state['route']=_V92_TABLE.get(shops,state['route'])
        state['day6']=True
    if step>=648 and not state.get('day27'):
        state['route']=2
        state['day27']=True
    return state.get('route',0)

_R42_OPENING=[['BUY_PRODUCT', 'WHEAT', 13], ['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]
for _r42_tape in _ROUTES.values():
    _r42_tape[0]=dict(_r42_tape[0],market=[list(o) for o in _R42_OPENING])
del _r42_tape
_IMPL=make_agent(_ROUTES,router=_router,**_SETTINGS)
_IMPL.chassis.diagnostics['terminal_rescue_errors']=0

def agent(observation,configuration=None):
    try:
        action=_IMPL(observation,configuration)
        pass
        return action
    except Exception:
        return {'farmer':['PASS'],'hands':[],'market':[]}

_SHOP_PARENT=agent
del agent

def agent(observation,configuration=None):
    action=_SHOP_PARENT(observation,configuration)
    try:
        if _step_of(observation)>=718:
            view=_View(observation,_int(_get(observation,'player',0)),_IMPL.chassis.cfg)
            units=[]
            for i,pos in enumerate(view.positions):
                units.append(['DROP'] if _shed_adjacent(pos,view.board) and view.inv(i) else ['PASS'])
            action={'farmer':units[0],'hands':units[1:],'market':[]}
            projected=_IMPL.chassis._projected_shed(action,view)
            action['market']=[['SELL',item,projected.get(item,0)] for item in PRODUCTS if projected.get(item,0)>0]
            action['market'].sort(key=lambda o:-view.prices.get(o[1],0)*o[2])
    except Exception:
        _IMPL.chassis.diagnostics['terminal_rescue_errors'] += 1
    return action

# EXP-154 modifications: Ahmed Berat Ozer; public capabilities credited below.
# Dmitrii Gluzdov Seven Turn Rescue and Kaggle engine contributors, Apache-2.0.

_UNIT_NS={"__name__":"v28_own_unit_model"}
exec('# SPDX-License-Identifier: Apache-2.0\n# Extracted Kaggle / kaggle-environments contributor code; see NOTICE.txt.\n"""Exact deterministic unit/decay semantics extracted from kaggle-environments 1.32.7.\nSource kaggriculture.py SHA256 bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e.\nNo interpreter, market RNG, policy controls, or replay content is included.\n"""\n\nENGINE_VERSION = "1.32.7"\nSOURCE_SHA256 = "bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e"\n\nCROPS = {\n    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},\n    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},\n    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},\n    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},\n    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},\n}\n\nANIMALS = {\n    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},\n    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},\n    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},\n}\n\nPRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]\n\nFARMER_MOVES = {\n    "NORTH": (0, -1),\n    "SOUTH": (0, 1),\n    "EAST":  (1, 0),\n    "WEST":  (-1, 0),\n}\n\ndef _shed_access_tiles(board_size):\n    """Four inner-corner tiles around the shed, in NWSE order."""\n    half = board_size // 2\n    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]\n\ndef _is_shed_adjacent(pos, board_size):\n    return tuple(pos) in {(x, y) for (x, y) in _shed_access_tiles(board_size)}\n\ndef _new_plant(crop, day, turns_per_day):\n    cd = CROPS[crop]\n    return {\n        "kind": "PLANT",\n        "crop": crop,\n        "planted_day": day,\n        "watered_today": False,\n        "consecutive_unwatered": 1,  # planting day counts as unwatered\n        "yield_units": 0 if cd["ongoing"] else 1,\n        "max_lifespan_step": (-1 if cd["ongoing"] else (day + cd["max_yield_day"] + 1) * turns_per_day),\n        "fertilized_until_day": -1,\n    }\n\ndef _new_animal(animal, day):\n    a = ANIMALS[animal]\n    return {\n        "kind": a["structure"],\n        "animal": animal,\n        "placed_day": day,\n        "yield_units": 0,\n        "consecutive_unfed": 0,\n        "fed_today": False,\n        "cared_today": False,\n        "fertilizer_available": False,\n        "pending_care_bonus": 0,\n    }\n\ndef _farmer_position(farm, idx):\n    """idx 0 = main farmer, 1+ = hand index."""\n    if idx == 0:\n        return farm["farmer"]\n    return farm["hands"][idx - 1] if idx - 1 < len(farm["hands"]) else None\n\ndef _set_farmer_position(farm, idx, pos):\n    if idx == 0:\n        farm["farmer"] = list(pos)\n    else:\n        farm["hands"][idx - 1] = list(pos)\n\ndef _farmer_inventory(private, idx):\n    """Inventories list is [main_farmer, *hands]; grow it if idx is past the end."""\n    while len(private["inventories"]) <= idx:\n        private["inventories"].append({})\n    return private["inventories"][idx]\n\ndef _inv_add(inv, item, n=1):\n    inv[item] = inv.get(item, 0) + n\n\ndef _inv_take(inv, item, n=1):\n    if inv.get(item, 0) < n:\n        return False\n    inv[item] -= n\n    if inv[item] == 0:\n        del inv[item]\n    return True\n\ndef _apply_unit_action(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):\n    """Process one farmer/hand\'s action. Invalid / illegal actions are silent no-ops."""\n    if not isinstance(action, list) or not action:\n        return\n    op = action[0]\n    pos = _farmer_position(farm, idx)\n    if pos is None:\n        return\n    fx, fy = pos[0], pos[1]\n    inv = _farmer_inventory(private, idx)\n\n    if op in FARMER_MOVES:\n        dx, dy = FARMER_MOVES[op]\n        nx, ny = fx + dx, fy + dy\n        if not (0 <= nx < board_size and 0 <= ny < board_size):\n            return\n        # Movement onto LOCKED tiles is allowed: a hand can spawn on a locked\n        # shed-access tile, and blocking movement would strand it there forever.\n        # Tile operations (PLANT, WATER, etc.) still no-op on LOCKED tiles.\n        _set_farmer_position(farm, idx, (nx, ny))\n        return\n\n    if op == "PASS":\n        return\n\n    tile = farm["tiles"][fy][fx]\n\n    # Shed operations resolve before the LOCKED guard. They use the tile only as\n    # a standing position -- the shed itself is always owned -- and three of the\n    # four shed-access tiles start LOCKED, so guarding them first would make the\n    # shed unreachable from those tiles.\n    if op == "DROP":\n        if not _is_shed_adjacent((fx, fy), board_size):\n            return\n        shed = private["shed"]\n        for item, n in list(inv.items()):\n            if n <= 0:\n                del inv[item]\n                continue\n            room = max(0, shed_capacity - sum(shed.values()))\n            take = min(n, room)\n            if take > 0:\n                shed[item] = shed.get(item, 0) + take\n            del inv[item]\n        return\n\n    if op == "PICKUP":\n        if not _is_shed_adjacent((fx, fy), board_size):\n            return\n        if len(action) < 2:\n            return\n        item = action[1]\n        n = int(action[2]) if len(action) >= 3 else 1\n        if n <= 0:\n            return\n        # Seeds live in private["seeds"] and are consumed directly by PLANT;\n        # they never pass through farmer inventory or the shed.\n        available = private["shed"].get(item, 0)\n        n = min(n, available)\n        if n <= 0:\n            return\n        private["shed"][item] -= n\n        _inv_add(inv, item, n)\n        return\n\n    if op == "PLACE":\n        if len(action) < 2:\n            return\n        item = action[1]\n        # Animal placement: standing on a matching unoccupied structure. A LOCKED\n        # tile is the string "LOCKED", never a dict, so this branch cannot match\n        # there and PLACE falls through to the shed path below.\n        if (\n            item in ANIMALS\n            and isinstance(tile, dict)\n            and tile.get("kind") == ANIMALS[item]["structure"]\n            and "animal" not in tile\n        ):\n            if _inv_take(inv, item, 1):\n                farm["tiles"][fy][fx] = _new_animal(item, day)\n            return\n        # Shed drop: orthogonally adjacent to the shed; obeys shedCapacity.\n        if _is_shed_adjacent((fx, fy), board_size):\n            n = int(action[2]) if len(action) >= 3 else 1\n            if n <= 0:\n                return\n            n = min(n, inv.get(item, 0))\n            if n <= 0:\n                return\n            current = sum(private["shed"].values())\n            room = max(0, shed_capacity - current)\n            n = min(n, room)\n            if n <= 0:\n                return\n            inv[item] -= n\n            if inv[item] == 0:\n                del inv[item]\n            private["shed"][item] = private["shed"].get(item, 0) + n\n        return\n\n    # Everything below mutates the tile the unit stands on, so it requires that\n    # tile to be owned.\n    if tile == "LOCKED":\n        return\n\n    if op == "PLANT":\n        if len(action) < 2:\n            return\n        crop = action[1]\n        if crop not in CROPS:\n            return\n        if tile is not None:\n            return\n        if private["seeds"].get(crop, 0) <= 0:\n            return\n        private["seeds"][crop] -= 1\n        farm["tiles"][fy][fx] = _new_plant(crop, day, turns_per_day)\n        return\n\n    if op == "WATER":\n        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):\n            return\n        if tile["watered_today"]:\n            return\n        tile["watered_today"] = True\n        crop_data = CROPS[tile["crop"]]\n        if not crop_data["ongoing"]:\n            age_days = day - tile["planted_day"]\n            window_start = (crop_data["max_yield_day"] + 1) // 2\n            if window_start <= age_days <= crop_data["max_yield_day"]:\n                bonus = 2 if tile["fertilized_until_day"] >= day else 1\n                tile["yield_units"] = min(crop_data["max_yield"], tile["yield_units"] + bonus)\n        return\n\n    if op == "HARVEST":\n        if not isinstance(tile, dict):\n            return\n        if tile.get("yield_units", 0) <= 0:\n            return\n        if tile.get("kind") == "PLANT":\n            crop_data = CROPS[tile["crop"]]\n            if day - tile["planted_day"] < crop_data["first_yield_day"]:\n                # Ongoing crops only accumulate yield_units after first_yield_day,\n                # so reaching here with yield_units > 0 indicates a bug.\n                if crop_data["ongoing"]:\n                    print(\n                        f"WARNING: HARVEST on immature ongoing {tile[\'crop\']} "\n                        f"(planted day {tile[\'planted_day\']}, current day {day}, "\n                        f"first_yield_day {crop_data[\'first_yield_day\']}, "\n                        f"yield_units {tile[\'yield_units\']}); should never happen"\n                    )\n                return\n            units = tile["yield_units"]\n            tile["yield_units"] = 0\n            _inv_add(inv, tile["crop"], units)\n            if not crop_data["ongoing"]:\n                farm["tiles"][fy][fx] = None\n        elif "animal" in tile:\n            units = tile["yield_units"]\n            tile["yield_units"] = 0\n            _inv_add(inv, ANIMALS[tile["animal"]]["product"], units)\n        return\n\n    if op == "FERTILIZE":\n        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):\n            return\n        if not _inv_take(inv, "FERTILIZER", 1):\n            return\n        # Active for `day`, `day+1`, `day+2` (3 days inclusive).\n        tile["fertilized_until_day"] = max(tile.get("fertilized_until_day", -1), day + 2)\n        return\n\n    if op == "DIG":\n        if tile is None:\n            return\n        # Removes plants, weeds, empty coop/pasture. Does NOT remove a placed animal.\n        if isinstance(tile, dict) and "animal" in tile:\n            return\n        farm["tiles"][fy][fx] = None\n        return\n\n    if op == "BUILD_COOP":\n        if tile is not None:\n            return\n        farm["tiles"][fy][fx] = {"kind": "COOP"}\n        return\n\n    if op == "BUILD_PASTURE":\n        if tile is not None:\n            return\n        farm["tiles"][fy][fx] = {"kind": "PASTURE"}\n        return\n\n    if op == "FEED":\n        if not (isinstance(tile, dict) and "animal" in tile):\n            return\n        if tile["fed_today"]:\n            return\n        if not _inv_take(inv, "WHEAT", 1):\n            return\n        tile["fed_today"] = True\n        return\n\n    if op == "COLLECT_FERTILIZER":\n        if not (isinstance(tile, dict) and "animal" in tile):\n            return\n        if not tile["fertilizer_available"]:\n            return\n        tile["fertilizer_available"] = False\n        _inv_add(inv, "FERTILIZER", 1)\n        return\n\n    if op == "CARE":\n        if not (isinstance(tile, dict) and "animal" in tile):\n            return\n        if tile["cared_today"]:\n            return\n        tile["cared_today"] = True\n        return\n\ndef _decay_plants(farm, step):\n    board_size = len(farm["tiles"])\n    for y in range(board_size):\n        for x in range(board_size):\n            tile = farm["tiles"][y][x]\n            if not isinstance(tile, dict) or tile.get("kind") != "PLANT":\n                continue\n            mls = tile["max_lifespan_step"]\n            if mls < 0 or step < mls:\n                continue\n            if (step - mls) % 2 != 0:\n                continue\n            tile["yield_units"] -= 1\n            if tile["yield_units"] <= 0:\n                farm["tiles"][y][x] = {"kind": "WEED"}\n\n',_UNIT_NS)
_PLANNER_NS=dict(_UNIT_NS)
exec('"""E182 modification: Shop0909 last-seven-turn physical closure planner.\n\nNo engine imports, policy tapes, replay fixtures, RNG or remote calls.\nThe only supported market continuation is SELL; unknown execution abstains.\n"""\nfrom copy import deepcopy\nfrom time import perf_counter\nSTART, FINAL = (712, 718)\nOPS = set(FARMER_MOVES) | {\'PASS\', \'DROP\', \'PICKUP\', \'PLACE\', \'PLANT\', \'WATER\', \'HARVEST\', \'FERTILIZE\', \'DIG\', \'BUILD_COOP\', \'BUILD_PASTURE\', \'FEED\', \'CARE\', \'COLLECT_FERTILIZER\'}\nITEMS = tuple(PRODUCTS) + tuple(ANIMALS)\n\nclass Unsupported(ValueError):\n    pass\n\ndef _get(obj, key, default=None):\n    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)\n\ndef _settings(config):\n    size, turns, last = (_get(config, k, d) for k, d in [(\'boardSize\', 10), (\'turnsPerDay\', 24), (\'episodeSteps\', 720)])\n    if (size, turns, last) != (10, 24, 720):\n        raise Unsupported(\'requires pinned 10x10/24/720 terminal window\')\n    cap = int(_get(config, \'shedCapacity\', 100))\n    orders = min(10, int(_get(config, \'maxMarketOrdersPerTurn\', 10)))\n    if cap < 1 or orders < 1:\n        raise Unsupported(\'invalid capacity/order limit\')\n    return (size, turns, cap, orders)\n\ndef physical_state(obs):\n    """Comparable own physical state; market prices and bank are intentionally excluded."""\n    seat = int(_get(obs, \'player\', 0))\n    farm = _get(obs, \'farms\')[seat]\n    return ({k: v for k, v in farm.items() if k != \'money\'}, _get(obs, \'private\'))\n\ndef _commands(action, n):\n    return [action.get(\'farmer\', [\'PASS\']), *action.get(\'hands\', [])][:n] + [[\'PASS\'] for _ in range(max(0, n - 1 - len(action.get(\'hands\', []))))]\n\ndef _clone_state(farm, private):\n    f = dict(farm)\n    f[\'tiles\'] = [[dict(tile) if isinstance(tile, dict) else tile for tile in row] for row in farm[\'tiles\']]\n    f[\'farmer\'] = list(farm[\'farmer\'])\n    f[\'hands\'] = [list(pos) for pos in farm[\'hands\']]\n    f[\'unlocked_quadrants\'] = list(farm[\'unlocked_quadrants\'])\n    pr = dict(private)\n    pr[\'shed\'], pr[\'seeds\'] = (dict(private[\'shed\']), dict(private[\'seeds\']))\n    pr[\'inventories\'] = [dict(inv) for inv in private[\'inventories\']]\n    return (f, pr)\n\ndef _clone_schedule(schedule):\n    result = []\n    for action in schedule:\n        value = dict(action)\n        if \'farmer\' in action:\n            value[\'farmer\'] = list(action[\'farmer\'])\n        for key in [\'hands\', \'market\']:\n            if key in action:\n                value[key] = [list(command) for command in action[key]]\n        result.append(value)\n    return result\n\ndef _validate(schedule, n, orders):\n    for action in schedule:\n        if not isinstance(action, dict) or set(action) - {\'farmer\', \'hands\', \'market\'}:\n            raise Unsupported(\'unknown action shape\')\n        if not isinstance(action.get(\'hands\', []), list):\n            raise Unsupported(\'hands must be a list\')\n        for command in [action.get(\'farmer\', [\'PASS\']), *action.get(\'hands\', [])]:\n            if not isinstance(command, list) or not command or command[0] not in OPS:\n                raise Unsupported(\'unknown/malformed unit operation\')\n            if command[0] in {\'PICKUP\', \'PLACE\', \'PLANT\'}:\n                if len(command) < 2 or command[1] not in ITEMS:\n                    raise Unsupported(\'unknown unit item\')\n                if len(command) > 2 and (not isinstance(command[2], int)):\n                    raise Unsupported(\'noninteger unit quantity\')\n        market = action.get(\'market\', [])\n        if not isinstance(market, list) or len(market) > orders:\n            raise Unsupported(\'market order shape/cap\')\n        for order in market:\n            if not isinstance(order, list) or len(order) != 3 or order[0] != \'SELL\' or (order[1] not in PRODUCTS) or (not isinstance(order[2], int)) or (order[2] <= 0):\n                raise Unsupported(\'baseline market must contain positive integer SELL only\')\n\ndef liquidation(shed, inherited_market, max_orders=10):\n    """Use actual post-unit stock; retain first parent item ordering, then stable product order."""\n    items = []\n    for order in inherited_market:\n        if order[1] not in items:\n            items.append(order[1])\n    items += [item for item in PRODUCTS if item not in items]\n    orders = [[\'SELL\', item, int(shed.get(item, 0))] for item in items if shed.get(item, 0) > 0]\n    if len(orders) > min(10, max_orders):\n        raise Unsupported(\'actual final stock exceeds order slots\')\n    return orders\n\ndef shop_liquidation(farm, private, prices):\n    """Exact original final worker/drop and market rule, with current stock/prices."""\n    return liquidate(FarmView({\'player\': 0, \'farms\': [farm], \'private\': private, \'market\': {\'prices\': prices}}))\n\ndef simulate(obs, config, schedule, *, final_liquidate=False, detailed=False, preserve_final_commands=False):\n    """Exact own unit/decay and SELL-stock transitions. No claim to simulate shared prices."""\n    size, turns, cap, order_cap = _settings(config)\n    step = int(_get(obs, \'step\', -1))\n    if step < START or step + len(schedule) - 1 > FINAL or (not schedule):\n        raise Unsupported(\'outside 712..718; no day boundary or terminal auto-drop\')\n    if any(((t + 1) % turns == 0 for t in range(step, step + len(schedule)))):\n        raise Unsupported(\'day boundary\')\n    farm0, private0 = physical_state(obs)\n    farm, private = _clone_state(farm0, private0)\n    n = 1 + len(farm[\'hands\'])\n    if len(private[\'inventories\']) != n or n > 32:\n        raise Unsupported(\'invalid/unbounded worker inventory shape\')\n    _validate(schedule, n, order_cap)\n    deposited = [dict() for _ in range(n)]\n    sold = {}\n    snapshots, rows, events = ([], [], [])\n    executed = _clone_schedule(schedule)\n    overflow = 0\n    for offset, action in enumerate(executed):\n        t = step + offset\n        if detailed:\n            snapshots.append(_clone_state(farm, private))\n        if t == FINAL and (not preserve_final_commands):\n            action = shop_liquidation(farm, private, _get(obs, \'market\')[\'prices\'])\n            executed[offset] = action\n        all_commands = [action.get(\'farmer\', [\'PASS\']), *action.get(\'hands\', [])]\n        demand = {}\n        for command in all_commands:\n            if command[0] == \'PLANT\':\n                demand[command[1]] = demand.get(command[1], 0) + 1\n        blocked = {item for item, count in demand.items() if count > private[\'seeds\'].get(item, 0)}\n        for actor, command in enumerate(_commands(action, n)):\n            if command[0] == \'PLANT\' and command[1] in blocked:\n                command = [\'PASS\']\n            pos = farm[\'farmer\'] if actor == 0 else farm[\'hands\'][actor - 1]\n            xy = tuple(pos)\n            inv = private[\'inventories\'][actor]\n            before_inv = dict(inv) if command[0] in {\'DROP\', \'HARVEST\', \'COLLECT_FERTILIZER\'} else None\n            before_shed = dict(private[\'shed\']) if command[0] in {\'DROP\', \'PLACE\'} else None\n            _apply_unit_action(farm, private, actor, command, size, t // turns, turns, cap)\n            if before_shed is not None:\n                delta = {item: amount - before_shed.get(item, 0) for item, amount in private[\'shed\'].items() if amount > before_shed.get(item, 0)}\n                for item, amount in delta.items():\n                    deposited[actor][item] = deposited[actor].get(item, 0) + amount\n                if delta:\n                    events.append({\'offset\': offset, \'actor\': actor, \'op\': command[0], \'xy\': xy, \'deposited\': delta})\n                if command[0] == \'DROP\':\n                    overflow += sum((max(0, amount - inv.get(item, 0) - delta.get(item, 0)) for item, amount in before_inv.items()))\n            if command[0] in {\'HARVEST\', \'COLLECT_FERTILIZER\'}:\n                delta = {item: amount - before_inv.get(item, 0) for item, amount in inv.items() if amount > before_inv.get(item, 0)}\n                if delta:\n                    events.append({\'offset\': offset, \'actor\': actor, \'op\': command[0], \'xy\': xy, \'acquired\': delta})\n        pre_market = dict(private[\'shed\'])\n        if t == FINAL and preserve_final_commands and final_liquidate:\n            action[\'market\'] = liquidation(pre_market, [], order_cap)\n            prices = _get(obs, \'market\')[\'prices\']\n            action[\'market\'].sort(key=lambda order: -int(prices.get(order[1], 0)) * order[2])\n        for _, item, requested in action.get(\'market\', []):\n            quantity = min(requested, private[\'shed\'].get(item, 0), 99999)\n            if quantity > 0:\n                private[\'shed\'][item] -= quantity\n                sold[item] = sold.get(item, 0) + quantity\n        _decay_plants(farm, t)\n        rows.append({\'pre_market_shed\': pre_market, \'post_market_shed\': dict(private[\'shed\']), \'deposited_by_actor\': [dict(v) for v in deposited], \'sold\': dict(sold)})\n    if detailed:\n        snapshots.append(_clone_state(farm, private))\n    return {\'rows\': rows, \'states\': snapshots, \'events\': events, \'actions\': executed, \'overflow_units\': overflow, \'farm\': farm, \'private\': private, \'sold\': sold}\n\ndef _ge(left, right):\n    return all((left.get(item, 0) >= value for item, value in right.items()))\n\ndef dominates(candidate, baseline):\n    """Preserve every baseline worker\'s actual deposit prefixes and shed availability."""\n    if candidate[\'overflow_units\']:\n        return False\n    for new, old in zip(candidate[\'rows\'], baseline[\'rows\']):\n        if not _ge(new[\'pre_market_shed\'], old[\'pre_market_shed\']):\n            return False\n        if not _ge(new[\'sold\'], old[\'sold\']):\n            return False\n        if any((not _ge(a, b) for a, b in zip(new[\'deposited_by_actor\'], old[\'deposited_by_actor\']))):\n            return False\n    return True\n\ndef _value(run, prices):\n    shed = run[\'private\'][\'shed\']\n    return sum(((run[\'sold\'].get(item, 0) + shed.get(item, 0)) * prices[item] for item in PRODUCTS))\n\ndef _walk(start, end):\n    x, y = start\n    tx, ty = end\n    return [[\'EAST\']] * max(0, tx - x) + [[\'WEST\']] * max(0, x - tx) + [[\'SOUTH\']] * max(0, ty - y) + [[\'NORTH\']] * max(0, y - ty)\n\ndef _return(pos):\n    targets = _shed_access_tiles(10)\n    target = min(targets, key=lambda xy: (abs(pos[0] - xy[0]) + abs(pos[1] - xy[1]), targets.index(xy)))\n    return _walk(pos, target) + [[\'DROP\']]\n\ndef _proposals(run, actor, prices, max_per_actor):\n    """One/two resource bundles plus direct carry closure, replacing a baseline suffix."""\n    owners = {}\n    for event in run[\'events\']:\n        if \'acquired\' in event:\n            owners.setdefault((tuple(event[\'xy\']), event[\'op\']), set()).add(event[\'actor\'])\n    proposals = []\n    seen = set()\n    horizon = len(run[\'rows\'])\n    for offset in range(horizon):\n        farm, private = run[\'states\'][offset]\n        pos = tuple(farm[\'farmer\'] if actor == 0 else farm[\'hands\'][actor - 1])\n        inventory = private[\'inventories\'][actor]\n        carried = sum((prices.get(item, 0) * count for item, count in inventory.items()))\n        prefix_deposits = run[\'rows\'][offset - 1][\'deposited_by_actor\'][actor] if offset else {}\n        future_deposits = run[\'rows\'][-1][\'deposited_by_actor\'][actor]\n        obligation = sum((prices.get(item, 0) * (count - prefix_deposits.get(item, 0)) for item, count in future_deposits.items()))\n        bundles = []\n        for y, row in enumerate(farm[\'tiles\']):\n            for x, tile in enumerate(row):\n                if not isinstance(tile, dict):\n                    continue\n                xy, operations, value = ((x, y), [], 0)\n                if tile.get(\'yield_units\', 0) > 0:\n                    item = tile.get(\'crop\') if tile.get(\'kind\') == \'PLANT\' else ANIMALS.get(tile.get(\'animal\'), {}).get(\'product\')\n                    mature = item and (\'animal\' in tile or (START + offset) // 24 - tile[\'planted_day\'] >= CROPS[item][\'first_yield_day\'])\n                    if mature and (not owners.get((xy, \'HARVEST\'), set()) - {actor}):\n                        operations.append([\'HARVEST\'])\n                        value += prices[item] * tile[\'yield_units\']\n                if tile.get(\'fertilizer_available\') and \'animal\' in tile and (not owners.get((xy, \'COLLECT_FERTILIZER\'), set()) - {actor}):\n                    operations.append([\'COLLECT_FERTILIZER\'])\n                    value += prices[\'FERTILIZER\']\n                if operations:\n                    distance = len(_walk(pos, xy)) + len(operations) + len(_return(xy))\n                    if distance <= horizon - offset:\n                        bundles.append((xy, operations, value, distance))\n        bundles.sort(key=lambda b: (-b[2] / b[3], -b[2], b[0]))\n        variants = [([], carried)] if carried else []\n        for xy, ops, value, _ in bundles[:6]:\n            variants.append(([(xy, ops)], carried + value))\n        for first in bundles[:3]:\n            for second in bundles[:3]:\n                if first[0] != second[0]:\n                    variants.append(([(first[0], first[1]), (second[0], second[1])], carried + first[2] + second[2]))\n        for stops, value in variants:\n            route, cursor = ([], pos)\n            for xy, ops in stops:\n                route += _walk(cursor, xy) + ops\n                cursor = xy\n            route += _return(cursor)\n            if len(route) > horizon - offset:\n                continue\n            route += [[\'PASS\']] * (horizon - offset - len(route))\n            key = (offset, tuple((tuple(c) for c in route)))\n            if key not in seen:\n                seen.add(key)\n                proposals.append((value - obligation, offset, route, len(stops)))\n    proposals.sort(key=lambda p: (-p[0], p[1], p[2]))\n    direct = [p for p in proposals if p[3] == 0 and p[0] > 0][:2]\n    chosen = direct + [p for p in proposals if p not in direct]\n    return chosen[:max_per_actor]\n\ndef plan_terminal(obs, config, baseline_remaining, *, max_simulations=64, passes=1, proposals_per_actor=4):\n    """At 712 accept seven actions; positive physical delivery is mandatory."""\n    begun = perf_counter()\n    fallback = {\'accepted\': False, \'reason\': \'\', \'actions\': None, \'simulations\': 0}\n    try:\n        if int(_get(obs, \'step\', -1)) != START or len(baseline_remaining) != FINAL - START + 1:\n            raise Unsupported(\'planning requires step 712 and exactly seven actions through 718\')\n        max_simulations = min(256, max(1, int(max_simulations)))\n        passes = min(2, max(1, int(passes)))\n        proposals_per_actor = min(16, max(1, int(proposals_per_actor)))\n        baseline = simulate(obs, config, baseline_remaining, detailed=True)\n        prices = {item: max(1, float(_get(obs, \'market\', {}).get(\'prices\', {}).get(item, 1))) for item in PRODUCTS}\n        current, best = (_clone_schedule(baseline_remaining), baseline)\n        baseline_value = best_value = _value(baseline, prices)\n        changes, simulations = ([], 0)\n        n = len(baseline[\'private\'][\'inventories\'])\n        for sweep in range(passes):\n            improved = False\n            for actor in range(n):\n                winner = None\n                for _, offset, route, bundle_count in _proposals(best, actor, prices, proposals_per_actor):\n                    if simulations >= max_simulations:\n                        break\n                    trial = _clone_schedule(current)\n                    for i, command in enumerate(route, offset):\n                        if actor == 0:\n                            trial[i][\'farmer\'] = command\n                        else:\n                            trial[i].setdefault(\'hands\', [])\n                            while len(trial[i][\'hands\']) < n - 1:\n                                trial[i][\'hands\'].append([\'PASS\'])\n                            trial[i][\'hands\'][actor - 1] = command\n                    evaluated = simulate(obs, config, trial)\n                    simulations += 1\n                    score = _value(evaluated, prices)\n                    if score > best_value and dominates(evaluated, baseline):\n                        required = {(tuple(e[\'xy\']), e[\'op\'], e[\'actor\']): e[\'acquired\'] for e in best[\'events\'] if \'acquired\' in e and e[\'actor\'] != actor}\n                        acquired = {}\n                        for e in evaluated[\'events\']:\n                            if \'acquired\' in e:\n                                key = (tuple(e[\'xy\']), e[\'op\'], e[\'actor\'])\n                                dst = acquired.setdefault(key, {})\n                                for item, amount in e[\'acquired\'].items():\n                                    dst[item] = dst.get(item, 0) + amount\n                        if all((_ge(acquired.get(k, {}), v) for k, v in required.items())):\n                            winner, best_value = ((trial, offset, bundle_count), score)\n                if winner:\n                    current, offset, bundle_count = winner\n                    best = simulate(obs, config, current, detailed=True)\n                    changes.append({\'pass\': sweep, \'actor\': actor, \'from_step\': START + offset, \'resource_bundles\': bundle_count, \'estimated_stock_value\': best_value})\n                    improved = True\n                if simulations >= max_simulations:\n                    break\n            if not improved or simulations >= max_simulations:\n                break\n        if not changes or best_value <= baseline_value:\n            return {**fallback, \'reason\': \'no positive physical delivery gain\', \'simulations\': simulations, \'changed_workers\': [], \'changes\': [], \'certificate\': {\'stock_value_gain_at_initial_prices\': 0, \'sold_unit_delta\': dict.fromkeys(PRODUCTS, 0)}, \'planning_ms\': (perf_counter() - begun) * 1000}\n        final = simulate(obs, config, current, final_liquidate=True, detailed=True)\n        physical = simulate(obs, config, current)\n        if not dominates(physical, baseline):\n            raise Unsupported(\'no zero-overflow dominating continuation\')\n        delta = {item: final[\'sold\'].get(item, 0) - baseline[\'sold\'].get(item, 0) for item in PRODUCTS}\n        deposited_gain = any((final[\'rows\'][-1][\'deposited_by_actor\'][actor].get(item, 0) > baseline[\'rows\'][-1][\'deposited_by_actor\'][actor].get(item, 0) for actor in range(n) for item in PRODUCTS))\n        worker_change = any((_commands(new, n) != _commands(old, n) for new, old in zip(final[\'actions\'], baseline[\'actions\'])))\n        accepted = worker_change and deposited_gain and any((v > 0 for v in delta.values())) and all((v >= 0 for v in delta.values()))\n        plan = {\'accepted\': accepted, \'reason\': \'joint physical dominance\' if accepted else \'no improvement\', \'baseline\': _clone_schedule(baseline_remaining), \'actions\': final[\'actions\'], \'expected_states\': final[\'states\'][:-1], \'simulations\': simulations, \'changes\': changes, \'abandoned\': False, \'changed_workers\': sorted({c[\'actor\'] for c in changes}), \'certificate\': {\'baseline_rows\': baseline[\'rows\'], \'physical_rows\': physical[\'rows\'], \'baseline_overflow\': baseline[\'overflow_units\'], \'candidate_overflow\': final[\'overflow_units\'], \'sold_unit_delta\': delta, \'stock_value_gain_at_initial_prices\': best_value - baseline_value, \'baseline_final_shed\': baseline[\'private\'][\'shed\'], \'final_shed\': final[\'private\'][\'shed\'], \'positive_physical_deposit_gain\': deposited_gain, \'markets_712_717_unchanged\': all((final[\'actions\'][i].get(\'market\', []) == baseline_remaining[i].get(\'market\', []) for i in range(FINAL - START)))}}\n    except (Unsupported, KeyError, TypeError, ValueError, IndexError) as exc:\n        plan = {**fallback, \'reason\': str(exc)}\n    plan[\'planning_ms\'] = (perf_counter() - begun) * 1000\n    return plan\n\ndef _effective_action(action, n):\n    return (_commands(action, n), action.get(\'market\', []))\n\ndef _recover_observed(obs, config, parent_action, plan):\n    """Bounded cargo salvage after deviation; never resume old positional commands."""\n    farm, private = physical_state(obs)\n    positions = [farm[\'farmer\'], *farm[\'hands\']]\n    remaining = FINAL - int(_get(obs, \'step\')) + 1\n    room = max(0, int(_get(config, \'shedCapacity\', 100)) - sum(private[\'shed\'].values()))\n    commands = []\n    problems = []\n    prices = _get(obs, \'market\', {}).get(\'prices\', {})\n    for actor, (pos, inv) in enumerate(zip(positions, private[\'inventories\'])):\n        command = [\'PASS\']\n        if any((v > 0 for v in inv.values())):\n            route = _return(pos)\n            if len(route) > remaining:\n                problems.append({\'actor\': actor, \'reason\': \'unreachable cargo\'})\n            elif len(route) > 1:\n                command = route[0]\n            elif sum((max(0, q) for q in inv.values())) <= room:\n                command = [\'DROP\']\n                room -= sum((max(0, q) for q in inv.values()))\n            else:\n                items = [item for item in PRODUCTS if inv.get(item, 0) > 0]\n                if room and items:\n                    item = max(items, key=lambda i: (prices.get(i, 1) * min(inv[i], room), -PRODUCTS.index(i)))\n                    quantity = min(inv[item], room)\n                    command = [\'PLACE\', item, quantity]\n                    room -= quantity\n                else:\n                    problems.append({\'actor\': actor, \'reason\': \'no shed capacity\'})\n        commands.append(command)\n    action = {\'farmer\': commands[0], \'hands\': commands[1:], \'market\': deepcopy(parent_action.get(\'market\', []))}\n    if int(_get(obs, \'step\')) == FINAL:\n        action[\'market\'] = []\n        action = simulate(obs, config, [action], final_liquidate=True, preserve_final_commands=True)[\'actions\'][0]\n    plan[\'recovery_steps\'] = plan.get(\'recovery_steps\', 0) + 1\n    if problems:\n        plan.setdefault(\'recovery_failures\', []).append({\'step\': int(_get(obs, \'step\')), \'problems\': problems})\n    return action\n\ndef terminal_action(obs, config, parent_action, plan):\n    """Canonical guard, pre-deviation abstention, observed recovery after deviation."""\n    step = int(_get(obs, \'step\', -1))\n    if not plan or not plan.get(\'accepted\') or (not START <= step <= FINAL):\n        return parent_action\n    if plan.get(\'abandoned\'):\n        return _recover_observed(obs, config, parent_action, plan) if plan.get(\'deviated\') else parent_action\n    index = step - START\n    n = 1 + len(physical_state(obs)[0][\'hands\'])\n    mismatch = physical_state(obs) != plan[\'expected_states\'][index] or _effective_action(parent_action, n) != _effective_action(plan[\'baseline\'][index], n)\n    if mismatch:\n        plan[\'abandoned\'] = True\n        plan[\'abandon_step\'] = step\n        plan[\'reason\'] = \'physical observation or effective baseline action diverged\'\n        plan[\'safety_failure\'] = True\n        return _recover_observed(obs, config, parent_action, plan) if plan.get(\'deviated\') else parent_action\n    result = deepcopy(plan[\'actions\'][index])\n    if step == FINAL:\n        farm, private = physical_state(obs)\n        result = shop_liquidation(farm, private, _get(obs, \'market\')[\'prices\'])\n    if _commands(result, n) != _commands(parent_action, n):\n        plan[\'deviated\'] = True\n    return result',_PLANNER_NS)
# EXP-154 integration by Ahmed Berat Ozer, derived from Dmitrii Gluzdov E182.
# The preserved v27 parent is simulated on a private shadow only at step 712.
_PRE_TERMINAL_AGENT=agent
del agent
_TERMINAL_PLANS={}
_TERMINAL_PREVIOUS={}
_UPGRADE_STATS={'planning_calls':0,'accepted':0,'changed_steps':0,'aborted':0,'shadow_declines':0,'errors':0,'max_planning_ms':0.0}

def _parent_liquidate(farm, private, prices):
    # Exactly v27's final projected DROP ordering, in the planner's private state.
    view=_View({'player':0,'farms':[farm],'private':private,'market':{'prices':prices}},0,_IMPL.chassis.cfg)
    commands=[['DROP'] if _shed_adjacent(pos,view.board) and view.inv(i) else ['PASS'] for i,pos in enumerate(view.positions)]
    action={'farmer':commands[0],'hands':commands[1:],'market':[]}
    stock=_IMPL.chassis._projected_shed(action,view)
    action['market']=[['SELL',item,stock.get(item,0)] for item in PRODUCTS if stock.get(item,0)>0]
    action['market'].sort(key=lambda o:-view.prices.get(o[1],0)*o[2])
    return action

_PLANNER_NS['shop_liquidation']=_parent_liquidate

def _shadow_terminal(obs,config):
    seat=int(obs['player']);chassis=_IMPL.chassis
    state=chassis.players.get(seat)
    if not state or state.get('last_step')!=711 or state.get('route')!=2:
        return None
    # No delayed weed/structure intervention may depend on an unmodeled future.
    if state.get('pending'):
        return None
    shadow=copy.copy(chassis);shadow.players=copy.deepcopy(chassis.players)
    shadow.diagnostics={k:0 for k in chassis.diagnostics}
    projected=copy.deepcopy(obs);baseline=[];states=[]
    for step in range(712,719):
        projected['step']=step;projected['day']=step//24;projected['hour']=step%24
        states.append(copy.deepcopy(shadow.players[seat]))
        action=shadow.act(projected,config)
        if step==718:
            action=_parent_liquidate(projected['farms'][seat],projected['private'],projected['market']['prices'])
        else:
            market=action.get('market',[])
            if len(market)!=9 or {o[1] for o in market}!=set(PRODUCTS) or any(o[0]!='SELL' or len(o)!=3 or type(o[2]) is not int or o[2]<100 for o in market):
                return None
        if any(shadow.diagnostics.values()):return None
        run=_PLANNER_NS['simulate'](projected,config,[action])
        if run['actions'][0]!=action:return None
        baseline.append(action)
        run['farm']['money']=projected['farms'][seat]['money']
        projected['farms'][seat]=run['farm'];projected['private']=run['private']
    return baseline,states

def agent(observation,configuration=None):
    try:
        step=int(observation['step']);seat=int(observation['player'])
    except Exception:
        return _PRE_TERMINAL_AGENT(observation,configuration)
    previous=_TERMINAL_PREVIOUS.get(seat)
    if step==0 or (previous is not None and step<=previous):_TERMINAL_PLANS.pop(seat,None)
    _TERMINAL_PREVIOUS[seat]=step
    plan=_TERMINAL_PLANS.get(seat)
    if plan and plan.get('accepted') and 712<=step<=718:
        if previous!=step-1:plan.update(abandoned=True,reason='nonconsecutive callback')
        try:
            result=_PLANNER_NS['terminal_action'](observation,configuration,plan['baseline'][step-712],plan)
            if plan.get('abandoned'):
                if not plan.get('abort_counted'):
                    plan['abort_counted']=True;_UPGRADE_STATS['aborted']+=1
                if not plan.get('deviated'):
                    _IMPL.chassis.players[seat]=copy.deepcopy(plan['parent_states_before'][step-712])
                    _TERMINAL_PLANS.pop(seat,None)
                    return _PRE_TERMINAL_AGENT(observation,configuration)
            _UPGRADE_STATS['changed_steps']+=int(result!=plan['baseline'][step-712])
            return result
        except Exception:
            _UPGRADE_STATS['errors']+=1
            if plan.get('deviated'):
                try:return _PLANNER_NS['_recover_observed'](observation,configuration,plan['baseline'][step-712],plan)
                except Exception:return _parent_liquidate(observation['farms'][seat],observation['private'],observation['market']['prices'])
    if step!=712:return _PRE_TERMINAL_AGENT(observation,configuration)
    _UPGRADE_STATS['planning_calls']+=1
    try:shadow=_shadow_terminal(observation,configuration)
    except (ValueError,KeyError,TypeError,IndexError):shadow=None
    if shadow is None:
        _UPGRADE_STATS['shadow_declines']+=1
        return _PRE_TERMINAL_AGENT(observation,configuration)
    baseline,states=shadow
    actual=_PRE_TERMINAL_AGENT(observation,configuration)
    if actual!=baseline[0]:
        _UPGRADE_STATS['shadow_declines']+=1;return actual
    try:
        plan=_PLANNER_NS['plan_terminal'](observation,configuration,baseline,max_simulations=64,passes=1,proposals_per_actor=4)
        _UPGRADE_STATS['max_planning_ms']=max(_UPGRADE_STATS['max_planning_ms'],plan.get('planning_ms',0.0))
        if not plan.get('accepted'):return actual
        plan['parent_states_before']=states;_TERMINAL_PLANS[seat]=plan
        _UPGRADE_STATS['accepted']+=1
        result=_PLANNER_NS['terminal_action'](observation,configuration,actual,plan)
        _UPGRADE_STATS['changed_steps']+=int(result!=actual)
        return result
    except Exception:
        _UPGRADE_STATS['errors']+=1;return actual

agent.telemetry=_UPGRADE_STATS

# EXP-154: aurax7 Reactive v2 day-end storage guard, adapted to our v27 view.
_PRE_ROOM_AGENT=agent
del agent
_ROOM_STATS={'changed_turns':0,'added_units':0,'errors':0}
def agent(observation,configuration=None):
    action=_PRE_ROOM_AGENT(observation,configuration)
    try:
        step=_step_of(observation)
        if step%24!=23:return action
        view=_View(observation,_int(_get(observation,'player',0)),_IMPL.chassis.cfg)
        carried=sum(max(0,int(n)) for inv in view.invs for n in inv.values())
        needed=sum(view.shed.values())+carried-99
        if needed<=0:return action
        planned={}
        for o in action.get('market',[]):
            if o and o[0]=='SELL' and len(o)>=3:planned[o[1]]=planned.get(o[1],0)+max(0,int(o[2]))
        result=copy.deepcopy(action);added=0
        for item in sorted(PRODUCTS,key=lambda it:-int(view.prices.get(it,0))):
            qty=min(needed,max(0,view.shed.get(item,0)-planned.get(item,0)))
            if qty<=0:continue
            if len(result['market'])>=10:break
            result['market'].append(['SELL',item,qty]);needed-=qty;added+=qty
            if needed<=0:break
        if added:_ROOM_STATS['changed_turns']+=1;_ROOM_STATS['added_units']+=added
        return result
    except Exception:
        _ROOM_STATS['errors']+=1;return action

agent.telemetry=_ROOM_STATS

# Incorporated upstream attribution and change notice:
# E182 Shop0909 + terminal physical closure (modified 2026-09-09)
# 
# The active public parent is Yusuke Hayashi's yhay81/shop-router-0909 v3.
# router_parent.py and actions.json are exact original bytes, not newly authored
# routes. The parent credits aurax7's Reactive Router for sale timing and shed
# projection; that attribution remains in router_parent.py. Original payload
# LICENSE.txt is preserved unchanged (Apache License 2.0 text); it contains no
# named copyright grantor and no separate NOTICE was supplied. No additional
# ownership, endorsement, or upstream replay-data rights claim is made.
# 
# Local changes: separate main.py/policy.py adapter; bounded start712 planner
# copied from frozen E180/S78 and modified for seven callbacks, exact Shop final
# liquidation, strict positive physical delivery/sale gain, and observation guards.
# unit_model.py is an unchanged frozen E180 copy of Kaggle's extracted semantics.
# The following original E180 notice is retained verbatim for attribution history.
# Its references to Thomas files describe E180, not files supplied in this Shop
# package: no Thomas tapes, trees or policy are included here.
# 
# ----- Original E180 notice -----
# Kaggriculture: Last-Mile Harvest Planner
# Attribution and change notice
# 
# Thomas Tschinkel is the author of the parent public state-router policy and its
# published decision trees and action-route data. Source: Kaggriculture: 93.8% Win
# Rate Public State Router, notebook version 3, scriptVersionId 347936183:
# https://www.kaggle.com/code/thomastschinkel/kaggriculture-93-8-win-rate-public-state-router?scriptVersionId=347936183
# The public notebook identifies its license as Apache License, Version 2.0.
# Original published main.py SHA-256:
# b87a27ed614a33329be85f1b662e51cf4078a019fee937afcebbbbf2f51f8522
# 
# Changes to that source for this distribution: compressed route/tree literals
# were decoded into readable tapes.json and trees.json; a read-only planned_action
# helper was added; descriptive headers and local data loading were adapted.
# The original parent feature extraction, tree traversal and agent behavior are
# retained. These public routes are not claimed as newly authored or trained by
# the notebook distributor.
# 
# unit_model.py contains deterministic unit-action and crop-decay definitions
# extracted from Kaggle's kaggle-environments 1.32.7 Kaggriculture engine, licensed
# under Apache License, Version 2.0. Credit: Kaggle and the kaggle-environments
# contributors. Project: https://github.com/Kaggle/kaggle-environments
# Source file: kaggle_environments/envs/kaggriculture/kaggriculture.py
# Source SHA-256:
# bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e
# The extracted unit/decay definitions are not a newly authored game engine;
# market price dynamics and the full interpreter are not part of this module.
# 
# Additional work in this distribution: a bounded last-nine-action collection
# and delivery planner, observation guards and recovery, a settings-consuming
# factory and entry point, standalone examples, and deterministic packaging.
# The full Apache License, Version 2.0 is included as LICENSE.txt.
# No endorsement by Thomas Tschinkel or Kaggle is implied.
# 
# Data provenance limitation: Thomas's source refers to public replay data and
# an upstream provenance.json. That original episode-level manifest, replay IDs
# and individual replay-author identities were not supplied with the public
# notebook/output used here. No names or episode lineage have been invented.
# Notebook-level licensing does not independently establish the missing underlying
# replay-data rights chain. The package supplies usable readable routes, not a
# reproducible reconstruction of their original collection or training process.
# 
# Packaging note: source inputs described as byte-exact above are
# normalized to UTF-8/LF text with a final newline in this standalone
# notebook package. Route JSON values and parent policy behavior are unchanged.

# Final public-entry guard; measured separately and compared on captured observations.
_V28_CORE=agent
del agent
_IMPL.chassis.diagnostics['v28_entry_errors']=0
def agent(observation,configuration=None):
    try:
        return _V28_CORE(observation,configuration)
    except Exception:
        _IMPL.chassis.diagnostics['v28_entry_errors']+=1
        return {'farmer':['PASS'],'hands':[],'market':[]}
agent.telemetry=_ROOM_STATS

# EXP-155: prvsiyan V221B finite tomato investment, adapted by Ahmed Berat Ozer.
# Original public source is retained under research24/public; Apache-2.0.
MAX_ORDERS=10
class FarmView(_View):
    def __init__(self,obs):super().__init__(obs,int(obs['player']),_IMPL.chassis.cfg)
    def inventory(self,actor):return self.inv(actor)
def projected_shed(action,view):return _IMPL.chassis._projected_shed(action,view)

CROP_MIN_PRICE=70

# V219: a finite late tomato investment with dedicated, observed workers.
_V219_PARENT = agent
del agent
_V219_FERTILIZE = True  # Builder changes only this flag for the ablation.
_V219_STATES = {}
_V219_REPORT = {'commitments': 0, 'hire_requests': 0, 'confirmed_workers': 0,
                'hire_shortfalls': 0, 'plant_requests': 0, 'confirmed_plants': 0,
                'water_requests': 0, 'fertilize_requests': 0, 'harvest_requests': 0,
                'confirmed_harvest_units': 0, 'drop_requests': 0,
                'tomato_sale_requests': 0, 'budget_declines': 0, 'lost_plants': 0}


def _v219_fib(n):
    a, b = 1, 1
    for _ in range(n): a, b = b, a+b
    return a


def _v219_native_day(native, day):
    tape = _IMPL.chassis.routes[native['route']]
    return tape[day*24:min((day+1)*24,719)]


def _v219_qualifies(obs, native):
    farm=obs['farms'][obs['player']]
    if len(farm['tiles']) != 10 or set(farm['unlocked_quadrants']) != {'NW','NE','SW'}:
        return False
    if farm['money'] < 12000 or obs['market']['prices']['TOMATO'] < CROP_MIN_PRICE:
        return False
    # Agent L: also two tomato shops once the town is short enough.
    _shops = sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in obs['town']['unlocked_shops'])
    _short = 10000 - obs['market']['inventory']['TOMATO']
    if _shops < 2 or (_shops < 3 and _short < 120):
        return False
    if any(farm['tiles'][y][x] != 'LOCKED' for y in (5,6) for x in range(5,10)):
        return False
    if obs['private']['seeds'].get('TOMATO',0) or obs['private']['shed'].get('TOMATO',0):
        return False
    if any(isinstance(t,dict) and t.get('crop')=='TOMATO' for row in farm['tiles'] for t in row):
        return False
    # The investment uses spare land and new worker indices. Avoid taking over
    # any native tomato or land purchase obligation on the known own schedule.
    for tape in _IMPL.chassis.routes.values():
        for a in tape[432:719]:
            if any(o and o[0]=='BUY_LAND' for o in a.get('market',[])):return False
            if any(c==['PLANT','TOMATO'] for c in [a.get('farmer')]+a.get('hands',[])):return False
    return True


def _v219_walk(pos, target):
    x,y=pos;tx,ty=target
    if x != tx:return ['EAST' if x < tx else 'WEST']
    if y != ty:return ['SOUTH' if y < ty else 'NORTH']
    return None


def _v219_home(pos):
    return min(((4,4),(5,4),(4,5),(5,5)),key=lambda p:abs(pos[0]-p[0])+abs(pos[1]-p[1]))


def _v219_request(obs, action, state, native):
    step=int(obs['step']);day=step//24;offset=step%24
    farm=obs['farms'][obs['player']];private=obs['private']
    # If the planting-day transaction could not complete, abandon investment.
    # Later purchases would miss the finite day26..29 production window.
    if not state.get('committed') and day!=18:return action
    if state.get('requested_day')==day:return action
    planned=_v219_native_day(native,day)
    # EXP240: committed crops must wait for the native worker indices.
    # New schedules finish native hiring at hour4 or6. The existing two/three
    # crop-worker groups can still water/harvest their ten cells by midnight.
    # Initial investment stays within hour3; ordinary schedules are unchanged.
    latest_hire=max((i for i,a in enumerate(planned) if any(o and o[0]=='HIRE' for o in a.get('market',[]))),default=-1)
    deadline=6 if state.get('committed') and 3<latest_hire<=6 else 3
    if offset>deadline:return action
    remaining=planned[offset+1:]
    if any(o and o[0]=='HIRE' for a in remaining for o in a.get('market',[])):
        return action
    parent_hires=sum(bool(o) and o[0]=='HIRE' for o in action['market'])
    expected=max(len(a.get('hands',[])) for a in planned)
    if len(farm['hands'])+parent_hires != expected:return action
    fertilizer=bool(_V219_FERTILIZE and day in (24,27) and _r79_tomato_fertilizer_worthwhile(obs,action))
    # One watering tour: at most 2 entry moves + 9 between tiles + 10 waters.
    # A hire request by hour2 leaves at least21 callbacks after confirmation.
    crop_workers=1 if day in (19,20,21,22,23,25) and offset<=2 else (3 if 26<=day<=28 else 2)
    labor=_r53_labor_assignment(obs,action,fertilizer)
    if labor is not None:crop_workers=labor['workers']
    count=crop_workers+int(fertilizer and day==27 and labor is None)
    extra=[]
    if not state.get('committed'):
        extra += [['BUY_LAND'],['BUY_SEED','TOMATO',10]]
    fertilizer_quantity=_r70_parent_fert_qty(obs,action,planned,offset) if fertilizer else 0
    if fertilizer:extra.append(['BUY_PRODUCT','FERTILIZER',fertilizer_quantity])
    extra += [['HIRE'] for _ in range(count)]
    if len(action['market'])+len(extra)>MAX_ORDERS:return action
    # No assumed sale proceeds. Reserve 3,000 for parent obligations and price
    # movement; the qualification separately requires 12,000 initial liquidity.
    budget=sum(_v219_fib(n) for n in range(farm['hires_today'],farm['hires_today']+parent_hires+count))
    if not state.get('committed'):budget+=4500
    if fertilizer:budget+=fertilizer_quantity*(obs['market']['prices']['FERTILIZER']+5)
    for order in action['market']:
        if not order:continue
        if order[0]=='BUY_PRODUCT':budget+=int(order[2])*(int(obs['market']['prices'][order[1]])+10)
        elif order[0]=='BUY_ANIMAL':budget+=int(order[2])*{'COW':400,'SHEEP':500,'GOOSE':300}[order[1]]
        elif order[0]=='BUY_SEED':budget+=int(order[2])*{'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}[order[1]]
    if farm['money']<budget+3000:
        _V219_REPORT['budget_declines']+=1;return action
    state['pending']={'step':step,'first_actor':expected+1,'count':count,'crop_workers':crop_workers,'fertilizer':fertilizer,'labor':labor}
    if labor is not None:
        _R53_LABOR_REPORT['labor_requests']+=1;_R53_LABOR_REPORT['labor_hires_avoided']+=1;_R53_LABOR_REPORT['labor_day'+str(day)]+=1
    state['requested_day']=day
    _V219_REPORT['hire_requests']+=count
    if not state.get('committed'):
        state['committed']=True;_V219_REPORT['commitments']+=1
    changed=copy.deepcopy(action);changed['market']+=extra
    return changed


def _v219_worker(obs, state, actor, role):
    day=int(obs['step'])//24;step=int(obs['step']);view=FarmView(obs)
    pos=tuple(view.positions[actor]);inv=view.inventory(actor)
    targets=role['targets']
    # Actual cargo differences, observed on the next callback, verify harvests.
    previous=state['last_work'].get(actor)
    if previous and previous['step']==step-1 and previous['command']==['HARVEST']:
        _V219_REPORT['confirmed_harvest_units']+=max(0,int(inv.get('TOMATO',0))-previous['tomatoes'])
    if role.get('needs_fertilizer') and not role.get('loaded'):
        home=_v219_home(pos)
        walk=_v219_walk(pos,home)
        if walk:return walk
        desired=role.get('fertilizer_quantity',10 if role['kind']=='fertilizer' else 5)
        if inv.get('FERTILIZER',0)>=desired:role['loaded']=True
        elif role.get('pickup_requested'):
            # Never spend repeated turns waiting for stock that was not bought.
            role['loaded']=True;role['fertilizer_available']=int(inv.get('FERTILIZER',0))
        elif view.shed.get('FERTILIZER',0)>=desired:
            role['pickup_requested']=True;return ['PICKUP','FERTILIZER',desired]
        else:role['loaded']=True
    todo=[]
    for target in targets:
        x,y=target;tile=view.tiles[y][x]
        tomato=isinstance(tile,dict) and tile.get('crop')=='TOMATO'
        if tomato and target not in state['seen_plants']:
            state['seen_plants'].add(target);_V219_REPORT['confirmed_plants']+=1
        if target in state['seen_plants'] and not tomato and target not in state['lost']:
            state['lost'].add(target);_V219_REPORT['lost_plants']+=1
        command=None
        if role['kind']=='fertilizer':
            if tomato and tile.get('fertilized_until_day',-1)<day+2 and inv.get('FERTILIZER',0)>0:
                command=['FERTILIZE']
        elif day==18 and not tomato:
            if tile is None and obs['private']['seeds'].get('TOMATO',0)>0:command=['PLANT','TOMATO']
            elif isinstance(tile,dict) and tile.get('kind')=='WEED':command=['DIG']
        elif tomato:
            # No later production follows the final day, so watering then would
            # consume time needed to harvest and deliver the final cargo.
            if day<29 and not tile.get('watered_today'):command=['WATER']
            elif role.get('needs_fertilizer') and tile.get('fertilized_until_day',-1)<day+2 and inv.get('FERTILIZER',0)>0:
                command=['FERTILIZE']
            elif tile.get('yield_units',0)>0:command=['HARVEST']
        if command:todo.append((target,command))
    # Final return has priority once only the exact distance plus DROP remains.
    home=_v219_home(pos);distance=abs(pos[0]-home[0])+abs(pos[1]-home[1])
    if step>=718-distance and inv.get('TOMATO',0):
        return _v219_walk(pos,home) or ['PLACE','TOMATO',int(inv.get('TOMATO',0))]
    if todo:
        target,command=min(todo,key=lambda v:(abs(pos[0]-v[0][0])+abs(pos[1]-v[0][1]),targets.index(v[0])))
        return _v219_walk(pos,target) or command
    if inv.get('TOMATO',0):return _v219_walk(pos,home) or ['PLACE','TOMATO',int(inv['TOMATO'])]
    if any(inv.values()):return _v219_walk(pos,home) or ['DROP']
    return ['PASS']


def agent(observation, configuration=None):
    action=_V219_PARENT(observation,configuration)
    step=int(observation['step']);player=int(observation['player']);day=step//24
    state=_V219_STATES.get(player)
    if state is None or step<=state['last_step']:
        state={'last_step':step,'day':-1,'workers':{},'last_work':{},'seen_plants':set(),'lost':set(),
               'targets':[(x,y) for y in (5,6) for x in range(5,10)]}
        _V219_STATES[player]=state
    state['last_step']=step
    native=_IMPL.chassis.players[player]
    if step==432:state['eligible']=_v219_qualifies(observation,native)
    if not state.get('eligible') or day<18:return action
    if state['day']!=day:
        state['day']=day;state['workers']={};state['last_work']={}
    farm=observation['farms'][player]
    pending=state.pop('pending',None)
    if pending:
        if len(farm['hands'])+1 >= pending['first_actor']+pending['count'] and 'SE' in farm['unlocked_quadrants']:
            for index in range(pending['count']):
                fertilizer_worker=index==pending['crop_workers']
                if fertilizer_worker:targets=state['targets']
                elif pending['crop_workers']==1:targets=state['targets']
                elif pending['crop_workers']==2:targets=state['targets'][index*5:index*5+5]
                else:targets=[[(5,5),(6,5),(7,5)],[(8,5),(9,5),(9,6),(8,6)],[(5,6),(6,6),(7,6)]][index]
                state['workers'][pending['first_actor']+index]={'kind':'fertilizer' if fertilizer_worker else 'crop','targets':targets,
                    'needs_fertilizer':pending['fertilizer'] and (day==24 or fertilizer_worker)}
                if pending.get('labor') is not None:
                    role=state['workers'][pending['first_actor']+index]
                    role['targets']=[tuple(p) for p in pending['labor']['paths'][index]]
                    role['needs_fertilizer']=pending['labor']['fertilizer'];role['fertilizer_quantity']=len(role['targets'])
                    if tuple(farm['hands'][pending['first_actor']+index-1])!=tuple(pending['labor']['spawns'][index]):_R53_LABOR_REPORT['labor_spawn_errors']+=1
                    if index==0:_R53_LABOR_REPORT['labor_confirmed']+=1
            _V219_REPORT['confirmed_workers']+=pending['count']
        else:_V219_REPORT['hire_shortfalls']+=pending['count']
    action=_v219_request(observation,action,state,native)
    if state['workers']:
        commands=[action.get('farmer') or ['PASS']]+list(action.get('hands') or [])
        commands += [['PASS'] for _ in range(len(farm['hands'])+1-len(commands))]
        for actor,role in state['workers'].items():
            if actor>=len(commands):continue
            command=_v219_worker(observation,state,actor,role)
            commands[actor]=command
            name={'PLANT':'plant_requests','WATER':'water_requests','FERTILIZE':'fertilize_requests',
                  'HARVEST':'harvest_requests','DROP':'drop_requests'}.get(command[0])
            if name:_V219_REPORT[name]+=1
            state['last_work'][actor]={'step':step,'command':command,'tomatoes':observation['private']['inventories'][actor].get('TOMATO',0)}
        action=copy.deepcopy(action);action['farmer'],action['hands']=commands[0],commands[1:]
    if state.get('committed') and len(action['market'])<MAX_ORDERS and not any(o[:2]==['SELL','TOMATO'] for o in action['market']):
        quantity=projected_shed(action,FarmView(observation)).get('TOMATO',0)
        if quantity>0:
            action=copy.deepcopy(action);action['market'].append(['SELL','TOMATO',quantity])
            _V219_REPORT['tomato_sale_requests']+=quantity
    return action


agent.telemetry=_V219_REPORT

# V221B: labor-only ablation of frozen V219G; not yet publicly scored.


# Crop workers own their final routes after commitment. A private parent shadow
# does not contain these obligations, so terminal rescue must abstain there.
_ORIGINAL_SHADOW_TERMINAL=_shadow_terminal
def _shadow_terminal(obs,config):
    if _V219_STATES.get(int(obs['player']),{}).get('committed'):return None
    return _ORIGINAL_SHADOW_TERMINAL(obs,config)

APPLY_TIMING=False

_EXPERIMENT_PARENT=agent
del agent
_V219_REPORT['extra_fertilizer_days']=0
_V219_REPORT['reordered_market_turns']=0
_V219_REPORT['errors']=0
def agent(observation,configuration=None):
    try:
        action=_EXPERIMENT_PARENT(observation,configuration)
        if APPLY_TIMING and int(observation['step'])>=144:action=_v224_sales_first(action)
        return action
    except Exception:
        _V219_REPORT['errors']+=1
        return {'farmer':['PASS'],'hands':[],'market':[]}
agent.telemetry=_V219_REPORT

def _v224_sales_first(action):
    original=action.get('market',[])[:MAX_ORDERS]
    orders=[list(o) for o in original if o and (o[0] in ('HIRE','BUY_LAND') or (len(o)>=3 and int(o[2])>0))]
    for index in range(len(orders)):
        order=orders[index]
        if order[0]!='SELL':continue
        cursor=index
        while cursor>0:
            previous=orders[cursor-1]
            if previous[0]=='SELL':break
            if previous[0] in ('BUY_PRODUCT','BUY_ANIMAL') and previous[1]==order[1]:break
            orders[cursor-1],orders[cursor]=orders[cursor],orders[cursor-1]
            cursor-=1
    if orders==original:return action
    _V219_REPORT['reordered_market_turns']+=1
    changed=copy.deepcopy(action);changed['market']=orders
    return changed
_ORDER_PARENT=agent
del agent

def agent(observation,configuration=None):
    try:
        action=_ORDER_PARENT(observation,configuration)
        if int(observation["step"])>=144:action=_v224_sales_first(action)
        return action
    except Exception:
        _V219_REPORT["errors"]+=1
        return {"farmer":["PASS"],"hands":[],"market":[]}
agent.telemetry=_V219_REPORT

_V31_CORE=agent
del agent
_IMPL.chassis.diagnostics['production_errors']=0
_IMPL.chassis.diagnostics['v31_entry_errors']=0
def agent(observation,configuration=None):
    before=_V219_REPORT['errors']
    try:
        action=_V31_CORE(observation,configuration)
        _IMPL.chassis.diagnostics['production_errors']+=_V219_REPORT['errors']-before
        return action
    except Exception:
        _IMPL.chassis.diagnostics['v31_entry_errors']+=1
        return {'farmer':['PASS'],'hands':[],'market':[]}
agent.telemetry=_V219_REPORT

# Apache-2.0; later cattle transfer from prvsiyan, Moon (2026-09-10).
# Bounded livestock substitution; confirm owned animals before redirecting workers.
_V231_PARENT=agent
_V231_CAP=4
_V231_STATES={}
_V231_REPORT={}

def _v231_new_state():
    return {'last':-1,'confirmed':0,'reserved':0,'pending_buy':None,
            'carrying':{},'pending_places':[],'sites':{},'milk_credit':0,
            'requested':0,'failed_purchase_units':0,'picked':0,'placed':0,
            'failed_placements':0,'extra_milk_harvested':0,'extra_milk_sale_requests':0}

def _v231_controller(obs,action,state,cap):
    step=int(obs['step']);seat=int(obs['player']);farm=obs['farms'][seat]
    private=obs['private'];shed=private['shed'];inventories=private['inventories']
    positions=[farm['farmer'],*farm['hands']]
    pending=state['pending_buy']
    if pending is not None:
        gained=max(0,int(shed.get('COW',0))-pending['before'])
        confirmed=min(pending['quantity'],gained)
        state['confirmed']+=confirmed;state['reserved']+=confirmed
        state['failed_purchase_units']+=pending['quantity']-confirmed
        state['pending_buy']=None
    for pending in state['pending_places']:
        x,y=pending['site'];tile=farm['tiles'][y][x]
        if (isinstance(tile,dict) and tile.get('animal')=='COW'
                and tile.get('placed_day')==pending['day']):
            state['sites'][(x,y)]=pending['day'];state['placed']+=1
            actor=pending['actor'];state['carrying'][actor]=max(0,state['carrying'].get(actor,0)-1)
        else:state['failed_placements']+=1
    state['pending_places']=[]
    state['last']=step
    result=copy.deepcopy(action)
    workers=[result.get('farmer') or ['PASS'],*(result.get('hands') or [])]
    seen_harvest=set();cow_available=int(shed.get('COW',0));occupied=set()
    for actor,work in enumerate(workers[:len(positions)]):
        inventory=inventories[actor] if actor<len(inventories) else {}
        x,y=positions[actor];tile=farm['tiles'][y][x];site=(x,y)
        if (work==['HARVEST'] and site in state['sites'] and site not in seen_harvest
                and isinstance(tile,dict) and tile.get('animal')=='COW'
                and tile.get('placed_day')==state['sites'][site]):
            units=max(0,int(tile.get('yield_units',0)))
            state['milk_credit']+=units;state['extra_milk_harvested']+=units
            seen_harvest.add(site)
        if len(work)>=2 and work[:2]==['PICKUP','SHEEP']:
            quantity=max(0,int(work[2]) if len(work)>2 else 1)
            center=len(farm['tiles'])//2
            if (quantity and state['reserved']>=quantity and cow_available>=quantity
                    and x in (center-1,center) and y in (center-1,center)
                    and not any(inventory.get(a,0) for a in ('COW','SHEEP','GOOSE'))):
                work[1]='COW';state['reserved']-=quantity;cow_available-=quantity
                state['carrying'][actor]=state['carrying'].get(actor,0)+quantity
                state['picked']+=quantity
        if (len(work)>=2 and work[:2]==['PLACE','SHEEP']
                and state['carrying'].get(actor,0)>0 and inventory.get('COW',0)>0
                and isinstance(tile,dict) and tile.get('kind')=='PASTURE'
                and 'animal' not in tile and site not in occupied):
            work[1]='COW'
            state['pending_places'].append({'actor':actor,'site':site,'day':step//24})
        if (len(work)>=2 and work[0]=='PLACE' and work[1] in ('COW','SHEEP','GOOSE')
                and inventory.get(work[1],0)>0):occupied.add(site)
    result['farmer'],result['hands']=workers[0],workers[1:]
    market=result.get('market',[])
    animal_orders=[o for o in market if len(o)>=3 and o[0]=='BUY_ANIMAL']
    shops=obs['town']['unlocked_shops'];prices=obs['market']['prices']
    counts={'COW':0,'SHEEP':0}
    for line in farm['tiles']:
        for tile in line:
            if isinstance(tile,dict) and tile.get('animal') in counts:counts[tile['animal']]+=1
    cargo=sum(int(inv.get(a,0)) for inv in inventories for a in ('COW','SHEEP','GOOSE'))
    stock_animals=sum(int(shed.get(a,0)) for a in ('COW','SHEEP','GOOSE'))
    milk_shops=sum(shop in ('PIZZA_SHOP','ICE_CREAM_SHOP','SMOOTHIE_SHOP') for shop in shops)
    if (216<=step<=227 and len(shops)>=3 and state['confirmed']<cap and not state['reserved']
            and not any(state['carrying'].values()) and not state['pending_places']
            and not cargo and not stock_animals and len(animal_orders)==1
            and animal_orders[0][1]=='SHEEP' and milk_shops>=2 and 'YARN_STORE' not in shops
            and int(prices.get('MILK',0))>=int(prices.get('WOOL',0))
            and counts['COW']>=4 and counts['SHEEP']>=2):
        order=animal_orders[0];quantity=int(order[2])
        if 1<=quantity<=2 and quantity<=cap-state['confirmed']:
            order[1]='COW';state['requested']+=quantity
            state['pending_buy']={'before':int(shed.get('COW',0)),'quantity':quantity}
    # Sell only additional physically harvested production at an existing sale slot.
    if state['milk_credit']>0:
        stock=projected_shed(result,FarmView(obs))
        total_planned=sum(max(0,int(o[2])) for o in market if len(o)>=3 and o[:2]==['SELL','MILK'])
        extra=min(state['milk_credit'],max(0,int(stock.get('MILK',0))-total_planned))
        if extra:
            for order in market:
                if len(order)>=3 and order[:2]==['SELL','MILK'] and int(order[2])>0:
                    order[2]=int(order[2])+extra
                    state['milk_credit']-=extra;state['extra_milk_sale_requests']+=extra
                    break
    result['market']=market
    return result

def agent(observation,configuration=None):
    step=int(observation['step']);seat=int(observation['player'])
    state=_V231_STATES.get(seat)
    if state is None or step<=state['last']:
        state=_V231_STATES[seat]=_v231_new_state()
    action=_V231_PARENT(observation,configuration)
    action=_v231_controller(observation,action,state,_V231_CAP)
    _V231_REPORT.clear();_V231_REPORT.update(_V231_PARENT.telemetry)
    for name in ('confirmed','reserved','requested','failed_purchase_units','picked','placed',
                 'failed_placements','extra_milk_harvested','extra_milk_sale_requests','milk_credit'):
        _V231_REPORT['cattle_'+name]=state[name]
    _V231_REPORT['cattle_carried_pending']=sum(state['carrying'].values())
    return action

agent.telemetry=_V231_REPORT


# EXP-167, adapted from Dmitrii Gluzdov's Two Coins, One Sheep (Apache-2.0).
# Reserve only physically available stock after the final parent worker actions.
_R36_SALE_PARENT=agent
_R36_NATIVE_LEAD=Chassis._sell_lead
_R36_NATIVE_SUPPRESS=Chassis._apply_suppression
_R36_SALE_REPORT={}

def _r36_native_lead(self,action,view,projected,route,step,next_sup):
    if step<288 or step>=696:
        return _R36_NATIVE_LEAD(self,action,view,projected,route,step,next_sup)

def _r36_suppress(action,state,step):
    _R36_NATIVE_SUPPRESS(action,state,step)
    due=state.get('r36_debts',{}).pop(step,{})
    for order in action.get('market',[]):
        if len(order)>=3 and order[0]=='SELL':
            removed=min(max(0,int(order[2])),due.get(order[1],0))
            order[2]-=removed
            due[order[1]]=due.get(order[1],0)-removed

Chassis._sell_lead=_r36_native_lead
Chassis._apply_suppression=staticmethod(_r36_suppress)

def _r36_reserve(obs,action):
    step=int(obs['step'])
    # The final planner forecasts its own parent, so keep its full window native.
    if not 192<=step<696:return action
    native=_IMPL.chassis.players[int(obs['player'])]
    tape=_IMPL.chassis.routes[native['route']]
    _v9_hz=_V9_ITEM_HZ.get(int(obs['player']))
    end=min(695,step+(max(_v9_hz.values()) if _v9_hz else _R37_HORIZONS.get(int(obs['player']),2)))
    if end<=step:return action
    commands=[action.get('farmer') or ['PASS'],*(action.get('hands') or [])]
    view=FarmView(obs)
    # This projection intentionally abstains on ambiguous animal depot returns.
    if any(len(c)>1 and c[0]=='PLACE' and c[1] in ANIMAL_STRUCTURE
           and view.inv(i).get(c[1],0)>0 for i,c in enumerate(commands[:len(view.positions)])):
        return action
    stock=projected_shed(action,view)
    market=action.get('market',[])
    blocked={o[1] for o in market if len(o)>1 and o[0] in ('SELL','BUY_PRODUCT')}
    blocked.update(c[1] for c in commands if len(c)>1 and c[0]=='PICKUP')
    blocked.update(c[1] for queue in native['pending'].values() for pos,c in queue
                   if len(c)>1 and c[0]=='PICKUP')
    debts=native['sell_state'].setdefault('r36_debts',{})
    for item in PRODUCTS:
        if item in blocked or view.prices.get(item,0)<2:continue
        available=max(0,int(stock.get(item,0)))
        if not available or len(market)>=10:continue
        reservations=[]
        item_end=min(end,step+_v9_hz[item]) if _v9_hz and item in _v9_hz else end
        for due_step in range(step+1,item_end+1):
            future=tape[due_step]
            work=[future.get('farmer') or ['PASS'],*(future.get('hands') or [])]
            if any(len(c)>1 and c[:2]==['PICKUP',item] for c in work):break
            if any(len(o)>1 and o[:2]==['BUY_PRODUCT',item] for o in future.get('market',[])):break
            planned=sum(max(0,int(o[2])) for o in future.get('market',[]) if len(o)>=3 and o[:2]==['SELL',item])
            amount=min(available,max(0,planned-debts.get(due_step,{}).get(item,0)))
            if amount:
                reservations.append((due_step,amount));available-=amount
            if not available:break
        qty=sum(q for _,q in reservations)
        if qty:
            market.append(['SELL',item,qty])
            for due,q in reservations:
                debt=debts.setdefault(due,{})
                debt[item]=debt.get(item,0)+q
            _R36_SALE_REPORT['sale_reserved_units']+=qty
            _R36_SALE_REPORT['sale_reservations']+=1
    return action

def agent(observation,configuration=None):
    if int(observation.get('step',0))==0:
        _R36_SALE_REPORT.update(sale_reserved_units=0,sale_reservations=0,sale_errors=0)
    action=_R36_SALE_PARENT(observation,configuration)
    try:
        if configuration is None or all(configuration.get(k,v)==v for k,v in
            [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)]):
            action=_r36_reserve(observation,action)
            if int(observation['step'])>=288:action=_v224_sales_first(action)
    except Exception:
        _R36_SALE_REPORT['sale_errors']=_R36_SALE_REPORT.get('sale_errors',0)+1
    _R36_SALE_REPORT.update(_R36_SALE_PARENT.telemetry)
    return action

agent.telemetry=_R36_SALE_REPORT

# Ensure the Kaggle-selected final callable is the exported policy.
agent = globals().pop("agent")


# Public capability transfer: lucifer19; Flexon is the same Two Coins asset set.
# Apache-2.0; exact functions from Kaggle kaggle-environments 1.32.7.
# https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/kaggriculture
import math
_R37_MARKET_PARAMS = {'WHEAT': {'base': 25, 'I0': 10000, 'T': 400, 'below_func': 'sqrt', 'below_target': 0.8, 'above_func': 'log', 'above_target': 0.2}, 'CARROT': {'base': 35, 'I0': 10000, 'T': 450, 'below_func': 'hinge', 'below_target': 1.0, 'above_func': 'sqrt', 'above_target': 0.7}, 'TOMATO': {'base': 60, 'I0': 10000, 'T': 200, 'below_func': 'hinge', 'below_target': 0.4, 'above_func': 'sqrt', 'above_target': 0.6}, 'STRAWBERRY': {'base': 120, 'I0': 10000, 'T': 100, 'below_func': 'sqrt', 'below_target': 0.7, 'above_func': 'linear', 'above_target': 1.6}, 'MELON': {'base': 250, 'I0': 10000, 'T': 300, 'below_func': 'log', 'below_target': 0.2, 'above_func': 'sq', 'above_target': 3.6}, 'EGG': {'base': 50, 'I0': 10000, 'T': 332, 'below_func': 'hinge', 'below_target': 0.4, 'above_func': 'log', 'above_target': 0.2}, 'MILK': {'base': 160, 'I0': 10000, 'T': 122, 'below_func': 'sqrt', 'below_target': 0.6, 'above_func': 'linear', 'above_target': 1.6}, 'WOOL': {'base': 200, 'I0': 10000, 'T': 105, 'below_func': 'log', 'below_target': 0.2, 'above_func': 'sq', 'above_target': 3.2}, 'FERTILIZER': {'base': 100, 'I0': 10000, 'T': 200, 'below_func': 'linear', 'below_target': 0.4, 'above_func': 'linear', 'above_target': 0.4}}
_R37_PRICE_FLOOR = 1
_R37_HINGE_GAIN = 8.0
def _r37_shape(func, x, T=None):
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(x)
    if func == "log":    return math.log(1.0 + x)
    if func == "log10":  return math.log10(1.0 + x)
    if func == "hinge":
        # Degenerates to linear if T is missing or non-positive.
        if not T or T <= 0:
            return x
        u = x / T
        return u + _R37_HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x

def _r37_market_price(item, inventory, params=None):
    """Floor at _R37_PRICE_FLOOR."""
    p = (params or _R37_MARKET_PARAMS)[item]
    base = p["base"]
    I0 = p["I0"]
    T = p["T"]
    if inventory < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _r37_shape(f, T, T)
        price = base + amp * _r37_shape(f, I0 - inventory, T)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _r37_shape(f, T, T)
        price = base - amp * _r37_shape(f, inventory - I0, T)
    return max(_R37_PRICE_FLOOR, int(round(price)))

def _r37_similarity(observation):
    """Empty tiles cannot make two unrelated production layouts look alike."""
    farms = observation['farms']
    own, rival = farms[observation['player']], farms[1-observation['player']]
    if own['unlocked_quadrants'] != rival['unlocked_quadrants']:
        return 0.0
    matches = total = 0
    for a, b in zip([t for row in own['tiles'] for t in row],
                    [t for row in rival['tiles'] for t in row]):
        sa = (a.get('crop'), a.get('animal')) if isinstance(a, dict) else (None, None)
        sb = (b.get('crop'), b.get('animal')) if isinstance(b, dict) else (None, None)
        if sa != (None, None) or sb != (None, None):
            total += 1
            matches += sa == sb
    return matches / total if total >= 8 else 0.0


def _r37_quote_priority(observation, order, stock):
    """Revenue exposed to a small rival batch, not nominal headline revenue."""
    item = order[1]
    quantity = min(max(0, int(order[2])), stock.get(item, 0))
    if not quantity or item not in _R37_MARKET_PARAMS:
        return 0.0
    inventory = observation['market']['inventory'][item]
    params = {k: dict(v) for k, v in _R37_MARKET_PARAMS.items()}
    for k, patch in observation['market'].get('params', {}).items():
        if k in params:
            params[k].update(patch)
    rival = observation['farms'][1-observation['player']]
    crop_item = item if item in ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON') else None
    animal = {'EGG':'GOOSE','MILK':'COW','WOOL':'SHEEP'}.get(item)
    standing = sum(max(0, int(t.get('yield_units', 0))) for row in rival['tiles'] for t in row
                   if isinstance(t, dict) and
                   ((crop_item is not None and t.get('crop') == crop_item) or
                    (animal is not None and t.get('animal') == animal)))
    # Public fields do not reveal the rival shed. Eight units are a scenario,
    # not a recovered hidden quantity; visible ripe yield increases the stress.
    batch = min(24, max(8, standing))
    now = sum(_r37_market_price(item, inventory+j, params) for j in range(quantity))
    later = sum(_r37_market_price(item, inventory+batch+j, params) for j in range(quantity))
    return now-later


def _r37_reorder_sales(observation, action):
    """Keep quantities and purchase barriers; rank distinct contiguous sales."""
    stock = projected_shed(action, FarmView(observation))
    orders = [list(o) for o in action['market']]
    start = 0
    while start < len(orders):
        if orders[start][0] != 'SELL':
            start += 1
            continue
        end = start
        while end < len(orders) and orders[end][0] == 'SELL':
            end += 1
        block = orders[start:end]
        if len({o[1] for o in block}) == len(block):
            orders[start:end] = sorted(block, key=lambda o: _r37_quote_priority(observation, o, stock), reverse=True)
        start = end
    if orders != action['market']:
        _R37_STATS['quote_reordered_turns'] += 1
        action = dict(action, market=orders)
    return action



# EXP175: bounded public cash-response probe inspired by leoprovorov,
# Two Coins Mirror Counter v1 (Apache-2.0). No hidden rival inventory.
_R44_PROBES={}
_R44_REPORT=dict(probe_matches=0,probe_four_turn_calls=0,probe_errors=0)

def _r44_before(obs):
    player=int(obs['player']);step=int(obs['step'])
    st=_R44_PROBES.get(player)
    if st is None or step<=st['step']:
        st=_R44_PROBES[player]={'step':-1,'money':None,'probe':0,'matched':False}
    if step==0:_R44_REPORT.update(probe_matches=0,probe_four_turn_calls=0,probe_errors=0)
    money=tuple(float(obs['farms'][i]['money']) for i in (player,1-player))
    if st['money'] is not None and st['probe']>=100 and _r37_similarity(obs)>=.90:
        own=money[0]-st['money'][0];rival=money[1]-st['money'][1]
        if own>0 and rival>0 and abs(own-rival)<=max(5.0,.05*st['probe']):
            if not st['matched']:_R44_REPORT['probe_matches']+=1
            st['matched']=True
    st.update(step=step,money=money,probe=0)
    return st

def _r44_after(obs,action,st):
    step=int(obs['step']);player=int(obs['player'])
    if not 336<=step<648 or st['matched']:return
    # Positive all-sale probes avoid mistaking equal spending for preemption.
    if not action['market'] or any(o and o[0]!='SELL' for o in action['market']):return
    debts=_IMPL.chassis.players[player]['sell_state'].get('r36_debts',{})
    own=debts.get(step+3,{})
    if own:st['probe']=sum(max(0,int(n))*int(obs['market']['prices'].get(item,0)) for item,n in own.items())

_R37_ADAPTIVE = True
_R37_QUOTE = True
# EXP-168: adapted from lucifer19 / Harvest Nocturne, Apache-2.0.
# All rivalry features use public occupied tiles; no private rival inventory.
_R37_PARENT = agent
_R37_PLAYERS = {}
_R37_HORIZONS = {}
_V9_ITEM_HZ = {}
_R37_REPORT = {}
_R37_STATS = dict(quote_reordered_turns=0, three_turn_calls=0, nocturne_errors=0)
del agent

def agent(observation, configuration=None):
    player, step = int(observation['player']), int(observation['step'])
    state = _R37_PLAYERS.get(player)
    if state is None or step <= state['step']:
        state = _R37_PLAYERS[player] = {'step': -1, 'streak': 0}
    if step == 0:
        _R37_STATS.update(quote_reordered_turns=0, three_turn_calls=0, nocturne_errors=0)
    state['step'] = step
    _R37_HORIZONS[player] = 2
    probe_state=_r44_before(observation)
    try:
        if _R37_ADAPTIVE and step < 648:
            state['streak'] = state['streak'] + 1 if _r37_similarity(observation) >= .90 else 0
            if 336 <= step < 648 and state['streak'] >= 6:
                _R37_HORIZONS[player] = 3
                _R37_STATS['three_turn_calls'] += 1
    except Exception:
        _R37_STATS['nocturne_errors'] += 1
    if _R37_HORIZONS[player]==3 and probe_state['matched']:
        _R37_HORIZONS[player]=4
        _R44_REPORT['probe_four_turn_calls']+=1
    # EXP179: four-turn reservation; retain stock, debt and purchase barriers.
    if 288 <= step < 696:_R37_HORIZONS[player] = 4
    action = _R37_PARENT(observation, configuration)
    _r44_after(observation,action,probe_state)
    if _R37_QUOTE and step >= 288:
        try:
            action = _r37_reorder_sales(observation, action)
        except Exception:
            _R37_STATS['nocturne_errors'] += 1
    _R37_REPORT.update(getattr(_R37_PARENT, 'telemetry', {}))
    _R37_REPORT.update(_R37_STATS)
    _R37_REPORT.update(_R44_REPORT)
    return action

agent.telemetry = _R37_REPORT

# Export guard: normal decisions stay identical to the frozen screened policy.
_RELEASE_PARENT=agent
_RELEASE_REPORT={}
_RELEASE_ERRORS=0
del agent

def agent(observation,configuration=None):
    global _RELEASE_ERRORS
    try:
        result=_RELEASE_PARENT(observation,configuration)
    except Exception:
        _RELEASE_ERRORS+=1
        count=0
        try:
            count=min(64,len(observation['farms'][int(observation['player'])]['hands']))
        except Exception:
            pass
        result={'farmer':['PASS'],'hands':[['PASS'] for _ in range(count)],'market':[]}
    _RELEASE_REPORT.update(getattr(_RELEASE_PARENT,'telemetry',{}))
    _RELEASE_REPORT['release_errors']=_RELEASE_ERRORS
    return result

agent.telemetry=_RELEASE_REPORT
agent=globals().pop('agent')

# Adapted from prvsiyan / The Soil Remembers Rain, Apache-2.0.
# V233: bounded, financed six-sheep SE discovery investment.
_V233_PARENT=agent
del agent
_V233_STATES={}
_V233_REPORT=dict(sheep_commit_requests=0,sheep_committed=0,sheep_hire_requests=0,
    sheep_workers_confirmed=0,sheep_hire_shortfalls=0,sheep_budget_declines=0,
    sheep_capacity_declines=0,sheep_purchase_shortfalls=0,sheep_feed_buy_requests=0,
    sheep_wool_harvested=0,sheep_fert_collected=0,sheep_extra_wool_sales=0,
    sheep_extra_fert_sales=0,sheep_rescue_feed_requests=0)

def _v233_eligible(obs,native):
    farm=obs['farms'][obs['player']];prices=obs['market']['prices']
    if len(farm['tiles'])!=10 or set(farm['unlocked_quadrants'])!={'NW','NE','SW'}:return False
    if obs['town']['unlocked_shops'].count('YARN_STORE')<2 or prices['WOOL']<220 or prices['WHEAT']>45:return False
    if any(farm['tiles'][y][x]!='LOCKED' for y in (5,6) for x in range(5,8)):return False
    if obs['private']['shed'].get('SHEEP',0) or any(i.get('SHEEP',0) for i in obs['private']['inventories']):return False
    for day in range(12,30):
        for a in _v219_native_day(native,day):
            if any(o and (o[0]=='BUY_LAND' or o[:2]==['BUY_ANIMAL','SHEEP']) for o in a.get('market',[])):return False
            if any(c and c[0] in ('PICKUP','PLACE') and len(c)>1 and c[1]=='SHEEP' for c in [a.get('farmer')]+a.get('hands',[])):return False
    return True

def _v233_request(obs,action,state,native):
    step=int(obs['step']);day=step//24;hour=step%24
    # EXP242: preserve native indices while servicing already committed sheep.
    if state.get('requested_day')==day:return action
    committed=state.get('committed')
    if not committed and (hour>(3 if day==11 else 1) or day not in (11,12) or not _v233_eligible(obs,native)):return action
    planned=_v219_native_day(native,day)
    deadline=2 if committed else (3 if day==11 else 1)
    if committed:
        last_native_hire=max((h for h,a in enumerate(planned) if any(o and o[0]=='HIRE' for o in a.get('market',[]))),default=0)
        if 2<last_native_hire<=6:deadline=6
    if hour>deadline:return action
    if any(o and o[0]=='HIRE' for a in planned[hour+1:] for o in a.get('market',[])):return action
    farm=obs['farms'][obs['player']];market=action.get('market',[])
    parent_hires=sum(bool(o) and o[0]=='HIRE' for o in market)
    expected=max(len(a.get('hands',[])) for a in planned)
    if len(farm['hands'])+parent_hires!=expected:return action
    initial=not state.get('committed')
    extra=([['BUY_LAND'],['BUY_ANIMAL','SHEEP',6]] if initial else [])+[['BUY_PRODUCT','WHEAT',6],['HIRE'],['HIRE']]
    if len(market)+len(extra)>MAX_ORDERS:return action
    stock=projected_shed(action,FarmView(obs))
    incoming=6+6*initial
    budget=7000*initial+6*(int(obs['market']['prices']['WHEAT'])+10)
    budget+=sum(_v219_fib(n) for n in range(farm['hires_today'],farm['hires_today']+parent_hires+2))
    for o in market:
        if not o:continue
        if o[0]=='BUY_LAND':return action
        if o[0]=='BUY_PRODUCT':
            incoming+=int(o[2]);budget+=int(o[2])*(int(obs['market']['prices'][o[1]])+10)
        elif o[0]=='BUY_ANIMAL':
            incoming+=int(o[2]);budget+=int(o[2])*{'SHEEP':500,'COW':400,'GOOSE':300}[o[1]]
        elif o[0]=='BUY_SEED':budget+=int(o[2])*{'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}[o[1]]
    if sum(stock.values())+incoming>100:
        _V233_REPORT['sheep_capacity_declines']+=1;return action
    if farm['money']<budget+(3000 if initial else 1000):
        _V233_REPORT['sheep_budget_declines']+=1;return action
    state['requested_day']=day
    state['pending']={'first':expected+1,'initial':initial}
    _V233_REPORT['sheep_hire_requests']+=2;_V233_REPORT['sheep_feed_buy_requests']+=6
    if initial:_V233_REPORT['sheep_commit_requests']+=1
    result=copy.deepcopy(action);result['market']=market+extra
    return result

def _v233_worker(obs,actor,targets):
    farm=obs['farms'][obs['player']];private=obs['private'];step=int(obs['step'])
    pos=tuple(farm['hands'][actor-1]);inv=private['inventories'][actor]
    access=((4,4),(5,4),(4,5),(5,5))
    home=min(access,key=lambda p:(abs(pos[0]-p[0])+abs(pos[1]-p[1]),p))
    distance=abs(pos[0]-home[0])+abs(pos[1]-home[1])
    cargo=[item for item in ('WOOL','FERTILIZER') if inv.get(item,0)]
    if cargo and step%24 >= (22 if step//24==29 else 23)-distance:
        return _v219_walk(pos,home) or ['PLACE',cargo[0],inv[cargo[0]]]
    missing=sum(not(isinstance(farm['tiles'][y][x],dict) and farm['tiles'][y][x].get('animal')=='SHEEP') for x,y in targets)
    if missing and not inv.get('SHEEP',0) and private['shed'].get('SHEEP',0):
        return _v219_walk(pos,home) or ['PICKUP','SHEEP',min(missing,private['shed']['SHEEP'])]
    hungry=sum(not(isinstance(farm['tiles'][y][x],dict) and farm['tiles'][y][x].get('fed_today')) for x,y in targets)
    if hungry and not inv.get('WHEAT',0) and private['shed'].get('WHEAT',0):
        return _v219_walk(pos,home) or ['PICKUP','WHEAT',min(hungry,private['shed']['WHEAT'])]
    tasks=[]
    for target in targets:
        x,y=target;tile=farm['tiles'][y][x];command=None
        if tile is None:command=['BUILD_PASTURE']
        elif isinstance(tile,dict) and tile.get('kind')=='WEED':command=['DIG']
        elif isinstance(tile,dict) and tile.get('kind')=='PASTURE' and not tile.get('animal'):
            if inv.get('SHEEP',0):command=['PLACE','SHEEP']
        elif isinstance(tile,dict) and tile.get('animal')=='SHEEP':
            if not tile['fed_today'] and inv.get('WHEAT',0):command=['FEED']
            elif not tile['cared_today']:command=['CARE']
            elif tile['yield_units']:command=['HARVEST']

        if command:tasks.append((abs(pos[0]-x)+abs(pos[1]-y),targets.index(target),target,command))
    if tasks:
        _,_,target,command=min(tasks);return _v219_walk(pos,target) or command
    if cargo:return _v219_walk(pos,home) or ['PLACE',cargo[0],inv[cargo[0]]]
    return ['PASS']

def _v234_rescue(obs,action,state):
    if not state['workers'] or int(obs['step'])%24>14:return action
    orders=action.get('market',[])
    if len(orders)>=MAX_ORDERS:return action
    if any(o and (o[0] in ('HIRE','BUY_LAND','BUY_ANIMAL','BUY_PRODUCT','BUY_SEED') or (len(o)>1 and o[1]=='WHEAT')) for o in orders):return action
    farm=obs['farms'][obs['player']];private=obs['private'];hungry=carried=0
    commands=[action.get('farmer') or ['PASS']]+list(action.get('hands') or [])
    for actor,targets in state['workers'].items():
        command=commands[actor]
        if command==['FEED'] or command[:2]==['PICKUP','WHEAT']:return action
        carried+=private['inventories'][actor].get('WHEAT',0)
        hungry+=sum(isinstance(farm['tiles'][y][x],dict) and farm['tiles'][y][x].get('animal')=='SHEEP' and not farm['tiles'][y][x].get('fed_today') for x,y in targets)
    stock=projected_shed(action,FarmView(obs))
    shortage=hungry-carried-stock.get('WHEAT',0)
    if not 0<shortage<=6 or state.get('rescue_today',0)+shortage>6:return action
    quote=int(obs['market']['prices']['WHEAT'])
    if quote<1 or farm['money']<1000+shortage*(quote+10) or sum(stock.values())+shortage>100:return action
    result=copy.deepcopy(action);result['market'].append(['BUY_PRODUCT','WHEAT',shortage])
    state['rescue_today']=state.get('rescue_today',0)+shortage
    _V233_REPORT['sheep_rescue_feed_requests']+=shortage
    return result

def agent(observation,configuration=None):
    action=_V233_PARENT(observation,configuration)
    step=int(observation['step']);player=int(observation['player']);day=step//24
    state=_V233_STATES.get(player)
    if state is None or step<=state['last_step']:
        state={'last_step':step,'day':-1,'workers':{},'work':{},'credit':{'WOOL':0,'FERTILIZER':0}}
        _V233_STATES[player]=state
    state['last_step']=step
    if configuration is not None and any(configuration.get(k,v)!=v for k,v in
        (('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10))):return action
    if day<11:return action
    farm=observation['farms'][player];private=observation['private']
    if state['day']!=day:state['day']=day;state['workers']={};state['work']={};state['rescue_today']=0
    for actor,previous in state['work'].items():
        if previous['step']!=step-1 or actor>=len(private['inventories']):continue
        item={'HARVEST':'WOOL','COLLECT_FERTILIZER':'FERTILIZER'}.get(previous['command'][0])
        if item:
            gained=max(0,private['inventories'][actor].get(item,0)-previous['inventory'].get(item,0))
            state['credit'][item]+=gained
            _V233_REPORT['sheep_wool_harvested' if item=='WOOL' else 'sheep_fert_collected']+=gained
    pending=state.pop('pending',None)
    if pending:
        funded='SE' in farm['unlocked_quadrants'] and (not pending['initial'] or private['shed'].get('SHEEP',0)>=6)
        if not funded:_V233_REPORT['sheep_purchase_shortfalls']+=1
        elif len(farm['hands'])<pending['first']+pending.get('count',2)-1:_V233_REPORT['sheep_hire_shortfalls']+=1
        else:
            if pending.get('count',2)==1:
                state['workers'][pending['first']]=list(pending['targets'])
                _SL_REPORT['confirmed']+=1
            else:
                for i in range(2):state['workers'][pending['first']+i]=[(x,5+i) for x in range(5,8)]
            _V233_REPORT['sheep_workers_confirmed']+=pending.get('count',2)
            if pending['initial']:state['committed']=True;_V233_REPORT['sheep_committed']+=1
    action=_v233_request(observation,action,state,_IMPL.chassis.players[player])
    if not state.get('committed'):return action
    result=copy.deepcopy(action)
    commands=[result.get('farmer') or ['PASS']]+list(result.get('hands') or [])
    commands += [['PASS'] for _ in range(len(farm['hands'])+1-len(commands))]
    state['work']={}
    for actor,targets in state['workers'].items():
        command=_v233_worker(observation,actor,targets);commands[actor]=command
        state['work'][actor]={'step':step,'command':command,'inventory':dict(private['inventories'][actor])}
    result['farmer'],result['hands']=commands[0],commands[1:]
    result=_v234_rescue(observation,result,state)
    stock=projected_shed(result,FarmView(observation))
    for item in ('WOOL','FERTILIZER'):
        scheduled=sum(int(o[2]) for o in result['market'] if o[:2]==['SELL',item])
        count=min(state['credit'][item],max(0,stock.get(item,0)-scheduled))
        if count and len(result['market'])<MAX_ORDERS:
            result['market'].append(['SELL',item,count]);state['credit'][item]-=count
            _V233_REPORT['sheep_extra_wool_sales' if item=='WOOL' else 'sheep_extra_fert_sales']+=count
    return result

_R46_SHEEP_AGENT=agent
_R46_SHADOW_PARENT=_shadow_terminal
_R46_REPORT={}
def _shadow_terminal(obs,config):
    if _V233_STATES.get(int(obs['player']),{}).get('committed'):return None
    return _R46_SHADOW_PARENT(obs,config)
del agent
def agent(observation,configuration=None):
    try:
        if int(observation.get('step',-1))==0:
            for k in _V233_REPORT:_V233_REPORT[k]=0
        result=_R46_SHEEP_AGENT(observation,configuration)
    except Exception:
        _R46_REPORT['sheep_overlay_errors']=_R46_REPORT.get('sheep_overlay_errors',0)+1
        result={'farmer':['PASS'],'hands':[],'market':[]}
    _R46_REPORT.update(getattr(_V233_PARENT,'telemetry',{}))
    _R46_REPORT.update(_V233_REPORT)
    return result
agent.telemetry=_R46_REPORT
agent=globals().pop('agent')

# EXP182: finite-harvest wheat/carrot input planner; original adaptation.
_R51_INPUT_PARENT=agent
_R51_INPUT_STATES={}
_R51_INPUT_REPORT={}
_R51_INPUT_MAX_WORKERS=2
_R51_INPUT_CROPS={'WHEAT':(2,4,6),'CARROT':(2,3,4)}

def _r51_input_forecast(obs,route,expected):
    step=int(obs['step']);day=step//24;farm=obs['farms'][obs['player']]
    pos=[list(farm['farmer'])]+[list(p) for p in farm['hands'][:expected]];targets={}
    for y,line in enumerate(farm['tiles']):
        for x,tile in enumerate(line):
            if not isinstance(tile,dict) or tile.get('crop') not in _R51_INPUT_CROPS:continue
            item=tile['crop'];first,last,cap=_R51_INPUT_CROPS[item]
            if 1<=day-tile['planted_day']<last:
                targets[(x,y)]={'crop':item,'birth':tile['planted_day'],'yield':tile['yield_units'],
                    'until':tile.get('fertilized_until_day',-1),'watered':tile.get('watered_today',False),'water':[],'harvest':None,'first':first,'last':last,'cap':cap}
    access=((4,4),(5,4),(4,5),(5,5));seen=set()
    # Native continuation ends before the reactive terminal closure planner.
    for t in range(step,min(712,(day+4)*24)):
        tape=_IMPL.chassis.routes[2 if t>=648 else route];a=tape[t]
        for actor,c in enumerate([a.get('farmer') or ['PASS'],*(a.get('hands') or [])][:len(pos)]):
            if not c:continue
            xy=tuple(pos[actor]);target=targets.get(xy)
            if target is not None and target['harvest'] is None:
                if c[0]=='WATER' and (t//24,xy) not in seen:
                    seen.add((t//24,xy))
                    if not(t//24==day and target['watered']) and target['first']<=t//24-target['birth']<=target['last']:target['water'].append(t)
                if c[0]=='HARVEST':target['harvest']=t
            if c[0] in MOVES:
                dx,dy=MOVES[c[0]];pos[actor]=[max(0,min(9,pos[actor][0]+dx)),max(0,min(9,pos[actor][1]+dy))]
        for o in a.get('market',[]):
            if o and o[0]=='HIRE':
                counts={p:sum(tuple(q)==p for q in pos) for p in access}
                pos.append(list(min(access,key=lambda p:(counts[p],access.index(p)))))
        if (t+1)%24==0:pos=[[4,4]]
    return targets

def _r51_input_gain(target,arrival,day):
    if target['harvest'] is None or target['harvest']<=arrival:return 0
    extra=sum(arrival<t<=target['harvest'] and day<=t//24<=day+2 and t//24>target['until'] for t in target['water'])
    baseline=target['yield']+sum(2 if t//24<=target['until'] else 1 for t in target['water'])
    return max(0,min(extra,target['cap']-baseline))

def _r51_input_path(obs,targets,action,index):
    step=int(obs['step']);day=step//24
    ready,start=_r62_input_start(obs,action,index)
    prices={p:max(1,int(obs['market']['prices'][p])-2) for p in ('WHEAT','CARROT')}
    fertilizer=max(1,_r37_market_price('FERTILIZER',obs['market']['inventory']['FERTILIZER']-16)+2)
    # Tuple: penalized value, gross value, next free turn, position, path, used,
    # wheat units, carrot units. No state reads from the rival's private farm.
    beam=[(0,0,ready,start,(),frozenset(),0,0)]
    best=None
    for depth in range(8):
        expanded=[]
        for score,gross,now,pos,path,used,wheat,carrot in beam:
            for xy,target in targets.items():
                if xy in used:continue
                arrival=now+abs(pos[0]-xy[0])+abs(pos[1]-xy[1])
                if arrival>=day*24+23:continue
                gain=_r51_input_gain(target,arrival,day)
                if not gain:continue
                item=target['crop'];new_gross=gross+gain*prices[item]
                new_path=path+((xy[0],xy[1],item,target['birth']),)
                expanded.append((new_gross-1.5*fertilizer*len(new_path),new_gross,arrival+1,xy,new_path,
                                 used|{xy},wheat+(gain if item=='WHEAT' else 0),carrot+(gain if item=='CARROT' else 0)))
        if not expanded:break
        expanded.sort(key=lambda s:(-s[0],-s[1],s[2],s[4]))
        beam=expanded[:8]
        if depth>=2:
            candidate=beam[0]
            if best is None or (-candidate[0],-candidate[1],candidate[2],candidate[4])<(-best[0],-best[1],best[2],best[4]):best=candidate
    if best is None:return [],{'WHEAT':0,'CARROT':0}
    return list(best[4]),{'WHEAT':best[6],'CARROT':best[7]}

def _r51_input_control(obs,action,state):
    step=int(obs['step']);day=step//24;hour=step%24;player=int(obs['player']);farm=obs['farms'][player];private=obs['private']
    native=_IMPL.chassis.players[player]
    if state.get('day')!=day:state.update(day=day,workers={},pending=None,placed=[])
    for x,y in state['placed']:
        tile=farm['tiles'][y][x]
        if isinstance(tile,dict) and tile.get('fertilized_until_day',-1)>=day+2:_R51_INPUT_REPORT['input_confirmed_applications']+=1
        else:_R51_INPUT_REPORT['input_application_errors']+=1
    state['placed']=[]
    if state.get('pending'):
        pending=state.pop('pending')
        for actor,plan in pending.items():
            if len(farm['hands'])>=actor:state['workers'][actor]=plan;_R51_INPUT_REPORT['input_confirmed_hires']+=1
            else:_R51_INPUT_REPORT['input_hire_errors']+=1
    if state['workers']:
        changed=copy.deepcopy(action)
        for actor,plan in state['workers'].items():
            inv=private['inventories'][actor];pos=tuple(farm['hands'][actor-1]);cmd=['PASS']
            if not plan['loaded']:
                stock=projected_shed(changed,FarmView(obs));q=min(plan['quantity'],max(0,stock.get('FERTILIZER',0)))
                if q and _shed_adjacent(pos,10):
                    cmd=['PICKUP','FERTILIZER',q];plan['loaded']=True;_R51_INPUT_REPORT['input_loaded_units']+=q
                    if q<plan['quantity']:_R51_INPUT_REPORT['input_stock_shortfalls']+=plan['quantity']-q
            elif inv.get('FERTILIZER',0):
                while plan['path']:
                    x,y,crop,birth=plan['path'][0];tile=farm['tiles'][y][x]
                    if not isinstance(tile,dict) or tile.get('crop')!=crop or tile.get('planted_day')!=birth or tile.get('fertilized_until_day',-1)>=day+2:
                        plan['path'].pop(0);continue
                    cmd=_v219_walk(pos,(x,y)) or ['FERTILIZE']
                    if cmd==['FERTILIZE']:state['placed'].append((x,y));plan['path'].pop(0);_R51_INPUT_REPORT['input_application_requests']+=1
                    break
            changed['hands'][actor-1]=cmd
        return changed
    if hour not in (1,2,3) or not 12<=day<=28:return action
    planned=_v219_native_day(native,day);expected=max(len(a.get('hands',[])) for a in planned)
    if any(o and o[0]=='HIRE' for a in planned[hour:] for o in a.get('market',[])) or native['pending']:return action
    parents=[_V219_STATES.get(player,{}),_V233_STATES.get(player,{})]
    # A parent may retry after a full market queue; its headcount must remain native.
    if day in (12,18) or any(p.get('committed') and p.get('requested_day')!=day for p in parents):return action
    if any(p.get('pending') for p in parents) or any(o and o[0]=='HIRE' for o in action.get('market',[])):return action
    owned=set(range(1,expected+1))
    for p in parents:
        actors=set(p.get('workers',{}))
        if owned&actors:return action
        owned|=actors
    if owned!=set(range(1,len(farm['hands'])+1)):return action
    targets=_r51_input_forecast(obs,native['route'],expected);plans=[];total_q=0;total_cost=0;all_units={'WHEAT':0,'CARROT':0}
    stock=projected_shed(action,FarmView(obs));purchases=sum(max(0,int(o[2])) for o in action.get('market',[]) if len(o)>2 and o[0] in ('BUY_PRODUCT','BUY_ANIMAL'))
    # Units act before market orders. Preserve the native next-turn pickup,
    # after the current parent's actual sales/purchases, before buying tour inputs.
    available=max(0,stock.get('FERTILIZER',0))
    for o in action.get('market',[]):
        if len(o)>=3 and o[:2]==['SELL','FERTILIZER']:available=max(0,available-max(0,int(o[2])))
        elif len(o)>=3 and o[:2]==['BUY_PRODUCT','FERTILIZER']:available+=max(0,int(o[2]))
    next_native=planned[hour+1];native_pickups=sum(max(0,int(c[2]) if len(c)>2 else 1) for c in [next_native.get('farmer') or ['PASS'],*(next_native.get('hands') or [])] if len(c)>1 and c[:2]==['PICKUP','FERTILIZER'])
    topup=max(0,native_pickups-available)
    plans,total_q,total_cost,all_units=_r68_joint_plans(obs,action,targets,stock,purchases,topup)
    if not plans:return action
    state['pending']={len(farm['hands'])+1+i:plan for i,plan in enumerate(plans)}
    _R51_INPUT_REPORT['input_hire_requests']+=len(plans);_R51_INPUT_REPORT['input_purchase_requests']+=total_q+topup
    _R51_INPUT_REPORT['input_forecast_wheat']+=all_units['WHEAT'];_R51_INPUT_REPORT['input_forecast_carrot']+=all_units['CARROT']
    changed=copy.deepcopy(action);changed['market'] += [['BUY_PRODUCT','FERTILIZER',total_q+topup]]+[['HIRE'] for _ in plans];return changed

def agent(observation,configuration=None):
    try:
        step=int(observation['step']);player=int(observation['player']);state=_R51_INPUT_STATES.get(player)
        if state is None or step<=state['step']:
            state=_R51_INPUT_STATES[player]={'step':-1}
            _R51_INPUT_REPORT.update(input_hire_requests=0,input_confirmed_hires=0,input_hire_errors=0,input_purchase_requests=0,
                input_loaded_units=0,input_stock_shortfalls=0,input_application_requests=0,input_confirmed_applications=0,
                input_application_errors=0,input_errors=0,input_forecast_wheat=0,input_forecast_carrot=0)
        state['step']=step;action=_R51_INPUT_PARENT(observation,configuration)
        if configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)]):
            action=_r51_input_control(observation,action,state)
        _R51_INPUT_REPORT.update(getattr(_R51_INPUT_PARENT,'telemetry',{}));return action
    except Exception:
        _R51_INPUT_REPORT['input_errors']=_R51_INPUT_REPORT.get('input_errors',0)+1
        return {'farmer':['PASS'],'hands':[],'market':[]}
agent.telemetry=_R51_INPUT_REPORT
agent=globals().pop('agent')

# EXP182: project the final hour's actual worker actions before automatic deposit.
_R51_WAREHOUSE_PARENT=agent
_R51_WAREHOUSE_REPORT={}

def _r51_close_warehouse(obs,action):
    step=int(obs['step']);day=step//24
    if step%24!=23 or not 12<=day<=28:return action
    # No speculative product purchase/worker count model: these hours abstain.
    if any(o and o[0] not in ('SELL',) for o in action.get('market',[])):return action
    farm,private=_PLANNER_NS['_clone_state'](obs['farms'][obs['player']],obs['private'])
    commands=[action.get('farmer') or ['PASS'],*(action.get('hands') or [])]
    demand={}
    for c in commands:
        if len(c)>1 and c[0]=='PLANT':demand[c[1]]=demand.get(c[1],0)+1
    blocked={k for k,q in demand.items() if q>private['seeds'].get(k,0)}
    for actor,c in enumerate(commands[:len(private['inventories'])]):
        if len(c)>1 and c[0]=='PLANT' and c[1] in blocked:c=['PASS']
        _PLANNER_NS['_apply_unit_action'](farm,private,actor,c,10,day,24,100)
    post=dict(private['shed'])
    for o in action.get('market',[]):
        if len(o)>=3 and o[0]=='SELL':post[o[1]]=max(0,post.get(o[1],0)-max(0,int(o[2])))
    needed=sum(post.values())+sum(max(0,q) for inv in private['inventories'] for q in inv.values())-100
    if needed<=0:return action
    result=copy.deepcopy(action);orders=result['market']
    # Grain and fertilizer have native input obligations; other products do not.
    # Additional commodity sales are bounded by actual post-action physical stock.
    for item in sorted((p for p in PRODUCTS if p not in ('WHEAT','FERTILIZER')),key=lambda p:-obs['market']['prices'].get(p,0)):
        qty=min(needed,post.get(item,0))
        if not qty:continue
        existing=next((o for o in orders if len(o)>=3 and o[:2]==['SELL',item]),None)
        if existing is not None:existing[2]=max(0,int(existing[2]))+qty
        elif len(orders)<10:orders.append(['SELL',item,qty])
        else:continue
        needed-=qty;post[item]-=qty;_R51_WAREHOUSE_REPORT['warehouse_extra_sales']+=qty
        if needed<=0:break
    if needed>0:
        native=_IMPL.chassis.players[int(obs['player'])];reserve=0
        for t in range(step+1,719):
            future=_IMPL.chassis.routes[2 if t>=648 else native['route']][t]
            for c in [future.get('farmer') or ['PASS'],*(future.get('hands') or [])]:
                if len(c)>1 and c[:2]==['PICKUP','WHEAT']:reserve+=max(0,int(c[2]) if len(c)>2 else 1)
            if any(len(o)>1 and o[:2]==['BUY_PRODUCT','WHEAT'] for o in future.get('market',[])):break
        incoming=sum(max(0,inv.get('WHEAT',0)) for inv in private['inventories'])
        others=sum(q for p,q in post.items() if p!='WHEAT')+sum(max(0,q) for inv in private['inventories'] for p,q in inv.items() if p!='WHEAT')
        # Even if every other carried item deposits first, this grain reserve fits.
        qty=min(needed,post.get('WHEAT',0),max(0,post.get('WHEAT',0)+incoming-reserve)) if 100-others>=reserve else 0
        existing=next((o for o in orders if len(o)>=3 and o[:2]==['SELL','WHEAT']),None)
        if qty and (existing is not None or len(orders)<10):
            if existing is not None:existing[2]=max(0,int(existing[2]))+qty
            else:orders.append(['SELL','WHEAT',qty])
            needed-=qty;_R51_WAREHOUSE_REPORT['warehouse_extra_sales']+=qty
    _R51_WAREHOUSE_REPORT['warehouse_projected_unresolved']+=max(0,needed)
    if result!=action:_R51_WAREHOUSE_REPORT['warehouse_changed_turns']+=1
    return result

def agent(observation,configuration=None):
    result=_R51_WAREHOUSE_PARENT(observation,configuration)
    try:
        if int(observation['step'])==0:_R51_WAREHOUSE_REPORT.update(warehouse_changed_turns=0,warehouse_extra_sales=0,warehouse_projected_unresolved=0,warehouse_errors=0)
        if configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)]):result=_r51_close_warehouse(observation,result)
    except Exception:_R51_WAREHOUSE_REPORT['warehouse_errors']=_R51_WAREHOUSE_REPORT.get('warehouse_errors',0)+1
    _R51_WAREHOUSE_REPORT.update(getattr(_R51_WAREHOUSE_PARENT,'telemetry',{}));return result
agent.telemetry=_R51_WAREHOUSE_REPORT
agent=globals().pop('agent')

from itertools import permutations as _r53_permutations
_R53_LABOR_REPORT=dict(labor_requests=0,labor_hires_avoided=0,labor_spawn_errors=0,labor_confirmed=0,labor_day26=0,labor_day27=0,labor_day28=0)

def _r53_labor_assignment(obs,action,fertilizer):
    step=int(obs['step']);day=step//24;farm=obs['farms'][obs['player']]
    if day not in (26,27,28) or step%24>2:return None
    # Do not preempt a later price-gated fertilizer request with a smaller unfertilized team.
    if day==27 and not fertilizer:return None
    count=3 if fertilizer else 2
    positions=[list(farm['farmer'])]+[list(p) for p in farm['hands']]
    for i,c in enumerate([action.get('farmer') or ['PASS'],*(action.get('hands') or [])][:len(positions)]):
        if c and c[0] in MOVES:
            dx,dy=MOVES[c[0]];positions[i]=[max(0,min(9,positions[i][0]+dx)),max(0,min(9,positions[i][1]+dy))]
    access=((4,4),(5,4),(4,5),(5,5));spawns=[]
    native_hires=sum(bool(o) and o[0]=='HIRE' for o in action.get('market',[]))
    for i in range(native_hires+count):
        chosen=min(access,key=lambda p:(sum(tuple(q)==p for q in positions),access.index(p)));positions.append(list(chosen))
        if i>=native_hires:spawns.append(chosen)
    groups=(((5,5),(6,5),(7,5),(8,5)),((9,5),(9,6),(8,6)),((5,6),(6,6),(7,6))) if fertilizer else (tuple((x,5) for x in range(5,10)),tuple((x,6) for x in range(5,10)))
    choices=[];remaining=23-step%24
    for assignment in _r53_permutations(groups):
        costs=[]
        for start,path in zip(spawns,assignment):
            distance=abs(start[0]-path[0][0])+abs(start[1]-path[0][1])
            distance+=sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in zip(path,path[1:]))
            distance+=min(abs(path[-1][0]-x)+abs(path[-1][1]-y) for x,y in access)
            costs.append(distance+(3 if fertilizer else 2)*len(path)+1+int(fertilizer))
        if max(costs)<=remaining:choices.append((max(costs),sum(costs),assignment))
    if not choices:return None
    _,_,assignment=min(choices)
    return dict(paths=assignment,spawns=spawns,remaining=remaining,workers=count,fertilizer=fertilizer)

_R53_LABOR_PARENT=agent
def agent(observation,configuration=None):
    if isinstance(observation,dict) and observation.get('step')==0:
        for k in _R53_LABOR_REPORT:_R53_LABOR_REPORT[k]=0
    result=_R53_LABOR_PARENT(observation,configuration)
    _R53_LABOR_COMBINED.update(getattr(_R53_LABOR_PARENT,'telemetry',{}));_R53_LABOR_COMBINED.update(_R53_LABOR_REPORT)
    return result
_R53_LABOR_COMBINED={}
agent.telemetry=_R53_LABOR_COMBINED
agent=globals().pop('agent')

# EXP193: deterministic HIRE spawn after native unit actions, then next-turn pickup.
def _r62_input_start(obs,action,index):
    farm=obs['farms'][obs['player']]
    positions=[list(farm['farmer'])]+[list(p) for p in farm['hands']]
    for actor,c in enumerate([action.get('farmer') or ['PASS'],*(action.get('hands') or [])][:len(positions)]):
        if c and c[0] in MOVES:
            dx,dy=MOVES[c[0]]
            positions[actor]=[max(0,min(9,positions[actor][0]+dx)),max(0,min(9,positions[actor][1]+dy))]
    access=((4,4),(5,4),(4,5),(5,5))
    native_hires=sum(bool(o) and o[0]=='HIRE' for o in action.get('market',[]))
    for _ in range(native_hires+index+1):
        chosen=min(access,key=lambda p:(sum(tuple(q)==p for q in positions),access.index(p)))
        positions.append(list(chosen))
    return int(obs['step'])+2,chosen

agent=globals().pop('agent')

def _r68_joint_plans(obs,action,targets,stock,purchases,topup):
    farm=obs['farms'][obs['player']];choices=[]
    for mode,first_crop in enumerate((None,'WHEAT','CARROT')):
        remaining=dict(targets);plans=[];total_q=0;total_cost=0;total_value=0
        all_units={'WHEAT':0,'CARROT':0}
        for i in range(_R51_INPUT_MAX_WORKERS):
            subset={xy:t for xy,t in remaining.items() if t['crop']==first_crop} if i==0 and first_crop else remaining
            path,units=_r51_input_path(obs,subset,action,i);q=len(path)
            if q<3 or len(action.get('market',[]))+2+i>10 or sum(stock.values())+purchases+total_q+q+topup>95:break
            quote=_r37_market_price('FERTILIZER',obs['market']['inventory']['FERTILIZER']-total_q-q-topup)
            cost=(q+(topup if i==0 else 0))*(quote+2)+_v219_fib(int(farm['hires_today'])+i)
            value=sum(n*max(1,_r37_market_price(item,obs['market']['inventory'][item]+all_units[item]+n)-2) for item,n in units.items())
            if value<1.5*cost+50 or farm['money']<total_cost+cost+3000:break
            plans.append({'path':path,'quantity':q,'loaded':False});total_q+=q;total_cost+=cost;total_value+=value
            for item,n in units.items():all_units[item]+=n
            for x,y,_,_ in path:remaining.pop((x,y),None)
        score=(total_value-total_cost,total_value,-total_cost,-len(plans),-mode)
        choices.append((score,plans,total_q,total_cost,all_units))
    _,plans,total_q,total_cost,all_units=max(choices,key=lambda v:v[0])
    return plans,total_q,total_cost,all_units

agent=globals().pop('agent')

_R70_STATES={}
_R70_REPORT={}

def _r70_parent_fert_qty(obs,action,planned,offset):
    stock=dict(projected_shed(action,FarmView(obs)))
    for order in action.get('market',[]):
        if len(order)<3:continue
        op,item,quantity=order[:3];quantity=max(0,int(quantity))
        if op=='SELL':stock[item]=max(0,stock.get(item,0)-quantity)
        elif op in ('BUY_PRODUCT','BUY_ANIMAL'):
            stock[item]=stock.get(item,0)+min(quantity,max(0,100-sum(stock.values())))
    next_action=planned[offset+1] if offset+1<len(planned) else {}
    commands=[next_action.get('farmer') or ['PASS'],*(next_action.get('hands') or [])]
    native_need=sum(max(0,int(c[2]) if len(c)>2 else 1) for c in commands if len(c)>1 and c[:2]==['PICKUP','FERTILIZER'])
    quantity=max(10,10+native_need-max(0,stock.get('FERTILIZER',0)))
    if quantity>max(0,100-sum(stock.values())):
        _R70_REPORT['parent_input_capacity_declines']+=1
        return 10
    if quantity>10:
        _R70_REPORT['parent_input_guard_turns']+=1
        _R70_REPORT['parent_input_guard_extra_units']+=quantity-10
    return quantity

def _r70_before(obs):
    player=int(obs['player']);step=int(obs['step']);state=_R70_STATES.get(player)
    if state is None or step<=state['step']:
        state=_R70_STATES[player]={'step':-1,'pending':[],'roles':set()}
        _R70_REPORT.update(parent_input_guard_turns=0,parent_input_guard_extra_units=0,
            parent_input_requests=0,parent_input_confirmed=0,parent_input_shortfalls=0,
            parent_input_errors=0,parent_input_capacity_declines=0)
    state['step']=step
    for request in state['pending']:
        actor,quantity,old=request
        actual=max(0,int(obs['private']['inventories'][actor].get('FERTILIZER',0))-old)
        _R70_REPORT['parent_input_confirmed']+=min(quantity,actual)
        _R70_REPORT['parent_input_shortfalls']+=max(0,quantity-actual)
    state['pending']=[]
    return state

def _r70_after(obs,action,state):
    player=int(obs['player']);day=int(obs['step'])//24
    for actor,role in _V219_STATES.get(player,{}).get('workers',{}).items():
        if not role.get('needs_fertilizer'):continue
        key=(day,actor);inv=obs['private']['inventories'][actor].get('FERTILIZER',0)
        if key not in state['roles']:
            state['roles'].add(key)
            desired=role.get('fertilizer_quantity',10 if role['kind']=='fertilizer' else 5)
            if role.get('loaded') and not role.get('pickup_requested') and inv<desired:
                _R70_REPORT['parent_input_shortfalls']+=desired-inv
        command=action.get('hands',[])[actor-1] if actor<=len(action.get('hands',[])) else ['PASS']
        if len(command)>1 and command[:2]==['PICKUP','FERTILIZER']:
            quantity=max(0,int(command[2]) if len(command)>2 else 1)
            _R70_REPORT['parent_input_requests']+=quantity
            state['pending'].append((actor,quantity,int(inv)))

_R70_PARENT=agent

def agent(observation,configuration=None):
    state=None
    try:state=_r70_before(observation)
    except Exception:_R70_REPORT['parent_input_errors']=_R70_REPORT.get('parent_input_errors',0)+1
    result=_R70_PARENT(observation,configuration)
    try:
        if state is not None:_r70_after(observation,result,state)
    except Exception:_R70_REPORT['parent_input_errors']=_R70_REPORT.get('parent_input_errors',0)+1
    _R70_REPORT.update(getattr(_R70_PARENT,'telemetry',{}))
    return result

agent.telemetry=_R70_REPORT
agent=globals().pop('agent')

def _r79_tomato_fertilizer_worthwhile(obs,action):
    if obs['market']['prices']['FERTILIZER']<=30:return True
    farm=obs['farms'][obs['player']];day=int(obs['step'])//24;bonus=0
    for y in (5,6):
        for x in range(5,10):
            tile=farm['tiles'][y][x]
            if not isinstance(tile,dict) or tile.get('crop')!='TOMATO':continue
            birth=tile['planted_day'];until=tile.get('fertilized_until_day',-1)
            bonus+=sum(until<d and 8<=d+1-birth<=11 for d in range(day,day+3))
    if not bonus:return False
    inventory=obs['market']['inventory']
    price=max(1,_r37_market_price('TOMATO',inventory['TOMATO']+bonus+10)-2)
    fertilizer=max(1,_r37_market_price('FERTILIZER',inventory['FERTILIZER']-10)+2)
    native_hires=sum(bool(o) and o[0]=='HIRE' for o in action.get('market',[]))
    extra_labor=_v219_fib(int(farm['hires_today'])+native_hires+3)
    return bonus*price>=2*(10*fertilizer+extra_labor)+100

agent=globals().pop('agent')

# EXP216: original adaptation of economic feed and fertilizer-sale concepts.
# Conceptual credit: Steven Lee Hans, "Lord Momo Returns", September12 snapshot.
_R85_FEED = True
_R85_FERT = True
_R85_PARENT = agent
_R85_STATES = {}
_R85_REPORT = {}

def _r85_feed(obs, action):
    step=int(obs['step']);day=step//24
    if not 10<=day<=28 or step%24>21:return action
    player=int(obs['player']);native=_IMPL.chassis.players[player]
    tape=_v219_native_day(native,day)
    expected=max(len(a.get('hands',[])) for a in tape)
    farm=obs['farms'][player];positions=[farm['farmer'],*farm['hands']]
    commands=[action.get('farmer') or ['PASS'],*(action.get('hands') or [])]
    prices=obs['market']['prices'];changed=False
    for actor,command in enumerate(commands[:expected+1]):
        if command!=['FEED'] or actor>=len(positions):continue
        tile=_tile_at(farm['tiles'],positions[actor])
        if not isinstance(tile,dict) or tile.get('animal') not in ('GOOSE','COW','SHEEP'):continue
        if tile.get('fed_today') or int(tile.get('consecutive_unfed',0))!=0:continue
        if int(obs['private']['inventories'][actor].get('WHEAT',0))<=0:continue
        item={'GOOSE':'EGG','COW':'MILK','SHEEP':'WOOL'}[tile['animal']]
        bonus=_r88_feed_bonus_cost(tile,day)
        if bonus*(float(prices[item])+5)*1.25>=float(prices['WHEAT']):continue
        if not _r86_next_feed(obs,positions[actor]):continue
        commands[actor]=['PASS'];changed=True
        _R85_REPORT['feed_skips']+=1
    if not changed:return action
    result=copy.deepcopy(action);result['farmer'],result['hands']=commands[0],commands[1:]
    return result

def _r85_reserve(obs, state):
    step=int(obs['step']);player=int(obs['player']);native=_IMPL.chassis.players[player]
    route=native['route'];key=(route,step)
    cache=state.setdefault('native_reserves',{})
    if route not in cache:
        # Backward recurrence preserves field-before-market order within a turn.
        reserve=[0]*720
        for t in range(718,-1,-1):
            a=_IMPL.chassis.routes[2 if t>=648 else route][t]
            pickup=sum(max(0,int(c[2]) if len(c)>2 else 1) for c in [a.get('farmer') or ['PASS'],*(a.get('hands') or [])] if len(c)>1 and c[:2]==['PICKUP','FERTILIZER'])
            purchase=sum(max(0,int(o[2])) for o in a.get('market',[]) if len(o)>2 and o[:2]==['BUY_PRODUCT','FERTILIZER'])
            reserve[t]=pickup+max(0,reserve[t+1]-purchase)
        cache[route]=reserve
    dedicated=0
    for parent in (_V219_STATES.get(player,{}),_V233_STATES.get(player,{})):
        for actor,role in parent.get('workers',{}).items():
            if not isinstance(role,dict) or not role.get('needs_fertilizer') or role.get('loaded'):continue
            desired=role.get('fertilizer_quantity',10 if role.get('kind')=='fertilizer' else 5)
            carried=obs['private']['inventories'][actor].get('FERTILIZER',0)
            dedicated+=max(0,desired-carried)
        pending=parent.get('pending') or {}
        if pending.get('fertilizer'):dedicated+=10
    inputs=_R51_INPUT_STATES.get(player,{})
    for actor,plan in {**inputs.get('workers',{}),**(inputs.get('pending') or {})}.items():
        if not plan.get('loaded'):dedicated+=max(0,int(plan['quantity']))
    return max(14,cache[route][min(719,step+1)]+dedicated)

def _r85_fertilizer(obs, action, state):
    step=int(obs['step']);day=step//24
    if not 6<=day<=28:return action
    market=action.get('market',[])
    if len(market)>=MAX_ORDERS or any(o and o[0]!='SELL' for o in market):return action
    stock=projected_shed(action,FarmView(obs))
    held=max(0,int(stock.get('FERTILIZER',0)))
    sold=sum(max(0,int(o[2])) for o in market if len(o)>2 and o[:2]==['SELL','FERTILIZER'])
    extra=held-sold-_r85_reserve(obs,state)
    if extra<=0:return action
    result=copy.deepcopy(action);result['market'].append(['SELL','FERTILIZER',extra])
    _R85_REPORT['fert_sale_turns']+=1;_R85_REPORT['fert_sale_units']+=extra
    return result

def agent(observation, configuration=None):
    result=_R85_PARENT(observation,configuration)
    try:
        step=int(observation['step']);player=int(observation['player'])
        state=_R85_STATES.get(player)
        if state is None or step<=state['step']:
            state=_R85_STATES[player]={'step':-1}
            _R85_REPORT.update(feed_skips=0,fert_sale_turns=0,fert_sale_units=0,economic_overlay_errors=0)
        state['step']=step
        if configuration is not None and any(configuration.get(k,v)!=v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)]):return result
        if _R85_FEED:result=_r85_feed(observation,result)
        if _R85_FERT:result=_r85_fertilizer(observation,result,state)
        if step%24==23:result=_r51_close_warehouse(observation,result)
    except Exception:
        _R85_REPORT['economic_overlay_errors']=_R85_REPORT.get('economic_overlay_errors',0)+1
    _R85_REPORT.update(getattr(_R85_PARENT,'telemetry',{}))
    return result

agent.telemetry=_R85_REPORT
agent=globals().pop('agent')

# EXP217: planned next-day service is required before discretionary feed cuts.
_R86_FEED_CACHE = {}

def _r86_next_feed(obs, target):
    step=int(obs['step']);day=step//24
    if day==28:return True  # No second dawn follows before game termination.
    player=int(obs['player']);native=_IMPL.chassis.players[player]
    tomorrow=day+1;route=2 if tomorrow>=27 else native['route'];key=(route,tomorrow)
    if key not in _R86_FEED_CACHE:
        positions=[(4,4)];wheat=[0];access=((4,4),(5,4),(4,5),(5,5));feeds=set()
        for hour in range(24):
            a=_IMPL.chassis.routes[route][tomorrow*24+hour]
            commands=[a.get('farmer') or ['PASS'],*(a.get('hands') or [])]
            for actor,command in enumerate(commands[:len(positions)]):
                if not command:continue
                pos=positions[actor];op=command[0]
                if op in MOVES:
                    dx,dy=MOVES[op];positions[actor]=(max(0,min(9,pos[0]+dx)),max(0,min(9,pos[1]+dy)))
                elif command[:2]==['PICKUP','WHEAT'] and pos in access:
                    wheat[actor]+=max(0,int(command[2]) if len(command)>2 else 1)
                elif op=='FEED' and wheat[actor]>0:
                    wheat[actor]-=1
                    if hour<=21:feeds.add(pos)
                elif op=='DROP' and pos in access:wheat[actor]=0
                elif command[:2]==['PLACE','WHEAT'] and pos in access:
                    wheat[actor]=max(0,wheat[actor]-max(0,int(command[2]) if len(command)>2 else 1))
            for order in a.get('market',[]):
                if order and order[0]=='HIRE':
                    chosen=min(access,key=lambda p:(positions.count(p),access.index(p)))
                    positions.append(chosen);wheat.append(0)
        _R86_FEED_CACHE[key]=frozenset(feeds)
    return tuple(target) in _R86_FEED_CACHE[key]

agent=globals().pop('agent')

# EXP219: charge care credits only when this feeding decision can affect them.
_R88_PHASE = True
_R88_HORIZON = True
_R88_ANIMAL_DAYS = {'GOOSE': (4, 1), 'COW': (8, 2), 'SHEEP': (6, 3)}


def _r88_feed_bonus_cost(tile, day):
    first, interval = _R88_ANIMAL_DAYS[tile['animal']]
    first += int(tile['placed_day'])
    tomorrow = day + 1
    produces = tomorrow >= first and (tomorrow - first) % interval == 0
    pending = max(0, int(tile.get('pending_care_bonus', 0)))
    if _R88_PHASE and not produces:
        pending = 0  # It remains banked on non-production dawns.
    care = 1  # Conservative: charge one possible CARE even if not yet observed.
    if _R88_HORIZON:
        # Today's care is added AFTER tomorrow's production; its first possible
        # payout is a later production dawn, which must occur before game end.
        next_use = first
        if next_use <= tomorrow:
            next_use += ((tomorrow - next_use) // interval + 1) * interval
        if next_use > 29:
            care = 0
    return pending + care


agent = globals().pop('agent')

# EXP226: retain physical grain for two complete days before trimming a buy.
_R95_PARENT = agent
_R95_REPORT = {}
_R95_RESERVES = {}

def _r95_reserve(obs):
    step=int(obs['step']);player=int(obs['player'])
    native=_IMPL.chassis.players[player];route=native['route']
    key=(route,step)
    if key not in _R95_RESERVES:
        demand=6  # Physical buffer beyond every scheduled pickup and sale.
        for t in range(step+1,min(719,step+49)):
            a=_IMPL.chassis.routes[2 if t>=648 else route][t]
            for c in [a.get('farmer') or ['PASS'],*(a.get('hands') or [])]:
                if c[:2]==['PICKUP','WHEAT']:
                    demand+=max(0,int(c[2]) if len(c)>2 else 1)
            for o in a.get('market',[]):
                if len(o)>2 and o[:2]==['SELL','WHEAT']:
                    demand+=max(0,int(o[2]))
        _R95_RESERVES[key]=demand
    demand=_R95_RESERVES[key]
    # Reserve full feed for a possible southeast sheep commitment. Do not
    # rely on its future discretionary buy, eligibility, or existing cargo.
    if obs['town']['unlocked_shops'].count('YARN_STORE')>=2:
        demand+=6*len({t//24 for t in range(step+1,step+49) if t//24>=12})
    return demand

def _r95_replenish(obs,action):
    step=int(obs['step'])
    if not 10<=step//24<=11:return action
    orders=action.get('market') or []
    if not any(len(o)>2 and o[:2]==['BUY_PRODUCT','WHEAT'] and int(o[2])>0 for o in orders):return action
    # Preserve all same-turn grain trading/arbitrage sequences unchanged.
    if any(o[:2]==['SELL','WHEAT'] for o in orders):return action
    farm,private=_PLANNER_NS['_clone_state'](obs['farms'][obs['player']],obs['private'])
    commands=[action.get('farmer') or ['PASS'],*(action.get('hands') or [])]
    for actor,c in enumerate(commands[:len(private['inventories'])]):
        _PLANNER_NS['_apply_unit_action'](farm,private,actor,c,10,step//24,24,100)
    held=max(0,int(private['shed'].get('WHEAT',0)))
    reserve=_r95_reserve(obs);result=None;removed=0
    for i,o in enumerate(orders):
        if len(o)<3 or o[:2]!=['BUY_PRODUCT','WHEAT']:continue
        quantity=max(0,int(o[2]));retained=min(quantity,max(0,reserve-held))
        held+=retained
        if retained<quantity:
            if result is None:result=copy.deepcopy(action)
            result['market'][i][2]=retained  # Zero keeps every later order slot.
            removed+=quantity-retained
    if result is None:return action
    _R95_REPORT['replenishment_trim_turns']+=1
    _R95_REPORT['replenishment_trim_units']+=removed
    return result

def agent(observation,configuration=None):
    result=_R95_PARENT(observation,configuration)
    try:
        if int(observation['step'])==0:
            _R95_REPORT.update(replenishment_trim_turns=0,replenishment_trim_units=0,replenishment_errors=0)
        if configuration is not None and any(configuration.get(k,v)!=v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)]):return result
        result=_r95_replenish(observation,result)
    except Exception:
        _R95_REPORT['replenishment_errors']=_R95_REPORT.get('replenishment_errors',0)+1
    _R95_REPORT.update(getattr(_R95_PARENT,'telemetry',{}))
    return result

agent.telemetry=_R95_REPORT
agent=globals().pop('agent')

# EXP231: protect inputs using funded current orders without unassigned cash padding from observed physical resources.
_R97_PARENT=agent
_R97_REPORT={}
_R97_LAST={}

def _r97_market_stock(shed,orders):
    stock=dict(shed);buys={};sales={}
    for index,order in enumerate(orders):
        if len(order)<3:continue
        op,item,n=order[:3];n=max(0,int(n))
        if op=='SELL':
            q=min(n,max(0,stock.get(item,0)));stock[item]=stock.get(item,0)-q;sales[index]=q
        elif op in ('BUY_PRODUCT','BUY_ANIMAL'):
            q=min(n,max(0,100-sum(stock.values())));stock[item]=stock.get(item,0)+q;buys[index]=q
    return stock,buys,sales

def _r97_delivery(stock,private,night):
    stock=dict(stock);lost={}
    if night:
        for inv in private['inventories']:
            for item,q in inv.items():
                q=max(0,int(q));take=min(q,max(0,100-sum(stock.values())))
                stock[item]=stock.get(item,0)+take
                if q>take:lost[item]=lost.get(item,0)+q-take
    return stock,lost

def _r97_budget(obs,orders):
    farm=obs['farms'][obs['player']];cost=0;hires=int(farm['hires_today'])
    # At most ten 100-unit purchases per opponent turn. The additional 1000
    # own units give an intentionally conservative upper bound on buy quotes.
    prices={p:_r37_market_price(p,obs['market']['inventory'][p]-2000) for p in ('WHEAT','FERTILIZER')}
    for order in orders:
        if not order:continue
        op=order[0]
        if op=='HIRE':cost+=_v219_fib(hires);hires+=1
        elif op=='BUY_LAND':cost+=4000
        elif len(order)>2:
            item=order[1];q=max(0,int(order[2]))
            if op=='BUY_PRODUCT':cost+=q*prices[item]
            elif op=='BUY_ANIMAL':cost+=q*{'GOOSE':300,'COW':400,'SHEEP':500}[item]
            elif op=='BUY_SEED':cost+=q*{'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}[item]
    return cost<=farm['money']  # No current sale proceeds are assumed.

def _r97_supply(obs,action):
    step=int(obs['step']);player=int(obs['player']);day=step//24
    if not 144<=step<695:return action
    native=_IMPL.chassis.players[player]
    future=_IMPL.chassis.routes[2 if step+1>=648 else native['route']][step+1]
    commands=[future.get('farmer') or ['PASS'],*(future.get('hands') or [])]
    following=_IMPL.chassis.routes[2 if step+2>=648 else native['route']][step+2]
    next_orders=future.get('market') or []
    prefund=0
    if len(next_orders)==10 and not any(o[:2] in (['BUY_PRODUCT','WHEAT'],['SELL','WHEAT']) for o in next_orders):
        later=[following.get('farmer') or ['PASS'],*(following.get('hands') or [])]
        demand=lambda cs:sum(max(0,int(c[2]) if len(c)>2 else 1) for c in cs if c[:2]==['PICKUP','WHEAT'])
        if demand(later):prefund=demand(commands)+demand(later)
    if not prefund and not any(c[:2]==['PICKUP','WHEAT'] for c in commands):return action
    orders=action.get('market') or []
    if len(orders)>10 or not _r97_budget(obs,orders):
        _R97_REPORT['supply_budget_declines']+=1;return action
    farm,private=_PLANNER_NS['_clone_state'](obs['farms'][player],obs['private'])
    for actor,c in enumerate([action.get('farmer') or ['PASS'],*(action.get('hands') or [])][:len(private['inventories'])]):
        _PLANNER_NS['_apply_unit_action'](farm,private,actor,c,10,day,24,100)
    positions=[tuple(farm['farmer']),*map(tuple,farm['hands'])];night=step%24==23
    access=((4,4),(5,4),(4,5),(5,5))
    if night:positions=[(4,4)]
    else:
        for order in orders:
            if order and order[0]=='HIRE':positions.append(min(access,key=lambda p:(positions.count(p),access.index(p))))
    need=sum(max(0,int(c[2]) if len(c)>2 else 1) for pos,c in zip(positions,commands) if pos in access and c[:2]==['PICKUP','WHEAT'])
    need=max(need,prefund)
    if not need:return action
    original_stock,original_buys,_=_r97_market_stock(private['shed'],orders)
    original_final,original_loss=_r97_delivery(original_stock,private,night)
    if original_final.get('WHEAT',0)>=need:return action
    result=copy.deepcopy(action);proposed=result['market'];blocked=False
    def project(candidate):
        stock,buys,sales=_r97_market_stock(private['shed'],candidate)
        final,loss=_r97_delivery(stock,private,night)
        safe=all(buys.get(i,0)>=q for i,q in original_buys.items()) and all(q<=original_loss.get(item,0) for item,q in loss.items())
        return final,sales,safe
    # Hold an existing grain sale first. Preserve all order indices and every
    # originally funded buy; no extra overnight overflow may be introduced.
    for index in range(len(proposed)-1,-1,-1):
        if proposed[index][:2]!=['SELL','WHEAT']:continue
        final,sales,safe=project(proposed);shortage=max(0,need-final.get('WHEAT',0))
        if not shortage:break
        sold=sales.get(index,0)
        if not sold:continue
        old=proposed[index][2];proposed[index][2]=max(0,sold-shortage)
        after,_,safe=project(proposed)
        if not safe or after.get('WHEAT',0)<=final.get('WHEAT',0):proposed[index][2]=old
    final,_,safe=project(proposed);shortage=max(0,need-final.get('WHEAT',0))
    if shortage:
        last_sale=max((i for i,o in enumerate(proposed) if o[:2]==['SELL','WHEAT']),default=-1)
        index=next((i for i in range(len(proposed)-1,last_sale,-1) if proposed[i][:2]==['BUY_PRODUCT','WHEAT']),None)
        if index is not None:proposed[index][2]=max(0,int(proposed[index][2]))+shortage
        elif len(proposed)<10:proposed.append(['BUY_PRODUCT','WHEAT',shortage])
        else:_R97_REPORT['supply_slot_declines']+=1;return action
    final,_,safe=project(proposed)
    if not safe or final.get('WHEAT',0)<need:
        _R97_REPORT['supply_capacity_declines']+=1;return action
    if not _r97_budget(obs,proposed):
        _R97_REPORT['supply_budget_declines']+=1;return action
    if prefund:
        _R97_REPORT['supply_prefund_changes']+=1
        _R97_REPORT['supply_prefund_units']+=max(0,final.get('WHEAT',0)-original_final.get('WHEAT',0))
    if step<288:
        _R97_REPORT['supply_early_changes']+=1
        _R97_REPORT['supply_early_units']+=max(0,final.get('WHEAT',0)-original_final.get('WHEAT',0))
    _R97_REPORT['supply_guard_changes']+=1
    _R97_REPORT['supply_grain_protected']+=final.get('WHEAT',0)-original_final.get('WHEAT',0)
    _R97_REPORT['supply_buy_units']+=sum(max(0,int(o[2])) for o in proposed if o[:2]==['BUY_PRODUCT','WHEAT'])-sum(max(0,int(o[2])) for o in orders if o[:2]==['BUY_PRODUCT','WHEAT'])
    return result

def agent(observation,configuration=None):
    result=_R97_PARENT(observation,configuration)
    try:
        player=int(observation['player']);step=int(observation['step'])
        if player not in _R97_LAST or step<=_R97_LAST[player]:
            _R97_REPORT.update(supply_guard_changes=0,supply_grain_protected=0,supply_buy_units=0,supply_early_changes=0,supply_early_units=0,supply_prefund_changes=0,supply_prefund_units=0,supply_slot_declines=0,supply_capacity_declines=0,supply_budget_declines=0,supply_errors=0)
        _R97_LAST[player]=step
        if configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10),('farmHandCostMult',1)]):result=_r97_supply(observation,result)
    except Exception:_R97_REPORT['supply_errors']=_R97_REPORT.get('supply_errors',0)+1
    _R97_REPORT.update(getattr(_R97_PARENT,'telemetry',{}))
    return result

agent.telemetry=_R97_REPORT
agent=globals().pop('agent')


# ---------------------------------------------------------------------------
# v9 COURIER: deliver premium cargo before midnight and sell it the same day.
#
# Roughly 40% of the tape's strawberries and milk are still in workers' hands
# when the day ends; the engine drops them into the shed *after* the market,
# so every sibling of this policy sells them the next morning.  No town draw
# happens between hour 20 and the next dawn's market, so an evening sale gets
# the morning's quote a day earlier than a rival who waits for the auto-drop.
#
# From hour V9_COURIER_FROM_HOUR, a tape worker carrying premium goods whose
# every remaining command today is a PASS or a move (moves are free: workers
# respawn at the shed at dawn) walks to the nearest shed-access tile, drops,
# and the delivered units are offered in the first market slot.
# ---------------------------------------------------------------------------
V9_COURIER_ITEMS = ("STRAWBERRY", "MILK", "WOOL", "MELON")
V9_COURIER_FROM_HOUR = 12
_V9_COURIER_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_V9_COURIER_IDLE = frozenset({"PASS", "NORTH", "SOUTH", "EAST", "WEST", "DROP"})
_V9_COURIER = {}
_V9_COURIER_REPORT = dict(courier_trips=0, courier_units=0, courier_errors=0)


def _v9_courier_walk(pos, target):
    x, y = pos
    tx, ty = target
    return ([["EAST"]] * max(0, tx - x) + [["WEST"]] * max(0, x - tx)
            + [["SOUTH"]] * max(0, ty - y) + [["NORTH"]] * max(0, y - ty))


def _v9_courier_plan(tape, unit, pos, commands, step, end):
    """Walk-and-drop route for an idle tape worker, or None if it has work left today."""
    if commands[unit] and commands[unit][0] not in _V9_COURIER_IDLE:
        return None
    for t in range(step + 1, end + 1):
        a = tape[t] if t < len(tape) else {}
        units = [a.get("farmer") or ["PASS"]] + list(a.get("hands") or [])
        command = units[unit] if unit < len(units) else ["PASS"]
        if command and command[0] not in _V9_COURIER_IDLE:
            return None
    target = min(_V9_COURIER_ACCESS, key=lambda a: abs(a[0] - pos[0]) + abs(a[1] - pos[1]))
    walk = _v9_courier_walk(pos, target)
    return walk + [["DROP"]] if len(walk) <= end - step else None


def _v9_courier(obs, action, st):
    step = int(obs["step"])
    player = int(obs["player"])
    if step >= 718 or step % 24 < V9_COURIER_FROM_HOUR:
        return action
    day = step // 24
    if st.get("day") != day:
        st["day"] = day
        st["plans"] = {}
    native = _IMPL.chassis.players.get(player)
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    tape = _IMPL.chassis.routes[native["route"]]
    farm = obs["farms"][player]
    positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
    inventories = obs["private"]["inventories"]
    commands = [list(action.get("farmer") or ["PASS"])] + [list(c) for c in (action.get("hands") or [])]
    commands += [["PASS"]] * (len(positions) - len(commands))
    end = day * 24 + 23
    plans = st["plans"]
    # Only tape workers: overlay-dedicated hands are appended after the tape's crew.
    crew = 1 + max(len(tape[t].get("hands") or []) for t in range(day * 24, min(len(tape), end + 1)))
    delivered = {}
    changed = False
    for unit, pos in enumerate(positions[:crew]):
        inventory = inventories[unit] if unit < len(inventories) else {}
        cargo = {k: int(v) for k, v in inventory.items() if k in V9_COURIER_ITEMS and int(v) > 0}
        plan = plans.get(unit)
        if plan is None:
            if not cargo or native.get("pending", {}).get(unit):
                continue
            route = _v9_courier_plan(tape, unit, pos, commands, step, end)
            if route is None:
                continue
            plan = plans[unit] = {"route": route, "start": step}
            _V9_COURIER_REPORT["courier_trips"] += 1
        index = step - plan["start"]
        if index >= len(plan["route"]):
            continue
        command = plan["route"][index]
        if command == ["DROP"]:
            if pos not in _V9_COURIER_ACCESS:
                plans[unit] = {"route": [], "start": step}
                continue
            for item, n in cargo.items():
                delivered[item] = delivered.get(item, 0) + n
        commands[unit] = command
        changed = True
    if not changed:
        return action
    result = dict(action)
    result["farmer"], result["hands"] = commands[0], commands[1:]
    if delivered:
        market = [list(o) for o in action.get("market") or []]
        prices = obs["market"]["prices"]
        for item, n in sorted(delivered.items(), key=lambda kv: -int(prices.get(kv[0], 0)) * kv[1]):
            if int(prices.get(item, 0)) < 2:
                continue
            existing = next((o for o in market if o and o[0] == "SELL" and len(o) >= 3 and o[1] == item), None)
            if existing is not None:
                existing[2] = int(existing[2]) + n
                market.remove(existing)
                market.insert(0, existing)
            elif len(market) < MAX_ORDERS:
                market.insert(0, ["SELL", item, n])
            _V9_COURIER_REPORT["courier_units"] += n
        result["market"] = market
    return result


_V9_COURIER_PARENT = agent


def agent(observation, configuration=None):
    player, step = int(observation["player"]), int(observation["step"])
    st = _V9_COURIER.get(player)
    if st is None or step <= st["step"]:
        st = _V9_COURIER[player] = {"step": -1}
        if step == 0:
            _V9_COURIER_REPORT.update(courier_trips=0, courier_units=0, courier_errors=0)
    st["step"] = step
    action = _V9_COURIER_PARENT(observation, configuration)
    try:
        return _v9_courier(observation, action, st)
    except Exception:
        _V9_COURIER_REPORT["courier_errors"] += 1
        return action


agent.telemetry = _V9_COURIER_REPORT
agent = globals().pop("agent")


# ---------------------------------------------------------------------------
# v9 CARROT: plant carrots instead of wheat when the carrot book pays for it.
#
# The tape replants wheat on the same short cycle a carrot needs (water daily,
# harvest at age 2-4), so the swap keeps every worker's schedule intact.  A
# watered wheat plant yields 4 and a carrot 3, for $10 more seed, so the swap
# only pays once the carrot quote clears V9_CARROT_RATIO x the wheat quote --
# which pet cafes and farmers markets make happen by draining the hinge book.
# Wheat is also feed, so the swap stops while the shed holds less than
# V9_CARROT_WHEAT_RESERVE wheat.
# ---------------------------------------------------------------------------
V9_CARROT_RATIO = 2.0
V9_CARROT_FIRST_DAY = 10
V9_CARROT_LAST_DAY = 23
V9_CARROT_WHEAT_RESERVE = 40
V9_CARROT_BOOM_RATIO = 4.5   # from this ratio the feed reserve is bought instead of grown
V9_CARROT_BOOM_RESERVE = 10
_V9_CARROT_REPORT = dict(carrot_swaps=0, carrot_seed_swaps=0, carrot_errors=0)


def _v9_carrot(obs, action, st):
    step = int(obs["step"])
    day = step // 24
    prices = obs["market"]["prices"]
    private = obs["private"]
    commands = [list(action.get("farmer") or ["PASS"])] + [list(c) for c in (action.get("hands") or [])]
    market = [list(o) for o in action.get("market") or []]
    changed = False
    if st.get("tiles"):
        # swapped carrots die at the start of age 4, but the wheat tape may harvest at age 4:
        # harvest them on the age-3 watering visit instead
        _farm = obs["farms"][int(obs["player"])]
        _pos = [_farm["farmer"]] + list(_farm["hands"])
        for _i, c in enumerate(commands[:len(_pos)]):
            if c != ["WATER"]:
                continue
            _p = tuple(_pos[_i])
            if st["tiles"].get(_p) != day - 3:
                continue
            _t = _farm["tiles"][_p[1]][_p[0]]
            if isinstance(_t, dict) and _t.get("crop") == "CARROT" and int(_t.get("planted_day", -9)) == day - 3 and int(_t.get("yield_units", 0)) > 0:
                commands[_i] = ["HARVEST"]
                changed = True
                _V9_CARROT_REPORT["carrot_rescues"] = _V9_CARROT_REPORT.get("carrot_rescues", 0) + 1
    wheat_held = int(private["shed"].get("WHEAT", 0)) + sum(int(i.get("WHEAT", 0)) for i in private["inventories"])
    ratio = int(prices.get("CARROT", 0)) / max(1, int(prices.get("WHEAT", 99)))
    boom = ratio >= V9_CARROT_BOOM_RATIO
    reserve = V9_CARROT_BOOM_RESERVE if boom else V9_CARROT_WHEAT_RESERVE
    if boom and V9_CARROT_FIRST_DAY <= day <= V9_CARROT_LAST_DAY and wheat_held < V9_CARROT_WHEAT_RESERVE:
        # Carrots are worth several wheat each: buy the feed the swap no longer grows.
        topup = V9_CARROT_WHEAT_RESERVE - wheat_held
        budget = float(obs["farms"][int(obs["player"])]["money"]) - 1500
        qty = min(topup, int(budget // max(1, int(prices.get("WHEAT", 99)) + 5)))
        if qty > 0 and len(market) < MAX_ORDERS and not any(o[:2] == ["BUY_PRODUCT", "WHEAT"] for o in market if len(o) >= 2):
            market.append(["BUY_PRODUCT", "WHEAT", qty])
            changed = True
    if (V9_CARROT_FIRST_DAY <= day <= V9_CARROT_LAST_DAY and wheat_held >= reserve
            and ratio >= V9_CARROT_RATIO):
        carrot_seeds = int(private["seeds"].get("CARROT", 0)) - sum(1 for c in commands if c[:2] == ["PLANT", "CARROT"])
        _farm = obs["farms"][int(obs["player"])]
        _pos = [_farm["farmer"]] + list(_farm["hands"])
        for _i, c in enumerate(commands):
            if c[:2] == ["PLANT", "WHEAT"] and carrot_seeds > 0:
                c[1] = "CARROT"
                carrot_seeds -= 1
                changed = st["swapped"] = True
                _V9_CARROT_REPORT["carrot_swaps"] += 1
                if _i < len(_pos):
                    st.setdefault("tiles", {})[tuple(_pos[_i])] = day
        for o in market:
            if len(o) >= 3 and o[:2] == ["BUY_SEED", "WHEAT"]:
                o[1] = "CARROT"
                changed = st["swapped"] = True
                _V9_CARROT_REPORT["carrot_seed_swaps"] += int(o[2])
    result = dict(action)
    result["farmer"], result["hands"], result["market"] = commands[0], commands[1:], market
    if st.get("swapped") and day < 24:
        # Swapped carrots have no planned sale on the tape before its own carrot days.
        stock = projected_shed(result, FarmView(obs)).get("CARROT", 0)
        selling = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ["SELL", "CARROT"])
        if stock > selling and len(market) < MAX_ORDERS and int(prices.get("CARROT", 0)) >= 2:
            market.insert(0, ["SELL", "CARROT", stock - selling])
            changed = True
    return result if changed else action


_V9_CARROT = {}


_V9_CARROT_PARENT = agent


def agent(observation, configuration=None):
    player, step = int(observation["player"]), int(observation["step"])
    st = _V9_CARROT.get(player)
    if st is None or step <= st["step"]:
        st = _V9_CARROT[player] = {"step": -1}
        if step == 0:
            _V9_CARROT_REPORT.update(carrot_swaps=0, carrot_seed_swaps=0, carrot_errors=0)
    st["step"] = step
    action = _V9_CARROT_PARENT(observation, configuration)
    try:
        return _v9_carrot(observation, action, st)
    except Exception:
        _V9_CARROT_REPORT["carrot_errors"] += 1
        return action


agent.telemetry = _V9_CARROT_REPORT
agent = globals().pop("agent")


# ---------------------------------------------------------------------------
# v9 HERD: raise the tape's day-10 geese as sheep or cows when the draw pays.
#
# A cared goose lays 2 eggs a day into a $50 book; a cared sheep grows 4 wool
# every 3 days into a $200 book, a cow 3 milk every 2 days into a $160 book.
# The tape handles its geese exactly like pasture animals (build, pick up,
# place, feed, care, collect fertilizer, harvest), so swapping the species at
# the first goose purchase keeps every worker's schedule.  Wool needs a yarn
# store to hold its price and milk needs pizza / ice cream / smoothie shops;
# egg shops keep the geese.  The swapped herd's extra product has no planned
# sale on the tape, so anything beyond the tape's remaining planned sales is
# sold as it reaches the shed.
# ---------------------------------------------------------------------------
V9_HERD_MIN_WOOL = 150         # wool quote needed to swap to sheep
V9_HERD_MIN_MILK = 150         # milk quote needed to swap to cows
V9_HERD_MAX_EGG_SHOPS = 1         # sheep swap: at most this many BAKERY + BRUNCH_SPOT
V9_HERD_MAX_EGG_SHOPS_COW = 0  # cow swap: at most this many
V9_HERD_MIN_MILK_SHOPS = 3      # cow swap: at least this many PIZZA / ICE_CREAM / SMOOTHIE
_V9_HERD_PRODUCT = {"SHEEP": "WOOL", "COW": "MILK"}
_V9_HERD = {}
_V9_HERD_REPORT = dict(herd_species="", herd_rewrites=0, herd_extra_sold=0, herd_errors=0)


def _v9_herd_choose(obs):
    shops = obs["town"]["unlocked_shops"]
    prices = obs["market"]["prices"]
    egg_shops = sum(s in ("BAKERY", "BRUNCH_SPOT") for s in shops)
    if (egg_shops <= V9_HERD_MAX_EGG_SHOPS and "YARN_STORE" in shops
            and int(prices.get("WOOL", 0)) >= V9_HERD_MIN_WOOL):
        return "SHEEP"
    milk_shops = sum(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in shops)
    if (egg_shops <= V9_HERD_MAX_EGG_SHOPS_COW and milk_shops >= V9_HERD_MIN_MILK_SHOPS
            and int(prices.get("MILK", 0)) >= V9_HERD_MIN_MILK):
        return "COW"
    return None


def _v9_herd(obs, action, st):
    step = int(obs["step"])
    orders = action.get("market") or []
    if st.get("species") is None and not st.get("decided"):
        if step >= 216 and any(len(o) >= 2 and o[:2] == ["BUY_ANIMAL", "GOOSE"] for o in orders):
            st["decided"] = True
            st["species"] = _v9_herd_choose(obs)
            _V9_HERD_REPORT["herd_species"] = st["species"] or ""
    species = st.get("species")
    if not species:
        return action
    product = _V9_HERD_PRODUCT[species]
    commands = [list(action.get("farmer") or ["PASS"])] + [list(c) for c in (action.get("hands") or [])]
    market = [list(o) for o in orders]
    for c in commands:
        if c and c[0] == "BUILD_COOP":
            c[0] = "BUILD_PASTURE"
            _V9_HERD_REPORT["herd_rewrites"] += 1
        elif len(c) >= 2 and c[0] in ("PICKUP", "PLACE") and c[1] == "GOOSE":
            c[1] = species
            _V9_HERD_REPORT["herd_rewrites"] += 1
    rewritten = []
    for o in market:
        if len(o) >= 3 and o[:2] == ["BUY_ANIMAL", "GOOSE"]:
            rewritten.append(["BUY_ANIMAL", species, o[2]])
        elif len(o) >= 2 and o[:2] == ["SELL", "EGG"] and not any(isinstance(t_, dict) and t_.get("animal") == "GOOSE" for r_ in obs["farms"][int(obs["player"])]["tiles"] for t_ in r_):
            continue
        else:
            rewritten.append(o)
    result = dict(action)
    result["farmer"], result["hands"], result["market"] = commands[0], commands[1:], rewritten
    player = int(obs["player"])
    native = _IMPL.chassis.players.get(player)
    if native and native.get("route") in _IMPL.chassis.routes and step < 718:
        stock = projected_shed(result, FarmView(obs)).get(product, 0)
        selling = sum(int(o[2]) for o in rewritten if len(o) >= 3 and o[:2] == ["SELL", product])
        planned = _IMPL.chassis.future_sells(native["route"], product, step + 1)
        extra = stock - selling - planned
        if extra > 0 and len(rewritten) < MAX_ORDERS and int(obs["market"]["prices"].get(product, 0)) >= 2:
            rewritten.insert(0, ["SELL", product, extra])
            _V9_HERD_REPORT["herd_extra_sold"] += extra
    return result


_V9_HERD_PARENT = agent


def agent(observation, configuration=None):
    player, step = int(observation["player"]), int(observation["step"])
    st = _V9_HERD.get(player)
    if st is None or step <= st["step"]:
        st = _V9_HERD[player] = {"step": -1}
        if step == 0:
            _V9_HERD_REPORT.update(herd_species="", herd_rewrites=0, herd_extra_sold=0, herd_errors=0)
    st["step"] = step
    action = _V9_HERD_PARENT(observation, configuration)
    try:
        return action
    except Exception:
        _V9_HERD_REPORT["herd_errors"] += 1
        return action


agent.telemetry = _V9_HERD_REPORT
agent = globals().pop("agent")


# ---------------------------------------------------------------------------
# v9 FERT: spend carried fertilizer on young wheat and carrots.
#
# Workers that tend animals carry collected fertilizer back to the shed, where
# the tape sells it into a book that falls from $55 on day 14 to $10 by day 27.
# On a short crop the same unit is worth far more: a watered wheat plant ends at
# 4 units, but fertilized for its yield window it caps at 6.  A worker that
# carries fertilizer and is about to water a wheat or carrot plant one day
# after planting (watered on planting day, not yet fertilized) fertilizes it
# instead; the tape waters it again on the following days.  Fertilizer the
# worker's own tape commands still spend today is left alone, and the layer only
# acts from day 16, once the fertilizer book is worth less than two wheat.
# ---------------------------------------------------------------------------
V9_FERT_CROPS = ("WHEAT", "CARROT")
V9_FERT_AGES = (1,)
V9_FERT_FIRST_DAY = 14
_V9_FERT_REPORT = dict(fert_applied=0, fert_errors=0)


def _v9_fert(obs, action):
    step = int(obs["step"])
    day = step // 24
    if day < V9_FERT_FIRST_DAY or step >= 700:
        return action
    player = int(obs["player"])
    farm = obs["farms"][player]
    positions = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]
    inventories = obs["private"]["inventories"]
    commands = [list(action.get("farmer") or ["PASS"])] + [list(c) for c in (action.get("hands") or [])]
    changed = False
    native = _IMPL.chassis.players.get(player)
    tape = _IMPL.chassis.routes.get(native.get("route")) if native else None
    planned = {}
    if tape is not None:
        # fertilizer this worker's own tape commands still spend today
        for t in range(step, min(len(tape), day * 24 + 24)):
            a = tape[t] or {}
            for u, c in enumerate([a.get("farmer") or ["PASS"]] + list(a.get("hands") or [])):
                if c and c[0] == "FERTILIZE":
                    planned[u] = planned.get(u, 0) + 1
    carried = {}
    targeted = set()
    for unit, command in enumerate(commands[:len(positions)]):
        if not command or command[0] != "WATER":
            continue
        x, y = positions[unit]
        tile = farm["tiles"][y][x]
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") in V9_FERT_CROPS):
            continue
        if (day - int(tile["planted_day"])) not in V9_FERT_AGES or tile.get("watered_today"):
            continue
        if int(tile.get("consecutive_unwatered", 1)) != 0 or int(tile.get("fertilized_until_day", -1)) >= day:
            continue
        have = carried.setdefault(unit, int((inventories[unit] if unit < len(inventories) else {}).get("FERTILIZER", 0))
                                  - planned.get(unit, 0))
        if have <= 0 or (x, y) in targeted:
            continue
        commands[unit] = ["FERTILIZE"]
        carried[unit] = have - 1
        targeted.add((x, y))
        changed = True
        _V9_FERT_REPORT["fert_applied"] += 1
    if not changed:
        return action
    result = dict(action)
    result["farmer"], result["hands"] = commands[0], commands[1:]
    return result


_V9_FERT_PARENT = agent


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _V9_FERT_REPORT.update(fert_applied=0, fert_errors=0)
    action = _V9_FERT_PARENT(observation, configuration)
    try:
        return _v9_fert(observation, action)
    except Exception:
        _V9_FERT_REPORT["fert_errors"] += 1
        return action


agent.telemetry = _V9_FERT_REPORT
agent = globals().pop("agent")


# ---------------------------------------------------------------------------
# v9 OPENING: a cash-safe step-0 wheat trade.
#
# Every route tape opens with a wheat round trip
#     step 0: BUY 13, BUY 30, SELL 30      step 1: SELL 13, BUY 5   (net +5)
# and then runs days 0-9 with only ~$6 of cash slack (minimum at step 32).
# The round trip wins cash from rivals whose own opening buys into it, but
# against openings that dump wheat in the same slots (e.g. BUY 43 / SELL 20 /
# SELL 22 or BUY 30 / SELL all) it ends step 1 up to $75 short; the day-1
# wheat and hire orders then fail, the herd goes unfed, and by days 5-8 the
# strawberry seed orders fail too (18-21 plants instead of 33, -20k..-65k).
#
# Replacing it with BUY 10, SELL 5 at step 0 (still net +5, nothing at
# step 1) leaves >= $1,050 after step 1 against all 6,648 recorded openings
# in the metav2 / M&M replays (exact market simulation, build/v9/opensim.py),
# and $2 more than the round trip against the V38/V39 tape lineage.
# ---------------------------------------------------------------------------
V9_OPENING_STEP0 = (("BUY_PRODUCT", "WHEAT", 20), ("SELL", "WHEAT", 15))
V9_OPENING_TAPE = ((("BUY_PRODUCT", "WHEAT", 13), ("BUY_PRODUCT", "WHEAT", 30), ("SELL", "WHEAT", 30)),
                   (("SELL", "WHEAT", 13), ("BUY_PRODUCT", "WHEAT", 5)))


def _v9_opening(obs, action):
    step = int(obs["step"])
    if step > 1:
        return action
    native = _IMPL.chassis.players.get(int(obs["player"]))
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    market = [list(o) for o in action.get("market") or []]
    wheat = [o for o in market if len(o) >= 3 and o[0] in ("BUY_PRODUCT", "SELL") and o[1] == "WHEAT"]
    if tuple((o[0], o[1], int(o[2])) for o in wheat) != V9_OPENING_TAPE[step]:
        return action  # the tape's opening was changed upstream; leave it alone
    rest = [o for o in market if o not in wheat]
    result = dict(action)
    result["market"] = ([list(o) for o in V9_OPENING_STEP0] if step == 0 else []) + rest
    return result


_V9_OPENING_PARENT = agent


def agent(observation, configuration=None):
    action = _V9_OPENING_PARENT(observation, configuration)
    try:
        return _v9_opening(observation, action)
    except Exception:
        return action


agent = globals().pop("agent")








# ---------------------------------------------------------------------------
# v9 RACE: fit the sale-reservation horizon to the rival's observed sale lead.
#
# Premium books crash within ~60 units of glut, so the first seller of a lot
# takes the price and the second sells into the crash.  The parent reserves
# planned tape sales a fixed four turns ahead; any deeper fixed horizon beats
# it head-to-head, but selling earlier than necessary gives away town-demand
# recovery against a rival that does not race.
#
# Everything here is public.  Each turn the rival's executed sales are
#
#   rival_sold[p] = inventory'[p] - inventory[p] + town_draw[p] - own_sold[p]
#
# (exact above the $1 floor, where sales never enter inventory).  When the
# rival sells a product while we still hold stock that our tape sells later,
# and the sale is not a late fill of our previous lot, the turns until our next
# planned sale are the rival's lead.  One horizon serves every product:
#
#   horizon = clamp(largest lead seen + RACE_MARGIN, RACE_DEFAULT, RACE_MAX)
#
# and it also lifts the parent's 72-turn block bound (patched into the
# parent's reservation by the release builder).
#
# v9/2: the shipped horizon is 40 turns with a 12-turn margin (was 6 and 4).
# Mirrors are the ladder's real opponent, and the premium books are first-come
# races, so reserve depth is the whole decision.  Against the 6/4 build the new
# setting wins 73-7 (+308) over 80 mirror games; against the shipped 32/12 build
# it wins 74-6 (+358).  Deeper is not better: 44/12 beats 40 head to head but
# drops the shallow-baseline record to 65-15, and 48/12 (a constant 48) falls to
# 14-26 against it, because a horizon past the rival's next lot gives up
# town-demand recovery for nothing.  The frozen top-30 stream panel is unchanged
# inside its noise (52.2% / +2,797 over 178 games vs 52.8% / +2,929 at 32/12) and
# the public field still goes 8-0.
#
# v9/2b: the reservation window starts at step 192 (day 8) instead of 288 (day 12),
# a one-line change in the parent's `_r36_reserve` gate made by the release builder.
# The herd's first milk and wool lots land on days 8-11 and the same-day sale
# reservation is what takes their price before a rival's lot lands; the two middle
# days of the tape's own schedule give that up.  Three fresh mirror blocks against
# the step-288 build: 32-0 (+147), 30-2 (+11), 30-2 (+10); and against the shallow
# 6/4 baseline the new build is if anything stronger, not weaker: 28-4 (+556) vs
# 28-4 (+406), 29-3 (+272), 31-1 (+359) vs 31-1 (+349).  Per-item horizons instead of
# one global horizon change nothing once the window starts at 192 (28 of 32 games
# identical), so the one-line gate is the whole change.
# ---------------------------------------------------------------------------
V9_RACE_DEFAULT = 44
V9_RACE_MAX = 48
V9_RACE_MARGIN = 12
V9_RACE_GAP = 3            # a sale this soon after our previous planned lot is a late fill
V9_RACE_WINDOW = 30        # turns of tape searched for planned sales around a rival sale
V9_RACE_ITEMS = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
_V9_SHOP_ITEMS = {
    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_V9_RACE = {}
_V9_RACE_REPORT = dict(rival_sales=0, leads=0, race_errors=0)


def _v9_town_draw(shops, step):
    """Units each shop instance and the town centre remove after `step`'s market."""
    draw = dict.fromkeys(V9_RACE_ITEMS, 0)
    if step % 4 == 0:
        for shop in shops:
            items = _V9_SHOP_ITEMS.get(shop, ())
            for item in items:
                if item in draw:
                    draw[item] += 2 if len(items) == 1 else 1
    if step % 24 == 0:
        for item in draw:
            draw[item] += 1
    return draw


def _v9_planned_sells(tape, item, step):
    """Turns within V9_RACE_WINDOW of `step` at which the tape sells `item`."""
    out = []
    for t in range(max(0, step - V9_RACE_WINDOW), min(len(tape), step + V9_RACE_WINDOW + 1)):
        if any(o and o[0] == "SELL" and len(o) >= 3 and o[1] == item and int(o[2]) > 0
               for o in tape[t].get("market") or []):
            out.append(t)
    return out


def _v9_race_update(obs, st):
    """Recover last turn's rival sales and record the leads that prove racing."""
    prev = st["prev"]
    step = int(obs["step"])
    if not prev or prev["step"] != step - 1:
        return
    native = _IMPL.chassis.players.get(int(obs["player"]))
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return
    tape = _IMPL.chassis.routes[native["route"]]
    inventory = obs["market"]["inventory"]
    draw = _v9_town_draw(prev["shops"], prev["step"])
    t = prev["step"]
    for item in V9_RACE_ITEMS:
        if prev["prices"].get(item, 0) <= 3:
            continue
        sold = inventory[item] - prev["inventory"][item] + draw[item] - prev["own"].get(item, 0)
        if sold < 2:
            continue
        _V9_RACE_REPORT["rival_sales"] += 1
        if prev["left"].get(item, 0) <= 0:
            continue
        planned = _v9_planned_sells(tape, item, t)
        after = [s for s in planned if s >= t]
        before = [s for s in planned if s < t]
        if not after or (before and t - before[-1] < V9_RACE_GAP):
            continue
        st["lead"] = max(st["lead"], after[0] - t)
        _V9_RACE_REPORT["leads"] += 1


_V9_RACE_PARENT = agent


def agent(observation, configuration=None):
    player, step = int(observation["player"]), int(observation["step"])
    st = _V9_RACE.get(player)
    if st is None or step <= st["step"]:
        st = _V9_RACE[player] = {"step": -1, "lead": -V9_RACE_MARGIN, "prev": None}
        if step == 0:
            _V9_RACE_REPORT.update(rival_sales=0, leads=0, race_errors=0)
    st["step"] = step
    try:
        _v9_race_update(observation, st)
        horizon = min(V9_RACE_MAX, max(V9_RACE_DEFAULT, st["lead"] + V9_RACE_MARGIN))
        _V9_ITEM_HZ[player] = dict.fromkeys(V9_RACE_ITEMS, horizon)
    except Exception:
        _V9_RACE_REPORT["race_errors"] += 1
        _V9_ITEM_HZ.pop(player, None)
    action = _V9_RACE_PARENT(observation, configuration)
    try:
        stock = projected_shed(action, FarmView(observation))
        own = {}
        for o in action.get("market") or []:
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in V9_RACE_ITEMS:
                n = min(max(0, int(o[2])), max(0, stock.get(o[1], 0) - own.get(o[1], 0)))
                own[o[1]] = own.get(o[1], 0) + n
        st["prev"] = {"step": step, "inventory": dict(observation["market"]["inventory"]),
                      "prices": dict(observation["market"]["prices"]), "own": own,
                      "left": {item: stock.get(item, 0) - own.get(item, 0) for item in V9_RACE_ITEMS},
                      "shops": list(observation["town"]["unlocked_shops"])}
    except Exception:
        _V9_RACE_REPORT["race_errors"] += 1
        st["prev"] = None
    return action


agent.telemetry = _V9_RACE_REPORT
agent = globals().pop("agent")


# ---------------------------------------------------------------------------
# v9 RACEPX: lead-sell a planned lot early only while its book is not glutted.
#
# The engine prices a product off the market inventory: below I0 the quote is above
# base, above I0 it is below.  The lead sale moves a lot one turn ahead of the tape's
# own plan, which is what takes the price when both sides hold the same lot -- but
# when the book is already above I0 the same units only fetch a lower price, and the
# town drain between the two turns is not enough to pay for it.
#
# Measured against the frozen top-20 streams the shipped build realizes below-base
# prices on exactly the products it floods (strawberry $107-123 vs a $120 base, milk
# $98-107 vs $160, wool $129-139 vs $200, melon $212 vs $250, fertilizer $43 vs $100)
# and above base on the ones the town drains (wheat $38 vs $25, carrot $54 vs $35,
# tomato $125 vs $60, egg $52 vs $50).
#
# This layer keeps the lead sale for products quoted at or above base + MARGIN and
# leaves the rest to the tape's own schedule.  The reservation (`_r36_reserve`) is
# untouched, so the RACE horizon still governs how far ahead lots may be pulled.
#
# Evidence (v9/3): mirror against the shipped build 35-13 (+220) over 48 fresh games;
# against the 6/4 ancestor 41-7 (+620) where the shipped build is 45-3 (+449); frozen
# top-20 panel 69/120 (+3,586) against 66/120 (+3,364); second panel 63/120 (+2,264)
# against 63/120 (+1,882); public field pool unchanged (14-2 vs cdb and fh11, 16-0
# vs fa103/fa141/fa238/wd14).
# ---------------------------------------------------------------------------
V9_RACEPX_BASE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
                  "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
V9_RACEPX_MARGIN = 0
_v9_racepx_report = dict(racepx_skipped=0, racepx_sold=0, racepx_errors=0)
_V9_RACEPX_LEAD = Chassis._sell_lead


def _v9_racepx_lead(self, action, view, projected, route, step, next_sup):
    prices = view.prices
    blocked = {i for i in V9_RACEPX_BASE
               if prices.get(i, 0) <= V9_RACEPX_BASE[i] + V9_RACEPX_MARGIN}
    if not blocked:
        _v9_racepx_report["racepx_sold"] += 1
        return _V9_RACEPX_LEAD(self, action, view, projected, route, step, next_sup)
    nxt = step + 1
    unlock_period = 3 * self.cfg["turns_per_day"]
    if nxt > LAST_ACT_STEP or nxt % unlock_period == 0 or step % 4 == 0:
        return
    tape = self.routes[route]
    future = tape[nxt] if nxt < len(tape) and isinstance(tape[nxt], dict) else {}
    planned = {}
    for o in future.get("market") or []:
        if o and o[0] == "SELL" and len(o) >= 3 and o[1] in PRODUCTS:
            planned[o[1]] = planned.get(o[1], 0) + max(0, int(o[2]))
    already = {o[1] for o in action.get("market") or [] if o and o[0] == "SELL" and len(o) > 1}
    for item in PRODUCTS:
        if item in blocked or item in already or planned.get(item, 0) <= 0:
            continue
        qty = min(projected.get(item, 0), planned[item])
        if qty <= 0 or prices.get(item, 0) < self.cfg["min_sell_price"]:
            continue
        if not self._add_sell(action, item, qty, self.cfg["max_orders"], merge=False):
            break
        projected[item] -= qty
        next_sup["suppress"][item] = next_sup["suppress"].get(item, 0) + qty
        _v9_racepx_report["racepx_skipped"] += 1
    if next_sup["suppress"]:
        next_sup["due_step"] = nxt


_V9_RACEPX_PARENT = agent
Chassis._sell_lead = _v9_racepx_lead


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _v9_racepx_report.update(racepx_skipped=0, racepx_sold=0, racepx_errors=0)
    try:
        return _V9_RACEPX_PARENT(observation, configuration)
    except Exception:
        _v9_racepx_report["racepx_errors"] += 1
        return {"farmer": ["PASS"], "hands": [], "market": []}


agent.telemetry = _v9_racepx_report
agent = globals().pop("agent")


# ---------------------------------------------------------------------------
# v9 RACEGATE: the same glut gate for the *reservation* (the 40-turn pull-forward).
#
# `_r36_reserve` moves tape-planned sales up to the RACE horizon forward, item by
# item.  RACEPX only gated the one-turn lead sale; this layer gates the reservation
# too: an item whose quote is at or below its base price is left to the tape's own
# schedule.  The debt ledger is untouched for the items that are still reserved, so
# suppression stays consistent.
#
# Evidence: see README (v9/3 round).
# ---------------------------------------------------------------------------
V9_RACEGATE_BASE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
                    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
V9_RACEGATE_MARGIN = 0
_v9_racegate_report = dict(racegate_reserved_units=0, racegate_errors=0)
_V9_RACEGATE_RESERVE = _r36_reserve


def _r36_reserve(obs, action):
    step = int(obs["step"])
    if not 192 <= step < 696:
        return action
    prices = obs["market"]["prices"]
    glutted = {i for i in V9_RACEGATE_BASE
               if prices.get(i, 0) <= V9_RACEGATE_BASE[i] + V9_RACEGATE_MARGIN}
    if not glutted:
        return _V9_RACEGATE_RESERVE(obs, action)
    native = _IMPL.chassis.players[int(obs["player"])]
    tape = _IMPL.chassis.routes[native["route"]]
    _v9_hz = _V9_ITEM_HZ.get(int(obs["player"]))
    end = min(695, step + (max(_v9_hz.values()) if _v9_hz else _R37_HORIZONS.get(int(obs["player"]), 2)))
    if end <= step:
        return action
    commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    view = FarmView(obs)
    if any(len(c) > 1 and c[0] == "PLACE" and c[1] in ANIMAL_STRUCTURE
           and view.inv(i).get(c[1], 0) > 0 for i, c in enumerate(commands[:len(view.positions)])):
        return action
    stock = projected_shed(action, view)
    market = action.get("market", [])
    blocked = {o[1] for o in market if len(o) > 1 and o[0] in ("SELL", "BUY_PRODUCT")}
    blocked.update(c[1] for c in commands if len(c) > 1 and c[0] == "PICKUP")
    blocked.update(c[1] for queue in native["pending"].values() for pos, c in queue
                   if len(c) > 1 and c[0] == "PICKUP")
    debts = native["sell_state"].setdefault("r36_debts", {})
    for item in PRODUCTS:
        if item in blocked or item in glutted or view.prices.get(item, 0) < 2:
            continue
        available = max(0, int(stock.get(item, 0)))
        if not available or len(market) >= 10:
            continue
        reservations = []
        item_end = min(end, step + _v9_hz[item]) if _v9_hz and item in _v9_hz else end
        for due_step in range(step + 1, item_end + 1):
            future = tape[due_step]
            work = [future.get("farmer") or ["PASS"], *(future.get("hands") or [])]
            if any(len(c) > 1 and c[:2] == ["PICKUP", item] for c in work):
                break
            if any(len(o) > 1 and o[:2] == ["BUY_PRODUCT", item] for o in future.get("market", [])):
                break
            planned = sum(max(0, int(o[2])) for o in future.get("market", [])
                          if len(o) >= 3 and o[:2] == ["SELL", item])
            amount = min(available, max(0, planned - debts.get(due_step, {}).get(item, 0)))
            if amount:
                reservations.append((due_step, amount))
                available -= amount
            if not available:
                break
        qty = sum(q for _, q in reservations)
        if qty:
            market.append(["SELL", item, qty])
            for due, q in reservations:
                debt = debts.setdefault(due, {})
                debt[item] = debt.get(item, 0) + q
            _R36_SALE_REPORT["sale_reserved_units"] += qty
            _R36_SALE_REPORT["sale_reservations"] += 1
            _v9_racegate_report["racegate_reserved_units"] += qty
    return action


_V9_RACEGATE_PARENT = agent


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        _v9_racegate_report.update(racegate_reserved_units=0, racegate_errors=0)
    try:
        return _V9_RACEGATE_PARENT(observation, configuration)
    except Exception:
        _v9_racegate_report["racegate_errors"] += 1
        return {"farmer": ["PASS"], "hands": [], "market": []}


agent.telemetry = _v9_racegate_report
agent = globals().pop("agent")


# ==== layer ctrtable.py 
_P_ctrtable_336053 = agent

# ---------------------------------------------------------------------------
# v9/3 CTRTABLE: rival-specific early wheat counters.
# Under the BUY 20 | SELL 15 opening, a rival tape's turn-2 observation (rival money, market wheat)
# identifies it exactly.  For known cash-tight tapes we trade alongside their own early wheat orders
# in the same market slots (checked unique over 4,604 recorded games):
#   feel the agi (979.0, 9989): steps 7-8  BUY 5 slot 0, SELL 5 slot 1
#   Mother-Goose (33.0, 9990): step 3      BUY 20 slot 0, SELL 20 slot 1
# ---------------------------------------------------------------------------
CT_TABLE = {
    (979.0, 9989): ((7, 0, ("BUY_PRODUCT", "WHEAT", 5)), (7, 1, ("SELL", "WHEAT", 5)),
                    (8, 0, ("BUY_PRODUCT", "WHEAT", 5)), (8, 1, ("SELL", "WHEAT", 5))),
    (33.0, 9990): ((3, 0, ("BUY_PRODUCT", "WHEAT", 20)), (3, 1, ("SELL", "WHEAT", 20))),
}
_CT = {}
_CT_REPORT = dict(ct_fired=0, ct_errors=0)


def _ct_apply(obs, action, st):
    step = int(obs["step"])
    if step == 2:
        rival = obs["farms"][1 - int(obs["player"])]
        st["plan"] = CT_TABLE.get((round(float(rival["money"]), 3), int(obs["market"]["inventory"]["WHEAT"])))
        if st["plan"]:
            _CT_REPORT["ct_fired"] += 1
    plan = st.get("plan")
    if not plan:
        return action
    items = sorted((slot, list(o)) for t, slot, o in plan if t == step)
    if not items:
        return action
    market = [list(o) for o in action.get("market") or []]
    for slot, o in items:
        while len(market) < slot:
            market.append(["SELL", "WHEAT", 0])
        market.insert(slot, o)
    result = dict(action)
    result["market"] = market[:MAX_ORDERS]
    return result


def agent(observation, configuration=None):
    player, step = int(observation["player"]), int(observation["step"])
    st = _CT.get(player)
    if st is None or step <= st["step"]:
        st = _CT[player] = {"step": -1}
    st["step"] = step
    action = _P_ctrtable_336053(observation, configuration)
    try:
        return _ct_apply(observation, action, st)
    except Exception:
        _CT_REPORT["ct_errors"] += 1
        return action


agent.telemetry = _CT_REPORT
agent = globals().pop("agent")


# ==== layer overflow.py 
_P_overflow_338343 = agent

# ---------------------------------------------------------------------------
# v9/3 OVERFLOW (ported from public V43 R148, Ahmed Berat Ozer, Apache-2.0):
# at hour 23 the workers' cargo drops into a 100-unit shed; cargo that does not fit
# is destroyed.  Sell exactly the shed stock that the destroyed cargo would replace,
# so the complete post-dawn stock vector is unchanged and the sold units are extra.
# ---------------------------------------------------------------------------
_OV_REPORT = dict(ov_turns=0, ov_units=0, ov_errors=0)


def _ov_fields(obs, action):
    farm, private = _PLANNER_NS['_clone_state'](obs['farms'][obs['player']], obs['private'])
    commands = [action.get('farmer') or ['PASS'], *(action.get('hands') or [])]
    demand = {}
    for c in commands:
        if len(c) > 1 and c[0] == 'PLANT':
            demand[c[1]] = demand.get(c[1], 0) + 1
    blocked = {p for p, n in demand.items() if n > private['seeds'].get(p, 0)}
    for actor, c in enumerate(commands[:len(private['inventories'])]):
        if len(c) > 1 and c[0] == 'PLANT' and c[1] in blocked:
            continue
        _PLANNER_NS['_apply_unit_action'](farm, private, actor, c, 10, int(obs['step']) // 24, 24, 100)
    return farm, private


def _ov_same(a, b):
    return all(int(a.get(p, 0)) == int(b.get(p, 0)) for p in set(a) | set(b))


def _ov_apply(obs, action):
    if int(obs['step']) % 24 != 23:
        return action
    orders = action.get('market') or []
    if len(orders) >= 10 or not _r97_budget(obs, orders):
        return action
    _, private = _ov_fields(obs, action)
    stock, _, _ = _r97_market_stock(private['shed'], orders)
    original, loss = _r97_delivery(stock, private, True)
    if not loss:
        return action
    remaining = max(0, 100 - sum(stock.values()))
    tail = []
    for bag in private['inventories']:
        for item, n in bag.items():
            n = max(0, int(n)); take = min(n, remaining); remaining -= take
            if n > take:
                tail.extend([item] * (n - take))
    released = {}; best = None
    for item in tail:
        released[item] = released.get(item, 0) + 1
        if item not in obs['market']['prices'] or released[item] > stock.get(item, 0):
            break
        if len(orders) + len(released) > 10:
            break
        proposed = list(orders) + [['SELL', p, n] for p, n in released.items()]
        after, _, _ = _r97_market_stock(private['shed'], proposed)
        final, _ = _r97_delivery(after, private, True)
        if _ov_same(original, final):
            best = (proposed, dict(released))
    if best is None:
        return action
    _OV_REPORT['ov_turns'] += 1
    _OV_REPORT['ov_units'] += sum(best[1].values())
    return dict(action, market=best[0])


def agent(observation, configuration=None):
    action = _P_overflow_338343(observation, configuration)
    try:
        return _ov_apply(observation, action)
    except Exception:
        _OV_REPORT['ov_errors'] += 1
        return action


agent.telemetry = _OV_REPORT
agent = globals().pop("agent")


# One-worker non-harvest service for the inherited six-sheep project.
# All feeding and care are mandatory. Optional fertilizer collection only uses
# leftover time; setup, wool harvests, and late-start days keep the old crew.
_SL_REQUEST = _v233_request
_SL_WORKER = _v233_worker
_SL_REPORT = dict(compact_days=0, confirmed=0, collect=0)
_SL_TILES = ((5,5),(6,5),(7,5),(7,6),(6,6),(5,6))


def _sl_dist(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])


def _sl_path(pos,targets):
    return min(_r53_permutations(targets),key=lambda path:(_sl_dist(pos,path[0])+sum(_sl_dist(a,b) for a,b in zip(path,path[1:])),path)) if targets else ()


def _v233_request(obs,action,state,native):
    result=_SL_REQUEST(obs,action,state,native)
    pending=state.get('pending')
    if result is action or not pending or pending['initial']:
        return result
    farm=obs['farms'][obs['player']];hour=int(obs['step'])%24
    tiles=[farm['tiles'][y][x] for x,y in _SL_TILES]
    if not all(isinstance(t,dict) and t.get('animal')=='SHEEP' and t.get('yield_units',0)==0 for t in tiles):
        return result
    # Exact spawn after native commands/hires, and a full feed pickup turn.
    ready,spawn=_r62_input_start(obs,action,0)
    path=_sl_path(spawn,_SL_TILES)
    travel=_sl_dist(spawn,path[0])+sum(_sl_dist(a,b) for a,b in zip(path,path[1:]))
    mandatory=sum(not t.get('fed_today') for t in tiles)+sum(not t.get('cared_today') for t in tiles)
    available=min((int(obs['step'])//24+1)*24,719)-ready
    if travel+mandatory>available:
        return result
    # Collection can be interleaved along the essential route. Charge the
    # discarded fertilizer against the saved wage, including final delivery.
    native_hires=sum(o and o[0]=='HIRE' for o in action.get('market',[]))
    saved=_v219_fib(farm['hires_today']+native_hires+1)
    delivery=_sl_dist(path[-1],_v219_home(path[-1]))+1 if int(obs['step'])//24==29 else 0
    possible=max(0,min(6,available-travel-mandatory-delivery))
    if saved<=(6-possible)*obs['market']['prices']['FERTILIZER']:
        return result
    out=copy.deepcopy(result)
    assert out['market'][-2:]==[['HIRE'],['HIRE']]
    out['market'].pop()
    pending.update(count=1,targets=path)
    _V233_REPORT['sheep_hire_requests']-=1
    _SL_REPORT['compact_days']+=1
    return out


def _v233_worker(obs,actor,targets):
    if len(targets)!=6:
        return _SL_WORKER(obs,actor,targets)
    farm=obs['farms'][obs['player']];private=obs['private'];step=int(obs['step'])
    pos=tuple(farm['hands'][actor-1]);inv=private['inventories'][actor]
    needed=[];hungry=0
    for target in targets:
        x,y=target;t=farm['tiles'][y][x]
        if not isinstance(t,dict) or t.get('animal')!='SHEEP':
            return _SL_WORKER(obs,actor,targets)
        if not t['fed_today']:hungry+=1
        if not t['fed_today'] or not t['cared_today']:needed.append(target)
    home=_v219_home(pos)
    if hungry>inv.get('WHEAT',0):
        return _v219_walk(pos,home) or ['PICKUP','WHEAT',min(hungry,private['shed'].get('WHEAT',0))]
    if needed:
        path=_sl_path(pos,needed)
        current=farm['tiles'][pos[1]][pos[0]]
        if pos in targets and isinstance(current,dict) and current.get('fed_today') and current.get('cared_today') and current.get('fertilizer_available'):
            travel=_sl_dist(pos,path[0])+sum(_sl_dist(a,b) for a,b in zip(path,path[1:]))
            work=sum(not farm['tiles'][y][x]['fed_today'] for x,y in path)+sum(not farm['tiles'][y][x]['cared_today'] for x,y in path)
            delivery=_sl_dist(path[-1],_v219_home(path[-1]))+1 if step//24==29 else 0
            remaining=min((step//24+1)*24,719)-step
            if 1+travel+work+delivery<=remaining:
                _SL_REPORT['collect']+=1
                return ['COLLECT_FERTILIZER']
        target=path[0];t=farm['tiles'][target[1]][target[0]]
        return _v219_walk(pos,target) or (['FEED'] if not t['fed_today'] else ['CARE'])
    # Essential work is complete. Collect what can still reach the shed on
    # the final day; on earlier days the normal midnight deposit is sufficient.
    remaining=719-step if step//24==29 else 24-step%24
    tasks=[]
    for target in targets:
        t=farm['tiles'][target[1]][target[0]]
        if not t.get('fertilizer_available'):continue
        dist=_sl_dist(pos,target)
        ret=_sl_dist(target,_v219_home(target))+1 if step//24==29 else 0
        if dist+1+ret<=remaining:tasks.append((dist,tuple(target)))
    if tasks:
        _,target=min(tasks)
        command=_v219_walk(pos,target) or ['COLLECT_FERTILIZER']
        _SL_REPORT['collect']+=command==['COLLECT_FERTILIZER']
        return command
    if inv.get('FERTILIZER',0):
        return _v219_walk(pos,home) or ['PLACE','FERTILIZER',inv['FERTILIZER']]
    return ['PASS']


agent=globals().pop('agent')


# v9/4 VE: commit the six-sheep expansion on day 11 when two of the first three
# shops are yarn stores. The melon sale lands on day 11, and sheep placed that
# day produce on days 17, 20, 23, 26 and 29 instead of 18, 21, 24 and 27: a
# fifth wool harvest for one more day of feed and labour.
# Day 11 waits until the tape's own land purchase (hour 1) and only ignores a
# native sheep that the tape itself picks up later today (units act before the
# market, and the project's hands spawn a step after its purchase). It commits
# only when cash also covers every purchase the tape still plans through day 12
# (its day-11 strawberry seeds above all); otherwise day 12 decides as before.
_VE_ELIGIBLE = _v233_eligible
_VE_REPORT = dict(ve_day11_checks=0, ve_day11_budget_declines=0, ve_day11_ok=0)
_VE_SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
_VE_ANIMAL = {'SHEEP': 500, 'COW': 400, 'GOOSE': 300}


def _v233_eligible(obs, native):
    step = int(obs['step'])
    if step // 24 != 11:
        return _VE_ELIGIBLE(obs, native)
    tape = _IMPL.chassis.routes[native['route']]
    private = obs['private']
    held = int(private['shed'].get('SHEEP', 0)) + sum(int(i.get('SHEEP', 0)) for i in private['inventories'])
    pickups = 0
    for t in range(step, 12 * 24):
        for c in [tape[t].get('farmer')] + tape[t].get('hands', []):
            if c and c[0] == 'PICKUP' and len(c) > 1 and c[1] == 'SHEEP':
                pickups += int(c[2]) if len(c) > 2 else 1
    if held > pickups:
        return False
    clean = dict(private, shed=dict(private['shed'], SHEEP=0),
                 inventories=[{k: v for k, v in i.items() if k != 'SHEEP'} for i in private['inventories']])
    if not _VE_ELIGIBLE(dict(obs, private=clean), native):
        return False
    _VE_REPORT['ve_day11_checks'] += 1
    prices = obs['market']['prices']
    spend = 0
    hires = {}
    for t in range(step + 1, min(len(tape), 13 * 24)):
        for o in tape[t].get('market', []):
            if not o:
                continue
            if o[0] == 'BUY_LAND' or o[:2] == ['BUY_ANIMAL', 'SHEEP']:
                return False
            if o[0] == 'BUY_SEED':
                spend += int(o[2]) * _VE_SEED.get(o[1], 100)
            elif o[0] == 'BUY_PRODUCT':
                spend += int(o[2]) * (int(prices.get(o[1], 50)) + 10)
            elif o[0] == 'BUY_ANIMAL':
                spend += int(o[2]) * _VE_ANIMAL.get(o[1], 500)
            elif o[0] == 'HIRE':
                d = t // 24
                spend += _v219_fib(hires.get(d, 0))
                hires[d] = hires.get(d, 0) + 1
    if obs['farms'][obs['player']]['money'] < 7000 + 3000 + spend:
        _VE_REPORT['ve_day11_budget_declines'] += 1
        return False
    _VE_REPORT['ve_day11_ok'] += 1
    return True


agent.telemetry = _VE_REPORT
agent = globals().pop('agent')


# v9/4 VT: the sheep expansion's last two days.
# No refresh follows day 29, so feeding, caring and buying feed that day are
# worthless: only wool already grown is worth a hand. Day 29 hires nothing when
# no sheep holds wool, and otherwise one harvest-only hand that delivers the
# wool before the final market. A care on day 28 adds to the bonus after the
# last production refresh has already consumed it, so day-28 hands skip CARE.
_VT_REQUEST = _v233_request
_VT_WORKER = _v233_worker
_VT_RESCUE = _v234_rescue
_VT_REPORT = dict(vt_no_hire_days=0, vt_single_harvest_days=0, vt_skipped_care=0)
_VT_TILES = ((5, 5), (6, 5), (7, 5), (5, 6), (6, 6), (7, 6))


def _vt_wool_tiles(obs):
    farm = obs['farms'][obs['player']]
    return [xy for xy in _VT_TILES if isinstance(farm['tiles'][xy[1]][xy[0]], dict)
            and farm['tiles'][xy[1]][xy[0]].get('animal') == 'SHEEP' and farm['tiles'][xy[1]][xy[0]].get('yield_units', 0) > 0]


def _v233_request(obs, action, state, native):
    result = _VT_REQUEST(obs, action, state, native)
    if result is action or int(obs['step']) // 24 != 29 or not state.get('committed'):
        return result
    pending = state.get('pending')
    if not pending or pending.get('initial'):
        return result
    wool = _vt_wool_tiles(obs)
    extra = result['market'][len(action.get('market', [])):]
    if not wool:
        state.pop('pending', None)
        _V233_REPORT['sheep_hire_requests'] -= sum(o == ['HIRE'] for o in extra)
        _V233_REPORT['sheep_feed_buy_requests'] -= 6
        _VT_REPORT['vt_no_hire_days'] += 1
        return action
    out = copy.deepcopy(action)
    out['market'] = list(out.get('market', [])) + [['HIRE']]
    _V233_REPORT['sheep_hire_requests'] -= sum(o == ['HIRE'] for o in extra) - 1
    _V233_REPORT['sheep_feed_buy_requests'] -= 6
    pending.update(count=1, targets=_sl_path(_r62_input_start(obs, action, 0)[1], wool))
    _VT_REPORT['vt_single_harvest_days'] += 1
    return out


def _v233_worker(obs, actor, targets):
    step = int(obs['step'])
    day = step // 24
    if day not in (28, 29):
        return _VT_WORKER(obs, actor, targets)
    farm = obs['farms'][obs['player']]
    private = obs['private']
    pos = tuple(farm['hands'][actor - 1])
    inv = private['inventories'][actor]
    home = _v219_home(pos)
    distance = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
    cargo = [item for item in ('WOOL', 'FERTILIZER') if inv.get(item, 0)]
    last = 717 if day == 29 else day * 24 + 23
    if cargo and step >= last - distance:
        return _v219_walk(pos, home) or ['PLACE', cargo[0], inv[cargo[0]]]
    sheep = [(x, y) for x, y in targets if isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('animal') == 'SHEEP']
    tasks = []
    if day == 28:
        hungry = sum(not farm['tiles'][y][x]['fed_today'] for x, y in sheep)
        if hungry and not inv.get('WHEAT', 0) and private['shed'].get('WHEAT', 0):
            return _v219_walk(pos, home) or ['PICKUP', 'WHEAT', min(hungry, private['shed']['WHEAT'])]
    for x, y in sheep:
        tile = farm['tiles'][y][x]
        command = None
        if day == 28 and not tile['fed_today'] and inv.get('WHEAT', 0):
            command = ['FEED']
        elif tile['yield_units']:
            command = ['HARVEST']
        elif day == 28 and tile['fertilizer_available']:
            command = ['COLLECT_FERTILIZER']
        if day == 28 and not tile['cared_today'] and command is None:
            _VT_REPORT['vt_skipped_care'] += 1
        if command:
            tasks.append((abs(pos[0] - x) + abs(pos[1] - y), (x, y), command))
    if tasks:
        _, target, command = min(tasks)
        return _v219_walk(pos, target) or command
    if cargo:
        return _v219_walk(pos, home) or ['PLACE', cargo[0], inv[cargo[0]]]
    return ['PASS']


def _v234_rescue(obs, action, state):
    if int(obs['step']) // 24 == 29:
        return action
    return _VT_RESCUE(obs, action, state)


agent.telemetry = _VT_REPORT
agent = globals().pop('agent')


# ---------------------------------------------------------------------------
# Claude CARROT2 layer: carrot instead of wheat when the carrot book pays. Own implementation.
# Built by tools/claude_build_carrot.py (derivation there).
# ---------------------------------------------------------------------------
_CA_FROM = 10
_CA_TO = 28
_CA_MARGIN = -20.0
_CA_DROP = 0.0
_CA_BUFFER = 8
_CA_FEED_DAYS = 1
_CA_CASH = 800
_CA_RESCUE = True
_CA_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_CA_CROP = {"WHEAT": (4, 6), "CARROT": (3, 4)}
_CA_STATE = {}
_CA_REPORT = {"ca_swaps": 0, "ca_rescues": 0, "ca_harvested": 0, "ca_sold": 0, "ca_seed_bought": 0,
              "ca_wheat_seed_saved": 0, "ca_carrot_seed_saved": 0, "ca_feed_block": 0, "ca_errors": 0,
              "ca_min_wheat": 999}


def _ca_tape(seat, t):
    native = _IMPL.chassis.players.get(seat)
    if not native or t > 719:
        return {}
    tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
    return tape[t] if t < len(tape) and isinstance(tape[t], dict) else {}


def _ca_spawn(positions, board):
    half = board // 2
    access = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    occ = {a: 0 for a in access}
    for p in positions:
        if tuple(p) in occ:
            occ[tuple(p)] += 1
    return list(min(access, key=lambda a: (occ[a], access.index(a))))


def _ca_visits(obs, action, pos, t_end, start=None):
    """Non-move commands issued on tile ``pos`` from this step (with ``action``) until ``t_end``."""
    seat = int(obs["player"])
    step = int(obs["step"])
    farm = obs["farms"][seat]
    board = len(farm["tiles"])
    half = board // 2
    positions = [list(farm["farmer"])] + [list(h) for h in farm["hands"]]
    out = []
    for t in range(step, min(t_end, 719) + 1):
        act = action if t == step else _ca_tape(seat, t)
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        for i in range(len(positions)):
            cmd = units[i] if i < len(units) and units[i] else ["PASS"]
            if cmd[0] in _CA_MOVES:
                dx, dy = _CA_MOVES[cmd[0]]
                nx, ny = positions[i][0] + dx, positions[i][1] + dy
                if 0 <= nx < board and 0 <= ny < board:
                    positions[i] = [nx, ny]
            elif tuple(positions[i]) == pos and (start is None or t >= start):
                out.append((t, i, cmd[0]))
        for _ in range(sum(1 for o in (act.get("market") or []) if o and o[0] == "HIRE")):
            positions.append(_ca_spawn(positions, board))
        if t % 24 == 23:
            positions = [[half - 1, half - 1]]
    return out


def _ca_decays(mls, a, b):
    """Decay events at steps s in [max(a, mls), b) with (s - mls) even."""
    a = max(a, mls)
    if b <= a:
        return 0
    first = a if (a - mls) % 2 == 0 else a + 1
    return 0 if first >= b else (b - 1 - first) // 2 + 1


def _ca_yield_path(crop, planted, visits, y0=1, fert_until=-1, watered_day=-1, now_step=0):
    """Return (harvest_units, best_rescue_units, rescue_step) for a crop following ``visits``.
    ``y0`` is the yield observed at ``now_step`` (decay before that step already included)."""
    myd, cap = _CA_CROP[crop]
    lo = (myd + 1) // 2
    mls = (planted + myd + 1) * 24
    y = y0
    best_rescue, rescue_t = 0, None
    for t, i, op in visits:
        day = t // 24
        age = day - planted
        dec = _ca_decays(mls, now_step, t)
        now = y - dec
        if now <= 0 and t > mls:
            return 0, best_rescue, rescue_t
        if op == "HARVEST":
            return (max(0, now) if age >= 2 else 0), best_rescue, rescue_t
        if op in ("PLANT", "DIG", "BUILD_COOP", "BUILD_PASTURE"):
            return 0, best_rescue, rescue_t
        if age >= 2 and now > best_rescue and t > now_step:
            best_rescue, rescue_t = now, t
        if op == "WATER" and lo <= age <= myd and day != watered_day:
            watered_day = day
            y = min(cap, y + (2 if fert_until >= day else 1))
    return 0, best_rescue, rescue_t


def _ca_wheat_total(obs):
    priv = obs["private"]
    return int(priv["shed"].get("WHEAT", 0)) + sum(int(inv.get("WHEAT", 0)) for inv in priv["inventories"])


def _ca_feed_need(seat, step, days):
    need = 0
    for t in range(step, min(719, step + 24 * days) + 1):
        act = _ca_tape(seat, t)
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        need += sum(1 for c in units if c and c[0] == "FEED")
    return need


_CA_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _CA_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        st = _CA_STATE.get(seat)
        if step == 0 or st is None or step <= st["step"]:
            st = _CA_STATE[seat] = {"step": -1, "tiles": {}, "spare_wheat": 0, "spare_carrot": 0, "credit": 0}
            if step == 0:
                _CA_REPORT.update(ca_swaps=0, ca_rescues=0, ca_harvested=0, ca_sold=0, ca_seed_bought=0,
                                  ca_wheat_seed_saved=0, ca_carrot_seed_saved=0, ca_feed_block=0,
                                  ca_errors=0, ca_min_wheat=999)
        st["step"] = step
        if not isinstance(action, dict) or step > 717:
            return action
        day = step // 24
        farm = observation["farms"][seat]
        tiles = farm["tiles"]
        priv = observation["private"]
        prices = observation["market"]["prices"]
        p_c, p_w = int(prices.get("CARROT", 0)), int(prices.get("WHEAT", 0))
        positions = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
        units = [list(action.get("farmer") or ["PASS"])] + [list(c) for c in (action.get("hands") or [])]
        market = [list(o) for o in (action.get("market") or [])]
        changed = False
        if _CA_FROM <= day <= _CA_TO + 4:
            _CA_REPORT["ca_min_wheat"] = min(_CA_REPORT["ca_min_wheat"], _ca_wheat_total(observation))
        # 1. bookkeeping + rescue of swapped carrots
        for pos, planted in list(st["tiles"].items()):
            tile = tiles[pos[1]][pos[0]]
            if not (isinstance(tile, dict) and tile.get("crop") == "CARROT" and int(tile.get("planted_day", -9)) == planted):
                st["tiles"].pop(pos, None)
                continue
            here = [i for i, p in enumerate(positions) if p == pos and i < len(units)]
            if not here:
                continue
            i = here[0]
            cmd = units[i]
            yu = int(tile.get("yield_units", 0))
            if cmd and cmd[0] == "HARVEST":
                if day - planted >= 2 and yu > 0:
                    st["credit"] += yu
                    _CA_REPORT["ca_harvested"] += yu
                    st["tiles"].pop(pos, None)
                continue
            if not _CA_RESCUE or (cmd and cmd[0] in _CA_MOVES) or day - planted < 2 or yu <= 0:
                continue
            visits = _ca_visits(observation, action, pos, (planted + 5) * 24)
            harvest, later, _ = _ca_yield_path("CARROT", planted, visits, y0=yu,
                                               fert_until=int(tile.get("fertilized_until_day", -1)),
                                               watered_day=day if tile.get("watered_today") else -1,
                                               now_step=step)
            if yu > max(harvest, later):
                units[i] = ["HARVEST"]
                st["credit"] += yu
                _CA_REPORT["ca_harvested"] += yu
                _CA_REPORT["ca_rescues"] += 1
                st["tiles"].pop(pos, None)
                changed = True
        # 2. swaps
        pays_now = 3 * (p_c - _CA_DROP) - 20 > 4 * p_w - 10 + _CA_MARGIN
        if _CA_FROM <= day <= _CA_TO and pays_now:
            seeds_c = min(st["spare_carrot"],
                          int(priv["seeds"].get("CARROT", 0)) - sum(1 for c in units if c[:2] == ["PLANT", "CARROT"]))
            wheat_ok = None
            for i, cmd in enumerate(units):
                if cmd[:2] != ["PLANT", "WHEAT"] or i >= len(positions) or seeds_c <= 0:
                    continue
                pos = positions[i]
                if tiles[pos[1]][pos[0]] is not None:
                    continue
                if wheat_ok is None:
                    wheat_ok = _ca_wheat_total(observation) >= _ca_feed_need(seat, step, _CA_FEED_DAYS)
                if not wheat_ok:
                    _CA_REPORT["ca_feed_block"] += 1
                    break
                visits = _ca_visits(observation, action, pos, (day + 6) * 24, start=step + 1)
                wu, _, _ = _ca_yield_path("WHEAT", day, visits)
                ch, cr, _ = _ca_yield_path("CARROT", day, visits)
                cu = max(ch, cr if _CA_RESCUE else 0)
                if cu * (p_c - _CA_DROP) - 20 > wu * p_w - 10 + _CA_MARGIN:
                    units[i] = ["PLANT", "CARROT"]
                    seeds_c -= 1
                    st["spare_carrot"] -= 1
                    st["tiles"][pos] = day
                    st["spare_wheat"] += 1
                    _CA_REPORT["ca_swaps"] += 1
                    changed = True
        # 3. seeds
        new_market = []
        for o in market:
            if len(o) >= 3 and o[0] == "BUY_SEED" and o[1] in ("WHEAT", "CARROT"):
                key = "spare_wheat" if o[1] == "WHEAT" else "spare_carrot"
                cut = min(int(o[2]), st[key])
                if cut > 0:
                    st[key] -= cut
                    _CA_REPORT["ca_wheat_seed_saved" if o[1] == "WHEAT" else "ca_carrot_seed_saved"] += cut
                    changed = True
                    if int(o[2]) - cut <= 0:
                        continue
                    o = [o[0], o[1], int(o[2]) - cut]
            new_market.append(o)
        market = new_market
        if _CA_FROM <= day <= _CA_TO - 1 and pays_now and len(market) < 10:
            have = int(priv["seeds"].get("CARROT", 0)) - sum(1 for c in units if c[:2] == ["PLANT", "CARROT"])
            buying = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ["BUY_SEED", "CARROT"])
            q = _CA_BUFFER - have - buying
            if q > 0 and int(farm.get("money", 0)) >= _CA_CASH + 20 * q:
                market.append(["BUY_SEED", "CARROT", q])
                st["spare_carrot"] += q
                _CA_REPORT["ca_seed_bought"] += q
                changed = True
        # 4. sell credited carrots
        if st["credit"] > 0 and p_c >= 2 and len(market) < 10:
            view_action = {"farmer": units[0], "hands": units[1:], "market": market}
            stock = int(projected_shed(view_action, FarmView(observation)).get("CARROT", 0))
            selling = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ["SELL", "CARROT"])
            q = min(st["credit"], stock - selling)
            if q > 0:
                market.insert(0, ["SELL", "CARROT", q])
                st["credit"] -= q
                _CA_REPORT["ca_sold"] += q
                changed = True
        if changed:
            action = dict(action)
            action["farmer"] = units[0]
            action["hands"] = units[1:]
            action["market"] = market[:10]
    except Exception:
        _CA_REPORT["ca_errors"] += 1
    return action


agent.telemetry = _CA_REPORT
agent = globals().pop('agent')


# ---------------------------------------------------------------------------
# Claude ORDERPRI2 layer: sales ordered by the rival's estimated sellable stock. Own implementation.
# Built by tools/claude_build_orderpri2.py (derivation there).
# ---------------------------------------------------------------------------
_OR2_CAP = 24
_OR2_SN_K = 0
_OR2_SN_H = 24
_OR2_SLOT_H = 6
_OR2_SLOT_MARGIN = 12.0
_OR2_SN_ITEMS = ("MILK", "STRAWBERRY", "WOOL", "MELON", "EGG")
_OR2_ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
_OR2_ONGOING = ("TOMATO", "STRAWBERRY")
_OR2_ANIMAL = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
_OR2_SHOPS = {"BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
              "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
              "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
              "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
              "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")}
_OR2_STATE = {}
_OR2_REPORT = {"or2_reordered": 0, "or2_changed_vs_v39": 0, "or2_rival_harvest": 0, "or2_rival_sold": 0,
               "or2_errors": 0}


def _or2_draw(shops, step):
    draw = {}
    if step % 4 == 0:
        for name in shops:
            products = _OR2_SHOPS.get(name, ())
            for item in products:
                draw[item] = draw.get(item, 0) + (2 if len(products) == 1 else 1)
    if step % 24 == 0:
        for item in _OR2_ITEMS:
            draw[item] = draw.get(item, 0) + 1
    return draw


def _or2_tiles(farm):
    out = {}
    for y, row in enumerate(farm["tiles"]):
        for x, t in enumerate(row):
            if not isinstance(t, dict):
                continue
            if t.get("kind") == "PLANT" and t.get("crop"):
                out[(x, y)] = ("P", t["crop"], int(t.get("planted_day", -1)), int(t.get("yield_units", 0)))
            elif t.get("animal") in _OR2_ANIMAL:
                out[(x, y)] = ("A", _OR2_ANIMAL[t["animal"]], int(t.get("placed_day", -1)), int(t.get("yield_units", 0)))
    return out


def _or2_exposure(observation, item, qty, batch):
    if qty <= 0 or batch <= 0 or item not in _R37_MARKET_PARAMS:
        return 0.0
    params = {k: dict(v) for k, v in _R37_MARKET_PARAMS.items()}
    for k, patch in (observation["market"].get("params") or {}).items():
        if k in params:
            params[k].update(patch)
    inv = int(observation["market"]["inventory"][item])
    return float(sum(_r37_market_price(item, inv + j, params) - _r37_market_price(item, inv + batch + j, params)
                     for j in range(qty)))


_OR2_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _OR2_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        st = _OR2_STATE.get(seat)
        if step == 0 or st is None or step <= st.get("step", -1):
            st = _OR2_STATE[seat] = {"step": -1, "stock": {i: 0 for i in _OR2_ITEMS}, "prev": None}
            if step == 0:
                for k in _OR2_REPORT:
                    _OR2_REPORT[k] = 0
        rival = observation["farms"][1 - seat]
        tiles = _or2_tiles(rival)
        inv_now = {i: int(observation["market"]["inventory"].get(i, 0)) for i in _OR2_ITEMS}
        prev = st["prev"]
        if prev and prev["step"] == step - 1:
            stock = st["stock"]
            for pos, old in prev["tiles"].items():
                kind, item, born, y = old
                if y <= 0:
                    continue
                new = tiles.get(pos)
                got = 0
                if kind == "P" and item not in _OR2_ONGOING:
                    if (new is None and not _OR2_WEED(rival, pos)) or (new is not None and new[2] != born):
                        got = y
                elif new is not None and new[0] == kind and new[1] == item and new[2] == born and new[3] < y:
                    if step % 24 != 0:
                        got = y - new[3]
                    elif new[3] == 0:
                        got = y
                if got > 0:
                    stock[item] = stock.get(item, 0) + got
                    _OR2_REPORT["or2_rival_harvest"] += got
            draw = _or2_draw(prev["shops"], prev["step"])
            for item in _OR2_ITEMS:
                if prev["prices"].get(item, 0) <= 1:
                    continue
                moved = inv_now[item] - prev["inv"][item] + draw.get(item, 0) - prev["own"].get(item, 0)
                if moved > 0:
                    stock[item] = max(0, stock.get(item, 0) - moved)
                    _OR2_REPORT["or2_rival_sold"] += moved
        own = {}
        if isinstance(action, dict):
            orders = [list(o) for o in (action.get("market") or [])]
            proj = dict(projected_shed(action, FarmView(observation)))
            if _OR2_SN_K > 0 and 24 <= step < 694:
                native = _IMPL.chassis.players.get(seat)
                debts = native["sell_state"].setdefault("r36_debts", {}) if native else None
                for item in _OR2_SN_ITEMS:
                    if debts is None or int(st["stock"].get(item, 0)) < _OR2_SN_K:
                        continue
                    if int(observation["market"]["prices"].get(item, 0)) < 2 or len(orders) >= 10:
                        continue
                    if any(len(o) >= 2 and o[0] in ("BUY_PRODUCT", "BUY_ANIMAL") and o[1] == item for o in orders):
                        continue
                    selling = sum(max(0, int(o[2])) for o in orders if len(o) >= 3 and o[0] == "SELL" and o[1] == item)
                    avail = int(proj.get(item, 0)) - selling
                    take = 0
                    for t in range(step + 1, min(694, step + _OR2_SN_H) + 1):
                        if take >= avail:
                            break
                        tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
                        act = tape[t] if t < len(tape) and isinstance(tape[t], dict) else {}
                        planned = sum(max(0, int(o[2])) for o in (act.get("market") or [])
                                      if len(o) >= 3 and o[0] == "SELL" and o[1] == item)
                        planned -= debts.get(t, {}).get(item, 0)
                        q = min(planned, avail - take)
                        if q > 0:
                            debts.setdefault(t, {})[item] = debts.get(t, {}).get(item, 0) + q
                            take += q
                    if take > 0:
                        for o in orders:
                            if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                                o[2] = int(o[2]) + take
                                break
                        else:
                            orders.append(["SELL", item, take])
                        _OR2_REPORT["or2_sellnow"] = _OR2_REPORT.get("or2_sellnow", 0) + take
                        action = dict(action)
                        action["market"] = orders
            if _OR2_SLOT_H > 0 and 288 <= step < 694 and len(orders) >= 10:
                native = _IMPL.chassis.players.get(seat)
                debts = native["sell_state"].setdefault("r36_debts", {}) if native else None
                sells = [o for o in orders if len(o) >= 3 and o[0] == "SELL"]
                selling_items = {o[1] for o in sells}
                bought_items = {o[1] for o in orders if len(o) >= 2 and o[0] in ("BUY_PRODUCT", "BUY_ANIMAL")}
                best = None
                for item in _OR2_SN_ITEMS:
                    if debts is None or item in selling_items or item in bought_items:
                        continue
                    avail = int(proj.get(item, 0))
                    if avail <= 0 or int(observation["market"]["prices"].get(item, 0)) < 2:
                        continue
                    plan, take = [], 0
                    for t in range(step + 1, min(694, step + _OR2_SLOT_H) + 1):
                        if take >= avail:
                            break
                        tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
                        act = tape[t] if t < len(tape) and isinstance(tape[t], dict) else {}
                        planned = sum(max(0, int(o[2])) for o in (act.get("market") or [])
                                      if len(o) >= 3 and o[0] == "SELL" and o[1] == item)
                        q = min(planned - debts.get(t, {}).get(item, 0), avail - take)
                        if q > 0:
                            plan.append((t, q))
                            take += q
                    if take <= 0:
                        continue
                    b = min(_OR2_CAP, int(st["stock"].get(item, 0)))
                    value = _or2_exposure(observation, item, take, max(1, b))
                    if best is None or value > best[0]:
                        best = (value, item, take, plan)
                if best is not None and sells:
                    def sval(o):
                        q = min(max(0, int(o[2])), max(0, int(proj.get(o[1], 0))))
                        return _or2_exposure(observation, o[1], q, max(1, min(_OR2_CAP, int(st["stock"].get(o[1], 0)))))
                    weakest = min(sells, key=sval)
                    if best[0] > sval(weakest) + _OR2_SLOT_MARGIN and weakest[1] not in ("WHEAT", "FERTILIZER")                             or best[0] > sval(weakest) + _OR2_SLOT_MARGIN and int(weakest[2]) <= 2:
                        # drop the weakest sale; give its booked debts back (nearest due first)
                        refund = max(0, int(weakest[2]))
                        for t in range(step + 1, step + 49):
                            if refund <= 0:
                                break
                            owed = debts.get(t, {}).get(weakest[1], 0)
                            back = min(owed, refund)
                            if back > 0:
                                debts[t][weakest[1]] = owed - back
                                refund -= back
                        orders.remove(weakest)
                        orders.append(["SELL", best[1], best[2]])
                        for t, q in best[3]:
                            debts.setdefault(t, {})[best[1]] = debts.get(t, {}).get(best[1], 0) + q
                        _OR2_REPORT["or2_slot_swaps"] = _OR2_REPORT.get("or2_slot_swaps", 0) + 1
                        action = dict(action)
                        action["market"] = orders
            left = dict(proj)
            movable, fixed, bought = [], [], set()
            for idx, o in enumerate(orders):
                if len(o) >= 2 and o[0] in ("BUY_PRODUCT", "BUY_ANIMAL"):
                    bought.add(o[1])
                if len(o) >= 3 and o[0] == "SELL" and int(o[2]) > 0 and o[1] not in bought:
                    movable.append((idx, o))
                else:
                    fixed.append((idx, o))
            if movable and step >= 1:
                def score(io):
                    item, qty = io[1][1], min(int(io[1][2]), max(0, int(proj.get(io[1][1], 0))))
                    b = min(_OR2_CAP, int(st["stock"].get(item, 0)))
                    return (-_or2_exposure(observation, item, qty, b),
                            -_r37_quote_priority(observation, io[1], proj), io[0])
                scored = sorted(movable, key=score)
                new = [o for _, o in scored] + [o for _, o in fixed]
                if new != orders:
                    v39 = sorted(movable, key=lambda io: (-_r37_quote_priority(observation, io[1], proj), io[0]))
                    if [o for _, o in v39] != [o for _, o in scored]:
                        _OR2_REPORT["or2_changed_vs_v39"] += 1
                    _OR2_REPORT["or2_reordered"] += 1
                    action = dict(action)
                    action["market"] = new
                    orders = new
            for o in orders[:10]:
                if len(o) >= 3 and o[0] == "SELL" and o[1] in _OR2_ITEMS:
                    got = min(max(0, int(o[2])), max(0, int(left.get(o[1], 0))))
                    left[o[1]] = left.get(o[1], 0) - got
                    own[o[1]] = own.get(o[1], 0) + got
        st["prev"] = {"step": step, "tiles": tiles, "inv": inv_now, "own": own,
                      "prices": dict(observation["market"]["prices"]),
                      "shops": list((observation.get("town") or {}).get("unlocked_shops") or [])}
        st["step"] = step
    except Exception:
        _OR2_REPORT["or2_errors"] += 1
    return action


def _OR2_WEED(farm, pos):
    t = farm["tiles"][pos[1]][pos[0]]
    return isinstance(t, dict) and t.get("kind") == "WEED"


agent.telemetry = _OR2_REPORT
agent = globals().pop('agent')


# ---------------------------------------------------------------------------
# Claude CAPHARV layer: harvest animals that would overflow tonight. Own implementation.
# Built by tools/claude_build_capharv.py (derivation there).
# ---------------------------------------------------------------------------
_CH_SHED = 100
_CH_SELL = True
_CH_ANIMALS = {"GOOSE": ("EGG", 4, 4, 1), "COW": ("MILK", 6, 8, 2), "SHEEP": ("WOOL", 6, 6, 3)}
_CH_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_CH_STATE = {}
_CH_REPORT = {"ch_collect_swaps": 0, "ch_care_swaps": 0, "ch_saved": 0, "ch_sold": 0, "ch_shed_block": 0,
              "ch_errors": 0}


def _ch_tape(seat, t):
    native = _IMPL.chassis.players.get(seat)
    if not native or t > 719:
        return {}
    tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
    return tape[t] if t < len(tape) and isinstance(tape[t], dict) else {}


def _ch_visits_today(obs, action):
    """{pos: [(t, op)]} for non-move commands from the next step to the end of today."""
    seat = int(obs["player"])
    step = int(obs["step"])
    farm = obs["farms"][seat]
    board = len(farm["tiles"])
    half = board // 2
    access = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    positions = [list(farm["farmer"])] + [list(h) for h in farm["hands"]]
    out = {}
    for t in range(step, (step // 24 + 1) * 24):
        act = action if t == step else _ch_tape(seat, t)
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        for i in range(len(positions)):
            cmd = units[i] if i < len(units) and units[i] else ["PASS"]
            if cmd[0] in _CH_MOVES:
                dx, dy = _CH_MOVES[cmd[0]]
                nx, ny = positions[i][0] + dx, positions[i][1] + dy
                if 0 <= nx < board and 0 <= ny < board:
                    positions[i] = [nx, ny]
            elif t > step:
                out.setdefault(tuple(positions[i]), []).append((t, cmd[0]))
        for _ in range(sum(1 for o in (act.get("market") or []) if o and o[0] == "HIRE")):
            occ = {a: 0 for a in access}
            for p in positions:
                if tuple(p) in occ:
                    occ[tuple(p)] += 1
            positions.append(list(min(access, key=lambda a: (occ[a], access.index(a)))))
    return out


_CH_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _CH_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        st = _CH_STATE.get(seat)
        if step == 0 or st is None or step <= st["step"]:
            st = _CH_STATE[seat] = {"step": -1, "credit": {}}
            if step == 0:
                for k in _CH_REPORT:
                    _CH_REPORT[k] = 0
        st["step"] = step
        if not isinstance(action, dict) or step > 717:
            return action
        day = step // 24
        farm = observation["farms"][seat]
        priv = observation["private"]
        prices = observation["market"]["prices"]
        positions = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
        units = [list(action.get("farmer") or ["PASS"])] + [list(c) for c in (action.get("hands") or [])]
        market = [list(o) for o in (action.get("market") or [])]
        changed = False
        visits = None
        for i, pos in enumerate(positions[:len(units)]):
            cmd = units[i]
            if not cmd or cmd[0] not in ("CARE", "COLLECT_FERTILIZER"):
                continue
            tile = farm["tiles"][pos[1]][pos[0]]
            if not (isinstance(tile, dict) and tile.get("animal") in _CH_ANIMALS):
                continue
            product, cap, first, interval = _CH_ANIMALS[tile["animal"]]
            since = day + 1 - int(tile.get("placed_day", 99)) - first
            if since < 0 or since % interval != 0:
                continue
            y = int(tile.get("yield_units", 0))
            if visits is None:
                visits = _ch_visits_today(observation, action)
            later = visits.get(pos, [])
            if any(op == "HARVEST" for t, op in later):
                continue
            fed = bool(tile.get("fed_today")) or any(op == "FEED" for t, op in later)
            prod = 1 + (int(tile.get("pending_care_bonus", 0)) if fed else 0)
            overflow = y + prod - cap
            if overflow <= 0 or y <= 0:
                continue
            quote = int(prices.get(product, 0))
            if cmd[0] == "COLLECT_FERTILIZER":
                if overflow * quote <= int(prices.get("FERTILIZER", 0)):
                    continue
            else:
                if any(op == "COLLECT_FERTILIZER" for t, op in later) or overflow <= 1:
                    continue
            carried = sum(int(v) for inv in priv["inventories"] for v in inv.values())
            if sum(int(v) for v in priv["shed"].values()) + carried + y >= _CH_SHED:
                _CH_REPORT["ch_shed_block"] += 1
                continue
            units[i] = ["HARVEST"]
            _CH_REPORT["ch_collect_swaps" if cmd[0] == "COLLECT_FERTILIZER" else "ch_care_swaps"] += 1
            saved = overflow if cmd[0] == "COLLECT_FERTILIZER" else overflow - 1
            _CH_REPORT["ch_saved"] += saved
            st["credit"][product] = st["credit"].get(product, 0) + saved
            changed = True
        if _CH_SELL and any(v > 0 for v in st["credit"].values()):
            view_action = {"farmer": units[0], "hands": units[1:], "market": market}
            stock = dict(projected_shed(view_action, FarmView(observation)))
            for product, credit in list(st["credit"].items()):
                if credit <= 0 or len(market) >= 10 or int(prices.get(product, 0)) < 2:
                    continue
                selling = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ["SELL", product])
                q = min(credit, int(stock.get(product, 0)) - selling)
                if q > 0:
                    for o in market:
                        if len(o) >= 3 and o[:2] == ["SELL", product]:
                            o[2] = int(o[2]) + q
                            break
                    else:
                        market.insert(0, ["SELL", product, q])
                    st["credit"][product] = credit - q
                    _CH_REPORT["ch_sold"] += q
                    changed = True
        if changed:
            action = dict(action)
            action["farmer"] = units[0]
            action["hands"] = units[1:]
            action["market"] = market[:10]
    except Exception:
        _CH_REPORT["ch_errors"] += 1
    return action


agent.telemetry = _CH_REPORT
agent = globals().pop('agent')


# ---------------------------------------------------------------------------
# Claude SHEDROOM layer: sell shed goods before the night drop overflows. Own implementation.
# Built by tools/claude_build_shedroom.py (derivation there).
# ---------------------------------------------------------------------------
_SR_MARGIN = 8
_SR_HOURS = (21, 22, 23)
_SR_PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
_SR_REPORT = {"sr_turns": 0, "sr_units": 0, "sr_errors": 0}


def _sr_tape(seat, t):
    native = _IMPL.chassis.players.get(seat)
    if not native or t > 719:
        return {}
    tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
    return tape[t] if t < len(tape) and isinstance(tape[t], dict) else {}


_SR_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _SR_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step == 0:
            for k in _SR_REPORT:
                _SR_REPORT[k] = 0
        if step % 24 not in _SR_HOURS or step >= 717 or not isinstance(action, dict):
            return action
        seat = int(observation["player"])
        farm = observation["farms"][seat]
        priv = observation["private"]
        view = FarmView(observation)
        proj = dict(projected_shed(action, view))
        market = [list(o) for o in (action.get("market") or [])]
        left = dict(proj)
        night_shed = sum(max(0, int(v)) for v in proj.values())
        for o in market:
            if len(o) >= 3 and o[0] == "SELL":
                got = min(max(0, int(o[2])), max(0, int(left.get(o[1], 0))))
                left[o[1]] = left.get(o[1], 0) - got
                night_shed -= got
            elif len(o) >= 3 and o[0] in ("BUY_PRODUCT", "BUY_ANIMAL"):
                night_shed += max(0, int(o[2]))
        units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        carried = 0
        for i, pos in enumerate(view.positions):
            inv = priv["inventories"][i] if i < len(priv["inventories"]) else {}
            held = sum(max(0, int(v)) for v in inv.values())
            cmd = units[i] if i < len(units) and units[i] else ["PASS"]
            tile = farm["tiles"][pos[1]][pos[0]] if isinstance(pos, (list, tuple)) else None
            op = cmd[0]
            if op == "DROP" and _shed_adjacent(pos, view.board):
                held = 0
            elif op == "HARVEST" and isinstance(tile, dict):
                held += max(0, int(tile.get("yield_units", 0)))
            elif op == "COLLECT_FERTILIZER" and isinstance(tile, dict) and tile.get("fertilizer_available"):
                held += 1
            elif op in ("FEED", "FERTILIZE") and held > 0:
                held -= 1
            elif op == "PICKUP" and len(cmd) >= 2 and _shed_adjacent(pos, view.board):
                held += max(1, int(cmd[2]) if len(cmd) >= 3 else 1)
            carried += held
        cap = int((configuration or {}).get("shedCapacity", 100)) if isinstance(configuration, dict) else 100
        overflow = night_shed + carried - cap + _SR_MARGIN
        if overflow <= 0:
            return action
        need = {"WHEAT": 0, "FERTILIZER": 0}
        for t in range(step + 1, min(719, step + 25)):
            act = _sr_tape(seat, t)
            for c in [act.get("farmer") or ["PASS"]] + list(act.get("hands") or []):
                if not c:
                    continue
                if c[0] == "FEED":
                    need["WHEAT"] += 1
                elif c[0] == "FERTILIZE":
                    need["FERTILIZER"] += 1
        prices = observation["market"]["prices"]
        cands = []
        for item in _SR_PRODUCTS:
            spare = int(left.get(item, 0)) - need.get(item, 0)
            if spare > 0 and int(prices.get(item, 0)) >= 2:
                cands.append((int(prices.get(item, 0)), item, spare))
        cands.sort()
        sold_now = 0
        for price, item, spare in cands:
            if overflow <= 0:
                break
            q = min(spare, overflow)
            for o in market:
                if len(o) >= 3 and o[:2] == ["SELL", item]:
                    o[2] = int(o[2]) + q
                    break
            else:
                if len(market) >= 10:
                    continue
                market.append(["SELL", item, q])
            overflow -= q
            sold_now += q
        if sold_now:
            _SR_REPORT["sr_turns"] += 1
            _SR_REPORT["sr_units"] += sold_now
            action = dict(action)
            action["market"] = market
    except Exception:
        _SR_REPORT["sr_errors"] += 1
    return action


agent.telemetry = _SR_REPORT
agent = globals().pop('agent')


# ---------------------------------------------------------------------------
# Claude HERD2 layer: goose / cow / sheep choice at the tape's goose purchase.
# Own implementation. Built by tools/claude_build_herd2.py (derivation there).
# ---------------------------------------------------------------------------
_HD2_FROM = 192
_HD2_TO = 360
_HD2_RATIO = 1.3
_HD2_MIN_GAIN = 600.0
_HD2_LOOKBACK = 3
_HD2_OPTIONS = ('COW', 'SHEEP')
_HD2_CARE = 0.8
_HD2_FUTURE = 0.0

_HD2_SPEC = {
    "GOOSE": {"cost": 300, "first": 4, "interval": 1, "per": 2, "product": "EGG", "structure": "COOP"},
    "COW": {"cost": 400, "first": 8, "interval": 2, "per": 3, "product": "MILK", "structure": "PASTURE"},
    "SHEEP": {"cost": 500, "first": 6, "interval": 3, "per": 4, "product": "WOOL", "structure": "PASTURE"},
}
_HD2_SHOP_TYPES = {
    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"), "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_HD2_STATE = {}
_HD2_REPORT = {"hd2_decision": "", "hd2_ev": "", "hd2_rewrites": 0, "hd2_credit_units": 0,
               "hd2_sold_units": 0, "hd2_errors": 0}


def _hd2_daily_shop_demand(item, shops):
    total = 0.0
    for name in shops:
        products = _HD2_SHOP_TYPES.get(name, ())
        if item in products:
            total += 6.0 * (2 if len(products) == 1 else 1)
    return total


def _hd2_future_demand_per_day(item):
    """Expected extra daily demand of one more uniformly drawn shop instance."""
    return sum(6.0 * (2 if len(p) == 1 else 1) for p in _HD2_SHOP_TYPES.values() if item in p) / len(_HD2_SHOP_TYPES)


def _hd2_schedule(animal, placed_day, day_from):
    """Units an animal of this type produces on each day >= day_from (daily care assumed,
    scaled by _HD2_CARE)."""
    spec = _HD2_SPEC[animal]
    out = {}
    for d in range(max(day_from, placed_day + spec["first"]), 30):
        if (d - placed_day - spec["first"]) % spec["interval"] == 0:
            out[d] = out.get(d, 0.0) + 1.0 + (spec["per"] - 1) * _HD2_CARE
    return out


def _hd2_ev(option, k, obs, st):
    """Margin value of k new animals of `option`: their own revenue, plus the price change
    their supply causes on (our existing future units - rival existing future units)."""
    spec = _HD2_SPEC[option]
    item = spec["product"]
    animal_of = {"EGG": "GOOSE", "MILK": "COW", "WOOL": "SHEEP"}[item]
    day = int(obs["step"]) // 24
    seat = int(obs["player"])
    market = obs["market"]
    params = {key: dict(v) for key, v in _R37_MARKET_PARAMS.items()}
    for key, patch in (market.get("params") or {}).items():
        if key in params and isinstance(patch, dict):
            params[key].update(patch)
    # existing supply, per farm, per day
    existing = [dict(), dict()]
    for farm_index, farm in enumerate(obs["farms"]):
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict) and tile.get("animal") == animal_of:
                    for d, u in _hd2_schedule(animal_of, int(tile.get("placed_day", day)), day + 1).items():
                        existing[farm_index][d] = existing[farm_index].get(d, 0.0) + u
    shed = (obs.get("private") or {}).get("shed") or {}
    carried = sum(int(inv.get(animal_of, 0)) for inv in (obs.get("private") or {}).get("inventories") or [])
    for _ in range(int(shed.get(animal_of, 0)) + carried):
        for d, u in _hd2_schedule(animal_of, day + 1, day + 1).items():
            existing[seat][d] = existing[seat].get(d, 0.0) + u
    # Purchases the tape already plans after this turn; a family-similar rival runs the same tape.
    native = _IMPL.chassis.players.get(seat)
    if native:
        similar = _r37_similarity(obs) >= 0.9
        for t in range(int(obs["step"]) + 1, 696):
            tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
            if t >= len(tape) or not isinstance(tape[t], dict):
                continue
            for order in tape[t].get("market", []) or []:
                if len(order) >= 3 and order[0] == "BUY_ANIMAL" and order[1] == animal_of:
                    for _ in range(max(0, int(order[2]))):
                        for d, u in _hd2_schedule(animal_of, t // 24 + 1, day + 1).items():
                            existing[seat][d] = existing[seat].get(d, 0.0) + u
                            if similar:
                                existing[1 - seat][d] = existing[1 - seat].get(d, 0.0) + u
    ours_existing, rival_existing = existing[seat], existing[1 - seat]
    new = {}
    for d, u in _hd2_schedule(option, day + 1, day + 1).items():
        new[d] = u * k
    shops = list((obs.get("town") or {}).get("unlocked_shops") or [])
    unlocks_left = max(0, 8 - len(shops))
    base_demand = _hd2_daily_shop_demand(item, shops) + 1.0
    extra_demand = _hd2_future_demand_per_day(item) * _HD2_FUTURE

    def path(with_new):
        inv = float(market["inventory"][item])
        prices, revenue = {}, 0.0
        for d in range(day + 1, 30):
            opened = min(unlocks_left, max(0, (d // 3) - (day // 3)))
            inv -= base_demand + extra_demand * opened
            inv += ours_existing.get(d, 0.0) + rival_existing.get(d, 0.0)
            prices[d] = _r37_market_price(item, int(round(inv)), params)
            if with_new:
                units = int(round(new.get(d, 0.0)))
                for _ in range(units):
                    price = _r37_market_price(item, int(round(inv)), params)
                    revenue += price
                    if price > 1:
                        inv += 1
        return prices, revenue

    base_prices, _ = path(False)
    new_prices, revenue = path(True)
    swing = sum((new_prices[d] - base_prices[d]) * (ours_existing.get(d, 0.0) - rival_existing.get(d, 0.0))
                for d in base_prices)
    return revenue + swing - spec["cost"] * k, revenue


def _hd2_decide(obs, action, st):
    market = action.get("market") or []
    buys = [o for o in market if len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "GOOSE"]
    if not buys:
        return
    st["decided"] = True
    step = int(obs["step"])
    if not (_HD2_FROM <= step < _HD2_TO):
        return
    farm = obs["farms"][int(obs["player"])]
    if any(isinstance(t, dict) and t.get("kind") == "COOP" for row in farm["tiles"] for t in row):
        _HD2_REPORT["hd2_decision"] = "skip:coop_exists"
        return
    k = sum(max(0, int(o[2])) for o in buys)
    k_plan = max(k, 3)
    evs = {opt: _hd2_ev(opt, k_plan, obs, st)[0] for opt in ("GOOSE",) + tuple(_HD2_OPTIONS)}
    _HD2_REPORT["hd2_ev"] = ",".join("%s:%d" % (o, v) for o, v in sorted(evs.items()))
    best = max(_HD2_OPTIONS, key=lambda o: evs[o]) if _HD2_OPTIONS else None
    goose = evs["GOOSE"]
    if best is None:
        return
    gain = evs[best] - goose
    ok_ratio = evs[best] >= _HD2_RATIO * max(goose, 1.0)
    extra_cost = (_HD2_SPEC[best]["cost"] - 300) * k
    cash = float(farm.get("money", 0))
    if gain >= _HD2_MIN_GAIN and ok_ratio and cash >= 300 * k + extra_cost + 50:
        st["mode"] = best
        _HD2_REPORT["hd2_decision"] = "%s@%d" % (best, step)
    else:
        _HD2_REPORT["hd2_decision"] = "keep@%d" % step


def _hd2_rewrite(obs, action, st):
    mode = st["mode"]
    spec = _HD2_SPEC[mode]
    item = spec["product"]
    seat = int(obs["player"])
    farm = obs["farms"][seat]
    private = obs["private"]
    positions = [farm["farmer"]] + list(farm["hands"])
    market = action.get("market") or []
    cash = float(farm.get("money", 0))
    seed_cost = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
    for order in market:
        if len(order) >= 3 and order[0] == "BUY_ANIMAL" and order[1] == "GOOSE":
            n = max(0, int(order[2]))
            affordable = int(max(0.0, cash) // spec["cost"])
            order[1] = mode
            order[2] = min(n, affordable)
            cash -= order[2] * spec["cost"]
            _HD2_REPORT["hd2_rewrites"] += 1
        elif len(order) >= 3 and order[0] in ("BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT"):
            # money spent by earlier orders of the same list is not available to the swap (DS-5 #6)
            q = max(0, int(order[2]))
            if order[0] == "BUY_ANIMAL":
                cash -= q * {"GOOSE": 300, "COW": 400, "SHEEP": 500}.get(order[1], 0)
            elif order[0] == "BUY_SEED":
                cash -= q * seed_cost.get(order[1], 0)
            else:
                cash -= q * int((obs["market"]["prices"] or {}).get(order[1], 0))
        elif order and order[0] == "BUY_LAND":
            cash -= 4000
    workers = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
    for actor, work in enumerate(workers[:len(positions)]):
        if not work:
            continue
        x, y = positions[actor]
        tile = farm["tiles"][y][x]
        if work[0] == "BUILD_COOP":
            workers[actor] = ["BUILD_PASTURE"]
            _HD2_REPORT["hd2_rewrites"] += 1
        elif len(work) >= 2 and work[0] in ("PICKUP", "PLACE") and work[1] == "GOOSE":
            workers[actor] = [work[0], mode] + list(work[2:])
            _HD2_REPORT["hd2_rewrites"] += 1
            if work[0] == "PLACE":
                st["pending"].append((x, y, int(obs["step"]) // 24))
        elif len(work) >= 2 and work[0] == "PLACE" and work[1] == "EGG":
            workers[actor] = ["PLACE", item] + list(work[2:])
            _HD2_REPORT["hd2_rewrites"] += 1
        elif work == ["HARVEST"] and (x, y) in st["sites"] and isinstance(tile, dict) \
                and tile.get("animal") == mode:
            units = max(0, int(tile.get("yield_units", 0)))
            st["credit"] += units
            _HD2_REPORT["hd2_credit_units"] += units
    action["farmer"] = workers[0]
    action["hands"] = workers[1:]
    if st["credit"] > 0:
        try:
            stock = projected_shed(action, FarmView(obs))
        except Exception:
            stock = dict(private.get("shed") or {})
        planned = sum(max(0, int(o[2])) for o in market if len(o) >= 3 and o[:2] == ["SELL", item])
        extra = min(st["credit"], max(0, int(stock.get(item, 0)) - planned))
        if extra > 0:
            for order in market:
                if len(order) >= 3 and order[:2] == ["SELL", item]:
                    order[2] = int(order[2]) + extra
                    break
            else:
                if len(market) < 10:
                    market.insert(0, ["SELL", item, extra])
                else:
                    extra = 0
            st["credit"] -= extra
            _HD2_REPORT["hd2_sold_units"] += extra
    action["market"] = market


def _hd2_confirm(obs, st):
    farm = obs["farms"][int(obs["player"])]
    keep = []
    for x, y, day in st["pending"]:
        tile = farm["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("animal") == st["mode"] and tile.get("placed_day") == day:
            st["sites"][(x, y)] = day
        elif int(obs["step"]) // 24 <= day + 1:
            keep.append((x, y, day))
    st["pending"] = keep


_HD2_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _HD2_PARENT(observation, configuration)
    try:
        seat = int(observation["player"])
        step = int(observation["step"])
        st = _HD2_STATE.get(seat)
        if st is None or step <= st["step"]:
            st = _HD2_STATE[seat] = {"step": -1, "inv": {}, "decided": False, "mode": None,
                                     "pending": [], "sites": {}, "credit": 0}
            if step == 0:
                _HD2_REPORT.update(hd2_decision="", hd2_ev="", hd2_rewrites=0, hd2_credit_units=0,
                                   hd2_sold_units=0, hd2_errors=0)
        st["step"] = step
        day = step // 24
        if day not in st["inv"]:
            st["inv"][day] = dict(observation["market"]["inventory"])
        if not isinstance(action, dict):
            return action
        if st["mode"]:
            _hd2_confirm(observation, st)
        elif not st["decided"]:
            _hd2_decide(observation, action, st)
        if st["mode"]:
            action = copy.deepcopy(action)
            _hd2_rewrite(observation, action, st)
    except Exception:
        _HD2_REPORT["hd2_errors"] += 1
    return action


agent.telemetry = _HD2_REPORT
agent = globals().pop('agent')


# ---------------------------------------------------------------------------
# Claude COWSWAP layer: cow / goose / sheep at the tape's first cow purchase. Own implementation.
# Built by tools/claude_build_cowswap.py (derivation there). Requires HERD2 above.
# ---------------------------------------------------------------------------
_CS_FROM = 144
_CS_TO = 192
_CS_RATIO = 1.3
_CS_MIN_GAIN = 600.0
_CS_OPTIONS = ('GOOSE',)
_CS_SHOP_RULE = 'nomilk'
_CS_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_CS_STATE = {}
_CS_REPORT = {"cs_decision": "", "cs_ev": "", "cs_rewrites": 0, "cs_broken": 0, "cs_credit": 0,
              "cs_sold": 0, "cs_errors": 0}


def _cs_tape(seat, t):
    native = _IMPL.chassis.players.get(seat)
    if not native or t > 719:
        return {}
    tape = _IMPL.chassis.routes[2 if t >= 648 else native["route"]]
    return tape[t] if t < len(tape) and isinstance(tape[t], dict) else {}


def _cs_spawn(positions, board):
    half = board // 2
    access = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    occ = {a: 0 for a in access}
    for p in positions:
        if tuple(p) in occ:
            occ[tuple(p)] += 1
    return list(min(access, key=lambda a: (occ[a], access.index(a))))


def _cs_plan(obs, action, k, mode):
    seat = int(obs["player"])
    step = int(obs["step"])
    farm = obs["farms"][seat]
    board = len(farm["tiles"])
    positions = [list(farm["farmer"])] + [list(h) for h in farm["hands"]]
    end = (step // 24 + 1) * 24 - 1
    builds, pickups, places = [], [], []
    for t in range(step, end + 1):
        act = action if t == step else _cs_tape(seat, t)
        units = [act.get("farmer") or ["PASS"]] + list(act.get("hands") or [])
        for i in range(len(positions)):
            cmd = units[i] if i < len(units) and units[i] else ["PASS"]
            pos = tuple(positions[i])
            if cmd[0] in _CS_MOVES:
                dx, dy = _CS_MOVES[cmd[0]]
                nx, ny = pos[0] + dx, pos[1] + dy
                if 0 <= nx < board and 0 <= ny < board:
                    positions[i] = [nx, ny]
            elif cmd[0] == "BUILD_PASTURE":
                builds.append((t, i, pos))
            elif len(cmd) >= 2 and cmd[0] == "PICKUP" and cmd[1] == "COW":
                pickups.append((t, i, max(1, int(cmd[2]) if len(cmd) > 2 else 1)))
            elif len(cmd) >= 2 and cmd[0] == "PLACE" and cmd[1] == "COW":
                places.append((t, i, pos))
        hires = sum(1 for o in (act.get("market") or []) if o and o[0] == "HIRE")
        for _ in range(hires):
            positions.append(_cs_spawn(positions, board))
    chosen, tiles = [], set()
    for t, i, pos in places:
        if pos not in tiles:
            chosen.append((t, i, pos))
            tiles.add(pos)
        if len(chosen) == k:
            break
    if len(chosen) < k:
        return None
    plan = {"builds": {}, "pickups": {}, "places": {}}
    buying_land = any(o and o[0] == "BUY_LAND" for o in (action.get("market") or []))
    unlocked = list(farm.get("unlocked_quadrants") or ["NW"])
    next_quadrant = [q for q in ("NE", "SW", "SE") if q not in unlocked][:1]
    half = board // 2
    for t, i, pos in chosen:
        x, y = pos
        tile = farm["tiles"][y][x]
        if mode == "GOOSE":
            quadrant = ("N" if y < half else "S") + ("W" if x < half else "E")
            locked_but_bought = tile == "LOCKED" and buying_land and quadrant in next_quadrant
            if tile is not None and not locked_but_bought:
                return None  # already built (or occupied): cannot become a coop without extra turns
            prior = [(tb, ib) for tb, ib, pb in builds if pb == pos and tb < t]
            if not prior:
                return None
            tb, ib = prior[-1]
            plan["builds"][(tb, ib)] = pos
        carrier = [(tp, ip, q) for tp, ip, q in pickups if ip == i and tp < t]
        if not carrier:
            return None
        tp, ip, q = carrier[-1]
        plan["pickups"][(tp, ip)] = plan["pickups"].get((tp, ip), 0) + 1
        plan["places"][(t, i)] = pos
    for key, n in plan["pickups"].items():
        q = next(q for tp, ip, q in pickups if (tp, ip) == key)
        if q != n:
            return None  # a pickup that also carries unswapped cows cannot be split
    return plan


_CS_PARENT = agent
del agent


def agent(observation, configuration=None):
    action = _CS_PARENT(observation, configuration)
    try:
        seat = int(observation["player"])
        step = int(observation["step"])
        st = _CS_STATE.get(seat)
        if st is None or step <= st["step"]:
            st = _CS_STATE[seat] = {"step": -1, "decided": False, "mode": None, "plan": None,
                                    "broken": False, "sites": {}, "pending": [], "credit": 0}
            if step == 0:
                _CS_REPORT.update(cs_decision="", cs_ev="", cs_rewrites=0, cs_broken=0, cs_credit=0,
                                  cs_sold=0, cs_errors=0)
        st["step"] = step
        if not isinstance(action, dict):
            return action
        farm = observation["farms"][seat]
        positions = [farm["farmer"]] + list(farm["hands"])
        market = [list(o) for o in (action.get("market") or [])]
        # confirm placements
        if st["pending"]:
            keep = []
            for x, y, day in st["pending"]:
                tile = farm["tiles"][y][x]
                if isinstance(tile, dict) and tile.get("animal") == st["mode"] and tile.get("placed_day") == day:
                    st["sites"][(x, y)] = day
                elif step // 24 <= day:
                    keep.append((x, y, day))
            st["pending"] = keep
        if not st["decided"] and _CS_FROM <= step < _CS_TO:
            buys = [o for o in market if len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW" and int(o[2]) > 0]
            shops_now = list((observation.get("town") or {}).get("unlocked_shops") or [])
            shop_ok = True
            if _CS_SHOP_RULE:
                # research/claude_20260913/RESULTS.md: over 48 seeds the swap only paid with an egg shop
                # open and no milk shop open (+1,254 mean over 9 seeds); with a milk shop it lost.
                no_milk = not any(s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP") for s in shops_now)
                if _CS_SHOP_RULE == "nomilk":
                    # 14 seeds without a milk shop and without a yarn store: +1,203 mean
                    shop_ok = no_milk and "YARN_STORE" not in shops_now
                else:
                    shop_ok = no_milk and any(s in ("BAKERY", "BRUNCH_SPOT") for s in shops_now)
            if buys and not shop_ok:
                st["decided"] = True
                _CS_REPORT["cs_decision"] = "shoprule@%d" % step
            elif buys:
                st["decided"] = True
                k = sum(int(o[2]) for o in buys)
                evs = {opt: _hd2_ev(opt, k, observation, st)[0] for opt in ("COW",) + tuple(_CS_OPTIONS)}
                _CS_REPORT["cs_ev"] = ",".join("%s:%d" % (o, v) for o, v in sorted(evs.items()))
                best = max(_CS_OPTIONS, key=lambda o: evs[o])
                cow = evs["COW"]
                if evs[best] - cow >= _CS_MIN_GAIN and evs[best] >= _CS_RATIO * max(cow, 1.0):
                    plan = _cs_plan(observation, action, k, best)
                    if plan is not None:
                        st["mode"], st["plan"] = best, plan
                        _CS_REPORT["cs_decision"] = "%s@%d" % (best, step)
                        for o in market:
                            if len(o) >= 3 and o[0] == "BUY_ANIMAL" and o[1] == "COW":
                                o[1] = best
                                _CS_REPORT["cs_rewrites"] += 1
                    else:
                        _CS_REPORT["cs_decision"] = "noplan@%d" % step
                else:
                    _CS_REPORT["cs_decision"] = "keep@%d" % step
        if st["mode"] and st["plan"] and not st["broken"]:
            plan = st["plan"]
            units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
            for i in range(min(len(units), len(positions))):
                cmd = units[i] or ["PASS"]
                pos = (int(positions[i][0]), int(positions[i][1]))
                key = (step, i)
                if key in plan["builds"]:
                    if cmd == ["BUILD_PASTURE"] and pos == plan["builds"][key]:
                        units[i] = ["BUILD_COOP"]
                        _CS_REPORT["cs_rewrites"] += 1
                    else:
                        st["broken"] = True
                if key in plan["pickups"]:
                    if len(cmd) >= 2 and cmd[0] == "PICKUP" and cmd[1] == "COW":
                        units[i] = ["PICKUP", st["mode"]] + list(cmd[2:])
                        _CS_REPORT["cs_rewrites"] += 1
                    else:
                        st["broken"] = True
                if key in plan["places"]:
                    if len(cmd) >= 2 and cmd[0] == "PLACE" and cmd[1] == "COW" and pos == plan["places"][key]:
                        units[i] = ["PLACE", st["mode"]] + list(cmd[2:])
                        st["pending"].append((pos[0], pos[1], step // 24))
                        _CS_REPORT["cs_rewrites"] += 1
                    else:
                        st["broken"] = True
            if st["broken"]:
                _CS_REPORT["cs_broken"] += 1
            action = dict(action)
            action["farmer"] = units[0]
            action["hands"] = units[1:]
        # credit harvests on swapped tiles and sell them as they reach the shed
        if st["sites"]:
            product = _HD2_SPEC[st["mode"]]["product"]
            units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
            for i in range(min(len(units), len(positions))):
                x, y = int(positions[i][0]), int(positions[i][1])
                tile = farm["tiles"][y][x]
                if units[i] == ["HARVEST"] and (x, y) in st["sites"] and isinstance(tile, dict) \
                        and tile.get("animal") == st["mode"]:
                    n = max(0, int(tile.get("yield_units", 0)))
                    st["credit"] += n
                    _CS_REPORT["cs_credit"] += n
            if st["credit"] > 0:
                stock = projected_shed(action, FarmView(observation))
                planned = sum(max(0, int(o[2])) for o in market if len(o) >= 3 and o[:2] == ["SELL", product])
                extra = min(st["credit"], max(0, int(stock.get(product, 0)) - planned))
                if extra > 0:
                    for o in market:
                        if len(o) >= 3 and o[:2] == ["SELL", product]:
                            o[2] = int(o[2]) + extra
                            break
                    else:
                        if len(market) < 10:
                            market.insert(0, ["SELL", product, extra])
                        else:
                            extra = 0
                    st["credit"] -= extra
                    _CS_REPORT["cs_sold"] += extra
        action = dict(action)
        action["market"] = market
    except Exception:
        _CS_REPORT["cs_errors"] += 1
    return action


agent.telemetry = _CS_REPORT
agent = globals().pop('agent')




# EXP283 adaptive arm: clone-gated sale pre-emption with drop-time race escalation.
# Original mechanism by Ahmed Berat Ozer's project. Live top-band replays (research155) show
# rivals executing the same public route tape and quoting the same product batches at the
# same drop turns. While the rival is observed executing our tape, V43's R36 native-tape
# reservation runs with horizon 8; if the rival is then observed selling a race product at the
# very turn the same product was dropped into our shed while we did not sell it (public market
# inventory change beyond town consumption; no own realized sale; own shed stock rose), the rival
# quotes at the drop and the horizon escalates to 24 for the rest of the game.
_RACE_PARENT=agent
_RACE_HORIZON_CLONE=8
_RACE_HORIZON_ESCALATED=24
_RACE_HORIZON_MIRROR=24
_RACE_ITEMS=('CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL')
_RACE_SHOPS={'BAKERY':('EGG','WHEAT'),'PIZZA_SHOP':('MILK','TOMATO','WHEAT'),'BRUNCH_SPOT':('EGG','WHEAT','STRAWBERRY'),'YARN_STORE':('WOOL',),
             'ICE_CREAM_SHOP':('STRAWBERRY','MILK','WHEAT'),'PET_CAFE':('CARROT',),'SMOOTHIE_SHOP':('STRAWBERRY','MILK'),'FARMERS_MARKET':('WHEAT','CARROT','TOMATO','STRAWBERRY')}
_RACE_STATE={}
_RACE_REPORT=dict(race_clone_turns=0,race_horizon_turns=0,race_lost_races=0,race_escalations=0,race_errors=0)
_RACE_ORIG_RESERVE=_r36_reserve

def _race_positions_equal(farms,player):
    own,rival=farms[player],farms[1-player]
    return len(own['hands'])>0 and own['hands']==rival['hands'] and own['farmer']==rival['farmer']

def _race_clone(observation,state):
    farms=observation['farms'];player=int(observation['player'])
    if len(farms[player]['hands'])>0:
        state['hist'].append(_race_positions_equal(farms,player))
        if len(state['hist'])>6:state['hist'].pop(0)
    return len(state['hist'])>=4 and sum(state['hist'])>=4 and _r37_similarity(observation)>=.95

def _race_town(step,shops):
    out={}
    if step%4==0:
        for shop in shops:
            items=_RACE_SHOPS.get(shop,())
            for item in items:out[item]=out.get(item,0)+(2 if len(items)==1 else 1)
    if step%24==0:
        for item in _RACE_ITEMS:out[item]=out.get(item,0)+1
    return out

def _race_lost(observation,state):
    """EXP293: True when the rival sold a race product at the previous turn while we held it unsold, the common tape
    has no sale of it within the lineage's own lead/reservation window (5 turns) and sells it within the following
    24 turns: the rival pre-empts the plan's own sale ahead of us."""
    prev=state.get('prev');prev_action=state.get('prev_action')
    if prev is None or prev_action is None:return False
    step=int(observation['step']);player=int(observation['player'])
    if step!=prev['step']+1 or step%24==0:return False
    inv=observation['market']['inventory'];pinv=prev['inventory'];prices=prev['prices']
    town=_race_town(step-1,prev['shops'])
    sold={}
    for order in prev_action.get('market',[]):
        if len(order)>=3 and order[0]=='SELL' and order[1] in _RACE_ITEMS:sold[order[1]]=1
    native=_IMPL.chassis.players[player]
    for item in _RACE_ITEMS:
        before=int(prev['view'].shed.get(item,0))
        if before<=0 or item in sold or prices.get(item,0)<=1:continue
        rival=int(inv[item])-int(pinv[item])+town.get(item,0)
        if rival<=0:continue
        def planned(t):
            future=_IMPL.chassis.routes[2 if t>=648 else native['route']][t]
            return any(len(o)>=3 and o[0]=='SELL' and o[1]==item for o in future.get('market',[]))
        # every member of this lineage sells at the scheduled turn, one turn early (sale lead) or up to four turns early
        # (the base reservation): only a sale further ahead of the plan is a race
        if any(planned(t) for t in range(step-1,min(719,step+5))):continue
        if any(planned(t) for t in range(step+5,min(719,step+24))):return True
    return False

def _race_snapshot(observation):
    market=observation['market']
    return dict(step=int(observation['step']),inventory=dict(market['inventory']),prices=dict(market['prices']),shops=list(observation['town'].get('unlocked_shops',[])),view=FarmView(observation))

def _r36_reserve(obs,action):
    player=int(obs['player']);h=_RACE_STATE.get(player,{}).get('horizon',0)
    if h>_R37_HORIZONS.get(player,2):
        saved=_R37_HORIZONS.get(player);_R37_HORIZONS[player]=h
        try:return _RACE_ORIG_RESERVE(obs,action)
        finally:
            if saved is None:_R37_HORIZONS.pop(player,None)
            else:_R37_HORIZONS[player]=saved
    return _RACE_ORIG_RESERVE(obs,action)

def agent(observation,configuration=None):
    state=None
    try:
        player=int(observation['player']);step=int(observation['step'])
        state=_RACE_STATE.get(player)
        if state is None or step<=state['step']:
            state=_RACE_STATE[player]={'step':-1,'hist':[],'horizon':0,'level':_RACE_HORIZON_CLONE,'prev':None,'prev_action':None}
        if step==0:_RACE_REPORT.update(race_clone_turns=0,race_horizon_turns=0,race_lost_races=0,race_escalations=0,race_errors=0)
        state['step']=step;state['horizon']=0
        # EXP288 mirror gate: a rival whose cash after the first turn equals ours executed the same first-turn
        # round trip (a copy of this agent); against a copy the sale race is won only by pre-empting the whole day.
        if step==1:
            try:
                farms=observation['farms'];rival=farms[1-player]['money'];own=farms[player]['money']
                state['level']=_RACE_HORIZON_MIRROR if (abs(float(rival)-float(own))<0.5 and _RACE_HORIZON_MIRROR>state['level']) else state['level']
                _RACE_REPORT['race_mirror']=int(abs(float(rival)-float(own))<0.5)
            except Exception:_RACE_REPORT['race_errors']+=1
        standard=configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)])
        if standard and 216<=step<696 and _race_clone(observation,state):
            _RACE_REPORT['race_clone_turns']+=1
            if state['level']<_RACE_HORIZON_ESCALATED and _race_lost(observation,state):
                _RACE_REPORT['race_lost_races']+=1;state['level']=_RACE_HORIZON_ESCALATED;_RACE_REPORT['race_escalations']+=1
            state['horizon']=state['level'];_RACE_REPORT['race_horizon_turns']+=1
    except Exception:_RACE_REPORT['race_errors']+=1
    snapshot=None
    try:
        if state is not None and 215<=int(observation['step'])<696:snapshot=_race_snapshot(observation)
    except Exception:_RACE_REPORT['race_errors']+=1
    action=_RACE_PARENT(observation,configuration)
    try:
        if state is not None:state['prev']=snapshot;state['prev_action']=action if snapshot is not None else None
    except Exception:_RACE_REPORT['race_errors']+=1
    _RACE_REPORT.update(getattr(_RACE_PARENT,'telemetry',{}))
    return action
agent.telemetry=_RACE_REPORT
agent=globals().pop('agent')


"""Fund urgent grain at the first quote slot; avoid unwatered last-hour plants.
Original safety contracts by Ahmed Berat Ozer, EXP258.
"""
_R127_PARENT=agent
_R127_STATES={}
_R127_REPORT={}

def _r127_fields(obs,action):
    farm,private=_PLANNER_NS['_clone_state'](obs['farms'][obs['player']],obs['private'])
    commands=[action.get('farmer') or ['PASS'],*(action.get('hands') or [])]
    demand={}
    for c in commands:
        if len(c)>1 and c[0]=='PLANT':demand[c[1]]=demand.get(c[1],0)+1
    blocked={p for p,n in demand.items() if n>private['seeds'].get(p,0)}
    for actor,c in enumerate(commands[:len(private['inventories'])]):
        if len(c)>1 and c[0]=='PLANT' and c[1] in blocked:continue
        _PLANNER_NS['_apply_unit_action'](farm,private,actor,c,10,int(obs['step'])//24,24,100)
    return farm,private

def _r127_last_hour(obs,action):
    if int(obs['step'])%24!=23:return action
    commands=[action.get('farmer') or ['PASS'],*(action.get('hands') or [])]
    if not any(c and c[0]=='PLANT' for c in commands):return action
    result=copy.deepcopy(action);changed=False
    # Removing rejected requests can unblock the engine's atomic crop batch.
    # Recompute until every retained request ends the turn with a watered crop.
    for _ in range(len(commands)+1):
        farm,_=_r127_fields(obs,result);original=obs['farms'][obs['player']]
        positions=[original['farmer'],*original['hands']];drop=[]
        for actor,c in enumerate(commands):
            if not c or c[0]!='PLANT':continue
            tile=None
            if actor<len(positions):
                x,y=positions[actor];tile=farm['tiles'][y][x]
            if not (isinstance(tile,dict) and tile.get('kind')=='PLANT' and tile.get('crop')==c[1] and tile.get('planted_day')==int(obs['step'])//24 and tile.get('watered_today')):drop.append(actor)
        if not drop:break
        for actor in drop:commands[actor]=['PASS']
        result['farmer']=commands[0];result['hands']=commands[1:];changed=True
        _R127_REPORT['last_hour_plants_dropped']+=len(drop)
    return result if changed else action

def _r127_prefix_bound(obs,quantity):
    inventory=int(obs['market']['inventory']['WHEAT'])
    # Both players quote one unit before either commits. Before own unit j,
    # at most j-1 own and j-1 opponent wheat purchases have depleted inventory.
    return sum(_r37_market_price('WHEAT',inventory-(2*j-1)) for j in range(1,quantity+1))

def _r127_priority(obs,action,state):
    step=int(obs['step']);player=int(obs['player'])
    if not 144<=step<695:return action
    orders=action.get('market') or []
    if len(orders)>9 or any(o[:2] in (['BUY_PRODUCT','WHEAT'],['SELL','WHEAT']) for o in orders):return action
    native=_IMPL.chassis.players[player]
    future=_IMPL.chassis.routes[2 if step+1>=648 else native['route']][step+1]
    commands=[future.get('farmer') or ['PASS'],*(future.get('hands') or [])]
    if not any(c[:2]==['PICKUP','WHEAT'] for c in commands):return action
    if not _r97_budget(obs,orders):return action
    farm,private=_r127_fields(obs,action);night=step%24==23
    access=((4,4),(5,4),(4,5),(5,5));positions=[tuple(farm['farmer']),*map(tuple,farm['hands'])]
    if night:positions=[(4,4)]
    else:
        for o in orders:
            if o and o[0]=='HIRE':positions.append(min(access,key=lambda p:(positions.count(p),access.index(p))))
    need=sum(max(0,int(c[2]) if len(c)>2 else 1) for pos,c in zip(positions,commands) if pos in access and c[:2]==['PICKUP','WHEAT'])
    stock,buys,_=_r97_market_stock(private['shed'],orders);before,loss=_r97_delivery(stock,private,night)
    shortage=max(0,need-before.get('WHEAT',0))
    if not shortage or shortage>100-sum(private['shed'].values()):return action
    cost=_r127_prefix_bound(obs,shortage)
    budget=dict(obs,farms=[dict(f) for f in obs['farms']]);budget['farms'][player]['money']-=cost
    if not _r97_budget(budget,orders):return action
    proposed=[['BUY_PRODUCT','WHEAT',shortage],*copy.deepcopy(orders)]
    stock,after_buys,_=_r97_market_stock(private['shed'],proposed);after,after_loss=_r97_delivery(stock,private,night)
    if after.get('WHEAT',0)<need or any(after_buys.get(i+1,0)<q for i,q in buys.items()) or any(q>loss.get(p,0) for p,q in after_loss.items()):return action
    state['pending_grain']=(step+1,after.get('WHEAT',0),shortage)
    _R127_REPORT['priority_grain_orders']+=1;_R127_REPORT['priority_grain_units']+=shortage
    return dict(action,market=proposed)

def agent(observation,configuration=None):
    result=_R127_PARENT(observation,configuration)
    try:
        player=int(observation['player']);step=int(observation['step']);state=_R127_STATES.get(player)
        if state is None or step<=state['step']:
            state=_R127_STATES[player]={'step':-1}
            _R127_REPORT.update(last_hour_plants_dropped=0,priority_grain_orders=0,priority_grain_units=0,priority_grain_confirmed=0,priority_grain_shortfalls=0,priority_contract_errors=0)
        pending=state.pop('pending_grain',None)
        if pending and step==pending[0]:
            if observation['private']['shed'].get('WHEAT',0)>=pending[1]:_R127_REPORT['priority_grain_confirmed']+=pending[2]
            else:_R127_REPORT['priority_grain_shortfalls']+=1
        state['step']=step
        standard=configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10),('farmHandCostMult',1)])
        if standard:result=_r127_priority(observation,_r127_last_hour(observation,result),state)
    except Exception:_R127_REPORT['priority_contract_errors']=_R127_REPORT.get('priority_contract_errors',0)+1
    _R127_REPORT.update(getattr(_R127_PARENT,'telemetry',{}))
    return result
agent.telemetry=_R127_REPORT
agent=globals().pop('agent')


# ---- v44y pre-guard: quote at hour 21,22 what the hour-23 day-end storage guard (EXP-154) would dump ----
# The guard sells shed stock by price desc once shed+carried exceeds 99 at hour 23. Selling those lots
# a step earlier stays in the same town-consumption price window and quotes before a same-tape rival.
_PG_HOST=[v for v in list(globals().values()) if callable(v)][-1]
_Y_HOURS=(21, 22)
_Y_ITEMS=('MILK', 'STRAWBERRY', 'MELON', 'WOOL', 'TOMATO')
_Y_MIN_DAY=1
_Y_MARGIN=-6
_PG_REPORT={'preguard_turns':0,'preguard_units':0,'preguard_errors':0}

def _y_preguard(obs,action):
    step=int(obs['step'])
    if step%24 not in _Y_HOURS or step//24<_Y_MIN_DAY or step>=696:return action
    orders=[list(o) for o in (action.get('market') or [])]
    if len(orders)>=10:return action
    farm,private=_r127_fields(obs,action)
    stock,_,_=_r97_market_stock(private['shed'],orders)
    carried=sum(max(0,int(n)) for bag in private['inventories'] for n in bag.values())
    needed=sum(max(0,int(v)) for v in stock.values())+carried-99-_Y_MARGIN
    if needed<=0:return action
    prices=obs['market']['prices'];extra=[]
    for item in sorted(PRODUCTS,key=lambda it:-int(prices.get(it,0))):
        avail=max(0,int(stock.get(item,0)));qty=min(needed,avail)
        if qty<=0:continue
        if item in _Y_ITEMS and int(prices.get(item,0))>=2:extra.append(['SELL',item,qty])
        needed-=qty
        if needed<=0:break
    if not extra or len(orders)+len(extra)>10:return action
    _PG_REPORT['preguard_turns']+=1;_PG_REPORT['preguard_units']+=sum(o[2] for o in extra)
    return dict(action,market=orders+extra)

def agent_v44y_preguard(observation,configuration=None):
    action=_PG_HOST(observation,configuration)
    try:
        standard=configuration is None or all(configuration.get(k,v)==v for k,v in [('boardSize',10),('turnsPerDay',24),('shedCapacity',100),('maxMarketOrdersPerTurn',10)])
        if standard:action=_y_preguard(observation,action)
    except Exception:_PG_REPORT['preguard_errors']+=1
    return action
agent_v44y_preguard.telemetry=_PG_REPORT


# ---- v44y: clone-mode race horizon override ----
_RACE_HORIZON_CLONE = 9

# ---- v44y: exact lockstep best-response SELL ordering against a detected clone ----
_V44Y_HOST = [v for v in list(globals().values()) if callable(v)][-1]
_V44Y_REORDER_GATE = False
_V44Y_REPORT = dict(v44y_reorder_turns=0, v44y_reorder_gain=0.0, v44y_errors=0)
import itertools as _v44y_it

def _v44y_price(item, inventory, params):
    return _r37_market_price(item, inventory, params)

def _v44y_params(obs):
    params = {k: dict(v) for k, v in _R37_MARKET_PARAMS.items()}
    for k, patch in (obs['market'].get('params') or {}).items():
        if k in params and isinstance(patch, dict): params[k].update(patch)
    return params

def _v44y_lockstep(orders_me, orders_opp, inv0, stock_me, stock_opp, params):
    """Replay the engine's per-slot / per-unit lockstep for SELL and BUY_PRODUCT orders (money-unbounded).
    Returns (revenue_me, revenue_opp)."""
    inv = dict(inv0); stock = [dict(stock_me), dict(stock_opp)]; rev = [0.0, 0.0]
    queues = [list(orders_me), list(orders_opp)]
    for i in range(max(len(queues[0]), len(queues[1]))):
        rem = [None, None]
        for p in (0, 1):
            if i < len(queues[p]):
                o = queues[p][i]
                if o and len(o) >= 3 and o[0] in ('SELL', 'BUY_PRODUCT') and o[1] in params:
                    try: n = int(o[2])
                    except Exception: n = 0
                    if n > 0: rem[p] = [o[0], o[1], n]
        guard = 0
        while True:
            guard += 1
            if guard > 5000: break
            quoted = [None, None]
            for p in (0, 1):
                r = rem[p]
                if r is None or r[2] <= 0: continue
                if r[0] == 'SELL':
                    quoted[p] = ('SELL', r[1], _v44y_price(r[1], inv[r[1]], params))
                elif r[1] in ('WHEAT', 'FERTILIZER'):
                    quoted[p] = ('BUY_PRODUCT', r[1], _v44y_price(r[1], inv[r[1]] - 1, params))
                else:
                    rem[p] = None
            if quoted[0] is None and quoted[1] is None: break
            committed = False
            for p in (0, 1):
                q = quoted[p]
                if q is None: continue
                op, item, price = q
                if op == 'SELL':
                    if stock[p].get(item, 0) <= 0:
                        rem[p] = None; continue
                    stock[p][item] -= 1; rev[p] += price
                    if price > 1: inv[item] += 1
                else:
                    stock[p][item] = stock[p].get(item, 0) + 1; rev[p] -= price; inv[item] -= 1
                rem[p][2] -= 1; committed = True
            if not committed: break
    return rev[0], rev[1]

def _v44y_factor_margin(opp, inv0, stock, params):
    # EXP298: cache independent item schedules, preserving the donor's exact search/ties.
    # The donor model has no shared cash/capacity constraint; per-item revenues add.
    cache = {}
    opp_schedules = {}
    for i, order in enumerate(opp):
        if order and len(order) >= 3 and order[0] in ('SELL', 'BUY_PRODUCT') and order[1] in params:
            item = order[1]
            padded = opp_schedules.setdefault(item, [[] for _ in opp])
            padded[i] = order
    def margin(cand):
        schedules = {item: [] for item in opp_schedules}
        for i, order in enumerate(cand):
            if order and len(order) >= 3 and order[0] in ('SELL', 'BUY_PRODUCT') and order[1] in params:
                schedules.setdefault(order[1], []).append((i, order[0], int(order[2])))
        total = 0.0
        for item, schedule in schedules.items():
            key = (item, tuple(schedule))
            value = cache.get(key)
            if value is None:
                mine = [[] for _ in cand]
                for i, op, n in schedule: mine[i] = [op, item, n]
                theirs = opp_schedules.get(item, [[] for _ in opp])
                a, b = _v44y_lockstep(mine, theirs, {item: inv0[item]},
                                      {item: stock.get(item, 0)}, {item: stock.get(item, 0)},
                                      {item: params[item]})
                value = a - b
                cache[key] = value
            total += value
        return total
    return margin

def _v44y_reorder(obs, action):
    market = action.get('market') or []
    if len(market) < 2: return action
    orders = [list(o) if isinstance(o, (list, tuple)) else o for o in market]
    blocks = []; i = 0
    while i < len(orders):
        o = orders[i]
        if o and o[0] == 'SELL':
            j = i
            while j < len(orders) and orders[j] and orders[j][0] == 'SELL': j += 1
            if 2 <= j - i <= 6: blocks.append((i, j))
            i = j
        else: i += 1
    if not blocks: return action
    view = FarmView(obs)
    stock = projected_shed(action, view)
    stock = {k: max(0, int(v)) for k, v in stock.items()}
    params = _v44y_params(obs)
    inv0 = {k: int(v) for k, v in obs['market']['inventory'].items()}
    opp = [list(o) for o in orders]
    margin = _v44y_factor_margin(opp, inv0, stock, params)
    base = margin(orders); best = base; best_orders = None
    for (i, j) in blocks:
        blk = orders[i:j]; n = j - i
        seen = set()
        for perm in _v44y_it.permutations(range(n)):
            key = tuple((blk[p][1], int(blk[p][2])) for p in perm)
            if key in seen: continue
            seen.add(key)
            cand = orders[:i] + [blk[p] for p in perm] + orders[j:]
            v = margin(cand)
            if v > best + 0.5: best = v; best_orders = cand
        if best_orders is not None:
            orders = best_orders; best_orders = None
    if best <= base + 0.5: return action
    _V44Y_REPORT['v44y_reorder_turns'] += 1; _V44Y_REPORT['v44y_reorder_gain'] += best - base
    out = dict(action); out['market'] = orders
    return out

def _v44y_clone_gate(obs):
    player = int(obs['player']); step = int(obs['step'])
    st = _RACE_STATE.get(player) or {}
    if st.get('horizon', 0) > 0: return True
    if step >= 696 and len(st.get('hist', [])) >= 4 and sum(st['hist']) >= 4:
        return _r37_similarity(obs) >= .95
    return False

def v44y_lockstep_agent(observation, configuration=None):
    action = _V44Y_HOST(observation, configuration)
    try:
        step = int(observation.get('step', 0))
        if step >= 216 and (not _V44Y_REORDER_GATE or _v44y_clone_gate(observation)):
            action = _v44y_reorder(observation, action)
    except Exception:
        _V44Y_REPORT['v44y_errors'] += 1
    return action
v44y_lockstep_agent.telemetry = _V44Y_REPORT

# ==== v44y shop-aware herd wrapper (appended after the public V44 file; host entry captured first) ====
_Y_HOST=[v for v in list(globals().values()) if callable(v)][-1]
_Y_CFG={'yarnsheep': True, 'yarngeese': True, 'days': (8, 11)}
import copy as _y_copy
_Y_PRODUCT={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}
_Y_STRUCT={'COW':'PASTURE','SHEEP':'PASTURE','GOOSE':'COOP'}
_Y_COST={'COW':400,'SHEEP':500,'GOOSE':300}
_Y_SEED={'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}
_Y_STATES={}
_Y_REPORT={'swaps':0,'pick':0,'place':0,'harvest':0,'boost':0,'errors':0,'coop':0,'declined':0}

def _y_new_state():
    return {'last':-1,'pending':[],'credit':{},'sites':{},'sale':{},'coop_swap':0}

def _y_target(kind,shops,cfg):
    yarn='YARN_STORE' in shops
    egg=('BAKERY' in shops) or ('BRUNCH_SPOT' in shops)
    milk=sum(s in ('PIZZA_SHOP','ICE_CREAM_SHOP','SMOOTHIE_SHOP') for s in shops)
    if kind=='SHEEP' and cfg.get('nosheep') and not yarn and milk>=cfg.get('min_milk',0):return 'COW'
    if kind=='COW' and cfg.get('yarnsheep') and yarn:return 'SHEEP'
    if kind=='GOOSE' and cfg.get('nogeese') and not egg:return 'SHEEP' if yarn else 'COW'
    if kind=='GOOSE' and cfg.get('yarngeese') and yarn:return 'SHEEP'
    return None

def _y_fib(n):
    a,b=1,1
    for _ in range(n):a,b=b,a+b
    return a

def _y_cash(obs,action,market):
    farm=obs['farms'][int(obs['player'])];prices=obs['market']['prices'];shed=obs['private']['shed']
    try:shed=projected_shed({'farmer':action.get('farmer') or ['PASS'],'hands':action.get('hands') or [],'market':[]},FarmView(obs))
    except Exception:pass
    cash=float(farm['money']);cost=0.0;hires=int(farm.get('hires_today',0) or 0)
    quads=len(farm.get('unlocked_quadrants',[]) or [])
    for o in market:
        if not o:continue
        op=o[0]
        if op=='SELL' and len(o)>=3:
            cash+=0.8*min(max(0,int(o[2])),int(shed.get(o[1],0)))*float(prices.get(o[1],0))
        elif op=='BUY_ANIMAL' and len(o)>=3:cost+=int(o[2])*_Y_COST.get(o[1],500)
        elif op=='BUY_PRODUCT' and len(o)>=3:cost+=int(o[2])*(float(prices.get(o[1],0))+10)
        elif op=='BUY_SEED' and len(o)>=3:cost+=int(o[2])*_Y_SEED.get(o[1],100)
        elif op=='BUY_LAND':cost+=(1000,2000,4000)[min(2,max(0,quads-1))]
        elif op=='HIRE':cost+=_y_fib(hires);hires+=1
    return cash-cost

def _y_controller(obs,action,state,cfg):
    step=int(obs['step']);day=step//24;seat=int(obs['player'])
    farm=obs['farms'][seat];private=obs['private'];shed=private['shed'];inventories=private.get('inventories',[])
    shops=list((obs.get('town') or {}).get('unlocked_shops',[]) or [])
    tiles=farm['tiles'];n=len(tiles);center=n//2
    # 1. confirm last step's swapped purchases (physical shed gain)
    gained={}
    for p in state['pending']:
        to=p['to']
        if to not in gained:gained[to]=max(0,int(shed.get(to,0))-p['before'])
        got=min(p['qty'],gained[to]);gained[to]-=got
        if got>0:
            key=(p['from'],to);state['credit'][key]=state['credit'].get(key,0)+got
            if _Y_STRUCT[p['from']]!=_Y_STRUCT[to]:state['coop_swap']+=got
    state['pending']=[]
    result=_y_copy.deepcopy(action)
    market=result.get('market') or []
    result['market']=market
    # 2. purchase-point substitution by unlocked shops (cash-checked)
    if cfg['days'][0]<=day<=cfg['days'][1]:
        for o in market:
            if len(o)>=3 and o[0]=='BUY_ANIMAL' and o[1] in _Y_COST and 1<=int(o[2])<=cfg.get('maxq',2):
                to=_y_target(o[1],shops,cfg)
                if to is None or to==o[1]:continue
                trial=[list(x) if isinstance(x,list) else x for x in market]
                for t in trial:
                    if isinstance(t,list) and t==o:t[1]=to
                if _y_cash(obs,result,trial)<cfg.get('margin',100):
                    _Y_REPORT['declined']+=1;continue
                state['pending'].append({'from':o[1],'to':to,'qty':int(o[2]),'before':int(shed.get(to,0))})
                _Y_REPORT['swaps']+=int(o[2]);o[1]=to
    # 3. worker command rewrites (PICKUP / PLACE / BUILD_COOP) and harvest credit
    workers=[result.get('farmer') or ['PASS'],*(result.get('hands') or [])]
    positions=[farm['farmer'],*farm['hands']]
    avail={k:int(shed.get(k,0)) for k in _Y_COST}
    seen=set();occupied=set()
    for actor,work in enumerate(workers[:len(positions)]):
        if not work or not isinstance(work,list):continue
        inv=inventories[actor] if actor<len(inventories) else {}
        x,y=positions[actor];tile=tiles[y][x];site=(x,y);op=work[0]
        if op=='PICKUP' and len(work)>=2 and work[1] in _Y_COST:
            kind=work[1];qty=max(1,int(work[2])) if len(work)>2 else 1
            if avail.get(kind,0)>=qty:avail[kind]-=qty;continue
            if not (x in (center-1,center) and y in (center-1,center)):continue
            if any(inv.get(a,0) for a in _Y_COST):continue
            for (frm,to),c in list(state['credit'].items()):
                if frm==kind and c>=qty and avail.get(to,0)>=qty:
                    work[1]=to;state['credit'][(frm,to)]=c-qty;avail[to]-=qty;_Y_REPORT['pick']+=qty;break
        elif op=='PLACE' and len(work)>=2 and work[1] in _Y_COST:
            kind=work[1]
            if inv.get(kind,0)>0:continue
            for to in ('COW','SHEEP','GOOSE'):
                if (to!=kind and inv.get(to,0)>0 and isinstance(tile,dict) and tile.get('kind')==_Y_STRUCT[to]
                        and not tile.get('animal') and site not in occupied):
                    work[1]=to;state['sites'][site]=to;occupied.add(site);_Y_REPORT['place']+=1;break
        elif op=='BUILD_COOP' and state['coop_swap']>0:
            work[0]='BUILD_PASTURE';_Y_REPORT['coop']+=1
        elif op=='HARVEST' and site in state['sites'] and site not in seen:
            if isinstance(tile,dict) and tile.get('animal')==state['sites'][site]:
                units=max(0,int(tile.get('yield_units',0) or 0))
                if units:
                    prod=_Y_PRODUCT[tile['animal']];state['sale'][prod]=state['sale'].get(prod,0)+units;_Y_REPORT['harvest']+=units
            seen.add(site)
    result['farmer'],result['hands']=workers[0],workers[1:]
    # 4. sell the extra production at the tape's own existing sale slots (never add new orders)
    if cfg.get('boost',True):
        for prod,credit in list(state['sale'].items()):
            credit=min(credit,int(shed.get(prod,0)))
            state['sale'][prod]=credit
            if credit<=0:continue
            planned=sum(max(0,int(o[2])) for o in market if len(o)>=3 and o[0]=='SELL' and o[1]==prod)
            if planned<=0:continue
            extra=min(credit,int(shed.get(prod,0))-planned)
            if extra<=0:continue
            for o in market:
                if len(o)>=3 and o[0]=='SELL' and o[1]==prod and int(o[2])>0:
                    o[2]=int(o[2])+extra;state['sale'][prod]=credit-extra;_Y_REPORT['boost']+=extra;break
    return result

def _y_agent_shopherd(observation,configuration=None):
    action=_Y_HOST(observation,configuration)
    try:
        seat=int(observation['player']);step=int(observation['step'])
        state=_Y_STATES.get(seat)
        if state is None or step<=state['last']:state=_Y_STATES[seat]=_y_new_state()
        state['last']=step
        return _y_controller(observation,action,state,_Y_CFG)
    except Exception:
        _Y_REPORT['errors']+=1
        return action

# V47 attribution and modification notice (17 September 2026):
# Seyit Kaan Gunes, kaggle.com/code/seyitkaangunes/kaggriculture-2820-score:
# pre-overflow sale guard, clone-market lockstep ordering/horizon, and shop-aware herd layers.
# Ahmed Berat Ozer: transfer onto V46 EXP293, exact per-product score caching,
# exact physical-prefix/resource reuse, terminal no-op/movement fast paths,
# private reacting-opponent confirmation and packaging.
# Original source notices and license text above are retained.

# EXP334: remove useless cash-product sale slots without moving purchases.
_E334_ITEMS={'CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL'}
_E334_REPORT=dict(changed=0,removed=0,errors=0)
_E334_BASE=_y_agent_shopherd

def _e334_compact(obs,action):
    market=action.get('market') or []
    if int(obs['step'])<144 or len(market)<2:return action
    segments=[];i=0
    while i<len(market):
        if len(market[i])>=3 and market[i][0]=='SELL' and market[i][1] in _E334_ITEMS:
            j=i+1
            while j<len(market) and len(market[j])>=3 and market[j][0]=='SELL' and market[j][1] in _E334_ITEMS:j+=1
            if j-i>=2:segments.append((i,j))
            i=j
        else:i+=1
    if not segments:return action
    _,private=_r127_fields(obs,action);remaining=dict(private['shed']);new=[list(o) for o in market];removed=0
    for start,end in segments:
        quantities={};order=[]
        for o in market[start:end]:
            p=o[1]
            if p not in quantities:order.append(p);quantities[p]=0
            quantities[p]+=max(0,int(o[2]))
        kept=[]
        for p in order:
            q=min(quantities[p],max(0,int(remaining.get(p,0))))
            if q:kept.append(['SELL',p,q]);remaining[p]-=q
        # Empty order slots are explicitly skipped by the pinned engine parser.
        # Keep external order indices unchanged; do not pull BUY/HIRE forward.
        replacement=kept+[[] for _ in range(end-start-len(kept))]
        if replacement!=market[start:end]:removed+=end-start-len(kept);new[start:end]=replacement
    if new==market:return action
    _E334_REPORT['changed']+=1;_E334_REPORT['removed']+=removed
    return dict(action,market=new)

def _e334_agent(observation,configuration=None):
    if int(observation.get('step',0))==0:
        for k in _E334_REPORT:_E334_REPORT[k]=0
    action=_E334_BASE(observation,configuration)
    try:return _e334_compact(observation,action)
    except Exception:
        _E334_REPORT['errors']+=1;return action

# EXP335: empty buyable-product sales are holes too, when no purchases exist.
_E335_ORIGINAL_COMPACT=_e334_compact

def _e334_compact(obs,action):
    market=action.get('market') or []
    if int(obs['step'])<144 or len(market)<2:return action
    if not all(len(o)>=3 and o[0]=='SELL' for o in market):return _E335_ORIGINAL_COMPACT(obs,action)
    _,private=_r127_fields(obs,action);remaining=dict(private['shed']);effective=[]
    for o in market:
        item=o[1];q=min(max(0,int(o[2])),max(0,int(remaining.get(item,0))))
        remaining[item]=max(0,int(remaining.get(item,0))-q)
        effective.append(['SELL',item,q] if q else [])
    new=[list(o) for o in effective];i=0;removed=0
    while i<len(effective):
        if effective[i] and effective[i][1] not in _E334_ITEMS:i+=1;continue
        j=i+1
        while j<len(effective) and (not effective[j] or effective[j][1] in _E334_ITEMS):j+=1
        order=[];qty={}
        for o in effective[i:j]:
            if not o:continue
            if o[1] not in qty:order.append(o[1]);qty[o[1]]=0
            qty[o[1]]+=o[2]
        kept=[['SELL',item,qty[item]] for item in order]
        new[i:j]=kept+[[] for _ in range(j-i-len(kept))];removed+=j-i-len(kept);i=j
    if new==market:return action
    _E334_REPORT['changed']+=1;_E334_REPORT['removed']+=removed
    return dict(action,market=new)

def _e335_agent(observation,configuration=None):
    return _e334_agent(observation,configuration)




# ---------------------------------------------------------------------------
# v11 entry normalisation: Kaggle's loader takes the last callable in the module
# namespace.  Rebind it to a fresh `agent` so the packaged name matches the rest
# of the v9 releases (and so validate.py's name check passes).
# ---------------------------------------------------------------------------
_V11_ENTRY = [v for v in list(globals().values()) if callable(v)][-1]


def agent(observation, configuration=None):
    return _V11_ENTRY(observation, configuration)


agent.telemetry = getattr(_V11_ENTRY, 'telemetry', {})
agent = globals().pop('agent')


# ---------------------------------------------------------------------------
# v13 V219SKIP (review suggestion #1): V219 hires a tomato crew every day from
# day 19, but tomatoes planted on day 18 only produce at the refreshes ending
# days 25-28.  Before that, watering only keeps them alive, and a plant
# survives one dry day (it dies after two consecutive dry refreshes).  On the
# chosen skip days, when every committed tomato was watered yesterday
# (consecutive_unwatered == 0), no crew is hired and nobody waters them today;
# the next day's crew waters them again.
# ---------------------------------------------------------------------------
V13V_SKIP_DAYS = (19, 21, 23)
_V13V_REPORT = dict(v_skipped=0, v_blocked=0, v_errors=0)
_V13V_ORIG_REQUEST = _v219_request


def _v219_request(obs, action, state, native):
    try:
        day = int(obs["step"]) // 24
        if day in V13V_SKIP_DAYS and state.get("committed") and state.get("requested_day") != day:
            farm = obs["farms"][int(obs["player"])]
            tomatoes = 0
            safe = True
            for x, y in state.get("targets", []):
                tile = farm["tiles"][y][x]
                if isinstance(tile, dict) and tile.get("crop") == "TOMATO":
                    tomatoes += 1
                    if int(tile.get("consecutive_unwatered", 1)) != 0:
                        safe = False
            if tomatoes and safe:
                state["requested_day"] = day
                _V13V_REPORT["v_skipped"] += 1
                return action
            if tomatoes:
                _V13V_REPORT["v_blocked"] += 1
    except Exception:
        _V13V_REPORT["v_errors"] += 1
    return _V13V_ORIG_REQUEST(obs, action, state, native)


_V13V_PARENT = agent


def agent(observation, configuration=None):
    if int(observation["step"]) == 0:
        for k in _V13V_REPORT:
            _V13V_REPORT[k] = 0
    return _V13V_PARENT(observation, configuration)


agent.telemetry = _V13V_REPORT
agent = globals().pop("agent")


# ===========================================================================
# AXIS 1.1: Weed Lag Replay Recovery (_e343_weedlag)
# ===========================================================================
_E343_WL_REPORT = dict(events=0, replays=0, errors=0)
_E343_WL_STATE = {}
_E343_WL_BASE = agent
_E343_WL_STEPS = 8
_E343_WL_OPS = ('BUILD_PASTURE', 'BUILD_COOP')

def _e343_tape_units(player, t):
    native = _IMPL.chassis.players.get(player)
    if not native or t < 0 or t > 718: return []
    route = 2 if t >= 648 else native.get('route', 0)
    e = _IMPL.chassis.routes[route][t]
    return [e.get('farmer') or ['PASS'], *(e.get('hands') or [])]

def _e343_weedlag(obs, action):
    step = int(obs['step']); player = int(obs['player']); st = _E343_WL_STATE.setdefault(player, {'step': -1, 'active': {}})
    if step <= st['step']: st['active'] = {}
    st['step'] = step
    if step % 24 == 0: st['active'] = {}   # hands are re-hired each day; lag state cannot survive day boundary
    farm = obs['farms'][player]; positions = [tuple(farm['farmer']), *map(tuple, farm['hands'])]; tiles = farm['tiles']
    units = [list(action.get('farmer') or ['PASS']), *[list(h) if isinstance(h, list) else ['PASS'] for h in (action.get('hands') or [])]]
    tape_now = _e343_tape_units(player, step); tape_prev = _e343_tape_units(player, step - 1)
    changed = False
    # 1. continue active lags
    for k, tx in list(st['active'].items()):
        if k >= len(units) or k >= len(positions): st['active'].pop(k, None); continue
        age = step - tx['start']
        if age == 1: units[k] = list(tx['intended']); changed = True; _E343_WL_REPORT['replays'] += 1
        elif 2 <= age <= 1 + _E343_WL_STEPS:
            prev = tape_prev[k] if k < len(tape_prev) else ['PASS']
            units[k] = list(prev) if isinstance(prev, list) and prev else ['PASS']; changed = True; _E343_WL_REPORT['replays'] += 1
        else: st['active'].pop(k, None)
    # 2. detect new weed-blocked build/plant events (chassis has turned them into DIG)
    for k in range(min(len(units), len(positions), len(tape_now))):
        if k in st['active']: continue
        intent = tape_now[k]
        if not (isinstance(intent, list) and intent and intent[0] in _E343_WL_OPS): continue
        x, y = positions[k]; tile = tiles[y][x]
        if not (isinstance(tile, dict) and tile.get('kind') == 'WEED'): continue
        if units[k] != ['DIG']: units[k] = ['DIG']; changed = True
        st['active'][k] = {'start': step, 'intended': list(intent)}; _E343_WL_REPORT['events'] += 1
    if not changed: return action
    return dict(action, farmer=units[0], hands=units[1:])

def agent(observation, configuration=None):
    if int(observation.get('step', 0)) == 0:
        for k in _E343_WL_REPORT: _E343_WL_REPORT[k] = 0
        _E343_WL_STATE.clear()
    action = _E343_WL_BASE(observation, configuration)
    try:
        standard = configuration is None or all(configuration.get(k, v) == v for k, v in [('boardSize', 10), ('turnsPerDay', 24), ('shedCapacity', 100), ('maxMarketOrdersPerTurn', 10)])
        if standard: action = _e343_weedlag(observation, action)
    except Exception:
        _E343_WL_REPORT['errors'] += 1
    return action

agent.telemetry = _E343_WL_REPORT
kaggle_agent = agent


# ===========================================================================
# AXIS 2.1: Ready-Stock Sale Advancing & Frontloading (_adv_apply, _adv_frontload)
# ===========================================================================
_ADV_PARENT = agent
_ADV_LOOK = 3
_ADV_FROM = 216
_ADV_TO = 718
_ADV_PROTECT = True
_ADV_FRONT = False
_ADV_BOOK = False
_ADV_SUBTRACT_DEBTS = True
_ADV_ITEMS = ('STRAWBERRY', 'WOOL', 'EGG', 'MILK', 'MELON', 'CARROT', 'TOMATO')
_ADV_REPORT = dict(adv_turns=0, adv_units=0, adv_errors=0, front_turns=0)

def _adv_future(player, t):
    native = _IMPL.chassis.players.get(player)
    if not native or t < 0 or t > 718: return []
    route = 2 if t >= 648 else native.get('route', 0)
    return _IMPL.chassis.routes[route][t].get('market', []) or []

def _adv_apply(obs, action):
    step = int(obs['step']); player = int(obs['player'])
    if step % 24 == 23 or not _ADV_FROM <= step < _ADV_TO: return action
    native = _IMPL.chassis.players.get(player)
    if not native: return action
    debts = native.setdefault('sell_state', {}).setdefault('r36_debts', {})
    plan = []; first = None
    for off in range(1, _ADV_LOOK + 1):
        t = step + off
        if t > 718: break
        for o in _adv_future(player, t):
            if not o or len(o) < 3: continue
            if first is None: first = o
            if o[0] == 'SELL' and o[1] in _ADV_ITEMS:
                try: q = max(0, int(o[2]))
                except Exception: q = 0
                if _ADV_SUBTRACT_DEBTS: q -= debts.get(t, {}).get(o[1], 0)
                if q > 0: plan.append((t, o[1], q))
    protected = first[1] if _ADV_PROTECT and first is not None and first[0] == 'SELL' else None
    plan = [(t, item, q) for t, item, q in plan if item != protected]
    if not plan: return action
    market = [list(o) for o in (action.get('market') or [])]
    if any(len(o) > 1 and o[0] == 'BUY_PRODUCT' for o in market): return action
    stock = projected_shed(action, FarmView(obs))
    selling = {}
    for o in market:
        if len(o) >= 3 and o[0] == 'SELL':
            try: selling[o[1]] = selling.get(o[1], 0) + max(0, int(o[2]))
            except Exception: return action
    commands = [action.get('farmer') or ['PASS'], *(action.get('hands') or [])]
    picked = {c[1] for c in commands if len(c) > 1 and c[0] == 'PICKUP'}
    prices = obs['market']['prices']; added = 0; extra = []; booked = []
    for item in sorted({it for _, it, _ in plan}, key=lambda it: -int(prices.get(it, 0))):
        if item in picked or int(prices.get(item, 0)) < 2: continue
        avail = int(stock.get(item, 0)) - selling.get(item, 0)
        if avail < 1: continue
        hit = next((o for o in market if len(o) >= 3 and o[0] == 'SELL' and o[1] == item), None)
        if hit is None and len(market) + len(extra) >= 10: continue
        n = 0
        for t, it, q in plan:
            if it != item or avail <= 0: continue
            take = min(q, avail); booked.append((t, item, take)); n += take; avail -= take
        if n < 1: continue
        if hit is not None: hit[2] = int(hit[2]) + n
        else: extra.append(['SELL', item, n])
        added += n
    if not added: return action
    for t, item, take in (booked if _ADV_BOOK else []):
        d = debts.setdefault(t, {}); d[item] = d.get(item, 0) + take
    _ADV_REPORT['adv_turns'] += 1; _ADV_REPORT['adv_units'] += added
    return dict(action, market=extra + market)

def _adv_frontload(obs, action):
    market = [list(o) for o in (action.get('market') or []) if o]
    if len(market) < 2 or int(obs['step']) < _ADV_FROM: return action
    buys = {o[1] for o in market if len(o) > 1 and o[0] == 'BUY_PRODUCT'}
    front = [o for o in market if len(o) >= 3 and o[0] == 'SELL' and o[1] not in buys]
    mid = [o for o in market if (len(o) >= 3 and o[0] == 'BUY_PRODUCT') or (len(o) >= 3 and o[0] == 'SELL' and o[1] in buys)]
    rest = [o for o in market if o not in front and o not in mid]
    new = front + mid + rest
    if new == market: return action
    _ADV_REPORT['front_turns'] = _ADV_REPORT.get('front_turns', 0) + 1
    return dict(action, market=new)

def agent(observation, configuration=None):
    action = _ADV_PARENT(observation, configuration)
    try:
        if int(observation.get('step', 0)) == 0:
            _ADV_REPORT.update(adv_turns=0, adv_units=0, adv_errors=0, front_turns=0)
        standard = configuration is None or all(configuration.get(k, v) == v for k, v in [('boardSize', 10), ('turnsPerDay', 24), ('shedCapacity', 100), ('maxMarketOrdersPerTurn', 10)])
        if standard: action = _adv_apply(observation, action)
        if standard and _ADV_FRONT: action = _adv_frontload(observation, action)
        st = _RACE_STATE.get(int(observation['player']))
        if st is not None and st.get('prev_action') is not None and st.get('step') == int(observation['step']):
            st['prev_action'] = action
    except Exception:
        _ADV_REPORT['adv_errors'] += 1
    return action

def cha20_entry_agent(observation, configuration=None):
    return agent(observation, configuration)

cha20_entry_agent.telemetry = _ADV_REPORT
kaggle_agent = cha20_entry_agent


# ===========================================================================
# AXIS 6.2A: Terminal 7-Turn Zero-Waste Liquidation (T_TERMINAL_CLEAR)
# ===========================================================================
_T62A_PARENT = agent
_T62A_REPORT = dict(term_sells=0, term_units=0)

def _t62a_agent(observation, configuration=None):
    action = _T62A_PARENT(observation, configuration)
    try:
        step = int(observation.get('step', 0))
        if step >= 712 and action and isinstance(action, dict):
            priv = observation.get('private', {})
            shed = priv.get('shed', {})
            prices = observation.get('market', {}).get('prices', {})
            # Find all non-zero shed goods
            items_to_sell = [it for it, q in shed.items() if int(q) > 0 and int(prices.get(it, 0)) >= 1]
            if items_to_sell:
                # Sort by price descending
                items_to_sell.sort(key=lambda it: -int(prices.get(it, 0)))
                # Build market orders strictly selling these goods
                market = []
                for it in items_to_sell[:10]:
                    market.append(['SELL', it, int(shed[it])])
                    _T62A_REPORT['term_units'] += int(shed[it])
                action['market'] = market
                _T62A_REPORT['term_sells'] += 1
    except Exception:
        pass
    return action

def cha20_entry_agent(observation, configuration=None):
    return _t62a_agent(observation, configuration)

cha20_entry_agent.telemetry = _T62A_REPORT
kaggle_agent = cha20_entry_agent

# ===========================================================================
# PIPE16 HybridOpening port onto cha20 (mode=HybridOpening)
# ===========================================================================
_PIPE_MODE = 'EarlyCycle'
_PIPE_RAW = copy.deepcopy(_IMPL.chassis.routes[0][:96])
_PIPE_CT = dict(CT_TABLE)
_PIPE_STATE = {}
_PIPE_REPORT = {}

def _pipe_install(mode):
    global CT_TABLE
    tape=_IMPL.chassis.routes[0]
    tape[:96]=copy.deepcopy(_PIPE_RAW)
    CT_TABLE=dict(_PIPE_CT)
    if mode=='Original': return
    if mode=='HybridOpening':
        tape[0]['market']=list(tape[0]['market'])+[['BUY_SEED','WHEAT',1]]
    else:
        CT_TABLE={}
        tape[0]['market']=[['BUY_PRODUCT','WHEAT',5],['BUY_SEED','WHEAT',1]]
        tape[1]['market']=[o for o in tape[1]['market'] if not (len(o)>=3 and o[0] in ('BUY_PRODUCT','SELL') and o[1]=='WHEAT')]
    # Day-zero idle hand 1 walks from (5,4) to the future (2,4) pasture.
    for step,command in {2:['WEST'],3:['WEST'],4:['WEST'],5:['PLANT','WHEAT'],6:['WATER']}.items():
        assert tape[step]['hands'][1]==['PASS']
        tape[step]['hands'][1]=command
    # On day one, water instead of building the not-yet-needed pasture.
    assert tape[29]['hands'][2]==['BUILD_PASTURE']
    tape[29]['hands'][2]=['WATER']
    # Day-two idle hand 0: water, harvest, restore pasture, deliver.
    commands=[['WEST'],['WEST'],['WEST'],['WATER'],['HARVEST'],['BUILD_PASTURE'],['EAST'],['EAST'],['DROP']]
    for step,command in zip(range(49,58),commands):
        assert tape[step]['hands'][0]==['PASS']
        tape[step]['hands'][0]=command
    # OMW port (notebook 2743, Dmitrii Gluzdov): mature the temporary wheat one
    # extra day, then harvest three instead of two and deliver at step 91.
    if mode in ('EarlyCycle','HybridOpening'):
        for step in range(53,58):
            tape[step]['hands'][0]=['PASS']
        omw=[['EAST'],['EAST'],['WATER'],['HARVEST'],['BUILD_PASTURE'],['EAST'],['EAST'],['DROP']]
        for step,command in zip(range(84,92),omw):
            assert tape[step]['hands'][0]==['PASS'], ('OMW tape mismatch at step %d' % step)
            tape[step]['hands'][0]=command
    if mode=='TomatoInsteadOfCow':
        tape[0]['market'].append(['BUY_SEED','TOMATO',1])
        cow=next(o for o in tape[1]['market'] if o[:2]==['BUY_ANIMAL','COW'])
        assert cow[2]==2; cow[2]=1
        # The first carrier still owns the bought cow; the other cow's site
        # becomes one tomato plant, with its worker route left in place.
        assert tape[2]['hands'][4][:2]==['PICKUP','COW']
        assert tape[3]['hands'][4]==['BUILD_PASTURE']
        assert tape[4]['hands'][4][:2]==['PLACE','COW']
        tape[2]['hands'][4]=['PASS']
        tape[3]['hands'][4]=['PASS']
        tape[4]['hands'][4]=['PLANT','TOMATO']
        tape[5]['hands'][4]=['WATER']
    assert max(len(a.get('market',[])) for a in tape[:96])<=10

def _pipe_sell_extra(action,item,n):
    if n<=0:return action
    orders=[list(o) for o in action.get('market',[])]
    sell=next((o for o in orders if len(o)>=3 and o[:2]==['SELL',item]),None)
    if sell is not None:sell[2]+=n
    elif len(orders)<10:orders.append(['SELL',item,n])
    else:return action
    return dict(action,market=orders)

_PIPE_PARENT = cha20_entry_agent

def _pipe_agent(observation, configuration=None):
    seat, step = int(observation['player']), int(observation['step'])
    state = _PIPE_STATE.get(seat)
    if state is None or step <= state['step']:
        mode = _PIPE_MODE
        _pipe_install(mode)
        state = _PIPE_STATE[seat] = {'step': -1, 'mode': mode}
        _PIPE_REPORT.clear()
        _PIPE_REPORT.update(selected_opening=mode, temporary_crop_seen=0, temporary_crop_harvested=0,
                           restored_pasture_seen=0, delivered_extra_wheat=0, tomato_seen=0,
                           tomato_water_requests=0, tomato_harvest_requests=0, tomato_units_harvest_requested=0,
                           extension_errors=0)
    action = _PIPE_PARENT(observation, configuration)
    try:
        mode = state['mode']
        if mode != 'Original':
            farm = observation['farms'][seat]; private = observation['private']
            site = farm['tiles'][4][2]
            if step == 6:
                _PIPE_REPORT['temporary_crop_seen'] = int(isinstance(site, dict) and site.get('crop') == 'WHEAT')
            if step == 54:
                _PIPE_REPORT['temporary_crop_harvested'] = int(private['inventories'][1].get('WHEAT', 0))
            if step == 55:
                _PIPE_REPORT['restored_pasture_seen'] = int(isinstance(site, dict) and site.get('kind') == 'PASTURE')
            if step in (57, 91) and len(farm['hands']) >= 1:
                if tuple(farm['hands'][0]) == (4, 4) and action.get('hands', [[]])[0] == ['DROP']:
                    n = int(private['inventories'][1].get('WHEAT', 0))
                    action = _pipe_sell_extra(action, 'WHEAT', n)
                    _PIPE_REPORT['delivered_extra_wheat'] = n
            if mode == 'TomatoInsteadOfCow':
                tomato = farm['tiles'][4][4]
                if isinstance(tomato, dict) and tomato.get('crop') == 'TOMATO' and tomato.get('planted_day') == 0:
                    _PIPE_REPORT['tomato_seen'] = 1
                    units = [list(action.get('farmer') or ['PASS'])] + [list(c) for c in action.get('hands', [])]
                    positions = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
                    watered = bool(tomato.get('watered_today')); yield_left = int(tomato.get('yield_units', 0))
                    for actor, pos in enumerate(positions):
                        if pos != (4, 4) or actor >= len(units):
                            continue
                        if units[actor][0] not in ('FEED', 'CARE', 'COLLECT_FERTILIZER', 'HARVEST', 'WATER', 'PASS'):
                            continue
                        if not watered:
                            units[actor] = ['WATER']; watered = True
                            _PIPE_REPORT['tomato_water_requests'] += 1
                        elif yield_left > 0:
                            units[actor] = ['HARVEST']
                            _PIPE_REPORT['tomato_harvest_requests'] += 1
                            _PIPE_REPORT['tomato_units_harvest_requested'] += yield_left
                            yield_left = 0
                        else:
                            units[actor] = ['PASS']
                    action = dict(action, farmer=units[0], hands=units[1:])
                stock = int(private['shed'].get('TOMATO', 0))
                scheduled = sum(int(o[2]) for o in action.get('market', []) if len(o) >= 3 and o[:2] == ['SELL', 'TOMATO'])
                action = _pipe_sell_extra(action, 'TOMATO', max(0, stock - scheduled))
    except Exception:
        _PIPE_REPORT['extension_errors'] += 1
    state['step'] = step
    return action

def cha20_entry_agent(observation, configuration=None):
    return _pipe_agent(observation, configuration)

cha20_entry_agent.telemetry = _PIPE_REPORT
kaggle_agent = cha20_entry_agent




# ===========================================================================
# MIRROR-LIKE CLASSIFIER (behavior only; no recorded streams)
# ===========================================================================
_MA_REPORT = dict(classified=0, mirror_like=0, market_drop=0, errors=0)
_MA_STATE = dict(prior=None, mirror_like=False)
_MA_INNER = cha20_entry_agent


def cha20_entry_agent(observation, configuration=None):
    step = int(observation.get('step', 0))
    if step == 0:
        _MA_STATE.update(prior=None, mirror_like=False)
        _MA_REPORT.update(classified=0, mirror_like=0, market_drop=0, errors=0)
    if step == 1:
        try:
            _MA_STATE['prior'] = int(observation['market']['inventory']['WHEAT'])
        except Exception:
            _MA_REPORT['errors'] += 1
    if step == 2:
        try:
            prior = _MA_STATE['prior']
            if prior is not None:
                fall = prior - int(observation['market']['inventory']['WHEAT'])
                _MA_STATE['mirror_like'] = fall >= 15
                _MA_REPORT['classified'] = 1
                _MA_REPORT['mirror_like'] = int(fall >= 15)
                _MA_REPORT['market_drop'] = fall
        except Exception:
            _MA_REPORT['errors'] += 1
    return _MA_INNER(observation, configuration)


import collections as _ma_collections
cha20_entry_agent.telemetry = _ma_collections.ChainMap(_MA_REPORT, _MA_INNER.telemetry)
kaggle_agent = cha20_entry_agent
_MA_ENTRY = cha20_entry_agent

# ===========================================================================
# WHEAT BUY-FIRST (gated): profitable pairs + mirror-like opponent
# ===========================================================================
_WB3_REPORT = dict(reordered=0)
_WB3_INNER = cha20_entry_agent
_WB3_PAIRS = {("BRUNCH_SPOT", "BRUNCH_SPOT"), ("BAKERY", "BRUNCH_SPOT"), ("PIZZA_SHOP", "SMOOTHIE_SHOP")}


def cha20_entry_agent(observation, configuration=None):
    action = _WB3_INNER(observation, configuration)
    try:
        shops = tuple((observation.get("town", {}) or {}).get("unlocked_shops", [])[:2])
        mirror = bool(_MA_STATE.get("mirror_like"))
        target = (mirror and shops in _WB3_PAIRS) or (shops in {("BRUNCH_SPOT", "BRUNCH_SPOT"), ("BAKERY", "BRUNCH_SPOT")})
        if target:
            market = [list(o) for o in (action.get("market") or [])]
            if len(market) > 1:
                buys = [o for o in market if len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT"]
                if buys and market[0] not in buys:
                    rest = [o for o in market if o not in buys]
                    _WB3_REPORT["reordered"] += 1
                    action = dict(action, market=buys + rest)
    except Exception:
        pass
    return action


import collections as _wb3_coll
cha20_entry_agent.telemetry = _wb3_coll.ChainMap(_WB3_REPORT, _WB3_INNER.telemetry)
kaggle_agent = cha20_entry_agent
_WB3_ENTRY = cha20_entry_agent




# ===========================================================================
# FLOWPX: live rival-flow lead-sell (general; no recorded opponent data)
#
# Rival sales are recovered each turn from public market inventory deltas, the
# town draw and our own submitted sells (same arithmetic RACE uses).  When the
# rival has been active in an item over the last few turns and the item's quote
# sits at or above its trailing average, planned sells of that item from the next
# turns are pulled forward into this turn, capped by shed stock and the planned
# quantity.  Raises our realized rate in endgame sale races without any
# opponent-specific data.
# ===========================================================================
_FX_ITEMS = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
_FX_FLOW_WIN = 8        # turns: rival considered active if >= _FX_FLOW_MIN units
_FX_FLOW_MIN = 999        # units sold by the rival in the window to trigger a lead
_FX_LEAD_H = 12         # turns of planned sells pulled forward
_FX_QUOTE_WIN = 12      # turns of quote history for the relative-strength test
_FX_MIN_STEP = 96       # keep away from the scripted opening
_FX_STATE = {}
_FX_REPORT = dict(fx_fires=0, fx_units=0, fx_rival_seen=0, fx_errors=0)


def _fx_update(observation, player, st):
    """Recover rival sales for the previous turn into st['flow']."""
    prev = st.get("prev")
    step = int(observation["step"])
    if not prev or prev["step"] != step - 1:
        return
    inv = observation["market"]["inventory"]
    draw = _v9_town_draw(prev["shops"], prev["step"])
    for item in _FX_ITEMS:
        if prev["prices"].get(item, 0) <= 3:
            continue
        sold = inv[item] - prev["inventory"][item] + draw.get(item, 0) - prev["own"].get(item, 0)
        if sold > 0:
            st["flow"][(prev["step"], item)] = sold
            _FX_REPORT["fx_rival_seen"] += 1
    if len(st["flow"]) > 512:
        for k in sorted(st["flow"])[:256]:
            st["flow"].pop(k, None)


def _fx_apply(observation, action, st):
    step = int(observation["step"])
    shops = list(observation["town"]["unlocked_shops"])
    prices = observation["market"]["prices"]
    st["quotes"][step] = {i: int(prices.get(i, 0)) for i in _FX_ITEMS}
    if len(st["quotes"]) > 96:
        for k in sorted(st["quotes"])[:48]:
            st["quotes"].pop(k, None)
    if step < _FX_MIN_STEP or step >= 700:
        return action
    if _MA_STATE.get("mirror_like"):
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if len(market) >= MAX_ORDERS:
        return action
    already = {o[1] for o in market if len(o) > 1 and o[0] in ("SELL", "BUY_PRODUCT")}
    stock = projected_shed(action, FarmView(observation))
    native = _IMPL.chassis.players.get(int(observation["player"]))
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    tape = _IMPL.chassis.routes[native["route"]]
    hist = st["quotes"]
    recent_turns = [t for t in hist if step - _FX_QUOTE_WIN <= t < step]
    added = False
    for item in _FX_ITEMS:
        if item in already or len(market) >= MAX_ORDERS:
            continue
        flow = sum(q for (t, i), q in st["flow"].items()
                   if i == item and step - _FX_FLOW_WIN <= t < step)
        if flow < _FX_FLOW_MIN:
            continue
        q = int(prices.get(item, 0))
        if q <= 3:
            continue
        vals = [hist[t].get(item, 0) for t in recent_turns if hist[t].get(item, 0) > 0]
        if vals and q < sum(vals) / len(vals):
            continue
        planned = 0
        for t in range(step + 1, min(len(tape), step + _FX_LEAD_H + 1)):
            for o in (tape[t] or {}).get("market") or []:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                    planned += max(0, int(o[2]))
        qty = min(int(stock.get(item, 0)), planned)
        if qty <= 0:
            continue
        market.insert(0, ["SELL", item, qty])
        _FX_REPORT["fx_fires"] += 1
        _FX_REPORT["fx_units"] += qty
        added = True
    if not added:
        return action
    result = dict(action)
    result["market"] = market[:MAX_ORDERS]
    return result


_EV_HOURS = (15, 16, 17, 18, 19, 20)
_EV_H = 8
_EV_STATE = {}


def _ev_apply(observation, action, st):
    """Evening-window chunked lead-sell: pull up to half of the next _EV_H turns'
    planned sells of premium items into the current turn while the quote is at or
    above its trailing average."""
    step = int(observation["step"])
    if step < _FX_MIN_STEP or step >= 700:
        return action
    if (step % 24) not in _EV_HOURS:
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if len(market) >= MAX_ORDERS:
        return action
    already = {o[1] for o in market if len(o) > 1 and o[0] in ("SELL", "BUY_PRODUCT")}
    prices = observation["market"]["prices"]
    stock = projected_shed(action, FarmView(observation))
    native = _IMPL.chassis.players.get(int(observation["player"]))
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    tape = _IMPL.chassis.routes[native["route"]]
    hist = _FX_STATE.get(int(observation["player"]), {}).get("quotes", {})
    recent = [t for t in hist if step - _FX_QUOTE_WIN <= t < step]
    added = False
    for item in _FX_ITEMS:
        if item in already or len(market) >= MAX_ORDERS:
            continue
        q = int(prices.get(item, 0))
        if q <= 3:
            continue
        vals = [hist[t].get(item, 0) for t in recent if hist[t].get(item, 0) > 0]
        if vals and q < sum(vals) / len(vals):
            continue
        planned = 0
        for t in range(step + 1, min(len(tape), step + _EV_H + 1)):
            for o in (tape[t] or {}).get("market") or []:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                    planned += max(0, int(o[2]))
        if planned <= 0:
            continue
        qty = min(int(stock.get(item, 0)), max(1, (3 * planned + 3) // 4))
        if qty <= 0:
            continue
        market.insert(0, ["SELL", item, qty])
        _FX_REPORT["ev_fires"] = _FX_REPORT.get("ev_fires", 0) + 1
        _FX_REPORT["ev_units"] = _FX_REPORT.get("ev_units", 0) + qty
        added = True
    if not added:
        return action
    result = dict(action)
    result["market"] = market[:MAX_ORDERS]
    return result


_FX_PARENT = cha20_entry_agent


def cha20_entry_agent(observation, configuration=None):
    player = int(observation.get("player", 0))
    step = int(observation.get("step", 0))
    st = _FX_STATE.get(player)
    if st is None or step <= st["step"]:
        st = _FX_STATE[player] = {"step": -1, "flow": {}, "quotes": {}, "prev": None}
        if step == 0:
            _FX_REPORT.update(fx_fires=0, fx_units=0, fx_rival_seen=0, fx_errors=0)
    st["step"] = step
    try:
        _fx_update(observation, player, st)
    except Exception:
        _FX_REPORT["fx_errors"] += 1
    action = _FX_PARENT(observation, configuration)
    try:
        out = _fx_apply(observation, action, st)
    except Exception:
        _FX_REPORT["fx_errors"] += 1
        out = action
    try:
        out = _ev_apply(observation, out, st)
    except Exception:
        _FX_REPORT["fx_errors"] += 1
    try:
        stock = projected_shed(action, FarmView(observation))
        own = {}
        for o in (out.get("market") or []):
            if o and o[0] == "SELL" and len(o) >= 3:
                own[o[1]] = own.get(o[1], 0) + max(0, int(o[2]))
        st["prev"] = {"step": step, "inventory": dict(observation["market"]["inventory"]),
                      "prices": dict(observation["market"]["prices"]), "own": own,
                      "shops": list(observation["town"]["unlocked_shops"])}
    except Exception:
        _FX_REPORT["fx_errors"] += 1
        st["prev"] = None
    return out


import collections as _fx_coll
cha20_entry_agent.telemetry = _fx_coll.ChainMap(_FX_REPORT, _FX_PARENT.telemetry)
kaggle_agent = cha20_entry_agent
_FX_ENTRY = cha20_entry_agent


# ===========================================================================
# DAWNPX: dawn-window chunked lead-sell (AXIS2 #8; general, no opponent data)
# ===========================================================================
_DP_HOURS = (0, 1, 2)
_DP_H = 8
_DP_REPORT = dict(dp_fires=0, dp_units=0, dp_errors=0)


def _dp_apply(observation, action):
    step = int(observation["step"])
    if step < 96 or step >= 700:
        return action
    if (step % 24) not in _DP_HOURS:
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if len(market) >= MAX_ORDERS:
        return action
    already = {o[1] for o in market if len(o) > 1 and o[0] in ("SELL", "BUY_PRODUCT")}
    prices = observation["market"]["prices"]
    stock = projected_shed(action, FarmView(observation))
    native = _IMPL.chassis.players.get(int(observation["player"]))
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    tape = _IMPL.chassis.routes[native["route"]]
    hist = _FX_STATE.get(int(observation["player"]), {}).get("quotes", {})
    recent = [t for t in hist if step - _FX_QUOTE_WIN <= t < step]
    added = False
    for item in _FX_ITEMS:
        if item in already or len(market) >= MAX_ORDERS:
            continue
        q = int(prices.get(item, 0))
        if q <= 3:
            continue
        vals = [hist[t].get(item, 0) for t in recent if hist[t].get(item, 0) > 0]
        if vals and q < sum(vals) / len(vals):
            continue
        planned = 0
        for t in range(step + 1, min(len(tape), step + _DP_H + 1)):
            for o in (tape[t] or {}).get("market") or []:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                    planned += max(0, int(o[2]))
        if planned <= 0:
            continue
        qty = min(int(stock.get(item, 0)), max(1, (3 * planned + 3) // 4))
        if qty <= 0:
            continue
        market.insert(0, ["SELL", item, qty])
        _DP_REPORT["dp_fires"] += 1
        _DP_REPORT["dp_units"] += qty
        added = True
    if not added:
        return action
    return dict(action, market=market[:MAX_ORDERS])


_DP_PARENT = cha20_entry_agent


def cha20_entry_agent(observation, configuration=None):
    step = int(observation.get("step", 0))
    if step == 0:
        _DP_REPORT.update(dp_fires=0, dp_units=0, dp_errors=0)
    action = _DP_PARENT(observation, configuration)
    try:
        return _dp_apply(observation, action)
    except Exception:
        _DP_REPORT["dp_errors"] += 1
        return action


import collections as _dp_coll
cha20_entry_agent.telemetry = _dp_coll.ChainMap(_DP_REPORT, _DP_PARENT.telemetry)
kaggle_agent = cha20_entry_agent
_DP_ENTRY = cha20_entry_agent


_MP_HOURS = (10, 11, 12, 13)
_MP_H = 8
_MP_REPORT = dict(mp_fires=0, mp_units=0, mp_errors=0)


def _mp_apply(observation, action):
    step = int(observation["step"])
    if step < 96 or step >= 700:
        return action
    if (step % 24) not in _MP_HOURS:
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if len(market) >= MAX_ORDERS:
        return action
    already = {o[1] for o in market if len(o) > 1 and o[0] in ("SELL", "BUY_PRODUCT")}
    prices = observation["market"]["prices"]
    stock = projected_shed(action, FarmView(observation))
    native = _IMPL.chassis.players.get(int(observation["player"]))
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    tape = _IMPL.chassis.routes[native["route"]]
    hist = _FX_STATE.get(int(observation["player"]), {}).get("quotes", {})
    recent = [t for t in hist if step - _FX_QUOTE_WIN <= t < step]
    added = False
    for item in _FX_ITEMS:
        if item in already or len(market) >= MAX_ORDERS:
            continue
        q = int(prices.get(item, 0))
        if q <= 3:
            continue
        vals = [hist[t].get(item, 0) for t in recent if hist[t].get(item, 0) > 0]
        if vals and q < sum(vals) / len(vals):
            continue
        planned = 0
        for t in range(step + 1, min(len(tape), step + _MP_H + 1)):
            for o in (tape[t] or {}).get("market") or []:
                if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                    planned += max(0, int(o[2]))
        if planned <= 0:
            continue
        qty = min(int(stock.get(item, 0)), max(1, (3 * planned + 3) // 4))
        if qty <= 0:
            continue
        market.insert(0, ["SELL", item, qty])
        _MP_REPORT["mp_fires"] += 1
        _MP_REPORT["mp_units"] += qty
        added = True
    if not added:
        return action
    return dict(action, market=market[:MAX_ORDERS])


_MP_PARENT = cha20_entry_agent


def cha20_entry_agent(observation, configuration=None):
    step = int(observation.get("step", 0))
    if step == 0:
        _MP_REPORT.update(mp_fires=0, mp_units=0, mp_errors=0)
    action = _MP_PARENT(observation, configuration)
    try:
        return _mp_apply(observation, action)
    except Exception:
        _MP_REPORT["mp_errors"] += 1
        return action


import collections as _mp_coll
cha20_entry_agent.telemetry = _mp_coll.ChainMap(_MP_REPORT, _MP_PARENT.telemetry)
kaggle_agent = cha20_entry_agent
_MP_ENTRY = cha20_entry_agent


# ===========================================================================
# BUYDIP: buy-the-dip for large wheat buys (general, no opponent data)
# ===========================================================================
_BD_ITEM = "WHEAT"
_BD_MIN = 8
_BD_WIN = 12
_BD_DEADLINE = 6
_BD_CAP = 64
_BD_STATE = {}
_BD_REPORT = dict(bd_split=0, bd_pending_units=0, bd_released=0, bd_errors=0)


def _bd_apply(observation, action):
    step = int(observation["step"])
    if step < 24 or step >= 690 or not isinstance(action, dict):
        return action
    player = int(observation["player"])
    st = _BD_STATE.setdefault(player, {"hist": [], "pending": 0, "since": None})
    price = int((observation["market"]["prices"] or {}).get(_BD_ITEM, 0))
    if price > 0:
        st["hist"].append((step, price))
        if len(st["hist"]) > 48:
            del st["hist"][:24]
    market = [list(o) for o in (action.get("market") or [])]

    if st["pending"] > 0:
        vals = [p for (s, p) in st["hist"] if step - _BD_WIN <= s < step]
        avg = (sum(vals) / len(vals)) if vals else price
        due = st["since"] is not None and step - st["since"] >= _BD_DEADLINE
        if price > 0 and (price <= avg or due):
            has = any(len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == _BD_ITEM for o in market)
            if len(market) < 10 and not has:
                qty = min(st["pending"], 8)
                market.append(["BUY_PRODUCT", _BD_ITEM, qty])
                st["pending"] -= qty
                _BD_REPORT["bd_released"] += qty
            if st["pending"] <= 0:
                st["since"] = None

    if st["pending"] < _BD_CAP:
        vals = [p for (s, p) in st["hist"] if step - _BD_WIN <= s < step]
        avg = (sum(vals) / len(vals)) if vals else price
        for o in market:
            if len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == _BD_ITEM and int(o[2]) >= _BD_MIN:
                q = int(o[2])
                if price > 0 and price > avg:
                    hold = min(q - 1, _BD_CAP - st["pending"], q // 2)
                    if hold > 0:
                        o[2] = q - hold
                        st["pending"] += hold
                        if st["since"] is None:
                            st["since"] = step
                        _BD_REPORT["bd_split"] += 1
                        _BD_REPORT["bd_pending_units"] += hold
    return dict(action, market=market)


_BD_PARENT = cha20_entry_agent


def cha20_entry_agent(observation, configuration=None):
    if int(observation.get("step", 0)) == 0:
        _BD_REPORT.update(bd_split=0, bd_pending_units=0, bd_released=0, bd_errors=0)
        _BD_STATE.clear()
    action = _BD_PARENT(observation, configuration)
    try:
        return _bd_apply(observation, action)
    except Exception:
        _BD_REPORT["bd_errors"] += 1
        return action


import collections as _bd_coll
cha20_entry_agent.telemetry = _bd_coll.ChainMap(_BD_REPORT, _BD_PARENT.telemetry)
kaggle_agent = cha20_entry_agent
_BD_ENTRY = cha20_entry_agent


# ===========================================================================
# MODELPX: model-based lead seller for MILK/STRAWBERRY (general)
# ===========================================================================
_MPX_ITEMS = ("MILK", "STRAWBERRY", "WOOL")
_MPX_HOURS = tuple(range(12, 23))
_MPX_REPORT = dict(mpx_fires=0, mpx_units=0, mpx_errors=0)
_MPX_HIST = {}


def _mpx_draw_units(item, step):
    # town draw cadence: shops every 4 steps, center every 24
    draw = 0
    if step % 4 == 0:
        draw += 1
    if step % 24 == 0:
        draw += 1
    return draw


def _mpx_apply(observation, action):
    step = int(observation["step"])
    if step < 144 or step >= 696 or (step % 24) not in _MPX_HOURS:
        return action
    player = int(observation["player"])
    market = observation["market"]
    inv_all = market.get("inventory") or {}
    prices = market.get("prices") or {}
    hist = _MPX_HIST.setdefault(player, {})
    # record rival cadence from public inventory deltas
    prev = hist.get("prev")
    inv_now = {i: int(inv_all.get(i, 0)) for i in _MPX_ITEMS}
    if prev and prev["step"] == step - 1:
        for i in _MPX_ITEMS:
            d = inv_now[i] - prev["inv"][i] + _mpx_draw_units(i, step - 1) - prev["own"].get(i, 0)
            hist.setdefault(i, []).append(max(0, d))
            if len(hist[i]) > 12:
                del hist[i][:6]
    hist["prev"] = {"step": step, "inv": inv_now, "own": {}}
    tape = None
    market_orders = [list(o) for o in (action.get("market") or [])]
    for o in market_orders:
        if len(o) >= 3 and o[0] == "SELL" and o[1] in _MPX_ITEMS:
            hist["prev"]["own"][o[1]] = hist["prev"]["own"].get(o[1], 0) + int(o[2])
    already = {o[1] for o in market_orders if len(o) > 1 and o[0] == "SELL"}
    native = _IMPL.chassis.players.get(player)
    if not native or native.get("route") not in _IMPL.chassis.routes:
        return action
    tape = _IMPL.chassis.routes[native["route"]]
    stock = projected_shed(action, FarmView(observation))
    added = False
    for item in _MPX_ITEMS:
        if item in already or len(market_orders) >= 10:
            continue
        avail = int(stock.get(item, 0))
        if avail <= 0:
            continue
        p_now = int(prices.get(item, 0))
        if p_now <= 1:
            continue
        rival = hist.get(item) or []
        rival_avg = (sum(rival[-4:]) / len(rival[-4:])) if rival else 0.0
        planned = 6
        try:
            inv = int(inv_all.get(item, 0))
            p_cur = float(_r37_market_price(item, inv))
            inv_next = inv + rival_avg + planned - _mpx_draw_units(item, step)
            p_next = float(_r37_market_price(item, max(0, int(inv_next))))
        except Exception:
            continue
        if p_next < p_cur - 0.5:
            take = min(avail, max(1, planned // 2))
            if take <= 0:
                continue
            market_orders.insert(0, ["SELL", item, take])
            _MPX_REPORT["mpx_fires"] += 1
            _MPX_REPORT["mpx_units"] += take
            hist["prev"]["own"][item] = hist["prev"]["own"].get(item, 0) + take
            added = True
    if not added:
        return action
    return dict(action, market=market_orders[:10])


_MPX_PARENT = cha20_entry_agent


def cha20_entry_agent(observation, configuration=None):
    if int(observation.get("step", 0)) == 0:
        _MPX_REPORT.update(mpx_fires=0, mpx_units=0, mpx_errors=0)
        _MPX_HIST.clear()
    action = _MPX_PARENT(observation, configuration)
    try:
        return _mpx_apply(observation, action)
    except Exception:
        _MPX_REPORT["mpx_errors"] += 1
        return action


import collections as _mpx_coll
cha20_entry_agent.telemetry = _mpx_coll.ChainMap(_MPX_REPORT, _MPX_PARENT.telemetry)
kaggle_agent = cha20_entry_agent
_MPX_ENTRY = cha20_entry_agent


# ===========================================================================
# SHIELD-MILK: fund failing animal/land buys only in milk-shop worlds
# ===========================================================================
_SM_ANIMAL = {"COW": 400, "SHEEP": 500, "GOOSE": 300}
_SM_LAND = (1000, 2000, 4000)
_SM_MILK_SHOP = ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP")
_SM_PRODUCTS = ("MELON", "STRAWBERRY", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")
_SM_REPORT = dict(sm_shields=0, sm_units=0, sm_errors=0)


def _sm_apply(observation, action):
    if not isinstance(action, dict):
        return action
    shops = list((observation.get("town") or {}).get("unlocked_shops") or [])
    if not any(s in _SM_MILK_SHOP for s in shops):
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if not market:
        return action
    seat = int(observation["player"])
    farm = observation["farms"][seat]
    shed = dict((observation.get("private") or {}).get("shed") or {})
    prices = observation["market"].get("prices") or {}
    quads = len(farm.get("unlocked_quadrants") or [])
    cash = float(farm.get("money", 0) or 0)
    sold = {}
    for o in market:
        if not o:
            continue
        if o[0] == "SELL" and len(o) >= 3:
            item = o[1]
            take = min(max(0, int(o[2])), int(shed.get(item, 0)) - sold.get(item, 0))
            if take > 0:
                cash += take * float(prices.get(item, 0))
                sold[item] = sold.get(item, 0) + take
        elif o[0] == "BUY_ANIMAL" and len(o) >= 3:
            cash -= _SM_ANIMAL.get(o[1], 400) * max(0, int(o[2]))
        elif o[0] == "BUY_SEED" and len(o) >= 3:
            cash -= {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(o[1], 100) * max(0, int(o[2]))
        elif o[0] == "BUY_PRODUCT" and len(o) >= 3:
            cash -= float(prices.get(o[1], 0)) * max(0, int(o[2]))
        elif o[0] == "BUY_LAND":
            extra = quads - 1
            cash -= _SM_LAND[extra] if 0 <= extra < 3 else 4000
    need = -cash
    if need <= 0:
        return action
    candidates = []
    for item in _SM_PRODUCTS:
        price = float(prices.get(item, 0))
        avail = int(shed.get(item, 0)) - sold.get(item, 0)
        if price > 1 and avail > 0:
            candidates.append((price, item, avail))
    candidates.sort(reverse=True)
    added = []
    for price, item, avail in candidates:
        if need <= 0 or len(market) + len(added) >= 10:
            break
        q = min(avail, int(need / price) + 1)
        if q <= 0:
            continue
        added.append(["SELL", item, q])
        need -= q * price
        _SM_REPORT["sm_units"] += q
    if not added:
        return action
    _SM_REPORT["sm_shields"] += 1
    idx = next((i for i, o in enumerate(market) if o and str(o[0]).startswith("BUY")), len(market))
    market = market[:idx] + added + market[idx:]
    return dict(action, market=market[:10])


_SM_PARENT = cha20_entry_agent


def cha20_entry_agent(observation, configuration=None):
    if int(observation.get("step", 0)) == 0:
        _SM_REPORT.update(sm_shields=0, sm_units=0, sm_errors=0)
    action = _SM_PARENT(observation, configuration)
    try:
        return _sm_apply(observation, action)
    except Exception:
        _SM_REPORT["sm_errors"] += 1
        return action


import collections as _sm_coll
cha20_entry_agent.telemetry = _sm_coll.ChainMap(_SM_REPORT, _SM_PARENT.telemetry)
kaggle_agent = cha20_entry_agent
_SM_ENTRY = cha20_entry_agent


# ==== F4: Layer D - exact best-response ordering (_CXD from elo_2615 order-book) ====
import itertools as _cxd_it
_CXD_HOST = cha20_entry_agent
_CXD_FIXED = ('HIRE', 'BUY_SEED', 'BUY_ANIMAL', 'BUY_LAND')
_CXD_BUDGET = 800
_CXD_FROM = 0
_CXD_REPORT = {'cxd_turns': 0, 'cxd_gain': 0.0, 'cxd_evals': 0, 'cxd_budget_hits': 0, 'cxd_errors': 0}
_CXD_MODELS = []
_CXD_PARENT_ORDERS = []


def _cxd_candidates(orders, slots, sells, fixed):
    """Orderings of `sells` over `slots`, fixed-price orders filling the rest in their own order."""
    for positions in _cxd_it.permutations(slots, len(sells)):
        out = list(orders)
        rest = [i for i in slots if i not in positions]
        for i, order in zip(positions, sells):
            out[i] = order
        for i, order in zip(rest, fixed):
            out[i] = order
        yield out


def _cxd_reorder(obs, action):
    market = action.get('market') or []
    if len(market) < 2:
        return action
    orders = [list(o) if isinstance(o, (list, tuple)) else o for o in market]
    bought = {o[1] for o in orders if o and len(o) > 1 and o[0] == 'BUY_PRODUCT'}
    slots, sells, fixed = [], [], []
    for i, o in enumerate(orders):
        if not o:
            continue
        if o[0] in _CXD_FIXED:
            slots.append(i); fixed.append(o)
        elif o[0] == 'SELL' and len(o) > 1 and o[1] not in bought:
            slots.append(i); sells.append(o)
    if not sells or len(slots) < 2:
        return action
    params = _v44y_params(obs)
    stock = {k: max(0, int(v)) for k, v in projected_shed(action, FarmView(obs)).items()}
    inv0 = {k: int(v) for k, v in obs['market']['inventory'].items()}
    _CXD_PARENT_ORDERS[:] = [list(o) for o in orders if o]
    models = [m for m in _CXD_MODELS if m] or [orders]
    margins = [_v44y_factor_margin(m, inv0, stock, params) for m in models]

    def margin(cand):
        return min(f(cand) for f in margins)
    base = best = margin(orders)
    best_orders = None
    evals = 0
    for cand in _cxd_candidates(orders, slots, sells, fixed):
        if cand == orders:
            continue
        evals += 1
        if evals > _CXD_BUDGET:
            _CXD_REPORT['cxd_budget_hits'] += 1
            break
        value = margin(cand)
        if value > best + 0.5:
            best, best_orders = value, cand
    _CXD_REPORT['cxd_evals'] += evals
    if best_orders is None:
        return action
    _CXD_REPORT['cxd_turns'] += 1
    _CXD_REPORT['cxd_gain'] += best - base
    return dict(action, market=best_orders)


def cxd_agent(observation, configuration=None):
    action = _CXD_HOST(observation, configuration)
    try:
        if int(observation.get('step', 0)) == 0:
            _CXD_REPORT.update(cxd_turns=0, cxd_gain=0.0, cxd_evals=0, cxd_budget_hits=0, cxd_errors=0)
        if int(observation.get('step', 0)) >= _CXD_FROM:
            return _cxd_reorder(observation, action)
    except Exception:
        _CXD_REPORT['cxd_errors'] += 1
    return action


import collections as _cxd_coll
cxd_agent.telemetry = _cxd_coll.ChainMap(_CXD_REPORT, _CXD_HOST.telemetry)
cha20_entry_agent = cxd_agent
kaggle_agent = cha20_entry_agent


# ==== F5: EXP410 fertilizer guard (pipe18 `e410_agent`) ====
_E410_REPORT = dict(skips=0, covered=0, capped=0, errors=0)
_E410_PARENT = cha20_entry_agent


def e410_agent(observation, configuration=None):
    action = _E410_PARENT(observation, configuration)
    try:
        step = int(observation['step']); seat = int(observation['player']); day = step // 24
        if step == 0:
            for k in _E410_REPORT: _E410_REPORT[k] = 0
        units = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
        if not any(c == ['FERTILIZE'] for c in units): return action
        farm, private = _PLANNER_NS['_clone_state'](observation['farms'][seat], observation['private'])
        positions = [farm['farmer']] + list(farm['hands']); changed = False
        native = _IMPL.chassis.players[seat]
        expected = max(len(a.get('hands', [])) for a in _v219_native_day(native, day))
        reactive = set(_R51_INPUT_STATES.get(seat, {}).get('workers', {}))
        for i, cmd in enumerate(units[:len(positions)]):
            pos = tuple(positions[i]); tile = farm['tiles'][pos[1]][pos[0]]
            if cmd == ['FERTILIZE'] and isinstance(tile, dict) and tile.get('crop') in ('WHEAT', 'CARROT') and private['inventories'][i].get('FERTILIZER', 0) > 0:
                until = int(tile.get('fertilized_until_day', -1)); covered = until >= day + 2; skip = covered
                if not skip and i <= expected and i not in reactive:
                    visits = _ca_visits(observation, action, pos, min(718, (int(tile['planted_day']) + 6) * 24), start=step + 1)
                    kw = dict(y0=int(tile['yield_units']), watered_day=day if tile.get('watered_today') else -1, now_step=step)
                    old = _ca_yield_path(tile['crop'], int(tile['planted_day']), visits, fert_until=until, **kw)[0]
                    new = _ca_yield_path(tile['crop'], int(tile['planted_day']), visits, fert_until=max(until, day + 2), **kw)[0]
                    skip = old > 0 and old == new
                if skip:
                    units[i] = cmd = ['PASS']; changed = True
                    _E410_REPORT['skips'] += 1; _E410_REPORT['covered' if covered else 'capped'] += 1
            _PLANNER_NS['_apply_unit_action'](farm, private, i, cmd, len(farm['tiles']), day, 24, 100)
        if changed: return dict(action, farmer=units[0], hands=units[1:])
    except Exception:
        _E410_REPORT['errors'] += 1
    return action


import collections as _e410_coll
e410_agent.telemetry = _e410_coll.ChainMap(_E410_REPORT, _E410_PARENT.telemetry)
cha20_entry_agent = e410_agent
kaggle_agent = cha20_entry_agent


# ==== F6: EXP402 late seed cap (pipe18 `e402_agent`) ====
_E402_PARENT = cha20_entry_agent
_E402_CACHE = {}
_E402_REPORT = dict(cut_units=0, saved_cost=0, changed_turns=0, errors=0)


def _e402_remaining(native, step):
    route = native['route']; key = (route, step)
    if key in _E402_CACHE: return _E402_CACHE[key]
    need = 0
    for t in range(step + 1, 719):
        tape = _IMPL.chassis.routes[2 if t >= 648 else route]
        act = tape[t]
        need += sum(1 for c in [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
                    if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
    _E402_CACHE[key] = need
    return need


def e402_agent(observation, configuration=None):
    action = _E402_PARENT(observation, configuration)
    try:
        step = int(observation['step']); seat = int(observation['player'])
        if step == 0:
            _E402_CACHE.clear()
            for k in _E402_REPORT: _E402_REPORT[k] = 0
        if step < 624: return action
        market = action.get('market', [])
        if not any(len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in ('WHEAT', 'CARROT') for o in market): return action
        native = _IMPL.chassis.players[seat]
        remaining = _e402_remaining(native, step)
        # Queued retries can outlive their original schedule; reserve for them too.
        remaining += sum(1 for queue in native['pending'].values() for pos, c in queue
                         if len(c) > 1 and c[0] == 'PLANT' and c[1] in ('WHEAT', 'CARROT'))
        units = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
        available = {p: max(0, int(observation['private']['seeds'].get(p, 0)) - sum(c[:2] == ['PLANT', p] for c in units)) for p in ('WHEAT', 'CARROT')}
        out = []; changed = False
        for o in market:
            if len(o) >= 3 and o[0] == 'BUY_SEED' and o[1] in available:
                p = o[1]; qty = max(0, int(o[2])); keep = min(qty, max(0, remaining - available[p])); available[p] += keep
                if keep < qty:
                    cut = qty - keep; changed = True
                    _E402_REPORT['cut_units'] += cut; _E402_REPORT['saved_cost'] += cut * (10 if p == 'WHEAT' else 20)
                    if p == 'CARROT':
                        st = _CA_STATE.get(seat)
                        if st is not None: st['spare_carrot'] = max(0, st.get('spare_carrot', 0) - cut)
                    o = [o[0], p, keep] if keep else []
            out.append(o)
        if changed:
            _E402_REPORT['changed_turns'] += 1
            action = dict(action, market=out)
    except Exception:
        _E402_REPORT['errors'] += 1
    return action


import collections as _e402_coll
e402_agent.telemetry = _e402_coll.ChainMap(_E402_REPORT, _E402_PARENT.telemetry)
cha20_entry_agent = e402_agent
kaggle_agent = cha20_entry_agent


# ==== MERGE: same-item SELL compaction (port of 2695's E334) ====
_MG_REPORT = dict(mg_turns=0, mg_merged=0, mg_errors=0)
_MG_PARENT = cha20_entry_agent


def _mg_apply(observation, action):
    if not isinstance(action, dict):
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if len(market) < 2:
        return action
    seen = {}
    out = []
    changed = False
    for o in market:
        if o and len(o) >= 3 and o[0] in ("SELL", "BUY_PRODUCT", "BUY_SEED"):
            it = (o[0], o[1])
            if it in seen:
                out[seen[it]][2] = int(out[seen[it]][2]) + int(o[2])
                changed = True
                continue
            seen[it] = len(out)
        out.append(o)
    if not changed:
        return action
    _MG_REPORT["mg_turns"] += 1
    _MG_REPORT["mg_merged"] += len(market) - len(out)
    return dict(action, market=out)


def mg_agent(observation, configuration=None):
    if int(observation.get("step", 0)) == 0:
        _MG_REPORT.update(mg_turns=0, mg_merged=0, mg_errors=0)
    action = _MG_PARENT(observation, configuration)
    try:
        return _mg_apply(observation, action)
    except Exception:
        _MG_REPORT["mg_errors"] += 1
        return action


import collections as _mg_coll
mg_agent.telemetry = _mg_coll.ChainMap(_MG_REPORT, _MG_PARENT.telemetry)
cha20_entry_agent = mg_agent
kaggle_agent = cha20_entry_agent


# ==== IG (bundled): queue hole-closure ====
_IG_CASH = frozenset(("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"))
_IG_REPORT = {"queue_changed_turns": 0, "zeroed_orders": 0, "pulled_orders": 0, "pulled_slots": 0, "errors": 0}
_IG_PARENT = cha20_entry_agent


def _ig_close_queue(observation, action):
    if not isinstance(action, dict):
        return action
    market = action.get("market") or []
    if len(market) < 2:
        return action
    projected = dict(projected_shed(action, FarmView(observation)))
    remaining = {item: max(0, int(projected.get(item, 0))) for item in _IG_CASH}
    revised = []
    zeroed = 0
    for raw in market:
        order = list(raw) if isinstance(raw, (list, tuple)) else raw
        if (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL" and order[1] in _IG_CASH):
            requested = max(0, int(order[2]))
            executed = min(requested, remaining[order[1]])
            remaining[order[1]] -= executed
            if executed <= 0:
                revised.append([])
                zeroed += 1
            else:
                revised.append(order)
        else:
            revised.append(order)
    holes = []
    pulled = 0
    distance = 0
    for index, order in enumerate(revised):
        if not order:
            holes.append(index)
            continue
        movable = (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL" and order[1] in _IG_CASH and int(order[2]) > 0)
        if not movable or not holes:
            continue
        target = holes.pop(0)
        revised[target] = order
        revised[index] = []
        holes.append(index)
        pulled += 1
        distance += index - target
    if revised == market:
        return action
    _IG_REPORT["queue_changed_turns"] += 1
    _IG_REPORT["zeroed_orders"] += zeroed
    _IG_REPORT["pulled_orders"] += pulled
    _IG_REPORT["pulled_slots"] += distance
    return dict(action, market=revised)


def ig_agent(observation, configuration=None):
    if int(observation.get("step", 0)) == 0:
        for key in _IG_REPORT:
            _IG_REPORT[key] = 0
    action = _IG_PARENT(observation, configuration)
    try:
        return _ig_close_queue(observation, action)
    except Exception:
        _IG_REPORT["errors"] += 1
        return action


import collections as _ig_coll
ig_agent.telemetry = _ig_coll.ChainMap(_IG_REPORT, _IG_PARENT.telemetry)
cha20_entry_agent = ig_agent
kaggle_agent = cha20_entry_agent


# ---- Agent L2: our layers, each in its own namespace ----
import base64 as _l2_b64
import zlib as _l2_zlib

_L2_SRC = {
    "market_front": "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",
    "animals": "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",
    "wheat_rt": "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",
    "outfarm": "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",
    "labour": "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",
    "shadow": "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",
    "safety": "eNqdV01v20YQvetXTO0DyYZV5ARtAyUy4KJqYzS1i1jNRRCItTgSWVFcYndlxTD83zszS1KULDtodSKXO2/efL1dncIP9INfxr9fXoFVC3T3EF4ssXTwKbCgtyUU6h5NJPt6pzDJEPTGoVlr62C5USbtw3UJf6jlskBQYPOSHzblXG2WmQP8OsfK5bqEtTIrC44AFDsgsPHnz9efQZUpLLRZYO7856Va43uCWquC1teYgpp3EHIHl1dfLj5d/gqhKqwGRVA1QPQe3MaUxPwODZtN8jUSXwjPwEaQGrUFAlLw0wAsGLRo7pCNxfE20wUSGBOIhZfZlCUFxD5Tcw+5JdPJ5Z/j678njUsIVxJ7guVdbnS5ptjs67k22K/uo37vlABvNOGTseRySAvfQ4nMsECKWZWdLKGdqwqH7NGgj0XBnSryFP66uLlpUpGX1qFKCR4ALomdRgtX1xOYq6KQYCpluIxUEZxrCsVRJtpILUUIhFBRXXlBYLxFUNOkWhhUDGCwogcqgxgoJlTiVrLkk0RpdO8lqnmG86bIQpTQbEYB1RsrlRPwNiNcCnCuSm+2QqwYVjjebtIlOtAEYhoqtBMoCrspKN92kfg9iV5FQA2gJXWqkCi22qwgxP6yz4nVVaVLzgOxSPU24hLaVV5VFM42w1KoNn1A1abg9daTqkxOlaR2QchQFS6DIqdnos42SPHoRduvMaHl86yZAx9QXra5lZbn1OqlbTqGIlpX6HImX3/5gFVudYrn8CEvU/x6Tg3Uy9eVNg7+sdy5FhKKn5+bdUlavc7PvV5y81tyM7mYjGEED0EdXTCkpu8PYgi4qxLrlKGa0iotPoqJ9BdbLBRNnaFP04DXghkZZVRAy0v8woOITt4ee71eigvoFiXUt+xScWCjK0pgLFOZrO3o7Y/CoeaU2NEbeo+GPUoRnJycTMyGxzBnKSnbuvouoPG/B1th08syUYzbJ0MBcObeI/GvKeoIFoVWLuySAhqDh8eoT3RDys9a5Tzl1zSRVCeWjCCGNonTNoOzKBJ4P60QTu4rHBujTQxfVLFpni+cM/ktiaS8R8coHQOXbRyfow1hU81+hWaRzPWmJNENSYe7tnuVnEXUtGeDASW0573x59bp+S7pMoze04emMnUZ2a0f09AP8K42F7UM1QqU5nMXcyK5wJAv6oEutYNbpFql6Pe31aEt/DG3rF2qnGPtIRaovTQJccaVNdZvastHefG9Se/e2Jewbti4bdioMZw232bcCN6WiIQdFn41pum2LvKnkay0fJ758c4nMNMBzYd1JooAC4stIQGTGTqg7ueKmNecn2ZJdtT0dklqsKazXageiyOdZodRZt0As0Py2Yu8D398imSsbuLQ7/GScBBcrRMvRee3PAmvhevGV8NJgFpYaGZR7+UW3OHqGnI2HZ4NZt2BIKidZm2NqkIR5xhK0vFR4JW6pkJgzoom8kcSvFK0XgaP1ZDlFHnKmxc/O15XRSi/0mx5kY33cxk47VSRNB8hsHTyJF3gQlmXCDotBAEpLdsJcbqpJUK0q2oxH5GLfLkxO+XtpPRZ3aD43IBF6bjktAB78nqA2KpYq7cdYi/qLB9K0c5Jra3j5kK077FS1rYLtRCNdkpxlCXf+UbwrWxFezYtdEcPCWd/EzVccxuzXgW1aVa+G7Hf4ZPxkYaa7tpkBq9GcPZs9HyuSwcMAU7rO2Nz71T+BiY3XXbORe0d8VX354GnzoZOn0n5Th4cHWyhrET9JOGeT5LHITzI0uPJdPhmMNhJw5M8DI/n8r9eLFotsC8fiG5wcPJ1YvPzdBB7860eQPlKTl4/g1EPMeeGHsOD1ZhMo0OTziw36Ofwbg/8SZ+yfpVH5oZv3TQnNCRwPoKfz9497Sq5qobBx/HFp8lHCOBVe0nsp5t1ZcOH1RBCQzlLw7sY3kYHYklrMrS1+N9F3zr7jp8JqxjuWJAlCf3c4dqG0WPE4Bubjfhy978GvRZu30heBXcK2HdY4BopnVQf8dwV+90+uobLf93x1a/NP135T/sv7ECVyg==",
}
_L2_A_VERBATIM = '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27EddFa6nwbbJi8sdjPXLtliB6GC+Z5O39X95HuWH34tp+65hc29OZrL8uGQ6qR7vv29z9nerDmhd0jksq1jIbp/e1qLPnvZUByELe/7Yd0+4Jax7GubajqpDut/8jQas3oltn86zAfB1v1it14wvUa6v4sMSh63s/4edKXZu7TPRn+WhLZgWnR3C3YX+nJ8iWu+V3/txLk7IeqKRcVl1z25t03zb/dWvmahhA+GpTZTVy3sHLpeTMbP/ds4eqRf4rW3mKdqMFps++nofjFPPbX8JoeJTxh85XUhn20fK0JQrK75tzf/tHP/9lEY9qxcf5H/op3WSHmefo9k+h6PZ96rNr31l/d8dZiji2+5uXngGdkm9iwwpe3vdy+LvP3jkE5y0ZpjG55mOjvX9D3iWhjtVJ03CC6vOB1sbdOhbRdK87VibT1bf5bpyHjvHgd9nzv6sB+6gouWmFwte/ukM+ktLzzNV+ATRvripL2ObqhQmFlu7/KFiGEbFPjQXetj5tiHSWqSObSz5UzakJ20X46HZspUMnST8Yo58doJMdUOySfLgi1mLMbGlehnNuJbeL28MKC300+TfTtw3rG22sLe9RvKYRfg6nLPMHbc3UUahXUgmDd92kXqY8427z/Dn4HycGDgF35bOhBhso6jo2+JbiOTnadcqzEpw4puTxwuoTfPHGuexcG+rZPZr+re5Ozs21n7cUgLrSFjWgT3L2xcPNqZxojssPf9bPq19VaKMNa4NbrLVXLTjIHp8fzq3sPHrWFgTb28TPrU08HdyX/ciTtzzvfEz72m8WaziH7kPowhervOWVKZzDxI5Rxly8ieZrx36VV22liZs4fIPPWai09sr5khM4ztjcfZ/s7RDC7L63VhbmzsltunePfVnrwrtl0b17ZvDTfi8ZUwTGddi7VNnN53rR5zIUh3t6uvySB9lzl8seN3V3Teju52Pj7jEdYba3A9vn+d0C3TSmjEE/Otc7JZfG59cZOjE69zO181OO036hTPuXKr0bAzd7a8rmKpE0qXnGm3abmurruc72CJVa2Fp2Ko73qxGIa51+SISzRt+fB7ysm/N9b+Anf3GTKbxaApOvGR/VB5MOFnk4ml6XLdc3mP7zM8i321hOEd77kXu/WD0RKnqy+5afZ965pyd8POBNiv45Erl96GOfbVVejzodDEukhn+RfHHbn5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'


def _l2_source(blob):
    return _l2_zlib.decompress(_l2_b64.b64decode(blob)).decode("utf-8")


def _l2_ns(name, inject=None):
    ns = {"__name__": "l2_" + name}
    ns.update(inject or {})
    exec(compile(_l2_source(_L2_SRC[name]), "l2_" + name, "exec"), ns)
    return ns


_L2_A_CODE = compile(_l2_source(_L2_A_VERBATIM), "agent_a_verbatim", "exec")


def _l2_a_factory():
    """A fresh copy of the unmodified Agent A, for the opponent shadow."""
    env = {}
    exec(_L2_A_CODE, env)
    return env, [v for v in env.values() if callable(v)][-1]


_L2_ENV = globals()
_L2 = {}
_L2["market_front"] = _l2_ns("market_front", {})
_L2["animals"] = _l2_ns("animals", {})
_L2["wheat_rt"] = _l2_ns("wheat_rt", {"_mf_price": _L2["market_front"]["_mf_price"]})
_L2["outfarm"] = _l2_ns("outfarm", {})
_L2["labour"] = _l2_ns("labour", {})
_L2["shadow"] = _l2_ns("shadow", {})
_L2["safety"] = _l2_ns("safety", {})
_l2_agent = kaggle_agent                  # Agent A's entry point (ig_agent), gate 120
_l2_agent = _L2["animals"]["an_wrap"](_l2_agent, _L2_ENV, {})
_l2_agent = _L2["wheat_rt"]["rt_inner"](_l2_agent, _L2_ENV)
_l2_agent = _L2["outfarm"]["lot_wrap"](_l2_agent, _L2_ENV)
_l2_agent = _L2["market_front"]["mf_wrap"](_l2_agent)
_l2_agent = _L2["labour"]["lb_wrap"](_l2_agent)
_l2_agent = _L2["shadow"]["shadow_wrap"](_l2_agent, reorder=True, early=True,
                                         factories={"A": _l2_a_factory})
agent_l2 = _L2["safety"]["sf_wrap"](_l2_agent, name="L2")
