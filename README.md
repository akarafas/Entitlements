# Entitlements System

A runnable full-stack entitlements system for a publisher website using **Django + Django REST Framework** and **Next.js (React)**.

## Features

- Grant/update user product entitlements (`POST` / `PUT`)
- Query a user's current access rights (`GET`)
- Revoke access rights and support expiry lifecycle
- Multiple products per user
- Purchase history tracking
- Access history tracking
- Role-based access control:
  - `support` = read/write entitlement operations
  - `developer` = read-only
- Seeded test accounts for support/developer

## Project layout

- `backend/` Django API server
- `frontend/` Next.js support UI

## Quick start

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver 0.0.0.0:8000
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Test accounts

- Support (read/write): `support@example.com` / `Support123!`
- Developer (read-only): `developer@example.com` / `Developer123!`

## API overview

- `POST /api/auth/login/` -> returns DRF token and user role
- `GET /api/products/`
- `GET /api/users/`
- `GET /api/entitlements/`
- `POST /api/entitlements/` (support only)
- `PUT /api/entitlements/{id}/` (support only)
- `POST /api/entitlements/{id}/revoke/` (support only)
- `GET /api/users/{id}/rights/` -> active rights summary
- `GET /api/purchase-history/`
- `GET /api/access-history/`

## Notes

- Expired entitlements are excluded from active rights automatically.
- Access history is also logged when rights are queried.
