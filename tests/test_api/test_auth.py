def test_register(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "name": "New User",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "email_verify_token" in data


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "pass123", "name": "User"}
    client.post("/api/v1/auth/register", json=payload)
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409


def test_login_success(client):
    client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "password123",
        "name": "Login User",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "password123",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "password": "password123",
        "name": "User",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_refresh_token(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "password": "password123",
        "name": "Refresh User",
    })
    refresh_token = res.json()["refresh_token"]

    res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert "refresh_token" in res.json()


def test_refresh_token_invalid(client):
    res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid_token",
    })
    assert res.status_code == 401


def test_logout(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "logout@example.com",
        "password": "password123",
        "name": "Logout User",
    })
    token = res.json()["access_token"]

    res = client.post("/api/v1/auth/logout", headers={
        "Authorization": f"Bearer {token}",
    })
    assert res.status_code == 204


def test_verify_email(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "verify@example.com",
        "password": "password123",
        "name": "Verify User",
    })
    verify_token = res.json()["email_verify_token"]

    res = client.post(f"/api/v1/auth/verify-email?token={verify_token}")
    assert res.status_code == 200
    assert res.json()["message"] == "Email verified successfully"


def test_verify_email_already_verified(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "verified@example.com",
        "password": "password123",
        "name": "Verified User",
    })
    verify_token = res.json()["email_verify_token"]

    client.post(f"/api/v1/auth/verify-email?token={verify_token}")
    res = client.post(f"/api/v1/auth/verify-email?token={verify_token}")
    assert res.status_code == 200
    assert res.json()["message"] == "Email already verified"


def test_verify_email_invalid_token(client):
    res = client.post("/api/v1/auth/verify-email?token=invalid")
    assert res.status_code == 400
