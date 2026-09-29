# ---- BEGIN draw_last (Agent N4's own layer) ----
# Settle our draw-step wheat purchases last -- only against a rival that rides them.
#
# Why: the town removes wheat after the market of every step % 4 == 0, so the
# lineage (and our round trip) buys wheat at that step and sells it at the
# next; market_front sorts the big purchase into slot 0. Some private forks
# ride it: at the draw step they queue BUY_PRODUCT WHEAT k in slot 0 and
# SELL WHEAT k in slot 1. The engine settles slot 0 unit by unit for both
# players, so their k units ride up the curve with ours and their slot-1 sale
# lands at the top of the curve our purchase built (RngRng, 2407, live 9-28:
# +13.5k on wheat to our +6.6k with identical farms; alone that round trip
# nets zero). Settling last in every game lost: most rivals run an honest
# round trip in slot 0, and going after it pays the top of their curve.
#
# Detection (exact, public data only): at a draw step whose priced orders are
# only wheat purchases, seeds and hires, the engine's own price table gives
# what those orders cost if the rival trades no wheat in that step. At the next
# step our money shows what they did cost, and the wheat inventory gives the
# rival's net wheat trade in the step. A rider pays nothing net (bought k, sold
# k) yet makes our purchase dearer; an honest trader shows a net purchase, and
# a rival that stays out leaves our cost exact. After `min_events` rider steps
# our draw-step wheat purchases go to the end of the queue, with the free slots
# before them filled with zero-quantity orders (they parse to nothing but keep
# their slot), so they settle after the rider's buy and sale. Some riders sell
# in slot 9 themselves (Sho Saga): then our last-slot purchase pairs with their
# sale unit by unit at the top of their curve, and the same reconciliation
# shows it; after `min_events` such steps the draw-step wheat purchases are
# dropped instead (skip mode) and the next step's wheat sale is cut to match,
# so the ride has nothing to ride. If instead the rival buys wheat outright at
# the draw and our last-slot purchase still overpays, it is an honest same-step
# round trip settling ahead of ours (RngRng's 9-29 version): after `min_events`
# such steps the layer plays normally again for the rest of the game.
#
# A rider of k units raises our 60-unit purchase by about 0.03 x (k^2/2 + k(60-k))
# coins (~46 at k = 40); a rival buying 2-3 wheat for feed in the same step adds
# ~5, so a step counts only from `min_excess` = 12 coins (N3's live games: two
# false alarms at 4, Victor's Team and Les 2 oies).
#
# Trip governor (N7): a round trip is worth doing only while it pays. With
# `governor`, the realized margin of each trip is read exactly -- the purchase
# from the draw step's money (as above), the sale from the next step's money
# when every other order is fixed-price and the sale is the trip alone -- and
# when the last `gov_window` trips average under `gov_margin` coins a unit the
# draw-step purchases are dropped for `gov_pause` steps (as in skip mode), then
# tried again. It needs no model of the rival: in N7's close mirror losses the
# trips earned nothing (bought and sold at 41.92) while the rival traded
# around them.
#
# Outermost (just inside the safety guard), so no layer appends after it. The
# opening (before step 96) is left alone. Any error returns the action as is.

import math as _dl_math

