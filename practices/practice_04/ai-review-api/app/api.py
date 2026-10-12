from fastapi import FastAPI

from app.dependencies import review_service

app = FastAPI()


@app.post("/api/reviews")
def create_review(payload: dict) -> dict[str, str]:
    return review_service.review(payload["diff"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
