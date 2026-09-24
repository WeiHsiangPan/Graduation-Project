"""Legacy Plotly drawings for selected Cayley-graph face systems.

This module is a visualization helper, not the authoritative surface registry.
All coordinates are placed on one torus background for display, even when the
verified cellulation has genus 0, 2, 3, or 4. Topological claims must come from
data/surfaces/catalogue.json and handbook/verify_examples.py.

所有例子統一使用相同的視覺設計：
  - 半透明灰色 torus 曲面作為背景
  - 每個 face 的邊界用一條彩色曲線在 torus 上描繪
  - 每條生成元的邊用不同顏色畫出
  - 頂點用黑色球標出，旁邊標上群元素名稱

uniform_rotation_embeddings enumerates only the Cayley-equivariant subclass
where every vertex has the same cyclic generator order. It is not an exhaustive
enumerator of all local rotation systems.
"""

# ── 安裝 (Colab 通常已有，保險起見) ──────────────────────────────────────
# !pip install plotly numpy -q

import numpy as np
import plotly.graph_objects as go
from itertools import permutations
from collections import defaultdict, Counter

pi = np.pi

# ══════════════════════════════════════════════════════════════════════════
# §1  Torus geometry
# ══════════════════════════════════════════════════════════════════════════

R_BIG  = 2.2   # 甜甜圈大半徑
R_TUBE = 0.85  # 甜甜圈管半徑

def torus_xyz(u, v):
    """(u,v) ∈ [0,2π)² → (x,y,z) on the torus surface."""
    x = (R_BIG + R_TUBE * np.cos(v)) * np.cos(u)
    y = (R_BIG + R_TUBE * np.cos(v)) * np.sin(u)
    z = R_TUBE * np.sin(v)
    return x, y, z

def arc_on_torus(p0, p1, n=80):
    """
    Shortest geodesic arc from p0=(u0,v0) to p1=(u1,v1)
    on the flat torus [0,2π)², then lift to 3D.
    Returns arrays (x, y, z).
    """
    u0, v0 = p0
    u1, v1 = p1
    du = u1 - u0
    dv = v1 - v0
    if du >  pi: du -= 2*pi
    if du < -pi: du += 2*pi
    if dv >  pi: dv -= 2*pi
    if dv < -pi: dv += 2*pi
    t = np.linspace(0, 1, n)
    u = np.mod(u0 + t * du, 2*pi)
    v = np.mod(v0 + t * dv, 2*pi)
    return torus_xyz(u, v)

def torus_surface():
    """Return Surface trace for the background torus."""
    uu = np.linspace(0, 2*pi, 90)
    vv = np.linspace(0, 2*pi, 60)
    U, V = np.meshgrid(uu, vv)
    X, Y, Z = torus_xyz(U, V)
    return go.Surface(
        x=X, y=Y, z=Z,
        opacity=0.12,
        showscale=False,
        colorscale=[[0, "#d9d9d9"], [1, "#d9d9d9"]],
        hoverinfo="skip",
        name="torus",
    )

# ══════════════════════════════════════════════════════════════════════════
# §2  Colour palette
# ══════════════════════════════════════════════════════════════════════════

FACE_COLORS = [
    "#ef4444",  # red
    "#f59e0b",  # amber
    "#38bdf8",  # sky
    "#84cc16",  # lime
    "#a78bfa",  # violet
    "#f472b6",  # pink
    "#34d399",  # emerald
    "#fb923c",  # orange
    "#60a5fa",  # blue
    "#facc15",  # yellow
    "#e879f9",  # fuchsia
    "#2dd4bf",  # teal
    "#f87171",  # rose
    "#4ade80",  # green
    "#818cf8",  # indigo
    "#fbbf24",  # warm yellow
]

EDGE_COLORS = ["#dc2626", "#2563eb", "#f97316", "#7c3aed", "#059669"]

# ══════════════════════════════════════════════════════════════════════════
# §3  Group definitions
# ══════════════════════════════════════════════════════════════════════════

def make_dihedral(n):
    el = [(r, f) for r in range(n) for f in range(2)]
    def m(a, b):
        r1,f1=a; r2,f2=b
        return (((r1-r2)%n, (f1+f2)%2) if f1 else ((r1+r2)%n, f2))
    e = (0, 0)
    mul = {(a,b): m(a,b) for a in el for b in el}
    inv = {a: next(b for b in el if m(a,b)==e) for a in el}
    return el, mul, inv, e

