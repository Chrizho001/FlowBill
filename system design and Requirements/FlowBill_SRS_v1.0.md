# FlowBill — Software Requirements Specification (SRS)
## Freelance Invoice & Business Management Platform

| Document Type | SRS |
| --- | --- |
| Version | v1.1.0 |
| Date | August 2026 |
| Author | FlowBill Dev Team |
| Status | Approved — Aligned with Codebase & Architecture |

---

# 1. Introduction

## 1.1 Purpose
This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for **FlowBill** — a cloud-based SaaS platform designed to help freelancers and small agencies manage clients, create professional invoices, track expenses and payments, and monitor business health through a unified dashboard.

This document serves as the authoritative specification for all features, constraints, and system behaviors implemented across the FlowBill backend API and frontend application.

## 1.2 Scope
FlowBill is a full-stack web application consisting of:
1. **Django REST Framework Backend API (Django 6.x / Python 3.12+)**: Clean layered architecture (Views → Services → Models) with row-level tenant data isolation (`owner` foreign keys).
2. **Next.js 16 + React 19 Frontend**: App Router, TypeScript, and Tailwind CSS v4.
3. **PostgreSQL Database**: Relational schema with UUIDv7 primary keys, soft-deletion, and indexed tenant scoping.
4. **Celery + Redis Task Queue**: Asynchronous processing for transactional email delivery, invoice PDF generation, automated overdue tracking, and recurring billing.
5. **Payment Gateway Integration**: Paystack integration (v1) with an extensible gateway strategy for Stripe (v2).
6. **Public Client Portal**: Read-only invoice viewing, WeasyPrint PDF downloads, and online payments accessible via cryptographic magic links.
7. **Multi-Currency Support**: Invoice-level currency selection and exchange rate capture.

## 1.3 Definitions & Acronyms

| Term | Definition |
| --- | --- |
| **Tenant / User** | A registered FlowBill user (freelancer or agency) identified by `accounts.User` and owning a `BusinessProfile` |
| **Business Profile** | The business identity (branding, address, logo, tax ID, bank details) linked 1:1 to a User |
| **Client** | A business or individual entity that a tenant bills for services rendered |
| **Invoice** | A formal payment request document issued from a tenant to a client |
| **Line Item** | An individual product or service entry on an invoice with quantity, unit price, and tax rate |
| **Magic Link** | A time-limited, cryptographic tokenized URL granting a client read-only portal access |
| **DRF** | Django REST Framework |
| **JWT** | JSON Web Token used for stateless authentication |
| **TDD** | Test-Driven Development (failing test written prior to implementation) |
| **UUIDv7** | Time-ordered, cryptographically random, 128-bit unique identifier |

## 1.4 References
- Django REST Framework Documentation — https://www.django-rest-framework.org
- Paystack API Documentation — https://paystack.com/docs/api
- Next.js Documentation — https://nextjs.org/docs
- Celery Documentation — https://docs.celeryq.dev
- WeasyPrint Documentation — https://doc.courtbouillon.org/weasyprint/

---

# 2. Overall Description

## 2.1 Product Perspective
FlowBill is a standalone SaaS platform designed with a clean, decoupled full-stack architecture. The backend exposes a versioned RESTful API (`/api/v1/`), while the frontend is built using Next.js 16 (App Router) and React 19.

Data multi-tenancy is implemented using **row-level ownership scoping** (`owner_id` foreign key referencing `accounts.User`). Every query in the service layer is explicitly scoped to the authenticated user, ensuring complete data isolation without the operational overhead of dynamic database schema provisioning.

## 2.2 Target Users

| User Type | Description | Primary Use Cases |
| --- | --- | --- |
| **Freelancer** | Solo professional (developer, designer, consultant) | Create invoices, log expenses, track payments, manage 1–50 clients |
| **Small Agency** | Small team billing multiple clients | Multi-client invoicing, revenue and expense analytics, recurring billing |
| **Client (End-User)** | Client receiving invoices from a tenant | View invoices via magic links, download PDFs, pay online via Paystack |
| **Admin** | FlowBill platform administrator | System monitoring, user verification status, operational health |

