### Book App with PostgreSQL and Docker

## Project layout

```
Book-app updated/
├── docker-compose.yml          NEW — Postgres service
├── Dockerfile                  NEW — (optional) Flask container
├── requirements.txt            NEW
├── .env.example                NEW — template (safe to commit)
├── .env                        NEW — local secrets (gitignored)
├── .gitignore                  NEW
├── app.py                      REWRITTEN — app factory, blueprints
├── models.py                   NEW — SQLAlchemy Book, Author, User
├── forms.py                    NEW — WTForms for book + auth
├── seed.py                     NEW — fetch from Open Library → DB
├── routes/
│   ├── __init__.py             NEW
│   ├── books.py                NEW — list/create/edit/delete
│   └── auth.py                 NEW — register/login/logout
└── templates/
    ├── base.html               NEW — shared layout (navbar/footer extracted)
    ├── books.html              UPDATED — extends base, adds edit/delete buttons
    ├── authors.html            UPDATED — extends base
    ├── book_form.html          NEW — add/edit book form
    ├── login.html              NEW
    └── register.html           NEW
```

---

## Database schema

Three tables. Authors are a separate table with a many-to-many join so a book can have multiple authors.

```sql
-- users
id            SERIAL PK
username      VARCHAR(64)  UNIQUE NOT NULL
email         VARCHAR(120) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL
created_at    TIMESTAMP    DEFAULT NOW()

-- authors
id    SERIAL PK
name  VARCHAR(200) UNIQUE NOT NULL

-- books
id         SERIAL PK
title      VARCHAR(300) NOT NULL
synopsis   TEXT
cover      VARCHAR(500)      -- image URL
created_by INT REFERENCES users(id) ON DELETE SET NULL
created_at TIMESTAMP DEFAULT NOW()

-- book_authors (join table)
book_id   INT REFERENCES books(id)   ON DELETE CASCADE
author_id INT REFERENCES authors(id) ON DELETE CASCADE
PRIMARY KEY (book_id, author_id)
```

Tables are created automatically by `db.create_all()` on startup — no manual SQL needed. The same shape is also represented as SQLAlchemy models in `models.py`.

---

## Step-by-step implementation

### Step 1 — Create `requirements.txt`

```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
WTForms==3.1.2
psycopg2-binary==2.9.9
python-dotenv==1.0.1
requests==2.32.3
email-validator==2.2.0
```

### Step 2 — Create `.env.example` and `.env`

`.env.example` (commit this):
```
FLASK_SECRET_KEY=change-me
DATABASE_URL=postgresql://bookapp:bookapp@localhost:5432/bookapp
POSTGRES_USER=bookapp
POSTGRES_PASSWORD=bookapp
POSTGRES_DB=bookapp
```
`.env` — copy of `.env.example` with a real `FLASK_SECRET_KEY` (generate with `python -c "import secrets;print(secrets.token_hex(32))"`).

`.gitignore`: add `.env`, `__pycache__/`, `*.pyc`, `.venv/`.

### Step 3 — Create `docker-compose.yml` (Postgres only)

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      retries: 5

volumes:
  pgdata:
