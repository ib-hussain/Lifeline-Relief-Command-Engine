"""Shared helpers for the generator: deterministic randomness and small graph/string tools
used for the generator's own self-checks.

All randomness comes from (group seed, case number, module name, attempt number).
String seeds are hashed with SHA-512 by Python's `random`, so they are stable across
runs and machines (unlike hash()).
"""
import heapq
import random
from collections import deque
from fractions import Fraction

INF = float("inf")


def make_rng(seed, case_no, module, attempt=0):
    return random.Random(f"LIFELINE|s={seed}|k={case_no}|{module}|a={attempt}")


def tier_of(k):
    if k <= 19:
        return "S"
    if k <= 39:
        return "M"
    if k <= 45:
        return "L"
    return "X"


def scenario_of(k):
    return k % 6 + 1


def ceil_div(a, b):
    return -(-a // b)


def retry(seed, case_no, module, fn, max_tries=2000):
    """Call fn(rng) with a fresh deterministic rng until it returns something not None."""
    for attempt in range(max_tries):
        result = fn(make_rng(seed, case_no, module, attempt))
        if result is not None:
            return result
    raise RuntimeError(f"case {case_no}: could not generate '{module}' in {max_tries} attempts")


# ---------------------------------------------------------------- graphs

def adjacency(V, roads):
    """adj[u] = sorted list of (v, minutes)."""
    adj = [[] for _ in range(V)]
    for r in roads:
        adj[r["u"]].append((r["v"], r["minutes"]))
        adj[r["v"]].append((r["u"], r["minutes"]))
    for a in adj:
        a.sort()
    return adj


def bfs_order(V, adj, src=0, closed_pairs=None):
    """Hop distances and BFS visiting order (neighbours in ascending id)."""
    hops = [-1] * V
    hops[src] = 0
    order = [src]
    q = deque([src])
    while q:
        u = q.popleft()
        for v, _ in adj[u]:
            if closed_pairs and (min(u, v), max(u, v)) in closed_pairs:
                continue
            if hops[v] == -1:
                hops[v] = hops[u] + 1
                order.append(v)
                q.append(v)
    return hops, order


def route_costs(V, roads, penalty, src=0):
    """For every location: hop distance, cheapest cost, and cheapest cost among the
    fewest-roads routes. The step u->v costs minutes(u,v) + penalty[v]."""
    adj = adjacency(V, roads)
    hops, order = bfs_order(V, adj, src)
    dist = [INF] * V
    dist[src] = 0
    pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, m in adj[u]:
            nd = d + m + penalty[v]
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    fewest = [INF] * V
    fewest[src] = 0
    for u in order:                       # BFS order = non-decreasing hops
        for v, m in adj[u]:
            if hops[v] == hops[u] + 1:
                c = fewest[u] + m + penalty[v]
                if c < fewest[v]:
                    fewest[v] = c
    return hops, dist, fewest


def find_bridges(V, edges):
    """Iterative Tarjan. edges: list of (u, v). Returns the set of edge indices that are bridges."""
    adj = [[] for _ in range(V)]
    for i, (u, v) in enumerate(edges):
        adj[u].append((v, i))
        adj[v].append((u, i))
    disc = [-1] * V
    low = [0] * V
    timer = 0
    bridges = set()
    for s in range(V):
        if disc[s] != -1:
            continue
        disc[s] = low[s] = timer
        timer += 1
        stack = [(s, -1, iter(adj[s]))]
        while stack:
            u, parent_edge, it = stack[-1]
            pushed = False
            for v, ei in it:
                if ei == parent_edge:
                    continue
                if disc[v] == -1:
                    disc[v] = low[v] = timer
                    timer += 1
                    stack.append((v, ei, iter(adj[v])))
                    pushed = True
                    break
                low[u] = min(low[u], disc[v])
            if not pushed:
                stack.pop()
                if stack:
                    p = stack[-1][0]
                    low[p] = min(low[p], low[u])
                    if low[u] > disc[p]:
                        bridges.add(parent_edge)
    return bridges


# ---------------------------------------------------------------- crates

def greedy_ratio_value(crates, capacity):
    """Take crates by value/weight descending (exact fractions, ties by crate_id),
    skip those that do not fit."""
    order = sorted(crates, key=lambda c: (-Fraction(c["value"], c["weight"]), c["crate_id"]))
    left, total = capacity, 0
    for c in order:
        if c["weight"] <= left:
            left -= c["weight"]
            total += c["value"]
    return total


def knapsack_value(crates, capacity):
    best = [0] * (capacity + 1)
    for c in crates:
        w, v = c["weight"], c["value"]
        for cap in range(capacity, w - 1, -1):
            if best[cap - w] + v > best[cap]:
                best[cap] = best[cap - w] + v
    return best[capacity]


# ---------------------------------------------------------------- strings

def count_overlapping(text, pattern):
    count, i = 0, text.find(pattern)
    while i != -1:
        count += 1
        i = text.find(pattern, i + 1)
    return count


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        ca = a[i - 1]
        for j in range(1, len(b) + 1):
            cost = 0 if ca == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[len(b)]


# ---------------------------------------------------------------- geometry

def manhattan(p, q):
    return abs(p[0] - q[0]) + abs(p[1] - q[1])


def closed_tour_length(points, order):
    n = len(order)
    return sum(manhattan(points[order[i]], points[order[(i + 1) % n]]) for i in range(n))
