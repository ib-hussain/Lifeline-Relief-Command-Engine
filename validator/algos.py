"""Independent reference algorithms used only for verification.
They are intentionally DIFFERENT from the generator's methods:
generator brute force  <->  validator dynamic programming / greedy / KMP / Held-Karp."""
import heapq
from bisect import bisect_right
from collections import deque
from functools import cmp_to_key

INF = float("inf")


# ------------------------------------------------------------ crates

def knapsack(items, capacity):
    """items: list of (weight, value). 0/1 knapsack by DP over capacity."""
    if capacity < 0:
        return 0
    table = [0] * (capacity + 1)
    for w, v in items:
        if w <= 0:
            continue
        for c in range(capacity, w - 1, -1):
            cand = table[c - w] + v
            if cand > table[c]:
                table[c] = cand
    return table[capacity]


def ratio_order(crates):
    """Value/weight descending compared by cross-multiplication, ties by crate_id ascending."""
    def cmp(a, b):
        left, right = a["value"] * b["weight"], b["value"] * a["weight"]
        if left != right:
            return -1 if left > right else 1
        return -1 if a["crate_id"] < b["crate_id"] else (1 if a["crate_id"] > b["crate_id"] else 0)
    return sorted(crates, key=cmp_to_key(cmp))


def greedy_by_ratio(crates, capacity):
    left = capacity
    total = 0
    for c in ratio_order(crates):
        if c["weight"] <= left:
            left -= c["weight"]
            total += c["value"]
    return total


# ------------------------------------------------------------ windows

def max_compatible_count(windows):
    """Earliest-finish greedy; touching windows are compatible."""
    last = -INF
    count = 0
    for s, f in sorted(((w["start"], w["finish"]) for w in windows), key=lambda x: (x[1], x[0])):
        if s >= last:
            count += 1
            last = f
    return count


def max_compatible_value(windows):
    """Weighted interval scheduling: DP over windows sorted by finish + binary search."""
    iv = sorted(((w["finish"], w["start"], w["value"]) for w in windows))
    finishes = [f for f, _, _ in iv]
    best = [0] * (len(iv) + 1)
    for i, (f, s, v) in enumerate(iv, 1):
        p = bisect_right(finishes, s, 0, i - 1)      # windows finishing at or before s
        best[i] = max(best[i - 1], best[p] + v)
    return best[-1]


# ------------------------------------------------------------ drum, tour, cover

def rod_cutting(prices):
    L = len(prices)
    best = [0] * (L + 1)
    for length in range(1, L + 1):
        best[length] = max(prices[j - 1] + best[length - j] for j in range(1, length + 1))
    return best[L]


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def held_karp(points):
    """Shortest closed tour from point 0 (Manhattan), O(n^2 2^n)."""
    n = len(points)
    if n == 1:
        return 0
    d = [[manhattan(p, q) for q in points] for p in points]
    full = 1 << (n - 1)
    dp = [[INF] * n for _ in range(full)]
    for j in range(1, n):
        dp[1 << (j - 1)][j] = d[0][j]
    for mask in range(1, full):
        row = dp[mask]
        for j in range(1, n):
            cur = row[j]
            if cur == INF:
                continue
            for k in range(1, n):
                bit = 1 << (k - 1)
                if not mask & bit:
                    nxt = dp[mask | bit]
                    if cur + d[j][k] < nxt[k]:
                        nxt[k] = cur + d[j][k]
    return min(dp[full - 1][j] + d[j][0] for j in range(1, n))


def nearest_neighbour_length(points):
    """Nearest unvisited site from site 0, ties -> lowest site_no, closed length."""
    n = len(points)
    unvisited = set(range(1, n))
    cur, total = 0, 0
    while unvisited:
        nxt = min(unvisited, key=lambda j: (manhattan(points[cur], points[j]), j))
        total += manhattan(points[cur], points[nxt])
        unvisited.remove(nxt)
        cur = nxt
    return total + manhattan(points[cur], points[0])


def has_cover(edges, k):
    """Bounded search tree: some endpoint of an uncovered edge must be in the cover."""
    if not edges:
        return True
    if k == 0:
        return False
    u, v = edges[0]
    return (has_cover([e for e in edges if u not in e], k - 1) or
            has_cover([e for e in edges if v not in e], k - 1))


def min_vertex_cover(edges):
    k = 0
    while not has_cover(edges, k):
        k += 1
    return k


# ------------------------------------------------------------ strings

def kmp_count(text, pattern):
    """Occurrences of pattern in text, overlaps included (Knuth-Morris-Pratt)."""
    m = len(pattern)
    fail = [0] * m
    j = 0
    for i in range(1, m):
        while j and pattern[i] != pattern[j]:
            j = fail[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        fail[i] = j
    count = j = 0
    for ch in text:
        while j and ch != pattern[j]:
            j = fail[j - 1]
        if ch == pattern[j]:
            j += 1
            if j == m:
                count += 1
                j = fail[j - 1]
    return count


def levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


# ------------------------------------------------------------ graphs

def neighbours(V, roads, closed=frozenset()):
    adj = [[] for _ in range(V)]
    for r in roads:
        if r["road_no"] in closed:
            continue
        adj[r["u"]].append((r["v"], r["minutes"]))
        adj[r["v"]].append((r["u"], r["minutes"]))
    for a in adj:
        a.sort()
    return adj


def bfs(adj, src):
    dist = [-1] * len(adj)
    dist[src] = 0
    order = [src]
    q = deque([src])
    while q:
        u = q.popleft()
        for v, _ in adj[u]:
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                order.append(v)
                q.append(v)
    return dist, order


def dijkstra(adj, penalty, src):
    dist = [INF] * len(adj)
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d != dist[u]:
            continue
        for v, m in adj[u]:
            nd = d + m + penalty[v]
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def cheapest_fewest_roads(adj, penalty, src):
    """Minimum cost over all fewest-roads routes, by DP over the BFS layers."""
    hops, order = bfs(adj, src)
    best = [INF] * len(adj)
    best[src] = 0
    for u in order:
        for v, m in adj[u]:
            if hops[v] == hops[u] + 1 and best[u] + m + penalty[v] < best[v]:
                best[v] = best[u] + m + penalty[v]
    return best
