"""Draw a regular hyperbolic Cayley surface {p,k} in the Poincare disk (standard library only).

The universal cover of a catalogue surface whose faces are all p-gons and whose
vertices all have degree k, with 1/p + 1/k < 1/2, is the regular hyperbolic
tiling {p,k}. Starting from one face placed at the centre, neighbouring faces are
placed by the half-turn about each shared edge midpoint, and every tiling vertex
is labelled by the group element it covers. One copy of each surface face is
shaded as a fundamental domain; its boundary edges carry letters showing which
pairs are glued together.

The script asserts that every tiling vertex receives one consistent label and
that the labels around every complete vertex follow the surface's rotation.

    python cayley-thesis/experiments/draw_hyperbolic_surface.py q8-g3-uniform
"""

from __future__ import annotations

import cmath
import json
import math
import sys
from collections import deque
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
import surface_systems as ss  # noqa: E402

OUT = ROOT / "reports/hyperbolic-drawings"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
AXIS = "#c3c2b7"
EDGE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]  # one per generator/inverse pair
DOMAIN_FILL = "#e9e7df"
TILE_FILL = "#f4f3ef"
FONT = "'Segoe UI','Noto Sans TC','Microsoft JhengHei',Arial,sans-serif"


# ------------------------------------------------------------------ surface data
def load_surface(surface_id):
    catalogue = json.loads((ROOT / "data/surfaces/catalogue.json").read_text(encoding="utf-8"))
    entry = next(s for s in catalogue["surfaces"] if s["id"] == surface_id)
    gspec = catalogue["groups"][entry["group"]]
    group = ss.group_from_spec(gspec["spec"])
    gens = tuple(ss.freeze(g) for g in gspec["generators"])
    labels = dict(zip(gens, gspec["generator_labels"]))
    c = entry["construction"]
    if c["type"] == "uniform_rotation":
        order = tuple(gens[i] for i in c["order"])
        rotations = {v: order for v in group["elements"]}
    elif c["type"] == "local_binary_rotation":
        base = tuple(gens[i] for i in c.get("base_order", (0, 1, 2)))
        flipped = (base[0], base[2], base[1])
        rotations = {v: (flipped if bit == "1" else base) for v, bit in zip(group["elements"], c["bits"])}
    else:
        raise SystemExit(f"construction {c['type']!r} is not supported by this drawing script")
    faces = ss.faces_from_rotation_system(group, gens, rotations)
    return entry, gspec, group, gens, labels, rotations, faces


def element_name(element):
    if isinstance(element, tuple):
        return "".join(str(x + 1) for x in element)
    return str(element)


# ------------------------------------------------------------------ hyperbolic geometry
def mat_mul(a, b):
    return ((a[0][0] * b[0][0] + a[0][1] * b[1][0], a[0][0] * b[0][1] + a[0][1] * b[1][1]),
            (a[1][0] * b[0][0] + a[1][1] * b[1][0], a[1][0] * b[0][1] + a[1][1] * b[1][1]))


def apply(m, z):
    return (m[0][0] * z + m[0][1]) / (m[1][0] * z + m[1][1])


def translate(a):
    """Disk isometry sending 0 to a."""
    return ((1, a), (a.conjugate(), 1))


def half_turn(a):
    return mat_mul(mat_mul(translate(a), ((1j, 0), (0, -1j))), translate(-a))


def reference_polygon(p, k):
    big_r = math.acosh(1 / (math.tan(math.pi / p) * math.tan(math.pi / k)))
    in_r = math.acosh(math.cos(math.pi / k) / math.sin(math.pi / p))
    offset = math.pi / 2 - math.pi / p
    verts = [math.tanh(big_r / 2) * cmath.exp(1j * (offset + 2 * math.pi * j / p)) for j in range(p)]
    mids = [math.tanh(in_r / 2) * cmath.exp(1j * (offset + 2 * math.pi * j / p + math.pi / p)) for j in range(p)]
    return verts, [half_turn(m) for m in mids]


def key(z):
    return (round(z.real, 6), round(z.imag, 6))


