# FinTrack 💰

A personal finance management system built with **Flask** and **SQLite**, extending what I learned in **Harvard's CS50: Introduction to Computer Science** into a full-featured, portfolio-ready web application.

**[Try the live demo](#) — no registration required.**

> Screenshots go in `docs/screenshots/` — drop in a few PNGs of the dashboard, expenses list, budgets, and analytics pages and link them here before publishing.

---

## What is this project?

FinTrack is an expense and income tracker: log transactions, set monthly budgets per category, visualize spending with charts, export PDF/Excel reports, import expenses from CSV, and share expenses with other users. It started as my first Flask project after finishing CS50 and has since gone through a full audit-and-refactor pass to bring it up to a standard I'd be comfortable shipping.

## Why was it built?

CS50's `finance` problem set (a stock trading app) was my first real exposure to Flask, SQL, and sessions. I wanted to take those same fundamentals — routing, templating, authentication, a relational schema — and build something outside the classroom, iterating on it the way a real small project evolves: first make it work, then make it right.

## Try it in 30 seconds

1. Open the site.
2. Click **Try Demo** on the homepage or login page.
3. You're dropped straight into a dashboard pre-loaded with ~3 months of realistic expenses, income, budgets, recurring charges, notifications, and a shared expense.
4. Explore freely — the demo workspace is wiped and reseeded every time someone clicks "Try Demo," so nothing you do can break it for the next visitor.

No account, no setup, no empty screens.

## Features

- **Authentication** — registration with password strength meter, login with "remember me," hashed passwords (Werkzeug), CSRF protection on every form
- **Expenses** — add, edit-by-replace, delete, search, filter (category/date range), sort, and paginate
- **Income** — track multiple sources with per-entry currency conversion
- **Budgets** — monthly limits per category with live progress bars and automatic over-budget notifications
- **Recurring expenses** — weekly/monthly/yearly recurring charges tracked separately from one-off spending
- **Shared expenses** — share a specific expense with another user by username; they get a notification
- **CSV import/export** — bulk-load expenses from a spreadsheet, or export everything back out
- **Reports** — generate a formatted PDF (ReportLab) or Excel (openpyxl) report of all expenses
- **Analytics** — line, bar, and doughnut charts (Chart.js) built from a small JSON API, exportable to PDF
- **Multi-currency** — a live exchange-rate API converts amounts to your preferred display currency (degrades gracefully to 1:1 if no API key is configured)
- **Dark mode** — toggle in the top bar, persisted in the browser
- **Demo mode** — the star feature for recruiters: a full, realistic workspace with zero setup

## Technology stack

| Layer | Choice |
|---|---|
| Backend | Python, Flask (application factory + Blueprints) |
| Database | SQLite, accessed through CS50's `SQL` wrapper |
| Templates | Jinja2, Bootstrap 5 |
| Auth | Flask sessions, Werkzeug password hashing, Flask-WTF CSRF |
| Reports | ReportLab (PDF), pandas + openpyxl (Excel/CSV) |
| Charts | Chart.js |
| Deployment | Gunicorn, configured for Render |

## What did I personally learn?

- **A single 1,000-line `app.py` doesn't scale** — splitting routes into Blueprints by feature (expenses, income, budgets, ...) made the codebase dramatically easier to navigate and reason about.
- **Mixing database access patterns is a trap** — the original project used both the CS50 `SQL` wrapper *and* raw `sqlite3` connections in different routes. Standardizing on one made every query consistent and removed an entire class of bugs.
- **A hardcoded secret key is a real vulnerability**, not a theoretical one — it's now read from an environment variable and the app refuses to start in production without it.
- **Decorators remove real duplication** — every protected route used to repeat the same `if 'user_id' not in session` check; a `@login_required` decorator replaced ~25 duplicate blocks.
- **"It runs on my machine" isn't the same as "it runs."** Auditing my own old code turned up a route with broken indentation that made the whole file fail to import, and several database tables that were queried constantly but never actually created by the app. Both are fixed now, and both are exactly the kind of bug automated tests would have caught — which is why I'd add tests next (see below).

## Software engineering concepts demonstrated

- Application factory pattern & Blueprints
- Separation of concerns (routes / data access / config / templates)
- Parameterized SQL queries (SQL-injection safe) throughout
- CSRF protection, password hashing, environment-based secrets
- A `login_required` decorator (DRY, cross-cutting concerns)
- A documented, indexed relational schema (`app/schema.sql`)
- Graceful degradation when an optional third-party API is unavailable
- Idempotent demo-data seeding (safe to run repeatedly)
- Centralized error handling (custom 404/500 pages)

## Project structure

```
FinTrack/
├── run.py                  # Entry point (flask run / gunicorn)
├── config.py                # Environment-based configuration
├── requirements.txt
├── render.yaml               # Render deployment config
├── .env.example
├── app/
│   ├── __init__.py           # Application factory
│   ├── extensions.py         # CSRFProtect, cs50 SQL instance
│   ├── schema.sql            # Full database schema
│   ├── demo.py                # Demo workspace seeding
│   ├── routes/                # One Blueprint per feature area
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── expenses.py
│   │   ├── income.py
│   │   ├── budgets.py
│   │   ├── recurring.py
│   │   ├── categories.py
│   │   ├── notifications.py
│   │   ├── reports.py
│   │   ├── settings.py
│   │   └── profile.py
│   ├── utils/
│   │   ├── decorators.py     # @login_required
│   │   └── currency.py       # Exchange-rate helpers
│   ├── templates/             # Jinja templates (Bootstrap 5)
│   └── static/
│       ├── css/styles.css     # Design system (spacing, colors, components)
│       └── js/main.js
└── instance/                 # SQLite database lives here (gitignored)
```

## Installation

```bash
git clone <this-repo-url>
cd FinTrack
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set SECRET_KEY (see the comment in that file for how to generate one)

python run.py
```

Visit `http://127.0.0.1:5000`. The SQLite database and its tables are created automatically on first run.

## Demo account

The "Try Demo" button on the homepage and login page logs into a fixed `demo` account. Every time it's used, that account's data is wiped and re-seeded with fresh, realistic sample data (expenses, income, budgets, recurring charges, notifications, a shared expense) — so it always looks its best and no visitor can "break" it for the next one. Profile editing is disabled for this account since its credentials aren't meant to be real.

## Deployment (Render)

This repo includes a `render.yaml` for one-click deployment:

1. Push to GitHub and create a new **Blueprint** on [Render](https://render.com) pointing at the repo.
2. Render will read `render.yaml`, generate a `SECRET_KEY` for you, and install `requirements.txt`.
3. Optionally set `EXCHANGE_RATE_API_KEY` in the Render dashboard for live currency conversion.

## Future improvements

- Automated tests (pytest) covering the route layer and the demo-seeding logic
- Real "forgot password" flow (currently a placeholder, as noted on the login page)
- Editing an existing expense/income entry in place, instead of delete-and-recreate
- Recurring expenses that actually generate their next occurrence automatically on a schedule
- Per-category color coding driven by user preference rather than a fixed palette

## License

MIT — see [LICENSE](LICENSE).
