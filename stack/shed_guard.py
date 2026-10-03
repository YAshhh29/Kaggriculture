# ---- BEGIN shed_guard (Agent N10's own layer) ----
# Keep the day-end drop from destroying goods.
#
# Why: at the end of every day the engine drops every worker's inventory into
# the shed up to its capacity (100) and DISCARDS the rest
# (kaggriculture._drop_inventories_to_shed). Our agents lose goods this way in
# ~90% of ladder games -- ~400 coins a game, mostly on days 23-28 when the shed
# holds stock waiting for timed sales; in 26 of 414 real games the destroyed
# value alone exceeded the losing margin. The parent's own room_guard is
# switched off (and, switched on, catches about half: it runs before our outer
# layers and can find no free order slot).
#
# How: on the last step of a day, project the shed after the drop -- stock now,
# plus what every worker carries, plus this step's harvests and fertilizer
# collections, minus what the workers use (feed, fertilize, place), minus the
# SELLs that will fill, plus purchases. If it exceeds capacity, sell the excess
# now, cheapest goods first (a unit of wheat sold frees the same room as a
# strawberry, at a fraction of the value and the price impact), never below a
# small reserve of feed and fertilizer. The extra units are merged into an
# existing SELL of the same good when possible, else added in a free slot, else
# they replace a zero-quantity padding order. Any error returns the action as is.

_SG_CAP = 100
_SG_RESERVE = {'WHEAT': 10, 'CARROT': 4, 'FERTILIZER': 2}
_SG_ANIMAL_PRODUCT = {'GOOSE': 'EGG', 'COW': 'MILK', 'SHEEP': 'WOOL'}


def _sg_projected(observation, action, capacity=_SG_CAP):
    """Units in the shed after this step's market and the day-end drop, and the
    shed stock available to sell (after the SELLs already queued)."""
    player = int(observation['player'])
    farm = observation['farms'][player]
    private = observation['private']
    shed = dict(private.get('shed') or {})
    invs = private.get('inventories') or []
    carried = sum(max(0, int(v)) for inv in invs for v in (inv or {}).values())
    positions = [farm['farmer']] + list(farm.get('hands') or [])
    commands = [action.get('farmer')] + list(action.get('hands') or [])
    produced = consumed = 0
    for i, c in enumerate(commands):
        if not (isinstance(c, list) and c) or i >= len(positions):
            continue
        x, y = int(positions[i][0]), int(positions[i][1])
        tile = farm['tiles'][y][x]
        op = c[0]
        if op == 'HARVEST' and isinstance(tile, dict):
            produced += max(0, int(tile.get('yield_units') or 0))
        elif op == 'COLLECT_FERTILIZER' and isinstance(tile, dict) and tile.get('fertilizer_available'):
            produced += 1
        elif op in ('FEED', 'FERTILIZE'):
            consumed += 1
        elif op == 'PLACE' and len(c) >= 2:
            if c[1] in _SG_ANIMAL_PRODUCT:
                consumed += 1
    # Sellable this step: the shed plus what the workers put into it this step
    # (units act before the market). At a day's last step the shed is often
    # nearly empty while the crew carries 60-90 units still being delivered.
    stock = dict(shed)
    room = capacity - sum(shed.values())
    for i, c in enumerate(commands):
        if not (isinstance(c, list) and c) or i >= len(invs):
            continue
        inv = invs[i] or {}
        if c[0] == 'DROP':
            for k, v in inv.items():
                take = min(max(0, int(v)), max(0, room))
                if take > 0:
                    stock[k] = stock.get(k, 0) + take
                    room -= take
        elif c[0] == 'PLACE' and len(c) >= 2 and c[1] not in _SG_ANIMAL_PRODUCT:
            take = min(max(0, int(inv.get(c[1], 0))), int(c[2]) if len(c) >= 3 else 1, max(0, room))
            if take > 0:
                stock[c[1]] = stock.get(c[1], 0) + take
                room -= take
    sold = 0
    bought = 0
    for o in action.get('market') or []:
        if not (isinstance(o, list) and len(o) >= 3):
            continue
        try:
            n = int(o[2])
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        if o[0] == 'SELL':
            take = min(n, stock.get(o[1], 0))
            stock[o[1]] = stock.get(o[1], 0) - take
            sold += take
        elif o[0] == 'BUY_PRODUCT':
            bought += n
    total = sum(shed.values()) + carried + produced - consumed - sold + bought
    return total, stock


def sg_wrap(parent, capacity=_SG_CAP, reserve=None, margin=1):
    reserve = dict(_SG_RESERVE if reserve is None else reserve)
    report = {'guard_steps': 0, 'units_sold': 0, 'no_slot': 0, 'errors': 0}

    def sg_agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            step = int(observation['step'])
            if step % 24 != 23 or step >= 719 or not isinstance(action, dict):
                return action
            total, stock = _sg_projected(observation, action, capacity)
            excess = total - capacity + margin
            if excess <= 0:
                return action
            prices = observation['market'].get('prices') or {}
            market = [list(o) if isinstance(o, list) else o for o in (action.get('market') or [])]
            # First cut this step's purchases: bought goods land in the shed
            # before the drop and push the crew's own harvest out (day 23 of
            # 115238015: 27 units bought at hour 23, 26 carried units destroyed).
            buys = sorted((o for o in market if isinstance(o, list) and len(o) >= 3
                           and o[0] == 'BUY_PRODUCT' and int(o[2] or 0) > 0),
                          key=lambda o: -int(o[2]))
            for o in buys:
                if excess <= 0:
                    break
                cut = min(int(o[2]), excess)
                o[2] = int(o[2]) - cut
                excess -= cut
                report['buys_cut'] = report.get('buys_cut', 0) + cut
            order = sorted((k for k, v in stock.items() if v - reserve.get(k, 0) > 0),
                           key=lambda k: (float(prices.get(k, 0) or 0), k))
            for item in order:
                if excess <= 0:
                    break
                qty = min(excess, stock[item] - reserve.get(item, 0))
                if qty <= 0:
                    continue
                placed = False
                for o in market:
                    if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL' and o[1] == item:
                        o[2] = int(o[2]) + qty
                        placed = True
                        break
                if not placed:
                    if len(market) < 10:
                        market.append(['SELL', item, qty])
                        placed = True
                    else:
                        for j, o in enumerate(market):
                            if isinstance(o, list) and len(o) >= 3 and int(o[2] or 0) == 0:
                                market[j] = ['SELL', item, qty]
                                placed = True
                                break
                if not placed:
                    report['no_slot'] += 1
                    continue
                excess -= qty
                report['units_sold'] += qty
            report['guard_steps'] += 1
            action = dict(action, market=market)
        except Exception:
            report['errors'] += 1
        return action

    sg_agent.telemetry = report
    return sg_agent
# ---- END shed_guard ----
