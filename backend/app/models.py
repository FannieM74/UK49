from pydantic import BaseModel
from typing import Optional

class DrawResponse(BaseModel):
    id: int
    draw_date: str
    draw_type: str
    n1: int
    n2: int
    n3: int
    n4: int
    n5: int
    n6: int
    bonus: int

class PredictionPick(BaseModel):
    numbers: list[int]
    bonus: int
    probability: float

class PredictionTier(BaseModel):
    tier: str
    picks: list[PredictionPick]

class PredictionResponse(BaseModel):
    generated_at: str
    draw_type: str
    tiers: list[PredictionTier]
    analysis: dict

class ScrapeResponse(BaseModel):
    message: str
    draws_added: int
