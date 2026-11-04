"""Exact integral homology of small free chain complexes, with certificates.

This module uses only Python integers and Fraction.  It computes integral
kernel bases before taking the incoming quotient; subtracting matrix ranks
alone would miss torsion and would not compute integral homology.

API: integral_homology({1: B1, 2: B2, 3: B3}, [c0, c1, c2, c3]).
Matrices are nested integer lists; dimensions specify even empty matrices.
"""
from __future__ import annotations

from fractions import Fraction


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(n):
    return [[int(i == j) for j in range(n)] for i in range(n)]


def zeros(rows, columns):
    return [[0] * columns for _ in range(rows)]


def checked_matrix(matrix, rows, columns):
    require(isinstance(matrix, (list, tuple)) and len(matrix) == rows,
            "Matrix row count disagrees with chain dimensions")
    require(all(isinstance(row, (list, tuple)) and len(row) == columns for row in matrix),
            "Matrix column count disagrees with chain dimensions")
    require(all(isinstance(value, int) and not isinstance(value, bool)
                for row in matrix for value in row), "Matrix entries must be integers")
    return [list(row) for row in matrix]


def multiply(left, right, columns):
    """Matrix product, with explicit output columns for an empty right matrix."""
    inner = len(right)
    require(all(len(row) == inner for row in left), "Product inner dimensions disagree")
    require(all(len(row) == columns for row in right), "Product columns disagree")
    return [[sum(row[k] * right[k][j] for k in range(inner))
             for j in range(columns)] for row in left]


def determinant(matrix):
    """Exact Bareiss determinant; the empty determinant is one."""
    n = len(matrix)
    a = checked_matrix(matrix, n, n)
    if n == 0:
        return 1
    sign, previous = 1, 1
    for k in range(n - 1):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            sign = -sign
        value = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = a[i][j] * value - a[i][k] * a[k][j]
                require(numerator % previous == 0, "Nonexact Bareiss division")
                a[i][j] = numerator // previous
            a[i][k] = 0
        previous = value
    return sign * a[-1][-1]


def inverse_unimodular(matrix):
    n = len(matrix)
    a = [[Fraction(x) for x in row] + [Fraction(int(i == j)) for j in range(n)]
         for i, row in enumerate(checked_matrix(matrix, n, n))]
    for j in range(n):
        pivot = next((i for i in range(j, n) if a[i][j]), None)
        require(pivot is not None, "Singular change of basis")
        a[j], a[pivot] = a[pivot], a[j]
        scale = a[j][j]
        a[j] = [x / scale for x in a[j]]
        for i in range(n):
            if i != j:
                scale = a[i][j]
                a[i] = [x - scale * y for x, y in zip(a[i], a[j])]
    answer = [row[n:] for row in a]
    require(all(x.denominator == 1 for row in answer for x in row),
            "Change of basis is not unimodular")
    return [[int(x) for x in row] for row in answer]


