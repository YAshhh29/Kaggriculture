# ---- BEGIN se_project (Agent L's own layer) ----
# A fourth-quadrant production project wrapped around a complete agent.
#
# The parent keeps three quadrants all game while its cash sits idle; stronger
# ladder teams buy the fourth (SE) quadrant around day 10 and grow wheat and
# carrot on it. The parent never sees the project: its observation shows SE as
# LOCKED, with the project's hands, seeds and stock removed. The project hires
# its own hands after the parent's (so hand indices never shift), buys its own
# seeds, sells only what its hands delivered, and hires only under a cost
# ceiling (the n-th hire of a day costs fib(n)).

import copy as _se_copy

# Snake order from the SE shed-access tile (5,5).
_SE_TILES = [(x, y) for y in range(5, 10)
             for x in (range(5, 10) if y % 2 else range(9, 4, -1))]
_SE_INDEX = {t: i for i, t in enumerate(_SE_TILES)}
_SE_HOME = (5, 5)
_SE_CROPS = {                # engine CROPS for the two crops the project grows
    'WHEAT': {'window': 2, 'max_day': 4, 'max_yield': 6, 'first': 2},
    'CARROT': {'window': 2, 'max_day': 3, 'max_yield': 4, 'first': 2},
}
_SE_ITEMS = ('WHEAT', 'CARROT')
_SE_ANIMAL_COST = {'GOOSE': 300, 'COW': 400, 'SHEEP': 500}
_SE_SEED_COST = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
_SE_LAND_COST = 4000
_SE_MAX_ORDERS = 10
_SE_LAST_STEP = 718          # actions observed at this step are the last to count

SE_DEFAULTS = {
    'buy_from_day': 10,
    'buy_until_day': 14,
    'reserve': 4000,           # parent keeps at least this after land and project costs
    'max_workers': 2,
    'max_hire_cost': 250,      # never pay more than this for one project hand-day
    'tiles_per_worker': 10,
    'carrot_every': 4,         # every 4th tile grows carrot, the rest wheat
    'last_plant': {'WHEAT': 26, 'CARROT': 26},
    'min_sell': {'WHEAT': 18, 'CARROT': 22},
    'first_hire_hour': 2,      # the parent hires at hours 0-1
    'last_hire_hour': 10,
    'deliver_daily': True,     # walk cargo home each evening (else the nightly drop)
}


def _se_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _se_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _se_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x != tx:
        return ['EAST' if x < tx else 'WEST']
    if y != ty:
        return ['SOUTH' if y < ty else 'NORTH']
    return None


def _se_order_cost(order, prices, hires_before):
    """Money one parent order can spend, and how many hires it makes."""
    if not isinstance(order, list) or not order:
        return 0, 0
    op = order[0]
    if op == 'HIRE':
        return _se_fib(hires_before), 1
    if op == 'BUY_LAND':
        return _SE_LAND_COST, 0
    try:
        n = int(order[2]) if len(order) >= 3 else 0
    except (TypeError, ValueError):
        return 0, 0
    if op == 'BUY_SEED':
        return n * _SE_SEED_COST.get(order[1], 100), 0
    if op == 'BUY_PRODUCT':
        return n * (int(prices.get(order[1], 100)) + 5), 0
    if op == 'BUY_ANIMAL':
        return n * _SE_ANIMAL_COST.get(order[1], 500), 0
    return 0, 0


def _se_new_state():
    return {'last_step': -1, 'day': -1, 'active': False, 'buy_step': None,
            'mine': [], 'hire_req': None, 'ledger': {'WHEAT': 0, 'CARROT': 0},
            'unsold': {'WHEAT': 0, 'CARROT': 0}, 'last_cmds': {},
            'parent_crew': 0, 'parent_crew_today': 0,
            'report': {'land_day': None, 'hires': 0, 'hire_cost': 0,
                       'seeds': {'WHEAT': 0, 'CARROT': 0}, 'seed_cost': 0,
                       'plants': 0, 'harvest_units': 0, 'placed_units': 0,
                       'sold_units': 0, 'sale_value': 0,
                       'hire_skips_cost': 0, 'errors': 0}}


