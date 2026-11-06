"""sites and the planted tour.

Sites: distinct integer points in [0, 999]^2.
Planted tour (correct by construction): nearest-neighbour tour from site 0 (ties -> lowest
site_no), then 2-opt moves that only ever shorten it. The result is a permutation that starts
at site 0 and is never longer than the nearest-neighbour tour (required on tiers L and X).
tour_length = its closed Manhattan length.
"""
from common import manhattan, closed_tour_length


def gen_sites(rng, n):
    cells = rng.sample(range(1000 * 1000), n)
    return [(c // 1000, c % 1000) for c in cells]


def nearest_neighbour_tour(points):
    n = len(points)
    seen = [False] * n
    seen[0] = True
    order, cur = [0], 0
    for _ in range(n - 1):
        best, best_d = -1, None
        for j in range(n):
            if not seen[j]:
                d = manhattan(points[cur], points[j])
                if best_d is None or d < best_d:          # strict: ties keep the lower site_no
                    best, best_d = j, d
        seen[best] = True
        order.append(best)
        cur = best
    return order


def two_opt(points, order, max_passes):
    n = len(order)
    for _ in range(max_passes):
        improved = False
        for i in range(1, n - 1):
            a, b = points[order[i - 1]], points[order[i]]
            for j in range(i + 1, n):
                c, d = points[order[j]], points[order[(j + 1) % n]]
                delta = manhattan(a, c) + manhattan(b, d) - manhattan(a, b) - manhattan(c, d)
                if delta < 0:
                    order[i:j + 1] = reversed(order[i:j + 1])
                    b = points[order[i]]
                    improved = True
        if not improved:
            break
    return order


def gen_tour(rng, n, tier):
    points = gen_sites(rng, n)
    nn = nearest_neighbour_tour(points)
    planted = two_opt(points, list(nn), max_passes=50 if n <= 16 else 4)
    length = closed_tour_length(points, planted)
    if length > closed_tour_length(points, nn) or planted[0] != 0:
        return None
    sites = [dict(site_no=i, x=x, y=y) for i, (x, y) in enumerate(points)]
    tour = [dict(step=s, site_no=v) for s, v in enumerate(planted)]
    return sites, tour, length
