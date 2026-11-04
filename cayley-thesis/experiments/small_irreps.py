"""Exact rational irreducible representations of D4, S3 and S4.

Matrices use column vectors and the multiplication convention of
``surface_systems``.  ``gram`` is the invariant inner product matrix;
nonorthogonal standard-representation bases are e_i-e_last.
"""
from fractions import Fraction


def _matrix(rows):
    return [[Fraction(x) for x in row] for row in rows]


def _identity(n):
    return _matrix([[int(i == j) for j in range(n)] for i in range(n)])


def _multiply(a, b):
    return [[sum((a[i][k] * b[k][j] for k in range(len(b))), Fraction(0))
             for j in range(len(b[0]))] for i in range(len(a))]


def _transpose(a):
    return [list(row) for row in zip(*a)]


def _standard(permutation):
    """Restrict e_j -> e_permutation[j] to the sum-zero subspace."""
    n = len(permutation)
    return _matrix([[int(permutation[j] == i) - int(permutation[-1] == i)
                     for j in range(n - 1)] for i in range(n - 1)])


def _standard_gram(n):
    return _matrix([[1 + int(i == j) for j in range(n)] for i in range(n)])


def _sign(p):
    return (-1) ** sum(p[i] > p[j] for i in range(len(p))
                       for j in range(i + 1, len(p)))


def _record(name, matrices, gram=None):
    dimension = len(matrices[0])
    return {"name": name, "dimension": dimension, "matrices": matrices,
            "gram": _identity(dimension) if gram is None else gram}


def representations(key, group):
    """Return all real rational irreps in the supplied element order.

    Construction is specific to the named catalogue group, not to arbitrary
    isomorphic encodings.  Validation certifies the full representation table.
    """
    elements = group["elements"]
    if key == "d4":
        if len(elements) != 8 or set(elements) != {(r, f) for r in range(4)
                                                       for f in range(2)}:
            raise ValueError("d4 requires the catalogue (rotation,flip) encoding")
        result = []
        for a, c, name in [(1, 1, "trivial"), (1, -1, "reflection_sign"),
                            (-1, 1, "rotation_sign"), (-1, -1, "rotation_reflection_sign")]:
            result.append(_record(name, [_matrix([[a ** r * c ** f]])
                                          for r, f in elements]))
        rotation = _matrix([[0, -1], [1, 0]])
        reflection = _matrix([[1, 0], [0, -1]])
        powers = [_identity(2)]
        for _ in range(3):
            powers.append(_multiply(powers[-1], rotation))
        result.append(_record("standard_2d", [_multiply(powers[r], reflection)
                                                if f else powers[r]
                                                for r, f in elements]))
    elif key in ("s3", "s4"):
        size = 3 if key == "s3" else 4
        if any(len(p) != size for p in elements):
            raise ValueError("Unexpected permutation size")
        offset = min(elements[0])
        permutations = [tuple(x - offset for x in p) for p in elements]
        if any(set(p) != set(range(size)) for p in permutations):
            raise ValueError("Invalid permutation encoding")
        signs = [_sign(p) for p in permutations]
        result = [_record("trivial", [_matrix([[1]]) for _ in elements]),
                  _record("sign", [_matrix([[s]]) for s in signs])]
        standard = [_standard(p) for p in permutations]
        result.append(_record(f"standard_{size - 1}d", standard,
                              _standard_gram(size - 1)))
        if size == 4:
            result.append(_record("sign_twist_3d",
                                  [[[s * x for x in row] for row in m]
                                   for s, m in zip(signs, standard)],
                                  _standard_gram(3)))
            # S4 permutes its three partitions into two unordered pairs.
            def matching(*pairs):
                return frozenset(frozenset(pair) for pair in pairs)

            matchings = [matching((0, 1), (2, 3)),
                         matching((0, 2), (1, 3)),
                         matching((0, 3), (1, 2))]
            quotient = []
            for p in permutations:
                action = tuple(matchings.index(frozenset(
                    frozenset(p[x] for x in pair) for pair in item))
                               for item in matchings)
                quotient.append(_standard(action))
            result.append(_record("matching_quotient_2d", quotient,
                                  _standard_gram(2)))
    else:
        raise ValueError(f"No exact representation table for {key!r}")
    validate(result, group)
    return result


def validate(reps, group):
    """Certify homomorphisms, metrics and completeness over exact rationals.

    Character norm one proves complex irreducibility; orthogonality proves
    inequivalence.  Sum d^2=|G| then proves no irreducibles are omitted.
    """
    elements = tuple(group["elements"])
    index = {g: i for i, g in enumerate(elements)}
    order = len(elements)
    if len(index) != order or not order:
        raise ValueError("Group elements must be nonempty and unique")
    names = [rep["name"] for rep in reps]
    if len(set(names)) != len(names):
        raise ValueError("Representation names must be unique")
    multiplication_checks = metric_checks = 0
    characters = []
    for rep in reps:
        d, matrices, gram = rep["dimension"], rep["matrices"], rep["gram"]
        if d < 1 or len(matrices) != order:
            raise ValueError("Representation dimension or element count mismatch")
        for m in [gram] + matrices:
            if len(m) != d or any(len(row) != d for row in m):
                raise ValueError("Matrix shape mismatch")
            if any(not isinstance(x, (int, Fraction)) for row in m for x in row):
                raise ValueError("Exact integer or Fraction entries required")
        if gram != _transpose(gram):
            raise ValueError("Gram matrix is not symmetric")
        # Exact LDL elimination certifies positive definiteness.
        work = _matrix(gram)
        for k in range(d):
            pivot = work[k][k]
            if pivot <= 0:
                raise ValueError("Gram matrix is not positive definite")
            for i in range(k + 1, d):
                for j in range(k + 1, d):
                    work[i][j] -= work[i][k] * work[k][j] / pivot
        if matrices[index[group["identity"]]] != _identity(d):
            raise ValueError("Identity has incorrect representation matrix")
        for i, a in enumerate(elements):
            m = matrices[i]
            if _multiply(_multiply(_transpose(m), gram), m) != gram:
                raise ValueError(f"Invariant metric failed for {rep['name']}")
            metric_checks += 1
            for j, b in enumerate(elements):
                if _multiply(m, matrices[j]) != matrices[index[group["mul"][a, b]]]:
                    raise ValueError(f"Homomorphism failed for {rep['name']}")
                multiplication_checks += 1
        characters.append([sum((m[i][i] for i in range(d)), Fraction(0))
                           for m in matrices])
    character_checks = 0
    for i, chi in enumerate(characters):
        for j, psi in enumerate(characters):
            inner = sum((a * b for a, b in zip(chi, psi)), Fraction(0)) / order
            if inner != int(i == j):
                raise ValueError("Character irreducibility/orthogonality failed")
            character_checks += 1
    dimension_square_sum = sum(rep["dimension"] ** 2 for rep in reps)
    if dimension_square_sum != order:
        raise ValueError("Representation table is incomplete")
    return {"group_order": order, "representation_count": len(reps),
            "dimension_square_sum": dimension_square_sum,
            "multiplication_checks": multiplication_checks,
            "metric_checks": metric_checks, "character_checks": character_checks}
