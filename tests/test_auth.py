"""
Tests for authentication endpoints:
  POST /auth/login
  GET  /auth/me
"""


def test_login_as_admin_returns_token(client, seeded_users):
    r = client.post("/auth/login", data={"username": "t_admin", "password": "admin123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_as_analyst_returns_token(client, seeded_users):
    r = client.post("/auth/login", data={"username": "t_analyst", "password": "analyst123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_as_viewer_returns_token(client, seeded_users):
    r = client.post("/auth/login", data={"username": "t_viewer", "password": "viewer123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_returns_401(client, seeded_users):
    r = client.post("/auth/login", data={"username": "t_admin", "password": "wrongpass"})
    assert r.status_code == 401
    assert "Incorrect" in r.json()["detail"]


def test_login_nonexistent_user_returns_401(client):
    r = client.post("/auth/login", data={"username": "ghost_user", "password": "nopass"})
    assert r.status_code == 401


def test_get_me_returns_current_user(client, auth_headers, seeded_users):
    r = client.get("/auth/me", headers=auth_headers["admin"])
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "t_admin"
    assert body["role"] == "admin"


def test_get_me_without_token_returns_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_get_me_with_invalid_token_returns_401(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer totally.fake.token"})
    assert r.status_code == 401