def make_s3():
    from itertools import permutations as P
    el = list(P([1,2,3])); e = (1,2,3)
    def m(a,b): return tuple(a[b[i]-1] for i in range(3))
    mul = {(a,b): m(a,b) for a in el for b in el}
    inv = {a: next(b for b in el if m(a,b)==e) for a in el}
    return el, mul, inv, e

def make_quaternion():
    el = ['1','-1','i','-i','j','-j','k','-k']
    t = {
      '1': {'1':'1','-1':'-1','i':'i','-i':'-i','j':'j','-j':'-j','k':'k','-k':'-k'},
      '-1':{'1':'-1','-1':'1','i':'-i','-i':'i','j':'-j','-j':'j','k':'-k','-k':'k'},
      'i': {'1':'i','-1':'-i','i':'-1','-i':'1','j':'k','-j':'-k','k':'-j','-k':'j'},
      '-i':{'1':'-i','-1':'i','i':'1','-i':'-1','j':'-k','-j':'k','k':'j','-k':'-j'},
      'j': {'1':'j','-1':'-j','i':'-k','-i':'k','j':'-1','-j':'1','k':'i','-k':'-i'},
      '-j':{'1':'-j','-1':'j','i':'k','-i':'-k','j':'1','-j':'-1','k':'-i','-k':'i'},
      'k': {'1':'k','-1':'-k','i':'j','-i':'-j','j':'-i','-j':'i','k':'-1','-k':'1'},
      '-k':{'1':'-k','-1':'k','i':'-j','-i':'j','j':'i','-j':'-i','k':'1','-k':'-1'},
    }
    mul = {(a,b): t[a][b] for a in el for b in el}
    inv = {a: next(b for b in el if t[a][b]=='1') for a in el}
    return el, mul, inv, '1'

def make_znzm(n, m_):
    el = [(a,b) for a in range(n) for b in range(m_)]
    mul = {(x,y): ((x[0]+y[0])%n,(x[1]+y[1])%m_) for x in el for y in el}
    inv = {x: ((-x[0])%n,(-x[1])%m_) for x in el}
    return el, mul, inv, (0,0)

def make_z2z2z2():
    el = [(a,b,c) for a in range(2) for b in range(2) for c in range(2)]
    mul = {(x,y): ((x[0]+y[0])%2,(x[1]+y[1])%2,(x[2]+y[2])%2) for x in el for y in el}
    inv = {x: x for x in el}
    return el, mul, inv, (0,0,0)

def make_z2z4():
    return make_znzm(2, 4)

def make_a4():
    from itertools import permutations as P
    def par(p):
        n=len(p); v=[False]*n; s=0
        for i in range(n):
            if not v[i]:
                j=i; c=0
                while not v[j]: v[j]=True; j=p[j]; c+=1
                if c%2==0: s+=1
        return s%2
    el = [p for p in P(range(4)) if par(p)==0]; e = (0,1,2,3)
    def m(a,b): return tuple(a[b[i]] for i in range(4))
    mul = {(a,b): m(a,b) for a in el for b in el}
    inv = {a: next(b for b in el if m(a,b)==e) for a in el}
    return el, mul, inv, e

def make_s4():
    from itertools import permutations as P
    el = list(P(range(4))); e = (0,1,2,3)
    def m(a,b): return tuple(a[b[i]] for i in range(4))
    mul = {(a,b): m(a,b) for a in el for b in el}
    inv = {a: next(b for b in el if m(a,b)==e) for a in el}
    return el, mul, inv, e

# ══════════════════════════════════════════════════════════════════════════
# §4  Face system construction
# ══════════════════════════════════════════════════════════════════════════

def _canon_face(f):
    return min([f[i:]+f[:i] for i in range(len(f))]+
               [f[::-1][i:]+f[::-1][:i] for i in range(len(f))])

def faces_from_relator_word(elems, mul, word):
    """
    Build the G-orbit of faces from a relator word.
    word = list of generators; the product must equal e for every start.
    """
    seen = set(); faces = []
    for start in elems:
        cur = start; path = [cur]
        for gen in word:
            cur = mul[(cur, gen)]; path.append(cur)
        key = _canon_face(tuple(path[:-1]))
        if key not in seen:
            seen.add(key); faces.append(tuple(path[:-1]))
    return faces

