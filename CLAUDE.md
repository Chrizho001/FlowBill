# CLAUDE.md
# FlowBill Monorepo — Developer & AI Agent Guide

This file provides authoritative guidance to Claude Code and developers working across the **FlowBill** codebase.

---

## 1. Project Overview & Architecture

FlowBill is a SaaS platform for freelancers and small agencies to manage clients, issue invoices, track expenses, accept payments, and monitor business health.

### Monorepo Structure
```
FLOWBILL PROJECT/
├── .claude/                          # Automated verification hooks & settings
├── system design and Requirements/   # Specifications (SRS, SDD, Status v1.1.0)
├── flowbill/                         # Django 6 / DRF REST API (Python 3.12+, uv)
│   ├── apps/                         # Domain apps (accounts, clients, invoices, etc.)
│   ├── config/                       # Settings (base/dev/prod/test), celery.py, urls.py
│   ├── core/                         # BaseModel (UUID7, soft-delete), exceptions, pagination
│   ├── templates/invoices/           # WeasyPrint PDF HTML/CSS template
│   └── tests/                        # Factory-boy test factories
└── frontend/                         # Next.js 16 (App Router) + React 19 + Tailwind v4
```

### Spec vs. Reality Alignment
`system design and Requirements/` contains the approved specifications (`FlowBill_SRS_v1.0.md` and `FlowBill_SD_v1.0.md` v1.1.0). Multi-tenancy is formalized on **row-level `owner`-scoping** (`owner = models.ForeignKey(User, on_delete=CASCADE)`). Every query must filter `owner=user`.

---

## 2. Automated Hooks (`.claude/hooks/`)

This monorepo has automated verification hooks configured in `.claude/settings.json`. Whenever a file is edited, the hooks automatically run:

