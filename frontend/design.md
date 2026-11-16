# FlowBill Landing Page — Design Spec

> Status: **DRAFT for review** · 2026-11-16 · Owner: FlowBill
> Product truth: [`../PRODUCT.md`](../PRODUCT.md) · Mood reference: `../Design_Inspiration/Flowbill_landingpage_inspo.jpg`
> Skills applied: design-taste-frontend (taste), impeccable, gsap-core / gsap-timeline / gsap-scrolltrigger / gsap-react

This spec is the source of truth for building the landing page. Build from it section by section.
If the build needs to differ, update this file first.

---

## 0. Direction contract

Paste this as the first child of `<body>` in `app/layout.tsx`. It goes in as an HTML comment, kept under 150 words.

```
THESIS     The invoice is the payment page. Show money moving from "Sent" to "Paid" on the first screen.
WORLD      Navy ledger at night, with coral as the moment of payment. Space Grotesk numerals, Inter prose, lots of air.
FIRST VIEW Diagonal navy field. Headline left. On the right, a live invoice → portal → "Paid" stack that plays once on load.
SIGNATURE  Pinned "Create → Send → Paid" scroll story: one invoice card changes state as you scroll.
RISK       Too close to the inspiration. Keep it ours with real FlowBill UI, NGN/USD data and the payment-flow motion.
```

### Kind and mode
- **taste kind:** `software` (SaaS / fintech). `<html data-type="software">`, `<meta name="page-type" content="software">`, `<meta name="site-kind" content="software">`.
- **impeccable mode:** **Persuade**. The visitor should leave believing "my clients will pay me faster", then join the waitlist.
- **Primary action:** **Join the waitlist** (email capture). One primary action per screen, at most twice.

### Where this spec overrides the skills (by owner's decision)
| Skill default | This page | Why |
|---|---|---|
| taste: no fade-in on scroll / card reveals | GSAP scroll and card reveals **are used** (rules in §6) | Owner explicitly asked for scroll, card-reveal and hover animation |
| impeccable: Space Grotesk is an overused default | **Space Grotesk + Montserrat** | Owner chose these fonts |
| taste: no tilt | Hero visual is **rotated −8°**, as in the inspiration | Owner asked to mirror the inspiration |
| taste: no carousels | Testimonials use a **static grid**, not a carousel | No conflict with the owner's wishes; static is better for a11y |
| taste/impeccable: no invented proof | Testimonials are **placeholder slots**; pricing is a **draft** | Pre-launch, no real data (see `PRODUCT.md` → Evidence) |

---

## 1. Brand tokens

### 1.1 Colour (strategy: *Committed*, navy carries ~40% of the page, coral is the action colour)

