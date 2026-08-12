from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

F = TypeVar("F", bound=Callable[..., Any])

limiter = Limiter(key_func=get_remote_address)


def limit(rate: str) -> Callable[[F], F]:
    return cast(Callable[[F], F], cast(Any, limiter).limit(rate))


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RateLimitExceeded)
    return _rate_limit_exceeded_handler(request, exc)


__all__ = ["RateLimitExceeded", "limit", "limiter", "rate_limit_exceeded_handler"]
