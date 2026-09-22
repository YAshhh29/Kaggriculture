"""Merge a whole Python file into another namespace, without executing it.

K's first packaging attempt embedded H2's file as a base64 blob and ran it
through `exec(compile(...))` at import time, in its own `types.ModuleType`
namespace, to keep its 83 top-level functions and 3 classes from colliding
with J's. That technique is correct -- verified against the source action
by action, 719 of 719 steps matching -- but it is also the one thing in
either packaged file that no working example read for this project does:
every public notebook studied decodes and verifies a blob like that at
BUILD time, inside their own notebook, and then submits the plain,
decoded, statically-readable source. None of them ship a submission that
still runs exec() on itself once it is on the grading server.

Both J's and K's submissions failed Kaggle's validation episode for a
reason that eight separate local hypotheses (entry point resolution, load
time, per-turn time at the engine's true default actTimeout of one
second, Python syntax compatibility, self-play, leftover imports, name
collisions, byte-level file integrity) could not reproduce. The blob
approach is the single structural outlier against everything proven to
work, so it is removed here, whether or not it is the actual cause,
because it costs little to remove and brings the file in line with every
working pattern seen.

This does the merge with an AST, not a text substitution. Every top-level
function, class and assigned name in the embedded file is prefixed and
every bare reference to it is renamed to match -- but only `ast.Name`
nodes are touched, so an attribute access like `obj.agent` (an
`ast.Attribute`, a string, not a Name) and a string literal that happens
to contain "agent" (an `ast.Constant`) are left alone by construction, not
by care taken in a regex. `global`/`nonlocal` declarations are updated too,
so a renamed module-level name stays consistent with any function that
declares it global. Plain stdlib imports (`import json`, `import copy`)
are left as ordinary duplicate imports, which Python handles for free --
only names the file itself DEFINES are prefixed.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets
                        if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    names.add(alias.asname)
    return names


class _Rename(ast.NodeTransformer):
    """Renames bare identifiers only -- never attributes, never strings."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self.mapping:
            node.id = self.mapping[node.id]
        return node

    def visit_FunctionDef(self, node):
        if node.name in self.mapping:
            node.name = self.mapping[node.name]
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        if node.name in self.mapping:
            node.name = self.mapping[node.name]
        self.generic_visit(node)
        return node

    def visit_Global(self, node: ast.Global) -> ast.Global:
        node.names = [self.mapping.get(n, n) for n in node.names]
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Nonlocal:
        node.names = [self.mapping.get(n, n) for n in node.names]
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # Only rename the LOCAL alias, never the module attribute being
        # imported -- `from itertools import permutations as _r53_p`
        # becomes `... as _H2_r53_p`, not a rename of `permutations`
        # itself, which is itertools' own name, not this file's.
        for alias in node.names:
            bound = alias.asname or alias.name
            if bound in self.mapping and alias.asname:
                alias.asname = self.mapping[bound]
            elif bound in self.mapping and not alias.asname:
                alias.asname = self.mapping[bound]
        return node

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            bound = alias.asname or alias.name
            if bound in self.mapping and alias.asname:
                alias.asname = self.mapping[bound]
        return node

    def visit_Call(self, node: ast.Call) -> ast.Call:
        # H2's own file layers many versions of `agent` by popping the
        # current one out of its own namespace BY STRING NAME and rebinding
        # a new one over it -- `agent = globals().pop("agent")`, sixteen
        # times through the file. A plain Name-based rename cannot see a
        # string constant, so `def agent` becomes `def _H2_agent` while the
        # sixteen `globals().pop("agent")` calls are still asking for a key
        # that was renamed out from under them. Every method call whose
        # receiver is a call to `globals()` and whose first string argument
        # names something renamed gets that argument renamed too.
        self.generic_visit(node)
        if (isinstance(node.func, ast.Attribute)
                and node.func.attr in ("pop", "get")
                and isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Name)
                and node.func.value.func.id == "globals"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value in self.mapping):
            node.args[0] = ast.Constant(value=self.mapping[node.args[0].value])
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.Subscript:
        self.generic_visit(node)
        key = node.slice
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "globals"
                and isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and key.value in self.mapping):
            node.slice = ast.Constant(value=self.mapping[key.value])
        return node


def merge(source: str, prefix: str, entry_point: str = "agent") -> tuple[str, str]:
    """Rename every top-level binding in `source` behind `prefix`.

    Returns the rewritten source (its own `from __future__ import
    annotations` dropped, since the final file declares one at the top)
    and the new, prefixed name of `entry_point`.
    """
    tree = ast.parse(source)
    names = _top_level_names(tree)
    mapping = {name: f"{prefix}{name}" for name in names}
    tree.body = [node for node in tree.body
                if not (isinstance(node, ast.ImportFrom)
                        and node.module == "__future__")]
    _Rename(mapping).visit(tree)
    ast.fix_missing_locations(tree)
    rewritten = ast.unparse(tree)
    new_entry = mapping.get(entry_point, entry_point)
    return rewritten, new_entry


def merge_file(path: Path, prefix: str, entry_point: str = "agent") -> tuple[str, str]:
    return merge(path.read_text(encoding="utf-8"), prefix, entry_point)
