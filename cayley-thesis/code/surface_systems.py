"""Core finite-group and rotation-system utilities for the Cayley-surface project.

The important distinction in this module is:

* a relator-orbit construction is a convenient source of candidate faces;
* a uniform rotation uses one cyclic generator order at every vertex;
* a general rotation system chooses a cyclic order independently at every vertex.

Only the last model is complete for orientable cellular embeddings of a fixed
Cayley graph.  All public constructors return oriented face cycles, which are
then checked by :func:`validate_surface`.
"""

from __future__ import annotations

from collections import Counter, deque
from itertools import permutations, product
from math import factorial


class SurfaceError(ValueError):
    """Raised when group, rotation, or face data are inconsistent."""


def _permutation_parity(permutation):
    inversions = 0
    for i, value in enumerate(permutation):
        for later in permutation[i + 1 :]:
            inversions += value > later
    return inversions % 2


def make_dihedral(n):
    elements = [(rotation, flip) for rotation in range(n) for flip in range(2)]

    def multiply(left, right):
        r1, f1 = left
        r2, f2 = right
        if f1:
            return ((r1 - r2) % n, (f1 + f2) % 2)
        return ((r1 + r2) % n, f2)

    return _finish_group(f"D{n}", elements, multiply, (0, 0))


def make_znzm(n, m):
    elements = [(a, b) for a in range(n) for b in range(m)]

    def multiply(left, right):
        return ((left[0] + right[0]) % n, (left[1] + right[1]) % m)

    return _finish_group(f"Z{n}xZ{m}", elements, multiply, (0, 0))


def make_z2_cubed():
    elements = [
        (a, b, c)
        for a in range(2)
        for b in range(2)
        for c in range(2)
    ]

    def multiply(left, right):
        return tuple((x + y) % 2 for x, y in zip(left, right))

    return _finish_group("Z2^3", elements, multiply, (0, 0, 0))


def make_permutation_group(size, even_only=False, one_based=False, name=None):
    base = tuple(range(1, size + 1)) if one_based else tuple(range(size))
    offset = 1 if one_based else 0
    elements = [
        permutation
        for permutation in permutations(base)
        if not even_only
        or _permutation_parity(tuple(value - offset for value in permutation)) == 0
    ]

    def multiply(left, right):
        return tuple(left[right[index] - offset] for index in range(size))

    default_name = f"A{size}" if even_only else f"S{size}"
    return _finish_group(name or default_name, elements, multiply, base)


def make_q8():
    elements = ["1", "-1", "i", "-i", "j", "-j", "k", "-k"]
    table = {
        "1": {"1": "1", "-1": "-1", "i": "i", "-i": "-i", "j": "j", "-j": "-j", "k": "k", "-k": "-k"},
        "-1": {"1": "-1", "-1": "1", "i": "-i", "-i": "i", "j": "-j", "-j": "j", "k": "-k", "-k": "k"},
        "i": {"1": "i", "-1": "-i", "i": "-1", "-i": "1", "j": "k", "-j": "-k", "k": "-j", "-k": "j"},
        "-i": {"1": "-i", "-1": "i", "i": "1", "-i": "-1", "j": "-k", "-j": "k", "k": "j", "-k": "-j"},
        "j": {"1": "j", "-1": "-j", "i": "-k", "-i": "k", "j": "-1", "-j": "1", "k": "i", "-k": "-i"},
        "-j": {"1": "-j", "-1": "j", "i": "k", "-i": "-k", "j": "1", "-j": "-1", "k": "-i", "-k": "i"},
        "k": {"1": "k", "-1": "-k", "i": "j", "-i": "-j", "j": "-i", "-j": "i", "k": "-1", "-k": "1"},
        "-k": {"1": "-k", "-1": "k", "i": "-j", "-i": "j", "j": "i", "-j": "-i", "k": "1", "-k": "-1"},
    }
    return _finish_group("Q8", elements, lambda left, right: table[left][right], "1")


def _finish_group(name, elements, multiply, identity):
    multiplication = {
        (left, right): multiply(left, right)
        for left in elements
        for right in elements
    }
    inverse = {
        element: next(
            candidate
            for candidate in elements
            if multiplication[(element, candidate)] == identity
            and multiplication[(candidate, element)] == identity
        )
        for element in elements
    }
    return {
        "name": name,
        "elements": tuple(elements),
        "mul": multiplication,
        "inv": inverse,
        "identity": identity,
    }


