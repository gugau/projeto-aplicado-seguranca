from __future__ import annotations

import logging
import os
import re
from datetime import timedelta

from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from .auth import auth_blueprint
from .security import configure_security
from .sessions import SessionTickets


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        APP_USERNAME=os.getenv("APP_USERNAME"),
        APP_PASSWORD_HASH=os.getenv("APP_PASSWORD_HASH"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=os.getenv("APP_ENV", "production") != "development",
        SESSION_REFRESH_EACH_REQUEST=False,
        SESSION_STORE_DIR=os.getenv("SESSION_STORE_DIR", os.path.join(app.instance_path, "sessions")),
        PERMANENT_SESSION_LIFETIME=timedelta(
            minutes=int(os.getenv("SESSION_MINUTES", "30"))
        ),
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    _validate_configuration(app)
    app.extensions["session_tickets"] = SessionTickets(app.config["SESSION_STORE_DIR"])
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    configure_security(app)
    app.register_blueprint(auth_blueprint)
    _register_error_handlers(app)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return app


def _validate_configuration(app: Flask) -> None:
    if app.testing:
        return

    required = ("SECRET_KEY", "APP_USERNAME", "APP_PASSWORD_HASH")
    missing = [name for name in required if not app.config.get(name)]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Configuração segura incompleta. Defina as variáveis: {names}."
        )

    if len(str(app.config["SECRET_KEY"])) < 32:
        raise RuntimeError("SECRET_KEY deve possuir pelo menos 32 caracteres.")
    if not re.fullmatch(r"scrypt:(32768|65536|131072):8:1\$[A-Za-z0-9]+\$[a-f0-9]{128}", str(app.config["APP_PASSWORD_HASH"])):
        raise RuntimeError("APP_PASSWORD_HASH deve ser gerado por tools/generate_password_hash.py (scrypt).")
    if not 60 <= app.config["PERMANENT_SESSION_LIFETIME"].total_seconds() <= 86400:
        raise RuntimeError("SESSION_MINUTES deve estar entre 1 e 1440.")


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("error.html", code=400, message="Requisição inválida."), 400

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="Acesso negado."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Página não encontrada."), 404

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("error.html", code=413, message="Requisição muito grande."), 413

    @app.errorhandler(429)
    def too_many(_error):
        return render_template("error.html", code=429, message="Muitas tentativas. Aguarde e tente novamente."), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(
            "internal_error path=%s request_id=%s",
            request.path,
            getattr(request, "request_id", "unknown"),
        )
        return render_template("error.html", code=500, message="Erro interno. Tente novamente mais tarde."), 500
