"""
Tests for user management endpoints:
  POST   /users/
  GET    /users/
  GET    /users/{id}
  PATCH  /users/{id}
  DELETE /users/{id}
"""
import pytest


def test_admin_can_create_user(client, auth_headers):
    r = client.post("/users/", headers=auth_headers["admin"], json={
        "username": "new_user_1", "email": "new1@test.com",
        "password": "pass1234", "role": "viewer"
    })
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "new_user_1"
    assert body["role"] == "viewer"
    assert "hashed_password" not in body


def test_viewer_cannot_create_user(client, auth_headers):
    r = client.post("/users/", headers=auth_headers["viewer"], json={
        "username": "should_fail", "email": "fail@test.com", "password": "pass1234"
    })
    assert r.status_code == 403


def test_analyst_cannot_create_user(client, auth_headers):
    r = client.post("/users/", headers=auth_headers["analyst"], json={
        "username": "should_fail2", "email": "fail2@test.com", "password": "pass1234"
    })
    assert r.status_code == 403


def test_duplicate_username_returns_400(client, auth_headers):
    r = client.post("/users/", headers=auth_headers["admin"], json={
        "username": "t_admin", "email": "unique_email@test.com", "password": "pass1234"
    })
    assert r.status_code == 400
    assert "Username" in r.json()["detail"]


def test_duplicate_email_returns_400(client, auth_headers):
    r = client.post("/users/", headers=auth_headers["admin"], json={
        "username": "totally_unique_name", "email": "t_admin@test.com", "password": "pass1234"
    })
    assert r.status_code == 400
    assert "Email" in r.json()["detail"]


def test_admin_can_list_users(client, auth_headers, seeded_users):
    r = client.get("/users/", headers=auth_headers["admin"])
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 3  # at least the 3 seeded users


def test_list_users_filter_by_role(client, auth_headers):
    r = client.get("/users/?role=viewer", headers=auth_headers["admin"])
    assert r.status_code == 200
    for user in r.json():
        assert user["role"] == "viewer"


def test_admin_can_get_user_by_id(client, auth_headers, seeded_users):
    admin_id = seeded_users["admin"].id
    r = client.get(f"/users/{admin_id}", headers=auth_headers["admin"])
    assert r.status_code == 200
    assert r.json()["id"] == admin_id


def test_get_nonexistent_user_returns_404(client, auth_headers):
    r = client.get("/users/999999", headers=auth_headers["admin"])
    assert r.status_code == 404


def test_admin_can_update_user_role(client, auth_headers, seeded_users):
    viewer_id = seeded_users["viewer"].id
    r = client.patch(f"/users/{viewer_id}", headers=auth_headers["admin"], json={"role": "analyst"})
    assert r.status_code == 200
    assert r.json()["role"] == "analyst"
    # Reset back
    client.patch(f"/users/{viewer_id}", headers=auth_headers["admin"], json={"role": "viewer"})


def test_admin_cannot_deactivate_own_account(client, auth_headers, seeded_users):
    admin_id = seeded_users["admin"].id
    r = client.patch(f"/users/{admin_id}", headers=auth_headers["admin"], json={"is_active": False})
    assert r.status_code == 400
    assert "deactivate" in r.json()["detail"].lower()


def test_admin_cannot_delete_own_account(client, auth_headers, seeded_users):
    admin_id = seeded_users["admin"].id
    r = client.delete(f"/users/{admin_id}", headers=auth_headers["admin"])
    assert r.status_code == 400