def _embed_rotation_system(elems, mul, inv, S, sig_e):
    n = len(sig_e)
    sm = {sig_e[i]: sig_e[(i+1)%n] for i in range(n)}
    if any(inv[s] not in set(S) for s in S): return None
    def sa(d):
        g,s = d; rev=(mul[(g,s)], inv[s]); gr,sr=rev
        return (gr, sm[sr])
    all_d = [(g,s) for g in elems for s in S]
    vis = set(); faces = []
    for st in all_d:
        if st in vis: continue
        face = []; cur = st
        while cur not in vis:
            vis.add(cur); face.append(cur); cur=sa(cur)
        if cur != st: return None
        faces.append(face)
    fv = []
    for f in faces:
        v = tuple(g for g,s in f)
        if len(set(v)) != len(v): return None
        fv.append(v)
    return fv

def _check_lk(fv, e):
    ef = [(i,f) for i,f in enumerate(fv) if e in f]
    if not ef: return False
    fo={}; fi_={}
    for idx,f in ef:
        k=f.index(e); nn=len(f)
        fo[idx]=f[(k+1)%nn]; fi_[idx]=f[(k-1)%nn]
    ii={v:i for i,v in fi_.items()}
    s=ef[0][0]; c=s; vis=[]
    for _ in range(len(ef)+2):
        if c in vis: break
        vis.append(c)
        nxt=ii.get(fo.get(c))
        if nxt is None: return False
        c=nxt
    return set(vis)=={i for i,_ in ef}

def uniform_rotation_embeddings(elems, mul, inv, e, S):
    """Enumerate valid embeddings with one generator rotation at every vertex."""
    seen=set(); results=[]
    first=S[0]; rest=S[1:]
    for perm in permutations(rest):
        sig=(first,)+perm
        fv=_embed_rotation_system(elems,mul,inv,S,sig)
        if fv is None: continue
        if not _check_lk(fv,e): continue
        key=frozenset(_canon_face(f) for f in fv)
        if key in seen: continue
        seen.add(key); results.append(fv)
    return results

# ══════════════════════════════════════════════════════════════════════════
# §5  Vertex placement on the torus  [0,2π)²
# ══════════════════════════════════════════════════════════════════════════

def place_grid(elems):
    """Generic: lay elements out on a regular grid on the torus."""
    n = len(elems)
    cols = int(np.ceil(np.sqrt(n)))
    coords = {}
    for i, g in enumerate(elems):
        row = i // cols
        col = i % cols
        u = 2*pi * (col + 0.5) / cols
        v = 2*pi * (row + 0.5) / (int(np.ceil(n/cols)))
        coords[g] = (u, v)
    return coords

def place_znzm(n, m_):
    """Z_n × Z_m: natural grid placement."""
    coords = {}
    for a in range(n):
        for b in range(m_):
            u = 2*pi * a / n
            v = 2*pi * b / m_
            coords[(a,b)] = (u, v)
    return coords

def place_d4_torus():
    """D4 torus: exact placement matching the reference image."""
    return {
        (0,0): (8*pi/7,   pi),       # e
        (1,0): (6*pi/7,   3*pi/2),   # r
        (2,0): (8*pi/7,   0),        # r²
        (3,0): (6*pi/7,   pi/2),     # r³
        (0,1): (0,        pi),       # s
        (1,1): (2*pi/7,   pi/2),     # rs
        (2,1): (0,        0),        # r²s
        (3,1): (2*pi/7,   3*pi/2),   # r³s
    }

def place_dihedral(n):
    """D_n: rotations on outer ring, reflections on inner ring."""
    coords = {}
    for k in range(n):
        u = 2*pi * k / n
        coords[(k,0)] = (u, pi/2)       # rotations: v = π/2
        coords[(k,1)] = (u + pi/n, 3*pi/2)  # reflections: v = 3π/2
    return coords

def place_s3():
    """S3: 6 elements, like D3 but labelled as permutations."""
    el, *_ = make_s3()
    return place_grid(el)

def place_a4():
    """A4: 12 elements on grid."""
    el, *_ = make_a4()
    return place_grid(el)

def place_s4():
    """S4: 24 elements on grid."""
    el, *_ = make_s4()
    return place_grid(el)

