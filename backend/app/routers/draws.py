from fastapi import APIRouter, Query
from app.database import get_draws
from app.models import DrawResponse

router = APIRouter(prefix="/api", tags=["draws"])

@router.get("/draws", response_model=list[DrawResponse])
def list_draws(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    draw_type: str = Query(None, pattern="^(brunchtime|lunchtime|drivetime|teatime)$")
):
    return get_draws(limit=limit, offset=offset, draw_type=draw_type)