## 2.3 Assumptions & Dependencies
1. Users have access to modern evergreen web browsers (Chrome 110+, Firefox 110+, Safari 16+, Edge).
2. Transactional email delivery utilizes Mailgun or SMTP provider via standard Django mail backends.
3. Online payments in v1 depend on Paystack API v2 availability.
4. Redis is used as the Celery message broker and caching layer.
5. All invoice totals, line item calculations, and state transitions are computed and validated exclusively on the server.

## 2.4 Constraints
1. **Stateless API**: Backend remains stateless using JWT bearer tokens and HttpOnly refresh cookies.
2. **API Versioning**: All endpoints are strictly versioned under `/api/v1/`.
3. **Data Integrity**: Soft deletion on critical entities (`Client`, `Invoice`, `Expense`); hard deletes are prohibited for auditable billing entities.
4. **Isolated Service Layer**: Business logic lives in domain service classes (`apps.<module>.services`), never inside DRF views or serializers.

---

# 3. Functional Requirements

## 3.1 Authentication, Users & Business Profiles

### 3.1.1 Registration & Authentication

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **AUTH-001** | System shall allow new users to register with email, password, and full name. | Critical | Unit + Integration |
| **AUTH-002** | System shall generate a 24-hour cryptographic token stored in cache and send an email verification link upon registration. | Critical | Integration |
| **AUTH-003** | System shall verify email addresses upon submitting a valid verification token. | Critical | Unit + Integration |
| **AUTH-004** | System shall enforce strong passwords (minimum 8 characters, common password validation). | High | Unit |
| **AUTH-005** | System shall support OAuth2 social authentication via Google (`django-allauth`). | Medium | Integration |
| **AUTH-006** | System shall support OAuth2 social authentication via GitHub (`django-allauth`). | Medium | Integration |
| **AUTH-007** | System shall authenticate users via JWT access tokens (15-minute lifetime, HS256 signature). | Critical | Unit + Integration |
| **AUTH-008** | System shall issue 7-day refresh tokens with rotation and blacklist support on logout. | Critical | Unit + Integration |
| **AUTH-009** | System shall support password reset via email link with a 1-hour expiration token. | High | Integration |
| **AUTH-010** | System shall strictly isolate and scope all tenant queries to the authenticated user (`owner=request.user`). | Critical | Integration |

### 3.1.2 Business Profile Management

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **PROF-001** | System shall maintain a 1:1 `BusinessProfile` for each user containing business name, phone, address, city, state, country, tax ID, and logo URL. | Critical | Unit + Integration |
| **PROF-002** | System shall allow users to retrieve and update their `BusinessProfile` via `GET/PUT /api/v1/auth/profile/`. | Critical | Integration |
| **PROF-003** | System shall store default payment instructions and bank details (bank name, account name, account number) on the `BusinessProfile` for rendering onto invoices. | High | Unit + Integration |
| **PROF-004** | System shall allow users to configure their default currency (e.g. USD, NGN, GBP, EUR) and default payment terms in their profile. | Medium | Unit |

---

## 3.2 Client Management

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **CLT-001** | System shall allow users to create clients with name, email, phone, company name, address, city, state, country, and currency. | Critical | Unit + Integration |
| **CLT-002** | System shall enforce email uniqueness per owner for active clients (`unique_active_client_email_per_owner`). | High | Unit |
| **CLT-003** | System shall allow users to list, search, filter, update, and soft-delete clients. | Critical | Integration |
| **CLT-004** | System shall prevent deletion of clients linked to invoices using `on_delete=models.PROTECT`. | Critical | Unit + Integration |
| **CLT-005** | System shall support client status toggling between `active` and `inactive`. | Medium | Unit |
| **CLT-006** | System shall provide client detail endpoints including total billed and outstanding invoice summary. | High | Integration |

---

