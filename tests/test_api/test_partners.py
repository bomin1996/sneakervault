def test_register_partner(client, auth_headers):
    res = client.post("/api/v1/partners/register", json={
        "business_name": "Test Store",
        "business_number": "123-45-67890",
        "contact_phone": "010-1234-5678",
    }, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["business_name"] == "Test Store"
    assert data["status"] == "pending"
    assert "api_key" in data


def test_register_partner_duplicate(client, auth_headers):
    payload = {
        "business_name": "Store",
        "business_number": "111-22-33333",
        "contact_phone": "010-0000-0000",
    }
    client.post("/api/v1/partners/register", json=payload, headers=auth_headers)
    res = client.post("/api/v1/partners/register", json=payload, headers=auth_headers)
    assert res.status_code == 409


def test_register_partner_unauthorized(client):
    res = client.post("/api/v1/partners/register", json={
        "business_name": "Store",
        "business_number": "999-99-99999",
        "contact_phone": "010-0000-0000",
    })
    assert res.status_code == 403