# ------------------------------------------------------------------ tiling
def build_tiling(faces, p, verts, turns, max_tiles=1400, max_radius=0.992):
    position = {}
    for f, cyc in enumerate(faces):
        for t in range(p):
            position[(cyc[t], cyc[(t + 1) % p])] = (f, t)
    start = translate(-verts[0])  # put a vertex of the first face at the centre of the disk
    tiles, seen = [], {key(apply(start, 0j))}
    queue = deque([(start, 0, 0, None)])
    while queue and len(tiles) < max_tiles:
        m, f, off, parent = queue.popleft()
        idx = len(tiles)
        tiles.append({"m": m, "face": f, "off": off, "parent": parent,
                      "pts": [apply(m, v) for v in verts],
                      "labels": [faces[f][(off + j) % p] for j in range(p)]})
        for j in range(p):
            a, b = faces[f][(off + j) % p], faces[f][(off + j + 1) % p]
            f2, t = position[(b, a)]
            m2 = mat_mul(m, turns[j])
            c = apply(m2, 0j)
            if abs(c) > max_radius or key(c) in seen:
                continue
            seen.add(key(c))
            queue.append((m2, f2, (t - j) % p, idx))
    return tiles


def check_tiling(tiles, p, k, rotations, group):
    label_at, incident = {}, {}
    for ti, tile in enumerate(tiles):
        for j, z in enumerate(tile["pts"]):
            kz = key(z)
            lab = tile["labels"][j]
            if label_at.setdefault(kz, lab) != lab:
                raise AssertionError(f"inconsistent label at {z}")
            incident.setdefault(kz, []).append((ti, j))
    complete = 0
    for kz, inc in incident.items():
        if len(inc) > k:
            raise AssertionError("more than k tiles at a vertex")
        if len(inc) < k:
            continue
        complete += 1
        centre = complex(*kz)
        v = label_at[kz]
        nbrs = set()
        for ti, j in inc:
            labs = tiles[ti]["labels"]
            for nb in (labs[(j + 1) % p], labs[(j - 1) % p]):
                nbrs.add(group["mul"][(group["inv"][v], nb)])
        if nbrs != set(rotations[v]):
            raise AssertionError("neighbours around a vertex do not match the generators")
        # cyclic order of outgoing generators by angle must be the rotation (or its mirror).
        out = []
        for ti, j in inc:
            nxt = tiles[ti]["pts"][(j + 1) % p]
            out.append((cmath.phase(nxt - centre), group["mul"][(group["inv"][v], tiles[ti]["labels"][(j + 1) % p])]))
        cyc = [g for _a, g in sorted(out)]
        rot = list(rotations[v])
        shifts = [rot[s:] + rot[:s] for s in range(k)]
        if cyc not in shifts and cyc[::-1] not in shifts:
            raise AssertionError("cyclic order around a vertex differs from the rotation system")
    return label_at, complete


def fundamental_domain(tiles, n_faces):
    around = [ti for ti, t in enumerate(tiles) if any(abs(z) < 1e-9 for z in t["pts"])]
    if len(around) == n_faces and len({tiles[ti]["face"] for ti in around}) == n_faces:
        return set(around)  # every surface face meets the central vertex once: symmetric domain
    chosen, used = set(), set()
    for ti, tile in enumerate(tiles):
        if tile["face"] in used:
            continue
        if ti == 0 or tile["parent"] in chosen:
            chosen.add(ti)
            used.add(tile["face"])
        if len(used) == n_faces:
            break
    if len(used) != n_faces:
        raise AssertionError("could not build a connected fundamental domain")
    return chosen


# ------------------------------------------------------------------ SVG
def screen(z, cx, cy, rad):
    return cx + rad * z.real, cy - rad * z.imag


