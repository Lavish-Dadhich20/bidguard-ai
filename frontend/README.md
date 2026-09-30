# BidGuard AI Frontend

Production-oriented React/Vite frontend for the BidGuard AI procurement compliance platform.

## Core rule

This frontend intentionally contains **no seeded/random production data** and does not calculate compliance itself. Tender, bidder, document, verification, compliance, report and audit data must come from the Python backend.

## Frontend-only mode

If `VITE_API_BASE_URL` is not set, the app automatically runs in **frontend preview mode**. It contains no generated tender/bidder/compliance data. List pages show empty states and the document page shows the fixed 15 document types as missing until the backend is connected.

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Set:

```env
VITE_API_BASE_URL=http://localhost:8000
```

to the URL of your Python backend.

## API contract

The service layer is in `src/services/api.ts`. It centralizes calls for:

- authentication
- tenders
- bidders
- document upload/replacement/removal
- Stage 1 verification
- compliance
- tender compliance across multiple bidders
- reports
- audit trail

If your existing FastAPI routes use different paths or response shapes, update **only the service layer / type adapters**, not the page components.

## Important integration note

The UI currently uses `/me` as the bidder identifier for account-scoped document/compliance calls. If your backend returns a concrete bidder ID from `/auth/me`, update the relevant page to use `user.id`.

The frontend does not recreate Stage 1/Stage 2 verification logic and does not generate compliance scores.

## No fake data

When the backend returns no data, the UI shows an empty state. It does not manufacture records to make the dashboard look populated.