_DL_MAX_ORDERS = 10
_DL_I0 = 10000
_DL_SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
_DL_WHEAT_SHOPS = ('BAKERY', 'PIZZA_SHOP', 'BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'FARMERS_MARKET')
# engine MARKET_PARAMS for wheat: base 25, T 400, below sqrt 0.80, above log 0.20
_DL_WHEAT = (25, 400, 0.80, 0.20)


def _dl_price(inventory):
    base, T, bt, at = _DL_WHEAT
    if inventory < _DL_I0:
        price = base + bt * base / _dl_math.sqrt(T) * _dl_math.sqrt(_DL_I0 - inventory)
    else:
        price = base - at * base / _dl_math.log(1.0 + T) * _dl_math.log(1.0 + inventory - _DL_I0)
    return max(1, int(round(price)))


def _dl_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _dl_draw(shops, step):
    if step % 4:
        return 0
    return sum(1 for s in shops if s in _DL_WHEAT_SHOPS) + (1 if step % 24 == 0 else 0)


def _dl_cut_sale(action, n):
    """Reduce the queue's wheat sales by n units (largest first)."""
    market = [list(o) if isinstance(o, list) else o for o in action.get('market') or []]
    for o in sorted([o for o in market if isinstance(o, list) and len(o) >= 3
                     and o[0] == 'SELL' and o[1] == 'WHEAT'], key=lambda o: -int(o[2])):
        take = min(n, int(o[2]))
        o[2] = int(o[2]) - take
        n -= take
        if n <= 0:
            break
    return dict(action, market=market)


def _dl_wheat_stock(obs, action):
    """Wheat the shed will hold when this step's market runs (units act first)."""
    stock = int((obs['private'].get('shed') or {}).get('WHEAT', 0))
    invs = obs['private'].get('inventories') or []
    for i, c in enumerate([action.get('farmer')] + list(action.get('hands') or [])):
        if not (isinstance(c, list) and c) or i >= len(invs):
            continue
        carried = int((invs[i] or {}).get('WHEAT', 0))
        if c[0] == 'DROP':
            stock += carried
        elif c[0] == 'PLACE' and len(c) >= 2 and c[1] == 'WHEAT':
            stock += min(carried, int(c[2]) if len(c) >= 3 else 1)
        elif c[0] == 'PICKUP' and len(c) >= 2 and c[1] == 'WHEAT':
            stock -= int(c[2]) if len(c) >= 3 else 1
    return max(0, stock)


def _dl_sale_record(obs, action, trip):
    """The step after a trip's purchase: what our wheat sale fetches can be read
    from our money next step when every other order is fixed-price and the sale
    is the trip alone (no farm wheat mixed in)."""
    farm = obs['farms'][int(obs['player'])]
    hires = int(farm.get('hires_today', 0))
    fixed, sells = 0.0, 0
    for o in action.get('market') or []:
        if not (isinstance(o, list) and o):
            continue
        if o[0] == 'HIRE':
            fixed += _dl_fib(hires)
            hires += 1
            continue
        if len(o) < 3:
            return None
        n = int(o[2])
        if n <= 0:
            continue
        if o[0] == 'BUY_SEED' and o[1] in _DL_SEED:
            fixed += n * _DL_SEED[o[1]]
        elif o[0] == 'SELL' and o[1] == 'WHEAT':
            sells += n
        else:
            return None
    units = min(sells, _dl_wheat_stock(obs, action))
    if units <= 0 or sells > trip['units'] + 5:
        return None
    return {'step': int(obs['step']), 'money': float(farm['money']), 'fixed': fixed,
            'units': units, 'avg_buy': trip['avg_buy']}


def _dl_lock_cost(inventory, q, k):
    """Cost of our q-unit purchase settled unit by unit with a rival buying k in
    the same slot."""
    cost = 0.0
    for j in range(1, q + 1):
        before = inventory - 2 * (j - 1) if j <= k else inventory - k - (j - 1)
        cost += _dl_price(before - 1)
    return cost


def _dl_implied_sale(prev, paid, their_net):
    """Units the rival sold within the step, implied by what our purchase cost.

    Our q units cost more than alone only if the rival bought alongside them:
    the smallest k whose lockstep cost reaches what we paid is its purchase in
    our slot; less its net purchase for the step (-their_net) is what it sold
    again in the same step (a rider buying 75 and selling 60 nets -15)."""
    q = int(prev.get('units') or 0)
    if q <= 0:
        return 0
    paid_wheat = paid - float(prev.get('fixed') or 0.0)
    inv = int(prev['inv'])
    # A rival buying more than our q interleaves with all of our units and costs
    # us no more than one buying exactly q (Otter Vibe's honest 70-unit trips
    # next to our 40 read as a 150-unit purchase before this cap). A cost above
    # full interleaving is not explained by a purchase in our slot: no inference.
    if paid_wheat > _dl_lock_cost(inv, q, q) + 1:
        return 0
    k = 0
    while k < q and _dl_lock_cost(inv, q, k) < paid_wheat - 0.5:
        k += 1
    return k + their_net


def dl_wrap(parent, pad=True, from_step=96, detect=True, min_events=2, min_excess=12, skip=True,
            implied=False, implied_min=20, governor=False, gov_window=6, gov_min_trips=4,
            gov_margin=0.3, gov_pause=48):
    report = {'moved': 0, 'padded': 0, 'clean_steps': 0, 'rider_steps': 0,
              'rider_mode_step': None, 'skip_mode_step': None, 'reverted_step': None, 'skipped_units': 0,
              'cut_units': 0, 'errors': 0}
    states = {}

    def expected_cost(obs, market):
        """Cost of our orders if the rival trades no wheat this step, or None
        when an order's price depends on anything else."""
        farm = obs['farms'][int(obs['player'])]
        inv = int(obs['market']['inventory']['WHEAT'])
        hires = int(farm.get('hires_today', 0))
        shed = sum(int(v) for v in (obs['private'].get('shed') or {}).values())
        cost, units, fixed = 0.0, 0, 0.0
        for o in market:
            if not (isinstance(o, list) and o):
                continue
            op = o[0]
            if op == 'HIRE':
                cost += _dl_fib(hires)
                fixed += _dl_fib(hires)
                hires += 1
                continue
            if len(o) < 3:
                return None
            n = int(o[2])
            if n <= 0:
                continue
            if op == 'BUY_SEED' and o[1] in _DL_SEED:
                cost += n * _DL_SEED[o[1]]
                fixed += n * _DL_SEED[o[1]]
            elif op == 'BUY_PRODUCT' and o[1] == 'WHEAT':
                for _ in range(n):
                    cost += _dl_price(inv - 1)
                    inv -= 1
                units += n
            else:
                return None
        if cost > float(farm['money']) or shed + units > 100:
            return None                      # a fill could fail: not an exact step
        return cost, units, fixed

    def dl_agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            step = int(observation['step'])
            player = int(observation['player'])
            st = states.get(player)
            if st is None or step <= st['step']:
                st = states[player] = {'step': -1, 'prev': None, 'events': 0, 'rider': not detect,
                                       'last_bad': 0, 'skip': False, 'owe': None, 'honest': 0,
                                       'trip': None, 'sale': None, 'margins': [], 'pause_until': -1}
            st['step'] = step
            farm = observation['farms'][player]
            inv = int(observation['market']['inventory']['WHEAT'])
            prev, st['prev'] = st['prev'], None
            if prev is not None and prev['step'] == step - 1 and step % 24 != 0:
                paid = prev['money'] - float(farm['money'])
                their_net = inv - prev['inv'] + prev['units'] + prev['draw']   # their net sold
                report['clean_steps'] += 1
                if governor and prev['units'] >= 10:
                    st['trip'] = {'step': prev['step'], 'units': prev['units'],
                                  'avg_buy': (paid - prev['fixed']) / prev['units']}
                if (st['rider'] and not st['skip'] and paid - prev['cost'] >= min_excess and their_net < -2
                        and st.get('kind') != 'implied'):
                    # still overpaying in the last slot while the rival buys: an honest
                    # same-step round trip settles before ours (RngRng's 9-29 version);
                    # the last slot pays the top of its curve, so play normally again
                    st['honest'] += 1
                    if st['honest'] >= min_events:
                        st['rider'] = False
                        st['events'] = -10 ** 9
                        report['reverted_step'] = step
                elif paid - prev['cost'] >= min_excess and (
                        abs(their_net) <= 2 or (st['rider'] and st.get('kind') == 'implied')
                        or (implied and _dl_implied_sale(prev, paid, their_net) >= implied_min)):
                    if st['rider']:
                        st['last_bad'] += 1
                        if st['last_bad'] >= min_events and not st['skip'] and skip:
                            st['skip'] = True
                            report['skip_mode_step'] = step
                    else:
                        st['events'] += 1
                        report['rider_steps'] += 1
                        if abs(their_net) > 2:
                            st['implied_events'] = st.get('implied_events', 0) + 1
                        if st['events'] >= min_events:
                            st['rider'] = True
                            # a rider seen buying more than it resells (Rio) keeps a net
                            # purchase ahead of our last-slot buy: overpaying there means
                            # skip, not a return to normal play
                            st['kind'] = 'implied' if st.get('implied_events', 0) else 'net0'
                            report['rider_mode_step'] = step
                            report['rider_kind'] = st['kind']
            sale, st['sale'] = st['sale'], None
            if governor and sale is not None and sale['step'] == step - 1:
                revenue = float(farm['money']) - sale['money'] + sale['fixed']
                margin = revenue / sale['units'] - sale['avg_buy']
                st['margins'] = (st['margins'] + [margin])[-gov_window:]
                report['gov_trips'] = report.get('gov_trips', 0) + 1
                if (len(st['margins']) >= gov_min_trips
                        and sum(st['margins']) / len(st['margins']) < gov_margin):
                    st['pause_until'] = step + gov_pause
                    st['margins'] = []
                    report['gov_pauses'] = report.get('gov_pauses', 0) + 1
            owe, st['owe'] = st['owe'], None
            if owe and owe[0] == step and isinstance(action, dict):
                action = _dl_cut_sale(action, owe[1])
                report['cut_units'] += owe[1]
            trip = st['trip']
            if governor and trip is not None and trip['step'] == step - 1 and isinstance(action, dict):
                st['trip'] = None
                rec = _dl_sale_record(observation, action, trip)
                if rec is not None:
                    st['sale'] = rec
            if not isinstance(action, dict) or step < from_step or step % 4 != 0:
                return action
            market = list(action.get('market') or [])
            buys = [o for o in market if isinstance(o, list) and len(o) >= 3
                    and o[0] == 'BUY_PRODUCT' and o[1] == 'WHEAT' and int(o[2]) > 0]
            if not buys:
                return action
            if st['skip'] or step < st['pause_until']:
                if not st['skip']:
                    report['gov_paused_steps'] = report.get('gov_paused_steps', 0) + 1
                kept = [o for o in market if not (isinstance(o, list) and len(o) >= 3 and o[0] == 'BUY_PRODUCT'
                                                   and o[1] == 'WHEAT' and int(o[2]) >= 10)]
                cut = sum(int(o[2]) for o in market if o not in kept and isinstance(o, list))
                if cut:
                    st['owe'] = (step + 1, cut)
                    report['skipped_units'] += cut
                    action = dict(action, market=kept)
                return action
            if detect:
                exp = expected_cost(observation, [o for o in market if not (isinstance(o, list) and len(o) >= 3
                                                                            and int(o[2]) == 0)])
                if exp is not None:
                    st['prev'] = {'step': step, 'money': float(farm['money']), 'cost': exp[0],
                                  'units': exp[1], 'inv': inv, 'fixed': exp[2],
                                  'draw': _dl_draw(observation['town']['unlocked_shops'], step)}
                if not st['rider']:
                    return action
            rest = [o for o in market if not any(o is b for b in buys)]
            if pad:
                free = _DL_MAX_ORDERS - len(rest) - len(buys)
                if free > 0:
                    rest = rest + [['BUY_PRODUCT', 'WHEAT', 0] for _ in range(free)]
                    report['padded'] += 1
            new = rest + buys
            if new != market:
                report['moved'] += 1
                action = dict(action, market=new)
        except Exception:
            report['errors'] += 1
        return action

    dl_agent.telemetry = report
    return dl_agent
# ---- END draw_last ----
