from __future__ import annotations

from flask import Blueprint, abort, current_app, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .security import (
    csrf_token,
    login_limiter,
    login_required,
    rate_limit_key,
    rotate_csrf_token,
    validate_csrf,
)


auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.app_context_processor
def inject_csrf_token():
    return {"csrf_token": csrf_token}


@auth_blueprint.get("/")
def index():
    if session.get("authenticated"):
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("auth.dashboard"))

    error = None
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password or len(username) > 80 or len(password) > 256:
            error = "Usuário ou senha inválidos."
        else:
            key = rate_limit_key(username)
            if login_limiter.is_blocked(key):
                current_app.logger.warning(
                    "auth_rate_limited ip=%s request_id=%s",
                    request.remote_addr,
                    g.request_id,
                )
                abort(429)

            valid_username = username == current_app.config["APP_USERNAME"]
            valid_password = check_password_hash(
                current_app.config["APP_PASSWORD_HASH"], password
            )

            if valid_username and valid_password:
                login_limiter.clear(key)
                session.clear()
                session.permanent = True
                session["authenticated"] = True
                session["username"] = current_app.config["APP_USERNAME"]
                rotate_csrf_token()
                current_app.logger.info(
                    "auth_success ip=%s user=%s",
                    request.remote_addr,
                    current_app.config["APP_USERNAME"],
                )
                return redirect(url_for("auth.dashboard"))

            login_limiter.record_failure(key)
            current_app.logger.warning(
                "auth_failure ip=%s username_length=%s",
                request.remote_addr,
                len(username),
            )
            error = "Usuário ou senha inválidos."

    return render_template("login.html", error=error)


@auth_blueprint.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session["username"])


@auth_blueprint.post("/logout")
@login_required
def logout():
    validate_csrf()
    username = session.get("username", "unknown")
    session.clear()
    current_app.logger.info("logout_success user=%s", username)
    return redirect(url_for("auth.login"))


@auth_blueprint.get("/healthz")
def healthz():
    return {"status": "ok"}
