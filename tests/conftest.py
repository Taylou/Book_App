"""Shared fixtures for the fast test layers (backend + API).

These run against an in-memory SQLite database — no Docker required. The E2E
layer has its own conftest (tests/e2e/conftest.py) that uses real Postgres.
"""
import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from models import Author, Book, User, db

TEST_CONFIG = {
    "TESTING": True,
    "SECRET_KEY": "5dec1f49940bd28f389fc47407b82151f7b54f834ef1dbed80b0edb1de3ef98a",
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "WTF_CSRF_ENABLED": False,
    # Keep a single shared connection so the in-memory DB created by the
    # factories is visible to the test client (the standard SQLite-:memory:
    # testing pattern — without this each connection gets its own empty DB).
    "SQLALCHEMY_ENGINE_OPTIONS": {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    },
}


@pytest.fixture
def app():
    """A fresh app + empty schema per test (function-scoped for isolation)."""
    app = create_app(TEST_CONFIG)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app, make_user):
    """A test client with a logged-in user (CSRF is disabled in TEST_CONFIG)."""
    make_user(username="tester", email="tester@example.com", password="secret123")
    client = app.test_client()
    client.post("/auth/login", data={"email": "tester@example.com", "password": "secret123"})
    return client


@pytest.fixture
def make_user(app):
    """Factory: create and persist a User. Returns the User instance."""
    def _make_user(username="alice", email="alice@example.com", password="secret123"):
        with app.app_context():
            user = User(username=username, email=email.lower())
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return User.query.filter_by(email=email.lower()).first()
    return _make_user


@pytest.fixture
def make_book(app):
    """Factory: create and persist a Book with optional comma-separated authors."""
    def _make_book(title="Test Book", authors="Test Author", synopsis=None, cover=None):
        with app.app_context():
            book = Book(title=title, synopsis=synopsis, cover=cover)
            for name in [n.strip() for n in authors.split(",") if n.strip()]:
                author = Author.query.filter_by(name=name).first() or Author(name=name)
                book.authors.append(author)
            db.session.add(book)
            db.session.commit()
            return Book.query.filter_by(title=title).first()
    return _make_book
