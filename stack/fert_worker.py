# ---- BEGIN fert_worker (Agent L's own layer) ----
# A hired hand that fertilizes young wheat.
#
# Wheat gains 1 unit per watering on days 2-4 after planting, 2 if the tile is
# fertilized that day, so fertilizer on a 1-day-old plant turns a 3-4 unit
# harvest into 5-6. As in se_project, the hand and the fertilizer it buys are
# invisible to the parent. The hand is hired after the parent's own hires,
# under a cost ceiling, and only while there is young wheat to treat.

_FW_HOME = ((4, 4), (5, 4), (4, 5), (5, 5))
_FW_DEFAULTS = {
    'max_hire_cost': 150,      # one hand-day; the 12th hire of a day costs 144
    'first_hire_hour': 2,      # the parent hires at hours 0-1
    'last_hire_hour': 6,
    'first_day': 3, 'last_day': 26,
    'min_targets': 4,          # don't hire for fewer tiles than this
    'max_price': 60,           # don't buy fertilizer above this
    'reserve': 3000,
}


def _fw_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _fw_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _fw_toward(pos, target):
    if pos[0] != target[0]:
        return ['EAST' if pos[0] < target[0] else 'WEST']
    if pos[1] != target[1]:
        return ['SOUTH' if pos[1] < target[1] else 'NORTH']
    return None


