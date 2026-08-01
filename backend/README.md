# DealBrief AI Flask API

Database-backed API for imports, customer intelligence, structured OpenAI
meeting briefs, engagement timelines, and admin delete operations.

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
GET   /api/customers
GET   /api/products
GET   /api/usage
GET   /api/customers/:customerId/dashboard
DELETE /api/customers/:customerId
DELETE /api/usage/:usageId
GET   /api/imports
GET   /api/imports/:importJobId
POST  /api/imports/customers
POST  /api/imports/usage
GET   /api/customers/:customerId/intelligence
GET   /api/customers/:customerId/intelligence/latest
POST  /api/customers/:customerId/intelligence/refresh
POST  /api/generate-brief
GET   /api/engagement-log
GET   /api/engagement-log/:engagementId
POST  /api/engagement-log
PATCH /api/engagement-log/:engagementId
DELETE /api/engagement-log/:engagementId
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
  "meetingType": "qbr",
  "deliverableType": "call_brief",
  "notes": "Focus on renewal planning and reporting adoption."
}
```

Generating a brief creates a draft engagement. Save it to the customer timeline with:

```json
POST /api/engagement-log
{
  "engagementId": "ENGAGEMENT_UUID"
}
```
