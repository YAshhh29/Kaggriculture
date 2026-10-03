# ---- BEGIN fert_runner (Agent N5's own layer) ----
# A fertilizer runner: one extra hand that fertilizes young wheat and carrot.
#
# Why: the 3000-rated teams fertilize 59-74% of their wheat lives (5.3-5.8
# units a life) against N's 22% (3.7 units), and N dumps ~111 fertilizer a
# game at 25 coins or less while wheat sells at 40-43 (study top_farms.md,
# P1). N's route books its wheat waterers solid, so fertilizing inside the
# route gains little (8 free turns a game); a dedicated hand does not need
# the route's turns.
#
# Engine: a WATER on wheat aged 2-4 (carrot 2-3) adds one unit, two while the
# tile is fertilized (FERTILIZE covers today and the next two days); wheat
# caps at 6 units (unfertilized lives reach 4), carrot at 4 (3). So wheat
# fertilized at age 1 gains 2 units from the route's own waterings at ages 2
# and 3, carrot at age 1 gains 1.
#
# How (as stack/tomato_annex.py): the parent never sees the runner. Each turn it
# gets a masked observation -- the runner's hand, its cargo and the runner's
# unpicked fertilizer removed. On days first_day..last_day, at the first hour
# the market has room, the runner prices today's targets (age-1 wheat and
# carrot not yet fertilized for the coming waterings, on a nearest-first path
# that fits the day's turns) at the current quotes; it hires one hand and buys
# the fertilizer only when the targets' value beats fertilizer plus the hire
# by `min_ratio`. The hand picks the fertilizer up at the shed, walks the
# path and fertilizes each tile still unfertilized; whatever it does not use
# drops into the shed at midnight, where the parent sells or uses it.

import copy as _fr_copy

_FR_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_FR_MAX_ORDERS = 10
_FR_CROPS = {'WHEAT': (2, 4, 2), 'CARROT': (2, 3, 1)}   # window start, end, max gain

FR_DEFAULTS = {
    'first_day': 12,
    'last_day': 26,
    'last_hire_hour': 3,
    'max_targets': 10,
    'min_ratio': 1.3,        # targets' value / (fertilizer + hire)
    'min_net': 60,           # and at least this many coins net
    'harvest_risk': 0.85,    # share of the gain kept (some lives are pulled at age 2)
    'reserve': 3000,
}


def _fr_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _fr_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _fr_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x != tx:
        return ['EAST' if x < tx else 'WEST']
    if y != ty:
        return ['SOUTH' if y < ty else 'NORTH']
    return None


def _fr_gain(tile, day):
    """Extra units from fertilizing this tile today (0 if none)."""
    if not (isinstance(tile, dict) and tile.get('kind') == 'PLANT' and tile.get('crop') in _FR_CROPS):
        return 0
    lo, hi, cap = _FR_CROPS[tile['crop']]
    pd = int(tile.get('planted_day', day))
    if day - pd != 1:
        return 0
    until = int(tile.get('fertilized_until_day', -1))
    new = [d for d in (day + 1, day + 2) if pd + lo <= d <= pd + hi and d > until]
    return min(len(new), cap)


def _fr_new_state():
    return {'last_step': -1, 'day': -1, 'mine': [], 'hire_req': None, 'hired_day': -1,
            'fert': 0, 'plan': {}, 'last_cmds': {}, 'loaded': set(),
            'report': {'days': 0, 'hires': 0, 'hire_cost': 0, 'fert_bought': 0, 'fert_cost': 0,
                       'fertilized': 0, 'planned_units': 0, 'declined': 0, 'errors': 0}}


