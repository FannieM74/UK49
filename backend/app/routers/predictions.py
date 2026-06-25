import json
import re
import logging
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from app.models import PredictionResponse
from app.database import get_cached_prediction, set_cached_prediction, get_draws_by_type_count
from crew.crew import run_analysis
from crew.tools.predictor_tool import PredictionTool
from crew.tools.analysis_tool import FrequencyAnalysisTool
from crew.tools.pattern_tool import PatternAnalysisTool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["predictions"])
CACHE_MAX_DAYS = 3


def extract_json(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def normalize_predictions(draw_type: str) -> dict:
    pred_tool = PredictionTool()
    analysis_tool = FrequencyAnalysisTool()
    pattern_tool = PatternAnalysisTool()

    raw_predictions = json.loads(pred_tool._run(input_str=draw_type))
    raw_analysis = analysis_tool._run(input_str=draw_type)
    raw_patterns = pattern_tool._run(input_str=draw_type)

    parsed_analysis = {}
    for src in [raw_analysis, raw_patterns]:
        d = extract_json(str(src))
        if d:
            parsed_analysis.update(d)

    tiers = []
    tier_order = ["2+bonus", "3+bonus", "4+bonus", "5+bonus", "6+bonus"]
    for key in tier_order:
        picks = raw_predictions.get(key, [])
        if picks:
            tiers.append({"tier": key, "picks": picks})

    return {"tiers": tiers, "analysis": parsed_analysis}


def extract_crew_output(result) -> str:
    if hasattr(result, "raw"):
        return result.raw
    if isinstance(result, (str, bytes)):
        return result if isinstance(result, str) else result.decode()
    return str(result)


@router.post("/analyze", response_model=PredictionResponse)
def trigger_analysis(
    draw_type: str = Query(
        "lunchtime", pattern="^(brunchtime|lunchtime|drivetime|teatime)$"
    )
):
    try:
        cached = get_cached_prediction(draw_type, CACHE_MAX_DAYS)
        if cached:
            return json.loads(cached)

        if get_draws_by_type_count(draw_type) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No historical draws are stored for '{draw_type}'."
            )

        try:
            result = run_analysis(draw_type)
        except Exception as crew_err:
            logger.error(f"Crew analysis failed: {crew_err}")
            raise HTTPException(status_code=500, detail="Crew analysis failed")

        raw_text = extract_crew_output(result)
        parsed = extract_json(raw_text)

        if parsed and ("tiers" in parsed or "2+bonus" in parsed):
            if "tiers" not in parsed:
                tiers = []
                tier_order = ["2+bonus", "3+bonus", "4+bonus", "5+bonus", "6+bonus"]
                for key in tier_order:
                    picks = parsed.get(key, [])
                    if picks:
                        tiers.append({"tier": key, "picks": picks})
                parsed["tiers"] = tiers
            if "analysis" not in parsed:
                parsed["analysis"] = {}
            prediction = parsed
        else:
            prediction = normalize_predictions(draw_type)

        payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "draw_type": draw_type,
            "tiers": prediction.get("tiers", []),
            "analysis": prediction.get("analysis", {}),
        }

        set_cached_prediction(draw_type, json.dumps(payload))
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