def place_quaternion():
    """Q8: arrange as 2 rings of 4."""
    el = ['1','-1','i','-i','j','-j','k','-k']
    ring1 = ['1',  'i',  'j',  'k' ]  # upper ring
    ring2 = ['-1', '-i', '-j', '-k']  # lower ring
    coords = {}
    for idx,g in enumerate(ring1):
        coords[g] = (2*pi*idx/4, pi/2)
    for idx,g in enumerate(ring2):
        coords[g] = (2*pi*idx/4 + pi/4, 3*pi/2)
    return coords

def place_z2z2z2():
    """Z2^3: 8 elements, spread evenly."""
    el = [(a,b,c) for a in range(2) for b in range(2) for c in range(2)]
    coords = {}
    for i,(a,b,c) in enumerate(el):
        u = 2*pi * (4*a + 2*b + c) / 8
        v = pi/2 + pi * (a^b^c)   # alternate between two rings
        coords[(a,b,c)] = (u, v)
    return coords

def place_z2z4():
    """Z2 × Z4: natural grid."""
    coords = {}
    for a in range(2):
        for b in range(4):
            u = 2*pi * a / 2
            v = 2*pi * b / 4
            coords[(a,b)] = (u, v)
    return coords

# ══════════════════════════════════════════════════════════════════════════
# §6  Core drawing engine
# ══════════════════════════════════════════════════════════════════════════

def draw_on_torus(title, elems, mul, inv, S, face_list, uv_coords,
                  gen_labels=None, show=True):
    """
    Draw a Cayley graph embedding on the torus surface.

    Parameters
    ----------
    title      : str  — plot title
    elems      : list — group elements
    mul        : dict — (g,h) → g*h
    inv        : dict — g → g^{-1}
    S          : list — generating set
    face_list  : list of tuples — each tuple is a sequence of group elements
                 forming the boundary of one face
    uv_coords  : dict — g → (u,v) in [0,2π)²
    gen_labels : dict — generator → display string (optional)
    show       : bool — call fig.show() if True

    Returns plotly Figure.
    """
    V_count  = len(elems)
    E_count  = V_count * len(S) // 2
    F_count  = len(face_list)
    chi      = V_count - E_count + F_count
    g_val    = 1 - chi // 2
    surf_str = ("Sphere" if chi == 2 else
                "Torus"  if chi == 0 else
                f"Genus-{g_val}")

    fig = go.Figure()
    fig.add_trace(torus_surface())

    # ── face boundary cycles ────────────────────────────────────────────
    for fi, face in enumerate(face_list):
        col = FACE_COLORS[fi % len(FACE_COLORS)]
        cycle = list(face) + [face[0]]
        xs, ys, zs = [], [], []
        for a, b in zip(cycle[:-1], cycle[1:]):
            x, y, z = arc_on_torus(uv_coords[a], uv_coords[b])
            xs.extend(list(x) + [None])
            ys.extend(list(y) + [None])
            zs.extend(list(z) + [None])
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color=col, width=7),
            name=f"F{fi}  ({len(face)}g)",
            hoverinfo="skip",
        ))

    # ── edges ───────────────────────────────────────────────────────────
    S_set = set(S)
    drawn = set()
    gen_groups = []
    seen_s = set()
    for s in S:
        if s in seen_s: continue
        grp = [s]
        si = inv[s]
        if si != s and si in S_set:
            grp.append(si); seen_s.add(si)
        seen_s.add(s)
        gen_groups.append(grp)

    idx_map = {g: i for i,g in enumerate(elems)}
    for gi, grp in enumerate(gen_groups):
        col = EDGE_COLORS[gi % len(EDGE_COLORS)]
        lbl = (gen_labels[grp[0]] if gen_labels and grp[0] in gen_labels
               else str(grp[0]))
        xs, ys, zs = [], [], []
        for g in elems:
            for s in grp:
                h = mul[(g, s)]
                key = frozenset([idx_map[g], idx_map[h]])
                if key in drawn: continue
                drawn.add(key)
                x, y, z = arc_on_torus(uv_coords[g], uv_coords[h])
                xs.extend(list(x) + [None])
                ys.extend(list(y) + [None])
                zs.extend(list(z) + [None])
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode="lines",
            line=dict(color=col, width=4),
            name=f"gen {lbl}",
            hoverinfo="skip",
        ))

    # ── vertices ────────────────────────────────────────────────────────
    vx, vy, vz, vtxt = [], [], [], []
    for g in elems:
        x, y, z = torus_xyz(*uv_coords[g])
        vx.append(x); vy.append(y); vz.append(z)
        vtxt.append(str(g))
    fig.add_trace(go.Scatter3d(
        x=vx, y=vy, z=vz,
        mode="markers+text",
        marker=dict(size=5, color="black"),
        text=vtxt,
        textposition="top center",
        textfont=dict(size=10),
        showlegend=False,
        hoverinfo="skip",
    ))

    # ── layout ──────────────────────────────────────────────────────────
    face_summary = "+".join(f"{c}×{p}g" for p,c in
                            sorted(Counter(len(f) for f in face_list).items()))
    fig.update_layout(
        title=(f"{title}<br>"
               f"<sup>V={V_count}  E={E_count}  F={F_count}  χ={chi}  "
               f"({surf_str})  ·  faces: {face_summary}</sup>"),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="data",
        ),
        width=950, height=750,
        margin=dict(l=0, r=0, b=0, t=80),
        legend=dict(x=0.82, y=0.95, font=dict(size=11)),
    )
    if show:
        fig.show()
    return fig