def fr_wrap(parent, **overrides):
    settings = _fr_copy.deepcopy(FR_DEFAULTS)
    settings.update(overrides)
    states = {}

    def reconcile(obs, st):
        step = int(obs['step'])
        day = step // 24
        farm = obs['farms'][int(obs['player'])]
        invs = obs['private'].get('inventories') or []
        rep = st['report']
        if day != st['day']:
            st.update(day=day, mine=[], hire_req=None, plan={}, last_cmds={}, loaded=set(), fert=0)
            return
        for p, cmd in st['last_cmds'].items():
            now = invs[p + 1] if p + 1 < len(invs) else {}
            before = cmd['cargo']
            if cmd['cmd'][0] == 'PICKUP':
                st['fert'] = max(0, st['fert'] - max(0, now.get('FERTILIZER', 0) - before.get('FERTILIZER', 0)))
            elif cmd['cmd'][0] == 'FERTILIZE':
                rep['fertilized'] += max(0, before.get('FERTILIZER', 0) - now.get('FERTILIZER', 0))
        st['last_cmds'] = {}
        hands = farm.get('hands') or []
        req = st['hire_req']
        if req is not None:
            if req['step'] == step - 1:
                new = len(hands) - req['base']
                parent_new = min(max(new, 0), req['parent'])
                if new - parent_new >= 1:
                    p = req['base'] + parent_new
                    st['mine'] = [p]
                    st['plan'][p] = list(req['path'])
                    st['hired_day'] = day
                    rep['hires'] += 1
                    rep['days'] += 1
                    rep['hire_cost'] += req['cost']
            st['hire_req'] = None
        shed = obs['private'].get('shed') or {}
        st['fert'] = max(0, min(st['fert'], int(shed.get('FERTILIZER', 0))))

    def masked(obs, st):
        player = int(obs['player'])
        farm = obs['farms'][player]
        mine = set(st['mine'])
        hands = farm.get('hands') or []
        farm2 = dict(farm)
        farm2['hands'] = [h for i, h in enumerate(hands) if i not in mine]
        farm2['hires_today'] = max(0, int(farm.get('hires_today', 0)) - len(mine))
        farms2 = list(obs['farms'])
        farms2[player] = farm2
        private = obs['private']
        private2 = dict(private)
        invs = private.get('inventories') or [{}]
        private2['inventories'] = [invs[0]] + [invs[i + 1] for i in range(len(hands))
                                               if i not in mine and i + 1 < len(invs)]
        shed2 = dict(private.get('shed') or {})
        shed2['FERTILIZER'] = max(0, int(shed2.get('FERTILIZER', 0)) - st['fert'])
        private2['shed'] = shed2
        obs2 = dict(obs)
        obs2['farms'] = farms2
        obs2['private'] = private2
        return obs2

    def plan_path(farm, day, budget):
        """Nearest-first path over today's targets that fits `budget` turns
        (one PICKUP, the walk, one FERTILIZE a tile)."""
        targets = {}
        for y, row in enumerate(farm['tiles']):
            for x, tile in enumerate(row):
                g = _fr_gain(tile, day)
                if g:
                    targets[(x, y)] = (g, tile['crop'])
        path, pos, used = [], (5, 5), 1
        while targets and len(path) < settings['max_targets']:
            xy = min(targets, key=lambda t: (_fr_dist(pos, t) - 2 * targets[t][0], t))
            cost = _fr_dist(pos, xy) + 1
            if used + cost > budget:
                break
            used += cost
            path.append((xy, targets.pop(xy)))
            pos = xy
        return path

    def worker(obs, st, p):
        step = int(obs['step'])
        day = step // 24
        farm = obs['farms'][int(obs['player'])]
        pos = tuple(farm['hands'][p])
        invs = obs['private'].get('inventories') or []
        inv = invs[p + 1] if p + 1 < len(invs) else {}
        if p not in st['loaded']:
            st['loaded'].add(p)
            if pos in _FR_ACCESS and st['fert'] > 0:
                return ['PICKUP', 'FERTILIZER', min(st['fert'], len(st['plan'].get(p, [])))]
        if not inv.get('FERTILIZER', 0):
            return ['PASS']
        path = st['plan'].get(p, [])
        while path:
            xy, _ = path[0]
            tile = farm['tiles'][xy[1]][xy[0]]
            if not _fr_gain(tile, day):
                path.pop(0)
                continue
            move = _fr_toward(pos, xy)
            if move:
                return move
            path.pop(0)
            return ['FERTILIZE']
        return ['PASS']

    def after(obs, st, action):
        step = int(obs['step'])
        day = step // 24
        hour = step % 24
        farm = obs['farms'][int(obs['player'])]
        prices = obs['market']['prices']
        rep = st['report']
        action = dict(action) if isinstance(action, dict) else {}
        market = list(action.get('market') or [])
        while market and not market[-1]:
            market.pop()
        parent_hands = list(action.get('hands') or [])
        hands = farm.get('hands') or []
        parent_hires = sum(1 for o in market if isinstance(o, list) and o and o[0] == 'HIRE')
        room = _FR_MAX_ORDERS - len(market)
        extra = []
        if (settings['first_day'] <= day <= settings['last_day'] and hour <= settings['last_hire_hour']
                and not st['mine'] and st['hire_req'] is None and st['hired_day'] != day and room >= 2):
            path = plan_path(farm, day, 22 - hour)
            if path:
                hire = _fr_fib(int(farm.get('hires_today', 0)) + parent_hires)
                fq = int(prices.get('FERTILIZER', 100)) + 1
                value = settings['harvest_risk'] * sum(
                    g * max(1, int(prices.get(crop, 0)) - 2) for _, (g, crop) in path)
                cost = hire + len(path) * fq
                spend = sum(_fr_fib(int(farm.get('hires_today', 0)) + i) for i in range(parent_hires))
                if (value >= settings['min_ratio'] * cost and value - cost >= settings['min_net']
                        and float(farm['money']) - spend - cost >= settings['reserve']):
                    extra += [['BUY_PRODUCT', 'FERTILIZER', len(path)], ['HIRE']]
                    st['fert'] += len(path)
                    st['hire_req'] = {'step': step, 'base': len(hands), 'parent': parent_hires,
                                      'path': path, 'cost': hire}
                    rep['fert_bought'] += len(path)
                    rep['fert_cost'] += len(path) * fq
                    rep['planned_units'] += sum(g for _, (g, _) in path)
                elif hour == settings['last_hire_hour']:
                    rep['declined'] += 1
        commands = {}
        invs = obs['private'].get('inventories') or []
        for p in st['mine']:
            if p < len(hands):
                cmd = worker(obs, st, p)
                commands[p] = cmd
                st['last_cmds'][p] = {'cmd': cmd, 'cargo': dict(invs[p + 1]) if p + 1 < len(invs) else {}}
        action['market'] = market + extra[:max(0, room)]
        if st['mine']:
            out, k = [], 0
            for i in range(len(hands)):
                if i in commands:
                    out.append(commands[i])
                elif i in st['mine']:
                    out.append(['PASS'])
                else:
                    out.append(parent_hands[k] if k < len(parent_hands) else ['PASS'])
                    k += 1
            action['hands'] = out
        return action

    def fallback(obs, st, action):
        hands = obs['farms'][int(obs['player'])].get('hands') or []
        mine = set(st['mine'])
        if not mine or not isinstance(action, dict):
            return action
        parent_hands = list(action.get('hands') or [])
        out, k = [], 0
        for i in range(len(hands)):
            if i in mine:
                out.append(['PASS'])
            else:
                out.append(parent_hands[k] if k < len(parent_hands) else ['PASS'])
                k += 1
        return dict(action, hands=out)

    def fr_agent(observation, configuration=None):
        step = int(observation['step'])
        player = int(observation['player'])
        st = states.get(player)
        if st is None or step <= st['last_step']:
            st = _fr_new_state()
            states[player] = st
            fr_agent.telemetry = st['report']
        st['last_step'] = step
        try:
            reconcile(observation, st)
        except Exception:
            st['report']['errors'] += 1
        view = observation
        if st['mine'] or st['fert']:
            try:
                view = masked(observation, st)
            except Exception:
                st['report']['errors'] += 1
        action = parent(view, configuration)
        try:
            return after(observation, st, action)
        except Exception:
            st['report']['errors'] += 1
            return fallback(observation, st, action)

    fr_agent.telemetry = _fr_new_state()['report']
    fr_agent.settings = settings
    return fr_agent
# ---- END fert_runner ----
