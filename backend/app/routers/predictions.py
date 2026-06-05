from fastapi import APIRouter, Query, HTTPException
from app.models import PredictionResponse
from app.database import get_cached_prediction, set_cached_prediction, get_draws_by_type_count
# Import run_analysis lazily – avoid heavy dependencies at import time
try:
    from backend.crew.crew import run_analysis
except Exception as e:
    run_analysis = None
    import logging
    logging.getLogger(__name__).warning(f"run_analysis could not be imported: {e}")

router = APIRouter(prefix="/api", tags=["predictions"])

CACHE_MAX_DAYS = 3

@router.post("/analyze", response_model=PredictionResponse)
def trigger_analysis(
    draw_type: str = Query(
        "lunchtime", pattern="^(brunchtime|lunchtime|drivetime|teatime)$"
    )
):
    try:
        cached = get_cached_prediction(draw_type, CACHE_MAX_DAYS)
        if cached:
            # cached is a JSON string; parse it back to dict for proper model validation
            import json
            return json.loads(cached)

        if get_draws_by_type_count(draw_type) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No historical draws are stored for '{draw_type}'. The current upstream data source only provides rows for the draw types already present in the database."
            )

        result = run_analysis(draw_type)
        # Build a proper PredictionResponse payload
        from datetime import datetime
        import json
        prediction_payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "draw_type": draw_type,
            "tiers": result.get("tiers", []),
            "analysis": result.get("analysis", {}),
        }
        # Cache the JSON string of the payload
        set_cached_prediction(draw_type, json.dumps(prediction_payload))
        return {
            "status": "complete",
            "result": prediction_payload,
            "cached": False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
