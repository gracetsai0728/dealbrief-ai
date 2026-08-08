# DealBrief AI

DealBrief AI is a React + Flask + PostgreSQL capstone application that turns
customer product subscriptions into AI-generated meeting briefs and periodic
customer intelligence.

## Features

- Configure customer, meeting type, product, deliverable, and notes
- Generate structured AI meeting briefs with talking points and suggested questions
- View one-to-three-product licensed-seat lines from subscription start through today
- Refresh sourced industry dynamics, company news, and commercial next steps
- Register and sign in with role-based access
- Let administrators manage customer, product, and subscription records
- Use the responsive interface on desktop and smaller screens

## Stack

- React 19 and Vite
- Flask and SQLAlchemy
- PostgreSQL
- OpenAI Agents SDK on the Responses API, with structured outputs and web search
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

The main environment variables are:

```dotenv
VITE_API_URL=http://localhost:3000/api
DATABASE_URL=postgresql+psycopg://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/dealbriefai
FLASK_DEBUG=true
CORS_ORIGINS=http://localhost:5173
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_BRIEF_MODEL=gpt-5.6-terra
OPENAI_INTELLIGENCE_MODEL=gpt-5.6-terra
SECRET_KEY=replace-with-a-long-random-secret
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
```

For a separately hosted HTTPS frontend, set `SESSION_COOKIE_SECURE=true` and
`SESSION_COOKIE_SAMESITE=None` on the backend so authenticated cross-site API
requests can include the session cookie. Keep the local defaults shown above
for HTTP development.

For a new or existing PostgreSQL database, run `database/schema.sql`, followed
by the optional `database/seed.sql` demo data. For example:

```bash
psql -d dealbriefai -f database/schema.sql
psql -d dealbriefai -f database/seed.sql
```

`database/schema.sql` is idempotent and includes compatibility upgrades for
databases created with an earlier version of the project.

The demo seed contains five customers and forty annual subscription records.
Customer portfolios intentionally vary between one and three products, producing
realistic staggered three-to-five-year licensed-seat histories in Subscription.

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

After loading the optional seed data, use one of these demo accounts:

- User: `user@dealbrief.ai` / `User123!`
- Administrator: `admin@dealbrief.ai` / `Admin123!`

New registrations always receive the `user` role. Only administrators can open
the Admin page or add and delete managed data.

The frontend calls the Flask API through `src/api.js`. To preview a production
build locally, run:

```bash
npm run build
npm run preview
```

## Project structure

```text
src/            React application and API client
backend/        Flask API, Agents SDK agents, services, models, and backend tests
database/       PostgreSQL schema and optional demo data
docs/           API, database, and test documentation
postman/        Postman collection and local environment
tests/          Playwright end-to-end tests
```

## AI agents

The backend defines two specialized OpenAI Agents SDK agents:

- `DealBrief Intelligence Agent` calls read-only function tools to load the
  authorized customer and subscriptions, performs separate hosted web searches
  for current industry dynamics and company news, and returns a
  schema-validated intelligence snapshot.
- `DealBrief Meeting Brief Agent` calls read-only function tools to load the
  authorized customer, product, latest matching subscription, and latest saved
  intelligence before generating the requested deliverable. It does not use
  web search.

Customer and product IDs are supplied through server-owned run context rather
than model-generated tool arguments. The Flask service layer remains
responsible for authorization, validation, persistence, and API error
responses; neither agent has a database-write tool. Agent traces use distinct
workflow names and exclude model inputs and outputs that may contain sensitive
customer data.

## Documentation and submission artifacts

- [API specification](docs/api-specification.md)
- [OpenAPI definition](backend/app/openapi.yaml)
- [Database design](docs/database-design.md)
- [API test cases](docs/api-test-cases.md)
- [Actual test results](docs/api-test-results.md)
- [Backend guide](backend/README.md)
- [Frontend guide](README_FRONTEND.md)
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

## Planned enhancements

- Real-time Salesforce integration
- Brief export and collaboration features
- Advanced customer analytics
