import json
from collections import Counter
from app.database import get_connection


def get_rows(draw_type: str, limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM draws WHERE draw_type = ? ORDER BY draw_date DESC LIMIT ?",
        (draw_type, limit)
    ).fetchall()
    conn.close()
    return rows


def make_picks(pool: list[int], bonus_pool: list[int]) -> dict:
    tiers = {}
    for k in [2, 3, 4, 5, 6]:
        picks = []
        for offset in range(3):
            nums = pool[offset:k + offset]
            if len(nums) < k:
                remaining = [n for n in pool if n not in nums]
                nums += remaining[:k - len(nums)]

            bonus = bonus_pool[offset] if offset < len(bonus_pool) else 1
            while bonus in nums:
                bonus = (bonus % 49) + 1

            prob = 1.0
            for n in nums:
                prob *= number_probability(pool, n)
            prob *= number_probability(bonus_pool, bonus)

            picks.append({
                "numbers": sorted(nums),
                "bonus": bonus,
                "probability": round(prob, 8)
            })

        picks.sort(key=lambda x: x["probability"], reverse=True)
        tiers[f"{k}+bonus"] = picks
    return tiers


def number_probability(pool: list[int], num: int) -> float:
    return pool.count(num) / len(pool) if pool else 0.01


def frequency_strategy(rows) -> dict:
    all_nums = []
    bonuses = []
    for r in rows:
        for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
            all_nums.append(n)
        bonuses.append(r["bonus"])

    freq = Counter(all_nums)
    sorted_nums = [n for n, _ in freq.most_common()]
    bonus_freq = Counter(bonuses)
    sorted_bonus = [b for b, _ in bonus_freq.most_common()]

    return make_picks(sorted_nums, sorted_bonus)


def weighted_recent_strategy(rows) -> dict:
    decay = 0.95
    weights = [decay ** i for i in range(len(rows))]
    total_weight = sum(weights)

    number_scores = Counter()
    bonus_scores = Counter()

    for idx, r in enumerate(rows):
        w = weights[idx]
        for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
            number_scores[n] += w
        bonus_scores[r["bonus"]] += w

    sorted_nums = [n for n, _ in number_scores.most_common()]
    sorted_bonus = [b for b, _ in bonus_scores.most_common()]

    return make_picks(sorted_nums, sorted_bonus)


def delta_strategy(rows) -> dict:
    if not rows:
        return {}

    deltas = []
    for r in rows:
        nums = sorted([r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]])
        for i in range(len(nums) - 1):
            deltas.append(nums[i + 1] - nums[i])

    delta_freq = Counter(deltas)
    common_deltas = [d for d, _ in delta_freq.most_common(5)]

    last_nums = sorted([rows[0]["n1"], rows[0]["n2"], rows[0]["n3"],
                        rows[0]["n4"], rows[0]["n5"], rows[0]["n6"]])

    candidates = set(range(1, 50))
    for base in last_nums:
        for d in common_deltas:
            for sign in [1, -1]:
                val = base + sign * d
                if 1 <= val <= 49:
                    candidates.add(val)

    scored = []
    freq = Counter()
    for r in rows:
        for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
            freq[n] += 1

    for n in range(1, 50):
        if n in candidates:
            scored.append((n, freq.get(n, 0)))

    scored.sort(key=lambda x: (-x[1], x[0]))
    pool = [n for n, _ in scored]

    bonus_freq = Counter(r["bonus"] for r in rows)
    bonus_pool = [b for b, _ in bonus_freq.most_common()]

    return make_picks(pool, bonus_pool)


