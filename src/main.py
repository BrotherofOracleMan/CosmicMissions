from fastapi import FastAPI

from routers import router as cosmic_missions_router

app = FastAPI()

app.include_router(cosmic_missions_router)


@app.get("/health", response_model=dict)
def health_check():
    return {"status": "ok"}