def group_from_spec(spec):
    """Construct a group from the JSON-friendly catalogue specification."""
    family = spec["family"]
    if family == "dihedral":
        return make_dihedral(spec["n"])
    if family == "znxm":
        return make_znzm(spec["n"], spec["m"])
    if family == "z2_cubed":
        return make_z2_cubed()
    if family == "quaternion":
        return make_q8()
    if family == "permutation":
        return make_permutation_group(
            spec["size"],
            even_only=spec.get("even_only", False),
            one_based=spec.get("one_based", False),
            name=spec.get("name"),
        )
    raise SurfaceError(f"Unknown group family: {family}")


def freeze(value):
    """Convert JSON arrays recursively to hashable tuples."""
    if isinstance(value, list):
        return tuple(freeze(item) for item in value)
    if isinstance(value, dict):
        return {key: freeze(item) for key, item in value.items()}
    return value


def canonical_cycle(face, allow_reverse=True):
    face = tuple(face)
    rotations = [face[index:] + face[:index] for index in range(len(face))]
    if allow_reverse:
        reverse = tuple(reversed(face))
        rotations.extend(reverse[index:] + reverse[:index] for index in range(len(face)))
    return min(rotations, key=repr)


def face_profile(faces):
    return dict(sorted(Counter(len(face) for face in faces).items()))


def profile_text(faces):
    return " + ".join(f"{count}x{length}" for length, count in face_profile(faces).items())


def cyclic_orders(generator_set):
    """Return cyclic orders modulo cyclic shift by fixing the first generator."""
    generator_set = tuple(generator_set)
    first = generator_set[0]
    return tuple((first,) + rest for rest in permutations(generator_set[1:]))


def rotation_search_size(vertex_count, degree):
    return factorial(degree - 1) ** vertex_count


def faces_from_rotation_system(group, generator_set, rotations):
    """Return face cycles for one orientable rotation system.

    ``rotations`` maps every group element to a cyclic permutation of the
    connection set.  Face traversal first crosses an edge and then takes the
    successor of the reverse dart at the new vertex.
    """
    elements = group["elements"]
    multiplication = group["mul"]
    inverse = group["inv"]
    generator_set = tuple(generator_set)
    expected = set(generator_set)
    if any(inverse[generator] not in expected for generator in generator_set):
        raise SurfaceError("The connection set must be inverse-closed")
    if set(rotations) != set(elements):
        raise SurfaceError("A cyclic rotation is required at every vertex")
    for vertex, order in rotations.items():
        if len(order) != len(generator_set) or set(order) != expected:
            raise SurfaceError(f"Invalid rotation at vertex {vertex!r}")

    def successor(dart):
        tail, generator = dart
        head = multiplication[(tail, generator)]
        reverse_generator = inverse[generator]
        order = rotations[head]
        position = order.index(reverse_generator)
        return head, order[(position + 1) % len(order)]

    all_darts = tuple((vertex, generator) for vertex in elements for generator in generator_set)
    visited = set()
    faces = []
    for start in all_darts:
        if start in visited:
            continue
        face_darts = []
        current = start
        while current not in visited:
            visited.add(current)
            face_darts.append(current)
            current = successor(current)
        if current != start:
            raise SurfaceError("Face permutation did not close at its starting dart")
        faces.append(tuple(vertex for vertex, _generator in face_darts))
    return tuple(faces)


def uniform_rotation_surface(group, generator_set, order_indices):
    generator_set = tuple(generator_set)
    order = tuple(generator_set[index] for index in order_indices)
    rotations = {vertex: order for vertex in group["elements"]}
    return faces_from_rotation_system(group, generator_set, rotations)


def local_binary_rotation_surface(group, generator_set, bits, base_order=(0, 1, 2)):
    """Build a cubic rotation system from normal/reversed local rotations."""
    if len(generator_set) != 3:
        raise SurfaceError("Binary local rotations are complete only for cubic graphs")
    if len(bits) != len(group["elements"]) or set(bits) - {"0", "1"}:
        raise SurfaceError("Rotation bits must contain one 0/1 value per vertex")
    normal = tuple(generator_set[index] for index in base_order)
    reversed_order = (normal[0], normal[2], normal[1])
    rotations = {
        vertex: reversed_order if bits[index] == "1" else normal
        for index, vertex in enumerate(group["elements"])
    }
    return faces_from_rotation_system(group, generator_set, rotations)


