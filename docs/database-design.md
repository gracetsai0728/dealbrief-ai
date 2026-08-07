# DealBrief AI database design

PostgreSQL is the source of truth. The React application does not keep business
records as mock data.

## Tables

| Table | Purpose | Important relationships |
|---|---|---|
| `users` | Login identities, password hashes, active state, and roles | `user` is assigned at registration; `admin` manages data |
| `customers` | Customer/account master data | Soft-deleted with `deleted_at` |
| `products` | Subscription products that can be selected for briefs | Referenced by customer subscriptions |
| `subscriptions` | One row per annual customer product contract | `customer_id → customers`; `product_id → products`; repeated rows preserve renewal history |
| `intelligence_snapshots` | Periodic AI analysis of subscriptions | Immutable history per customer; latest row drives the UI |

Passwords are never stored directly. Flask stores Werkzeug-generated password
hashes in `users.password_hash`, and the browser receives only an HttpOnly
session cookie after authentication.

## Delete behavior

- Customer Delete is a soft delete: `deleted_at` is set and status becomes
  `inactive`. The customer disappears from normal API reads while historical data
  remains available for audit.
- Subscription Delete is a hard delete of one subscription record.

## Intelligence lifecycle

1. Each annual product contract is stored in `subscriptions` with its start
   date, optional end date, status, and licensed seats.
2. Subscription combines consecutive renewals for the same product into one seat
   line, allowing seat expansion, flat renewals, and contractions to be visible.
3. `POST /api/customers/:id/intelligence/refresh` starts the Intelligence Agent.
   Its read-only function tools load the authorized customer and subscriptions
   active during the requested analysis period.
4. The agent performs separate OpenAI web searches for current industry
   dynamics and company news, then creates Cross-sell, Upsell, Renewal, and
   Winback recommendations.
5. Flask writes a new immutable `intelligence_snapshots` row. Previous snapshots
   remain available as history.

Meeting briefs are generated on demand by a separate agent whose read-only
function tools load the authorized customer, product, latest subscription, and
latest saved intelligence. Briefs are not stored in an engagement log.
Customers, products, and subscriptions are entered manually; the database does
not contain an import queue or CSV audit table.

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
