# Entitlements System (Flask + React)

A runnable full-stack entitlements system for a publisher website built with:

- **Backend:** Python Flask + SQLAlchemy
- **Frontend:** React JavaScript (Vite)

## What the system supports

- Grant customer product entitlements (`POST` / `PUT`)
- Query a customer's active rights (`GET`)
- Revoke and expire access rights lifecycle
- Multiple products per customer
- Clear separation of identities:
  - **App users** (support/developer) authenticate into the console
  - **Customers** are the consumers who receive entitlements
- Role model:
  - `support`: read + write
  - `developer`: read only
- Purchase history and access history tracking

## Data model

- `AppUser`: support/developer users with app access credentials
- `Customer`: media consumer profile (name, email, address)
- `Product`: product name, free-text description, and capability set (`READ_DIGITAL`, `RECEIVE_PRINT`, `NO_ADS`)
- `Entitlement`: customer ↔ product mapping, start/end dates, revoke metadata
- `PurchaseHistory`: customer, product, price, date start/end
- `AccessHistory`: customer, accessed page, datetime

## Project layout

- `backend/` Flask API
- `frontend/` React UI (support console)

## Run locally

### 1) Backend (Flask)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Flask runs on `http://localhost:8000` and auto-creates/initializes `entitlements_v2.db` with seed data.

If you previously installed dependencies before this fix, re-install backend requirements:

```bash
pip install -r requirements.txt --upgrade
```

### 2) Frontend (React)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

### Frontend troubleshooting (blank page)

If `http://localhost:5173` is blank:

1. Ensure backend is running on `http://localhost:8000`.
2. In `frontend/.env`, confirm `VITE_API_BASE=http://localhost:8000/api`.
3. Reinstall frontend dependencies after this update:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

4. Open browser devtools console for runtime errors (the app now shows a fallback message if render fails).
5. Hard refresh the page (`Cmd+Shift+R` on macOS / `Ctrl+F5` on Windows/Linux) to clear stale cached bundles.
6. Confirm the Vite terminal shows `Local: http://localhost:5173/` and no build errors.

## Seeded test data

### App users (can log in)

- Support (read/write): `support@example.com` / `Support123!`
- Developer (read-only): `developer@example.com` / `Developer123!`

### Customers (cannot log in)

- `alex.reader@example.com`
- `priya.subscriber@example.com`
- `morgan.print@example.com`

## API endpoints

- `POST /api/auth/login`
- `GET /api/app-users`
- `GET /api/customers`
- `POST /api/customers` (support only)
- `PUT /api/customers/{id}` (support only)
- `GET /api/products`
- `PUT /api/products/{id}` (support only, includes editable `description`)
- `GET /api/entitlements`
- `POST /api/entitlements` (support only)
- `PUT /api/entitlements/{id}` (support only)
- `POST /api/entitlements/{id}/revoke` (support only)
- `GET /api/customers/{id}/rights`
- `GET /api/purchase-history`
- `GET /api/access-history`

## Potential Enhancements
- Caching: Since this service acts as a gateway and is called on nearly every user interaction, adding a caching layer for resolved entitlements would significantly reduce latency and database load.
- Authentication & Authorization: Replace the simplified developer/support login with a proper auth solution (e.g., RBAC or SSO) to clearly separate end-user access from administrative and support workflows.
- Schema Refinement: Further normalize the schema around customers, users, products, and entitlements to better reflect real-world relationships and support future product expansion.
- Multiple Subscriptions: Expand entitlement resolution logic to handle multiple active products per user (e.g., returning the union of entitlements or applying precedence rules), depending on business requirements.
- Scalability: Containerize the application to enable horizontal scaling, especially to handle traffic spikes during content releases or breaking news.
- Audit & Analytics: Add a lightweight action history for entitlement changes and access checks to support debugging, security, and usage analysis.
- Support Tooling: Enhance the UI to allow authorized support staff to edit entitlements for common customer support scenarios.

## Notes


- Capability model for default seeded products:
  - `Digital`  → `[READ_DIGITAL]`
  - `Print`    → `[READ_DIGITAL, RECEIVE_PRINT]`
  - `Premium`  → `[READ_DIGITAL, RECEIVE_PRINT, NO_ADS]`
- Payments are intentionally not implemented.
- Entitlements expose lifecycle `status` as `active`, `revoked`, or `expired` (expired after end date).
- Entitlement active rights are computed from `is_revoked` and `end_date >= today`.
- Access history logs customer rights lookups.
