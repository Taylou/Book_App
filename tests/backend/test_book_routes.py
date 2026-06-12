"""Lab 3 backend: book CRUD routes via an authenticated test client."""
from models import Author, Book, db


def test_create_book(auth_client, app):
    resp = auth_client.post(
        "/books/new",
        data={"title": "Created Book", "authors": "A. Writer", "synopsis": "", "cover": ""},
    )
    assert resp.status_code == 302
    with app.app_context():
        book = Book.query.filter_by(title="Created Book").first()
        assert book is not None
        assert "A. Writer" in book.author_names()


def test_create_book_requires_title(auth_client, app):
    resp = auth_client.post(
        "/books/new",
        data={"title": "", "authors": "Someone", "synopsis": "", "cover": ""},
    )
    assert resp.status_code == 200          # re-rendered with a validation error
    with app.app_context():
        assert Book.query.count() == 0      # nothing persisted


def test_edit_book(auth_client, make_book, app):
    book_id = make_book(title="Old Title", authors="Author X").id
    resp = auth_client.post(
        f"/books/{book_id}/edit",
        data={"title": "New Title", "authors": "Author X", "synopsis": "", "cover": ""},
    )
    assert resp.status_code == 302
    with app.app_context():
        assert db.session.get(Book, book_id).title == "New Title"


def test_delete_book(auth_client, make_book, app):
    book_id = make_book(title="Throwaway", authors="Author Y").id
    resp = auth_client.post(f"/books/{book_id}/delete")
    assert resp.status_code == 302
    with app.app_context():
        assert db.session.get(Book, book_id) is None


def test_existing_author_is_reused(auth_client, app):
    auth_client.post(
        "/books/new",
        data={"title": "B1", "authors": "Shared", "synopsis": "", "cover": ""},
    )
    auth_client.post(
        "/books/new",
        data={"title": "B2", "authors": "Shared, New", "synopsis": "", "cover": ""},
    )
    with app.app_context():
        assert Author.query.filter_by(name="Shared").count() == 1   # not duplicated
        assert Author.query.filter_by(name="New").count() == 1
