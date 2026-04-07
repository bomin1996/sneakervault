def test_register(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "name": "New User",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


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
    assert "access_token" in res.json()


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
