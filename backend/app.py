"""
FastAPI application entry point.

Run locally:   uvicorn backend.app:app --reload
Interactive API docs (Swagger UI): http://localhost:8000/docs
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from backend.config import settings
from backend.routes import assignments, auth, courses, dashboard, submissions
from backend.utils.errors import ServiceError
from backend.utils.logger import get_logger
from cloud.database_service import init_db
from cloud.storage_service import StorageError

log = get_logger("app")

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    log.info("Portal started (env=%s, storage=%s)", settings.app_env, settings.storage_backend)
    yield


app = FastAPI(title="Cloud-Based Student Assignment Submission & Feedback Portal", version="1.0.0", lifespan=lifespan)

# CORS: only the configured frontend origin(s) may call the API from a browser.
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def access_log_and_security_headers(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    log.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, response.status_code, (time.time() - start) * 1000)
    return response


# ---- graceful failure handling: clients always get a clean JSON error ----
@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(StorageError)
async def storage_error_handler(_: Request, exc: StorageError):
    log.error("storage failure: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "File storage is temporarily unavailable. Please retry shortly."}, headers={"Retry-After": "10"})


@app.exception_handler(OperationalError)
async def db_error_handler(_: Request, exc: OperationalError):
    log.error("database failure: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "Database is temporarily unavailable. Please retry shortly."}, headers={"Retry-After": "10"})


@app.exception_handler(Exception)
async def unhandled_handler(_: Request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health", tags=["ops"])
def health():
    """Used by load balancers / uptime monitors."""
    return {"status": "ok"}


for r in (auth.router, courses.router, assignments.router, submissions.router, dashboard.router):
    app.include_router(r)