```

Start it with `docker compose up -d`. This is all the "manual" infra you need — everything else is code.

### Step 4 — Create `models.py`

- `db = SQLAlchemy()` (shared instance).
- `User(UserMixin)` with `set_password` / `check_password` helpers using `werkzeug.security` (`generate_password_hash`, `check_password_hash`).
- `Author` with `name` unique.
- `Book` with `title`, `synopsis`, `cover`, `created_by` FK; `authors` relationship via the `book_authors` association table.
- Helper method `Book.author_names()` returning a list of names (so templates don't need to iterate nested objects).

### Step 5 — Rewrite `app.py` as an app factory

- Load `.env` via `python-dotenv`.
- `create_app()`:
  - Reads `DATABASE_URL`, `FLASK_SECRET_KEY` from env.
  - Initializes `db`, `LoginManager` (`login_view='auth.login'`), registers blueprints.
  - `with app.app_context(): db.create_all()` so tables are created on first run.
- `@login_manager.user_loader` returns `User.query.get(int(user_id))`.
- `if __name__ == '__main__': create_app().run(debug=True)`.

### Step 6 — Create `forms.py` (Flask-WTF)

- `RegisterForm`: username, email, password, confirm (validators: length, Email, EqualTo, custom uniqueness check).
- `LoginForm`: email, password.
- `BookForm`: title (required), authors (comma-separated string → split on save), synopsis (TextArea), cover (URL, optional).

### Step 7 — Create `routes/auth.py` (blueprint `auth`, prefix `/auth`)

- `GET/POST /register` → validate form, hash password, insert user, `login_user`, redirect to `books.list_books`.
- `GET/POST /login` → verify password, `login_user`, redirect.
- `GET /logout` → `logout_user`, redirect to login.

### Step 8 — Create `routes/books.py` (blueprint `books`, prefix `/`)

- `GET /` → list all books (replaces current `show_books`). Pass `book.author_names()` list.
- `GET /authors` → distinct author names (replaces current `show_authors`, now a simple `Author.query.order_by(Author.name).all()`).
- `GET/POST /books/new` → `@login_required`, renders `book_form.html`, on submit creates `Book` + upserts `Author` rows + join rows, sets `created_by=current_user.id`.
- `GET/POST /books/<int:id>/edit` → `@login_required`, same form prefilled.
- `POST /books/<int:id>/delete` → `@login_required`, CSRF-protected delete.

Authors parsing helper: split the CSV field on commas, strip whitespace, for each name do `Author.query.filter_by(name=n).first() or Author(name=n)`.

### Step 9 — Update templates

- **`base.html`** (new): extract the navbar + footer. Navbar adds "Add Book", "Login/Register" or "Logout ({{ current_user.username }})" using `current_user.is_authenticated`. Renders `get_flashed_messages()` as Bootstrap alerts.
- **`books.html`**: `{% extends "base.html" %}`, removes inline navbar/footer, adds Edit/Delete buttons inside each card wrapped in `{% if current_user.is_authenticated %}`. Delete is a `<form method="POST">` with the CSRF token so it can't be triggered by GET.
- **`authors.html`**: extends base, strips duplicated chrome.
- **`book_form.html`** (new): Bootstrap form rendering `form.hidden_tag()` (CSRF) + each field. Reused for create and edit.
- **`login.html` / `register.html`** (new): standard Bootstrap forms.

### Step 10 — Create `seed.py` (Open Library importer)

Standalone script invoked via `python seed.py`. Uses `requests` to hit Open Library's search API and populates the DB.

- Endpoint: `https://openlibrary.org/search.json?q=<subject>&limit=20` for several subjects (e.g. `fantasy`, `science`, `history`, `mystery`) to get ~80 books.
- For each doc:
  - `title` ← `doc["title"]`
  - `authors` ← `doc.get("author_name", [])`
  - `cover` ← `https://covers.openlibrary.org/b/id/{doc["cover_i"]}-L.jpg` if present, else `None`
  - `synopsis` ← first sentence from `doc.get("first_sentence", [""])[0]` or empty (Open Library search doesn't return full synopses; this is the documented trade-off).
- Wrap in `create_app().app_context()`. Skip inserts when a book with the same title already exists (idempotent — safe to re-run).
- Prints a progress line per book and a final count.

### Step 11 — Run & verify

Commands the user runs (in order):

```bash
# 1. Start Postgres
docker compose up -d
docker compose ps                                    # db should be "healthy"

# 2. Python deps (create a venv first if desired)
python -m venv .venv
.venv\Scripts\activate                               # Windows
pip install -r requirements.txt

# 3. First-run: creates tables + seeds books
python seed.py

# 4. Start the app
python app.py                                        # http://127.0.0.1:5000
```

Manual verification checklist:
- [ ] `/` shows ~80 seeded books with covers and authors.
- [ ] `/authors` lists distinct authors alphabetically.
- [ ] Clicking "Add Book" while logged out redirects to `/auth/login`.
- [ ] `/auth/register` creates a user; after submit you're logged in.
- [ ] Logged-in: Add Book form creates a new book and it appears on `/`.
- [ ] Edit form pre-fills; save updates the card.
- [ ] Delete removes the book (and no orphan rows in `book_authors`; verify with `docker compose exec db psql -U bookapp -d bookapp -c "select count(*) from book_authors;"`).
- [ ] Logout returns you to the login page; Add/Edit/Delete buttons disappear.
- [ ] Restart `docker compose down && docker compose up -d` — data persists via the `pgdata` volume.

---

# Happy Coding 