def explicit_rotation_surface(group, generator_set, orders_by_vertex):
    if len(orders_by_vertex) != len(group["elements"]):
        raise SurfaceError("Explicit rotations must contain one order per vertex")
    rotations = {
        vertex: tuple(generator_set[index] for index in orders_by_vertex[position])
        for position, vertex in enumerate(group["elements"])
    }
    return faces_from_rotation_system(group, generator_set, rotations)


def relator_face_candidates(group, generator_set, relator_words):
    """Generate unique undirected face orbits from relator words."""
    multiplication = group["mul"]
    seen = set()
    faces = []
    for index_word in relator_words:
        word = tuple(generator_set[index] for index in index_word)
        for start in group["elements"]:
            path = []
            current = start
            for generator in word:
                path.append(current)
                current = multiplication[(current, generator)]
            if current != start:
                raise SurfaceError(f"Word {index_word!r} is not a relator")
            key = canonical_cycle(path, allow_reverse=True)
            if key not in seen:
                seen.add(key)
                faces.append(tuple(path))
    return tuple(faces)


def _generator_for_step(group, generator_set, tail, head):
    matches = [
        generator
        for generator in generator_set
        if group["mul"][(tail, generator)] == head
    ]
    if len(matches) != 1:
        raise SurfaceError(
            f"Expected one generator from {tail!r} to {head!r}; found {len(matches)}"
        )
    return matches[0]


def darts_of_face(group, generator_set, face):
    return tuple(
        (
            face[index],
            _generator_for_step(
                group,
                generator_set,
                face[index],
                face[(index + 1) % len(face)],
            ),
        )
        for index in range(len(face))
    )


def orient_relator_faces(group, generator_set, undirected_faces):
    """Choose one orientation per candidate face to partition all darts exactly."""
    all_darts = {
        (vertex, generator)
        for vertex in group["elements"]
        for generator in generator_set
    }
    options = []
    for face in undirected_faces:
        forward = tuple(face)
        backward = tuple(reversed(face))
        options.append(
            (
                (forward, set(darts_of_face(group, generator_set, forward))),
                (backward, set(darts_of_face(group, generator_set, backward))),
            )
        )

    solution = None

    def search(index, used, chosen):
        nonlocal solution
        if solution is not None:
            return
        if index == len(options):
            if used == all_darts:
                solution = tuple(chosen)
            return
        for face, darts in options[index]:
            if len(darts) != len(face) or used & darts:
                continue
            chosen.append(face)
            search(index + 1, used | darts, chosen)
            chosen.pop()

    search(0, set(), [])
    if solution is None:
        raise SurfaceError("No consistent orientation partitions the Cayley darts")
    return solution


def relator_surface(group, generator_set, relator_words):
    candidates = relator_face_candidates(group, generator_set, relator_words)
    return orient_relator_faces(group, generator_set, candidates)


