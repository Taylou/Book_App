"""Smoke test: the home page loads, navbar renders, seeded books appear."""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def test_home_page_loads(page: Page):
    # domcontentloaded: don't block on external CDN/placeholder-image requests.
    page.goto("/", wait_until="domcontentloaded")
    expect(page).to_have_title("Books")
    # Navbar brand + primary links are present.
    expect(page.get_by_role("link", name="Book App")).to_be_visible()
    expect(page.get_by_role("link", name="Books")).to_be_visible()
    expect(page.get_by_role("link", name="Authors")).to_be_visible()


def test_seeded_books_render(page: Page):
    page.goto("/", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="The Hobbit")).to_be_visible()
    expect(page.get_by_role("heading", name="Dune")).to_be_visible()
