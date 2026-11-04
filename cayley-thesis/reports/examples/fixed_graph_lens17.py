"""Exact checks for a fixed-face-pairing-graph pair of lens spaces.

The layered construction is specified by Regina's public mathematical recipe:
https://github.com/regina-normal/regina/blob/master/engine/triangulation/example3.cpp
https://github.com/regina-normal/regina/blob/master/engine/triangulation/dim3/insertlayered.cpp

This is a standalone verifier, not a call to Regina and not a homeomorphism
recognition algorithm. Lens-space identification uses that construction recipe;
non-homeomorphism uses the classical lens-space classification theorem.
Only the Python standard library and NumPy are required.
"""

from collections import Counter, defaultdict, deque
from fractions import Fraction
from itertools import combinations, product
from math import gcd, lcm
from pathlib import Path
import json

import numpy as np


FACES = [tuple(v for v in range(4) if v != f) for f in range(4)]
EDGES = list(combinations(range(4), 2))


def parity(values):
    return (-1) ** sum(values[i] > values[j]
                       for i in range(len(values))
                       for j in range(i + 1, len(values)))


class SignedClasses:
    """Relations x = sign*y, retaining orientation consistency."""
    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.sign = {x: 1 for x in items}
        self.valid = True

    def find(self, x):
        if self.parent[x] == x:
            return x, 1
        root, s = self.find(self.parent[x])
        self.sign[x] *= s
        self.parent[x] = root
        return root, self.sign[x]

    def join(self, x, y, sign=1):
        rx, sx = self.find(x)
        ry, sy = self.find(y)
        if rx == ry:
            self.valid &= sx == sign * sy
        else:
            self.parent[rx] = ry
            self.sign[rx] = sign * sy * sx

    def groups(self):
        ans = defaultdict(list)
        for x in self.parent:
            ans[self.find(x)[0]].append(x)
        return dict(ans)


def layered_lens(p, q):
    """The standard (nondegenerate) layered recipe used for this pair."""
    assert p > 3 and 0 < 3*q <= p and gcd(p, q) == 1
    a, b = q, p - 2*q
    glues, branches = [], []
    current = 0
    while a + b > 3:
        nxt = current + 1
        if b-a > a:
            p2, p3 = (0, 2, 1, 3), (3, 1, 2, 0)
            a, b = a, b-a
            branches.append('A')
        else:
            p2, p3 = (3, 1, 0, 2), (0, 2, 3, 1)
            a, b = b-a, a
            branches.append('B')
        glues += [(nxt, 2, current, p2), (nxt, 3, current, p3)]
        current = nxt
    assert (a, b) == (1, 2)
    glues.append((current, 0, current, (1, 2, 3, 0)))
    glues.append((0, 3, 0, (3, 0, 1, 2)))
    return current + 1, glues, branches


def normalize_faces(n, glues, branches):
    """Make both examples have exactly the same labeled face pairs."""
    relabel = [(1, 0, 2, 3) if b == 'A' else (0, 1, 2, 3)
               for b in branches] + [(0, 1, 2, 3)]
    ans = []
    for t, f, s, p in glues:
        rt, rs = relabel[t], relabel[s]
        inv = tuple(rt.index(v) for v in range(4))
        transformed = tuple(rs[p[inv[v]]] for v in range(4))
        ans.append((t, rt[f], s, transformed))
    return ans


