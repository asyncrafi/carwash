# CarWash API

On-demand car wash booking platform built with Django REST Framework + Celery.

---

## Run the Project

### Docker

Two compose files for different environments:

#### Development (hot reload)

```bash
# 1. Copy env file
cp .env.example .env

# 2. Build & start (runserver + auto-reload on code changes)
docker compose -f docker-compose.dev.yml up --build

# 3. Open in browser
# API:      http://localhost:8000/api/
# Swagger:  http://localhost:8000/api/docs/
# Admin:    http://localhost:8000/admin/
```

**Dev features:** code volume mounts for instant reload, `config.local` settings, browsable DRF API, debug mode, postgres port exposed on host.

#### Production

```bash
# 1. Copy env file (edit for production settings)
cp .env.example .env

# 2. Build & start detached
docker compose -f docker-compose.prod.yml up --build -d

# 3. Check logs
docker compose -f docker-compose.prod.yml logs -f
```

**Prod features:** gunicorn (4 workers), celery (4 concurrency), `config.production` settings, JSON-only API, throttling, no code mounts.

### Local Dev (without Docker)

**Requirements:** Python 3.12+, PostgreSQL 16+, Redis 7+

```bash
# 1. Setup venv
python3.12 -m venv venv && source venv/bin/activate

# 2. Install deps
pip install -r requirements.txt

# 3. Copy env & edit DB creds
cp .env.example .env

# 4. Create database
createdb carwash

# 5. Migrate + seed
python manage.py migrate
python manage.py createsuperuser

# 6. Start services (3 terminals)
redis-server
celery -A config worker --loglevel=info
python manage.py runserver
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | required | Django secret key |
| `DJANGO_SETTINGS_MODULE` | `config.local` | Settings module |
| `DEBUG` | `True` | Django debug mode |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | localhost:5432 | Database config |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker |
| `EMAIL_BACKEND` | `console` | `console` for dev, `anymail` for prod |
| `SENDGRID_API_KEY` | — | For SendGrid email delivery |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | CORS origins |

---

## Architecture

```
carwash/
├── config/               # Django settings (base, local, production)
│   ├── celery.py         # Celery app + autodiscovery
│   └── urls.py           # Root URL routing
├── apps/
│   ├── core/             # Mixins, utils, email tasks, templates
│   ├── accounts/         # User model, auth, OTP, JWT
│   ├── customers/        # Customer profile, addresses, cards, vehicles
│   ├── providers/        # Provider profile, docs, bank, availability
│   ├── services/         # Services, vehicle/engine types, dirt levels
│   ├── bookings/         # Booking lifecycle, signals, jobs
│   ├── payments/         # Payments, provider earnings
│   ├── ratings/          # Ratings, tips
│   ├── notifications/    # Notifications, bulk send
│   └── admin_dashboard/  # Admin CRUD, stats, payouts, config
├── Dockerfile
├── docker-compose.yml    # db + redis + app + celery_worker + celery_beat
└── carwash-api.postman_collection.json
```

---

## API Flow

### 1. Authentication Flow

```
Register ──→ Login ──→ JWT tokens ──→ Bearer Auth ──→ Protected endpoints
                │
                └── Token expired? ──→ Refresh token ──→ New access token
                
Forgot password:
Request OTP ──→ Verify OTP ──→ Reset password with new credentials
```

- Register with `role: customer` or `role: provider`
- Login returns `access` (expires short) + `refresh` (long-lived)
- Set `Authorization: Bearer <access_token>` on all protected endpoints
- Refresh: `POST /api/auth/token/refresh/` with `{ "refresh": "..." }`

### 2. Booking Lifecycle

```
Customer creates booking (pending)
         │
         ▼
Provider accepts job (accepted)
         │
         ▼
Provider marks en_route (en_route)
         │
         ▼
Provider marks in_progress (in_progress)
         │
         ▼
Provider marks completed (completed)
         │
         ▼
