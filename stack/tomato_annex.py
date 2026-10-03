# ---- BEGIN tomato_annex (Agent N3's own layer) ----
# More tomato tiles beside the parent's day-18 tomato project, worked by the
# annex's own hands.
#
# Stronger opponents plant 12-20 tomato tiles to the parent's 10; on recorded
# markets 5 more fertilized tiles were worth +4.8k to +9.6k before about 3.5k
# of costs. As in stack/se_project.py, the parent never sees the annex: annex
# tiles show empty and its hands, seeds, fertilizer and undelivered tomatoes are
# masked out. The annex hires after the parent's orders, buys its own seeds and
# fertilizer, and sells only the tomatoes its hands placed in the shed. Planted
# on day 18, the tiles are fertilized on days 24 and 26, watered daily on days
# 25-28 and harvested on days 27 and 29.

import copy as _ta_copy

_TA_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_TA_MAX_ORDERS = 10
_TA_LAST_STEP = 718          # the last step whose actions and orders count
_TA_SEED_COST = 50

TA_DEFAULTS = {
    'rows': (7,),            # SE rows for the annex (V219 plants rows 5-6)
    'plant_day': 18,
    'last_start_hour': 4,    # day 18: the annex must be hired by this hour
    'fert_days': (24, 26),   # fertilizer lasts 3 days: 24 covers the nights of 25-26, 26 of 26-28
    'harvest_days': (27, 29),
    'max_hands': 3,          # annex hands on one day
    'last_hire_hour': 6,     # the day's crew is hired by this hour
    'max_hire_cost': 1600,   # never pay more than this for one annex hand-day
    'reserve': 3000,         # money kept after the annex's orders
    # Tomato demand gate at the start (day 18). On N's pinned project games the
    # annex lost only in towns with 2 tomato shops or a small shortage (-1,320,
    # -686, -33); elsewhere the margin rose +201..+5,537.
    'min_tomato_shops': 0,   # PIZZA_SHOP + FARMERS_MARKET unlocked
    'min_shortage': 0,       # 10000 - the tomato book's inventory
}


def _ta_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _ta_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _ta_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x != tx:
        return ['EAST' if x < tx else 'WEST']
    if y != ty:
        return ['SOUTH' if y < ty else 'NORTH']
    return None


def _ta_home(pos):
    return min(_TA_ACCESS, key=lambda p: (_ta_dist(pos, p), _TA_ACCESS.index(p)))


def _ta_new_state():
    return {'last_step': -1, 'day': -1, 'active': False, 'done': False, 'tiles': [],
            'mine': [], 'groups': {}, 'hire_req': None, 'hired_day': -1,
            'seeds': 0, 'fert': 0, 'unsold': 0, 'last_cmds': {}, 'loaded': set(),
            'report': {'start_step': None, 'tiles': 0, 'hires': 0, 'hire_cost': 0,
                       'hand_days': 0, 'seed_cost': 0, 'fert_bought': 0, 'fert_cost': 0,
                       'plants': 0, 'fertilized': 0, 'harvest_units': 0, 'placed_units': 0,
                       'sold_units': 0, 'sale_value': 0, 'lost_tiles': 0, 'hire_skips': 0,
                       'errors': 0}}


