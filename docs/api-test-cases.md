# API test cases

Test date: 2026-07-24  
Environment: local React `:5173`, Flask `:3000`, PostgreSQL `:5432`

| ID | API / component | Test input or action | Expected API result | Expected database evidence |
|---|---|---|---|---|
| TC-001 | `GET /health` | No input | `200`, status `ok` | `SELECT 1` succeeds |
| TC-002 | `GET /products` | No input | Active product array | No mutation |
| TC-003 | Customer import | One valid Postman customer | `201`, completed, inserted/updated = 1 | Customer and import job exist |
| TC-004 | Customer search | Search `Postman Demo` | Imported customer returned | Same customer row is readable |
| TC-005 | Import audit | Import job UUID | `200`, row counts match | `import_jobs.id` exists |
| TC-006 | Usage import | Valid customer/product/date/metrics | `201`, failedRows = 0 | Usage and import job exist |
| TC-007 | Usage read | Imported customer UUID | One usage row returned | Row values match import |
| TC-008 | Intelligence refresh | Valid period with usage | `201`, structured actions | New intelligence snapshot exists |
| TC-009 | Latest intelligence | Customer UUID | Latest completed snapshot | Same snapshot is returned |
| TC-010 | Intelligence history | Customer UUID | Non-empty array | Snapshot history retained |
| TC-011 | Generate brief | Valid customer/product/QBR/call brief | `201`, draft structured output | Draft engagement exists |
| TC-012 | Engagement detail | Draft engagement UUID | `200`, content/input snapshot included | Draft row is readable |
| TC-013 | Save engagement | Draft engagement UUID | `200`, status saved | Engagement status becomes saved |
| TC-014 | Patch engagement | Status saved | `200`, status saved | Updated status persists |
| TC-015 | Timeline | Customer UUID | Saved brief appears with summary | Saved row selected by timeline query |
| TC-016 | Dashboard | Customer UUID | Customer renewal date, active users, intelligence, timeline | Combined read matches source tables |
| TC-017 | Delete engagement | Saved engagement UUID | `200`, archive mode | Status becomes archived |
| TC-018 | Verify engagement delete | Timeline read | Archived UUID absent | Archived row still retained for audit |
| TC-019 | Delete usage | Usage UUID | `200`, hard mode | Usage row no longer exists |
| TC-020 | Verify usage delete | Customer usage read | Deleted UUID absent | Count is zero for test record |
| TC-021 | Delete customer | Customer UUID | `200`, soft mode | `deleted_at` set; status inactive |
| TC-022 | Verify customer delete | Customer search | Soft-deleted customer absent | Historical related rows remain |
| TC-023 | Validation | Generate brief without customerId | `422`, `VALIDATION_ERROR` | No engagement inserted |
| TC-024 | React integration | Load app and open Admin tab | Seed customer/product visible | UI GET requests receive `200` |

## Automated test layers

- Unit/contract tests validate request normalization and Pydantic output schemas.
- PostgreSQL integration test runs the full API mutation flow with OpenAI mocked,
  but all database operations real.
- Live OpenAI smoke test calls the configured model twice and validates structured
  brief and intelligence responses.
- Newman runs all 24 requests in the exported Postman collection.
- Playwright confirms React loads customer/product data through Flask.
