# DealBrief AI

DealBrief AI is a React + Flask + PostgreSQL capstone application that turns
customer usage and saved engagement history into AI-generated meeting briefs and
periodic customer intelligence.

## Stack

- React 19 and Vite
- Flask and SQLAlchemy
- PostgreSQL
- OpenAI Responses API with structured outputs
- Postman/Newman, Python `unittest`, and Playwright

## First-time setup

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
npm install
```

Fill in the root `.env`. Keep the OpenAI key server-side and never place it in a
`VITE_` variable.

For a new PostgreSQL database, execute:

1. `database/schema.sql`
2. `database/seed.sql`

For the existing capstone database, execute
`backend/sql/mvp_schema_patch.sql`, then optionally `database/seed.sql`.

## Run

Terminal 1:

```bash
source .venv/bin/activate
python backend/run.py
```

Terminal 2:

```bash
npm run dev
```

- React: `http://localhost:5173`
- Flask: `http://127.0.0.1:3000/api`

## Documentation and submission artifacts

- [API specification](docs/api-specification.md)
- [Database design](docs/database-design.md)
- [API test cases](docs/api-test-cases.md)
- [Actual test results](docs/api-test-results.md)
- [Demo script](docs/demo-script.md)
- [Postman collection](postman/DealBriefAI.postman_collection.json)

## Tests

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v

RUN_DB_INTEGRATION=1 PYTHONPATH=backend \
  python -m unittest discover -s backend/tests -v

npm run build
npm run lint
npx playwright test
```

The live OpenAI smoke test incurs API usage:

```bash
RUN_LIVE_OPENAI=1 PYTHONPATH=backend \
  python -m unittest backend.tests.test_live_openai -v
```
