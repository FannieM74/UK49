import json
import logging
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from app.models import PredictionResponse
from app.database import get_cached_prediction, set_cached_prediction, get_draws_by_type_count
from crew.tools.predictor_tool import PredictionTool
from crew.tools.analysis_tool import FrequencyAnalysisTool
from crew.tools.pattern_tool import PatternAnalysisTool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["predictions"])
CACHE_MAX_DAYS = 3


def normalize_predictions(draw_type: str) -> dict:
    pred_tool = PredictionTool()
    analysis_tool = FrequencyAnalysisTool()
    pattern_tool = PatternAnalysisTool()

    raw_predictions = json.loads(pred_tool._run(input_str=draw_type))
    raw_analysis = analysis_tool._run(input_str=draw_type)
    raw_patterns = pattern_tool._run(input_str=draw_type)

    parsed_analysis = {}
    for src in [raw_analysis, raw_patterns]:
        try:
            d = json.loads(str(src))
            if d:
                parsed_analysis.update(d)
        except json.JSONDecodeError:
            pass

    tiers = []
    tier_order = ["2+bonus", "3+bonus", "4+bonus", "5+bonus", "6+bonus"]
    for key in tier_order:
        picks = raw_predictions.get(key, [])
        if picks:
            tiers.append({"tier": key, "picks": picks})

    return {"tiers": tiers, "analysis": parsed_analysis}


@router.get("/debug")
def debug_prediction(
    draw_type: str = Query("lunchtime", pattern="^(lunchtime|teatime)$")
):
    from crew.tools.predictor_tool import PredictionTool
    from crew.tools.analysis_tool import FrequencyAnalysisTool
    from crew.tools.pattern_tool import PatternAnalysisTool
    try:
        pred_result = PredictionTool()._run(input_str=draw_type)
        freq_result = FrequencyAnalysisTool()._run(input_str=draw_type)
        pat_result = PatternAnalysisTool()._run(input_str=draw_type)
        return {
            "prediction_raw": pred_result[:2000],
            "frequency_raw": freq_result[:2000],
            "pattern_raw": pat_result[:2000],
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


@router.post("/analyze", response_model=PredictionResponse)
def trigger_analysis(
    draw_type: str = Query(
        "lunchtime", pattern="^(lunchtime|teatime)$"
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
