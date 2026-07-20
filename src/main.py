from auth import get_api_key
from routers import router as cosmic_missions_router
import os
from fastapi import FastAPI, Depends, HTTPException

app=FastAPI()

app.include_router(cosmic_missions_router)

@app.get("/health", response_model=dict)
def health_check():
    return {"status": "ok"}