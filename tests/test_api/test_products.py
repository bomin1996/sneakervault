def test_create_product(client, partner_headers, db):
    from app.models.product import Brand, Category
    brand = Brand(name="Adidas", slug="adidas")
    category = Category(name="Running", slug="running")
    db.add_all([brand, category])
    db.commit()
    db.refresh(brand)
    db.refresh(category)

    res = client.post("/api/v1/products", json={
        "brand_id": brand.id,
        "category_id": category.id,
        "model_number": "GW2871",
        "name": "Adidas Forum Low",
        "size": "275",
        "release_price": 119000,
        "current_price": 159000,
        "stock_quantity": 3,
    }, headers=partner_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Adidas Forum Low"
    assert data["current_price"] == 159000
    assert data["is_active"] is True


def test_list_products(client, partner_headers, sample_product):
    res = client.get("/api/v1/products", headers=partner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_get_product(client, partner_headers, sample_product):
    product_id = sample_product["id"]
    res = client.get(f"/api/v1/products/{product_id}", headers=partner_headers)
    assert res.status_code == 200
    assert res.json()["id"] == product_id


def test_get_product_not_found(client, partner_headers):
    res = client.get("/api/v1/products/99999", headers=partner_headers)
    assert res.status_code == 404


def test_update_product_price(client, partner_headers, sample_product):
    product_id = sample_product["id"]
    res = client.patch(f"/api/v1/products/{product_id}", json={
        "current_price": 210000,
    }, headers=partner_headers)
    assert res.status_code == 200
    assert res.json()["current_price"] == 210000


def test_delete_product_soft_delete(client, partner_headers, sample_product):
    product_id = sample_product["id"]
    res = client.delete(f"/api/v1/products/{product_id}", headers=partner_headers)
    assert res.status_code == 204

    res = client.get(f"/api/v1/products/{product_id}", headers=partner_headers)
    assert res.json()["is_active"] is False


def test_list_products_with_search(client, partner_headers, sample_product):
    res = client.get("/api/v1/products?search=Dunk", headers=partner_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


def test_list_products_pagination(client, partner_headers, sample_product):
    res = client.get("/api/v1/products?page=1&size=1", headers=partner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["size"] == 1


def test_create_product_unauthorized(client):
    res = client.post("/api/v1/products", json={
        "brand_id": 1,
        "category_id": 1,
        "model_number": "TEST-001",
        "name": "Test Product",
        "size": "270",
        "release_price": 100000,
        "current_price": 150000,
    })
    assert res.status_code == 403
