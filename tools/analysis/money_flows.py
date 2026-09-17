"""Money flows by good and by day on the live tapes, for us and the opponent.

Wraps the engine's market phase to log every sale, purchase, hire and land
buy per player. With AGENT h-package the game is the live game exactly, so
the opponent's flows are its real ones.

usage: flows.py AGENT OUT.json [KEY=VALUE ...]
"""
import json
import os
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def one(job):
    kind, settings, path = job
    sys.path.insert(0, str(ROOT))
    from kaggle_environments import make
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
    from rl.replay_agent import build_replay_agent
    from tools.data.extract_live_tapes import unpack
    from tools.eval.live_replay import build_agent

    record = json.loads(Path(path).read_text(encoding="utf-8"))
    side = int(record["our_side"])
    ctx = {"farms": None, "step": 0}
    flows = [defaultdict(float), defaultdict(float)]
    orig_market, orig_commit = K._process_market, K._commit_unit
    orig_hire, orig_land = K._do_hire, K._do_buy_land

    def who(farm):
        for i, f in enumerate(ctx["farms"] or []):
            if f is farm:
                return i
        return None

    def log(farm, key, delta):
        i = who(farm)
        if i is not None and delta:
            flows[i][f"{ctx['step'] // 24}|{key}"] += delta

    def market(state, env):
        ctx["farms"] = state[0].observation.farms
        ctx["step"] = int(state[0].observation.step or 0)
        return orig_market(state, env)

    def commit(op, item, price, farm, private, mk, cap=100):
        before = farm["money"]
        ok = orig_commit(op, item, price, farm, private, mk, cap)
        if ok:
            log(farm, f"{op}|{item}", farm["money"] - before)
        return ok

    def hire(farm, *a, **k):
        before = farm["money"]
        out = orig_hire(farm, *a, **k)
        log(farm, "HIRE|", farm["money"] - before)
        return out

    def land(farm, *a, **k):
        before = farm["money"]
        out = orig_land(farm, *a, **k)
        log(farm, "LAND|", farm["money"] - before)
        return out

    K._process_market, K._commit_unit = market, commit
    K._do_hire, K._do_buy_land = hire, land
    try:
        agent = build_agent(kind, settings)
        opponent = build_replay_agent(tuple(unpack(record["opp_actions_zlib_b64"])))
        env = make("kaggriculture", configuration={
            "episodeSteps": 720, "seed": record["seed"], "runTimeout": 36000,
            "actTimeout": 60}, debug=False)
        env.run([agent, opponent] if side == 0 else [opponent, agent])
    finally:
        K._process_market, K._commit_unit = orig_market, orig_commit
        K._do_hire, K._do_buy_land = orig_hire, orig_land
    return {"episode_id": record["episode_id"], "side": side,
            "rating": record.get("opponent_rating"),
            "live": record["rewards"],
            "reward": [env.state[side].reward, env.state[1 - side].reward],
            "us": dict(flows[side]), "them": dict(flows[1 - side])}


def main():
    kind, out = sys.argv[1], sys.argv[2]
    settings = {}
    for item in sys.argv[3:]:
        k, _, v = item.partition("=")
        try:
            settings[k] = json.loads(v)
        except json.JSONDecodeError:
            settings[k] = v
    sub = int(os.environ.get("ONLY_SUBMISSION", "0"))
    paths = sorted(str(p) for p in (ROOT / "rl/data/our_live_tapes").glob("ep*.json"))
    if sub:
        paths = [q for q in paths
                 if json.loads(Path(q).read_text(encoding="utf-8")).get("submission") == sub]
    with Pool(5) as pool:
        games = pool.map(one, [(kind, settings, p) for p in paths])
    Path(out).write_text(json.dumps(games), encoding="utf-8")
    print("saved", out, len(games))


if __name__ == "__main__":
    main()
