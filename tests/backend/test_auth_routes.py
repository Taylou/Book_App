"""Lab 3 backend: auth routes via the Flask test client (CSRF disabled)."""
from models import User


def test_register_creates_user_and_logs_in(client, app):
    resp = client.post(
        "/auth/register",
        data={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "secret123",
            "confirm": "secret123",
        },
    )
    assert resp.status_code == 302  # redirected to the book list
    with app.app_context():
        assert User.query.filter_by(email="newbie@example.com").first() is not None
    # The session is now authenticated: a protected page renders.
    assert client.get("/books/new").status_code == 200


def test_duplicate_email_is_rejected(client, make_user, app):
    make_user(username="exists", email="dupe@example.com")
    resp = client.post(
        "/auth/register",
        data={
            "username": "another",
            "email": "dupe@example.com",
            "password": "secret123",
            "confirm": "secret123",
        },
    )
    assert resp.status_code == 200                    # form re-rendered, not redirected
    assert b"Email already registered." in resp.data
    with app.app_context():
        assert User.query.filter_by(email="dupe@example.com").count() == 1


def test_duplicate_username_is_rejected(client, make_user, app):
    make_user(username="taken", email="first@example.com")
    resp = client.post(
        "/auth/register",
        data={
            "username": "taken",
            "email": "second@example.com",
            "password": "secret123",
            "confirm": "secret123",
        },
    )
    assert resp.status_code == 200
    assert b"Username already taken." in resp.data
    with app.app_context():
        assert User.query.filter_by(email="second@example.com").first() is None


def test_login_then_logout(client, make_user):
    make_user(username="lo", email="lo@example.com", password="secret123")

    login = client.post("/auth/login", data={"email": "lo@example.com", "password": "secret123"})
    assert login.status_code == 302
    assert client.get("/books/new").status_code == 200      # authenticated

    logout = client.get("/auth/logout")
    assert logout.status_code == 302
    after = client.get("/books/new")                        # protected again
    assert after.status_code == 302
    assert "/auth/login" in after.headers["Location"]


def test_new_book_requires_login(client):
    resp = client.get("/books/new")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