## 3.3 Invoice Management

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **INV-001** | System shall allow users to create invoices with multiple line items, discount amount, notes, issue date, due date, and payment terms. | Critical | Unit + Integration |
| **INV-002** | System shall auto-generate sequential, immutable invoice numbers in the format `INV-YYYY-XXXX`. | Critical | Unit |
| **INV-003** | System shall support invoice lifecycle states: `draft`, `pending`, `paid`, `overdue`, and `cancelled`. | Critical | Unit |
| **INV-004** | System shall only permit updating or deleting invoices in `draft` status. | Critical | Unit + Integration |
| **INV-005** | System shall calculate line item totals, subtotal, tax amount, and final total exclusively server-side. | Critical | Unit |
| **INV-006** | System shall record an immutable, append-only audit trail in `InvoiceEvent` for all status changes and interactions. | High | Integration |
| **INV-007** | System shall allow users to duplicate an existing invoice into a new `draft` invoice. | Medium | Integration |
| **INV-008** | System shall transition an invoice from `draft` to `pending` when sent to the client. | Critical | Integration |
| **INV-009** | System shall support automated overdue transitions via a scheduled Celery Beat task (`mark_overdue_invoices`). | High | Celery + Unit |
| **INV-010** | System shall generate a secure, 32-byte cryptographic magic link token for each sent invoice for client portal access. | Critical | Unit + Integration |

---

## 3.4 PDF Generation & Delivery

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **PDF-001** | System shall generate high-fidelity invoice PDFs using WeasyPrint from HTML/CSS templates. | Critical | Integration |
| **PDF-002** | Invoice PDF shall display tenant business branding (business name, logo, address, contact, tax ID) from `BusinessProfile`. | Critical | Integration |
| **PDF-003** | Invoice PDF shall display client details, invoice number, issue/due dates, payment terms, and status badge. | Critical | Integration |
| **PDF-004** | Invoice PDF shall itemize line items with quantity, unit price, tax rate, and calculate subtotal, taxes, discounts, and total. | Critical | Integration |
| **PDF-005** | Invoice PDF shall include banking details and payment instructions configured on the tenant's profile. | High | Integration |
| **PDF-006** | System shall provide a direct PDF download endpoint (`GET /api/v1/invoices/{id}/pdf/`). | Critical | Integration |
| **PDF-007** | System shall automatically attach the generated PDF to invoice dispatch emails. | High | Integration + Celery |

---

## 3.5 Payment Tracking & Gateways

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **PAY-001** | System shall allow users to manually record payments against `pending` or `overdue` invoices, transitioning status to `paid`. | Critical | Unit + Integration |
| **PAY-002** | System shall record payment date, amount, currency, method, and transaction reference. | High | Unit |
| **PAY-003** | System shall integrate Paystack API (v1) to initialize checkout transactions from the client portal. | Critical | Integration + E2E |
| **PAY-004** | System shall process Paystack webhook events (`charge.success`) with HMAC-SHA512 signature verification. | Critical | Integration |
| **PAY-005** | System shall implement payment gateways using a `BasePaymentGateway` abstraction to facilitate adding Stripe in v2. | High | Unit |
| **PAY-006** | System shall trigger payment confirmation emails to both client and tenant upon successful payment. | High | Celery + Integration |
| **PAY-007** | System shall store exchange rates at invoice creation time for multi-currency tracking. | Medium | Unit |

---

## 3.6 Public Client Portal (Magic Link)

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **PRT-001** | System shall provide an unauthenticated public portal accessible via unique magic link tokens (`/portal/{token}`). | Critical | Integration + E2E |
| **PRT-002** | Magic links shall be validated against expiration dates and active status without requiring client authentication. | Critical | Unit + Integration |
| **PRT-003** | Client portal shall render full invoice details, line items, and issuer business profile in a clean responsive UI. | Critical | Integration + E2E |
| **PRT-004** | Client portal shall allow clients to download the official PDF directly. | Critical | Integration |
| **PRT-005** | Client portal shall allow clients to click "Pay Now" to initialize Paystack checkout. | Critical | Integration + E2E |
| **PRT-006** | System shall log a `viewed` event in `InvoiceEvent` upon the client's first visit to the portal. | High | Integration |

---

## 3.7 Expense Tracking

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **EXP-001** | System shall allow users to log business expenses with date, amount, currency, category, and description. | High | Unit + Integration |
| **EXP-002** | System shall support standard expense categories: `software`, `equipment`, `marketing`, `travel`, `education`, `internet`, and `other`. | High | Unit |
| **EXP-003** | System shall allow expenses to be optionally linked to a specific `Client` for project cost tracking. | Medium | Unit + Integration |
| **EXP-004** | System shall support attaching receipt URLs or file uploads to expense records. | Medium | Integration |
| **EXP-005** | System shall provide filterable, paginated expense list endpoints (`GET /api/v1/expenses/`). | High | Integration |

