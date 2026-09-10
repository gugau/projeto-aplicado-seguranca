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