# ══════════════════════════════════════════════════════════════════════════
# §7  Legacy visualization gallery (15 views; not the full catalogue)
# ══════════════════════════════════════════════════════════════════════════

# ─── 1. S3 sphere ────────────────────────────────────────────────────────
def example_01_S3():
    el, mu, iv, e = make_s3()
    r=(2,3,1); ri=(3,1,2); s=(2,1,3)
    S = [r, ri, s]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    fv = embs[0]   # first distinct uniform-rotation surface
    uv = place_s3()
    lbl = {g: "".join(str(x) for x in g) for g in el}
    uv_named = {g: uv[g] for g in el}
    return draw_on_torus(
        "S₃  —  S = {r, r⁻¹, s}",
        el, mu, iv, S, fv, uv_named,
        gen_labels={r:"r", ri:"r⁻¹", s:"s"},
    )

# ─── 2. D4 sphere ────────────────────────────────────────────────────────
def example_02_D4_sphere():
    el, mu, iv, e = make_dihedral(4)
    r=(1,0); ri=(3,0); s=(0,1)
    S = [r, ri, s]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    # the uniform-rotation subclass yields the sphere here
    fv = embs[0]
    uv = place_dihedral(4)
    return draw_on_torus(
        "D₄  —  S = {r, r⁻¹, s}  (sphere)",
        el, mu, iv, S, fv, uv,
        gen_labels={r:"r", ri:"r⁻¹", s:"s"},
    )

# ─── 3. D4 torus ─────────────────────────────────────────────────────────
def example_03_D4_torus():
    el, mu, iv, e = make_dihedral(4)
    r=(1,0); ri=(3,0); s=(0,1)
    S = [r, ri, s]
    # hexagonal relator: r r s r r s = e
    fv = faces_from_relator_word(el, mu, [r, r, s, r, r, s])
    uv = place_d4_torus()   # exact coordinates from the reference image
    return draw_on_torus(
        "D₄  —  S = {r, r⁻¹, s}  (torus, hexagonal faces)",
        el, mu, iv, S, fv, uv,
        gen_labels={r:"r", ri:"r⁻¹", s:"s"},
    )

# ─── 4. A4 sphere ────────────────────────────────────────────────────────
def example_04_A4():
    el, mu, iv, e = make_a4()
    r3=(1,2,0,3); r3i=(2,0,1,3); s2=(1,0,3,2)
    S = [r3, r3i, s2]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    fv = embs[0]
    uv = place_a4()
    return draw_on_torus(
        "A₄  —  S = {r₃, r₃⁻¹, s₂}",
        el, mu, iv, S, fv, uv,
        gen_labels={r3:"r₃", r3i:"r₃⁻¹", s2:"s₂"},
    )

# ─── 5. D6 sphere ────────────────────────────────────────────────────────
def example_05_D6():
    el, mu, iv, e = make_dihedral(6)
    r=(1,0); ri=(5,0); s=(0,1)
    S = [r, ri, s]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    fv = embs[0]
    uv = place_dihedral(6)
    return draw_on_torus(
        "D₆  —  S = {r, r⁻¹, s}",
        el, mu, iv, S, fv, uv,
        gen_labels={r:"r", ri:"r⁻¹", s:"s"},
    )

