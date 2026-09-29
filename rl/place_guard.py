# ---- BEGIN place_guard (Agent N7's own layer) ----
# Build the missing pasture or coop under an animal the plan is placing.
#
# Why: the plan's weed repair digs a weed out of a tile its tape meant to
# build on and queues the build, but drops the queue when the hand's next tape
# step is a move. The pasture is never built; the animal bought for it later is
# PLACEd on an empty tile, which the engine ignores, and the farm is one animal
# short all game (Tagir Eminov and mikelou1, both on tile (4, 2): one cow,
# -6.9k and -11.8k).
#
# How: a PLACE of an animal on an empty owned tile that is not beside the shed
# can never succeed. Replace it with BUILD_PASTURE (cow, sheep) or BUILD_COOP
# (goose), and on the next step PLACE the animal if the hand still stands on
# the new structure with the animal in hand. Nothing else is touched; any error
# returns the action as is.

_PG_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_PG_STRUCTURE = {'COW': ('BUILD_PASTURE', 'PASTURE'), 'SHEEP': ('BUILD_PASTURE', 'PASTURE'),
                 'GOOSE': ('BUILD_COOP', 'COOP')}


def pg_wrap(parent):
    report = {'built': 0, 'placed': 0, 'errors': 0}
    states = {}

    def pg_agent(observation, configuration=None):
        action = parent(observation, configuration)
        try:
            step = int(observation['step'])
            player = int(observation['player'])
            st = states.get(player)
            if st is None or step <= st['step']:
                st = states[player] = {'step': -1, 'pending': {}}
            st['step'] = step
            if not isinstance(action, dict):
                return action
            farm = observation['farms'][player]
            invs = observation['private'].get('inventories') or []
            commands = [action.get('farmer')] + list(action.get('hands') or [])
            changed = False
            for i, c in enumerate(commands):
                pos = farm['farmer'] if i == 0 else (farm['hands'][i - 1] if i - 1 < len(farm['hands']) else None)
                if pos is None:
                    continue
                x, y = int(pos[0]), int(pos[1])
                tile = farm['tiles'][y][x]
                held = invs[i] if i < len(invs) and invs[i] else {}
                pend = st['pending'].pop(i, None)
                if pend and pend[0] == step - 1 and pend[2] == (x, y):
                    animal = pend[1]
                    kind = _PG_STRUCTURE[animal][1]
                    if (isinstance(tile, dict) and tile.get('kind') == kind and 'animal' not in tile
                            and held.get(animal, 0) > 0):
                        commands[i] = ['PLACE', animal]
                        report['placed'] += 1
                        changed = True
                        continue
                if (isinstance(c, list) and len(c) >= 2 and c[0] == 'PLACE' and c[1] in _PG_STRUCTURE
                        and tile is None and (x, y) not in _PG_ACCESS and held.get(c[1], 0) > 0):
                    commands[i] = [_PG_STRUCTURE[c[1]][0]]
                    st['pending'][i] = (step, c[1], (x, y))
                    report['built'] += 1
                    changed = True
            if changed:
                action = dict(action, farmer=commands[0], hands=commands[1:])
        except Exception:
            report['errors'] += 1
        return action

    pg_agent.telemetry = report
    return pg_agent
# ---- END place_guard ----
