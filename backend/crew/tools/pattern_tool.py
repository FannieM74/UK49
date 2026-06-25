from langchain.tools import BaseTool
from collections import Counter
from app.database import get_connection
import re
import json


class PatternAnalysisTool(BaseTool):
    name: str = "Pattern Analysis"
    description: str = "Analyzes delta patterns, sequential pairs, positional frequency, and overdue numbers."

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

        deltas = []
        pairs = []

        for r in rows:
            nums = sorted([r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]])
            for i in range(len(nums)-1):
                deltas.append(nums[i+1] - nums[i])
            for i in range(len(nums)):
                for j in range(i+1, len(nums)):
                    pairs.append((nums[i], nums[j]))

        delta_freq = Counter(deltas)
        pair_freq = Counter(pairs)

        drawn_numbers = set()
        for r in rows:
            for n in [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]]:
                drawn_numbers.add(n)
        overdue = sorted([n for n in range(1, 50) if n not in drawn_numbers])

        result = {
            "common_deltas": [{"delta": d, "count": c} for d, c in delta_freq.most_common(5)],
            "common_pairs": [{"pair": list(p), "count": c} for p, c in pair_freq.most_common(5)],
            "overdue_numbers": overdue,
        }

        return json.dumps(result)

    def _extract_draw_type(self, text: str) -> str | None:
        for dt in ["brunchtime", "lunchtime", "drivetime", "teatime"]:
            if re.search(rf"\b{dt}\b", text.lower()):
                return dt
        match = re.search(r'"draw_type"\s*:\s*"(brunchtime|lunchtime|drivetime|teatime)"', text)
        return match.group(1) if match else None

    def _extract_limit(self, text: str) -> int | None:
        match = re.search(r'\b(\d+)\s*(draws|draw)', text.lower())
        return int(match.group(1)) if match else None
