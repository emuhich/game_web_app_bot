# Tests

## Running tests

Install dev dependencies and run tests:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio
pytest -q
```

## What is covered

- Unit tests for services (users, honesty) with DAO mocking
- Integration tests for DAO using in-memory SQLite DB (async)
- Basic router smoke test

## Notes

- The test DB uses SQLite in-memory and creates schema from SQLAlchemy models at startup.
- If your app requires Postgres-only features, adapt tests to use a test Postgres instance.

