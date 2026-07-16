from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import CosmicMission
from schemas import CosmicMissionBase, CosmicMissionCreate, CosmicMissionPut, CosmicMissionUpdate
from routers import router as cosmic_missions_router

app=FastAPI()

app.include_router(cosmic_missions_router)

@app.get("/health", response_model=dict)
def health_check():
    return {"status": "ok"}