def ta_wrap(parent, **overrides):
    settings = _ta_copy.deepcopy(TA_DEFAULTS)
    settings.update(overrides)
    states = {}
    plan_tiles = []                      # snake order along the rows, from x=5
    for k, y in enumerate(settings['rows']):
        xs = range(5, 10) if k % 2 == 0 else range(9, 4, -1)
        plan_tiles += [(x, y) for x in xs]

    # ---- what a tile needs today ----

    def jobs(tile, day, hand_fert=True):
        """Ordered jobs for one annex tile today (from its observed state)."""
        out = []
        if day == settings['plant_day'] and (tile is None or (isinstance(tile, dict) and tile.get('kind') == 'WEED')):
            if isinstance(tile, dict):
                out.append('DIG')
            return out + ['PLANT', 'WATER']
        if not (isinstance(tile, dict) and tile.get('crop') == 'TOMATO'):
            return out
        until = int(tile.get('fertilized_until_day', -1))
        if day in settings['fert_days'] and until < day + 2 and hand_fert:
            out.append('FERTILIZE')
            until = day + 2
        if day <= 28 and not tile.get('watered_today') and (
                int(tile.get('consecutive_unwatered', 0)) >= 1 or (day >= 25 and until >= day)):
            out.append('WATER')
        held = int(tile.get('yield_units', 0))
        if held > 0 and (day in settings['harvest_days'] or held >= 4 or day >= 29):
            out.append('HARVEST')
        return out

    def group_turns(group, day, tiles_now, start=(5, 5)):
        """Turns one hand needs for a contiguous group of tiles today."""
        turns, pos, carry, fert = 0, start, False, False
        for xy in group:
            j = jobs(tiles_now(xy), day)
            if not j:
                continue
            fert = fert or 'FERTILIZE' in j
            carry = carry or 'HARVEST' in j
            turns += _ta_dist(pos, xy) + len(j)
            pos = xy
        if carry:
            turns += _ta_dist(pos, _ta_home(pos)) + 1
        return turns + (1 if fert else 0)

    def split(day, tiles_now, budget):
        """Fewest contiguous groups of today's working tiles that each fit."""
        work = [xy for xy in plan_tiles if xy in set(tiles_now.keys) and jobs(tiles_now(xy), day)]
        if not work:
            return []
        for k in range(1, settings['max_hands'] + 1):
            size = -(-len(work) // k)
            groups = [work[i:i + size] for i in range(0, len(work), size)]
            if all(group_turns(g, day, tiles_now) <= budget for g in groups):
                return groups
        size = -(-len(work) // settings['max_hands'])
        return [work[i:i + size] for i in range(0, len(work), size)]

    class _Tiles:
        def __init__(self, farm, st):
            self.farm = farm
            self.keys = st['tiles']

        def __call__(self, xy):
            return self.farm['tiles'][xy[1]][xy[0]]

    # ---- before the parent ----

    def reconcile(obs, st):
        step = int(obs['step'])
        day = step // 24
        farm = obs['farms'][int(obs['player'])]
        private = obs['private']
        rep = st['report']
        night = day != st['day']
        invs = private.get('inventories') or []
        for p, cmd in st['last_cmds'].items():
            op = cmd['cmd'][0]
            if op == 'PLANT':
                x, y = cmd['tile']
                tile = farm['tiles'][y][x]
                if isinstance(tile, dict) and tile.get('crop') == 'TOMATO':
                    st['seeds'] = max(0, st['seeds'] - 1)
                    rep['plants'] += 1
            if night:
                continue             # the cargo dropped into the parent's shed at midnight
            now = invs[p + 1] if p + 1 < len(invs) else {}
            before = cmd['cargo']
            if op == 'PICKUP':
                st['fert'] = max(0, st['fert'] - max(0, now.get('FERTILIZER', 0) - before.get('FERTILIZER', 0)))
            elif op == 'FERTILIZE':
                rep['fertilized'] += max(0, before.get('FERTILIZER', 0) - now.get('FERTILIZER', 0))
            elif op == 'HARVEST':
                rep['harvest_units'] += max(0, now.get('TOMATO', 0) - before.get('TOMATO', 0))
            elif op == 'PLACE':
                placed = max(0, before.get('TOMATO', 0) - now.get('TOMATO', 0))
                rep['placed_units'] += placed
                st['unsold'] += max(0, placed - cmd.get('sold', 0))
        st['last_cmds'] = {}
        if night:
            st['mine'] = []
            st['groups'] = {}
            st['hire_req'] = None
            st['loaded'] = set()
            st['fert'] = 0           # unused annex fertilizer is released to the parent
            st['day'] = day
        hands = farm.get('hands') or []
        req = st['hire_req']
        if req is not None:
            if req['step'] == step - 1:
                new = len(hands) - req['base']
                parent_new = min(max(new, 0), req['parent'])
                mine_new = max(0, min(new - parent_new, len(req['groups'])))
                first = req['base'] + parent_new
                for k in range(mine_new):
                    st['mine'].append(first + k)
                    st['groups'][first + k] = req['groups'][k]
                if mine_new:
                    st['hired_day'] = day
                rep['hires'] += mine_new
                rep['hand_days'] += mine_new
                rep['hire_cost'] += sum(req['costs'][:mine_new])
            st['hire_req'] = None
        shed = private.get('shed') or {}
        st['unsold'] = max(0, min(st['unsold'], int(shed.get('TOMATO', 0))))
        st['fert'] = max(0, min(st['fert'], int(shed.get('FERTILIZER', 0))))
        st['seeds'] = max(0, min(st['seeds'], int((private.get('seeds') or {}).get('TOMATO', 0))))
        if st['active']:
            alive = []
            for (x, y) in st['tiles']:
                tile = farm['tiles'][y][x]
                if day > settings['plant_day'] and not (isinstance(tile, dict) and tile.get('crop') == 'TOMATO'):
                    rep['lost_tiles'] += 1
                    continue
                alive.append((x, y))
            st['tiles'] = alive

    def masked(obs, st):
        player = int(obs['player'])
        farm = obs['farms'][player]
        mine = set(st['mine'])
        hands = farm.get('hands') or []
        farm2 = dict(farm)
        farm2['hands'] = [h for i, h in enumerate(hands) if i not in mine]
        farm2['hires_today'] = max(0, int(farm.get('hires_today', 0)) - len(mine))
        if st['tiles']:
            rows = [list(r) for r in farm['tiles']]
            for (x, y) in st['tiles']:
                rows[y][x] = None
            farm2['tiles'] = rows
        farms2 = list(obs['farms'])
        farms2[player] = farm2
        private = obs['private']
        private2 = dict(private)
        invs = private.get('inventories') or [{}]
        private2['inventories'] = [invs[0]] + [invs[i + 1] for i in range(len(hands))
                                               if i not in mine and i + 1 < len(invs)]
        seeds2 = dict(private.get('seeds') or {})
        seeds2['TOMATO'] = max(0, int(seeds2.get('TOMATO', 0)) - st['seeds'])
        shed2 = dict(private.get('shed') or {})
        shed2['TOMATO'] = max(0, int(shed2.get('TOMATO', 0)) - st['unsold'])
        shed2['FERTILIZER'] = max(0, int(shed2.get('FERTILIZER', 0)) - st['fert'])
        private2['seeds'] = seeds2
        private2['shed'] = shed2
        obs2 = dict(obs)
        obs2['farms'] = farms2
        obs2['private'] = private2
        return obs2

    # ---- after the parent ----

    def worker(obs, st, p, group):
        step = int(obs['step'])
        day = step // 24
        farm = obs['farms'][int(obs['player'])]
        pos = tuple(farm['hands'][p])
        invs = obs['private'].get('inventories') or []
        inv = invs[p + 1] if p + 1 < len(invs) else {}
        end = _TA_LAST_STEP if day >= 29 else day * 24 + 23
        if step > end:
            return ['PASS'], None
        tomatoes = int(inv.get('TOMATO', 0))
        home = _ta_home(pos)
        if tomatoes and step + _ta_dist(pos, home) >= end:
            return (_ta_toward(pos, home) or ['PLACE', 'TOMATO', tomatoes]), None
        tiles_now = _Tiles(farm, st)
        want_fert = day in settings['fert_days'] and any(
            'FERTILIZE' in jobs(tiles_now(xy), day) for xy in group)
        if want_fert and p not in st['loaded'] and not inv.get('FERTILIZER', 0):
            st['loaded'].add(p)
            need = sum('FERTILIZE' in jobs(tiles_now(xy), day) for xy in group)
            if pos in _TA_ACCESS and st['fert'] > 0:
                return ['PICKUP', 'FERTILIZER', min(need, st['fert'])], None
        has_fert = inv.get('FERTILIZER', 0) > 0
        todo = []
        for xy in group:
            j = jobs(tiles_now(xy), day, hand_fert=has_fert)
            if j:
                todo.append((xy, j[0]))
        if todo:
            xy, job = min(todo, key=lambda t: (_ta_dist(pos, t[0]), plan_tiles.index(t[0])))
            move = _ta_toward(pos, xy)
            if move:
                return move, None
            return ([job, 'TOMATO'] if job == 'PLANT' else [job]), xy
        if tomatoes:
            return (_ta_toward(pos, home) or ['PLACE', 'TOMATO', tomatoes]), None
        return ['PASS'], None

    def after(obs, st, action):
        step = int(obs['step'])
        day = step // 24
        hour = step % 24
        farm = obs['farms'][int(obs['player'])]
        prices = obs['market']['prices']
        private = obs['private']
        rep = st['report']
        action = dict(action) if isinstance(action, dict) else {}
        market = list(action.get('market') or [])
        while market and not market[-1]:
            market.pop()
        parent_hands = list(action.get('hands') or [])
        hands = farm.get('hands') or []
        mine = st['mine']
        room = _TA_MAX_ORDERS - len(market)
        extra = []
        spend = 0
        parent_hires = 0
        for o in market:
            if not (isinstance(o, list) and o):
                continue
            if o[0] == 'HIRE':
                spend += _ta_fib(int(farm.get('hires_today', 0)) + parent_hires)
                parent_hires += 1
            elif o[0] == 'BUY_LAND':
                spend += 4000
            elif o[0] in ('BUY_SEED', 'BUY_PRODUCT', 'BUY_ANIMAL') and len(o) >= 3:
                try:
                    n = int(o[2])
                except (TypeError, ValueError):
                    n = 0
                unit = {'BUY_SEED': 100, 'BUY_ANIMAL': 500}.get(o[0], int(prices.get(o[1], 100)) + 5)
                spend += n * unit
        money = float(farm['money']) - spend

        # Start: the step the parent commits its day-18 tomato project.
        starting = False
        if settings.get('debug') and day == settings['plant_day'] and hour <= 6:
            rep.setdefault('debug', []).append((step, len(market), [o[:2] for o in market if o],
                                                sorted(farm.get('unlocked_quadrants') or [])))
        if not st['active'] and not st['done'] and day == settings['plant_day']:
            buying_land = any(o[0] == 'BUY_LAND' for o in market if isinstance(o, list) and o)
            buying_seed = any(o[:2] == ['BUY_SEED', 'TOMATO'] for o in market if isinstance(o, list) and o)
            quadrants = set(farm.get('unlocked_quadrants') or [])
            # The parent's project: it buys SE and tomato seeds in one step (the
            # market is usually full then), so start that step or the next ones,
            # while its seeds wait in stock or its rows 5-6 hold tomatoes.
            committing = buying_land and buying_seed and quadrants == {'NW', 'NE', 'SW'}
            committed = 'SE' in quadrants and (
                int((private.get('seeds') or {}).get('TOMATO', 0)) > 0
                or any(isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('crop') == 'TOMATO'
                       for y in (5, 6) for x in range(5, 10)))
            shops = obs['town'].get('unlocked_shops') or []
            demand = (sum(x in ('PIZZA_SHOP', 'FARMERS_MARKET') for x in shops) >= settings['min_tomato_shops']
                      and 10000 - int(obs['market']['inventory'].get('TOMATO', 10000)) >= settings['min_shortage'])
            if hour > settings['last_start_hour']:
                st['done'] = True
            elif (committing or committed) and not demand:
                st['done'] = True
                rep['gated'] = 1
            elif committing or committed:
                free = [xy for xy in plan_tiles
                        if farm['tiles'][xy[1]][xy[0]] in (None, 'LOCKED')
                        or (isinstance(farm['tiles'][xy[1]][xy[0]], dict)
                            and farm['tiles'][xy[1]][xy[0]].get('kind') == 'WEED')]
                cost = len(free) * _TA_SEED_COST + 2 * _ta_fib(int(farm.get('hires_today', 0)) + parent_hires + 1)
                if free and room >= 2 and money >= cost + settings['reserve']:
                    extra.append(['BUY_SEED', 'TOMATO', len(free)])
                    money -= len(free) * _TA_SEED_COST
                    st['seeds'] += len(free)
                    rep['seed_cost'] += len(free) * _TA_SEED_COST
                    st['tiles'] = free
                    st['active'] = True
                    rep['start_step'] = step
                    rep['tiles'] = len(free)
                    starting = True

        # Hands for today's work, hired right after the parent's orders.
        if st['active'] and st['tiles'] and st['hire_req'] is None and st['hired_day'] != day \
                and (starting or hour <= settings['last_hire_hour']) and step < _TA_LAST_STEP - 4:
            tiles_now = _Tiles(farm, st)
            if starting:                 # the tiles are still LOCKED or empty: plan the planting day
                class _Plant:
                    keys = st['tiles']

                    def __call__(self, xy):
                        return None
                tiles_now = _Plant()
            budget = (22 if day >= 29 else 23) - hour - 2
            groups = split(day, tiles_now, budget)
            if groups:
                hires_now = int(farm.get('hires_today', 0)) + parent_hires
                need_fert = sum('FERTILIZE' in jobs(tiles_now(xy), day) for g in groups for xy in g)
                need_fert = max(0, need_fert - st['fert'])
                free = room - len(extra) - (1 if need_fert else 0)
                if len(groups) > free and hour < settings['last_hire_hour'] and not starting:
                    # Not enough market slots for today's crew (and its fertilizer):
                    # the parent's hires fill hour 0; wait for the next hour.
                    rep['hire_waits'] = rep.get('hire_waits', 0) + 1
                    groups = []
            if groups:
                costs = []
                for j in range(len(groups)):
                    c = _ta_fib(hires_now + j)
                    if c > settings['max_hire_cost'] or j >= free or money < c + settings['reserve']:
                        break
                    costs.append(c)
                    money -= c
                if len(costs) < len(groups):
                    rep['hire_skips'] += len(groups) - len(costs)
                if costs:
                    if len(costs) < len(groups):
                        groups = [sum(groups[i::len(costs)], []) for i in range(len(costs))]
                    if need_fert and len(extra) < room:
                        price = int(prices.get('FERTILIZER', 100))
                        extra.append(['BUY_PRODUCT', 'FERTILIZER', need_fert])
                        st['fert'] += need_fert
                        rep['fert_bought'] += need_fert
                        rep['fert_cost'] += need_fert * (price + 1)
                        money -= need_fert * (price + 1)
                    extra += [['HIRE'] for _ in costs]
                    st['hire_req'] = {'step': step, 'base': len(hands), 'parent': parent_hires,
                                      'groups': groups, 'costs': costs}
                    if settings.get('debug'):
                        rep.setdefault('log', []).append((day, hour, [len(g) for g in groups], costs, need_fert))

        # The annex hands' commands.
        commands = {}
        sell_now = 0
        invs = private.get('inventories') or []
        for p in mine:
            if p >= len(hands):
                continue
            command, xy = worker(obs, st, p, st['groups'].get(p, []))
            cargo = dict(invs[p + 1]) if p + 1 < len(invs) else {}
            rec = {'cmd': command, 'tile': xy, 'cargo': cargo}
            if command[0] == 'PLACE':
                shed_total = sum(int(v) for v in (private.get('shed') or {}).values())
                q = int(command[2])
                if shed_total + q <= 85:
                    rec['sold'] = q      # placed before the market of this step: sell it now
                    sell_now += q
            st['last_cmds'][p] = rec
            commands[p] = command

        # Sell what the annex placed (same step) and anything left over.
        total = sell_now + st['unsold']
        if total > 0:
            merged = False
            for i, o in enumerate(market):
                if isinstance(o, list) and len(o) >= 3 and o[:2] == ['SELL', 'TOMATO']:
                    market[i] = ['SELL', 'TOMATO', int(o[2]) + total] + list(o[3:])
                    merged = True
                    break
            if not merged and len(extra) < room:
                extra.append(['SELL', 'TOMATO', total])
                merged = True
            if merged:
                rep['sold_units'] += total
                rep['sale_value'] += total * int(prices.get('TOMATO', 0))
                st['unsold'] = 0
            else:
                for rec in st['last_cmds'].values():
                    rec.pop('sold', None)

        action['market'] = market + extra[:max(0, room)]
        if mine:
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
        """If the annex code fails, the parent's hands still get their commands."""
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

    def ta_agent(observation, configuration=None):
        step = int(observation['step'])
        player = int(observation['player'])
        st = states.get(player)
        if st is None or step <= st['last_step']:
            st = _ta_new_state()
            states[player] = st
            ta_agent.telemetry = st['report']
        st['last_step'] = step
        try:
            reconcile(observation, st)
        except Exception:
            st['report']['errors'] += 1
        view = observation
        if st['tiles'] or st['mine'] or st['seeds'] or st['fert'] or st['unsold']:
            try:
                view = masked(observation, st)
            except Exception:
                st['report']['errors'] += 1
                view = observation
        action = parent(view, configuration)
        try:
            return after(observation, st, action)
        except Exception:
            st['report']['errors'] += 1
            return fallback(observation, st, action)

    ta_agent.telemetry = _ta_new_state()['report']
    ta_agent.settings = settings
    return ta_agent
# ---- END tomato_annex ----
