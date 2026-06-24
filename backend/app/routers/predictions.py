from fastapi import APIRouter, Query, HTTPException
from app.models import PredictionResponse
from app.database import get_cached_prediction, set_cached_prediction, get_draws_by_type_count
# Import run_analysis lazily – avoid heavy dependencies at import time
from crew.crew import run_analysis

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

        # Run the crew analysis and handle potential errors
        try:
            result = run_analysis(draw_type)
        except Exception as crew_err:
            logging.getLogger(__name__).error(f"Crew analysis failed: {crew_err}")
            raise HTTPException(status_code=500, detail="Crew analysis failed")
        # The crew returns a JSON string; ensure we have a dict (robust handling)
        import json
        try:
            if isinstance(result, (str, bytes)):
                result = json.loads(result)
        except Exception:
            # If parsing fails, default to empty dict so .get is safe
            result = {}
        # Build a proper PredictionResponse payload
        from datetime import datetime
        prediction_payload = {
            "generated_at": datetime.utcnow().isoformat(),
            "draw_type": draw_type,
            "tiers": result.get("tiers", []),
            "analysis": result.get("analysis", {}),
        }
        # Cache the JSON string of the payload
        set_cached_prediction(draw_type, json.dumps(prediction_payload))
        import json
        return {
            "status": "complete",
            "generated_at": prediction_payload["generated_at"],
            "draw_type": prediction_payload["draw_type"],
            "tiers": prediction_payload["tiers"],
            "analysis": prediction_payload["analysis"],
            "cached": False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
