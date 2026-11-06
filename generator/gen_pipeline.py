"""pipeline_dims (matrix chain) and drum_prices (cutting a drum of length L).

dims: n + 1 integers in 2..100 (matrix i is dims[i-1] x dims[i]).
prices: price of a piece of length j, j = 1..L, integer 1..500. Prices follow a noisy
per-length rate with a cap of 500, so long pieces are often worth less per unit and the
best cut is not obvious. Re-drawn if all prices happen to be proportional to length.
"""
RATE = {"S": (2.0, 30.0), "M": (0.8, 4.0), "L": (0.2, 1.2)}


def gen_dims(rng, stages):
    return [dict(idx=i, dim=rng.randint(2, 100)) for i in range(stages + 1)]


def gen_drum(rng, L, tier):
    rate = rng.uniform(*RATE[tier])
    prices = []
    for j in range(1, L + 1):
        p = round(j * rate * rng.uniform(0.6, 1.4))
        prices.append(min(500, max(1, p)))
    if all(prices[j - 1] * 1 == prices[0] * j for j in range(1, L + 1)):
        return None
    return [dict(length=j, price=prices[j - 1]) for j in range(1, L + 1)]
