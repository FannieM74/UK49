from fastapi import APIRouter, HTTPException
from app.models import ScrapeResponse
from backend.crew.tools.scraper_tool import UK49ScraperTool
from app.database import get_draws_count, clear_prediction_cache

router = APIRouter(prefix="/api", tags=["scrape"])

@router.post("/scrape", response_model=ScrapeResponse)
def trigger_scrape():
    try:
        tool = UK49ScraperTool()
        before = get_draws_count()
        result = tool._run(start_date="2026-01-01")
        after = get_draws_count()
        if after > before:
            clear_prediction_cache()
        return ScrapeResponse(
            message=result,
            draws_added=after - before
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
