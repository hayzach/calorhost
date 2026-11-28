# calorhost

A self-hosted calorie/macro tracker web app

## Tech stack

| Concern                 | Choice                                                            |
| ----------------------- | ----------------------------------------------------------------- |
| Language and runtime    | Python; FastAPI                                                   |
| UI                      | Server-rendered HTML with Jinja2, HTMX, Web components, Alpine.js |
| Database                | SQLite                                                            |
| Database access         | SQLAlchemy, with Alembic migrations                               |
| External food data      | Open Food Facts behind an application service/client              |
| Packaging/configuration | `pyproject.toml`/`uv`; environment-driven configuration           |
| Testing                 | `pytest`                                                          |

## Documentation

- For planned feature behavior, consult `docs/requirements.md`.
- For planned data model, consult `docs/database_erd.md`.
- For architecture diagram, consult `docs/architecture.md`.

## Development

- Python 3.14+; use `uv sync` to install dependencies.
- Apply database migrations with `uv run calorhost-db`, then run the app with `uv run calorhost` (`src/calorhost/main.py`, binds to `127.0.0.1:8000`).
- The default database is `/var/lib/calorhost/calorhost.db`; set `DATABASE_URL` to override it (for example, `sqlite:////tmp/calorhost.db` during local development).
- Quality checks: `uv run ruff check src`, `uv run ruff format src`, `uv run mypy src` and `uv run pytest`.
