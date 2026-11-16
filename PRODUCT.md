# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS v4 frontend (`frontend/`), talking to the
Django 6 / DRF API in `flowbill/` under `/api/v1/`. Animation: GSAP + ScrollTrigger via `@gsap/react`.
Icons: lucide-react. Package manager: npm.

## Users
- **Freelancers** (developers, designers, consultants) billing 1–50 clients, often in Nigeria and billing
  international clients. Job: send a professional invoice and get paid without chasing.
- **Small agencies** billing many clients, needing recurring billing and revenue/expense visibility.
- **Clients** (the people paying): open a magic link, view and download the invoice, pay online. No account.

## Product Purpose
FlowBill takes a freelancer from "work done" to "money received": clients, invoices, PDFs, expenses,
payments and a dashboard of business health, all in one app. Success means invoices get paid faster
with less admin.

## Positioning
The invoice *is* the payment page: every sent invoice carries a secure magic link where the client pays
by card, bank transfer or USSD (Paystack), with crypto payments planned, in NGN, USD, GBP or EUR, with no login.

## Capabilities and Constraints
- Built: accounts (JWT, email verification, password reset, business profile), clients, invoices
  (draft → pending → paid / overdue / cancelled, `INV-YYYY-XXXX`, totals worked out on the server, append-only audit log),
  WeasyPrint PDFs, expenses, dashboard analytics.
- Planned: magic-link client portal, Paystack payments, automatic overdue marking, recurring invoices,
  CSV export, **crypto payments for clients** (not yet in the SRS; must be specced before it is built).
- The product is pre-launch: the landing page's goal is waitlist sign-ups.

## Brand Commitments
- Name: FlowBill.
- Binding visual constraints from the owner: navy + coral palette (after
  `Design_Inspiration/Flowbill_landingpage_inspo.jpg`), Space Grotesk + Roboto, very generous spacing.

## Evidence on Hand
- No real customers, testimonials, usage numbers or logos yet. **Do not invent them.** Testimonials ship
  as clearly marked placeholder slots; pricing ships as marked drafts.
- Real product facts that can be shown: invoice number format, status lifecycle, supported currencies,
  payment methods, PDF output, dashboard metrics (Total Earned / Pending / Overdue, 6-month revenue).

## Product Principles
1. Getting paid is the product; every surface shortens the path to "Paid".
2. Show the real thing: real invoice, portal and dashboard UI, never generic mock charts.
3. Honest by default: no invented proof; drafts and placeholders are labelled in code.
4. Local and global at once: naira and dollars side by side, local payment methods first-class.

## Accessibility & Inclusion
WCAG 2.2 AA. Full keyboard support, visible focus, `prefers-reduced-motion` respected, works down to 320 px.
