from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.dependencies import review_service

DIFF_LIMIT = 20000

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "invalid request"})


@app.post("/api/reviews")
def create_review(payload: dict):
    if "diff" not in payload or not isinstance(payload.get("diff"), str):
        if "diff" not in payload:
            return JSONResponse(status_code=422, content={"error": "diff is required"})
        return JSONResponse(status_code=422, content={"error": "diff must be a string"})
    diff = payload["diff"]
    if not diff.strip():
        return JSONResponse(status_code=400, content={"error": "diff is empty"})
    if len(diff) > DIFF_LIMIT:
        return JSONResponse(
            status_code=413, content={"error": "diff too large", "limit": DIFF_LIMIT}
        )
    return review_service.review(diff)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
