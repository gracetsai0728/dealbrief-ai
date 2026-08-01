# DealBrief AI API specification

Base URL: `http://127.0.0.1:3000/api`

Successful responses use `{ "data": ... }`. Errors use:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "customerId is required.",
    "details": null
  }
}
```

## Health and reference data

### `GET /health`

Input: none.

```json
{ "data": { "status": "ok" } }
```

### `GET /customers?status=active&search=Bank`

Input: optional query parameters `status` and `search`.

```json
{
  "data": [
    {
      "id": "30000000-0000-0000-0000-000000000001",
      "name": "ABC Bank",
      "industry": "Financial Services",
      "accountOwner": {
        "id": "10000000-0000-0000-0000-000000000001",
        "name": "Grace Lin"
      },
      "salesforceAccountId": "SF-ACCT-1042",
      "opportunityStage": "Renewal Review",
      "renewalDate": "2026-10-15",
      "status": "active"
    }
  ]
}
```

### `GET /products`

Input: none.

```json
{
  "data": [
    {
      "id": "20000000-0000-0000-0000-000000000001",
      "name": "CRM Platform",
      "description": "Pipeline, account, and sales workflow management.",
      "status": "active"
    }
  ]
}
```

### `GET /usage?customerId={uuid}`

Input: optional `customerId` query parameter.

```json
{
  "data": [
    {
      "id": "40000000-0000-0000-0000-000000000001",
      "customerId": "30000000-0000-0000-0000-000000000001",
      "customerName": "ABC Bank",
      "productId": "20000000-0000-0000-0000-000000000001",
      "productName": "CRM Platform",
      "snapshotDate": "2026-07-04",
      "activeUsers": 410,
      "licensedSeats": 500,
      "licenseUtilization": 82,
      "usageGrowth": 35,
      "featureAdoption": { "Reporting": 58, "Automation": 42 }
    }
  ]
}
```

### `GET /customers/{customerId}/dashboard`

Input: customer UUID in the path.

```json
{
  "data": {
    "customer": {
      "id": "CUSTOMER_UUID",
      "name": "ABC Bank",
      "renewalDate": "2026-10-15",
      "status": "active"
    },
    "latestUsage": [
      {
        "id": "USAGE_UUID",
        "productName": "CRM Platform",
        "activeUsers": 410,
        "licenseUtilization": 82
      }
    ],
    "intelligence": {
      "id": "INTELLIGENCE_UUID",
      "nextBestActions": [
        {
          "action": "Prepare renewal value story",
          "priority": "high",
          "reason": "Reporting adoption is uneven.",
          "dueDate": null
        }
      ]
    },
    "engagementTimeline": [
      {
        "id": "ENGAGEMENT_UUID",
        "title": "ABC Bank QBR Call Brief",
        "meetingSummary": "QBR preparation focused on proving renewal value."
      }
    ]
  }
}
```

## Imports

### `POST /imports/customers`

Creates an `import_jobs` row and inserts or updates customers by
`salesforceAccountId`.

```json
{
  "filename": "customers.csv",
  "uploadedBy": "10000000-0000-0000-0000-000000000001",
  "rows": [
    {
      "name": "Demo Customer",
      "industry": "Software",
      "accountOwner": "Grace Lin",
      "salesforceAccountId": "SF-DEMO-001",
      "opportunityStage": "Discovery",
      "renewalDate": "2027-01-15",
      "status": "active"
    }
  ]
}
```

```json
{
  "data": {
    "id": "IMPORT_JOB_UUID",
    "importType": "customers",
    "filename": "customers.csv",
    "status": "completed",
    "totalRows": 1,
    "insertedRows": 1,
    "updatedRows": 0,
    "failedRows": 0,
    "errorDetails": [],
    "completedAt": "2026-07-23T18:30:00+00:00"
  }
}
```

### `POST /imports/usage`

Upserts by customer, product, and snapshot date.

```json
{
  "filename": "usage.csv",
  "rows": [
    {
      "customerId": "CUSTOMER_UUID",
      "productId": "PRODUCT_UUID",
      "snapshotDate": "2026-07-20",
      "activeUsers": 80,
      "licensedSeats": 100,
      "licenseUtilization": 80,
      "usageGrowth": 12.5,
      "featureAdoption": { "Reporting": 55 }
    }
  ]
}
```

```json
{
  "data": {
    "id": "IMPORT_JOB_UUID",
    "importType": "usage",
    "status": "completed",
    "totalRows": 1,
    "insertedRows": 1,
    "updatedRows": 0,
    "failedRows": 0,
    "errorDetails": []
  }
}
```

### `GET /imports?type=customers`

Input: optional `type=customers|usage`.

```json
{
  "data": [
    {
      "id": "IMPORT_JOB_UUID",
      "importType": "customers",
      "filename": "customers.csv",
      "status": "completed",
      "totalRows": 1,
      "insertedRows": 1,
      "updatedRows": 0,
      "failedRows": 0,
      "errorDetails": []
    }
  ]
}
```

### `GET /imports/{importJobId}`

Input: import job UUID in the path. Output is one import object with the same
shape as above.

## Intelligence

### `POST /customers/{customerId}/intelligence/refresh`

Both dates are optional. Defaults to the latest 90 days.

```json
{
  "periodStart": "2026-05-01",
  "periodEnd": "2026-07-31"
}
```

```json
{
  "data": {
    "id": "INTELLIGENCE_UUID",
    "snapshotDate": "2026-07-23",
    "aiKeySignal": "Usage is growing while reporting adoption remains uneven.",
    "nextBestActions": [
      {
        "action": "Validate reporting goals",
        "priority": "high",
        "reason": "Reporting trails overall utilization.",
        "dueDate": null
      }
    ],
    "metrics": {
      "accountHealthScore": 76,
      "adoptionScore": 72,
      "engagementScore": 60,
      "usageGrowth": 12.5,
      "licenseUtilization": 80,
      "riskReasons": ["No recent executive engagement"]
    },
    "generationStatus": "completed",
    "model": "gpt-5.6-terra",
    "generatedAt": "2026-07-23T18:35:00+00:00"
  }
}
```

### `GET /customers/{customerId}/intelligence/latest`

Input: customer UUID in the path. Output is one intelligence object with the
same shape as the refresh response.

### `GET /customers/{customerId}/intelligence`

Input: customer UUID in the path.

```json
{
  "data": [
    {
      "id": "INTELLIGENCE_UUID",
      "aiKeySignal": "Usage is growing while reporting adoption remains uneven.",
      "generationStatus": "completed",
      "generatedAt": "2026-07-23T18:35:00+00:00"
    }
  ]
}
```

## Brief and engagement APIs

### `POST /generate-brief`

Creates a draft engagement and calls OpenAI with schema-validated output.

```json
{
  "customerId": "CUSTOMER_UUID",
  "productId": "PRODUCT_UUID",
  "meetingType": "qbr",
  "deliverableType": "call_brief",
  "notes": "Focus on renewal value and reporting adoption."
}
```

```json
{
  "data": {
    "id": "ENGAGEMENT_UUID",
    "engagementId": "ENGAGEMENT_UUID",
    "customerId": "CUSTOMER_UUID",
    "customerName": "ABC Bank",
    "productId": "PRODUCT_UUID",
    "product": "CRM Platform",
    "meetingType": "QBR",
    "deliverable": "Call Brief",
    "deliverableType": "call_brief",
    "status": "draft",
    "title": "ABC Bank QBR Call Brief",
    "summary": "Preparation focused on renewal value.",
    "customerSnapshot": "ABC Bank is approaching renewal.",
    "keyInsights": ["Usage is growing."],
    "talkingPoints": ["Review reporting outcomes."],
    "suggestedQuestions": ["Which reports matter most?"],
    "risksAndOpportunities": ["Reporting adoption is uneven."],
    "nextSteps": ["Agree on a success metric."]
  }
}
```

### `POST /engagement-log`

```json
{ "engagementId": "ENGAGEMENT_UUID" }
```

```json
{
  "data": {
    "id": "ENGAGEMENT_UUID",
    "customerName": "ABC Bank",
    "title": "ABC Bank QBR Call Brief",
    "summary": "Preparation focused on renewal value.",
    "status": "saved",
    "content": {}
  }
}
```

### `GET /engagement-log?customerId={uuid}`

Input: optional customer UUID.

```json
{
  "data": [
    {
      "id": "ENGAGEMENT_UUID",
      "customerName": "ABC Bank",
      "meetingType": "qbr",
      "deliverableType": "call_brief",
      "title": "ABC Bank QBR Call Brief",
      "meetingSummary": "Preparation focused on renewal value.",
      "status": "saved"
    }
  ]
}
```

### `GET /engagement-log/{engagementId}`

Input: engagement UUID in the path. Output includes the same engagement fields
plus `notes`, `content`, `inputSnapshot`, `model`, and `promptVersion`.

### `PATCH /engagement-log/{engagementId}`

```json
{ "status": "saved" }
```

Output: the updated engagement object. Valid status values are `draft`, `saved`,
and `archived`.

## Delete APIs

### `DELETE /customers/{customerId}`

Input: customer UUID in path.

```json
{
  "data": {
    "id": "CUSTOMER_UUID",
    "deleted": true,
    "deleteMode": "soft",
    "deletedAt": "2026-07-23T18:45:00+00:00"
  }
}
```

### `DELETE /usage/{usageId}`

```json
{
  "data": {
    "id": "USAGE_UUID",
    "deleted": true,
    "deleteMode": "hard"
  }
}
```

### `DELETE /engagement-log/{engagementId}`

```json
{
  "data": {
    "id": "ENGAGEMENT_UUID",
    "deleted": true,
    "deleteMode": "archive",
    "status": "archived"
  }
}
```

The OpenAI integrations use the Responses API and structured outputs so model
responses are validated before database writes. See the official
[Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
and [GPT-5.6 Terra model page](https://developers.openai.com/api/docs/models/gpt-5.6-terra).