def validate_surface(group, generator_set, faces, require_simple_faces=True):
    """Validate a connected closed orientable cellular Cayley surface.

    The checks include inverse closure, graph connectivity, exact dart use,
    simple face boundaries, a single cyclic vertex link, and integral genus.
    """
    elements = tuple(group["elements"])
    generator_set = tuple(generator_set)
    errors = []
    expected_darts = {(vertex, generator) for vertex in elements for generator in generator_set}

    if any(group["inv"][generator] not in generator_set for generator in generator_set):
        errors.append("connection set is not inverse-closed")

    index = {vertex: position for position, vertex in enumerate(elements)}
    undirected_edges = set()
    for vertex, generator in expected_darts:
        head = group["mul"][(vertex, generator)]
        pair = tuple(sorted((index[vertex], index[head])))
        undirected_edges.add(pair)

    adjacency = {vertex: set() for vertex in elements}
    for vertex, generator in expected_darts:
        adjacency[vertex].add(group["mul"][(vertex, generator)])
    reached = set()
    queue = deque([group["identity"]])
    while queue:
        vertex = queue.popleft()
        if vertex in reached:
            continue
        reached.add(vertex)
        queue.extend(adjacency[vertex] - reached)
    if reached != set(elements):
        errors.append("Cayley graph is disconnected")

    dart_counter = Counter()
    link_successor = {vertex: {} for vertex in elements}
    for face_index, face in enumerate(faces):
        face = tuple(face)
        if len(face) < 3:
            errors.append(f"face {face_index} has length below 3")
            continue
        if require_simple_faces and len(set(face)) != len(face):
            errors.append(f"face {face_index} repeats a vertex")
        if any(vertex not in index for vertex in face):
            errors.append(f"face {face_index} contains an unknown vertex")
            continue
        try:
            face_darts = darts_of_face(group, generator_set, face)
        except SurfaceError as exc:
            errors.append(f"face {face_index}: {exc}")
            continue
        dart_counter.update(face_darts)
        for position, vertex in enumerate(face):
            previous = face[(position - 1) % len(face)]
            following = face[(position + 1) % len(face)]
            incoming_side = _generator_for_step(group, generator_set, vertex, previous)
            outgoing_side = _generator_for_step(group, generator_set, vertex, following)
            old_value = link_successor[vertex].get(incoming_side)
            if old_value is not None and old_value != outgoing_side:
                errors.append(f"vertex {vertex!r} has a non-functional link")
            link_successor[vertex][incoming_side] = outgoing_side

    if set(dart_counter) != expected_darts:
        missing = len(expected_darts - set(dart_counter))
        extra = len(set(dart_counter) - expected_darts)
        errors.append(f"dart set mismatch: {missing} missing, {extra} extra")
    repeated = [dart for dart, count in dart_counter.items() if count != 1]
    if repeated:
        errors.append(f"{len(repeated)} darts do not occur exactly once")

    generator_set_values = set(generator_set)
    for vertex, successor in link_successor.items():
        if set(successor) != generator_set_values or set(successor.values()) != generator_set_values:
            errors.append(f"vertex {vertex!r} link does not use every incident side once")
            continue
        start = generator_set[0]
        current = start
        visited = set()
        while current not in visited:
            visited.add(current)
            current = successor[current]
        if current != start or visited != generator_set_values:
            errors.append(f"vertex {vertex!r} link is not one cycle")

    vertex_count = len(elements)
    edge_count = len(undirected_edges)
    face_count = len(faces)
    chi = vertex_count - edge_count + face_count
    genus_numerator = 2 - chi
    genus = genus_numerator // 2 if genus_numerator >= 0 and genus_numerator % 2 == 0 else None
    if genus is None:
        errors.append(f"Euler characteristic {chi} does not give an orientable genus")

    return {
        "valid": not errors,
        "errors": errors,
        "vertex_count": vertex_count,
        "edge_count": edge_count,
        "face_count": face_count,
        "chi": chi,
        "genus": genus,
        "profile": face_profile(faces),
    }


def uniform_rotation_candidates(group, generator_set, require_simple_faces=True):
    """Enumerate the Cayley-equivariant (uniform) rotation subclass."""
    candidates = []
    seen = set()
    for order in cyclic_orders(generator_set):
        indices = tuple(generator_set.index(generator) for generator in order)
        faces = uniform_rotation_surface(group, generator_set, indices)
        validation = validate_surface(
            group,
            generator_set,
            faces,
            require_simple_faces=require_simple_faces,
        )
        if not validation["valid"]:
            continue
        key = frozenset(canonical_cycle(face) for face in faces)
        if key in seen:
            continue
        seen.add(key)
        candidates.append({"order": indices, "faces": faces, "validation": validation})
    return tuple(candidates)


def exhaustive_rotation_candidates(
    group,
    generator_set,
    max_states=1_000_000,
    require_simple_faces=True,
):
    """Enumerate all local rotations when the explicit state bound permits it."""
    orders = cyclic_orders(generator_set)
    state_count = len(orders) ** len(group["elements"])
    if state_count > max_states:
        raise SurfaceError(
            f"Refusing {state_count:,} rotation systems; max_states={max_states:,}"
        )
    candidates = []
    seen = set()
    for order_choice in product(range(len(orders)), repeat=len(group["elements"])):
        rotations = {
            vertex: orders[order_choice[position]]
            for position, vertex in enumerate(group["elements"])
        }
        faces = faces_from_rotation_system(group, generator_set, rotations)
        validation = validate_surface(
            group,
            generator_set,
            faces,
            require_simple_faces=require_simple_faces,
        )
        if not validation["valid"]:
            continue
        key = frozenset(canonical_cycle(face) for face in faces)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            {"orders": order_choice, "faces": faces, "validation": validation}
        )
    return tuple(candidates)
