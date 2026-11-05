"""Static SVG figures for the circuit-model and partial-irrep runs (standard library only).

Reads the saved, verified result directories read-only and writes four SVG files to
cayley-thesis/reports/bound-figures/. Run from the repository root:

    python cayley-thesis/experiments/draw_bound_figures.py
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIRCUIT_RUN = ROOT / "experiments/results/circuit-model/20261104T102000_570473Z"
PARTIAL_RUN = ROOT / "experiments/results/partial-irreps/20261104T171505_843220Z"
OUT = ROOT / "reports/bound-figures"

# Reference palette (dataviz skill, light mode).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
FONT = "'Segoe UI','Noto Sans TC','Microsoft JhengHei',Arial,sans-serif"

GROUP_NAMES = {
    "d4": "D₄", "q8": "Q₈", "d6": "D₆", "z4xz4": "ℤ₄×ℤ₄", "z2_cubed": "ℤ₂³",
    "z3xz3": "ℤ₃×ℤ₃", "s3": "S₃", "a4": "A₄", "d8": "D₈", "s4": "S₄",
}
REP_NAMES = {"sign": "ε", "standard_3d": "V", "sign_twist_3d": "εV", "matching_quotient_2d": "W"}
REP_ORDER = ["sign", "matching_quotient_2d", "standard_3d", "sign_twist_3d"]


def text(x, y, s, size=13, fill=INK2, anchor="start", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(s)}</text>')


def svg(width, height, body, title, subtitle, source):
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}">',
        f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>',
        text(24, 34, title, 18, INK, weight="600"),
        text(24, 56, subtitle, 13, INK2),
    ]
    foot = [text(24, height - 14, source, 11, MUTED), "</svg>"]
    return "\n".join(head + body + foot)


def hbar(x, y, w, h, fill, tip):
    """Horizontal bar with 4px rounded data end, square at the baseline."""
    if w <= 0:
        return ""
    r = min(4, w, h / 2)
    d = (f"M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r:.1f} "
         f"a{r},{r} 0 0 1 {-r},{r} h{-(w - r):.1f} z")
    return f'<path d="{d}" fill="{fill}"><title>{escape(tip)}</title></path>'


def legend(x, y, items):
    out, cx = [], x
    for label, color in items:
        out.append(f'<rect x="{cx}" y="{y - 10}" width="12" height="12" rx="3" fill="{color}"/>')
        out.append(text(cx + 18, y, label, 13, INK2))
        cx += 40 + sum(13 if ord(ch) > 0x2E80 else 7 for ch in label)
    return out


def load(run):
    return json.loads((run / "results.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- figure 1
def fig_circuit_reduction(groups):
    rows = []
    for g in groups:
        free = g["totals"]["nonzero"]["generated"]
        circ = g["totals"]["circuit"]["generated"]
        rows.append((GROUP_NAMES[g["group"]], free, circ, 1 - circ / free))
    rows.sort(key=lambda r: (-r[3], r[0]))
    left, top, bar_h, gap, plot_w = 110, 96, 22, 12, 520
    height = top + len(rows) * (bar_h + gap) + 60
    body = []
    for pct in (0, 10, 20, 30, 40, 50):
        x = left + plot_w * pct / 50
        body.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{height - 52}" stroke="{GRID}"/>')
        body.append(text(x, top - 14, f"{pct}%", 11, MUTED, "middle"))
    for i, (name, free, circ, red) in enumerate(rows):
        y = top + i * (bar_h + gap)
        body.append(text(left - 12, y + 16, name, 14, INK, "end"))
        tip = f"{name}: 免費 h=1 產生 {free} 個節點，完整電阻 {circ} 個（減少 {red:.1%}）"
        if red > 0:
            body.append(hbar(left, y, plot_w * red / 0.5, bar_h, BLUE, tip))
            body.append(text(left + plot_w * red / 0.5 + 8, y + 16, f"{red:.1%}　({free} → {circ})", 12, INK2))
        else:
            body.append(f'<circle cx="{left}" cy="{y + bar_h / 2}" r="4" fill="{MUTED}"><title>{escape(tip)}</title></circle>')
            body.append(text(left + 12, y + 16, f"0%　({free} → {circ})", 12, MUTED))
    body.append(f'<line x1="{left}" y1="{top - 8}" x2="{left}" y2="{height - 52}" stroke="{AXIS}"/>')
    return svg(760, height, body,
               "完整電阻下界相對「免費 h=1」減少的搜尋節點",
               "10 個群、119 個目標的節點總數；6 個群完全沒有改進",
               "資料：experiments/results/circuit-model/20261104T102000_570473Z")


# ---------------------------------------------------------------- figure 2
def fig_circuit_gap(groups):
    rows = sorted(((GROUP_NAMES[g["group"]], g["diameter"], g["resistance_diameter_lower_bound"],
                    g["max_resistance"]) for g in groups), key=lambda r: (-r[1], r[0]))
    left, top, row_h, plot_w, xmax = 110, 110, 32, 520, 6
    height = top + len(rows) * row_h + 70
    body = legend(left, 84, [("⌈max R_eff⌉（電阻給出的最好下界）", BLUE), ("diameter（真實值）", INK2)])
    for v in range(0, xmax + 1):
        x = left + plot_w * v / xmax
        body.append(f'<line x1="{x:.1f}" y1="{top - 10}" x2="{x:.1f}" y2="{height - 64}" stroke="{GRID}"/>')
        body.append(text(x, height - 48, str(v), 11, MUTED, "middle"))
    body.append(text(left + plot_w / 2, height - 32, "步數", 12, INK2, "middle"))
    for i, (name, diam, lb, rmax) in enumerate(rows):
        y = top + i * row_h + 6
        xl, xd = left + plot_w * lb / xmax, left + plot_w * diam / xmax
        tip = f"{name}: diameter {diam}，max R_eff = {rmax}，⌈max R⌉ = {lb}"
        body.append(text(left - 12, y + 5, name, 14, INK, "end"))
        body.append(f'<line x1="{xl:.1f}" y1="{y}" x2="{xd:.1f}" y2="{y}" stroke="{AXIS}" stroke-width="2"/>')
        body.append(f'<circle cx="{xd:.1f}" cy="{y}" r="6" fill="{INK2}" stroke="{SURFACE}" stroke-width="2"><title>{escape(tip)}</title></circle>')
        body.append(f'<circle cx="{xl:.1f}" cy="{y}" r="6" fill="{BLUE}" stroke="{SURFACE}" stroke-width="2"><title>{escape(tip)}</title></circle>')
        body.append(text(xd + 14, y + 4, f"差 {diam - lb}", 12, MUTED))
    return svg(760, height, body,
               "電阻下界和真實 diameter 的差距",
               "每個群上 ⌈R_eff⌉ 的最大值 vs diameter；差距隨 diameter 變大",
               "資料：experiments/results/circuit-model/20261104T102000_570473Z")


# ---------------------------------------------------------------- figure 3
def subset_label(members):
    return "+".join(REP_NAMES[m] for m in sorted(members, key=REP_ORDER.index)) or "免費 h=1"


def fig_partial_budget(s4):
    arms = [a for a in s4["arms"] if a["heuristic"] != "full_electrical"]
    full = {a["pruning"]: a["totals"]["generated"] for a in s4["arms"] if a["heuristic"] == "full_electrical"}
    left, top, plot_w, plot_h = 90, 124, 600, 330
    xmax, ymin, ymax = 24, 400, 950
    X = lambda v: left + plot_w * v / xmax
    Y = lambda v: top + plot_h * (ymax - v) / (ymax - ymin)
    height = top + plot_h + 80
    body = legend(left, 82, [("不加規則", BLUE), ("加關係式規則", ORANGE)])
    for v in range(400, 951, 100):
        body.append(f'<line x1="{left}" y1="{Y(v):.1f}" x2="{left + plot_w}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        body.append(text(left - 8, Y(v) + 4, str(v), 11, MUTED, "end"))
    for v in range(0, 25, 4):
        body.append(text(X(v), top + plot_h + 20, str(v), 11, MUTED, "middle"))
    body.append(text(left + plot_w / 2, top + plot_h + 42, "所選表示的 Σ d²（成本代理；全部非平凡表示 = 23）", 12, INK2, "middle"))
    body.append(text(left - 60, top - 12, "產生的節點數（S₄ 全部 24 個目標）", 12, INK2))
    for pruning, color in ((False, BLUE), (True, ORANGE)):
        y = Y(full[pruning])
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="{color}" stroke-dasharray="5 4" stroke-width="1.5" opacity="0.7"/>')
    body.append(text(left + 8, Y(full[False]) - 6, f"完整電阻（不加規則）{full[False]}", 11, INK2))
    body.append(text(left + 8, Y(full[True]) + 15, f"完整電阻＋規則 {full[True]}", 11, INK2))
    points = {}
    for a in arms:
        points.setdefault((a["pruning"], a["dimension_squared"], a["totals"]["generated"]), []).append(subset_label(a["members"]))
    callouts = {("ε+V", False), ("ε+W+V", False), ("V+εV", False), ("W+V+εV", False)}
    for (pruning, budget, gen), labels in sorted(points.items()):
        color = ORANGE if pruning else BLUE
        tip = f"{'加規則' if pruning else '不加規則'}，Σd²={budget}，{gen} 個節點：" + "、".join(labels)
        body.append(f'<circle cx="{X(budget):.1f}" cy="{Y(gen):.1f}" r="6" fill="{color}" stroke="{SURFACE}" stroke-width="2"><title>{escape(tip)}</title></circle>')
        for lab in labels:
            if (lab, pruning) in callouts:
                body.append(text(X(budget) - 10, Y(gen) + 4, lab, 12, INK, "end"))
    body.append(text(X(5), Y(912) - 12, "單一表示、以及多數組合：與免費 h=1 相同（912 / 740）", 12, INK2))
    body.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="{AXIS}"/>')
    return svg(760, height, body,
               "S₄：部分不可約表示的組合與搜尋節點數",
               "每個點是一組表示（共 15 組）；單獨無效，組合跨過取整門檻才有效",
               "資料：experiments/results/partial-irreps/20261104T171505_843220Z；ε=sign，W=2 維，V=標準 3 維，εV=V⊗sign")


# ---------------------------------------------------------------- figure 4
def fig_partial_cost(s4):
    want = [
        ("free_h1", (), False, "免費 h=1"),
        ("free_h1", (), True, "免費 h=1＋規則"),
        ("sign+standard_3d", ("sign", "standard_3d"), False, "ε+V"),
        ("standard_3d+sign_twist_3d", ("standard_3d", "sign_twist_3d"), False, "V+εV"),
        ("standard_3d+sign_twist_3d+matching_quotient_2d", None, False, "W+V+εV"),
        ("standard_3d+sign_twist_3d+matching_quotient_2d", None, True, "W+V+εV＋規則"),
        ("full_electrical", (), False, "完整電阻"),
        ("full_electrical", (), True, "完整電阻＋規則"),
    ]
    rows = []
    for key, _, pruning, label in want:
        a = next(a for a in s4["arms"] if a["heuristic"] == key and a["pruning"] == pruning)
        rows.append((label, a["preprocessing_seconds"] * 1000, a["search_seconds"] * 1000, a["totals"]["generated"]))
    left, top, bar_h, gap, plot_w, xmax = 170, 104, 22, 12, 480, 340
    height = top + len(rows) * (bar_h + gap) + 80
    body = legend(left, 82, [("setup（建表示、驗證、查找表）", BLUE), ("搜尋（5 次中位數）", ORANGE)])
    for v in range(0, 341, 50):
        x = left + plot_w * v / xmax
        body.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{height - 60}" stroke="{GRID}"/>')
        body.append(text(x, height - 44, f"{v}", 11, MUTED, "middle"))
    body.append(text(left + plot_w / 2, height - 28, "毫秒（ms）", 12, INK2, "middle"))
    for i, (label, setup, search, gen) in enumerate(rows):
        y = top + i * (bar_h + gap)
        ws, wq = plot_w * setup / xmax, plot_w * search / xmax
        tip = f"{label}: setup {setup:.3f} ms，搜尋 {search:.3f} ms，總計 {setup + search:.3f} ms，{gen} 個節點"
        body.append(text(left - 12, y + 16, label, 13, INK, "end"))
        body.append(f'<rect x="{left}" y="{y}" width="{max(ws, 1):.1f}" height="{bar_h}" fill="{BLUE}"><title>{escape(tip)}</title></rect>')
        body.append(hbar(left + ws + 2, y, max(wq, 3), bar_h, ORANGE, tip))
        body.append(text(left + ws + max(wq, 3) + 10, y + 16, f"{setup + search:.1f} ms　·　{gen} 節點", 12, INK2))
    body.append(f'<line x1="{left}" y1="{top - 8}" x2="{left}" y2="{height - 60}" stroke="{AXIS}"/>')
    return svg(820, height, body,
               "S₄：節點變少，但總時間由 setup 主導",
               "冷啟動總時間 = setup + 搜尋；直接 BFS 整張圖約 0.02 ms",
               "資料：experiments/results/partial-irreps/20261104T171505_843220Z（正式跑；時間只在同一次執行內可比）")


def main():
    circuit = load(CIRCUIT_RUN)["groups"]
    s4 = next(g for g in load(PARTIAL_RUN)["groups"] if g["group"] == "s4")
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {
        "circuit-node-reduction.svg": fig_circuit_reduction(circuit),
        "circuit-diameter-gap.svg": fig_circuit_gap(circuit),
        "partial-irrep-budget.svg": fig_partial_budget(s4),
        "partial-irrep-cost.svg": fig_partial_cost(s4),
    }
    for name, content in figures.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(OUT / name)


if __name__ == "__main__":
    main()
