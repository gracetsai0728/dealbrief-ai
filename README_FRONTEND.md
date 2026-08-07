# DealBrief AI frontend

The React 19 and Vite frontend provides:

- Login and user registration
- Subscription, Intelligence, and Meeting Brief pages for regular users
- A single Admin page for administrators
- Manual customer, product, and subscription entry
- Subscription tables showing start date, end date, status, and licensed seats

Subscription combines annual renewals into one to three product licensed-seat lines.
Intelligence separates
industry dynamics, sourced recent company news, and Cross-sell, Upsell,
Renewal, and Winback recommendations.

Generated briefs are displayed and can be copied, but are not saved to an
Engagement Log.

## Run

```bash
npm install
npm run dev
```

The application is available at `http://localhost:5173`. The frontend calls the
Flask API through `src/api.js`; configure its URL in the root `.env`:

```dotenv
VITE_API_URL=http://localhost:3000/api
```

## Validate

```bash
npm run lint
npm run build
npm run test:e2e
```