def analyse(n, glues):
    vertices = SignedClasses((t,v) for t in range(n) for v in range(4))
    edges = SignedClasses((t,a,b) for t in range(n) for a,b in EDGES)
    faces = SignedClasses((t,f) for t in range(n) for f in range(4))
    corners = SignedClasses((t,v,w) for t in range(n)
                            for v in range(4) for w in range(4) if v != w)
    sides = SignedClasses((t,v,f) for t in range(n)
                          for v in range(4) for f in range(4) if v != f)
    ports = SignedClasses((t,v,w,f) for t in range(n)
                          for v in range(4) for w in range(4) if v != w
                          for f in range(4) if f not in (v,w))
    paired = set()
    orientation_graph = defaultdict(list)
    for t, f, s, p in glues:
        g = p[f]
        assert (t,f) not in paired and (s,g) not in paired
        assert (t,f) != (s,g)
        paired.update(((t,f),(s,g)))
        orientation_graph[t].append((s, -parity(p)))
        orientation_graph[s].append((t, -parity(p)))
        image = [p[v] for v in FACES[f]]
        faces.join((t,f),(s,g),parity(image))
        for v in FACES[f]:
            vertices.join((t,v),(s,p[v]))
            sides.join((t,v,f),(s,p[v],g))
            for w in FACES[f]:
                if w != v:
                    corners.join((t,v,w),(s,p[v],p[w]))
                    ports.join((t,v,w,f),(s,p[v],p[w],g))
        for a,b in combinations(FACES[f],2):
            x,y = p[a],p[b]
            edges.join((t,a,b),(s,min(x,y),max(x,y)),1 if x < y else -1)

    tet_sign = {}
    orientable, components = True, 0
    for start in range(n):
        if start in tet_sign:
            continue
        components += 1
        tet_sign[start] = 1
        todo = [start]
        while todo:
            t = todo.pop()
            for s, relation in orientation_graph[t]:
                value = relation*tet_sign[t]
                if s in tet_sign:
                    orientable &= tet_sign[s] == value
                else:
                    tet_sign[s] = value
                    todo.append(s)

    boundary = [(t,f) for t in range(n) for f in range(4)
                if (t,f) not in paired]
    vertex_groups = vertices.groups()
    link_data = []
    for group in vertex_groups.values():
        cv = {corners.find((t,v,w))[0] for t,v in group
              for w in range(4) if w != v}
        ce = {sides.find((t,v,f))[0] for t,v in group
              for f in range(4) if f != v}
        boundary_edges = []
        for t,v in group:
            for f in range(4):
                if f != v and (t,f) not in paired:
                    others = [w for w in FACES[f] if w != v]
                    boundary_edges.append(tuple(corners.find((t,v,w))[0]
                                                for w in others))
        bclasses = SignedClasses(set(x for e in boundary_edges for x in e))
        degrees = Counter()
        for x,y in boundary_edges:
            bclasses.join(x,y)
            degrees[x] += 1
            degrees[y] += 1
        # Check the link of every vertex of this two-dimensional link.
        link_is_surface = all(d == 2 for d in degrees.values())
        for corner_group in corners.groups().values():
            if (corner_group[0][0],corner_group[0][1]) not in group:
                continue
            endpoint_edges = []
            for t,v,w in corner_group:
                fs = [f for f in range(4) if f not in (v,w)]
                endpoint_edges.append(tuple(ports.find((t,v,w,f))[0] for f in fs))
            local = SignedClasses(set(x for e in endpoint_edges for x in e))
            degree = Counter()
            for x,y in endpoint_edges:
                local.join(x,y); degree[x] += 1; degree[y] += 1
            ds = list(degree.values())
            link_is_surface &= len(local.groups()) == 1 and (
                all(d == 2 for d in ds) or
                (ds.count(1) == 2 and all(d in (1,2) for d in ds)))
        chi = len(cv)-len(ce)+len(group)
        b = len(bclasses.groups())
        link_data.append(dict(corners=group,V=len(cv),E=len(ce),F=len(group),
                              chi=chi,boundary_components=b,
                              is_surface=link_is_surface,
                              type=('sphere' if chi == 2 and b == 0 else
                                    'disk' if chi == 1 and b == 1 else 'other')))

    vr, er, fr = (sorted(c.groups()) for c in (vertices,edges,faces))
    vi, ei, fi = ({r:i for i,r in enumerate(rs)} for rs in (vr,er,fr))
    B1 = np.zeros((len(vr),len(er)),dtype=np.int64)
    B2 = np.zeros((len(er),len(fr)),dtype=np.int64)
    B3 = np.zeros((len(fr),n),dtype=np.int64)
    for root,j in ei.items():
        t,a,b = root
        B1[vi[vertices.find((t,a))[0]],j] -= 1
        B1[vi[vertices.find((t,b))[0]],j] += 1
    for root,j in fi.items():
        t,f = root
        a,b,c = FACES[f]
        for x,y,coefficient in [(b,c,1),(a,c,-1),(a,b,1)]:
            r,sgn = edges.find((t,x,y))
            B2[ei[r],j] += coefficient*sgn
    for t in range(n):
        for f in range(4):
            r,sgn = faces.find((t,f))
            B3[fi[r],t] += (-1)**f*sgn
    assert np.all(B1@B2 == 0) and np.all(B2@B3 == 0)

    edge_occurrences = defaultdict(list)
    for t,f in boundary:
        for a,b in combinations(FACES[f],2):
            r,sgn = edges.find((t,a,b))
            edge_occurrences[r].append((t,f,a,b,sgn))
    Ce = []
    for occurrences in edge_occurrences.values():
        assert len(occurrences) == 2
        x,y = sorted(occurrences)
        Ce.append([list(x[:4]),list(y[:4]),x[4] == y[4]])
    boundary_vertices = {(t,v) for t,f in boundary for v in FACES[f]}
    Cv = sorted(sorted(x for x in group if x in boundary_vertices)
                for group in vertex_groups.values() if any(x in boundary_vertices for x in group))
    return dict(f_vector=[len(vr),len(er),len(fr),n],connected=components == 1,
                orientable=orientable,boundary_faces=boundary,
                edge_orientation_consistent=edges.valid,links=link_data,
                boundary_state=dict(Ce=sorted(Ce),Cv=Cv),
                edge_basis=er,boundary_edge_coordinates=[
                    dict(tetrahedron=t,face=f,edge=[a,b],
                         basis_index=ei[edges.find((t,a,b))[0]],
                         sign=edges.find((t,a,b))[1])
                    for t,f in boundary for a,b in combinations(FACES[f],2)],
                B1=B1,B2=B2,B3=B3)


