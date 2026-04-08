def test_get_price_history(client, partner_headers, sample_product):
    product_id = sample_product["id"]
    res = client.get(f"/api/v1/prices/{product_id}/history", headers=partner_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["product_id"] == product_id


def test_get_price_history_with_limit(client, partner_headers, sample_product):
    product_id = sample_product["id"]
    res = client.get(f"/api/v1/prices/{product_id}/history?limit=1", headers=partner_headers)
    assert res.status_code == 200
    assert len(res.json()) <= 1


def test_get_price_history_not_found(client, partner_headers):
    res = client.get("/api/v1/prices/99999/history", headers=partner_headers)
    assert res.status_code == 404


def test_get_price_trend(client, partner_headers, sample_product):
    product_id = sample_product["id"]
    res = client.get(f"/api/v1/prices/{product_id}/trend", headers=partner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == product_id
    assert "current_price" in data
    assert "min_price" in data
    assert "max_price" in data
    assert "avg_price" in data
    assert "price_change_rate" in data


def test_get_price_trend_not_found(client, partner_headers):
    res = client.get("/api/v1/prices/99999/trend", headers=partner_headers)
    assert res.status_code == 404


def test_get_ai_analysis(client, partner_headers, sample_product):
    product_id = sample_product["id"]
    res = client.get(f"/api/v1/prices/{product_id}/ai-analysis", headers=partner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == product_id
    assert "summary" in data
    assert "trend" in data
    assert "recommendation" in data


def test_get_ai_analysis_not_found(client, partner_headers):
    res = client.get("/api/v1/prices/99999/ai-analysis", headers=partner_headers)
    assert res.status_code == 404