def fw_wrap(parent, **overrides):
    settings = dict(_FW_DEFAULTS)
    settings.update(overrides)
    states = {}
    report = {'hires': 0, 'hire_cost': 0, 'bought': 0, 'buy_cost': 0,
              'fertilized': 0, 'errors': 0}

    def targets(obs, day, hour, own):
        farm = obs['farms'][int(obs['player'])]
        out = []
        for y, row in enumerate(farm['tiles']):
            for x, t in enumerate(row):
                if not (isinstance(t, dict) and t.get('kind') == 'PLANT'
                        and t.get('crop') == 'WHEAT'):
                    continue
                if int(t.get('fertilized_until_day', -1)) >= day:
                    continue
                age = day - int(t.get('planted_day', day))
                if age == 1 or (age == 2 and not t.get('watered_today')):
                    out.append((x, y))
        return out

    def new_state():
        return {'last_step': -1, 'day': -1, 'mine': [], 'req': None,
                'ledger': 0, 'buy_step': None}

    def se_view(obs, st):
        mine = set(st['mine'])
        player = int(obs['player'])
        farm = obs['farms'][player]
        hands = farm.get('hands') or []
        farm2 = dict(farm)
        farm2['hands'] = [h for i, h in enumerate(hands) if i not in mine]
        farm2['hires_today'] = max(0, int(farm.get('hires_today', 0)) - len(mine))
        farms2 = list(obs['farms'])
        farms2[player] = farm2
        private = obs['private']
        invs = private.get('inventories') or [{}]
        private2 = dict(private)
        private2['inventories'] = [invs[0]] + [invs[i + 1] for i in range(len(hands))
                                               if i not in mine and i + 1 < len(invs)]
        shed2 = dict(private.get('shed') or {})
        ours_in_shed = max(0, st['ledger'] - st.get('carried', 0))
        shed2['FERTILIZER'] = max(0, int(shed2.get('FERTILIZER', 0)) - ours_in_shed)
        private2['shed'] = shed2
        obs2 = dict(obs)
        obs2['farms'] = farms2
        obs2['private'] = private2
        return obs2

    def reconcile(obs, st):
        step = int(obs['step'])
        day = step // 24
        farm = obs['farms'][int(obs['player'])]
        private = obs['private']
        invs = private.get('inventories') or []
        if day != st['day']:
            # Night: the hand is dismissed, its leftover fertilizer drops into
            # the shed and stays ours.
            st['mine'], st['req'], st['day'] = [], None, day
        req = st['req']
        if req is not None:
            if req['step'] == step - 1:
                hands = farm.get('hands') or []
                new = len(hands) - req['base']
                parent_new = min(max(new, 0), req['parent'])
                if new - parent_new >= 1:
                    st['mine'] = [req['base'] + parent_new]
                    report['hires'] += 1
                    report['hire_cost'] += req['cost']
            st['req'] = None
        # Our fertilizer is what sits in the shed for us plus what our hand carries.
        carried = sum(int((invs[p + 1] or {}).get('FERTILIZER', 0))
                      for p in st['mine'] if p + 1 < len(invs))
        shed = int((private.get('shed') or {}).get('FERTILIZER', 0))
        st['ledger'] = max(0, min(st['ledger'], shed + carried))
        st['carried'] = carried

    def after(obs, st, action):
        step = int(obs['step'])
        day = step // 24
        hour = step % 24
        farm = obs['farms'][int(obs['player'])]
        private = obs['private']
        prices = obs['market']['prices']
        action = dict(action) if isinstance(action, dict) else {}
        market = [o for o in (action.get('market') or [])]
        while market and not market[-1]:
            market.pop()
        parent_hands = list(action.get('hands') or [])
        hands = farm.get('hands') or []
        mine = st['mine']
        room = 10 - len(market)
        extra = []
        todo = targets(obs, day, hour, st) if settings['first_day'] <= day <= settings['last_day'] else []

        # Buy our own fertilizer a turn ahead of use (it lands in the shed).
        have = st['ledger']
        need = len(todo) - have
        price = int(prices.get('FERTILIZER', 100))
        shed_total = sum(int(v) for v in (private.get('shed') or {}).values())
        if (need > 0 and room > len(extra) and price <= settings['max_price']
                and float(farm['money']) > settings['reserve'] + need * (price + 5)
                and shed_total + need <= 90 and hour <= 20):
            extra.append(['BUY_PRODUCT', 'FERTILIZER', need])
            st['ledger'] += need
            report['bought'] += need
            report['buy_cost'] += need * price

        # Hire one hand when there is enough young wheat to treat.
        if (not mine and st['req'] is None and len(todo) >= settings['min_targets']
                and settings['first_hire_hour'] <= hour <= settings['last_hire_hour']
                and room > len(extra)):
            parent_hires = sum(1 for o in market if isinstance(o, list) and o and o[0] == 'HIRE')
            n_now = int(farm.get('hires_today', 0)) + parent_hires
            cost = _fw_fib(n_now)
            if cost <= settings['max_hire_cost'] and float(farm['money']) > settings['reserve'] + cost:
                extra.append(['HIRE'])
                st['req'] = {'step': step, 'base': len(hands), 'parent': parent_hires, 'cost': cost}

        # The hand: collect fertilizer at the shed, then treat the nearest target.
        commands = {}
        for p in mine:
            if p >= len(hands):
                continue
            pos = tuple(hands[p])
            invs = private.get('inventories') or []
            carry = int((invs[p + 1] or {}).get('FERTILIZER', 0)) if p + 1 < len(invs) else 0
            shed_ours = min(st['ledger'] - carry,
                            int((private.get('shed') or {}).get('FERTILIZER', 0)))
            cmd = ['PASS']
            if carry == 0 and shed_ours > 0 and todo:
                home = min(_FW_HOME, key=lambda h: _fw_dist(pos, h))
                cmd = _fw_toward(pos, home) or ['PICKUP', 'FERTILIZER', int(min(shed_ours, len(todo)))]
            elif carry > 0 and todo:
                tgt = min(todo, key=lambda t: (_fw_dist(pos, t), t))
                cmd = _fw_toward(pos, tgt)
                if cmd is None:
                    cmd = ['FERTILIZE']
                    report['fertilized'] += 1
                    st['ledger'] -= 1
            commands[p] = cmd

        action['market'] = market + extra[:max(0, room)]
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

    def fert_agent(observation, configuration=None):
        step = int(observation['step'])
        player = int(observation['player'])
        st = states.get(player)
        if st is None or step <= st['last_step']:
            st = new_state()
            states[player] = st
        st['last_step'] = step
        try:
            reconcile(observation, st)
        except Exception:
            report['errors'] += 1
        view = se_view(observation, st) if (st['mine'] or st['ledger']) else observation
        action = parent(view, configuration)
        try:
            return after(observation, st, action)
        except Exception:
            report['errors'] += 1
            if st['mine'] and isinstance(action, dict):
                hands = observation['farms'][player].get('hands') or []
                ph = list(action.get('hands') or [])
                out, k = [], 0
                for i in range(len(hands)):
                    if i in st['mine']:
                        out.append(['PASS'])
                    else:
                        out.append(ph[k] if k < len(ph) else ['PASS'])
                        k += 1
                return dict(action, hands=out)
            return action

    fert_agent.telemetry = report
    return fert_agent
# ---- END fert_worker ----
