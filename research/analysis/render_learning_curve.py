"""Render a compact SVG from a demand-animal learning-curve report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


SERIES = (
    ("learned", "Learned tree", "#006D77"),
    ("fixed_0", "Balanced", "#6B7280"),
    ("fixed_1", "Fixed cows", "#D97706"),
    ("fixed_2", "Fixed geese", "#2563EB"),
    ("oracle", "Oracle", "#111827"),
)


def render_svg(report: dict[str, Any]) -> str:
    """Render validation wins against accumulated training contexts."""
    points = report["points"]
    width, height = 900, 520
    left, right, top, bottom = 72, 30, 60, 70
    plot_width = width - left - right
    plot_height = height - top - bottom
    x_values = [int(point["training_contexts"]) for point in points]
    max_games = max(
        int(point[key]["games"])
        for point in points
        for key, _, _ in SERIES
    )
    min_wins = min(
        int(point[key]["wins"])
        for point in points
        for key, _, _ in SERIES
    )
    y_min = max(0, min_wins - 2)
    y_max = max_games

    def x(value: int) -> float:
        span = max(1, max(x_values) - min(x_values))
        return left + (value - min(x_values)) * plot_width / span

    def y(value: int) -> float:
        span = max(1, y_max - y_min)
        return top + (y_max - value) * plot_height / span

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F8FAFC"/>',
        '<text x="72" y="32" font-family="Segoe UI, sans-serif" font-size="22" font-weight="700" fill="#111827">Demand-animal validation learning curve</text>',
        '<text x="72" y="51" font-family="Segoe UI, sans-serif" font-size="12" fill="#475569">Held-out wins; 40 contexts at every point</text>',
    ]
    for value in range(y_min, y_max + 1):
        y_value = y(value)
        lines.append(
            f'<line x1="{left}" y1="{y_value:.2f}" x2="{width-right}" y2="{y_value:.2f}" stroke="#E2E8F0"/>'
        )
        lines.append(
            f'<text x="{left-12}" y="{y_value+4:.2f}" text-anchor="end" font-family="Segoe UI, sans-serif" font-size="11" fill="#64748B">{value}</text>'
        )
    lines.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#334155"/>',
            f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#334155"/>',
        ]
    )
    for value in x_values:
        x_value = x(value)
        lines.append(
            f'<text x="{x_value:.2f}" y="{height-bottom+24}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="11" fill="#64748B">{value}</text>'
        )
    lines.append(
        f'<text x="{left+plot_width/2:.2f}" y="{height-18}" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="12" fill="#334155">Training contexts</text>'
    )
    for series_index, (key, label, color) in enumerate(SERIES):
        coordinates = [
            (x(int(point["training_contexts"])), y(int(point[key]["wins"])))
            for point in points
        ]
        path = " ".join(
            f'{"M" if index == 0 else "L"}{x_value:.2f},{y_value:.2f}'
            for index, (x_value, y_value) in enumerate(coordinates)
        )
        lines.append(
            f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3"/>'
        )
        for x_value, y_value in coordinates:
            lines.append(
                f'<circle cx="{x_value:.2f}" cy="{y_value:.2f}" r="4" fill="{color}"/>'
            )
        legend_x = 570 + (series_index % 2) * 155
        legend_y = 76 + (series_index // 2) * 22
        lines.append(
            f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x+22}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        lines.append(
            f'<text x="{legend_x+29}" y="{legend_y+4}" font-family="Segoe UI, sans-serif" font-size="11" fill="#334155">{html.escape(label)}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(report), encoding="utf-8")
    print(f"Learning curve written to {args.output}")


if __name__ == "__main__":
    main()
