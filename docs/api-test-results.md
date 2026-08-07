# DealBrief AI test results

## Result summary

Validation completed after the Subscription and expanded Intelligence changes.

| Layer | Result |
|---|---|
| Python and PostgreSQL integration | 24 passed, 1 paid live test skipped |
| Frontend lint | Passed |
| Vite production build | Passed |
| Playwright end-to-end | 1 passed |
| OpenAPI YAML parse | Passed |
| Postman collection JSON parse | Passed |

## Database verification

The current database contains five active customers:

| Customer | Annual contracts | Distinct products | Current licensed seats |
|---|---:|---:|---:|
| ABC Bank | 8 | 2 | 800 |
| BrightPath Education | 7 | 2 | 925 |
| GreenHealth Group | 5 | 1 | 200 |
| Northstar Retail | 12 | 3 | 2,157 |
| Summit Manufacturing | 8 | 2 | 550 |

The database contains forty annual subscription records across deliberately
varied one-to-three-product portfolios. CRM histories span five contract years,
Collaboration spans four, and Analytics spans three.

`to_regclass('engagements')` returned `NULL`, confirming that the Engagement Log
table was removed.

`to_regclass('import_jobs')` returned `NULL`. The legacy
`source_import_job_id` and `import_job_id` columns are also absent.

The database contains exactly five customers and no soft-deleted customer rows.
The subscription table is named `subscriptions`; `usage_snapshots` no longer
exists. Customer `opportunity_stage` and `renewal_date`, plus subscription
`active_users`, are absent.

## Behaviors verified

- Anonymous API access is rejected.
- Registration assigns the `user` role.
- Only administrators can manage data.
- Subscription start, end, status, and licensed seats are persisted.
- Subscription returns dated licensed-seat series for each product subscription.
- Customer intelligence uses web search with structured output.
- Agent function tools read authorized customer, product, subscription, and
  intelligence data without changing database row counts.
- Industry dynamics and sourced company news are stored separately.
- Recommendations are grouped into Cross-sell, Upsell, Renewal, and Winback.
- Brief generation returns structured content without storing an engagement.
- `/api/engagement-log` returns `404`.
- `/api/imports` returns `404`; data is managed through individual admin APIs.
- `/api/usage` returns `404`; subscription APIs use `/api/subscriptions`.
