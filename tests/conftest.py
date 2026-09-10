import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.security import login_limiter


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-with-at-least-32-characters",
            "APP_USERNAME": "admin",
            "APP_PASSWORD_HASH": generate_password_hash("Senha-Segura-123!"),
            "SESSION_COOKIE_SECURE": False,
        }
    )
    login_limiter._attempts.clear()
    yield application
    login_limiter._attempts.clear()


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_from_session(client) -> str:
    with client.session_transaction() as session:
        return session["csrf_token"]