def pair_strategy(rows) -> dict:
    if not rows:
        return {}

    pair_freq = Counter()
    for r in rows:
        nums = [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                pair_freq[tuple(sorted((nums[i], nums[j])))] += 1

    top_pairs = [pair for pair, _ in pair_freq.most_common(15)]
    all_pair_nums = []
    for a, b in top_pairs:
        all_pair_nums.append(a)
        all_pair_nums.append(b)

    freq = Counter(all_pair_nums)
    pool = [n for n, _ in freq.most_common()]

    if len(pool) < 6:
        freq = Counter()
        for r in rows:
            for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
                freq[n] += 1
        for n, _ in freq.most_common():
            if n not in pool:
                pool.append(n)

    bonus_freq = Counter(r["bonus"] for r in rows)
    bonus_pool = [b for b, _ in bonus_freq.most_common()]

    return make_picks(pool, bonus_pool)


def cold_recovery_strategy(rows) -> dict:
    if not rows:
        return {}

    all_drawn = set()
    for r in rows:
        for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
            all_drawn.add(n)

    overdue = [n for n in range(1, 50) if n not in all_drawn]

    freq = Counter()
    for r in rows:
        for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
            freq[n] += 1

    seen_sorted = sorted(freq.keys(), key=lambda n: freq[n])
    pool = overdue + seen_sorted

    if len(pool) < 6:
        pool = list(range(1, 50))

    bonus_freq = Counter(r["bonus"] for r in rows)
    all_bonus_drawn = set(r["bonus"] for r in rows)
    overdue_bonus = [b for b in range(1, 50) if b not in all_bonus_drawn]
    bonus_pool = overdue_bonus + [b for b, _ in bonus_freq.most_common()]

    return make_picks(pool, bonus_pool)


def sum_targeting_strategy(rows) -> dict:
    if not rows:
        return {}

    sums = [r["n1"] + r["n2"] + r["n3"] + r["n4"] + r["n5"] + r["n6"] for r in rows]
    avg_sum = round(sum(sums) / len(sums))
    target_range = range(avg_sum - 20, avg_sum + 21)

    freq = Counter()
    for r in rows:
        for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
            freq[n] += 1

    all_nums = sorted(freq.keys(), key=lambda n: -freq[n])

    valid_picks = []
    for offset in range(0, min(30, len(all_nums) - 5)):
        base = all_nums[offset:offset + 6]
        if len(base) < 6:
            continue
        s = sum(base)
        if s in target_range:
            bonus_freq = Counter(r["bonus"] for r in rows)
            top_bonus = [b for b, _ in bonus_freq.most_common()]
            bonus = top_bonus[0] if top_bonus else 1
            while bonus in base:
                bonus = (bonus % 49) + 1
            prob = 1.0
            for n in base:
                prob *= (freq[n] / max(freq.values()))
            prob *= (bonus_freq.get(bonus, 0) / len(rows))
            valid_picks.append({
                "numbers": sorted(base),
                "bonus": bonus,
                "probability": round(prob, 8)
            })

    valid_picks.sort(key=lambda x: -x["probability"])
    top_main = [n for p in valid_picks[:3] for n in p["numbers"]]
    top_main_freq = Counter(top_main)
    pool = [n for n, _ in top_main_freq.most_common()]

    if len(pool) < 6:
        pool = all_nums

    bonus_freq = Counter(r["bonus"] for r in rows)
    bonus_pool = [b for b, _ in bonus_freq.most_common()]

    return make_picks(pool, bonus_pool)


def ensemble_strategy(rows) -> dict:
    strategies = [
        frequency_strategy,
        weighted_recent_strategy,
        delta_strategy,
        pair_strategy,
        cold_recovery_strategy,
        sum_targeting_strategy,
    ]

    vote_scores = Counter()
    all_tiers = {}

    for strat in strategies:
        result = strat(rows)
        for key, picks in result.items():
            if key not in all_tiers:
                all_tiers[key] = []
            for pick in picks:
                for n in pick["numbers"]:
                    vote_scores[n] += 1

    pool = [n for n, _ in vote_scores.most_common()]

    bonus_freq = Counter(r["bonus"] for r in rows)
    bonus_pool = [b for b, _ in bonus_freq.most_common()]

    return make_picks(pool, bonus_pool)


STRATEGIES = {
    "frequency": frequency_strategy,
    "weighted_recent": weighted_recent_strategy,
    "delta": delta_strategy,
    "pair": pair_strategy,
    "cold_recovery": cold_recovery_strategy,
    "sum_targeting": sum_targeting_strategy,
    "ensemble": ensemble_strategy,
}
