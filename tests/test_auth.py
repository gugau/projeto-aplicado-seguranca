from tests.conftest import csrf_from_session


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_requires_valid_csrf(client):
    client.get("/login")

    response = client.post(
        "/login",
        data={"username": "admin", "password": "Senha-Segura-123!", "csrf_token": "invalido"},
    )

    assert response.status_code == 400


def test_invalid_credentials_use_generic_message(client):
    client.get("/login")

    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "errada",
            "csrf_token": csrf_from_session(client),
        },
    )

    assert response.status_code == 200
    assert "Usuário ou senha inválidos" in response.get_data(as_text=True)


def test_login_dashboard_and_logout(client):
    client.get("/login")
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "Senha-Segura-123!",
            "csrf_token": csrf_from_session(client),
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Olá, admin" in dashboard.get_data(as_text=True)

    logout = client.post(
        "/logout",
        data={"csrf_token": csrf_from_session(client)},
    )
    assert logout.status_code == 302
    assert client.get("/dashboard").status_code == 302


def test_login_is_rate_limited_after_five_failures(client):
    client.get("/login")

    for _ in range(5):
        response = client.post(
            "/login",
            data={
                "username": "admin",
                "password": "errada",
                "csrf_token": csrf_from_session(client),
            },
        )
        assert response.status_code == 200

    blocked = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "errada",
            "csrf_token": csrf_from_session(client),
        },
    )
    assert blocked.status_code == 429


def test_logout_rejects_get(client):
    assert client.get("/logout").status_code == 405


def authenticate(client):
    client.get("/login")
    return client.post("/login", data={"username": "admin", "password": "Senha-Segura-123!", "csrf_token": csrf_from_session(client)})


def test_captured_cookie_is_revoked_after_logout(client, app):
    authenticate(client)
    captured = client.get_cookie("session").value
    from app import create_app
    other_worker = create_app(dict(app.config)).test_client()
    other_worker.set_cookie("session", captured)
    assert other_worker.get("/dashboard").status_code == 200
    client.post("/logout", data={"csrf_token": csrf_from_session(client)})
    client.set_cookie("session", captured)
    assert client.get("/dashboard").status_code == 302
    assert other_worker.get("/dashboard").status_code == 302


def test_session_expires_absolutely_even_with_activity(client, monkeypatch):
    import app.sessions as tickets
    now = tickets.time.time()
    authenticate(client)
    monkeypatch.setattr(tickets.time, "time", lambda: now + 1790)
    assert client.get("/dashboard").status_code == 200
    monkeypatch.setattr(tickets.time, "time", lambda: now + 1810)
    assert client.get("/dashboard").status_code == 302


def test_logout_requires_csrf_and_does_not_revoke_on_failure(client):
    authenticate(client)
    assert client.post("/logout", data={"csrf_token": "wrong"}).status_code == 400
    assert client.get("/dashboard").status_code == 200


def test_non_ascii_csrf_returns_bad_request(client):
    client.get("/login")
    assert client.post("/login", data={"csrf_token": "não-ascii"}).status_code == 400


def test_cookie_is_rotated_on_login(client):
    client.get("/login")
    before = client.get_cookie("session").value
    old_csrf = csrf_from_session(client)
    authenticate(client)
    assert client.get_cookie("session").value != before
    assert csrf_from_session(client) != old_csrf


def test_unsafe_next_url_is_not_used(client):
    client.get("/login")
    response = client.post("/login?next=https://example.org", data={"username": "admin", "password": "Senha-Segura-123!", "csrf_token": csrf_from_session(client)})
    assert response.headers["Location"] == "/dashboard"
