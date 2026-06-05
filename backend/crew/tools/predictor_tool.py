from langchain.tools import BaseTool
from collections import Counter
from app.database import get_connection
import json
import re


class PredictionTool(BaseTool):
    name: str = "Prediction Generator"
    description: str = "Generates tiered predictions (2+bonus through 6+bonus) based on frequency analysis of past draws."

    def _run(self, input_str: str = "") -> str:
        draw_type = self._extract_draw_type(input_str) or "lunchtime"
        limit = 50

        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM draws WHERE draw_type = ? ORDER BY draw_date DESC LIMIT ?",
            (draw_type, limit)
        ).fetchall()
        conn.close()

        if not rows:
            return json.dumps({"error": "No data found"})

        all_nums = []
        for r in rows:
            for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
                all_nums.append(n)

        freq = Counter(all_nums)
        total_main = len(all_nums)

        number_probs = {}
        for n in range(1, 50):
            number_probs[n] = freq.get(n, 0) / total_main if total_main > 0 else 0

        sorted_by_prob = sorted(number_probs.items(), key=lambda x: x[1], reverse=True)
        top_prob_numbers = [n for n, _ in sorted_by_prob]

        bonus_freq = Counter(r["bonus"] for r in rows)
        total_bonus = len(rows)
        bonus_probs = {}
        for b in range(1, 50):
            bonus_probs[b] = bonus_freq.get(b, 0) / total_bonus if total_bonus > 0 else 0

        sorted_bonus = sorted(bonus_probs.items(), key=lambda x: x[1], reverse=True)
        top_bonus = [b for b, _ in sorted_bonus]

        tiers = {}
        for k in [2, 3, 4, 5, 6]:
            picks = []
            for offset in range(3):
                nums = top_prob_numbers[offset:k+offset]
                if len(nums) < k:
                    remaining = [n for n in top_prob_numbers if n not in nums]
                    nums += remaining[:k - len(nums)]

                bonus = top_bonus[offset] if offset < len(top_bonus) else 1
                while bonus in nums:
                    bonus = (bonus % 49) + 1

                prob = 1.0
                for n in nums:
                    prob *= number_probs.get(n, 0.01)
                prob *= bonus_probs.get(bonus, 0.01)

                picks.append({
                    "numbers": sorted(nums),
                    "bonus": bonus,
                    "probability": round(prob, 8)
                })

            picks.sort(key=lambda x: x["probability"], reverse=True)
            tiers[f"{k}+bonus"] = picks

        return json.dumps(tiers)

    def _extract_draw_type(self, text: str) -> str | None:
        for dt in ["brunchtime", "lunchtime", "drivetime", "teatime"]:
            if re.search(rf"\b{dt}\b", text.lower()):
                return dt
        match = re.search(r'"draw_type"\s*:\s*"(brunchtime|lunchtime|drivetime|teatime)"', text)
        if match:
            return match.group(1)
        return None
