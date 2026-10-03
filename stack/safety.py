# ---- BEGIN safety (Agent L's own layer) ----
# The outermost guard: never forfeit a game.
#
# On Kaggle an uncaught exception (ERROR), a malformed action (INVALID) or an
# exhausted 60 s overtime reserve (TIMEOUT) forfeits the game. This layer
# returns a valid PASS action instead of raising (without calling the parent
# again for the same step), repairs the action's shape where it can, keeps a
# time budget other layers can consult (sf_budget_ok), and prints one health
# line at the end of the game for the agent's logs.

import json as _sf_json
import time as _sf_time

_SF_STATE = {'reserve': 60.0, 'turn_started': 0.0}
_SF_PASS = {'farmer': ['PASS'], 'hands': [], 'market': []}


def sf_budget_ok(observation=None, turn_ms=350.0, reserve_s=20.0):
    """True while an optional layer may spend time this turn."""
    try:
        reserve = float((observation or {}).get('remainingOverageTime', _SF_STATE['reserve']))
    except (TypeError, ValueError, AttributeError):
        reserve = _SF_STATE['reserve']
    spent = (_sf_time.perf_counter() - _SF_STATE['turn_started']) * 1000.0
    return reserve > reserve_s and spent < turn_ms


def _sf_repair(action):
    """A valid action dict, or None if it cannot be made valid."""
    if not isinstance(action, dict):
        return None
    out = {}
    farmer = action.get('farmer', ['PASS'])
    out['farmer'] = farmer if (isinstance(farmer, list) and farmer
                               and isinstance(farmer[0], str)) else ['PASS']
    hands = action.get('hands', [])
    if not isinstance(hands, list):
        hands = []
    out['hands'] = [h if (isinstance(h, list) and h and isinstance(h[0], str)) else ['PASS']
                    for h in hands]
    market = action.get('market', [])
    if not isinstance(market, list):
        market = []
    out['market'] = [o for o in market if isinstance(o, list)][:10]
    return out


def sf_wrap(agent, name='agent'):
    stats = {'name': name, 'turns': 0, 'errors': 0, 'repaired': 0, 'max_ms': 0.0,
             'total_s': 0.0, 'slow_turns': 0, 'last_error': ''}

    def safe_agent(observation, configuration=None):
        _SF_STATE['turn_started'] = t0 = _sf_time.perf_counter()
        try:
            _SF_STATE['reserve'] = float(observation.get('remainingOverageTime', 60.0))
        except Exception:
            pass
        action = None
        try:
            raw = agent(observation, configuration)
            action = _sf_repair(raw)
            if action is None or action != raw:
                stats['repaired'] += 1
        except Exception as error:  # never forfeit a game over one turn
            stats['errors'] += 1
            stats['last_error'] = f"{type(error).__name__}: {error}"[:200]
        if action is None:
            action = {'farmer': ['PASS'], 'hands': [], 'market': []}
        ms = (_sf_time.perf_counter() - t0) * 1000.0
        stats['turns'] += 1
        stats['total_s'] += ms / 1000.0
        stats['max_ms'] = max(stats['max_ms'], ms)
        stats['slow_turns'] += ms > 800.0
        try:
            if int(observation.get('step', 0)) >= 718:
                print('HEALTH ' + _sf_json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                                 for k, v in stats.items()}), flush=True)
        except Exception:
            pass
        return action

    safe_agent.telemetry = stats
    return safe_agent
# ---- END safety ----
