"""Lab 2 E2E: book create / edit / delete, plus auth-gating.

Each test uses a unique title so it stays independent against the session-scoped
database and leaves the Lab-1 seed data intact.
"""
import re
import uuid

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _add_book(page: Page, title: str, authors: str = "Test Author"):
    page.get_by_role("link", name="Add Book").click()
    page.get_by_label("Title").fill(title)
    page.get_by_label("Authors").fill(authors)  # "Authors (comma-separated)"
    page.get_by_role("button", name="Save").click()


def test_add_book_appears_in_list(logged_in_page: Page):
    page = logged_in_page
    title = f"E2E Add {uuid.uuid4().hex[:6]}"
    _add_book(page, title)
    expect(page.locator(".alert-success")).to_be_visible()
    expect(page.get_by_role("heading", name=title)).to_be_visible()


def test_edit_book_updates_card(logged_in_page: Page):
    page = logged_in_page
    title = f"E2E Edit {uuid.uuid4().hex[:6]}"
    new_title = f"{title} (revised)"
    _add_book(page, title)

    card = page.locator(".book-card").filter(has_text=title)
    card.get_by_role("link", name="Edit").click()
    page.get_by_label("Title").fill(new_title)
    page.get_by_role("button", name="Save").click()

    expect(page.get_by_role("heading", name=new_title)).to_be_visible()
    # The old, unrevised title no longer exists as a heading on its own.
    expect(page.get_by_role("heading", name=title, exact=True)).to_have_count(0)


def test_delete_book_removes_card(logged_in_page: Page):
    page = logged_in_page
    title = f"E2E Delete {uuid.uuid4().hex[:6]}"
    _add_book(page, title)

    # The delete button triggers a JS confirm() dialog — auto-accept it once.
    page.once("dialog", lambda dialog: dialog.accept())
    card = page.locator(".book-card").filter(has_text=title)
    card.get_by_role("button", name="Delete").click()

    expect(page.get_by_role("heading", name=title, exact=True)).to_have_count(0)


def test_add_book_requires_login(page: Page):
    # Logged-out: a protected route bounces to the login page.
    page.goto("/books/new", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r"/auth/login"))