def smith_normal_form(matrix, n_columns=None):
    """Return integer U, V, D with U*A*V=D in Smith normal form.

    Euclidean row/column operations reduce each pivot.  If the pivot does
    not divide a remaining entry, bringing that entry into its row forces
    another gcd reduction.  All operations are elementary unimodular ones.
    """
    m = len(matrix)
    n = len(matrix[0]) if m else (0 if n_columns is None else n_columns)
    if n_columns is not None:
        require(n == n_columns, "Smith column count disagrees")
    a = checked_matrix(matrix, m, n)
    u, v = identity(m), identity(n)

    def swap_rows(i, j):
        a[i], a[j] = a[j], a[i]
        u[i], u[j] = u[j], u[i]

    def add_row(i, j, coefficient):
        a[i] = [x + coefficient * y for x, y in zip(a[i], a[j])]
        u[i] = [x + coefficient * y for x, y in zip(u[i], u[j])]

    def swap_columns(i, j):
        for row in a:
            row[i], row[j] = row[j], row[i]
        for row in v:
            row[i], row[j] = row[j], row[i]

    def add_column(i, j, coefficient):
        for row in a:
            row[i] += coefficient * row[j]
        for row in v:
            row[i] += coefficient * row[j]

    for k in range(min(m, n)):
        nonzero = [(abs(a[i][j]), i, j)
                   for i in range(k, m) for j in range(k, n) if a[i][j]]
        if not nonzero:
            break
        _, i, j = min(nonzero)
        swap_rows(k, i)
        swap_columns(k, j)
        while True:
            column_entry = next((i for i in range(k + 1, m) if a[i][k]), None)
            if column_entry is not None:
                i = column_entry
                add_row(i, k, -(a[i][k] // a[k][k]))
                if a[i][k]:
                    swap_rows(i, k)
                continue
            row_entry = next((j for j in range(k + 1, n) if a[k][j]), None)
            if row_entry is not None:
                j = row_entry
                add_column(j, k, -(a[k][j] // a[k][k]))
                if a[k][j]:
                    swap_columns(j, k)
                continue
            obstruction = next(((i, j) for i in range(k + 1, m)
                                for j in range(k + 1, n) if a[i][j] % a[k][k]), None)
            if obstruction is None:
                break
            add_row(k, obstruction[0], 1)
        if a[k][k] < 0:
            a[k] = [-x for x in a[k]]
            u[k] = [-x for x in u[k]]
    diagonal = [a[i][i] for i in range(min(m, n)) if a[i][i]]
    result = {"rows": m, "columns": n, "U": u, "V": v, "D": a,
              "diagonal": diagonal, "rank": len(diagonal)}
    verify_smith(matrix, n, result)
    return result


def verify_smith(matrix, columns, certificate):
    """Check a Smith certificate by integer multiplication and determinants."""
    m = len(matrix)
    original = checked_matrix(matrix, m, columns)
    require(certificate["rows"] == m and certificate["columns"] == columns,
            "Smith certificate shape mismatch")
    u = checked_matrix(certificate["U"], m, m)
    v = checked_matrix(certificate["V"], columns, columns)
    d = checked_matrix(certificate["D"], m, columns)
    require(abs(determinant(u)) == 1 and abs(determinant(v)) == 1,
            "Smith transforms are not unimodular")
    require(multiply(multiply(u, original, columns), v, columns) == d,
            "Smith transform identity failed")
    require(all(value == 0 for i, row in enumerate(d)
                for j, value in enumerate(row) if i != j), "Smith result is not diagonal")
    diag = [d[i][i] for i in range(min(m, columns))]
    rank = sum(x != 0 for x in diag)
    require(all(x > 0 for x in diag[:rank]) and all(x == 0 for x in diag[rank:]),
            "Smith pivots must be positive before all zero pivots")
    require(all(b % a == 0 for a, b in zip(diag[:rank], diag[1:rank])),
            "Smith pivots do not form a divisibility chain")
    require(certificate["diagonal"] == diag[:rank] and certificate["rank"] == rank,
            "Smith diagonal summary mismatch")
    return True


def group_label(free_rank, torsion):
    pieces = ([] if free_rank == 0 else ["Z" if free_rank == 1 else f"Z^{free_rank}"])
    pieces += [f"Z/{value}" for value in torsion]
    return " + ".join(pieces) or "0"


def _chain_data(boundaries, dimensions):
    require(isinstance(dimensions, (list, tuple)) and len(dimensions) > 0,
            "At least C0 must be specified")
    require(all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in dimensions),
            "Chain dimensions must be nonnegative integers")
    dims = list(dimensions)
    maps = {0: []}
    for k in range(1, len(dims)):
        matrix = boundaries.get(k, boundaries.get(str(k)))
        require(matrix is not None, f"Missing boundary B{k}")
        maps[k] = checked_matrix(matrix, dims[k - 1], dims[k])
    maps[len(dims)] = zeros(dims[-1], 0)
    checks = []
    for k in range(2, len(dims)):
        product = multiply(maps[k - 1], maps[k], dims[k])
        require(not any(x for row in product for x in row), f"B{k - 1} * B{k} is nonzero")
        checks.append({"product": f"B{k - 1}B{k}", "zero": True})
    return dims, maps, checks


def integral_homology(boundaries, dimensions):
    """Compute H_k=ker(B_k)/im(B_{k+1}) over Z, including torsion."""
    dims, maps, checks = _chain_data(boundaries, dimensions)
    groups, certificates = {}, {}
    for k, dim in enumerate(dims):
        outgoing = smith_normal_form(maps[k], dim)
        rank = outgoing["rank"]
        kernel = [row[rank:] for row in outgoing["V"]]
        incoming_columns = dims[k + 1] if k + 1 < len(dims) else 0
        coordinates = multiply(inverse_unimodular(outgoing["V"]), maps[k + 1], incoming_columns)
        require(not any(x for row in coordinates[:rank] for x in row),
                "Incoming image does not lie in the integral kernel")
        inside = coordinates[rank:]
        quotient = smith_normal_form(inside, incoming_columns)
        free_rank = dim - rank - quotient["rank"]
        torsion = [x for x in quotient["diagonal"] if x > 1]
        groups[f"H{k}"] = {"free_rank": free_rank, "torsion": torsion,
                            "label": group_label(free_rank, torsion)}
        certificates[f"H{k}"] = {"outgoing_smith": outgoing, "kernel_basis": kernel,
                                  "incoming_in_kernel": inside, "quotient_smith": quotient}
    result = {"coefficients": "Z", "dimensions": dims, "chain_checks": checks,
              "groups": groups, "certificates": certificates,
              "method": "Unimodular Smith reduction, integral kernel basis, incoming quotient."}
    verify_homology(boundaries, dims, result)
    return result


def verify_homology(boundaries, dimensions, result):
    """Verify saved homology certificates without running Smith reduction."""
    dims, maps, checks = _chain_data(boundaries, dimensions)
    require(result["coefficients"] == "Z" and result["dimensions"] == dims,
            "Homology coefficient/dimension mismatch")
    require(result["chain_checks"] == checks, "Chain check summary mismatch")
    require(set(result["groups"]) == {f"H{k}" for k in range(len(dims))},
            "Homology degrees mismatch")
    require(set(result["certificates"]) == set(result["groups"]), "Certificate degrees mismatch")
    for k, dim in enumerate(dims):
        cert = result["certificates"][f"H{k}"]
        outgoing = cert["outgoing_smith"]
        verify_smith(maps[k], dim, outgoing)
        rank = outgoing["rank"]
        kernel = [row[rank:] for row in outgoing["V"]]
        require(cert["kernel_basis"] == kernel, "Integral kernel basis mismatch")
        incoming_columns = dims[k + 1] if k + 1 < len(dims) else 0
        inside = checked_matrix(cert["incoming_in_kernel"], dim - rank, incoming_columns)
        require(multiply(kernel, inside, incoming_columns) == maps[k + 1],
                "Incoming image/kernel coordinates mismatch")
        verify_smith(inside, incoming_columns, cert["quotient_smith"])
        q = cert["quotient_smith"]
        free_rank = dim - rank - q["rank"]
        torsion = [x for x in q["diagonal"] if x > 1]
        expected = {"free_rank": free_rank, "torsion": torsion,
                    "label": group_label(free_rank, torsion)}
        require(result["groups"][f"H{k}"] == expected, "Homology group summary mismatch")
    return True