def determinant(rows):
    """Fraction-free Bareiss determinant."""
    a = [list(map(int,row)) for row in rows]
    n = len(a)
    if n == 0:
        return 1
    sign, previous = 1, 1
    for k in range(n-1):
        pivot = next((i for i in range(k,n) if a[i][k]),None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k],a[pivot] = a[pivot],a[k]; sign = -sign
        value = a[k][k]
        for i in range(k+1,n):
            for j in range(k+1,n):
                a[i][j] = (a[i][j]*value-a[i][k]*a[k][j])//previous
            a[i][k] = 0
        previous = value
    return sign*a[-1][-1]


def smith_factors(matrix):
    """Invariant factors from exact determinantal divisors, for small matrices."""
    m,n = matrix.shape
    previous, ans = 1, []
    for k in range(1,min(m,n)+1):
        divisor = 0
        done = False
        for rs in combinations(range(m),k):
            for cs in combinations(range(n),k):
                d = determinant([[matrix[r,c] for c in cs] for r in rs])
                divisor = gcd(divisor,abs(d))
                if divisor == previous:
                    done = True; break
            if done:
                break
        if divisor == 0:
            break
        assert divisor % previous == 0
        ans.append(divisor//previous)
        previous = divisor
    return ans


def face_pair_key(glues):
    return sorted(sorted(((t,f),(s,p[f]))) for t,f,s,p in glues)


def primitive_nullvector(matrix):
    """A primitive integral generator of a one-dimensional rational kernel."""
    a = [[Fraction(int(x)) for x in row] for row in matrix]
    nr,nc = len(a),len(a[0])
    row,pivots = 0,[]
    for col in range(nc):
        k = next((i for i in range(row,nr) if a[i][col]),None)
        if k is None:
            continue
        a[row],a[k] = a[k],a[row]
        z = a[row][col]
        a[row] = [x/z for x in a[row]]
        for i in range(nr):
            if i != row:
                z = a[i][col]
                a[i] = [x-z*y for x,y in zip(a[i],a[row])]
        pivots.append(col)
        row += 1
        if row == nr:
            break
    free = [i for i in range(nc) if i not in pivots]
    assert len(free) == 1
    v = [Fraction(0)]*nc
    v[free[0]] = 1
    for i,c in reversed(list(enumerate(pivots))):
        v[c] = -sum(a[i][j]*v[j] for j in free)
    den = lcm(*(x.denominator for x in v))
    v = [int(x*den) for x in v]
    divisor = gcd(*v)
    return [x//divisor for x in v]


def main():
    output = {}
    for q in [3,4]:
        n,raw,branches = layered_lens(17,q)
        glues = normalize_faces(n,raw,branches)
        full = analyse(n,glues)
        partial = analyse(n,glues[:-1])
        assert n == 5 and full['f_vector'] == [1,6,10,5]
        assert full['connected'] and full['orientable']
        assert full['edge_orientation_consistent'] and not full['boundary_faces']
        assert all(x['is_surface'] and x['type'] == 'sphere' for x in full['links'])
        assert all(x['is_surface'] and x['type'] == 'disk' for x in partial['links'])
        factors = smith_factors(full['B2'])
        assert factors == [1,1,1,1,1,17]
        full['smith_B2'] = factors
        full['smith_B3'] = smith_factors(full['B3'])
        L1 = full['B1'].T@full['B1']+full['B2']@full['B2'].T
        full['L1'] = L1
        full['L1_spectrum_numerical'] = np.linalg.eigvalsh(L1).tolist()
        full['glues'] = glues
        full['branches'] = branches
        full['partial'] = {k:partial[k] for k in
                           ['f_vector','links','boundary_faces','boundary_state']}
        assert smith_factors(partial['B2']) == [1]*6
        w = primitive_nullvector(partial['B2'].T)
        full['partial']['boundary_inclusion_to_Z'] = [
            dict(edge=e['edge'],value=e['sign']*w[e['basis_index']])
            for e in partial['boundary_edge_coordinates']
            if e['tetrahedron'] == 0 and e['face'] == 2]
        full['L1_trace_square_exact'] = int(np.trace(L1@L1))
        output[str(q)] = full
        print('L(17,%d)'%q,'branches',branches,'f',full['f_vector'],
              'B2_SNF',factors,'B3_SNF',full['smith_B3'])
        print('gluings',glues)
        print('partial state',partial['boundary_state'])
        print('boundary inclusion',full['partial']['boundary_inclusion_to_Z'])
        print('link',full['links'])
        print('B2',full['B2'].tolist())
        print('L1',L1.tolist(),'spectrum',np.round(full['L1_spectrum_numerical'],8))
    assert face_pair_key(output['3']['glues']) == face_pair_key(output['4']['glues'])
    assert output['3']['partial']['boundary_state'] == output['4']['partial']['boundary_state']
    assert output['3']['glues'][-1] == output['4']['glues'][-1]
    squares = sorted({a*a % 17 for a in range(1,17)})
    assert 12 not in squares and (-12)%17 not in squares
    output['checks'] = dict(same_labeled_face_pairs=True,same_partial_boundary_state=True,
                            same_final_gluing=True,nonzero_squares_mod17=squares,
                            homeomorphism_orbit_of_3=sorted({3,(-3)%17,pow(3,-1,17),(-pow(3,-1,17))%17}))
    family = []
    reference_pairs = face_pair_key(output['3']['glues'])
    for word in product('AB',repeat=4):
        a,b = 1,2
        for letter in reversed(word):
            a,b = (a,a+b) if letter == 'A' else (b,a+b)
        p,q = 2*a+b,a
        n,g,w = layered_lens(p,q)
        assert tuple(w) == word
        g = normalize_faces(n,g,w)
        assert face_pair_key(g) == reference_pairs
        result = analyse(n,g)
        assert result['connected'] and result['orientable']
        assert result['edge_orientation_consistent']
        assert all(x['is_surface'] and x['type'] == 'sphere' for x in result['links'])
        assert smith_factors(result['B2']) == [1,1,1,1,1,p]
        family.append(dict(word=''.join(word),p=p,q=q,H1_torsion_order=p))
    output['complete_restricted_family'] = family
    dest = Path(__file__).with_suffix('.json')
    dest.write_text(json.dumps(output,indent=2,default=lambda x:x.tolist()),encoding='utf-8')
    print('ALL CHECKS PASSED; output:',dest)


if __name__ == '__main__':
    main()
