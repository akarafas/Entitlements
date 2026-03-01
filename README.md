# Entitlements System (Flask + React)

A runnable full-stack entitlements system for a publisher website built with:

- **Backend:** Python Flask + SQLAlchemy
- **Frontend:** React JavaScript (Vite)

## What the system supports

- Grant user a product entitlement (`POST` / `PUT`)
- Query a user's active rights (`GET`)
- Revoke and expire access rights lifecycle
- Multiple products per user
- Role model:
  - `support`: read + write
  - `developer`: read only
- Purchase history and access history tracking
- Two seeded accepted test accounts for validation

## Data model

- `User`: name, email, physical address, role
- `Product`: product name + access type (`digital`, `print`, `premium`)
- `Entitlement`: user ↔ product mapping, start/end dates, revoke metadata
- `PurchaseHistory`: user, product, price, date start/end
- `AccessHistory`: user, accessed page, datetime

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

Flask runs on `http://localhost:8000` and auto-creates/initializes `entitlements.db` with seed data.

If you previously installed dependencies before this fix, re-install backend requirements to avoid `hashlib.scrypt` compatibility errors on some Python builds:

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

## Seeded test accounts

- Support (read/write): `support@example.com` / `Support123!`
- Developer (read-only): `developer@example.com` / `Developer123!`

## API endpoints

- `POST /api/auth/login`
- `GET /api/users`
- `GET /api/products`
- `GET /api/entitlements`
- `POST /api/entitlements` (support only)
- `PUT /api/entitlements/{id}` (support only)
- `POST /api/entitlements/{id}/revoke` (support only)
- `GET /api/users/{id}/rights`
- `GET /api/purchase-history`
- `GET /api/access-history`

## Notes

- Payments are intentionally not implemented.
- Entitlement active rights are computed from `is_revoked` and `end_date >= today`.
- Access history logs when rights are queried.
