"""
Shared fixtures for all test modules.

Uses a separate SQLite test database (test_finance.db) so the production
finance.db is never touched during test runs.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.database import Base, get_db
from app.models import User, FinancialRecord, UserRole, RecordType
from app.auth import hash_password

TEST_DB_URL = "sqlite:///./test_finance.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once, drop them after the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(setup_database):
    return TestClient(app)


@pytest.fixture(scope="session")
def seeded_users(setup_database):
    """Insert admin, analyst, and viewer users used across all tests."""
    db = TestingSessionLocal()
    users = [
        User(username="t_admin",   email="t_admin@test.com",   full_name="Test Admin",
             hashed_password=hash_password("admin123"),   role=UserRole.admin,   is_active=True),
        User(username="t_analyst", email="t_analyst@test.com", full_name="Test Analyst",
             hashed_password=hash_password("analyst123"), role=UserRole.analyst, is_active=True),
        User(username="t_viewer",  email="t_viewer@test.com",  full_name="Test Viewer",
             hashed_password=hash_password("viewer123"),  role=UserRole.viewer,  is_active=True),
    ]
    db.add_all(users)
    db.commit()
    for u in users:
        db.refresh(u)
    db.close()
    return {u.role.value: u for u in users}


@pytest.fixture(scope="session")
def tokens(client, seeded_users):
    """Log in as each role and return their Bearer tokens."""
    def login(username, password):
        r = client.post("/auth/login", data={"username": username, "password": password})
        assert r.status_code == 200, f"Login failed for {username}: {r.text}"
        return r.json()["access_token"]

    return {
        "admin":   login("t_admin",   "admin123"),
        "analyst": login("t_analyst", "analyst123"),
        "viewer":  login("t_viewer",  "viewer123"),
    }


@pytest.fixture(scope="session")
def auth_headers(tokens):
    return {role: {"Authorization": f"Bearer {t}"} for role, t in tokens.items()}


@pytest.fixture(scope="session")
def sample_records(seeded_users, setup_database):
    """Insert a small, known set of records for dashboard / filter tests."""
    db = TestingSessionLocal()
    admin_id = seeded_users["admin"].id
    records = [
        FinancialRecord(amount=10000, type=RecordType.income,  category="Salary",    date=datetime(2024, 1, 15), created_by=admin_id),
        FinancialRecord(amount=2000,  type=RecordType.expense, category="Rent",      date=datetime(2024, 1, 20), created_by=admin_id),
        FinancialRecord(amount=5000,  type=RecordType.income,  category="Freelance", date=datetime(2024, 2, 10), created_by=admin_id),
        FinancialRecord(amount=1500,  type=RecordType.expense, category="Utilities", date=datetime(2024, 2, 18), created_by=admin_id),
    ]
    db.add_all(records)
    db.commit()
    ids = [r.id for r in records]
    db.close()
    return ids
