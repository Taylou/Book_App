"""E2E fixtures: run the *real* app on a throwaway Postgres DB in a background
thread, with CSRF enabled (real browser flow), and point Playwright at it.

Requires Postgres running and a `bookapp_test` database:
    docker compose up -d
    docker compose exec db createdb -U bookapp bookapp_test
"""
import os
import threading

import pytest
from dotenv import load_dotenv
from werkzeug.serving import make_server

from app import create_app
from models import Author, Book, db

# Load .env.test if it exists; otherwise fall back to local defaults so a fresh
# clone can still run E2E without that (gitignored) file.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env.test"))

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://bookapp:bookapp@localhost:5432/bookapp_test"
)
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "test-secret-not-for-production")

E2E_CONFIG = {
    "TESTING": True,
    "SECRET_KEY": SECRET_KEY,
    "SQLALCHEMY_DATABASE_URI": DATABASE_URL,
    # CSRF stays ON — the browser submits the rendered hidden token.
    "WTF_CSRF_ENABLED": True,
}

# Deterministic dataset so smoke/search assertions are stable.
SEED_BOOKS = [
    ("The Hobbit", ["J.R.R. Tolkien"]),
    ("Dune", ["Frank Herbert"]),
    ("Mystery of the Test Suite", ["Ada Lovelace", "Grace Hopper"]),
]


def _seed():
    db.drop_all()
    db.create_all()
    for title, author_names in SEED_BOOKS:
        book = Book(title=title)
        for name in author_names:
            author = Author.query.filter_by(name=name).first() or Author(name=name)
            book.authors.append(author)
        db.session.add(book)
    db.session.commit()


@pytest.fixture(scope="session")
def live_server():
    """Start the app on an ephemeral port; yield the base URL."""
    app = create_app(E2E_CONFIG)
    with app.app_context():
        _seed()

    srv = make_server("127.0.0.1", 0, app, threaded=True)
    port = srv.socket.getsockname()[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}"

    srv.shutdown()
    thread.join(timeout=5)
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def base_url(live_server):
    """Override pytest-playwright's base_url so page.goto('/') hits the app."""
    return live_server
