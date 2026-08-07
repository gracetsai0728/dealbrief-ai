# DealBrief AI API specification

Base URL: `http://127.0.0.1:3000/api`

Successful responses use `{ "data": ... }`. Errors use
`{ "error": { "code": "...", "message": "...", "details": null } }`.

## Authentication

Flask uses an HttpOnly session cookie. `GET /health`, `POST /auth/login`, and
`POST /auth/register` are public. All other endpoints require authentication.
Registration always assigns the `user` role. Data mutation endpoints require
the `admin` role.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create and sign in a user account |
| POST | `/auth/login` | Start a session |
| POST | `/auth/logout` | End the session |
| GET | `/auth/me` | Return the signed-in user |

## Customers and products

| Method | Path | Purpose |
|---|---|---|
| GET | `/customers` | List active, non-deleted customers |
| POST | `/customers` | Add a customer (admin) |
| DELETE | `/customers/{customerId}` | Soft-delete a customer (admin) |
| GET | `/products` | List active subscription products |
| POST | `/products` | Add a product (admin) |

## Subscriptions

Each row in `subscriptions` represents one annual customer contract for one
product. Repeated product rows preserve renewals and licensed-seat changes.

| Method | Path | Purpose |
|---|---|---|
| GET | `/subscriptions?customerId={uuid}` | List subscriptions |
| POST | `/subscriptions` | Add a subscription (admin) |
| DELETE | `/subscriptions/{subscriptionId}` | Delete a subscription (admin) |
| GET | `/customers/{customerId}/timeline` | Licensed seats across subscription periods |

Example create request:

```json
{
  "customerId": "CUSTOMER_UUID",
  "productId": "PRODUCT_UUID",
  "subscriptionStartDate": "2026-01-01",
  "subscriptionEndDate": "2026-12-31",
  "subscriptionStatus": "active",
  "licensedSeats": 100
}
```

Subscription status must be `active`, `expired`, or `canceled`. The Subscription page
uses `licensedSeats` from the subscription start date through its end date or
today and combines annual renewals into one line per product.

## Intelligence

| Method | Path | Purpose |
|---|---|---|
| GET | `/customers/{customerId}/dashboard` | Customer, subscriptions, and latest intelligence |
| GET | `/customers/{customerId}/intelligence` | Intelligence history |
| GET | `/customers/{customerId}/intelligence/latest` | Latest intelligence |
| POST | `/customers/{customerId}/intelligence/refresh` | Analyze subscriptions and save a snapshot |

The Intelligence response separates `industryDynamics`, sourced `companyNews`,
and `recommendedNextSteps` grouped into `crossSell`, `upsell`, `renewal`, and
`winback`.

## Meeting briefs

`POST /generate-brief` generates a schema-validated Call Brief, Email Draft, or
Meeting Agenda. The result is returned directly and is not stored.

```json
{
  "customerId": "CUSTOMER_UUID",
  "productId": "PRODUCT_UUID",
  "meetingType": "winback",
  "deliverableType": "call_brief",
  "notes": "Focus on subscription value."
}
```

There is no Engagement Log API.
There is no bulk import API; administrators enter customers, products, and
subscriptions through the individual create endpoints.
