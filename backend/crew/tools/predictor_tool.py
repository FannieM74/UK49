from langchain.tools import BaseTool
from app.database import get_connection
import json
import re
from crew.tools.strategies import STRATEGIES, get_rows


class PredictionTool(BaseTool):
    name: str = "Prediction Generator"
    description: str = "Generates tiered predictions (2+bonus through 6+bonus) using the specified strategy."

    def _run(self, input_str: str = "") -> str:
        draw_type = self._extract_draw_type(input_str) or "lunchtime"
        method = self._extract_method(input_str) or "frequency"
        limit = 50

        rows = get_rows(draw_type, limit)
        if not rows:
            return json.dumps({"error": "No data found"})

        strategy = STRATEGIES.get(method, STRATEGIES["frequency"])
        tiers = strategy(rows)
        return json.dumps(tiers)

    def _extract_draw_type(self, text: str) -> str | None:
        for dt in ["brunchtime", "lunchtime", "drivetime", "teatime"]:
            if re.search(rf"\b{dt}\b", text.lower()):
                return dt
        match = re.search(r'"draw_type"\s*:\s*"(brunchtime|lunchtime|drivetime|teatime)"', text)
        if match:
            return match.group(1)
        return None

    def _extract_method(self, text: str) -> str | None:
        for m in STRATEGIES:
            if re.search(rf"\b{m}\b", text.lower()):
                return m
        match = re.search(r'"method"\s*:\s*"(\w+)"', text)
        return match.group(1) if match else None