| Token | Hex | Use |
|---|---|---|
| `navy-950` | `#0B1230` | Deepest ground: footer, final CTA band |
| `navy-900` | `#141C42` | Hero field, pinned "how it works" section |
| `navy-800` | `#1E2A5A` | Cards on navy, nav on scroll |
| `navy-700` | `#2C3A72` | Borders and dividers on navy |
| `navy-300` | `#A9B3D9` | Secondary text on navy (≥ 4.5:1 on `navy-900`) |
| `coral-600` | `#D93A43` | **Primary button fill** (white text ≥ 4.5:1) |
| `coral-500` | `#F2545B` | Brand coral: highlights, decorative blobs, active states, large display accents only |
| `coral-400` | `#F7777D` | Hover glow, chart lines on navy |
| `coral-100` | `#FFE4E5` | Tinted chips/badges on light ground |
| `surface` | `#F5F7FC` | Main light ground (the grey of the inspiration's lower half) |
| `white` | `#FFFFFF` | Cards on light ground |
| `ink` | `#141C42` | Headings on light (same as navy-900) |
| `ink-muted` | `#5A6388` | Body text on light (≥ 4.5:1 on `surface`) |
| `line` | `#E3E7F2` | Hairlines, card borders on light |
| `teal-400` | `#2DD4BF` | **Crypto / "new" accent only.** Used sparingly (the inspiration's cyan blob) |

**Invoice status colours.** These match the product and are always shown with a label or icon, never colour alone.
`paid` `#15803D` on `#DCFCE7` · `pending` `#B45309` on `#FEF3C7` · `overdue` `#BE123C` on `#FFE4E6` · `draft` `#475569` on `#F1F5F9` · `cancelled` `#64748B` on `#F1F5F9`.
Overdue uses rose-700, not brand coral, so "error" never reads as "brand".

**Bans:** no violet/lavender, no gradient text, no neon glow edges. One soft coral radial glow behind the hero visual is allowed.

### 1.2 Typography
- **Display:** Space Grotesk (500, 700) via `next/font/google`, variable `--font-display`. Used for headings, prices, invoice amounts and the logo wordmark.
- **Body/UI:** Montserrat (variable) via `next/font/google`, variable `--font-sans`. (Owner choice: Roboto → Inter → Montserrat, 2026-11-16.)
- Money always uses `font-variant-numeric: tabular-nums`.

| Role | Desktop (≥1280) | Mobile (390) | Weight / tracking / leading |
|---|---|---|---|
| Hero h1 | 80px (`clamp(2.75rem, 5.5vw + 0.5rem, 5rem)`) | 44px | SG 700, −0.035em, 1.02 |
| Section h2 | 56px (`clamp(2.25rem, 3.5vw + 0.5rem, 3.5rem)`) | 36px | SG 700, −0.03em, 1.08 |
| h3 / card title | 24px | 20px | SG 500, −0.01em, 1.25 |
| Eyebrow | 13px | 12px | Montserrat 500, +0.14em, uppercase, coral-500 |
| Lead | 20px | 18px | Montserrat 400, 1.6, max 56ch |
| Body | 17px | 16px | Montserrat 400, 1.65, max 65ch |
| Small / meta | 14px | 14px | Montserrat 400/500 |

Headings are sentence case. Make the space above a heading bigger than the space below it.

### 1.3 Space (very generous, on a 4px base)
- Section vertical padding: **`py-24` (96px) mobile → `md:py-32` (128px) → `lg:py-44` (176px)**. The hero and the pinned story set their own height.
- Heading block → content: 64px desktop / 48px mobile. Eyebrow → h2: 20px. h2 → lead: 24px.
- Card padding: 40px desktop / 28px mobile. Grid gaps: 32px (`gap-8`) desktop, 24px mobile.
- Rule: if a section feels finished, add 16px more air before adding any element.

### 1.4 Container (Tailwind v4 custom `container` utility)
Every section's content sits in one `.container`. Left and right edges are equal on every screen.

```css
@utility container {
  margin-inline: auto;
  width: 100%;
  padding-inline: 1.25rem;            /* 20px @ 320–639 */
  @variant sm  { max-width: 640px;  padding-inline: 1.5rem; }
  @variant md  { max-width: 768px;  padding-inline: 2rem; }
  @variant lg  { max-width: 1024px; padding-inline: 2.5rem; }
  @variant xl  { max-width: 1280px; }
  @variant 2xl { max-width: 1400px; }
}
```
Full-bleed grounds (the navy diagonal, bands) live on the `<section>`. Content always goes inside `.container`.

### 1.5 Shape, depth, texture
- Radius scale: `8px` (chips, inputs) · `14px` (buttons) · `20px` (cards) · `28px` (app frame). One scale only.
- Shadows on light: `0 1px 2px rgb(20 28 66 / .06), 0 12px 32px -12px rgb(20 28 66 / .18)`. On hover: `0 24px 48px -16px rgb(20 28 66 / .28)`.
- Cards on navy: `navy-800` fill, 1px `navy-700` border, no shadow.
- Decorative shapes: two or three soft coral circles (the inspiration's blobs), built from CSS radial gradients, `aria-hidden`. They drift slowly only when motion is allowed.

### 1.6 Tailwind v4 `@theme` (in `globals.css`)
```css
@theme inline {
  --font-display: var(--font-space-grotesk), ui-sans-serif, system-ui;
  --font-sans: var(--font-roboto), ui-sans-serif, system-ui;
  --color-navy-950:#0B1230; --color-navy-900:#141C42; --color-navy-800:#1E2A5A;
  --color-navy-700:#2C3A72; --color-navy-300:#A9B3D9;
  --color-coral-600:#D93A43; --color-coral-500:#F2545B; --color-coral-400:#F7777D; --color-coral-100:#FFE4E5;
  --color-surface:#F5F7FC; --color-ink:#141C42; --color-ink-muted:#5A6388; --color-line:#E3E7F2;
  --color-teal-400:#2DD4BF;
  --radius-chip:8px; --radius-btn:14px; --radius-card:20px; --radius-frame:28px;
  --ease-out-expo: cubic-bezier(.16,1,.3,1);
}
```

---

## 2. Components (one system)

- **Buttons.** There are two kinds. **No icons inside CTA buttons** (owner, 2026-11-16).
  - *Primary:* `coral-600` fill, white Montserrat 500 at 16px, 52px tall (56px in the hero), radius 14px, with an arrow icon on the right.
  - *Secondary:* transparent with a 1.5px border. The border is `navy-700` on navy and `ink` at 15% on light.
  - Every button has a verb and an object ("Join the waitlist", "See how it works").
  - Hover: lifts 2px and the arrow slides 4px to the right. Active: scales to 0.97. Focus: 3px `coral-400` ring with a 2px offset.
- **Links:** ink, with an underline that draws from left to right on hover (`scaleX` 0→1, 250ms).
- **Card:** white with a 1px `line` border, radius 20px, 40px padding. If linked, it lifts on hover (`y: -4`, larger shadow, 300ms ease-out-expo). There is one card family across the page.
- **Status badge:** pill, 12px Montserrat 500 uppercase, uses the status palette above with a dot icon.
- **App frame:** a FlowBill window. Radius 28px, a 40px top bar with three muted dots, the FlowBill wordmark and a search field. It frames the product UI as live HTML, never as a screenshot.
- **Waitlist form:** an email input and a Primary button. They sit side by side at ≥640px and stack below that. See §5.
- **Icons:** lucide-react at 1.75 stroke for UI. Payment-method marks (Visa, Mastercard, Paystack, USDT/USDC) use their real logos as SVG files in `public/brands/` and keep their own colours. Never redraw a logo.

---

## 3. Page structure

Each section is `main > section#id`, has one `.container`, and puts its h2 first. Target heights at 1440×900 come from the taste skill: the hero fills exactly one screen, and other sections are 1–2 screens.

| # | id | Ground | Idea (one per section) | Height |
|---|---|---|---|---|
| — | header | transparent → navy-900/80 blur | Nav + waitlist button | 80px |
| 1 | `hero` | navy-900 diagonal over surface | Invoice → paid, on screen | 1 screen |
| 2 | `rails` | surface | Facts strip: currencies + payment methods | ~0.4 screen (joins hero bottom) |
| 3 | `how-it-works` | navy-900 (pinned) | Create → Send → Paid story | pinned, 3 steps |
| 4 | `features` | surface | Everything around the invoice (bento) | 1–2 screens |
| 5 | `insights` | white | Dashboard: know where your money is | 1 screen |
| 6 | `portal` | surface | What your client sees + crypto coming soon | 1–2 screens |
| 7 | `voices` | white | Testimonial slots (placeholder) | 1 screen |
| 8 | `pricing` | surface | Plans, NGN/USD, monthly/yearly | 1–2 screens |
| 9 | `faq` | white | Objections answered | 1 screen |
| 10 | `join` | navy-950 | Final waitlist CTA | 1 screen |
| — | footer | navy-950 | Links, legal, credit line | auto |

Every customer name, number and amount below is **demo data**. Keep it all in `src/content/landing.ts`, with comments marking it `// demo`.

### 3.0 Header (mirrors the inspiration)
- Left: FlowBill wordmark, then the nav links **directly beside it** (56px gap, 36px between links). Links are not centred.
- Right: **only** "Log in" (text button) and "Sign up" (white button, navy text). No waitlist button in the navbar.
  - Pre-launch, Sign up opens the waitlist modal. Log in opens the same modal with "We're not open yet" copy.
- Starts transparent over the navy and becomes `navy-900/85` with blur after 24px of scroll.
- Below 1024: logo + menu button. The full-screen menu has the links, then Sign up and Log in buttons.

### 3.1 Hero (`#hero`), mirrors the inspiration
- Navy field (`#27325E`) with the diagonal bottom edge. No coral blob.
- **Moons:** eight small translucent grey spheres drift slowly in the navy (GSAP, 5–9s yoyo). The large ones are hidden on mobile.
- **Copy, left column.** Each block is at most two lines on desktop:
  - H1, two lines that never wrap: "Get paid for every / invoice you send."
  - Lead, two lines: "Invoice clients and get paid by card, bank transfer or USSD, all from one secure link."
  - One standalone coral "Get started" button that opens the waitlist modal.
  - No currency chips and no inline form.
- **Visual, right column.** A live-HTML desktop FlowBill dashboard, with the whole group rotated −8° and bleeding off the right edge:
  - **Sidebar:** icons with the coral logo dot.
  - **Top cards:** a coral "Total earned" card and a navy "Pending" card.
  - **Client list:** four rows, each with invoice count and amount billed.
  - **Two floating cards:** a client payment card with a sparkline, and a "New invoice" card with line-item sliders and a Send button.
- **Load:** the headline lines rise, the dashboard slides in, the rows stagger, the sliders fill and the numbers count up.
- **After load:** the moons and cards drift. A pause button controls this.

### 3.2 Payment rails strip
- A muted line, then **five large logo tiles** using the owner's files from `/Logos`: Paystack, Visa, Mastercard, OPay, USSD.
  - The files are cleaned to transparent PNGs in `public/logos/`.
  - Tiles are white cards, 112–128px tall, with the logos in full colour.
  - Hover lifts the card and scales the logo to 1.05.
- These are payment methods. They are not customer logos.

### 3.3 How it works (`#how-it-works`): horizontal iPhone carousel
- **White background.** Heading on the left; pause, previous and next round buttons on the right.
- **Coverflow carousel of four iPhone 16 slides:** Create, Send, Client pays, Get paid.
  - The active phone is centred at full size. Its neighbours sit at 80% scale, 50% opacity and a slight rotation.
  - It loops, and you can swipe or drag, use the arrows, or click a neighbour.
- **Phones:** each is an iPhone 16 drawn in code (`ui/iphone16.tsx`) with a real app screen (`app-screens.tsx`).
  - A Gemini render at `public/images/steps/step-*.png` replaces it automatically when the file exists (see `docs/image-prompts.md`).
- **Motion:**
  - The stage rises in on scroll.
  - The active screen's parts stagger in, and the "paid" check pops.
  - Slides glide with an expo ease.
- **Autoplay:** 6s per step, shown by a filling coral bar on the step tabs.
  - It pauses off-screen or with the pause button, and is off under reduced motion.
- **Below the stage:** four step tabs (desktop), or the caption plus dots (mobile).

### 3.4 Features bento (`#features`)
- h2: "Everything around the invoice." Lead: "Clients, expenses, PDFs and reminders in the same place you bill from."
- Bento grid (≥1024, 6 columns, 2 rows). Every card has a small piece of live UI, not an icon on its own:
  - **Clients** (span 2): a mini client list with avatar initials, outstanding totals and an "Active" toggle.
  - **Branded PDFs** (span 2): an invoice PDF thumbnail with your logo, bank details and a "Download PDF" chip.
  - **Expenses** (span 2): categorised expense rows (Software, Internet, Travel) with a monthly total.
  - **Recurring invoices** (span 3): a calendar strip showing "Monthly · next on Dec 1" with a `coming soon` chip.
  - **Overdue reminders** (span 3): an invoice row turns `OVERDUE` and shows a "Reminder sent" event (`coming soon`).
- Hover: the card lifts and its UI does one small loop (2.5–4s, restarts on hover). Examples: the toggle flips, an expense row adds, the calendar ticks.
- Mobile: one column, full-width cards, in the order Clients, PDFs, Expenses, Recurring, Reminders.

### 3.5 Insights (`#insights`)
- Split layout: copy in columns 1–5, a large **app frame** in columns 6–12, bleeding right.
- h2: "Know where your money is." Lead: "Earned, pending and overdue at a glance, with six months of revenue and the clients who bring it in."
- Three bullets with check icons: Total earned / pending / overdue · 6-month revenue chart · Top clients by revenue.
- The app frame shows the dashboard: 4 stat cards (Total Earned ₦3.4M, Pending ₦620K, Overdue ₦85K, Active clients 12 *(demo)*), a 6-month bar chart (coral bars, the current month highlighted), a top-clients list with % bars, and "Due this week".
- Scroll moment: when the section enters, the stat numbers count up (1.2s) and the chart bars grow from 0 with a stagger. This plays once, triggered by toggleActions, not scrubbed.

### 3.6 Client portal + crypto (`#portal`)
- h2: "What your client sees."
- The centre shows an iPhone with the magic-link payment page. Four callouts with connector lines sit on desktop.
  - The phone is `public/images/portal/portal-iphone.png` (Gemini render) when present, otherwise the coded iPhone 16 with `ClientScreen`.
  - On reveal, the phone rises and its screen parts stagger in. A gentle scroll parallax follows.
- Below it, the crypto "coming soon" card stays as before.

### 3.7 Voices (`#voices`): testimonial carousel
- Layout follows the inspiration: heading, lead and a "Get early access" button on the left, a premium card on the right.
- **Card:**
  - a 4:5 portrait, from a Gemini-generated photo or the initials fallback
  - a large Space Grotesk quote
  - name, role and city
  - a counter such as "01 / 05"
- **Depth:** two stacked, tilted cards sit behind the main card, with a coral circle and navy hexagon from the inspiration.
- **Controls:** avatar thumbnails, pause, previous (outlined) and next (filled navy).
- **Transition:** the portrait wipes in with a clip-path and zooms, the quote lines rise, and the meta fades.
- **Autoplay:** 7s, pausing on hover or focus, off-screen, or by the button.
- **Content:** five **sample** African freelancers in `landing.ts` (`isSample: true`).
  - They show in development, or in production only with `NEXT_PUBLIC_SHOW_SAMPLE_TESTIMONIALS=true`.
  - Otherwise the founder's note renders.

### 3.8 Pricing (`#pricing`): mirrors the inspiration
- **Header and toggles:** h2 "Our pricing". Below it, a coral Monthly/Yearly switch with a "Save 20%" chip, and a small NGN/USD pill.
- **Cards:** text is centred.
  - Side cards are flat on desktop and turn white on hover.
  - The **middle (Pro) card is raised in white** with a large soft shadow and a coral circle behind its top-left corner.
- **Card content:** name, blurb, divider, a circle-check feature list, the price in coral, "Per month", and a small coral "Get started" button.
- **Plans:** Starter, Pro and Agency at the same DRAFT prices. Prices roll when a toggle changes.

### 3.9 FAQ (`#faq`)
- Two columns at ≥1024: h2 + lead + a "Still curious? Email us" link on the left, and an accordion on the right.
- Uses native `<details>/<summary>`, with the height animated by GSAP on toggle and a plus icon that rotates 45°.
- Questions (draft answers in `landing.ts`):
  1. Do my clients need a FlowBill account to pay? (No, a secure link.)
  2. Which currencies and payment methods are supported? (NGN, USD, GBP, EUR; card, bank, USSD via Paystack.)
  3. When are crypto payments coming? (After launch, joining the waitlist gets you early access.)
  4. Is my data safe? (Each account's data is isolated; payments go through Paystack; we never store card details.)
  5. Can I use my own branding on invoices? (Yes: logo, address, tax ID, bank details on every PDF.)
  6. What does it cost? (Free to start; see drafts above.)

### 3.10 Final CTA (`#join`)
- navy-950 ground with one large coral circle half off the right edge (decorative, slow drift).
- h2 set large (96px desktop / 48px mobile, Space Grotesk 700): **"Stop chasing. Start getting paid."**
- One line of lead copy and a "Get early access" button that opens the waitlist modal.
- Type moment: the h2's words rise in line by line with SplitText masks on enter (§6.3).

### 3.11 Footer
- navy-950. The wordmark with one line: "Invoicing and payments for freelancers and small agencies."
- Columns: Product (Features, Pricing, FAQ) · Company (About, Contact: `hello@flowbill.example`) · Legal (Privacy, Terms).
- The bottom row has © 2026 FlowBill, a "Built in Lagos" tag (owner to confirm), and one credit line for any logos/assets.

---

## 4. Copy rules
- Speak to the freelancer as "you" and to their customer as "your client". Keep the voice plain and confident with a little warmth. No hype words: *revolutionary, seamless, effortless, supercharge, unlock, game-changer*.
- Every heading names a thing. Every button is a verb plus an object.
- Never invent user counts, ratings, logos or "trusted by". Mark future features "coming soon" every time.
- Write money as `₦450,000`, `$1,200`, with tabular numerals.

---

## 5. Waitlist modal
- Every waitlist CTA opens one shared modal: hero, navbar Sign up / Log in, pricing, crypto card and final CTA.
  - It's a native `<dialog>` with GSAP open and close, Esc and backdrop-click to close, and the body scroll locked.
- Fields:
  - **Full name** (required)
  - **Email** (required)
  - **What do you do?** (required select: Software developer, Designer, Writer or content creator, Consultant, Marketer, Agency owner, Other)
  - **"I'm interested in crypto payments"** checkbox, pre-ticked when opened from the crypto card
- States:
  - **invalid:** an inline error under each field, and focus moves to the first invalid field
  - **submitting:** a spinner on the button
  - **success:** "You're on the list."
  - **duplicate:** "You're already on the list."
  - **error:** a generic message
- Endpoint: a temporary Next route `POST /api/waitlist` that validates name, email and profession and stores to `data/waitlist.json`. Replace it with a Django endpoint before deploying.

## 6. Motion (GSAP)

### 6.1 Setup
- Packages: `gsap`, `@gsap/react`. Plugins: `ScrollTrigger`, `SplitText` (free since GSAP 3.13).
- Register the plugins once in `src/lib/gsap.ts` (client only): `gsap.registerPlugin(useGSAP, ScrollTrigger, SplitText)`.
- Each animated section is a client component that uses `useGSAP(() => {...}, { scope: ref })`. Never use unscoped selectors. Handlers created later are wrapped in `contextSafe`.
- Every rule lives inside `gsap.matchMedia()`:
  - `(prefers-reduced-motion: no-preference)` gets the full motion.
  - `(prefers-reduced-motion: reduce)` gets a static final state, with no hiding, no pinning and no scrub.
  - `(min-width: 768px)` adds pinning.
- **No hidden content without JS.** Initial states are set by `gsap.from()` / `gsap.set()` inside `useGSAP`, never in CSS. With JS off, everything is visible.
- Call `ScrollTrigger.refresh()` after fonts load (`document.fonts.ready`).
- Create ScrollTriggers in page order. No `markers` in production.

### 6.2 Motion tokens
| Token | Value |
|---|---|
| ease-out | `power3.out` (most reveals), `expo.out` (hero) |
| ease-inOut | `power2.inOut` (state swaps) |
| fast / base / slow | 0.25s / 0.6s / 0.9s |
| stagger | 0.08s (cards), 0.05s (list rows), 0.1s (headline lines) |
| reveal distance | y: 40px (cards), 24px (text) |

**Hero load timeline** (one `gsap.timeline({ defaults:{ ease:"expo.out" } })`):
`eyebrow` fade 0.4 → `h1` lines via SplitText mask, yPercent 100→0, stagger .1 (at .1) → `lead`+chips y24 fade (at .5) → `form` (at .65) → invoice card x40 fade (at .4) → portal card y60 scale .96→1 (at .55) → method chip highlight (at 1.0) → badge `PENDING→PAID` crossfade (at 1.2) → toast slide from y-16 + check draw (at 1.3) → sparkline `strokeDashoffset` (at 1.35) → coral underline under "Get paid" scaleX (at 1.4).
After it ends, start an idle float (`yoyo, repeat:-1, 6s, sine.inOut`). It pauses when the hero is off screen (ScrollTrigger `onToggle`), and there's a visible pause button in the hero corner for WCAG 2.2.2.

### 6.3 Scroll patterns
| Pattern | Where | Spec |
|---|---|---|
| **Section heading reveal** | every h2 | SplitText lines + masks, `yPercent:100→0`, 0.9s, stagger .1, `start:"top 80%"`, `once:true` |
| **Card reveal** | features, pricing, voices, rails, mobile steps | `ScrollTrigger.batch(".js-card", { start:"top 85%", once:true, onEnter: b => gsap.from(b,{y:40,autoAlpha:0,stagger:.08,duration:.7,ease:"power3.out"}) })` |
| **Pinned story** | how-it-works (≥768) | One timeline, `pin:true, scrub:.8, end:"+=250%", snap:"labels"`. Labels are `create`, `send`, `paid` |
| **Count-up** | insights stats, how-it-works totals | `gsap.to(obj,{val:target, duration:1.2, snap:{val:1}, onUpdate: format})`, triggered once |
| **Chart grow** | insights bars | `scaleY:0→1, transformOrigin:"bottom", stagger:.06` |
| **Connector draw** | portal callouts | SVG `strokeDashoffset` → 0, then the callout fades in |
| **Hero exit** | hero visual | Scrubbed `y:-60, scale:.97` as the hero leaves. This is the only parallax, and never on text |
| **Header state** | header | `toggleClass` after 24px |

Never use parallax on text, scroll-jacking, or a fade on *every* element. Body paragraphs inside a revealed block just appear with their block.

### 6.4 Hover and micro-interactions
- Primary button: `y:-2` + arrow `x:4` (0.25s) on enter, `scale:.97` on press. Done in CSS transitions, no GSAP needed.
- Linked card: `y:-4` + shadow upgrade (0.3s ease-out-expo). Any UI inside the card plays its loop once on hover.
- Rails logos: grayscale → colour, 0.3s.
- Pricing card: border becomes coral-500 at 40%, and the CTA arrow nudges.
- Nav links: underline draws from the left.
- **Magnetic hero CTA** (pointer devices only, `(hover:hover)`): the button follows the cursor up to 6px using `gsap.quickTo`.
- No tilt, no cursor trails, no blinking.

---

## 7. Responsive

| Width | Behaviour |
|---|---|
| ≥1536 | 1400px container. The hero visual may bleed to the viewport edge |
| 1280 | Design reference width |
| 1024 | 12-col grid kept. Nav links visible. Bento 6-col |
| 768–1023 | Hero stacks (copy then visual). Bento 2-col. Pin still on. Pricing 3-col compact or stacked if narrower than 900 |
| 390 | One column. 20px gutters. Full-width buttons. Hero visual scaled to width. No pin. Menu is a full-screen sheet |
| 320 | Nothing overflows sideways. Tap targets ≥ 44px with ≥ 8px apart |

- Test at 1440×900, 1024×768, 820×1180, 768×1024, 390×844 and 320×568.
- Mockup text inside the product UI can shrink to 12px, but page text never goes below 14px.
- Use `svh` units for the hero (`min-h-[100svh]`) to avoid mobile toolbar jumps.

---

## 8. Accessibility, performance, SEO
- WCAG 2.2 AA contrast for every text/ground pair listed in §1.1 (check coral-600 buttons and navy-300 text).
- One `h1`. Headings go down one level at a time. There's a skip link to `#main`, and landmarks: `header`, `main`, `footer`.
- Decorative blobs and mockups are `aria-hidden="true"`. Each mockup gets one `sr-only` sentence describing what it shows.
- Focus is always visible (coral-400 ring), and the sticky header never covers the focused element (`scroll-margin-top: 96px`).
- The accordion uses native `<details>`. Toggles use `role="radiogroup"` / `aria-pressed`.
- Performance: LCP is the hero h1 (text). Fonts load through `next/font` with `display: swap`. GSAP is loaded only in client components. No WebGL.
  - Lighthouse targets: Performance ≥ 90 (mobile), Accessibility 100, CLS < 0.05.
- Metadata: title "FlowBill · Invoicing that gets freelancers paid faster", a description, Open Graph/Twitter image (`app/opengraph-image.tsx` rendering the hero), `theme-color` `#141C42`, and a favicon from the wordmark dot.

---

## 9. Build map

```
frontend/
├── design.md                       ← this file
└── src/
    ├── app/
    │   ├── layout.tsx              fonts, metadata, direction-contract comment
    │   ├── page.tsx                composes sections in order
    │   ├── globals.css             @theme tokens, container utility, base styles
    │   ├── opengraph-image.tsx
    │   └── api/waitlist/route.ts   (temporary) waitlist handler
    ├── components/landing/
    │   ├── site-header.tsx  mobile-menu.tsx
    │   ├── hero.tsx  hero-payment-stack.tsx
    │   ├── rails.tsx  how-it-works.tsx  features-bento.tsx  insights.tsx
    │   ├── portal-showcase.tsx  voices.tsx  pricing.tsx  faq.tsx  final-cta.tsx  site-footer.tsx
    │   └── waitlist-form.tsx
    ├── components/ui/               button.tsx  status-badge.tsx  app-frame.tsx  card.tsx
    ├── content/landing.ts           all copy + demo data + DRAFT pricing + placeholder testimonials
    └── lib/  gsap.ts  format-money.ts  cn.ts
```
New dependencies: `gsap`, `@gsap/react`, `lucide-react`, `clsx`, `tailwind-merge`.

### Open decisions (owner)
1. Waitlist storage: a Next route handler (temporary) or a Django `POST /api/v1/waitlist/` endpoint (recommended, throttled).
2. Confirm the draft pricing and the NGN/USD amounts.
3. Real testimonials, or approve the founder's-note fallback text.
4. Crypto: rails (USDT/USDC on which networks?) and provider. Add SRS PAY-008+ before any build.
5. "Built in Lagos" and contact email: confirm or replace.

### Done when
- Every section in §3 is built to spec at all widths in §7, with no horizontal scroll at 320.
- Motion works as in §6, and with reduced motion on the page is fully static and fully visible.
- `npx tsc --noEmit`, `npm run lint`, `npm run build` are clean.
- Playwright screenshots at the §7 sizes have been reviewed.
- Lighthouse targets in §8 are met.
- Taste gate (`gate.mjs`) and impeccable `detect.mjs` have run, with remaining findings fixed or waived with a reason.
- DESIGN.md is recorded from the built page by the impeccable documenter.
