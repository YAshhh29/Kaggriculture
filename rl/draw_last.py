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
# their slot), so they settle after the rider's buy and sale.
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


def dl_wrap(parent, pad=True, from_step=96, detect=True, min_events=2, min_excess=4):
    report = {'moved': 0, 'padded': 0, 'clean_steps': 0, 'rider_steps': 0,
              'rider_mode_step': None, 'errors': 0}
    states = {}

    def expected_cost(obs, market):
        """Cost of our orders if the rival trades no wheat this step, or None
        when an order's price depends on anything else."""
        farm = obs['farms'][int(obs['player'])]
        inv = int(obs['market']['inventory']['WHEAT'])
        hires = int(farm.get('hires_today', 0))
        shed = sum(int(v) for v in (obs['private'].get('shed') or {}).values())
        cost, units = 0.0, 0
        for o in market:
            if not (isinstance(o, list) and o):
                continue
            op = o[0]
            if op == 'HIRE':
                cost += _dl_fib(hires)
                hires += 1
                continue
            if len(o) < 3:
                return None
            n = int(o[2])
            if n <= 0:
                continue
            if op == 'BUY_SEED' and o[1] in _DL_SEED:
                cost += n * _DL_SEED[o[1]]
            elif op == 'BUY_PRODUCT' and o[1] == 'WHEAT':
                for _ in range(n):
                    cost += _dl_price(inv - 1)
                    inv -= 1
                units += n
            else:
                return None
        if cost > float(farm['money']) or shed + units > 80:
            return None                      # a fill could fail: not an exact step
        return cost, units

    def dl_agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            step = int(observation['step'])
            player = int(observation['player'])
            st = states.get(player)
            if st is None or step <= st['step']:
                st = states[player] = {'step': -1, 'prev': None, 'events': 0, 'rider': not detect}
            st['step'] = step
            farm = observation['farms'][player]
            inv = int(observation['market']['inventory']['WHEAT'])
            prev, st['prev'] = st['prev'], None
            if prev is not None and prev['step'] == step - 1 and step % 24 != 0:
                paid = prev['money'] - float(farm['money'])
                their_net = inv - prev['inv'] + prev['units'] + prev['draw']   # their net sold
                report['clean_steps'] += 1
                if paid - prev['cost'] >= min_excess and abs(their_net) <= 2:
                    st['events'] += 1
                    report['rider_steps'] += 1
                    if st['events'] >= min_events and not st['rider']:
                        st['rider'] = True
                        report['rider_mode_step'] = step
            if not isinstance(action, dict) or step < from_step or step % 4 != 0:
                return action
            market = list(action.get('market') or [])
            buys = [o for o in market if isinstance(o, list) and len(o) >= 3
                    and o[0] == 'BUY_PRODUCT' and o[1] == 'WHEAT' and int(o[2]) > 0]
            if not buys:
                return action
            if detect and not st['rider']:
                exp = expected_cost(observation, market)
                if exp is not None:
                    st['prev'] = {'step': step, 'money': float(farm['money']), 'cost': exp[0],
                                  'units': exp[1], 'inv': inv,
                                  'draw': _dl_draw(observation['town']['unlocked_shops'], step)}
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
