"""Extract the exact main.py a public Kaggriculture notebook submits.

Most public notebooks ship their agent as a compressed blob (base85 or base64,
usually zlib-compressed) and assert its sha256 before writing main.py. This
finds every large encoded string in the notebook, decodes it, keeps the one
that is valid agent source (compiles, defines functions, reads an
observation), and checks it against any 64-hex digest the notebook states.

For each notebook it writes rl/public/nb_<name>.py: a header, the decoded
main.py byte for byte between BEGIN/END markers, and `agent = <entry>`,
where <entry> is the callable Kaggle's loader would pick (the last callable).
Duplicates of programs already in rl/public (same main.py sha256) are
reported, not written. Nothing from the notebook is executed except the
decoded main.py itself, once, in a fresh namespace, to find its entry point.

    python -m tools.data.extract_notebook_agents abhinav0370__cha22-agent ...
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS = ROOT / "kaggle_cache" / "notebooks"
PUBLIC = ROOT / "rl" / "public"
BEGIN, END = "# ---- BEGIN main.py ----", "# ---- END main.py ----"

B85 = r"0-9A-Za-z!#$%&()*+\-;<=>?@^_`{|}~"
LONG_B85 = re.compile(r"['\"]([" + B85 + r"\s]{20000,})['\"]")
LONG_B64 = re.compile(r"['\"]([A-Za-z0-9+/=\s]{20000,})['\"]")
TRIPLE = re.compile(r"(?:[rRbB]{0,2})('''|\"\"\")(.{20000,}?)\1", re.S)
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")


ARCHIVE_FILES: dict = {}     # extracted main.py text -> the archive's other files


def _from_archive(data: bytes):
    """(main.py text, other members) if data is a tar or zip archive holding main.py."""
    import io
    import tarfile
    import zipfile
    try:
        if data[257:262] == b"ustar":
            with tarfile.open(fileobj=io.BytesIO(data)) as tar:
                files = {m.name.lstrip("./"): tar.extractfile(m).read()
                         for m in tar.getmembers() if m.isfile()}
        elif data[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
        else:
            return None
    except Exception:
        return None
    main = next((k for k in files if k.split("/")[-1] == "main.py"), None)
    if main is None:
        return None
    return files[main].decode("utf-8"), {k: v for k, v in files.items() if k != main}


def _decodings(blob):
    if isinstance(blob, bytes):
        blob = blob.decode("latin-1")
    s = re.sub(r"\s+", "", blob)
    for name, dec in (("b85", base64.b85decode), ("b64", base64.b64decode)):
        try:
            raw = dec(s)
        except Exception:
            continue
        # zlib.decompress(wbits=47) accepts both zlib and gzip streams
        for zname, z in (("zlib", lambda b: zlib.decompress(b, 47)), ("raw", lambda b: b)):
            try:
                data = z(raw)
            except Exception:
                continue
            arc = _from_archive(data)
            if arc is not None:
                ARCHIVE_FILES[arc[0]] = arc[1]
                yield f"{name}+{zname}+archive", arc[0]
                continue
            try:
                yield f"{name}+{zname}", data.decode("utf-8")
            except Exception:
                continue


def _agent_like(text: str) -> bool:
    if "def " not in text or "observation" not in text and "obs" not in text:
        return False
    try:
        compile(text, "main.py", "exec")
    except SyntaxError:
        return False
    return True


def _ast_constants(src: str):
    """Large str/bytes constants in the notebook's code, found by parsing it
    (never running it). Adjacent literals -- a source split into chunks inside
    parentheses -- are already one constant in the AST. Notebook magics
    (!pip, %%writefile) are blanked so the rest parses."""
    import ast
    lines = [("" if ln.lstrip().startswith(("!", "%")) else ln) for ln in src.splitlines()]
    try:
        tree = ast.parse("\n".join(lines))
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) \
                and len(node.value) > 20000:
            out.append(node.value)
        elif isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) > 5 and all(
                isinstance(e, ast.Constant) and isinstance(e.value, (str, bytes))
                for e in node.elts):
            kinds = {type(e.value) for e in node.elts}
            if len(kinds) == 1:                     # a source or blob split into chunks
                joined = (b"" if bytes in kinds else "").join(e.value for e in node.elts)
                if len(joined) > 20000:
                    out.append(joined)
    return out


def extract(notebook: Path):
    src = notebook.read_text(encoding="utf-8", errors="replace")
    blobs = [m.group(1) for m in LONG_B85.finditer(src)]
    blobs += [m.group(1) for m in LONG_B64.finditer(src)]
    candidates = []
    for value in _ast_constants(src):
        try:
            text = value.decode("utf-8") if isinstance(value, bytes) else value
        except UnicodeDecodeError:
            text = None
        if text is not None and _agent_like(text):  # the source itself, as a literal
            candidates.append((len(text), "literal", text))
        else:
            blobs.append(value)                     # an encoded blob; try decoders below
    for blob in blobs:
        for how, text in _decodings(blob):
            if _agent_like(text):
                candidates.append((len(text), how, text))
    for m in TRIPLE.finditer(src):          # plain source in a triple-quoted string
        if _agent_like(m.group(2)):
            candidates.append((len(m.group(2)), "plain", m.group(2)))
    if not candidates:
        return None
    _, how, text = max(candidates)
    digests = set(HEX64.findall(src))
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {"text": text, "how": how, "sha": sha, "sha_confirmed": sha in digests,
            "digests_in_notebook": len(digests), "others": ARCHIVE_FILES.get(text, {})}


def entry_of(text: str) -> str:
    env: dict = {}
    exec(compile(text, "main.py", "exec"), env)
    return [k for k, v in env.items() if callable(v)][-1]


def known_shas() -> dict:
    out = {}
    for p in PUBLIC.glob("nb_*.py"):
        t = p.read_text(encoding="utf-8", errors="replace")
        if BEGIN in t and END in t:
            body = t.split(BEGIN, 1)[1].split("\n", 1)[1].split(END, 1)[0]
            out[hashlib.sha256(body.encode("utf-8")).hexdigest()] = p.stem
    a = (ROOT / "submissions" / "agent-a" / "main.py").read_text(encoding="utf-8")
    out[hashlib.sha256(a.encode("utf-8")).hexdigest()] = "A"
    return out


def short_name(slug: str) -> str:
    user, _, rest = slug.partition("__")
    rest = re.sub(r"^kaggriculture-?", "", rest)
    return "nb_" + re.sub(r"[^a-z0-9]+", "_", (user[:12] + "_" + rest[:40]).lower()).strip("_")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notebooks", nargs="+", help="file stems in kaggle_cache/notebooks")
    args = ap.parse_args()
    known = known_shas()
    for stem in args.notebooks:
        found = extract(NOTEBOOKS / f"{stem}.py")
        if not found:
            print(f"  {stem}: no agent source found")
            continue
        dup = known.get(found["sha"])
        name = short_name(stem)
        if dup:
            print(f"  {stem}: DUPLICATE of {dup} (sha {found['sha'][:12]})")
            continue
        try:
            entry = entry_of(found["text"])
        except Exception as error:
            print(f"  {stem}: decoded ({found['how']}) but failed to load: {type(error).__name__}: {error}")
            continue
        header = (f"# Extracted public agent -- local evaluation and opponent modelling only.\n"
                  f"# Source: kaggle_cache/notebooks/{stem}.py (public Kaggle notebook).\n"
                  f"# main.py decoded from a {found['how']} blob; sha256 {found['sha']}"
                  f" ({'matches a digest stated in the notebook' if found['sha_confirmed'] else 'no matching digest in the notebook'}).\n"
                  f"# Kaggle's loader (get_last_callable) selects `{entry}`; the alias after END\n"
                  f"# makes it `agent` for local loaders. Licence notices are inside main.py.\n")
        out = PUBLIC / f"{name}.py"
        out.write_text(header + BEGIN + "\n" + found["text"] + ("" if found["text"].endswith("\n") else "\n")
                       + END + "\n" + f"agent = {entry}\n", encoding="utf-8")
        known[found["sha"]] = name
        if found["others"]:
            print(f"      archive also holds {sorted(found['others'])[:8]} -- the agent may read them")
        print(f"  {stem}: -> {out.relative_to(ROOT)} ({len(found['text']):,} chars, {found['how']}, "
              f"sha {'CONFIRMED' if found['sha_confirmed'] else 'unconfirmed'}, entry {entry})")


if __name__ == "__main__":
    main()
