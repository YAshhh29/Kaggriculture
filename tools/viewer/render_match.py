"""Play one match and write a watchable HTML replay.

    python tools/viewer/render_match.py --agent candidates.candidate_e:agent \
        --opponent agents/experimental_distilled_elite_andrey_agent.py \
        --seed 6 --out artifacts/replays/e_vs_andrey_seed6.html

Then watch it:

    python tools/viewer/render_match.py --seed 6 --serve

**The replay must be served over HTTP, not opened as a file.** The
Kaggriculture visualiser is built as an ES module (`<script
type="module">`), and every browser refuses to execute module scripts from
a `file://` URL under its CORS rules -- so double-clicking the HTML gives
a blank page with no error. `--serve` starts a throwaway local web server
on the output directory and opens the right URL, which fixes it.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_agent(spec: str):
    """Load `module:attr` from the repo, or a path to an agent file."""
    if ":" in spec and not spec.endswith(".py"):
        module, attr = spec.split(":", 1)
        return getattr(importlib.import_module(module), attr)
    path = (ROOT / spec).resolve()
    name = "viewer_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    loaded = importlib.util.spec_from_file_location(name, path)
    if loaded is None or loaded.loader is None:
        raise SystemExit(f"could not load agent: {spec}")
    module = importlib.util.module_from_spec(loaded)
    sys.modules[name] = module
    loaded.loader.exec_module(module)
    return module.agent


def serve(path: Path, port: int) -> None:
    """Serve the replay over http and open it.

    A `file://` page cannot run the visualiser, which is an ES module, so
    the replay has to come off a real origin. This starts a plain static
    server on the replay's own directory, opens the page, and keeps
    running until interrupted.
    """
    import functools
    import http.server
    import socketserver
    import threading
    import webbrowser

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(path.parent)
    )
    socketserver.TCPServer.allow_reuse_address = True
    while True:
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            port += 1
    url = f"http://127.0.0.1:{port}/{path.name}"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print("")
    print(f"serving at {url}")
    print("opening it now -- press Ctrl+C here when you are done watching")
    webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", default="candidates.candidate_e:agent")
    parser.add_argument(
        "--opponent",
        default="agents/experimental_distilled_elite_andrey_agent.py",
    )
    parser.add_argument("--seed", type=int, default=6)
    parser.add_argument("--seat", type=int, default=0, choices=(0, 1))
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--out", default=None)
    parser.add_argument("--open", action="store_true",
                        help="open the replay in the default browser")
    parser.add_argument("--serve", action="store_true",
                        help="serve the replay over http and open it "
                             "(required: file:// cannot run module scripts)")
    parser.add_argument("--port", type=int, default=8777)
    args = parser.parse_args()

    from kaggle_environments import make

    mine = load_agent(args.agent)
    theirs = load_agent(args.opponent)
    players = [mine, theirs] if args.seat == 0 else [theirs, mine]

    environment = make(
        "kaggriculture",
        configuration={"episodeSteps": args.steps, "seed": args.seed},
        debug=False,
    )
    environment.run(players)

    final = environment.toJSON()["steps"][-1]
    mine_reward = final[args.seat].get("reward")
    their_reward = final[1 - args.seat].get("reward")
    verdict = (
        "WIN" if (mine_reward or 0) > (their_reward or 0)
        else "loss" if (mine_reward or 0) < (their_reward or 0)
        else "tie"
    )
    print(f"{args.agent} {mine_reward:,.0f}  vs  "
          f"{Path(args.opponent).stem} {their_reward:,.0f}   -> {verdict}")

    out = Path(args.out) if args.out else (
        ROOT / "artifacts" / "replays"
        / f"{args.agent.replace(':', '_').replace('.', '_')}"
          f"_seed{args.seed}_seat{args.seat}.html"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(environment.render(mode="html", width=1000, height=760),
                   encoding="utf-8")
    print(f"replay written to {out}")
    if args.serve:
        serve(out, args.port)
    elif args.open:
        import webbrowser
        webbrowser.open(out.resolve().as_uri())
        print("NOTE: a file:// page cannot run the visualiser's module "
              "scripts and will render blank -- use --serve instead.")
    else:
        print("watch it with:  python tools/viewer/render_match.py "
              f"--seed {args.seed} --serve")


if __name__ == "__main__":
    main()
