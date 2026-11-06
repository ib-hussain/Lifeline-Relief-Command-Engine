"""sensor_edges and sensor_cover (vertex cover with a planted solution).

Correct by construction: choose the cover C (k nodes, 2 <= k <= n/2) FIRST, then draw edges
only among pairs that have at least one end in C. Every edge is then touched by C.
Edges: u < v, no loops, no repeats, between n - 1 and 3n of them.
"""


def gen_sensors(rng, n):
    k = rng.randint(2, n // 2)
    cover = sorted(rng.sample(range(n), k))
    in_cover = set(cover)
    candidates = [(u, v) for u in range(n) for v in range(u + 1, n)
                  if u in in_cover or v in in_cover]
    m = rng.randint(n - 1, min(len(candidates), 3 * n))
    edges = sorted(rng.sample(candidates, m))
    return ([dict(u=u, v=v) for u, v in edges],
            [dict(node=x) for x in cover], k)
