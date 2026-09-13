"""Uniform JSON errors: every failure returns {"error": {"code": ..., "message": ...}}."""
import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from app.llm.base import LLMError, LLMNotConfiguredError

log = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str = "bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _error(status_code: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, **extra}},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return _error(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Drop "input" so a 422 doesn't echo the whole resume back.
        errors = [{k: v for k, v in e.items() if k != "input"} for e in exc.errors()]
        summary = "; ".join(
            f"{'.'.join(str(p) for p in e['loc'] if p != 'body')}: {e['msg']}" for e in errors[:3]
        )
        return _error(422, "validation_error", summary or "Invalid request", details=jsonable_encoder(errors))

    @app.exception_handler(LLMNotConfiguredError)
    async def _llm_not_configured(_: Request, exc: LLMNotConfiguredError) -> JSONResponse:
        return _error(503, "llm_not_configured", str(exc))

    @app.exception_handler(LLMError)
    async def _llm_error(_: Request, exc: LLMError) -> JSONResponse:
        log.warning("LLM call failed: %s", exc)
        return _error(502, "llm_error", str(exc))

    @app.exception_handler(PyMongoError)
    async def _db_error(_: Request, exc: PyMongoError) -> JSONResponse:
        log.error("MongoDB error: %s", exc)
        return _error(
            503,
            "database_unavailable",
            "The database is unavailable. Check MONGODB_URI and that MongoDB is running.",
        )
