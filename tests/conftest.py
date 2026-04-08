import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app import database

SQLALCHEMY_TEST_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# SQLite doesn't support Enum natively — store as VARCHAR
@event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(bind=test_engine)

# Override engine before importing app to avoid MySQL connection on startup
database.engine = test_engine

from app.main import app, limiter  # noqa: E402
from app.api.v1 import auth as auth_module, prices as prices_module

limiter.enabled = False
auth_module.limiter.enabled = False
prices_module.limiter.enabled = False


# Mock Redis for all tests
@pytest.fixture(autouse=True)
def mock_redis():
    fake_store = {}

    mock = MagicMock()
    mock.get = lambda k: fake_store.get(k)
    mock.set = lambda k, v: fake_store.update({k: v})
    mock.setex = lambda k, t, v: fake_store.update({k: v})
    mock.exists = lambda k: 1 if k in fake_store else 0
    mock.delete = lambda k: fake_store.pop(k, None)
    mock.incr = lambda k: fake_store.update({k: str(int(fake_store.get(k, "0")) + 1)}) or fake_store[k]
    mock.ttl = lambda k: 900
    mock.expire = lambda k, t: None

    pipe_mock = MagicMock()
    pipe_mock.incr = lambda k: None
    pipe_mock.expire = lambda k, t: None
    pipe_mock.execute = lambda: None
    mock.pipeline = lambda: pipe_mock

    with patch("app.api.v1.auth.redis_client", mock), \
         patch("app.utils.security._redis_client", mock), \
         patch("app.services.ai_service._redis_client", mock):
        yield mock


@pytest.fixture
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, db):
    from app.models.user import User
    client.post("/api/v1/auth/register", json={
        "email": "admin@example.com",
        "password": "adminpass123",
        "name": "Admin User",
    })
    user = db.query(User).filter(User.email == "admin@example.com").first()
    user.is_admin = True
    db.commit()
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpass123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def partner_headers(client, db, auth_headers):
    from app.models.partner import Partner, PartnerStatus
    client.post("/api/v1/partners/register", json={
        "business_name": "Test Store",
        "business_number": "123-45-67890",
        "contact_phone": "010-1234-5678",
    }, headers=auth_headers)
    partner = db.query(Partner).first()
    partner.status = PartnerStatus.APPROVED
    db.commit()
    return auth_headers


@pytest.fixture
def sample_product(client, db, partner_headers):
    from app.models.product import Brand, Category
    brand = Brand(name="Nike", slug="nike")
    category = Category(name="Sneakers", slug="sneakers")
    db.add_all([brand, category])
    db.commit()
    db.refresh(brand)
    db.refresh(category)

    res = client.post("/api/v1/products", json={
        "brand_id": brand.id,
        "category_id": category.id,
        "model_number": "DQ8423-100",
        "name": "Nike Dunk Low Retro",
        "size": "270",
        "release_price": 139000,
        "current_price": 189000,
        "stock_quantity": 5,
    }, headers=partner_headers)
    return res.json()