# ─── 6. S4 uniform rotation (verified genus 4, not a sphere) ─────────────
def example_06_S4():
    el, mu, iv, e = make_s4()
    s12=(1,0,2,3); s23=(0,2,1,3); s34=(0,1,3,2)
    S = [s12, s23, s34]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    fv = embs[0]
    uv = place_s4()
    return draw_on_torus(
        "S₄  —  uniform rotation (genus 4; 6 dodecagons)",
        el, mu, iv, S, fv, uv,
        gen_labels={s12:"(12)", s23:"(23)", s34:"(34)"},
    )

# ─── 7. Z2^3 torus ───────────────────────────────────────────────────────
def example_07_Z2cubed():
    el, mu, iv, e = make_z2z2z2()
    e1=(1,0,0); e2=(0,1,0); e3=(0,0,1)
    S = [e1, e2, e3]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    fv = embs[0]   # one torus embedding
    uv = place_z2z2z2()
    return draw_on_torus(
        "ℤ₂³  —  S = {e₁, e₂, e₃}",
        el, mu, iv, S, fv, uv,
        gen_labels={e1:"e₁", e2:"e₂", e3:"e₃"},
    )

# ─── 8-10. Z3×Z3 torus (3 embeddings) ────────────────────────────────────
def example_08_Z3Z3(embedding_idx=0):
    el, mu, iv, e = make_znzm(3, 3)
    a1=(1,0); a2=(2,0); b1=(0,1); b2=(0,2)
    S = [a1, a2, b1, b2]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    fv = embs[embedding_idx]
    uv = place_znzm(3, 3)
    sc = Counter(len(f) for f in fv)
    fd = "+".join(f"{c}×{p}g" for p,c in sorted(sc.items()))
    return draw_on_torus(
        f"ℤ₃×ℤ₃  —  embedding {embedding_idx+1}  ({fd})",
        el, mu, iv, S, fv, uv,
        gen_labels={a1:"(1,0)", a2:"(2,0)", b1:"(0,1)", b2:"(0,2)"},
    )

def example_08_Z3Z3_v1(): return example_08_Z3Z3(0)
def example_09_Z3Z3_v2(): return example_08_Z3Z3(1)
def example_10_Z3Z3_v3(): return example_08_Z3Z3(2)

# ─── 11. Z4×Z4 torus ─────────────────────────────────────────────────────
def example_11_Z4Z4_torus():
    el, mu, iv, e = make_znzm(4, 4)
    a1=(1,0); a3=(3,0); b1=(0,1); b3=(0,3)
    S = [a1, a3, b1, b3]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    V,E_c = 16, 32
    torus_embs = [fv for fv in embs if V-E_c+len(fv)==0]
    fv = torus_embs[0]
    uv = place_znzm(4, 4)
    return draw_on_torus(
        "ℤ₄×ℤ₄  —  torus embedding  (16×4g)",
        el, mu, iv, S, fv, uv,
        gen_labels={a1:"(1,0)", a3:"(3,0)", b1:"(0,1)", b3:"(0,3)"},
    )

# ─── 12. Z2×Z4 torus ─────────────────────────────────────────────────────
def example_12_Z2Z4():
    el, mu, iv, e = make_z2z4()
    g1=(0,1); g3=(0,3); g2=(1,0)
    S = [g1, g3, g2]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    V,E_c = 8, 12
    torus_embs = [fv for fv in embs if V-E_c+len(fv)==0] or embs[:1]
    fv = torus_embs[0]
    uv = place_z2z4()
    return draw_on_torus(
        "ℤ₂×ℤ₄  —  S = {(0,1),(0,3),(1,0)}",
        el, mu, iv, S, fv, uv,
        gen_labels={g1:"(0,1)", g3:"(0,3)", g2:"(1,0)"},
    )