def arc_path(z1, z2, cx, cy, rad, move=True):
    x1, y1 = screen(z1, cx, cy, rad)
    x2, y2 = screen(z2, cx, cy, rad)
    start = f"M{x1:.2f},{y1:.2f} " if move else ""
    det = 2 * (z1.real * z2.imag - z1.imag * z2.real)
    if abs(det) < 1e-9:
        return start + f"L{x2:.2f},{y2:.2f}"
    r1, r2 = abs(z1) ** 2 + 1, abs(z2) ** 2 + 1
    ccx = (r1 * z2.imag - r2 * z1.imag) / det
    ccy = (z1.real * r2 - z2.real * r1) / det
    crad = math.sqrt(ccx * ccx + ccy * ccy - 1) * rad
    sx, sy = cx + rad * ccx, cy - rad * ccy
    cross = (x1 - sx) * (y2 - sy) - (y1 - sy) * (x2 - sx)
    sweep = 1 if cross > 0 else 0
    return start + f"A{crad:.2f},{crad:.2f} 0 0 {sweep} {x2:.2f},{y2:.2f}"


def text(x, y, s, size=13, fill=INK2, anchor="start", weight="normal", halo=False):
    stroke = f' stroke="{SURFACE}" stroke-width="3" paint-order="stroke"' if halo else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{stroke}>{escape(s)}</text>')