1. **Security & Secret Scanner ([secret-scanner.sh](file:///home/chris-friday/Documents/PROJECTS/FLOWBILL%20PROJECT/.claude/hooks/secret-scanner.sh))**: Blocks hardcoded API keys, tokens, and private keys.
2. **Backend Test & Integrity Hook ([backend-check.sh](file:///home/chris-friday/Documents/PROJECTS/FLOWBILL%20PROJECT/.claude/hooks/backend-check.sh))**:
   - Runs `python manage.py check` to catch configuration/syntax errors.
   - Runs `makemigrations --check --dry-run` on `models.py` edits to prevent missing migrations.
   - Executes targeted `pytest` tests on the modified app in seconds.
3. **Frontend Type-Check Hook ([frontend-check.sh](file:///home/chris-friday/Documents/PROJECTS/FLOWBILL%20PROJECT/.claude/hooks/frontend-check.sh))**:
   - Runs `npx tsc --noEmit` on modified Next.js/React files to catch type errors.

---

## 3. Commands

### Backend (`flowbill/`) — Prefix with `uv run`
All backend commands must run from the `flowbill/` directory:
- **Dev Server**: `uv run python manage.py runserver` (uses `config.settings.development`)
- **Migrations**: `uv run python manage.py makemigrations` / `uv run python manage.py migrate`
- **Superuser**: `uv run python manage.py createsuperuser`
- **Full Test Suite & Coverage Gate**: `uv run python -m pytest` (enforces `--cov-fail-under=80`)
- **Targeted Fast App Test**: `uv run python -m pytest apps/<app_name>/tests/ --no-cov`
- **Single Test Method**: `uv run python -m pytest apps/invoices/tests/test_views.py::TestInvoiceCreate::test_create_invoice_success --no-cov`
- **Add Dependencies**: `uv add <pkg>` (runtime) or `uv add --dev <pkg>` (dev)
- **Django Integrity Check**: `uv run python manage.py check`

### Frontend (`frontend/`)
All frontend commands must run from the `frontend/` directory:
- **Dev Server**: `npm run dev` (runs on `http://localhost:3000`)
- **Type Check**: `npx tsc --noEmit`
- **Build Bundle**: `npm run build`
- **Linting**: `npm run lint`

---

## 4. Backend Architectural Rules & Conventions

### A. Layered Architecture: View → Service → Model
- **Views (`views.py`)**: Thin `APIView` subclasses. Only handle request deserialization, serializer validation, calling the service class, and returning standardized responses.
- **Services (`services.py`)**: Pure Python classes exposing `@staticmethod`s (e.g. `InvoiceService`, `AccountsService`, `ClientService`). **All business logic, state machine transitions, server-side calculations, and atomic transactions live here.** Never write business logic in views or serializers.
- **Models (`models.py`)**: Inherit from `core.models.BaseModel`.

### B. Base Models & Multi-Tenancy (`core/models.py`)
- `BaseModel` combines:
  - `UUIDModel`: Time-ordered `UUIDv7` primary key (`uuid6.uuid7`).
  - `TimeStampedModel`: `created_at` (indexed) and `updated_at`.
  - `SoftDeleteModel`: `is_deleted=True` and `deleted_at`. Always filter querysets with `is_deleted=False`. Use `.restore()` to recover.
- `accounts.User` is a custom email-as-identifier model (`AUTH_USER_MODEL = "accounts.User"`).
- Every tenant model has an `owner` FK to `User`. Services must scope every read and write with `owner=user`.

### C. Standardized API Envelopes
- **Success**: `{"status": "success", "data": ..., "message": ...}`
- **Paginated Lists**: `{"status": "success", "meta": {"page": 1, "page_size": 10, "total_pages": 4, "total_count": 34}, "data": [...]}` (via `core.pagination.StandardPagination`).
- **Errors**: Centralized in `core/exceptions.py::flowbill_exception_handler`:
  `{"status": "error", "code": "VALIDATION_ERROR", "message": "...", "fields": {"field_name": ["Error detail"]}}` (returns 400 Bad Request on validation errors).

### D. Authentication & Security
- **JWT**: `djangorestframework-simplejwt` (access token 15 min, refresh token 7 days with rotation and blacklisting).
- **Social Auth**: `django-allauth` + `dj-rest-auth` (Google & GitHub OAuth).
- **Email Verification**: Mandatory. `AccountsService` generates a one-time token stored in Redis cache (24h expiry) and dispatches via notification task.
- DRF permissions default to `IsAuthenticated` + JWT globally.

### E. Invoices Domain Rules
- **State Machine**: `draft → pending → paid / overdue / cancelled`. Only `draft` invoices can be edited or sent.
- **Server-Side Totals**: `subtotal`, `tax_amount`, and `total` are computed exclusively server-side in `InvoiceService._calculate_totals`. Never trust client-submitted totals.
- **Invoice Numbers**: Auto-generated sequence `INV-YYYY-XXXX`, sequential globally per year, immutable.
- **Audit Log**: `InvoiceEvent` is append-only. Never update or delete its rows.
- **PDF Generation**: WeasyPrint renders `templates/invoices/invoice_pdf.html` via `apps.invoices.pdf.PDFService`.

### F. Logging
- Use `structlog` with event-name-first calls:
  `logger.info("invoices.created", invoice_id=str(invoice.id), owner_id=str(user.id), total=str(total))`
  Never use raw `print()` or standard Python `logging`.

### G. Testing & TDD
- Write tests first (TDD). Every new model, endpoint, and service method must have comprehensive tests.
- Tests live in `apps/<app_name>/tests/test_*.py`.
- Use `factory-boy` factories in `tests/factories.py` (`UserFactory`, `ClientFactory`, `InvoiceFactory`, `LineItemFactory`, `ExpenseFactory`) rather than manually creating model instances.
- Total coverage must stay ≥ 80% (`--cov=apps`).

### H. Settings Layout
- `config/settings/base.py`: Shared base configuration.
- `config/settings/development.py`: Default development settings (Postgres, Redis, console email).
- `config/settings/test.py`: Fast testing settings (locmem cache, MD5 hasher, eager tasks).
- `config/settings/production.py`: Production settings with WhiteNoise and secure cookies.

---

## 5. First Steps for a Fresh Session
1. Run `uv run python -m pytest` in `flowbill/` to confirm all 218+ tests pass and coverage is ≥ 80%.
2. Run `bash .claude/hooks/run-all-checks.sh` to ensure hook integrations are healthy.
3. Consult `system design and Requirements/IMPLEMENTATION_STATUS.md` for prioritized feature pick-ups.
