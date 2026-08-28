# FlowBill — Master Project Todo List & Implementation Roadmap

**Architecture:** Django 6 REST API (`flowbill/`) + Next.js 16 App Router (`frontend/`)  
**Specification Reference:** `FlowBill_SRS_v1.0.md` (v1.1.0) & `FlowBill_SD_v1.0.md` (v1.1.0)  
**Legend:** ⬜ Pending · 🟡 In-Progress · ✅ Completed

---

## Phase 1: Core Async Infrastructure & Business Profile

- [x] **1.1 Celery Async Infrastructure (`flowbill/config/`)**
  - [x] Create `flowbill/config/celery.py` and register the Celery app instance in `config/__init__.py`.
  - [x] Convert `apps.notifications.tasks` functions to Celery tasks invoked asynchronously via `.delay()`.
  - [x] Ensure test environment runs tasks in eager mode (`CELERY_TASK_ALWAYS_EAGER = True` in `config/settings/test.py`).

- [x] **1.2 TOTP Email Verification & Business Profile Module (`apps/accounts/`)**
  - [x] Implement 6-digit TOTP email verification with brute-force lockout (5 attempts) and 60s cooldown resend.
  - [x] Create `BusinessProfile` model (1:1 with `accounts.User`): `business_name`, `logo_url`, `phone`, `website`, `address`, `city`, `state`, `country`, `tax_id`, `bank_account_name`, `bank_account_number`, `bank_name`, `default_currency`, `default_payment_terms`, `payment_instructions`.
  - [x] Implement `BusinessProfileSerializer` with validation.
  - [x] Implement `AccountsService.get_or_create_profile()` and `AccountsService.update_profile()`.
  - [x] Expose `GET /api/v1/auth/profile/` and `PUT/PATCH /api/v1/auth/profile/`.
  - [x] Write unit & view tests maintaining 94.64% test coverage.
  - [x] Wire `BusinessProfile` fields into `apps/invoices/pdf.py` context and `templates/invoices/invoice_pdf.html`.

- [x] **1.3 Password Reset Flow (`apps/accounts/`)**
  - [x] Implement 6-digit OTP password reset request (`POST /api/v1/auth/password-reset/`).
  - [x] Implement password reset confirmation (`POST /api/v1/auth/password-reset/confirm/`).
  - [x] Add integration tests.

---

## Phase 2: Client Portal & Payments

- [ ] **2.1 Public Client Portal (`apps/portal/`)**
  - [ ] Create `InvoiceMagicLink` model: `invoice` (1:1), 32-byte cryptographic `token`, `expires_at` (default 30 days), `viewed_at`, `is_active`.
  - [ ] Implement `ClientPortalService`:
    - `generate_magic_link(invoice)`: Generates secure token on invoice send.
    - `validate_magic_link(token)`: Validates active state and expiry without requiring login.
    - `record_view(token)`: Records first viewed timestamp and logs `viewed` in `InvoiceEvent`.
  - [ ] Expose public portal endpoints:
    - `GET /api/v1/portal/{token}/` (read-only invoice details + issuer profile)
    - `GET /api/v1/portal/{token}/pdf/` (stream invoice PDF download)
    - `POST /api/v1/portal/{token}/pay/` (initialize online checkout)
  - [ ] Update `InvoiceService.send_invoice()` to generate magic links and include URL in client emails.
  - [ ] Add comprehensive test suite.

- [ ] **2.2 Payment Gateway Integration (`apps/payments/`)**
  - [ ] Implement `BasePaymentGateway` abstract class and `PaystackGateway` (Paystack API v2).
  - [ ] Implement `Payment` model and `PaymentService`:
    - Transaction initialization and reference generation.
    - Webhook handler (`POST /api/v1/webhooks/paystack/`) with HMAC-SHA512 signature validation.
    - Atomic invoice status transition (`pending/overdue` → `paid`), payment recording, and `paid` audit event logging.
    - Payment confirmation emails to tenant and client via notification tasks.
  - [ ] Expose manual payment recording (`POST /api/v1/payments/`).
  - [ ] Add unit and mock integration tests.

---

## Phase 3: Automation & Scheduled Tasks

- [ ] **3.1 Automated Overdue State Machine (`apps/invoices/`)**
  - [ ] Implement Celery task `mark_overdue_invoices_task` to query pending invoices past due date and mark as `overdue`.
  - [ ] Configure Celery Beat schedule in settings (daily at 00:00 UTC).
  - [ ] Add tests with `freezegun`.