def draw(surface_id):
    entry, gspec, group, gens, labels, rotations, faces = load_surface(surface_id)
    p = len(faces[0])
    k = len(gens)
    if any(len(f) != p for f in faces) or 1 / p + 1 / k >= 0.5:
        raise SystemExit("this script needs a regular hyperbolic surface {p,k} with 1/p + 1/k < 1/2")
    verts, turns = reference_polygon(p, k)
    tiles = build_tiling(faces, p, verts, turns)
    label_at, complete = check_tiling(tiles, p, k, rotations, group)
    domain = fundamental_domain(tiles, len(faces))

    pair_class, classes = {}, []
    for g in gens:
        if g in pair_class:
            continue
        pair_class[g] = pair_class[group["inv"][g]] = len(classes)
        gi = group["inv"][g]
        classes.append(gi if labels[g].startswith("-") and not labels[gi].startswith("-") else g)

    def gen_of(a, b):
        return group["mul"][(group["inv"][a], b)]

    w, h, cx, cy, rad = 900, 980, 450, 520, 400
    body = [f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="{SURFACE}" stroke="{AXIS}" stroke-width="1.5"/>']
    # tiles
    for ti, tile in enumerate(tiles):
        pts = tile["pts"]
        d = arc_path(pts[0], pts[1], cx, cy, rad)
        for j in range(1, p):
            d += " " + arc_path(pts[j], pts[(j + 1) % p], cx, cy, rad, move=False)
        fill = DOMAIN_FILL if ti in domain else TILE_FILL
        body.append(f'<path d="{d} Z" fill="{fill}" stroke="none"><title>surface face F{tile["face"] + 1}</title></path>')
    # edges coloured by generator pair
    drawn = set()
    for tile in tiles:
        pts, labs = tile["pts"], tile["labels"]
        for j in range(p):
            e = frozenset((key(pts[j]), key(pts[(j + 1) % p])))
            if e in drawn:
                continue
            drawn.add(e)
            g = gen_of(labs[j], labs[(j + 1) % p])
            size = abs(pts[j] - pts[(j + 1) % p])
            width = max(0.4, min(2.0, 14 * size))
            tip = f"{element_name(labs[j])} → {element_name(labs[(j + 1) % p])}  ({labels[g]})"
            body.append(f'<path d="{arc_path(pts[j], pts[(j + 1) % p], cx, cy, rad)}" fill="none" '
                        f'stroke="{EDGE_COLORS[pair_class[g]]}" stroke-width="{width:.2f}" stroke-linecap="round">'
                        f'<title>{escape(tip)}</title></path>')
    # fundamental-domain boundary and gluing letters
    sides = {}
    for ti in domain:
        pts, labs = tiles[ti]["pts"], tiles[ti]["labels"]
        for j in range(p):
            e = frozenset((key(pts[j]), key(pts[(j + 1) % p])))
            sides.setdefault(e, []).append((ti, j))
    boundary = [(ti, j) for e, lst in sides.items() if len(lst) == 1 for ti, j in lst]
    by_edge = {}
    for ti, j in boundary:
        labs = tiles[ti]["labels"]
        by_edge.setdefault(frozenset((labs[j], labs[(j + 1) % p])), []).append((ti, j))
    letters = "abcdefghijklmnopqrstuvwxyz"
    for n, (edge, lst) in enumerate(sorted(by_edge.items(), key=lambda kv: sorted(map(element_name, kv[0])))):
        for ti, j in lst:
            pts = tiles[ti]["pts"]
            body.append(f'<path d="{arc_path(pts[j], pts[(j + 1) % p], cx, cy, rad)}" fill="none" stroke="{INK}" stroke-width="2.6"/>')
            mid = apply(tiles[ti]["m"], cmath.rect(abs(verts[0]) * 0.86, cmath.phase(verts[j]) + math.pi / p))
            x, y = screen(mid, cx, cy, rad)
            body.append(text(x, y + 4, letters[n % 26], 13, INK, "middle", "600", halo=True))
    # face names at domain tile centres, vertex labels on the domain
    for ti in domain:
        x, y = screen(apply(tiles[ti]["m"], 0j), cx, cy, rad)
        body.append(text(x, y + 6, f"F{tiles[ti]['face'] + 1}", 18, INK2, "middle", "600", halo=True))
    placed = set()
    for ti in domain:
        for j, z in enumerate(tiles[ti]["pts"]):
            if key(z) in placed:
                continue
            placed.add(key(z))
            x, y = screen(z, cx, cy, rad)
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{INK}" stroke="{SURFACE}" stroke-width="1.5"/>')
            body.append(text(x + 6, y - 6, element_name(label_at[key(z)]), 12, INK, halo=True))

    V, E, F = len(group["elements"]), len(group["elements"]) * k // 2, len(faces)
    genus = (2 - (V - E + F)) // 2
    title = f"{gspec['display']} 的 Cayley 曲面（genus {genus}）在 Poincaré 圓盤中的萬有覆蓋"
    sub = (f"正則雙曲鋪排 {{{p},{k}}}：每個面是正 {p} 邊形、每個頂點 {k} 個面、內角 {360 // k}°；"
           f"V − E + F = {V} − {E} + {F} = {V - E + F}")
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">',
            f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>',
            text(24, 34, title, 18, INK, weight="600"), text(24, 56, sub, 13, INK2)]
    lx = 24
    for ci, c in enumerate(classes):
        g, gi = c, group["inv"][c]
        lab = labels[g] if g == gi else f"{labels[g]} / {labels[gi]}"
        head.append(f'<rect x="{lx}" y="{72}" width="18" height="4" rx="2" fill="{EDGE_COLORS[ci]}"/>')
        head.append(text(lx + 24, 79, f"生成元 {lab} 的邊", 13, INK2))
        lx += 150
    head.append(f'<rect x="{lx}" y="{68}" width="14" height="12" fill="{DOMAIN_FILL}" stroke="{INK}" stroke-width="2"/>')
    head.append(text(lx + 20, 79, "基本區域：每個面各一份；同字母的粗邊彼此黏合", 13, INK2))
    foot = [text(24, h - 34, f"每個頂點標的是它覆蓋的群元素；同一個元素在圓盤中出現多次，代表曲面上的同一點。"
                 f"已檢查 {len(tiles)} 個面、{complete} 個完整頂點的標籤與旋轉系統一致。", 12, INK2),
            text(24, h - 14, f"資料：data/surfaces/catalogue.json 的 {surface_id}；程式：experiments/draw_hyperbolic_surface.py", 11, MUTED),
            "</svg>"]
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{surface_id}.svg"
    out.write_text("\n".join(head + body + foot), encoding="utf-8")
    print(out, f"tiles={len(tiles)} complete_vertices={complete} boundary_pairs={len(by_edge)}")


if __name__ == "__main__":
    for sid in sys.argv[1:] or ["q8-g3-uniform"]:
        draw(sid)
