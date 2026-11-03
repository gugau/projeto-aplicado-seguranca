def test_security_headers_are_present(client):
    response = client.get("/login")

    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"]


def test_hsts_is_only_added_over_https(client):
    insecure = client.get("/login", base_url="http://localhost")
    secure = client.get("/login", base_url="https://localhost")

    assert "Strict-Transport-Security" not in insecure.headers
    assert "max-age=31536000" in secure.headers["Strict-Transport-Security"]


def test_health_endpoint(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_oversized_request_is_rejected(client):
    client.get("/login")
    response = client.post(
        "/login",
        data={"username": "admin", "password": "x" * 20_000, "csrf_token": "x"},
    )

    assert response.status_code == 413


def test_production_cookie_flags(app):
    app.config["SESSION_COOKIE_SECURE"] = True
    response = app.test_client().get("/login", base_url="https://localhost")
    cookie = response.headers["Set-Cookie"]
    assert "Secure;" in cookie
    assert "HttpOnly;" in cookie
    assert "SameSite=Strict" in cookie


def test_validation_rejects_missing_and_plaintext_credentials(tmp_path):
    import pytest
    from app import create_app
    config = {"SECRET_KEY": "x" * 64, "APP_USERNAME": "admin", "APP_PASSWORD_HASH": "plaintext", "SESSION_STORE_DIR": str(tmp_path)}
    with pytest.raises(RuntimeError, match="scrypt"):
        create_app(config)
    config["APP_PASSWORD_HASH"] = ""
    with pytest.raises(RuntimeError, match="incompleta"):
        create_app(config)


def test_configured_username_is_html_escaped(client, app):
    app.config["APP_USERNAME"] = '<script>alert(1)</script>'
    client.get("/login")
    from tests.conftest import csrf_from_session
    client.post("/login", data={"username": app.config["APP_USERNAME"], "password": "Senha-Segura-123!", "csrf_token": csrf_from_session(client)})
    page = client.get("/dashboard").get_data(as_text=True)
    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;' in page
