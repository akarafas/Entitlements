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
- `Product`: product name + access type (`digital`, `print`, `premium`)
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
- `GET /api/products`
- `GET /api/entitlements`
- `POST /api/entitlements` (support only)
- `PUT /api/entitlements/{id}` (support only)
- `POST /api/entitlements/{id}/revoke` (support only)
- `GET /api/customers/{id}/rights`
- `GET /api/purchase-history`
- `GET /api/access-history`

## Notes

- Payments are intentionally not implemented.
- Entitlement active rights are computed from `is_revoked` and `end_date >= today`.
- Access history logs customer rights lookups.
