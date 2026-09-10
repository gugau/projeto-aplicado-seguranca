from __future__ import annotations

import hmac
import secrets
import time
import uuid
from collections import defaultdict, deque
from functools import wraps
from threading import Lock

from flask import Flask, abort, g, redirect, request, session, url_for


class LoginRateLimiter:
    """Limitador simples adequado a uma instância do protótipo."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_blocked(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            attempts = self._attempts[key]
            self._discard_expired(attempts, now)
            return len(attempts) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            attempts = self._attempts[key]
            self._discard_expired(attempts, now)
            attempts.append(now)

    def clear(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def _discard_expired(self, attempts: deque[float], now: float) -> None:
        threshold = now - self.window_seconds
        while attempts and attempts[0] < threshold:
            attempts.popleft()


login_limiter = LoginRateLimiter()


def configure_security(app: Flask) -> None:
    @app.before_request
    def attach_request_context() -> None:
        g.request_id = uuid.uuid4().hex
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)

    @app.after_request
    def set_security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = g.get("request_id", "unknown")
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


def csrf_token() -> str:
    return session.get("csrf_token", "")


def validate_csrf() -> None:
    expected = session.get("csrf_token", "")
    received = request.form.get("csrf_token", "")
    if not expected or not received or not hmac.compare_digest(expected, received):
        abort(400)


def rotate_csrf_token() -> None:
    session["csrf_token"] = secrets.token_urlsafe(32)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated") or not session.get("username"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def rate_limit_key(username: str) -> str:
    address = request.remote_addr or "unknown"
    return f"{address}:{username.casefold()}"
