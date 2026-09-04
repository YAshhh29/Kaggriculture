"""Cross-sectional study of how the field actually plays Kaggriculture.

Two analyses, deliberately separated because they answer different
questions and have different confounds:

1. **Paired within-game contrast.** For every replay, contrast the
   winner's profile against the loser's. Both players in a game share a
   seed, a market and an opponent, so this controls for "who drew the
   easy game" in a way a cross-sectional median cannot. Reported as the
   share of games in which the winner did more of a thing (a sign test),
   plus the median within-game difference. The sign share is the honest
   headline: a feature that wins 50% of pairs is noise no matter how
   large its median difference looks.

2. **Skill gradient.** Aggregate per team, then correlate each feature
   with that team's public leaderboard score. This answers "what do
   better teams do", which is not the same question as "what wins a
   given game", and is vulnerable to the fact that stronger teams face
   stronger opponents.

Both are computed over whatever replays are on disk, across the whole
rating range, rather than a hand-picked elite subset.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any, Iterable

from tools.data.profile_agents import profile_file


SCALARS = (
    "reward",
    "total_sale_revenue",
    "hires",
    "final_hands",
    "final_quadrants",
    "move_turns",
    "task_turns",
    "pass_turns",
    "utilisation",
    "first_half_revenue_share",
    "wheat_bought_for_feed",
)
PRODUCTS = (
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "EGG",
    "MILK",
    "WOOL",
    "FERTILIZER",
)
ANIMALS = ("COW", "SHEEP", "GOOSE")
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


def flatten(row: dict[str, Any]) -> dict[str, float]:
    """Reduce one profile to a flat, comparable feature vector."""
    out: dict[str, float] = {}
    for key in SCALARS:
        value = row.get(key)
        if isinstance(value, (int, float)):
            out[key] = float(value)
    for product in PRODUCTS:
        out[f"sold_{product}"] = float(row.get("units_sold", {}).get(product, 0))
        out[f"rev_{product}"] = float(row.get("revenue", {}).get(product, 0))
        out[f"price_{product}"] = float(row.get("mean_price", {}).get(product, 0))
    for animal in ANIMALS:
        out[f"buy_{animal}"] = float(row.get("animals_bought", {}).get(animal, 0))
    for crop in CROPS:
        out[f"plant_{crop}"] = float(row.get("planted", {}).get(crop, 0))

    herd = out["buy_COW"] + out["buy_SHEEP"] + out["buy_GOOSE"]
    out["sheep_share_of_herd"] = out["buy_SHEEP"] / herd if herd else 0.0
    out["goose_share_of_herd"] = out["buy_GOOSE"] / herd if herd else 0.0
    plantings = sum(out[f"plant_{c}"] for c in CROPS)
    out["carrot_share_of_plantings"] = (
        out["plant_CARROT"] / plantings if plantings else 0.0
    )
    scarce = out["rev_TOMATO"] + out["rev_CARROT"] + out["rev_EGG"]
    out["scarce_market_revenue"] = scarce
    out["scarce_revenue_share"] = (
        scarce / out["total_sale_revenue"]
        if out.get("total_sale_revenue")
        else 0.0
    )
    glut = out["rev_MILK"] + out["rev_WOOL"] + out["rev_MELON"]
    out["glut_market_revenue"] = glut
    return out


def load_profiles(directories: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for directory in directories:
        for path in sorted(directory.glob("episode-*-replay.json")):
            try:
                pair = profile_file(path)
            except Exception:
                continue
            if len(pair) != 2:
                continue
            episode = pair[0].get("episode_id")
            if episode in seen:
                continue
            seen.add(episode)
            rows.append({"episode_id": episode, "players": pair})
    return rows


def paired_contrast(games: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Winner-minus-loser, within each game."""
    diffs: dict[str, list[float]] = {}
    for game in games:
        a, b = game["players"]
        if a["reward"] == b["reward"]:
            continue
        winner, loser = (a, b) if a["reward"] > b["reward"] else (b, a)
        fw, fl = flatten(winner), flatten(loser)
        for key in fw:
            if key in ("reward", "total_sale_revenue"):
                continue
            diffs.setdefault(key, []).append(fw[key] - fl[key])

    results = []
    for key, values in diffs.items():
        decided = [v for v in values if v != 0]
        if len(decided) < 20:
            continue
        wins = sum(1 for v in decided if v > 0)
        share = wins / len(decided)
        # Two-sided sign test, normal approximation.
        z = (
            abs(wins - len(decided) / 2) / math.sqrt(len(decided) / 4)
            if decided
            else 0.0
        )
        results.append(
            {
                "feature": key,
                "winner_more_often": round(share, 3),
                "n_decided": len(decided),
                "median_diff": round(statistics.median(values), 2),
                "z": round(z, 1),
            }
        )
    results.sort(key=lambda r: -abs(r["winner_more_often"] - 0.5))
    return results


def skill_gradient(
    games: list[dict[str, Any]],
    scores: dict[str, float],
    min_games: int = 4,
) -> list[dict[str, Any]]:
    by_team: dict[str, list[dict[str, float]]] = {}
    for game in games:
        for player in game["players"]:
            team = str(player.get("team", ""))
            if team.casefold() in scores:
                by_team.setdefault(team.casefold(), []).append(flatten(player))

    teams = {t: rows for t, rows in by_team.items() if len(rows) >= min_games}
    if len(teams) < 5:
        return []
    keys = sorted({k for rows in teams.values() for k in rows[0]})
    out = []
    xs = [scores[t] for t in teams]
    for key in keys:
        ys = [statistics.median([r.get(key, 0.0) for r in rows]) for rows in teams.values()]
        if len(set(ys)) < 3:
            continue
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        if not dx or not dy:
            continue
        out.append(
            {
                "feature": key,
                "corr_with_leaderboard": round(num / (dx * dy), 3),
                "teams": len(teams),
            }
        )
    out.sort(key=lambda r: -abs(r["corr_with_leaderboard"]))
    return out


def leaderboard_scores(path: Path) -> dict[str, float]:
    import csv
    import io
    import zipfile

    archive = zipfile.ZipFile(path)
    name = archive.namelist()[0]
    reader = csv.DictReader(
        io.TextIOWrapper(archive.open(name), encoding="utf-8")
    )
    return {
        str(row["TeamName"]).casefold(): float(row["Score"])
        for row in reader
        if row.get("Score")
    }