- [ ] **3.2 Recurring Invoices Module (`apps/invoices/`)**
  - [ ] Create `RecurringInvoice` model: `template_invoice` (FK), `interval` (`weekly`, `monthly`, `quarterly`, `annually`), `next_run_at`, `status` (`active`, `paused`, `cancelled`), `instances_count`.
  - [ ] Implement `RecurringInvoiceService.generate_due_invoices()`: Clones draft invoices from template on schedule.
  - [ ] Configure Celery Beat periodic task (hourly execution).
  - [ ] Expose CRUD endpoints under `/api/v1/recurring-invoices/`.
  - [ ] Add unit & integration tests.

- [ ] **3.3 Reporting & CSV Export (`apps/dashboard/`)**
  - [ ] Expose `GET /api/v1/dashboard/export/` for streaming CSV export of invoices and expenses.

---

## Phase 4: Frontend Web Application (`frontend/` Next.js 16)

- [ ] **4.1 API Client, State & Middleware**
  - [ ] Build `src/lib/api.ts` (fetch client with JWT refresh token handling and response unwrapping).
  - [ ] Implement Auth Provider / Context (session storage, login, logout, user profile state).
  - [ ] Implement Route Protection Middleware (`src/middleware.ts`) for `/dashboard/*`.

- [ ] **4.2 Authentication & Onboarding Screens**
  - [ ] `/login`: Email/password login with JWT cookie storage.
  - [ ] `/register`: Account registration with password strength meter.
  - [ ] `/verify-email`: Token verification landing page.
  - [ ] `/forgot-password` & `/reset-password`: Password recovery screens.
  - [ ] `/onboarding`: Guided step-by-step business profile setup (business name, logo upload, address, currency, banking details).

- [ ] **4.3 Dashboard Core Views**
  - [ ] Layout shell: Sidebar navigation, quick actions, user menu, and dark/light theme tokens.
  - [ ] **Overview (`/dashboard`)**:
    - Summary stat cards (Total Earned, Total Pending, Total Overdue, Active Clients).
    - 6-month interactive revenue chart.
    - Recent invoices table and upcoming due alerts.
  - [ ] **Invoices (`/dashboard/invoices`)**:
    - Paginated invoice table with status badge filters, search, and date sorting.
    - Invoice Creator & Editor (`/dashboard/invoices/new`, `/dashboard/invoices/[id]/edit`):
      * Dynamic line item builder with live calculation (quantity × price + tax).
      * Client selector, payment terms, discount, notes, and PDF live preview.
    - Invoice Detail View (`/dashboard/invoices/[id]`):
      * Action buttons (Send Invoice, Mark as Paid, Duplicate, Cancel, Download PDF).
      * Visual audit event timeline (`InvoiceEvent`).
  - [ ] **Clients (`/dashboard/clients`)**:
    - Client table with search, company name, currency, and active status.
    - Create/Edit client modal.
    - Client detail view with billing summary and associated invoices.
  - [ ] **Expenses (`/dashboard/expenses`)**:
    - Expense logging table with category filters and client linkage.
    - Add/Edit expense modal with receipt upload.
  - [ ] **Settings (`/dashboard/settings`)**:
    - Business branding, address, tax ID, and banking details editor.
    - Default currency and payment terms selector.

- [ ] **4.4 Public Client Portal View (`/portal/[token]`)**
  - [ ] Unauthenticated responsive invoice preview.
  - [ ] Issuer business profile and line items breakdown.
  - [ ] Direct PDF download button.
  - [ ] Paystack "Pay Now" checkout button with modal/redirect.
  - [ ] Post-payment confirmation receipt screen.

---

## Phase 5: Production Readiness & DevOps

- [ ] **5.1 Health Checks & Rate Limiting**
  - [ ] Implement `/api/v1/health/` and `/api/v1/ready/` in `config/urls.py`.
  - [ ] Configure DRF throttling in `base.py` (100 req/min public, 1000 req/min authenticated).

- [ ] **5.2 Docker & CI/CD**
  - [ ] Multi-stage `Dockerfile` and `docker-compose.yml` (Django, Next.js, Postgres, Redis, Celery).
  - [ ] GitHub Actions workflow (`.github/workflows/ci.yml`): Runs backend `pytest` (enforcing 80% coverage) and frontend `tsc --noEmit`.
