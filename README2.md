# Book App — Testing Guide (README 2.0)

This document tracks the **testing** effort for the Book App. The original
[`ReadMe.md`](ReadMe.md) (app setup) is unchanged. We build the test suite
**incrementally, one lab session at a time** — small first, then up the pyramid.

> Benchmarking is **not** covered here. It gets its own guide (`README3.md`) in a
> later lab once the functional suite is in place. See *Roadmap* at the bottom.

---

## Testing philosophy — the pyramid

```
        ▲  fewer, slower, most realistic
        │   E2E (Playwright)      ← real browser, real Postgres
        │   API / HTTP-contract   ← test client, status/redirect/CSRF
        │   Backend (unit)        ← models, routes, validation (SQLite)
        ▼  many, fast, isolated
```

- **One runner:** everything is `pytest`. E2E uses `pytest-playwright` (Python).
- **Two databases:** in-memory **SQLite** for the fast layers (no Docker), real
  **Postgres** (`bookapp_test`) for E2E so behavior matches production.
- **Markers** keep layers separable: `e2e`, `api`. Fast layers = `pytest -m "not e2e"`.

---

## Progress checklist

- [x] **Lab 1** — Foundation + first E2E
      (`create_app(test_config)`, dev deps, `pytest.ini`, conftest fixtures, smoke + auth-flow)
- [ ] **Lab 2** — E2E: book CRUD / client-side search / auth-gating
- [ ] **Lab 3** — Backend: models / auth routes / book routes
- [ ] **Lab 4** — API: HTTP-contract + CSRF enforcement
- [ ] **Later** — Benchmarking → moves to its own `README3.md` (not in this series)

---

## One-time setup

```bash
# Python deps for testing
pip install -r requirements-dev.txt

# Browser binaries for Playwright
playwright install

# Postgres for E2E + a throwaway test database
docker compose up -d
docker compose exec db createdb -U bookapp bookapp_test
```

`.env.test` (gitignored) holds the E2E DB URL; the E2E conftest falls back to
`postgresql://bookapp:bookapp@localhost:5432/bookapp_test` if it's missing.

---

## Running tests

```bash
# Fast layers only — no Docker needed (Labs 3 & 4, once written)
pytest -m "not e2e"

# E2E only — needs Postgres + browsers (Labs 1 & 2)
pytest -m e2e
pytest -m e2e --headed       # watch the browser
pytest -m e2e --headed --slowmo 500   # ...slowly

# Everything
pytest
```

---

## Layout

```
tests/
  conftest.py            # shared fixtures: SQLite app, client, make_user/make_book
  e2e/
    conftest.py          # live_server on Postgres, base_url for Playwright
    test_smoke.py        # Lab 1 — home loads, seeded books render
    test_auth_flow.py    # Lab 1 — register / logout / bad-login
    test_book_crud.py    # Lab 2 (todo)
    test_search.py       # Lab 2 (todo)
  backend/               # Lab 3 (todo)
  api/                   # Lab 4 (todo)
```

---

## What landed in Lab 1

- `app.py` — `create_app(test_config=None)` so tests can inject config (production
  path via env vars is unchanged).
- `requirements-dev.txt`, `pytest.ini`, `.env.test`.
- `tests/conftest.py` — SQLite app + `client` + `make_user` / `make_book` factories
  (no network / Open Library dependency).
- `tests/e2e/conftest.py` — threaded `live_server` on Postgres with CSRF enabled,
  deterministic seed data, and a `base_url` fixture for Playwright.
- `tests/e2e/test_smoke.py`, `tests/e2e/test_auth_flow.py`.

**Verify:** `pytest -m e2e` is green.

---

## Roadmap (future labs)

| Lab | Focus | DB | Status |
|-----|-------|----|--------|
| 1 | Foundation + first E2E | Postgres | ✅ done |
| 2 | E2E: CRUD, search, auth-gating | Postgres | ⬜ |
| 3 | Backend: models, routes, validation | SQLite | ⬜ |
| 4 | API: HTTP-contract, CSRF | SQLite | ⬜ |
| — | Benchmarking (`README3.md`) | both | ⬜ later |

*To be continued.*
