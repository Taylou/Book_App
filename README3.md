# Book App — Testing Guide 3.0 (Continuation: Labs 2 & 3)

This continues [`README2.md`](README2.md) (Lab 1 — foundation + first E2E). It covers the
next two lab sessions:

- **Lab 2** — Expanded **E2E** coverage (book CRUD, client-side search, auth-gating).
- **Lab 3** — **Backend** tests (models, auth routes, book routes) on fast in-memory SQLite.

> Benchmarking now gets its own future guide, **`README4.md`** (microbenchmarks, load
> testing, frontend perf). It is *not* part of this lab series.

---

## Progress checklist

- [x] **Lab 1** — Foundation + first E2E *(see README2.md)*
- [x] **Lab 2** — E2E: book CRUD / client-side search / auth-gating
- [x] **Lab 3** — Backend: models / auth routes / book routes
- [ ] **Lab 4** — API: HTTP-contract + CSRF enforcement *(next session)*
- [ ] **Later** — Benchmarking → future `README4.md`

**Current status:** `25 passed` — 11 E2E (`-m e2e`) + 14 backend (`-m "not e2e"`).

---

## What landed in Lab 2 (E2E)

Reuses the Lab-1 `live_server` / `base_url` Playwright infra. New shared fixture
`logged_in_page` (in [tests/e2e/conftest.py](tests/e2e/conftest.py)) registers a
uniquely-named user via the UI and returns the logged-in page, so CRUD tests stay independent
against the session-scoped database.

- [tests/e2e/test_book_crud.py](tests/e2e/test_book_crud.py)
  - **add** — Add Book form → new card appears + success flash.
  - **edit** — edit a card's title → updated heading shown, old one gone.
  - **delete** — accept the JS `confirm()` dialog → card removed.
  - **auth-gating** — logged-out visit to `/books/new` redirects to `/auth/login`.
- [tests/e2e/test_search.py](tests/e2e/test_search.py)
  - typing in the search box filters cards (the inline JS in `books.html`); clearing it
    restores them.

## What landed in Lab 3 (backend)

Fast tests on in-memory SQLite via the Flask test client. Two new fixtures in
[tests/conftest.py](tests/conftest.py): a `StaticPool` engine option (so the in-memory DB is
shared between the factories and the client) and `auth_client` (a logged-in test client).

- [tests/backend/test_models.py](tests/backend/test_models.py) — password hashing,
  `author_names()`, many-to-many backref, delete-removes-join-rows (author preserved).
- [tests/backend/test_auth_routes.py](tests/backend/test_auth_routes.py) — register +
  auto-login, duplicate username/email rejection, login/logout, `@login_required` redirect.
- [tests/backend/test_book_routes.py](tests/backend/test_book_routes.py) — create/edit/delete,
  empty-title rejection, existing-author reuse (no duplicate `Author` rows).

---

## Running these labs

```bash
# Lab 3 — fast backend layer (no Docker/browser)
pytest -m "not e2e"
pytest tests/backend -q

# Labs 1 & 2 — E2E (needs Postgres + chromium)
docker compose up -d                  # or: docker start book-appupdated-db-1
docker compose exec db createdb -U bookapp bookapp_test   # one-time (ignore "already exists")
pytest -m e2e
pytest -m e2e --headed                # watch CRUD/search run

# Everything
pytest
```

> Heads-up: the committed `docker-compose.yml` currently fails to parse
> (`volumes must be a mapping`). Until it's fixed, start Postgres with a standalone container
> or an already-running `book-appupdated-db-1`.

---

## Layout after Labs 2 & 3

```
tests/
  conftest.py            # app, client, make_user/make_book, auth_client, StaticPool
  e2e/
    conftest.py          # live_server (Postgres), base_url, logged_in_page
    test_smoke.py        # Lab 1
    test_auth_flow.py    # Lab 1
    test_book_crud.py    # Lab 2  ← new
    test_search.py       # Lab 2  ← new
  backend/               # Lab 3  ← new
    test_models.py
    test_auth_routes.py
    test_book_routes.py
  api/                   # Lab 4 (todo)
```

---

## Next session (Lab 4 — API / HTTP-contract)

Treat the existing routes as a contract: status codes & redirects, protected-route 302s,
**CSRF enforced** (POST without a token → 400), `404` for missing ids, and POST-only delete
(`405` on GET). Lands in `tests/api/` and marker `api`.

*To be continued.*
