# API test results

Executed on 2026-07-24 in MDT. These are actual command results, not proposed
results.

## Final result summary

| Suite | Command | Result |
|---|---|---|
| Python unit + PostgreSQL integration | `RUN_DB_INTEGRATION=1 PYTHONPATH=backend python -m unittest discover -s backend/tests -v` | PASS — 10 discovered, 9 passed, 1 paid live test skipped, 0 failures, 0.251 s |
| Live OpenAI integration | `RUN_LIVE_OPENAI=1 PYTHONPATH=backend python -m unittest backend.tests.test_live_openai -v` | PASS — 1 test, 0 failures, 18.178 s |
| Postman/Newman | `newman run postman/DealBriefAI.postman_collection.json -e postman/DealBriefAI.local.postman_environment.json` | PASS — 24 requests, 26 assertions, 0 failures, 16.5 s |
| React production build | `npm run build` | PASS — Vite built 19 modules |
| JavaScript lint | `npm run lint` | PASS — 0 warnings, 0 errors |
| Browser integration | `npx playwright test --reporter=list` | PASS — 1 test, 0 failures, 1.5 s |
| Postman JSON validation | `jq empty postman/*.json` | PASS |
| Dependency audit after test-only cleanup | `npm audit --offline` | PASS — 0 vulnerabilities |

The Postman run included two real OpenAI calls. Intelligence took approximately
6.3 seconds and call-brief generation approximately 9.6 seconds. The average
response time across all 24 requests was 677 ms.

## Customer Intelligence card update verification

Executed on 2026-07-31 after replacing Renewal Risk and Expansion Signal with
Renewal Date and Active Users:

| Check | Result |
|---|---|
| Python unit + PostgreSQL integration | PASS — 10 discovered, 9 passed, 1 paid live test skipped, 0 failures |
| JavaScript lint | PASS — 0 warnings, 0 errors |
| React production build | PASS — Vite built 19 modules |
| Browser integration | PASS — 1 Playwright test, 0 failures |
| PostgreSQL schema | PASS — obsolete `renewal_risk` and `expansion_signal` columns are absent |
| Dashboard source data | PASS — ABC Bank renewal date `2026-10-15`; latest active users `410` |

The paid live OpenAI smoke test was not rerun for this UI/schema update. Its
Pydantic structured-output contract and mocked API integration tests passed.

## Database evidence after the Postman workflow

The final read-only verification query returned:

```text
salesforce_account_id: POSTMAN-DEMO-001
status: inactive
soft_deleted: true
intelligence_rows: 1
archived_engagements: 1
usage_rows: 0
```

Import audit rows:

```text
customers | completed | total 1 | inserted 1 | updated 0 | failed 0
usage     | completed | total 1 | inserted 1 | updated 0 | failed 0
```

This proves the Delete semantics: customer was soft-deleted, engagement was
archived, usage was hard-deleted, and audit/intelligence history remained.

## Issues encountered and resolved

1. The initial seed used `sales` and `customer_success`, while the existing
   PostgreSQL constraint accepts `admin`, `sales_rep`, and `manager`. PostgreSQL
   rejected the seed with `users_role_check`. The full schema and seed were
   aligned to the existing role contract, then the seed completed successfully.
2. Sandbox access initially blocked localhost PostgreSQL. The database checks
   were rerun with explicit local-network permission; the connection and
   migration succeeded.
3. The strengthened Playwright test initially used a selector matching all three
   `<tbody>` elements. It failed twice under strict mode. The selector was scoped
   to each `section.table-panel`; the final browser test passed.
4. Newman was installed only to execute the collection and brought deprecated
   transitive packages. It was removed after the run; the final dependency audit
   reports zero vulnerabilities.

## Reproduction

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt

RUN_DB_INTEGRATION=1 PYTHONPATH=backend \
  python -m unittest discover -s backend/tests -v

RUN_LIVE_OPENAI=1 PYTHONPATH=backend \
  python -m unittest backend.tests.test_live_openai -v

npm install
npm run build
npm run lint
npx playwright install chromium
npx playwright test
```

The live test uses OpenAI API credits. Leave `RUN_LIVE_OPENAI` unset for normal
local test runs.
