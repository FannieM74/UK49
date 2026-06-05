from langchain.tools import BaseTool
from collections import Counter
from app.database import get_connection
import re


class FrequencyAnalysisTool(BaseTool):
    name: str = "Frequency Analysis"
    description: str = "Analyzes number frequency, hot/cold numbers, odd/even splits, and sum ranges from draw history."

    def _run(self, input_str: str = "") -> str:
        draw_type = self._extract_draw_type(input_str) or "lunchtime"
        limit = self._extract_limit(input_str) or 50

        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM draws WHERE draw_type = ? ORDER BY draw_date DESC LIMIT ?",
            (draw_type, limit)
        ).fetchall()
        conn.close()

        if not rows:
            return "No data found."

        all_nums = []
        bonuses = []
        for r in rows:
            for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
                all_nums.append(n)
            bonuses.append(r["bonus"])

        freq = Counter(all_nums)
        bonus_freq = Counter(bonuses)

        sorted_by_freq = freq.most_common()
        hot = sorted_by_freq[:5]
        cold = sorted_by_freq[-5:] if len(sorted_by_freq) >= 5 else sorted_by_freq

        odd_count = sum(1 for n in all_nums if n % 2 == 1)
        even_count = len(all_nums) - odd_count

        sums = [r["n1"]+r["n2"]+r["n3"]+r["n4"]+r["n5"]+r["n6"] for r in rows]

        result = {
            "total_draws_analyzed": len(rows),
            "hot_numbers": [{"number": n, "count": c} for n, c in hot],
            "cold_numbers": [{"number": n, "count": c} for n, c in cold],
            "bonus_frequency": [{"number": n, "count": c} for n, c in bonus_freq.most_common(5)],
            "odd_even_ratio": {"odd": odd_count, "even": even_count, "ratio": f"{odd_count}:{even_count}"},
            "sum_range": {"min": min(sums), "max": max(sums), "avg": round(sum(sums)/len(sums), 1)}
        }

        return str(result)

    def _extract_draw_type(self, text: str) -> str | None:
        for dt in ["brunchtime", "lunchtime", "drivetime", "teatime"]:
            if re.search(rf"\b{dt}\b", text.lower()):
                return dt
        match = re.search(r'"draw_type"\s*:\s*"(brunchtime|lunchtime|drivetime|teatime)"', text)
        return match.group(1) if match else None

    def _extract_limit(self, text: str) -> int | None:
        match = re.search(r'\b(\d+)\s*(draws|draw)', text.lower())
        return int(match.group(1)) if match else None
