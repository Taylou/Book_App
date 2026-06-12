"""Lab 3 backend: model behavior (SQLite, no HTTP)."""
from models import Author, Book, User, book_authors, db


def test_password_round_trip(app):
    with app.app_context():
        user = User(username="bob", email="bob@example.com")
        user.set_password("hunter2")
        assert user.password_hash != "hunter2"      # stored as a hash
        assert user.check_password("hunter2") is True
        assert user.check_password("wrong") is False


def test_author_names(make_book, app):
    make_book(title="Book A", authors="Alice, Bob")
    with app.app_context():
        book = Book.query.filter_by(title="Book A").first()
        assert set(book.author_names()) == {"Alice", "Bob"}


def test_many_to_many_backref(make_book, app):
    make_book(title="Shared Book", authors="Shared Author")
    with app.app_context():
        author = Author.query.filter_by(name="Shared Author").first()
        assert "Shared Book" in [b.title for b in author.books]


def test_deleting_book_removes_join_rows_but_keeps_author(make_book, app):
    make_book(title="Doomed", authors="Keeper")
    with app.app_context():
        book = Book.query.filter_by(title="Doomed").first()
        book_id = book.id
        db.session.delete(book)
        db.session.commit()

        rows = db.session.execute(
            book_authors.select().where(book_authors.c.book_id == book_id)
        ).fetchall()
        assert rows == []                                    # join rows gone
        assert Author.query.filter_by(name="Keeper").first() is not None  # author kept