Customer adds tip + rating (optional)
```

**Status transitions (booked → cancelled):** Customer can cancel anytime before `in_progress`. Admin can cancel any booking.

**Async (Celery) triggers on each transition:**
- Notification created for the relevant user
- Email sent (booking created, completed, etc.)
- Provider earnings calculated (on `completed`)

### 3. Provider Registration Flow

```
Provider registers ──→ Upload documents ──→ Submit bank details
                                                │
                                                ▼
Admin reviews documents ──→ Approve/Reject ──→ Provider goes online
                                                │
                                                ▼
                                        Sets availability + location
                                                │
                                                ▼
                                        Receives job notifications
```

### 4. Pricing Engine

```
Total = service.base_price
       + vehicle_type.extra_price
       + dirt_level.extra_price
       + distance * distance_price_per_km
       - engine_type.discount_percent% discount
       + platform_fee_fixed
       + tip_amount (optional, added after completion)

Provider earnings:
  Net = total - platform_fee - (total * commission_percent%)
```

### 5. Admin Operations

```
Dashboard ──→ Stats (users, bookings, revenue)
Users     ──→ List, block/unblock, change role
Providers ──→ Review docs, approve/reject
Bookings  ──→ View all, cancel any
Earnings  ──→ Platform revenue, pending payouts
Payouts   ──→ View, retry failed
Services  ──→ CRUD car wash services & pricing
Config    ──→ Platform fees, commission rates
Notify    ──→ Send bulk notification (all/customers/providers)
```

---

## Postman Collection

Import `carwash-api.postman_collection.json` into Postman.

**Setup:**
1. Click **Environments → Import** → create environment with:
   - `base_url`: `http://localhost:8000`
   - `access_token`: (leave blank)
   - `refresh_token`: (leave blank)
2. Go to **Login** request → **Tests** tab → paste this:
   ```javascript
   const json = pm.response.json();
   if (json.data && json.data.access) {
       pm.environment.set("access_token", json.data.access);
       pm.environment.set("refresh_token", json.data.refresh);
   }
   ```
3. **Send Register** (create user) → **Send Login** (tokens auto-set)
4. All other requests inherit `{{access_token}}` automatically

**Folders:**
| Folder | Endpoints | Auth |
|---|---|---|
| System | Health, Schema, Swagger | ❌ |
| Auth | Register, Login, OTP, Password | Some |
| Customer | Profile, Addresses, Cards, Vehicles | ✅ |
| Provider | Profile, Online, Docs, Bank, Availability | ✅ |
| Services | Services, Vehicle/Engine Types, Dirt Levels | ❌ |
| Bookings | CRUD, Tips, Ratings, Jobs | ✅ |
| Payments | Earnings | ✅ |
| Ratings | My Ratings | ✅ |
| Notifications | List, Read, Read All | ✅ |
| Admin | Dashboard, Users, Docs, Bookings, Earnings, Config | ✅ (Admin) |

---

## Celery Tasks

All 17 async tasks auto-discovered:

```
accounts:   send_welcome_email, send_otp_email, send_password_reset_email, 
            send_provider_approved_email
bookings:   handle_booking_{created,accepted,en_route,in_progress,completed,cancelled},
            handle_user_registered
core:       send_email (generic)
notifications: create_notification, notify_all_online_providers, bulk_create_notifications
payments:   create_provider_earning, send_booking_completed_email
```

Monitor via `celery -A config flower` or view logs: `docker compose logs -f celery_worker`.

---

## Quick Test Sequence

```bash
# 1. Register a customer
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"phone":"+971501234567","password":"test1234","role":"customer","full_name":"John Doe"}'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone":"+971501234567","password":"test1234"}'

# 3. List services (public)
curl http://localhost:8000/api/services/

# 4. Create booking (use token from login)
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"service":1,"vehicle":1,"dirt_level":1,"service_address":"Dubai Marina","schedule_type":"now"}'

# 5. Check Swagger docs
open http://localhost:8000/api/docs/
```
# carwash
# carwash
