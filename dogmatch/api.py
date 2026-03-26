from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dogmatch.pipeline import (
    load_artifacts,
    append_feedback,
    predict_compatibility_matches,
    predict_return_risk,
)


app = FastAPI(title="AVDS Dog Matching + Adoption Risk", version="0.1.0")

_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


class PreferredTraits(BaseModel):
    size: str = Field(default="medium")
    age: str = Field(default="adult")
    temperament: str = Field(default="friendly")


class UserInput(BaseModel):
    housing_type: str = Field(default="apartment", description="apartment|house")
    yard_size_bucket: str = Field(default="none", description="none|small|medium|large")
    activity_level: str = Field(default="medium", description="low|medium|high")
    work_hours_away: float = Field(default=4, description="hours away from home per day")
    pet_experience: str = Field(default="some", description="none|some|expert")
    allergies: str = Field(default="none", description="none|mild|severe")
    preferred_traits: PreferredTraits = Field(default_factory=PreferredTraits)
    budget_monthly: float = Field(default=250, description="monthly budget in your currency")
    kids_in_household: int = Field(default=0, ge=0, le=1)
    other_pets_in_household: int = Field(default=0, ge=0, le=1)

    # Optional fairness/audit input. Not used by default in training.
    fairness_group: Optional[str] = Field(default=None, description="e.g. income_bracket=low|mid|high")


class DogInput(BaseModel):
    breed: str = Field(default="Mixed")
    age_years: float = Field(default=3.0, ge=0)
    size: str = Field(default="medium", description="small|medium|large")
    energy_level: str = Field(default="medium", description="low|medium|high")
    temperament: str = Field(default="friendly", description="friendly|shy|energetic|calm|aggressive")
    training_level: str = Field(default="medium", description="low|medium|high")
    special_needs: bool = Field(default=False)
    hypoallergenic: bool = Field(default=False)
    kid_compatibility: str = Field(default="medium", description="high|medium|low")
    other_pets_compatibility: str = Field(default="medium", description="high|medium|low")
    shelter_notes: Optional[str] = None


class MatchDogsRequest(BaseModel):
    user: UserInput
    candidate_dogs: List[DogInput] = Field(..., min_items=1)
    top_k: int = Field(default=5, ge=1, le=20)


class PredictRiskRequest(BaseModel):
    user: UserInput
    dog: DogInput


class FeedbackRequest(BaseModel):
    user: UserInput
    dog: DogInput
    returned: bool = Field(..., description="True if adopter returned the dog after adoption")


def _user_dict(user: UserInput) -> Dict[str, Any]:
    d = user.model_dump()
    # Pipeline expects 'preferred_traits' and 'allergies' keys at top level.
    d["preferred_traits"] = user.preferred_traits.model_dump()
    return d


def _dog_dict(dog: DogInput) -> Dict[str, Any]:
    return dog.model_dump()


@lru_cache(maxsize=1)
def _get_artifacts() -> Dict[str, Any]:
    # If artifacts don't exist, pipeline falls back to rules-only.
    return load_artifacts()


@app.post("/match_dogs")
def match_dogs(req: MatchDogsRequest) -> Dict[str, Any]:
    artifacts = _get_artifacts()

    user = _user_dict(req.user)
    candidate_dogs = [_dog_dict(d) for d in req.candidate_dogs]

    return predict_compatibility_matches(
        user=user, candidate_dogs=candidate_dogs, artifacts=artifacts, top_k=req.top_k
    )


@app.post("/predict_risk")
def predict_risk(req: PredictRiskRequest) -> Dict[str, Any]:
    artifacts = _get_artifacts()

    user = _user_dict(req.user)
    dog = _dog_dict(req.dog)

    return predict_return_risk(user=user, dog=dog, artifacts=artifacts)


@app.post("/feedback")
def feedback(req: FeedbackRequest) -> Dict[str, Any]:
    # Bonus: feedback loop endpoint.
    # In production, you’d store this in a DB, then retrain on a schedule.
    user = _user_dict(req.user)
    dog = _dog_dict(req.dog)
    append_feedback(user=user, dog=dog, returned=int(req.returned))
    return {"ok": True, "returned": bool(req.returned)}

