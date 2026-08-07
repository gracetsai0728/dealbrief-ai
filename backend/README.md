# DealBrief AI Flask API

Database-backed API for customer product subscriptions, customer intelligence,
structured meeting briefs produced by two OpenAI Agents SDK agents, and
administrator data operations.

## Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
```

The root `.env.example` is the single environment template for both React and Flask.
Update the root `.env` with the PostgreSQL password and an OpenAI project API
key. Never put the OpenAI key in a `VITE_` variable or frontend code.

For a new or existing database, run `database/schema.sql`, then optionally run
`database/seed.sql` for demo data. The schema file is idempotent and includes
compatibility upgrades for earlier versions of the project database.

Run the API:

```bash
python backend/run.py
```

The API listens on `http://localhost:3000/api`.

## Swagger UI

After starting Flask, open the interactive API documentation:

```text
http://127.0.0.1:3000/api/docs
```

The OpenAPI 3.0 source is available at:

```text
http://127.0.0.1:3000/api/openapi.yaml
```

In Swagger UI, expand an endpoint, select **Try it out**, replace example UUIDs
with IDs returned by `GET /customers` and `GET /products`, then select
**Execute**. The UI shows the request URL, generated cURL command, response
status, and response body.

The Swagger UI page loads official Swagger UI assets from unpkg, so the
documentation page requires an internet connection. The API and OpenAPI YAML
remain available locally.

## Endpoints

```text
GET   /api/health
POST  /api/auth/register
POST  /api/auth/login
POST  /api/auth/logout
GET   /api/auth/me
GET   /api/customers
POST  /api/customers
GET   /api/products
POST  /api/products
GET   /api/subscriptions
POST  /api/subscriptions
GET   /api/customers/:customerId/dashboard
GET   /api/customers/:customerId/timeline
DELETE /api/customers/:customerId
DELETE /api/subscriptions/:subscriptionId
GET   /api/customers/:customerId/intelligence
GET   /api/customers/:customerId/intelligence/latest
POST  /api/customers/:customerId/intelligence/refresh
POST  /api/generate-brief
```

Run the contract tests from the project root:

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

Example brief request:

```json
{
  "customerId": "CUSTOMER_UUID",
  "productId": "PRODUCT_UUID",
  "meetingType": "winback",
  "deliverableType": "call_brief",
  "notes": "Focus on renewal planning and reporting adoption."
}
```

Generated briefs are returned directly and are not saved to an engagement log.

## Agents

Agent definitions are under `backend/app/agents/`:

```text
context.py              Server-owned run context and typed tool results
database_tools.py       Read-only customer, product, and subscription tools
intelligence_agent.py   Database- and web-search-enabled intelligence specialist
meeting_brief_agent.py  Database-grounded meeting deliverable specialist
runtime.py              Required-tool-call validation
```

Both agents use Pydantic structured outputs and the configured OpenAI model.
The Intelligence Agent must load the customer and overlapping subscriptions,
then perform current industry and company-news research. The Meeting Brief
Agent must load the customer, selected product, latest matching subscription,
and latest saved intelligence. Database function tools obtain authorized IDs
from local run context, execute serially, and cannot write data.

The service layer calls each agent through `Runner.run_sync()`, verifies that
all required database tools ran, validates the structured result, and performs
the only database write: saving a completed intelligence snapshot. Tracing
uses the `dealbrief-intelligence` and `dealbrief-meeting-brief` workflow names
with sensitive trace payloads disabled.
