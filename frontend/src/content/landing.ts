/**
 * FlowBill landing page content — the single source for copy and demo data.
 *
 * Honesty rules (PRODUCT.md → Evidence on Hand):
 *  - Names, amounts and dashboard figures marked `// demo` are illustrative product UI, not customers.
 *  - Pricing is DRAFT until the owner confirms it.
 *  - Testimonials are placeholders and do not render in production until real quotes exist.
 */

export const nav = [
  { label: "Product", href: "#features" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
] as const;

export const hero = {
  // Each line must stay on one line at desktop widths (owner requirement: max two lines).
  titleLine1: "Get paid for every",
  titleLine2: "invoice you send.",
  lead: "Invoice clients and get paid by card, bank transfer or USSD, all from one secure link.",
  cta: "Get started",
};

export const PROFESSIONS = [
  "Software developer",
  "Designer",
  "Writer or content creator",
  "Consultant",
  "Marketer",
  "Agency owner",
  "Other",
] as const;

// demo — hero dashboard (mirrors the inspiration's desktop dashboard)
export const heroDashboard = {
  earned: 3_400_000,
  pending: 620_000,
  rows: [
    { initials: "AS", name: "Adaeze Studio", role: "Brand studio", invoices: 12, billed: 1_240_000, tone: "from-coral-400 to-coral-600" },
    { initials: "NB", name: "Northbank Labs", role: "Fintech", invoices: 8, billed: 640_000, tone: "from-[#60A5FA] to-[#2563EB]" },
    { initials: "OP", name: "Ola & Partners", role: "Law firm", invoices: 5, billed: 380_000, tone: "from-[#FBBF24] to-[#D97706]" },
    { initials: "TK", name: "Tunde Kitchen Co.", role: "Restaurant", invoices: 3, billed: 96_000, tone: "from-[#34D399] to-[#059669]" },
  ],
  builder: [
    { label: "Brand identity", amount: 350_000, fill: 0.78 },
    { label: "Website design", amount: 100_000, fill: 0.46 },
    { label: "Copywriting", amount: 60_000, fill: 0.32 },
    { label: "Hosting, 1 year", amount: 40_000, fill: 0.2 },
  ],
};

// demo — the invoice that travels through the hero and the pinned story
export const demoInvoice = {
  number: "INV-2026-0042",
  issuer: "Kemi Okafor Design",
  client: "Adaeze Studio",
  clientEmail: "ada@adaeze.example",
  items: [
    { label: "Brand identity", qty: 1, price: 350_000 },
    { label: "Website design", qty: 1, price: 100_000 },
  ],
  taxRate: 0,
  total: 450_000,
  monthRevenue: 1_200_000,
  monthDelta: 18,
};

export const rails = {
  label: "Paid in your currency, on the payment methods your clients already use.",
};

export const steps = [
  {
    key: "create",
    index: "01",
    title: "Create",
    body: "Add your client and line items. FlowBill works out the totals and numbers the invoice for you.",
    image: "/images/steps/step-create.png",
  },
  {
    key: "send",
    index: "02",
    title: "Send",
    body: "One tap emails a branded PDF and a secure payment link. Your client doesn't need an account.",
    image: "/images/steps/step-send.png",
  },
  {
    key: "client",
    index: "03",
    title: "Client pays",
    body: "They open the link and pay by card, bank transfer or USSD in the currency you billed.",
    image: "/images/steps/step-client.png",
  },
  {
    key: "paid",
    index: "04",
    title: "Get paid",
    body: "The invoice marks itself paid, and you both get a receipt. No chasing, no spreadsheets.",
    image: "/images/steps/step-paid.png",
  },
] as const;

// demo
export const clients = [
  { initials: "AS", name: "Adaeze Studio", owed: 450_000, active: true },
  { initials: "NB", name: "Northbank Labs", owed: 120_000, active: true },
  { initials: "TK", name: "Tunde Kitchen Co.", owed: 0, active: false },
];

// demo
export const expenses = [
  { category: "Software", note: "Figma, yearly", amount: 96_000 },
  { category: "Internet", note: "Fibre, November", amount: 25_000 },
  { category: "Travel", note: "Client workshop", amount: 18_500 },
];

// demo — dashboard (Insights section)
export const dashboard = {
  stats: [
    { label: "Total earned", value: 3_400_000, tone: "paid" },
    { label: "Pending", value: 620_000, tone: "pending" },
    { label: "Overdue", value: 85_000, tone: "overdue" },
    { label: "Active clients", value: 12, tone: "neutral", plain: true },
  ],
  revenue: [
    { month: "Jun", value: 380 },
    { month: "Jul", value: 520 },
    { month: "Aug", value: 460 },
    { month: "Sep", value: 690 },
    { month: "Oct", value: 610 },
    { month: "Nov", value: 840 },
  ],
  topClients: [
    { name: "Adaeze Studio", share: 42 },
    { name: "Northbank Labs", share: 31 },
    { name: "Ola & Partners", share: 17 },
  ],
  dueSoon: [
    { number: "INV-2026-0039", client: "Northbank Labs", amount: 120_000, due: "Thu" },
    { number: "INV-2026-0040", client: "Ola & Partners", amount: 64_000, due: "Sat" },
  ],
};

export const portalImage = "/images/portal/portal-iphone.png";

export const portalCallouts = [
  "Your logo & business details",
  "Download the official PDF",
  "Pay by card, bank or USSD",
  "Receipt sent to both of you",
];

export type Testimonial = {
  quote: string;
  name: string;
  role: string;
  location: string;
  initials: string;
  photo: string; // generated portrait (see frontend/docs/image-prompts.md)
  isSample: boolean;
};

// SAMPLE testimonials with AI-generated portraits — illustrative only, not real customers.
// They render in development, or in production only when NEXT_PUBLIC_SHOW_SAMPLE_TESTIMONIALS=true.
// Replace with real quotes (and real, consented photos) before launch.
export const testimonials: Testimonial[] = [
  {
    quote:
      "My clients used to take three weeks to pay. Now they tap the link and pay the same day. I spend my mornings designing, not chasing.",
    name: "Amaka Obi",
    role: "Brand designer",
    location: "Lagos",
    initials: "AO",
    photo: "/images/testimonials/amaka.jpg",
    isSample: true,
  },
  {
    quote:
      "I bill clients in the UK and in Ghana. FlowBill lets me invoice in pounds or dollars, and everything lands in one dashboard.",
    name: "Kwame Mensah",
    role: "Full-stack developer",
    location: "Accra",
    initials: "KM",
    photo: "/images/testimonials/kwame.jpg",
    isSample: true,
  },
  {
    quote:
      "The PDF looks like it came from a big agency. Clients take me more seriously, and the payment page means fewer awkward follow-ups.",
    name: "Zainab Bello",
    role: "Content writer",
    location: "Abuja",
    initials: "ZB",
    photo: "/images/testimonials/zainab.jpg",
    isSample: true,
  },
  {
    quote:
      "We run twelve retainers. Seeing earned, pending and overdue on one screen changed how we plan hiring every month.",
    name: "Tunde Adeyemi",
    role: "Founder, studio agency",
    location: "Lagos",
    initials: "TA",
    photo: "/images/testimonials/tunde.jpg",
    isSample: true,
  },
  {
    quote:
      "My clients pay by card or bank transfer without creating an account. Setting up my branding took ten minutes.",
    name: "Wanjiru Kamau",
    role: "UX consultant",
    location: "Nairobi",
    initials: "WK",
    photo: "/images/testimonials/wanjiru.jpg",
    isSample: true,
  },
];

// Shown while there are no real testimonials (owner to confirm wording).
export const founderNote = {
  quote:
    "I built FlowBill after one too many “just following up on this invoice” emails. Getting paid should be the easy part of freelancing.",
  name: "The FlowBill founder",
  role: "Freelancer, builder of FlowBill",
};

export type Plan = {
  id: "starter" | "pro" | "agency";
  name: string;
  blurb: string;
  monthly: { NGN: number; USD: number };
  yearly: { NGN: number; USD: number }; // per month, billed yearly
  features: string[];
  featured?: boolean;
};

// DRAFT pricing — confirm before launch.
export const plans: Plan[] = [
  {
    id: "starter",
    name: "Starter",
    blurb: "For your first few clients.",
    monthly: { NGN: 0, USD: 0 },
    yearly: { NGN: 0, USD: 0 },
    features: ["3 clients", "5 invoices a month", "Branded PDF invoices", "Card & bank payments"],
  },
  {
    id: "pro",
    name: "Pro",
    blurb: "For full-time freelancers.",
    monthly: { NGN: 7_500, USD: 9 },
    yearly: { NGN: 6_000, USD: 7 },
    features: [
      "Unlimited clients & invoices",
      "Expense tracking",
      "Dashboard & revenue insights",
      "Multi-currency invoices",
      "Overdue reminders",
    ],
    featured: true,
  },
  {
    id: "agency",
    name: "Agency",
    blurb: "For small teams billing many clients.",
    monthly: { NGN: 20_000, USD: 24 },
    yearly: { NGN: 16_000, USD: 19 },
    features: [
      "Everything in Pro",
      "Recurring invoices",
      "CSV export",
      "Priority support",
      "Crypto payments (soon)",
    ],
  },
];

export const faqs = [
  {
    q: "Do my clients need a FlowBill account to pay?",
    a: "No. Every invoice you send includes a secure link. Your client opens it, sees the invoice with your branding, downloads the PDF if they want, and pays. No sign-up, no password.",
  },
  {
    q: "Which currencies and payment methods are supported?",
    a: "You can invoice in NGN, USD, GBP or EUR. Clients pay by card, bank transfer or USSD through Paystack.",
  },
  {
    q: "When are crypto payments coming?",
    a: "After launch. We're planning stablecoin payments (USDT and USDC) so clients abroad can pay you easily. Join the waitlist and tick the crypto box to get early access.",
  },
  {
    q: "Is my data safe?",
    a: "Each account's data is kept separate from everyone else's. Payments are handled by Paystack, so FlowBill never stores your clients' card details.",
  },
  {
    q: "Can I use my own branding on invoices?",
    a: "Yes. Your logo, business address, tax ID and bank details appear on every invoice PDF and on the payment page your client sees.",
  },
  {
    q: "What does it cost?",
    a: "Starter is free. Paid plans add unlimited invoices, insights and recurring billing. Early-access members will hear about pricing first.",
  },
];

export const finalCta = {
  titleLine1: "Stop chasing.",
  titleLine2: "Start getting paid.",
  lead: "Join the waitlist and be first to send invoices your clients can pay in one tap.",
};

export const footer = {
  tagline: "Invoicing and payments for freelancers and small agencies.",
  email: "hello@flowbill.example",
  place: "Built in Lagos", // owner to confirm
};