def se_wrap(parent, **overrides):
    settings = _se_copy.deepcopy(SE_DEFAULTS)
    settings.update(overrides)
    states = {}
    every = settings['carrot_every']
    crop_of = {t: ('CARROT' if every and i % every == every - 1 else 'WHEAT')
               for i, t in enumerate(_SE_TILES)}
    plan = _SE_TILES[:min(len(_SE_TILES), settings['tiles_per_worker'] * settings['max_workers'])]

    # ---- before the parent: what last turn did, and the parent's view ----

    def confirm(obs, st, commands):
        farm = obs['farms'][int(obs['player'])]
        invs = obs['private'].get('inventories') or []
        rep = st['report']
        for p, cmd in commands.items():
            op = cmd['cmd'][0]
            if op == 'PLANT':
                x, y = cmd['tile']
                tile = farm['tiles'][y][x]
                if isinstance(tile, dict) and tile.get('crop') == cmd['cmd'][1]:
                    st['ledger'][cmd['cmd'][1]] -= 1
                    rep['plants'] += 1
            if cmd['night']:
                # Hands are gone; their cargo dropped into the shed at midnight.
                cargo = dict(cmd['cargo'])
                if op == 'PLACE':
                    item = cmd['cmd'][1]
                    placed = min(int(cmd['cmd'][2]), cargo.get(item, 0))
                    cargo[item] = cargo.get(item, 0) - placed
                    st['unsold'][item] += placed
                    rep['placed_units'] += placed
                for item in _SE_ITEMS:
                    st['unsold'][item] += max(0, cargo.get(item, 0))
                continue
            if p + 1 >= len(invs):
                continue
            now = invs[p + 1] or {}
            if op == 'PLACE':
                item = cmd['cmd'][1]
                placed = max(0, cmd['cargo'].get(item, 0) - now.get(item, 0))
                st['unsold'][item] += placed
                rep['placed_units'] += placed
            elif op == 'HARVEST':
                for item in _SE_ITEMS:
                    rep['harvest_units'] += max(0, now.get(item, 0) - cmd['cargo'].get(item, 0))

    def reconcile(obs, st):
        step = int(obs['step'])
        day = step // 24
        farm = obs['farms'][int(obs['player'])]
        private = obs['private']
        rep = st['report']
        night = day != st['day']
        for cmd in st['last_cmds'].values():
            cmd['night'] = night
        confirm(obs, st, st['last_cmds'])
        st['last_cmds'] = {}
        if night:
            st['mine'] = []
            st['hire_req'] = None
            if st['parent_crew_today']:
                st['parent_crew'] = st['parent_crew_today']
            st['parent_crew_today'] = 0
            st['day'] = day
        hands = farm.get('hands') or []
        req = st['hire_req']
        if req is not None:
            if req['step'] == step - 1:
                new = len(hands) - req['base']
                parent_new = min(max(new, 0), req['parent'])
                mine_new = max(0, min(new - parent_new, req['mine']))
                first = req['base'] + parent_new
                st['mine'] += list(range(first, first + mine_new))
                rep['hires'] += mine_new
                rep['hire_cost'] += sum(req['costs'][:mine_new])
            st['hire_req'] = None
        if not st['active'] and st['buy_step'] is not None and \
                'SE' in (farm.get('unlocked_quadrants') or []):
            st['active'] = True
            rep['land_day'] = day
        shed = private.get('shed') or {}
        seeds = private.get('seeds') or {}
        for item in _SE_ITEMS:
            st['unsold'][item] = max(0, min(st['unsold'][item], int(shed.get(item, 0))))
            st['ledger'][item] = max(0, min(st['ledger'][item], int(seeds.get(item, 0))))

    def masked(obs, st):
        player = int(obs['player'])
        farm = obs['farms'][player]
        mine = set(st['mine'])
        hands = farm.get('hands') or []
        farm2 = dict(farm)
        farm2['hands'] = [h for i, h in enumerate(hands) if i not in mine]
        farm2['hires_today'] = max(0, int(farm.get('hires_today', 0)) - len(mine))
        if st['active']:
            farm2['unlocked_quadrants'] = [q for q in farm.get('unlocked_quadrants') or []
                                           if q != 'SE']
            rows = [list(r) for r in farm['tiles']]
            for (x, y) in _SE_TILES:
                rows[y][x] = 'LOCKED'
            farm2['tiles'] = rows
        farms2 = list(obs['farms'])
        farms2[player] = farm2
        private = obs['private']
        private2 = dict(private)
        invs = private.get('inventories') or [{}]
        private2['inventories'] = [invs[0]] + [invs[i + 1] for i in range(len(hands))
                                               if i not in mine and i + 1 < len(invs)]
        seeds2 = dict(private.get('seeds') or {})
        shed2 = dict(private.get('shed') or {})
        for item in _SE_ITEMS:
            seeds2[item] = max(0, int(seeds2.get(item, 0)) - st['ledger'][item])
            shed2[item] = max(0, int(shed2.get(item, 0)) - st['unsold'][item])
        private2['seeds'] = seeds2
        private2['shed'] = shed2
        obs2 = dict(obs)
        obs2['farms'] = farms2
        obs2['private'] = private2
        return obs2

    # ---- after the parent: the project's orders and hands ----

    def worker_command(obs, p, zone, seeds_left, claimed):
        step = int(obs['step'])
        day = step // 24
        hour = step % 24
        farm = obs['farms'][int(obs['player'])]
        pos = tuple(farm['hands'][p])
        invs = obs['private'].get('inventories') or []
        cargo = {k: v for k, v in (invs[p + 1] if p + 1 < len(invs) else {}).items()
                 if k in _SE_ITEMS and v > 0}
        final_day = day >= 29
        end = _SE_LAST_STEP - 1 if final_day else day * 24 + 23
        if step > end:
            return ['PASS'], None
        if cargo and (final_day or settings['deliver_daily']):
            need = _se_dist(pos, _SE_HOME) + len(cargo)
            if step + need >= end:
                move = _se_toward(pos, _SE_HOME)
                if move:
                    return move, None
                item = max(cargo, key=cargo.get)
                return ['PLACE', item, int(cargo[item])], None

        tasks = []
        for xy in zone:
            if xy in claimed:
                continue
            x, y = xy
            tile = farm['tiles'][y][x]
            crop = crop_of[xy]
            if tile is None:
                if day <= settings['last_plant'][crop] and seeds_left[crop] > 0 and hour <= 21:
                    tasks.append((3, xy, ['PLANT', crop]))
            elif not isinstance(tile, dict):
                continue
            elif tile.get('kind') == 'WEED':
                if day <= settings['last_plant'][crop] and hour <= 20:
                    tasks.append((3, xy, ['DIG']))
            elif tile.get('kind') == 'PLANT' and tile.get('crop') in _SE_CROPS:
                info = _SE_CROPS[tile['crop']]
                planted = int(tile.get('planted_day', day))
                age = day - planted
                units = int(tile.get('yield_units', 0))
                in_window = info['window'] <= age <= info['max_day']
                watered = bool(tile.get('watered_today'))
                survives = planted + info['max_day'] <= 29 or age >= info['first']
                if not watered and survives and (in_window or age == 0):
                    urgent = (age == 0 or age >= info['max_day']
                              or int(tile.get('consecutive_unwatered', 0)) >= 1)
                    tasks.append((1 if urgent else 2, xy, ['WATER']))
                elif units > 0 and age >= info['first'] and (
                        age > info['max_day'] or (age == info['max_day'] and watered)
                        or (final_day and (watered or not in_window))):
                    tasks.append((0, xy, ['HARVEST']))
        if tasks:
            _, xy, command = min(tasks, key=lambda t: (t[0] > 1, _se_dist(pos, t[1]),
                                                       t[0], _SE_INDEX[t[1]]))
            return (_se_toward(pos, xy) or command), xy
        if cargo:
            move = _se_toward(pos, _SE_HOME)
            if move:
                return move, None
            item = max(cargo, key=cargo.get)
            return ['PLACE', item, int(cargo[item])], None
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

        n_parent = len(hands) - len(mine)
        parent_hires = sum(1 for o in market if isinstance(o, list) and o and o[0] == 'HIRE')
        st['parent_crew_today'] = max(st['parent_crew_today'], n_parent + parent_hires)
        spend = 0
        hires_before = int(farm.get('hires_today', 0))
        for o in market:
            cost, h = _se_order_cost(o, prices, hires_before)
            spend += cost
            hires_before += h
        money = float(farm['money']) - spend
        room = _SE_MAX_ORDERS - len(market)
        extra = []

        quadrants = set(farm.get('unlocked_quadrants') or [])
        buying = False
        if not st['active']:
            if st['buy_step'] is not None and step - st['buy_step'] > 2:
                st['buy_step'] = None      # the purchase failed; may retry
            if (st['buy_step'] is None and 'SE' not in quadrants
                    and settings['buy_from_day'] <= day <= settings['buy_until_day']
                    and quadrants == {'NW', 'NE', 'SW'}
                    and settings['first_hire_hour'] <= hour <= settings['last_hire_hour']
                    and not any(isinstance(o, list) and o and o[0] == 'BUY_LAND' for o in market)
                    and money >= _SE_LAND_COST + settings['reserve'] + 1000 and room >= 4):
                extra.append(['BUY_LAND'])
                money -= _SE_LAND_COST
                st['buy_step'] = step
                buying = True

        commands = {}
        if st['active'] or buying:
            # Seeds for today's plantings, bought a turn ahead of use.
            want = {'WHEAT': 0, 'CARROT': 0}
            for xy in plan:
                crop = crop_of[xy]
                if day > settings['last_plant'][crop]:
                    continue
                tile = farm['tiles'][xy[1]][xy[0]]
                if tile is None or tile == 'LOCKED' or (isinstance(tile, dict) and tile.get('kind') == 'WEED'):
                    want[crop] += 1
                elif isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                    info = _SE_CROPS.get(tile.get('crop'))
                    if info and int(tile.get('planted_day', day)) + info['max_day'] <= day:
                        want[crop] += 1
            bought_now = {'WHEAT': 0, 'CARROT': 0}
            for crop in _SE_ITEMS:
                need = want[crop] - st['ledger'][crop]
                cost = need * _SE_SEED_COST[crop]
                if need > 0 and len(extra) < room and money >= cost + settings['reserve']:
                    extra.append(['BUY_SEED', crop, need])
                    money -= cost
                    st['ledger'][crop] += need
                    bought_now[crop] = need
                    rep['seeds'][crop] += need
                    rep['seed_cost'] += cost

            # Hands for the project, under the cost ceiling.
            busy = sum(1 for xy in plan if isinstance(farm['tiles'][xy[1]][xy[0]], dict))
            work = busy + sum(want.values())
            target = min(settings['max_workers'], -(-work // max(1, settings['tiles_per_worker'])))
            if (st['hire_req'] is None and len(mine) < target
                    and settings['first_hire_hour'] <= hour <= settings['last_hire_hour']):
                crew = max(st['parent_crew'], n_parent + parent_hires)
                hires_now = int(farm.get('hires_today', 0)) + parent_hires
                costs = []
                for j in range(target - len(mine)):
                    marginal = _se_fib(crew + len(mine) + j)
                    actual = _se_fib(hires_now + j)
                    if max(marginal, actual) > settings['max_hire_cost']:
                        rep['hire_skips_cost'] += 1
                        break
                    if len(extra) >= room or money < actual + settings['reserve']:
                        break
                    costs.append(actual)
                    money -= actual
                if costs:
                    extra += [['HIRE'] for _ in costs]
                    st['hire_req'] = {'step': step, 'base': len(hands), 'parent': parent_hires,
                                      'mine': len(costs), 'costs': costs}

            # The project's hands. Seeds usable this turn: our confirmed ledger,
            # and never more than the pool minus the parent's own plantings.
            if mine:
                parent_plants = {'WHEAT': 0, 'CARROT': 0}
                for c in [action.get('farmer')] + parent_hands:
                    if isinstance(c, list) and len(c) >= 2 and c[0] == 'PLANT' and c[1] in parent_plants:
                        parent_plants[c[1]] += 1
                pool = private.get('seeds') or {}
                seeds_left = {c: max(0, min(st['ledger'][c] - bought_now[c],
                                            int(pool.get(c, 0)) - parent_plants[c]))
                              for c in _SE_ITEMS}
                size = -(-len(plan) // len(mine))
                claimed = set()
                invs = private.get('inventories') or []
                for k, p in enumerate(mine):
                    if p >= len(hands):
                        continue
                    zone = plan[k * size:(k + 1) * size] + [t for t in plan if t not in plan[k * size:(k + 1) * size]]
                    command, xy = worker_command(obs, p, zone[:size], seeds_left, claimed)
                    if xy is not None:
                        claimed.add(xy)
                    if command[0] == 'PLANT':
                        seeds_left[command[1]] -= 1
                    st['last_cmds'][p] = {'cmd': command, 'tile': xy, 'night': False,
                                          'cargo': dict(invs[p + 1]) if p + 1 < len(invs) else {}}
                    commands[p] = command

        # Sell what the project's hands delivered.
        for item in _SE_ITEMS:
            n = st['unsold'][item]
            if n <= 0 or len(extra) >= room:
                continue
            if int(prices.get(item, 0)) >= settings['min_sell'][item] or step >= _SE_LAST_STEP - 12:
                extra.append(['SELL', item, n])
                rep['sold_units'] += n
                rep['sale_value'] += n * int(prices.get(item, 0))
                st['unsold'][item] = 0

        action['market'] = market + extra[:max(0, room)]

        # The parent's commands go to the parent's hands, in order.
        if mine:
            out, k = [], 0
            for i in range(len(hands)):
                if i in commands:
                    out.append(commands[i])
                elif i in mine:
                    out.append(['PASS'])
                else:
                    out.append(parent_hands[k] if k < len(parent_hands) else ['PASS'])
                    k += 1
            action['hands'] = out
        return action

    def fallback(obs, st, action):
        """If the project code fails, the parent's hands still get their commands."""
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

    def se_agent(observation, configuration=None):
        step = int(observation['step'])
        player = int(observation['player'])
        st = states.get(player)
        if st is None or step <= st['last_step']:
            st = _se_new_state()
            states[player] = st
            se_agent.telemetry = st['report']
        st['last_step'] = step
        try:
            reconcile(observation, st)
        except Exception:
            st['report']['errors'] += 1
        view = observation
        if st['active'] or st['mine']:
            view = masked(observation, st)
        action = parent(view, configuration)
        try:
            return after(observation, st, action)
        except Exception:
            st['report']['errors'] += 1
            return fallback(observation, st, action)

    se_agent.telemetry = _se_new_state()['report']
    se_agent.settings = settings
    return se_agent
# ---- END se_project ----
