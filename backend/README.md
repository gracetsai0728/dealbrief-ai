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

For a new database, run `database/schema.sql` followed by `database/seed.sql`.
For the existing database, run `backend/sql/mvp_schema_patch.sql`.

Run the API:

```bash
python backend/run.py
```

The API listens on `http://localhost:3000/api`.

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
  "notes": "Focus on renewal risk and reporting adoption."
}
```

Generating a brief creates a draft engagement. Save it to the customer timeline with:

```json
POST /api/engagement-log
{
  "engagementId": "ENGAGEMENT_UUID"
}
```
