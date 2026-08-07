# DealBrief AI API test cases

| ID | Area | Scenario | Expected result |
|---|---|---|---|
| TC-001 | Authentication | Access customers without a session | `401` |
| TC-002 | Registration | Register a new account | `201`, role is `user` |
| TC-003 | Authorization | User adds a product | `403` |
| TC-004 | Customers | Admin manually adds a customer | `201` |
| TC-005 | Products | Admin manually adds a product | `201` |
| TC-006 | Subscriptions | Admin adds a subscription | `201`, supplied licensed seats persisted |
| TC-007 | Subscriptions | Customer has multiple product rows | All subscriptions returned |
| TC-008 | Intelligence | Refresh with subscription data | `201`, structured snapshot |
| TC-009 | Brief | Generate a call brief | `201`, structured result |
| TC-010 | Brief | Inspect generated response | No `engagementId` or saved status |
| TC-011 | Engagement | Request removed `/engagement-log` | `404` |
| TC-012 | Delete | Delete subscription | `200`, hard delete |
| TC-013 | Delete | Delete customer | `200`, soft delete |
| TC-014 | Validation | Subscription end precedes start | `422` |
| TC-015 | Validation | Generate brief without customer | `422` |
| TC-016 | Removed import API | Request `/imports` | `404` |
| TC-017 | Subscription | Read customer seat history | Dated licensed-seat series returned |
| TC-018 | Intelligence | Refresh with web search | Industry, news, and four action groups |
| TC-019 | Agents | Invoke database function tools with server run context | Authorized data returned; row counts unchanged |

## Automated layers

- Python unit tests validate request normalization, required Agent tool calls,
  and OpenAI structured outputs.
- PostgreSQL integration tests validate authentication, roles, manual data
creation, multi-product subscription rows, Agent database function tools,
intelligence, briefs, and deletes.
- Playwright validates the administrator interface and all three user tabs.
- The paid live OpenAI smoke test is opt-in with `RUN_LIVE_OPENAI=1`.
