from fastapi import APIRouter, Query
from app.database import get_connection
from crew.tools.strategies import STRATEGIES
from collections import Counter
import json

router = APIRouter(prefix="/api", tags=["evaluate"])


def get_training_rows(draw_type: str, before_id: int, limit: int = 50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM draws WHERE draw_type = ? AND id < ? ORDER BY id DESC LIMIT ?",
        (draw_type, before_id, limit)
    ).fetchall()
    conn.close()
    return rows


def score_pick(pick_nums: list[int], pick_bonus: int, actual_nums: list[int], actual_bonus: int) -> dict:
    main_hits = sum(1 for n in pick_nums if n in actual_nums)
    bonus_hit = 1 if pick_bonus == actual_bonus else 0
    any_match = 1 if main_hits > 0 or bonus_hit else 0
    return {"main_hits": main_hits, "bonus_hit": bonus_hit, "any_match": any_match}


@router.get("/evaluate")
def evaluate_methods(draw_type: str = Query("lunchtime", pattern="^(lunchtime|teatime)$")):
    conn = get_connection()
    all_draws = conn.execute(
        "SELECT * FROM draws WHERE draw_type = ? ORDER BY id ASC",
        (draw_type,)
    ).fetchall()
    conn.close()

    if len(all_draws) < 51:
        return {
            "error": f"Need at least 51 draws for {draw_type}, have {len(all_draws)}",
            "requires_scrape": True,
        }

    tier_order = ["2+bonus", "3+bonus", "4+bonus", "5+bonus", "6+bonus"]

    results = {}
    for method_name in STRATEGIES:
        results[method_name] = {t: {"main_hits": [], "bonus_hits": 0, "any_matches": 0, "tests": 0} for t in tier_order}

    test_count = 0
    for idx, draw in enumerate(all_draws):
        if idx < 50:
            continue
        test_count += 1
        actual_nums = [draw["n1"], draw["n2"], draw["n3"], draw["n4"], draw["n5"], draw["n6"]]
        actual_bonus = draw["bonus"]

        training = get_training_rows(draw_type, draw["id"], 50)
        if len(training) < 50:
            continue

        for method_name, strategy in STRATEGIES.items():
            tiers = strategy(training)
            for tier_key in tier_order:
                picks = tiers.get(tier_key, [])
                tier_scores = []
                for pick in picks:
                    s = score_pick(pick["numbers"], pick["bonus"], actual_nums, actual_bonus)
                    tier_scores.append(s)

                if tier_scores:
                    best = max(tier_scores, key=lambda x: x["main_hits"] + x["bonus_hit"])
                    results[method_name][tier_key]["main_hits"].append(best["main_hits"])
                    results[method_name][tier_key]["bonus_hits"] += best["bonus_hit"]
                    results[method_name][tier_key]["any_matches"] += best["any_match"]
                    results[method_name][tier_key]["tests"] += 1

    summary = {}
    for method_name, tiers in results.items():
        summary[method_name] = {}
        for tier_key, data in tiers.items():
            n = data["tests"]
            avg_main = round(sum(data["main_hits"]) / n, 3) if n else 0
            bonus_rate = round(data["bonus_hits"] / n * 100, 1) if n else 0
            any_rate = round(data["any_matches"] / n * 100, 1) if n else 0
            summary[method_name][tier_key] = {
                "avg_main_hits": avg_main,
                "bonus_hit_rate": bonus_rate,
                "any_match_rate": any_rate,
                "tests": n,
            }

    method_totals = {}
    for method_name in STRATEGIES:
        totals = {"main_hits": 0, "bonus_hits": 0, "any_matches": 0, "tests": 0}
        for tier_key in tier_order:
            d = results[method_name][tier_key]
            totals["main_hits"] += sum(d["main_hits"])
            totals["bonus_hits"] += d["bonus_hits"]
            totals["any_matches"] += d["any_matches"]
            totals["tests"] += d["tests"]

        n = totals["tests"]
        method_totals[method_name] = {
            "avg_main_hits": round(totals["main_hits"] / n, 3) if n else 0,
            "bonus_hit_rate": round(totals["bonus_hits"] / n * 100, 1) if n else 0,
            "any_match_rate": round(totals["any_matches"] / n * 100, 1) if n else 0,
            "tests": n,
            "tiers": summary[method_name],
        }

    ranking = sorted(method_totals.items(), key=lambda x: (-x[1]["avg_main_hits"], -x[1]["bonus_hit_rate"]))

    return {
        "draw_type": draw_type,
        "test_count": test_count,
        "methods": {name: data for name, data in ranking},
        "ranking": [name for name, _ in ranking],
    }