---

## 3.8 Recurring Invoices

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **REC-001** | System shall allow users to configure recurring invoice schedules based on existing invoice templates. | High | Unit + Integration |
| **REC-002** | System shall support recurrence intervals: `weekly`, `monthly`, `quarterly`, and `annually`. | High | Unit |
| **REC-003** | System shall automatically generate draft or pending invoices on schedule via Celery Beat tasks. | High | Celery + Integration |
| **REC-004** | System shall allow users to pause, resume, or cancel active recurring schedules. | High | Integration |
| **REC-005** | System shall track the execution history and count of generated invoices for each recurring template. | Medium | Unit |

---

## 3.9 Dashboard & Financial Analytics

| ID | Requirement | Priority | TDD Test Type |
| --- | --- | --- | --- |
| **DSH-001** | Dashboard shall provide aggregated summary metrics: Total Earned, Total Pending, Total Overdue, Active Clients, Pending Count, Overdue Count, and Invoices Created this Month. | Critical | Integration |
| **DSH-002** | Dashboard shall provide a monthly revenue chart endpoint for the last N months (default 6, max 12) with continuous zero-filled data. | High | Integration |
| **DSH-003** | Dashboard shall list top clients ranked by total billed revenue with percentage contributions. | High | Integration |
| **DSH-004** | Dashboard shall list upcoming invoices due within N days (default 7 days), ordered by urgency. | High | Integration |
| **DSH-005** | System shall support exporting invoice data to CSV format. | Medium | Integration |

---

# 4. Non-Functional Requirements

## 4.1 Performance & Scalability
- **API Response Time**: List and detail queries shall respond in `< 200ms` at p95 under standard load.
- **PDF Generation**: WeasyPrint generation shall complete in `< 2.5s` for standard invoices.
- **Data Scoping Indexes**: Composite database indexes on `(owner_id, is_deleted, created_at)` and `(owner_id, status)` ensure linear scaling as tenant volume grows.
- **Asynchronous Processing**: Heavy I/O (email delivery, PDF generation, webhook processing) is offloaded to Celery workers.

## 4.2 Security
- **Data Isolation**: Strict row-level scoping (`owner=request.user`) in service layer methods guarantees zero data leakage across tenants.
- **Authentication**: JWT access tokens (15m expiration) paired with HttpOnly refresh cookies (7-day expiration) with automatic token rotation and blacklisting.
- **Password Security**: Django PBKDF2 with SHA-256 (or bcrypt), minimum 8 characters with strength validation.
- **Webhook Integrity**: Paystack webhook payloads verified using HMAC-SHA512 signatures (`X-Paystack-Signature`).
- **Input Validation & Sanitization**: All inputs validated via DRF serializers; ORM parameterized queries prevent SQL injection.
- **Error Shielding**: Database errors and stack traces are suppressed in production; standardized error envelopes are returned.

## 4.3 Reliability & Error Handling
- **Unified Response Envelope**:
  - Success: `{"status": "success", "data": <payload>, "message": "<optional string>"}`
  - Paginated List: `{"status": "success", "meta": {"page": 1, "page_size": 10, "total_pages": 4, "total_count": 34}, "data": [...]}`
  - Error: `{"status": "error", "code": "VALIDATION_ERROR", "message": "Human readable summary", "fields": {"field_name": ["Detail"]}}`
- **HTTP Status Codes**:
  - `200 OK` / `201 Created` / `204 No Content` for successes.
  - `400 Bad Request` for validation and business logic constraint failures.
  - `401 Unauthorized` / `403 Forbidden` for auth and permission failures.
  - `404 Not Found` for missing resources.
  - `500 Internal Server Error` with JSON error mask for unhandled exceptions.

## 4.4 Quality & Testing Standards
- **Test-Driven Development**: All endpoints, services, and models are built against comprehensive test suites.
- **Coverage Requirement**: Test suite must maintain `≥ 80%` test coverage enforced in `pytest.ini` (`--cov-fail-under=80`).
- **Structured Logging**: `structlog` used for machine-readable JSON logging across all modules.

