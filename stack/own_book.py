# ---- BEGIN own_book (Agent N11's own layer) ----
# Tell the parent what we really sold.
#
# Why: every turn the parent recovers the rival's sales from the public market
# (inventory change + town draw - OUR sales) and feeds them to its sale races:
# RACE (lead -> reservation horizon), PREDICT (matches the rival against
# recorded sale streams and sells our planned milk, wool and strawberry lots up
# to 48 turns early), ORDERPRI2 (rival stock), MODELPX (rival flow -> lead
# sales) and the clone race (EXP293 escalation). "Our sales" are recorded from
# the action the parent returns. The parent's own later layers keep that record
# current -- each one rewrites _RACE_STATE[player]['prev_action'] -- but our
# outer layers (shadow early sales, m_sell races, the tomato annex, the shed
# guard) do not: every unit they sell is booked as a rival sale, and every
# parent sale they cancel hides a real one.
#
# How: record the SELLs of the parent's own action (innermost), and after the
# whole stack has decided, correct each tracker's record for this step by what
# the final action sells instead, and hand the clone race the final action.
# Only the seven raced goods: wheat is left alone, because our wheat round trip
# also buys, and booking its sales without its purchases would skew the record.
# Any error leaves the action (and the records) as they are.

_OB_ITEMS = ('CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL')
_OB_TRACKERS = {'_V9_RACE': 'V9_RACE_ITEMS', '_OR2_STATE': '_OR2_ITEMS',
                '_S758_HIST': '_S758_ITEMS', '_S804_HIST': '_S758_ITEMS'}
_OB_CAPPED = ('_V9_RACE', '_OR2_STATE')      # these cap a sale by the stock on hand


def _ob_sells(action):
    out = {}
    for o in list((action or {}).get('market') or [])[:10]:
        if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == 'SELL' and o[1] in _OB_ITEMS:
            try:
                n = int(o[2])
            except (TypeError, ValueError):
                continue
            if n > 0:
                out[o[1]] = out.get(o[1], 0) + n
    return out


def ob_record(entry):
    """Innermost: remember what the parent's own action sells this step."""
    seen = {}

    def ob_rec(observation, configuration=None):
        action = entry(observation, configuration)
        try:
            seen[int(observation['player'])] = (int(observation['step']), _ob_sells(action))
        except Exception:
            seen.clear()
        return action

    ob_rec.seen = seen
    ob_rec.telemetry = getattr(entry, 'telemetry', {})
    return ob_rec


def ob_wrap(parent, env, recorder, race_final=False):
    """Outermost (inside safety): correct the parent's records of our sales.
    race_final: rebuild the race/PREDICT snapshot (_V9_RACE) wholly from the
    final action every turn, as V53 does -- which also books the parent's own
    later lead sales (MODELPX, above RACE in its chain) as ours."""
    report = {'book_steps': 0, 'book_units': 0, 'book_clone': 0, 'book_errors': 0}

    def ob_agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            player, step = int(observation['player']), int(observation['step'])
            rec = recorder.seen.get(player)
            if rec is None or rec[0] != step or not isinstance(action, dict):
                return action
            rs = (env.get('_RACE_STATE') or {}).get(player)
            if (isinstance(rs, dict) and rs.get('prev_action') is not None and rs.get('step') == step
                    and _ob_sells(rs['prev_action']) != _ob_sells(action)):
                rs['prev_action'] = action
                report['book_clone'] += 1
            final, base = _ob_sells(action), rec[1]
            diff = {k: final.get(k, 0) - base.get(k, 0) for k in set(final) | set(base)}
            diff = {k: v for k, v in diff.items() if v}
            stock = None
            changed = 0
            if race_final:
                st = (env.get('_V9_RACE') or {}).get(player)
                prev = st.get('prev') if isinstance(st, dict) else None
                items = tuple(env.get('V9_RACE_ITEMS') or ())
                if isinstance(prev, dict) and prev.get('step') == step and isinstance(prev.get('own'), dict):
                    stock = env['projected_shed'](action, env['FarmView'](observation))
                    own = {}
                    for o in list(action.get('market') or [])[:10]:
                        if isinstance(o, (list, tuple)) and len(o) >= 3 and o[0] == 'SELL' and o[1] in items:
                            n = min(max(0, int(o[2])), max(0, int(stock.get(o[1], 0)) - own.get(o[1], 0)))
                            own[o[1]] = own.get(o[1], 0) + n
                    moved = sum(abs(own.get(k, 0) - int(prev['own'].get(k, 0))) for k in items)
                    if moved:
                        prev['own'] = own
                        prev['left'] = {k: int(stock.get(k, 0)) - own.get(k, 0) for k in items}
                        changed += moved
            for name, items_name in (_OB_TRACKERS.items() if diff else ()):
                if race_final and name == '_V9_RACE':
                    continue
                items = set(env.get(items_name) or ())
                st = (env.get(name) or {}).get(player)
                prev = st.get('prev') if isinstance(st, dict) else None
                if not isinstance(prev, dict) or prev.get('step') != step or not isinstance(prev.get('own'), dict):
                    continue
                own = prev['own']
                left = prev.get('left') if isinstance(prev.get('left'), dict) else None
                for item, delta in diff.items():
                    if item not in items:
                        continue
                    old = int(own.get(item, 0))
                    if name in _OB_CAPPED:
                        if stock is None:
                            stock = env['projected_shed'](action, env['FarmView'](observation))
                        new = min(final.get(item, 0), max(0, int(stock.get(item, 0))))
                    else:
                        new = max(0, old + delta)
                    if new == old:
                        continue
                    own[item] = new
                    if left is not None and item in left:
                        left[item] = left[item] - (new - old)
                    changed += abs(new - old)
            if changed:
                report['book_steps'] += 1
                report['book_units'] += changed
        except Exception:
            report['book_errors'] += 1
        return action

    ob_agent.telemetry = report
    return ob_agent
# ---- END own_book ----
