def test_admin_list_partners(client, admin_headers, partner_headers):
    res = client.get("/api/v1/admin/partners", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_admin_list_partners_unauthorized(client, auth_headers):
    res = client.get("/api/v1/admin/partners", headers=auth_headers)
    assert res.status_code == 403


def test_admin_get_partner(client, admin_headers, partner_headers, db):
    from app.models.partner import Partner
    partner = db.query(Partner).first()

    res = client.get(f"/api/v1/admin/partners/{partner.id}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["id"] == partner.id


def test_admin_get_partner_not_found(client, admin_headers):
    res = client.get("/api/v1/admin/partners/99999", headers=admin_headers)
    assert res.status_code == 404


def test_admin_update_partner_status(client, admin_headers, partner_headers, db):
    from app.models.partner import Partner
    partner = db.query(Partner).first()

    res = client.patch(f"/api/v1/admin/partners/{partner.id}", json={
        "status": "suspended",
    }, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "suspended"


def test_admin_update_partner_tier(client, admin_headers, partner_headers, db):
    from app.models.partner import Partner
    partner = db.query(Partner).first()

    res = client.patch(f"/api/v1/admin/partners/{partner.id}", json={
        "tier": "gold",
    }, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["tier"] == "gold"


def test_admin_list_products(client, admin_headers, sample_product):
    res = client.get("/api/v1/admin/products", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1


def test_admin_stats(client, admin_headers, partner_headers, sample_product):
    res = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_partners" in data
    assert "total_products" in data
    assert "active_products" in data


def test_admin_stats_unauthorized(client, auth_headers):
    res = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert res.status_code == 403


def test_no_token_returns_403(client):
    res = client.get("/api/v1/admin/stats")
    assert res.status_code == 403
