# FlowBill — Software Design Document (SDD)
## Architecture, OOP Design, Database Schema & API Specification

| Document Type | SDD |
| --- | --- |
| Version | v1.1.0 |
| Date | August 2026 |
| Author | FlowBill Dev Team |
| Status | Approved — Aligned with Codebase & Architecture |

---

# 1. System Architecture Overview

## 1.1 Architectural Style
FlowBill is designed around a **Layered Clean Architecture** on the backend paired with a **Single Page / Server-Rendered Frontend** built on Next.js 16.

```
┌───────────────────────────────────────────────────────────────────────┐
│                    Presentation Layer (Next.js 16)                    │
│  - Authenticated SaaS Dashboard (App Router, Tailwind CSS v4)         │
│  - Public Client Portal (Magic Link Invoice View & Payment Checkout)  │
└──────────────────────────────────┬────────────────────────────────────┘
                                   │ HTTPS / JSON API
┌──────────────────────────────────▼────────────────────────────────────┐
│                    API Layer (Django REST Framework)                  │
│  - URL Routing & Versioning (/api/v1/)                                │
│  - Serializers (Validation & Representation)                          │
│  - Standardized Exception Handling & Pagination Envelope              │
│  - JWT & OAuth2 Authentication (SimpleJWT + django-allauth)           │
└──────────────────────────────────┬────────────────────────────────────┘
                                   │ DTOs / Validated Data
┌──────────────────────────────────▼────────────────────────────────────┐
│                    Service Layer (Pure Python Classes)                │
│  - AccountsService, ClientService, InvoiceService, PDFService         │
│  - PaymentService, ClientPortalService, ExpenseService, Dashboard     │
│  - Gateway Strategy: BasePaymentGateway -> PaystackGateway            │
└──────────────────┬─────────────────────────────────┬──────────────────┘
                   │ ORM Querysets                   │ Async Tasks (.delay())
┌──────────────────▼──────────────────┐   ┌──────────▼──────────────────┐
│             Data Layer              │   │     Celery Task Queue       │
│  - PostgreSQL 16+ (Row-Level Scope) │   │  - Redis 8 Broker           │
│  - BaseModel (UUIDv7, Soft-Delete)  │   │  - Email Delivery Worker    │
│  - Composite Indexes by owner_id    │   │  - PDF Rendering & Beat     │
└─────────────────────────────────────┘   └─────────────────────────────┘
```

The four core layers are:
1. **Presentation Layer**: Next.js 16 (App Router) + React 19 + Tailwind CSS v4. Consumes the REST API and renders both the user dashboard and the unauthenticated client portal.
2. **API Layer (DRF)**: Thin `APIView` classes responsible solely for authentication, deserialization, payload validation, and serializing responses.
3. **Service Layer**: App-specific domain service classes (`apps.<module>.services`) housing all business logic, transactions, state machines, and calculations. Views never perform database mutations directly.
4. **Data Layer**: PostgreSQL database managed via Django ORM. Multi-tenancy is enforced via row-level scoping (`owner = models.ForeignKey(User)`).

## 1.2 Multi-Tenancy Architecture (Row-Level Scoping)
FlowBill utilizes **Row-Level Tenancy Scoping**:
- Every business entity (`Client`, `Invoice`, `Expense`, `RecurringInvoice`, `BusinessProfile`) maintains a foreign key to `accounts.User` (`owner`).
- All queries in the Service Layer explicitly filter by `owner=user`.
- Database indexes on `(owner_id, is_deleted, ...)` ensure optimal query execution plans.
- Unique constraints (e.g. `unique_active_client_email_per_owner`) enforce tenant-level uniqueness rather than global table uniqueness.

This model provides strong, reliable multi-tenant isolation, effortless migrations, zero connection-switching latency, and operational simplicity.

---

# 2. Object-Oriented Design & Domain Models

## 2.1 OOP Principles Applied

