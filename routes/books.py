from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from forms import BookForm
from models import Author, Book, db

books_bp = Blueprint("books", __name__)


def _parse_authors(csv_value: str) -> list[Author]:
    names = [n.strip() for n in csv_value.split(",") if n.strip()]
    authors = []
    for name in names:
        author = Author.query.filter_by(name=name).first()
        if author is None:
            author = Author(name=name)
            db.session.add(author)
        authors.append(author)
    return authors


@books_bp.route("/")
def list_books():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template("books.html", books=books)


@books_bp.route("/authors")
def list_authors():
    authors = Author.query.order_by(Author.name).all()
    return render_template("authors.html", authors=[a.name for a in authors])


@books_bp.route("/books/new", methods=["GET", "POST"])
@login_required
def new_book():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(
            title=form.title.data.strip(),
            synopsis=form.synopsis.data or None,
            cover=form.cover.data or None,
            created_by=current_user.id,
        )
        book.authors = _parse_authors(form.authors.data)
        db.session.add(book)
        db.session.commit()
        flash(f"Added “{book.title}”.", "success")
        return redirect(url_for("books.list_books"))

    return render_template("book_form.html", form=form, heading="Add a book")


@books_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(book_id: int):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    if form.validate_on_submit():
        book.title = form.title.data.strip()
        book.synopsis = form.synopsis.data or None
        book.cover = form.cover.data or None
        book.authors = _parse_authors(form.authors.data)
        db.session.commit()
        flash(f"Updated “{book.title}”.", "success")
        return redirect(url_for("books.list_books"))

    if not form.is_submitted():
        form.authors.data = ", ".join(book.author_names())

    return render_template("book_form.html", form=form, heading=f"Edit: {book.title}")


@books_bp.route("/books/<int:book_id>/delete", methods=["POST"])
@login_required
def delete_book(book_id: int):
    book = Book.query.get_or_404(book_id)
    title = book.title
    db.session.delete(book)
    db.session.commit()
    flash(f"Deleted “{title}”.", "info")
    return redirect(url_for("books.list_books"))