# ─── 13-15. Q8 (2× Genus-2,  1× Genus-3) ────────────────────────────────
def example_Q8(embedding_idx=0):
    el, mu, iv, e = make_quaternion()
    S = ['i','-i','j','-j']
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    fv = embs[embedding_idx]
    uv = place_quaternion()
    sc = Counter(len(f) for f in fv)
    fd = "+".join(f"{c}×{p}g" for p,c in sorted(sc.items()))
    V,E_c = 8,16; chi = V-E_c+len(fv); g_val = 1-chi//2
    return draw_on_torus(
        f"Q₈  —  embedding {embedding_idx+1}  ({fd},  genus {g_val})",
        el, mu, iv, S, fv, uv,
        gen_labels={'i':"i", '-i':"-i", 'j':"j", '-j':"-j"},
    )

def example_13_Q8_g2a(): return example_Q8(0)
def example_14_Q8_g2b(): return example_Q8(1)
def example_15_Q8_g3():  return example_Q8(2)

# ─── Z4×Z4 genus-3 embeddings ─────────────────────────────────────────
def example_Z4Z4_genus3(embedding_idx=0):
    el, mu, iv, e = make_znzm(4, 4)
    a1=(1,0); a3=(3,0); b1=(0,1); b3=(0,3)
    S = [a1, a3, b1, b3]
    embs = uniform_rotation_embeddings(el, mu, iv, e, S)
    V,E_c = 16, 32
    g3_embs = [fv for fv in embs if V-E_c+len(fv)==-4]
    fv = g3_embs[embedding_idx]
    uv = place_znzm(4, 4)
    sc = Counter(len(f) for f in fv)
    fd = "+".join(f"{c}×{p}g" for p,c in sorted(sc.items()))
    return draw_on_torus(
        f"ℤ₄×ℤ₄  —  genus-3 embedding {embedding_idx+1}  ({fd})",
        el, mu, iv, S, fv, uv,
        gen_labels={a1:"(1,0)", a3:"(3,0)", b1:"(0,1)", b3:"(0,3)"},
    )

# ══════════════════════════════════════════════════════════════════════════
# §8  Run the 15 legacy gallery views
# ══════════════════════════════════════════════════════════════════════════

ALL_EXAMPLES = [
    ("01  S₃            sphere",    example_01_S3),
    ("02  D₄            sphere",    example_02_D4_sphere),
    ("03  D₄            torus",     example_03_D4_torus),
    ("04  A₄            sphere",    example_04_A4),
    ("05  D₆            sphere",    example_05_D6),
    ("06  S₄            genus-4",   example_06_S4),
    ("07  ℤ₂³           torus",     example_07_Z2cubed),
    ("08  ℤ₃×ℤ₃  v1     torus",     example_08_Z3Z3_v1),
    ("09  ℤ₃×ℤ₃  v2     torus",     example_09_Z3Z3_v2),
    ("10  ℤ₃×ℤ₃  v3     torus",     example_10_Z3Z3_v3),
    ("11  ℤ₄×ℤ₄         torus",     example_11_Z4Z4_torus),
    ("12  ℤ₂×ℤ₄         torus",     example_12_Z2Z4),
    ("13  Q₈  emb 1     genus-2",   example_13_Q8_g2a),
    ("14  Q₈  emb 2     genus-2",   example_14_Q8_g2b),
    ("15  Q₈  emb 3     genus-3",   example_15_Q8_g3),
]

def run_all():
    """Run the 15 legacy visualization views in sequence."""
    for label, fn in ALL_EXAMPLES:
        print(f"\n{'─'*50}")
        print(f"  {label}")
        print(f"{'─'*50}")
        fn()

def run_one(n):
    """Run a single example by number (1-15)."""
    label, fn = ALL_EXAMPLES[n-1]
    print(f"Running: {label}")
    return fn()

# ══════════════════════════════════════════════════════════════════════════
# §9  Quick-start  (uncomment what you want in Colab)
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Run all 15:
    run_all()

    # Or run just one by index (1–15):
    # run_one(3)    # D4 torus  ← the reference image example

    # Individual functions:
    # example_01_S3()
    # example_02_D4_sphere()
    # example_03_D4_torus()
    # example_04_A4()
    # example_05_D6()
    # example_06_S4()
    # example_07_Z2cubed()
    # example_08_Z3Z3_v1()
    # example_09_Z3Z3_v2()
    # example_10_Z3Z3_v3()
    # example_11_Z4Z4_torus()
    # example_12_Z2Z4()
    # example_13_Q8_g2a()
    # example_14_Q8_g2b()
    # example_15_Q8_g3()
    # example_Z4Z4_genus3(0)
    # example_Z4Z4_genus3(1)
