# DealBrief AI database design

PostgreSQL is the source of truth. The React application does not keep business
records as mock data.

## Tables

| Table | Purpose | Important relationships |
|---|---|---|
| `users` | Admin, sales representative, and manager identities | Owns customers, uploads, and generated engagements |
| `customers` | Customer/account master data | `account_owner_id → users`; soft-deleted with `deleted_at` |
| `products` | Products that can be selected for briefs and usage | Referenced by usage and engagements |
| `usage_snapshots` | Time-series product adoption facts | `customer_id → customers`; `product_id → products`; optional import job |
| `engagements` | Every AI-generated meeting brief and its source snapshot | Draft when generated, saved when added to timeline, archived on Delete |
| `import_jobs` | Audit record for each customer or usage import | Stores row counts and row-level errors |
| `intelligence_snapshots` | Periodic AI analysis of usage and saved engagements | Immutable history per customer; latest row drives the UI |

## Delete behavior

- Customer Delete is a soft delete: `deleted_at` is set and status becomes
  `inactive`. The customer disappears from normal API reads while historical data
  remains available for audit.
- Usage Delete is a hard delete of one time-series snapshot.
- Engagement Delete is an archive operation: status becomes `archived`, so the
  record no longer appears in the normal engagement timeline.

## Intelligence lifecycle

1. Usage is loaded into `usage_snapshots`.
2. Generated briefs are initially stored as draft `engagements`.
3. Saving a brief changes it to `saved`, making its summary available to the
   Customer Engagement Timeline.
4. `POST /api/customers/:id/intelligence/refresh` gathers usage and saved
   engagements for an analysis period.
5. OpenAI returns schema-validated customer signals, metrics, and next actions.
6. Flask writes a new immutable `intelligence_snapshots` row. Previous snapshots
   remain available as history.

## SQL files

- `database/schema.sql`: the single source of database structure. It creates a
  new database schema and applies compatibility upgrades when rerun against an
  earlier project database.
- `database/seed.sql`: deterministic demo data; safe to run repeatedly.

Run from pgAdmin in this order for a new or existing database:

```sql
-- Open and execute database/schema.sql
-- Optionally execute database/seed.sql for demo data
```