| Principle | Application in FlowBill |
| --- | --- |
| **Single Responsibility** | Services handle domain logic (`InvoiceService`, `PDFService`), Views handle HTTP routing, Serializers handle data validation/transformation, Models define schemas. |
| **Open / Closed** | Payment gateways implement an abstract `BasePaymentGateway` contract; new providers (Stripe) can be added without modifying existing checkout orchestration. |
| **Liskov Substitution** | `PaystackGateway` and future `StripeGateway` can be swapped interchangeably wherever `BasePaymentGateway` is consumed. |
| **Encapsulation** | Invoice calculations (subtotal, tax, discount, total) and state machine validations are private methods within `InvoiceService`. |
| **DRY (Don't Repeat Yourself)** | Shared abstract base classes ([BaseModel](file:///home/chris-friday/Documents/PROJECTS/FLOWBILL%20PROJECT/flowbill/core/models.py)) provide UUIDv7 primary keys, timestamps, and soft-delete capabilities. |

---

## 2.2 Core Domain Models

### 2.2.1 Base Infrastructure Models (`core/models.py`)

```python
class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid6.uuid7, editable=False)

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    def delete(self, using=None, keep_parents=False): ...
    def restore(self): ...

class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Base model for all FlowBill business entities."""
```

---

### 2.2.2 User & Profile Domain (`apps.accounts`)

```
┌───────────────────────────────────────┐       1:1       ┌───────────────────────────────────────┐
│              User                     │─────────────────│           BusinessProfile             │
│ ───────────────────────────────────── │                 │ ───────────────────────────────────── │
│ id: UUID7 (PK)                        │                 │ id: UUID7 (PK)                        │
│ email: EmailField (Unique, Index)     │                 │ user: OneToOneField(User, CASCADE)    │
│ full_name: CharField(255)             │                 │ business_name: CharField(255)         │
│ is_verified: BooleanField             │                 │ logo_url: URLField / ImageField       │
│ is_active: BooleanField               │                 │ phone: CharField(20)                  │
│ is_staff: BooleanField                │                 │ address, city, state, country: Char   │
│ created_at / updated_at               │                 │ tax_id: CharField(50)                 │
│                                       │                 │ bank_name, bank_account_name, num     │
│                                       │                 │ default_currency, payment_terms       │
└───────────────────────────────────────┘                 └───────────────────────────────────────┘
```

---

### 2.2.3 Core Billing & Invoicing Domain

```
       ┌────────────────────────┐
       │         User           │
       └───────────┬────────────┘
                   │ 1:N
       ┌───────────▼────────────┐ 1:N ┌────────────────────────┐
       │        Client          │────<│        Invoice         │
       │ ────────────────────── │     │ ────────────────────── │
       │ id: UUID7 (PK)         │     │ id: UUID7 (PK)         │
       │ owner: FK(User)        │     │ owner: FK(User)        │
       │ name, email, phone     │     │ client: FK(Client)     │
       │ company_name, currency │     │ number: INV-YYYY-XXXX  │
       │ status: active/inactive│     │ status: draft/pending..│
       │ is_deleted: Boolean    │     │ issue_date, due_date   │
       └────────────────────────┘     │ currency, subtotal...  │
                                      └───────────┬────────────┘
                                                  │
                   ┌──────────────────────────────┼──────────────────────────────┐
                   │ 1:N                          │ 1:1                          │ 1:N
       ┌───────────▼────────────┐     ┌───────────▼────────────┐     ┌───────────▼────────────┐
       │       LineItem         │     │    InvoiceMagicLink    │     │      InvoiceEvent      │
       │ ────────────────────── │     │ ────────────────────── │     │ ────────────────────── │
       │ id: UUID7 (PK)         │     │ id: UUID7 (PK)         │     │ id: UUID7 (PK)         │
       │ invoice: FK(Invoice)   │     │ invoice: OneToOne(Inv) │     │ invoice: FK(Invoice)   │
       │ description: Char(500) │     │ token: CharField(64)   │     │ event_type: created..  │
       │ quantity: Decimal      │     │ expires_at: DateTime   │     │ description: Char(500) │
       │ unit_price, tax_rate   │     │ viewed_at: DateTime    │     │ metadata: JSONField    │
       │ total: Decimal         │     │ is_active: Boolean     │     │ created_at: DateTime   │
       └────────────────────────┘     └────────────────────────┘     └────────────────────────┘
```

---

## 2.3 Service Layer Architecture

Business logic is organized into stateless service classes exposing static methods:

| Service Class | File Location | Core Responsibilities |
| --- | --- | --- |
| **`AccountsService`** | `apps/accounts/services.py` | User registration, token generation in Redis cache, email verification, password reset, profile management. |
| **`ClientService`** | `apps/clients/services.py` | Client CRUD, active email uniqueness validation, soft deletion protection when linked to active invoices. |
| **`InvoiceService`** | `apps/invoices/services.py` | Atomic invoice creation, server-side line calculations, status transitions (`send`, `mark_paid`, `cancel`), number generation (`INV-YYYY-XXXX`), duplication, and audit logging. |
| **`PDFService`** | `apps/invoices/pdf.py` | WeasyPrint HTML/CSS rendering pipeline, context preparation with business branding and line items. |
| **`PaymentService`** | `apps/payments/services.py` | Manual payment recording, gateway initialization, webhook processing, payment event logging. |
| **`ClientPortalService`** | `apps/portal/services.py` | Magic link generation, token validation, portal view payload generation, tracking client views. |
| **`ExpenseService`** | `apps/expenses/services.py` | Expense logging, category tracking, client expense linkage. |
| **`DashboardService`** | `apps/dashboard/services.py` | Aggregated metrics calculation (earned, pending, overdue), 6-month continuous revenue charts, top clients. |
| **`NotificationService`** | `apps/notifications/tasks.py`| Async email dispatching for email verification, invoice notifications, and payment receipts. |

---

## 2.4 Payment Gateway Abstraction (Strategy Pattern)

To enable seamless support for multiple payment providers (Paystack in v1, Stripe in v2), the payment module implements the Strategy Pattern:

```python
from abc import ABC, abstractmethod

class BasePaymentGateway(ABC):
    @abstractmethod
    def initialize_transaction(self, invoice, callback_url: str) -> dict:
        """Initializes an online checkout and returns authorization_url and reference."""
        pass

    @abstractmethod
    def verify_transaction(self, reference: str) -> dict:
        """Verifies transaction status with the provider."""
        pass

    @abstractmethod
    def process_webhook(self, request_payload: dict, signature: str) -> dict:
        """Validates webhook HMAC signature and extracts payment confirmation details."""
        pass

class PaystackGateway(BasePaymentGateway):
    """Paystack API v2 Implementation."""
    # Implements initialize_transaction, verify_transaction, process_webhook

class PaymentGatewayFactory:
    @staticmethod
    def get_gateway(provider: str = "paystack") -> BasePaymentGateway:
        if provider == "paystack":
            return PaystackGateway()
        raise ValueError(f"Unsupported payment gateway: {provider}")
```

---

# 3. Database Schema & Data Integrity

## 3.1 Relational Schema & Indexes

| Table Name | Model | Key Fields & Types | Indexes & Constraints |
| --- | --- | --- | --- |
| **`users`** | `User` | `id` (UUID7, PK), `email` (VarChar 255), `full_name`, `password`, `is_verified`, `is_active` | `UNIQUE(email)` |
| **`business_profiles`** | `BusinessProfile` | `id` (UUID7, PK), `user_id` (FK, User), `business_name`, `logo_url`, `phone`, `tax_id`, `bank_details` | `UNIQUE(user_id)` |
| **`clients`** | `Client` | `id` (UUID7, PK), `owner_id` (FK, User), `name`, `email`, `company_name`, `currency`, `status`, `is_deleted` | `INDEX(owner_id, is_deleted)`, `UNIQUE(owner_id, email) WHERE is_deleted=False` |
| **`invoices`** | `Invoice` | `id` (UUID7, PK), `owner_id` (FK, User), `client_id` (FK, Client), `number` (VarChar 20), `status`, `due_date`, `subtotal`, `tax_amount`, `discount_amount`, `total`, `is_deleted` | `UNIQUE(number)`, `INDEX(owner_id, is_deleted)`, `INDEX(owner_id, status)`, `INDEX(due_date)` |
| **`invoice_line_items`** | `LineItem` | `id` (UUID7, PK), `invoice_id` (FK, Invoice), `description`, `quantity` (Decimal 10,2), `unit_price` (Decimal 12,2), `tax_rate` (Decimal 5,2), `total` (Decimal 12,2) | `INDEX(invoice_id)` |
| **`invoice_events`** | `InvoiceEvent` | `id` (UUID7, PK), `invoice_id` (FK, Invoice), `event_type` (VarChar 20), `description`, `metadata` (JSONB), `created_at` | `INDEX(invoice_id, created_at)` |
| **`invoice_magic_links`** | `InvoiceMagicLink` | `id` (UUID7, PK), `invoice_id` (OneToOne, Invoice), `token` (VarChar 64), `expires_at`, `viewed_at`, `is_active` | `UNIQUE(token)`, `INDEX(token, is_active)` |
| **`payments`** | `Payment` | `id` (UUID7, PK), `invoice_id` (FK, Invoice), `amount` (Decimal 12,2), `currency`, `reference` (VarChar 100), `method`, `paid_at` | `UNIQUE(reference)`, `INDEX(invoice_id)` |
| **`expenses`** | `Expense` | `id` (UUID7, PK), `owner_id` (FK, User), `client_id` (FK, Client, Nullable), `amount` (Decimal 12,2), `currency`, `category`, `date`, `receipt_url`, `is_deleted` | `INDEX(owner_id, is_deleted)`, `INDEX(owner_id, date)` |

## 3.2 Data Integrity Rules
1. **Financial Decimals**: All monetary fields use `DecimalField(max_digits=12, decimal_places=2)`. Floats are strictly prohibited.
2. **Client Deletion Protection**: `Invoice.client` foreign key is configured with `on_delete=models.PROTECT`. A client cannot be deleted if referenced by any invoice.
3. **Immutable Audit Trail**: `InvoiceEvent` records are append-only. Updates and deletes are blocked.
4. **Soft Deletion**: `Client`, `Invoice`, and `Expense` implement `SoftDeleteModel`. Calling `.delete()` sets `is_deleted=True` and `deleted_at=timezone.now()`.

---

# 4. API Specification & Standards

## 4.1 URL Structure
All endpoints are rooted under `/api/v1/`:
- **Auth**: `/api/v1/auth/`
- **Clients**: `/api/v1/clients/`
- **Invoices**: `/api/v1/invoices/`
- **Expenses**: `/api/v1/expenses/`
- **Dashboard**: `/api/v1/dashboard/`
- **Payments & Webhooks**: `/api/v1/payments/`, `/api/v1/webhooks/`
- **Client Portal**: `/api/v1/portal/`

## 4.2 Standard API Envelopes

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Paginated List Response
```json
{
  "status": "success",
  "meta": {
    "page": 1,
    "page_size": 10,
    "total_pages": 3,
    "total_count": 28
  },
  "data": [ ... ]
}
```

### Error Response (Handled by `flowbill_exception_handler`)
```json
{
  "status": "error",
  "code": "VALIDATION_ERROR",
  "message": "Invalid input provided.",
  "fields": {
    "email": ["Enter a valid email address."],
    "due_date": ["Due date must be in the future."]
  }
}
```

---

## 4.3 Core API Endpoints

### Authentication & Profile (`/api/v1/auth/`)
| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register/` | Public | Register new user; dispatches verification email |
| `POST` | `/api/v1/auth/verify-email/` | Public | Verify email address using token |
| `POST` | `/api/v1/auth/login/` | Public | Authenticate user; returns access token + refresh cookie |
| `POST` | `/api/v1/auth/refresh/` | Public | Refresh expired access token |
| `POST` | `/api/v1/auth/logout/` | Bearer | Blacklist refresh token and clear cookies |
| `GET` | `/api/v1/auth/profile/` | Bearer | Retrieve user `BusinessProfile` details |
| `PUT/PATCH` | `/api/v1/auth/profile/` | Bearer | Update business branding, address, tax ID, bank details |

### Clients (`/api/v1/clients/`)
| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/clients/` | Bearer | List paginated clients (search by name/company/status) |
| `POST` | `/api/v1/clients/` | Bearer | Create new client |
| `GET` | `/api/v1/clients/{id}/` | Bearer | Client details with billing summary |
| `PUT/PATCH` | `/api/v1/clients/{id}/` | Bearer | Update client details |
| `DELETE` | `/api/v1/clients/{id}/` | Bearer | Soft-delete client |

### Invoices (`/api/v1/invoices/`)
| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/invoices/` | Bearer | List paginated invoices (filter by status/client/dates) |
| `POST` | `/api/v1/invoices/` | Bearer | Create invoice with line items |
| `GET` | `/api/v1/invoices/{id}/` | Bearer | Retrieve invoice with line items and events |
| `PUT/PATCH` | `/api/v1/invoices/{id}/` | Bearer | Update draft invoice |
| `DELETE` | `/api/v1/invoices/{id}/` | Bearer | Cancel invoice |
| `POST` | `/api/v1/invoices/{id}/send/` | Bearer | Transition to `pending`, generate magic link, send email |
| `POST` | `/api/v1/invoices/{id}/mark-paid/` | Bearer | Manually record invoice as paid |
| `POST` | `/api/v1/invoices/{id}/duplicate/` | Bearer | Duplicate invoice into a new draft |
| `GET` | `/api/v1/invoices/{id}/pdf/` | Bearer | Generate and stream invoice PDF bytes |
| `GET` | `/api/v1/invoices/{id}/events/` | Bearer | List invoice audit trail events |

### Client Portal & Payments (`/api/v1/portal/`, `/api/v1/webhooks/`)
| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/portal/{token}/` | Public | Read-only invoice data for client portal |
| `GET` | `/api/v1/portal/{token}/pdf/` | Public | Download PDF from client portal |
| `POST` | `/api/v1/portal/{token}/pay/` | Public | Initialize Paystack payment for invoice |
| `POST` | `/api/v1/webhooks/paystack/` | HMAC Header | Handle Paystack `charge.success` webhook |

### Dashboard & Analytics (`/api/v1/dashboard/`)
| Method | Endpoint | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/dashboard/stats/` | Bearer | Summary metrics (earned, pending, overdue, client count) |
| `GET` | `/api/v1/dashboard/revenue-chart/` | Bearer | Monthly revenue data for last N months (default 6) |
| `GET` | `/api/v1/dashboard/top-clients/` | Bearer | Top clients ranked by total billed revenue |
| `GET` | `/api/v1/dashboard/upcoming-due/` | Bearer | Invoices due in next N days |

---

# 5. Background Processing & Celery Architecture

Celery is configured with Redis as the message broker. Async tasks offload heavy I/O from request-response cycles:

```
┌─────────────────┐       dispatch        ┌─────────────────┐
│   DRF Service   │ ────────────────────> │  Redis Broker   │
└─────────────────┘                       └────────┬────────┘
                                                   │ task payload
                                          ┌────────▼────────┐
                                          │  Celery Worker  │
                                          └────────┬────────┘
                                                   │
                 ┌─────────────────────────────────┼─────────────────────────────────┐
                 │                                 │                                 │
        ┌────────▼────────┐               ┌────────▼────────┐               ┌────────▼────────┐
        │ Transactional   │               │ WeasyPrint PDF  │               │ Celery Beat     │
        │ Email Dispatch  │               │ Generation      │               │ Periodic Tasks  │
        └─────────────────┘               └─────────────────┘               └─────────────────┘
```

### Task Specifications

| Task Function | Module | Trigger | Retry Policy | Description |
| --- | --- | --- | --- | --- |
| `send_verification_email_task` | `apps.notifications.tasks` | User registration | 3 retries, 60s backoff | Sends account verification link |
| `send_invoice_email_task` | `apps.notifications.tasks` | Invoice sent | 3 retries, 60s backoff | Renders PDF and emails client with magic link |
| `send_payment_receipt_task` | `apps.notifications.tasks` | Payment confirmed | 3 retries, 60s backoff | Emails payment confirmation to tenant & client |
| `mark_overdue_invoices` | `apps.invoices.tasks` | Celery Beat (Daily 00:00 UTC) | 1 retry | Queries overdue pending invoices and updates status |
| `generate_recurring_invoices` | `apps.invoices.tasks` | Celery Beat (Hourly) | 2 retries | Generates new invoices from active recurring templates |

---

# 6. Repository & Codebase Structure

```
FLOWBILL PROJECT/
├── system design and Requirements/
│   ├── FlowBill_SRS_v1.0.md
│   ├── FlowBill_SD_v1.0.md
│   └── IMPLEMENTATION_STATUS.md
│
├── flowbill/                         # Django REST API Backend
│   ├── config/                       # Settings & Root URLs
│   │   ├── settings/                 # base.py, development.py, production.py, test.py
│   │   ├── celery.py                 # Celery application instance
│   │   ├── urls.py                   # Root URL routing
│   │   └── wsgi.py / asgi.py
│   │
│   ├── core/                         # Core Base Architecture
│   │   ├── models.py                 # BaseModel (UUID7, TimeStamped, SoftDelete)
│   │   ├── exceptions.py             # flowbill_exception_handler
│   │   └── pagination.py             # StandardPagination
│   │
│   ├── apps/
│   │   ├── accounts/                 # User, BusinessProfile, Auth, Registration
│   │   ├── clients/                  # Client management
│   │   ├── invoices/                 # Invoice, LineItem, InvoiceEvent, PDFService
│   │   ├── expenses/                 # Expense management
│   │   ├── dashboard/                # Analytics & metrics aggregation
│   │   ├── payments/                 # PaystackGateway, Payment processing
│   │   ├── portal/                   # Public Client Portal endpoints
│   │   └── notifications/            # Celery email tasks
│   │
│   ├── templates/invoices/           # HTML templates for WeasyPrint PDF
│   └── tests/                        # Factories & test configurations
│
└── frontend/                         # Next.js 16 + React 19 Frontend
    ├── src/
    │   ├── app/                      # App Router pages (Landing, Dashboard, Portal)
    │   └── lib/                      # Utilities & API client
    ├── package.json
    └── tailwind.config.ts
```

---

# 7. Security Architecture

1. **Row-Level Access Isolation**: All database reads and writes in the Service Layer strictly filter by `owner=request.user`. No tenant can query or alter another tenant's records.
2. **Cryptographic Magic Links**: Public portal access tokens are 32-byte URL-safe cryptographic strings (`secrets.token_urlsafe(32)`). Tokens are stored hashed or indexed with strict expiration timeouts (default 30 days).
3. **Paystack Webhook Verification**: Webhooks enforce HMAC-SHA512 verification against the `X-Paystack-Signature` header using the configured Paystack secret key before processing any event.
4. **JWT Security**: Access tokens are signed using HS256 with 15-minute validity. Refresh tokens (7 days) are transmitted in secure HttpOnly cookies with automatic rotation and token blacklisting on logout.
5. **Secure PDF Rendering**: WeasyPrint renders isolated HTML without external script execution capabilities.

---

# 8. Revision History

| Version | Date | Author | Description of Changes |
| --- | --- | --- | --- |
| 1.0.0 | May 2026 | Dev Team | Initial software design draft. |
| 1.1.0 | August 2026 | FlowBill Team | Updated software design to match implementation: row-level multi-tenancy (`owner` FK), Next.js 16 (App Router) + React 19 frontend, `BusinessProfile` model architecture, app-level service classes, Strategy Pattern for payment gateways, and unified DRF error envelope. |
