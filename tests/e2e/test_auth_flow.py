"""Auth journey: register -> auto-login -> logout, plus a bad-login attempt.

Tests share a session-scoped database, so each uses a distinct account to stay
independent (registration rejects duplicate username/email).
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

PASSWORD = "secret123"


def _register(page: Page, who: str):
    username, email = who, f"{who}@example.com"
    page.goto("/auth/register", wait_until="domcontentloaded")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password", exact=True).fill(PASSWORD)
    page.get_by_label("Confirm password").fill(PASSWORD)
    page.get_by_role("button", name="Register").click()
    return username, email


def test_register_logs_user_in(page: Page):
    username, _ = _register(page, "reg_user")
    # After registering you're redirected to the book list, logged in.
    expect(page.get_by_text(f"Hi, {username}")).to_be_visible()
    expect(page.get_by_role("link", name="Logout")).to_be_visible()


def test_logout_returns_to_login(page: Page):
    _register(page, "logout_user")
    page.get_by_role("link", name="Logout").click()
    expect(page.get_by_role("heading", name="Log in")).to_be_visible()
    expect(page.get_by_role("link", name="Login")).to_be_visible()


def test_login_with_wrong_password_shows_error(page: Page):
    _, email = _register(page, "badpw_user")
    page.get_by_role("link", name="Logout").click()

    page.goto("/auth/login", wait_until="domcontentloaded")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password", exact=True).fill("wrong-password")
    page.get_by_role("button", name="Log in").click()

    expect(page.get_by_text("Invalid email or password.")).to_be_visible()
