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
