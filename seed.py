"""Populate the database with books from the Open Library search API.

Usage:  python seed.py
Idempotent: skips books whose title already exists.
"""
import sys

import requests

from app import create_app
from models import Author, Book, db

SUBJECTS = ["fantasy", "science fiction", "history", "mystery"]
PER_SUBJECT = 20
SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"


def _get_or_create_author(name: str) -> Author:
    author = Author.query.filter_by(name=name).first()
    if author is None:
        author = Author(name=name)
        db.session.add(author)
        db.session.flush()
    return author


def _first_sentence(doc: dict) -> str | None:
    fs = doc.get("first_sentence")
    if isinstance(fs, list) and fs:
        return fs[0] if isinstance(fs[0], str) else None
    if isinstance(fs, str):
        return fs
    return None


def fetch_subject(subject: str) -> list[dict]:
    resp = requests.get(
        SEARCH_URL,
        params={"q": subject, "limit": PER_SUBJECT, "fields": "title,author_name,cover_i,first_sentence"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("docs", [])


def seed() -> int:
    inserted = 0
    for subject in SUBJECTS:
        print(f"Fetching subject: {subject}...")
        try:
            docs = fetch_subject(subject)
        except requests.RequestException as exc:
            print(f"  ! failed to fetch {subject}: {exc}", file=sys.stderr)
            continue

        for doc in docs:
            title = doc.get("title")
            if not title:
                continue
            if Book.query.filter_by(title=title).first():
                continue

            cover = COVER_URL.format(cover_id=doc["cover_i"]) if doc.get("cover_i") else None
            book = Book(title=title, synopsis=_first_sentence(doc), cover=cover)
            for name in doc.get("author_name", []) or []:
                book.authors.append(_get_or_create_author(name))
            db.session.add(book)
            inserted += 1
            print(f"  + {title}")

        db.session.commit()

    return inserted


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        count = seed()
        total = Book.query.count()
        print(f"\nInserted {count} new book(s). Total in DB: {total}.")
