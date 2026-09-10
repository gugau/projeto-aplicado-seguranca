from __future__ import annotations

import logging
import os
from datetime import timedelta

from flask import Flask, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from .auth import auth_blueprint
from .security import configure_security


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        APP_USERNAME=os.getenv("APP_USERNAME"),
        APP_PASSWORD_HASH=os.getenv("APP_PASSWORD_HASH"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=os.getenv("APP_ENV", "production") != "development",
        PERMANENT_SESSION_LIFETIME=timedelta(
            minutes=int(os.getenv("SESSION_MINUTES", "30"))
        ),
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    _validate_configuration(app)
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
