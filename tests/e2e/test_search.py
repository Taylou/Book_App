"""Lab 2 E2E: the client-side search box filters cards (inline JS in books.html)."""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

SEARCH_PLACEHOLDER = "Search by title or author..."


def test_search_filters_books(page: Page):
    page.goto("/", wait_until="domcontentloaded")
    page.get_by_placeholder(SEARCH_PLACEHOLDER).fill("Dune")

    expect(page.get_by_role("heading", name="Dune")).to_be_visible()
    expect(page.get_by_role("heading", name="The Hobbit")).not_to_be_visible()


def test_clearing_search_restores_all(page: Page):
    page.goto("/", wait_until="domcontentloaded")
    search = page.get_by_placeholder(SEARCH_PLACEHOLDER)

    search.fill("Dune")
    expect(page.get_by_role("heading", name="The Hobbit")).not_to_be_visible()

    search.fill("")  # clearing the box re-shows every card
    expect(page.get_by_role("heading", name="The Hobbit")).to_be_visible()