---

# 5. Technology Stack Specification

| Layer | Technology | Version | Purpose & Rationale |
| --- | --- | --- | --- |
| **Backend Framework** | Django + DRF | 6.0+ / 3.17+ | Robust ORM, built-in admin, auth, and ecosystem maturity |
| **Language** | Python | 3.12+ | Type hints, performance, and package ecosystem |
| **Database** | PostgreSQL | 16+ | ACID compliance, JSONB support, relational indexing |
| **Task Queue & Broker** | Celery + Redis | 5.6+ / 8.0+ | Reliable async background jobs and scheduled Beat tasks |
| **Authentication** | SimpleJWT + allauth | 5.5+ / 65.18+ | JWT token rotation, blacklist, and Google/GitHub OAuth |
| **PDF Generation** | WeasyPrint | 69.0+ | Pixel-perfect HTML/CSS to PDF rendering |
| **Payment Gateway** | Paystack API | v2 | Comprehensive African payment gateway with cards, bank transfers, USSD |
| **API Documentation** | drf-spectacular | 0.29+ | OpenAPI 3.0 auto-generation with Swagger UI |
| **Logging** | structlog | 25.5+ | Contextual, structured JSON application logging |
| **Frontend Framework** | Next.js (App Router) | 16.3+ | Fast SSR/SSG, React Server Components, clean routing |
| **UI Library** | React | 19.2+ | Modern declarative UI component model |
| **Styling** | Tailwind CSS | 4.0+ | Modern utility-first design system with rich dark mode |
| **Icons & Animation** | Lucide React + Framer Motion | Latest | Consistent icon set and smooth micro-animations |
| **Package Managers** | `uv` (Backend) / `npm` (Frontend) | Latest | Blazing-fast Python virtual environment and JS package management |

---

# 6. User Journeys & Core Flows

## Flow 1: User Registration & Onboarding
1. User registers with email, password, and full name (`POST /api/v1/auth/register/`).
2. System creates unverified `User` and generates a 24-hour verification token in Redis cache.
3. System sends verification email with magic link (`/verify-email?token=...`).
4. User clicks link (`POST /api/v1/auth/verify-email/`); account is marked `is_verified=True`.
5. User logs in (`POST /api/v1/auth/login/`), receiving JWT access & refresh tokens.
6. User sets up `BusinessProfile` (business name, logo, address, bank details) via `PUT /api/v1/auth/profile/`.

## Flow 2: Creating & Dispatching an Invoice
1. User creates or selects a `Client` (`POST /api/v1/clients/`).
2. User submits invoice payload with line items, due date, and payment terms (`POST /api/v1/invoices/`).
3. `InvoiceService` validates client ownership, calculates line totals, taxes, and subtotal atomically, generating number `INV-YYYY-XXXX`.
4. User reviews draft invoice and triggers send (`POST /api/v1/invoices/{id}/send/`).
5. Status transitions from `draft` to `pending`; system generates 32-byte magic link and queues email with attached WeasyPrint PDF.
6. System logs `sent` event in `InvoiceEvent`.

## Flow 3: Client Portal View & Payment
1. Client receives email and opens link: `https://app.flowbill.com/portal/{magic_token}`.
2. Portal queries `GET /api/v1/portal/{token}/` (unauthenticated); system validates token and logs `viewed` event.
3. Portal displays invoice details, issuer business branding, and PDF download button.
4. Client clicks "Pay Now" (`POST /api/v1/portal/{token}/pay/`); system initializes Paystack transaction and returns authorization URL.
5. Client completes checkout; Paystack sends `charge.success` webhook to `POST /api/v1/webhooks/paystack/`.
6. System verifies HMAC signature, marks invoice as `paid`, logs audit event, and sends confirmation emails to both parties.

---

# 7. Revision History

| Version | Date | Author | Description of Changes |
| --- | --- | --- | --- |
| 1.0.0 | May 2026 | Dev Team | Initial draft specification. |
| 1.1.0 | August 2026 | FlowBill Team | Realigned specification with codebase: formalized row-level multi-tenancy (`owner` FK), Next.js 16 + React 19 frontend stack, `BusinessProfile` model, unified response envelope, and Paystack v1 strategy. |
