import {
  Building2,
  Check,
  ChevronLeft,
  Copy,
  CreditCard,
  Download,
  Eye,
  FileText,
  Link2,
  Lock,
  Mail,
  Plus,
  Send,
  Smartphone,
} from "lucide-react";
import { StatusBadge } from "@/components/ui/status-badge";
import { demoInvoice as inv } from "@/content/landing";
import { formatMoney } from "@/lib/utils";

/*
 * FlowBill mobile screens, authored at the iPhone 16 size (393×852 points).
 * Elements marked `js-sx` animate in (staggered) when their slide becomes active.
 */

const Screen = ({ children, tone = "light" }: { children: React.ReactNode; tone?: "light" | "navy" }) => (
  <div className={`absolute inset-0 flex flex-col font-sans ${tone === "navy" ? "bg-navy-900 text-white" : "bg-surface text-ink"}`}>
    {children}
  </div>
);

const AppBar = ({ title, tone = "light" }: { title: string; tone?: "light" | "navy" }) => (
  <div className={`flex items-center gap-3 px-5 pt-[62px] pb-4 ${tone === "navy" ? "" : "bg-white"}`}>
    <ChevronLeft className="size-6 opacity-70" />
    <p className="text-[19px] font-bold tracking-tight">{title}</p>
  </div>
);

export function CreateScreen() {
  return (
    <Screen>
      <AppBar title="New invoice" />
      <div className="flex-1 space-y-4 px-5 pt-4">
        <div className="js-sx flex items-center gap-3 rounded-[18px] bg-white p-4 shadow-sm">
          <span className="grid size-11 place-items-center rounded-full bg-gradient-to-br from-coral-400 to-coral-600 text-[13px] font-bold text-white">AS</span>
          <div className="flex-1 leading-tight">
            <p className="text-[12px] text-ink-muted">Bill to</p>
            <p className="text-[16px] font-semibold">{inv.client}</p>
          </div>
          <span className="text-[13px] font-semibold text-coral-600">Change</span>
        </div>

        <div className="js-sx rounded-[18px] bg-white p-4 shadow-sm">
          <div className="flex justify-between text-[12px] text-ink-muted">
            <span>{inv.number}</span>
            <span>Due in 7 days</span>
          </div>
          <ul className="mt-3 divide-y divide-line">
            {inv.items.map((it) => (
              <li key={it.label} className="js-sx flex items-center justify-between py-3.5">
                <div className="leading-tight">
                  <p className="text-[15px] font-semibold">{it.label}</p>
                  <p className="text-[12px] text-ink-muted">1 × {formatMoney(it.price)}</p>
                </div>
                <p className="text-[15px] font-semibold tabular">{formatMoney(it.price)}</p>
              </li>
            ))}
          </ul>
          <button className="js-sx mt-2 flex w-full items-center justify-center gap-2 rounded-[12px] border border-dashed border-ink/20 py-3 text-[14px] font-semibold text-ink-muted">
            <Plus className="size-4" /> Add item
          </button>
        </div>

        <div className="js-sx space-y-2 rounded-[18px] bg-white p-4 text-[14px] shadow-sm">
          <div className="flex justify-between text-ink-muted">
            <span>Subtotal</span>
            <span className="tabular">{formatMoney(inv.total)}</span>
          </div>
          <div className="flex justify-between text-ink-muted">
            <span>VAT</span>
            <span className="tabular">₦0</span>
          </div>
          <div className="flex items-baseline justify-between border-t border-line pt-3">
            <span className="font-semibold">Total</span>
            <span className="font-display text-[26px] font-bold tabular">{formatMoney(inv.total)}</span>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 px-5 pt-4 pb-10">
        <span className="rounded-[14px] border border-line bg-white py-4 text-center text-[15px] font-semibold">Save draft</span>
        <span className="js-sx rounded-[14px] bg-coral-600 py-4 text-center text-[15px] font-semibold text-white">Continue</span>
      </div>
    </Screen>
  );
}

export function SendScreen() {
  return (
    <Screen>
      <AppBar title="Send invoice" />
      <div className="flex-1 space-y-4 px-5 pt-4">
        <div className="js-sx rounded-[18px] bg-white p-4 shadow-sm">
          <p className="text-[12px] text-ink-muted">To</p>
          <p className="mt-1 flex items-center gap-2 text-[15px] font-semibold">
            <Mail className="size-4 text-ink-muted" /> {inv.clientEmail}
          </p>
          <div className="mt-4 rounded-[12px] bg-surface p-3 text-[14px] leading-relaxed text-ink-muted">
            Hi Ada, here&apos;s the invoice for the brand identity and website. You can pay online from the link. Thank you!
          </div>
        </div>

        <div className="js-sx flex items-center gap-3 rounded-[18px] bg-white p-4 shadow-sm">
          <span className="grid size-11 place-items-center rounded-[12px] bg-coral-100 text-coral-600">
            <FileText className="size-5" />
          </span>
          <div className="flex-1 leading-tight">
            <p className="text-[15px] font-semibold">{inv.number}.pdf</p>
            <p className="text-[12px] text-ink-muted">Attached · 128 KB</p>
          </div>
          <StatusBadge status="pending" />
        </div>

        <div className="js-sx rounded-[18px] bg-navy-900 p-4 text-white">
          <p className="flex items-center gap-2 text-[12px] text-navy-300">
            <Link2 className="size-4" /> Secure payment link
          </p>
          <div className="mt-3 flex items-center justify-between rounded-[12px] bg-white/10 px-3 py-3">
            <span className="text-[14px]">pay.flowbill.app/i/0042</span>
            <Copy className="size-4 text-navy-300" />
          </div>
          <p className="mt-3 text-[12px] text-navy-300">No account needed. Expires in 30 days.</p>
        </div>

        <div className="js-sx flex items-center gap-3 rounded-[16px] bg-[#DCFCE7] px-4 py-3 text-[14px] font-semibold text-[#15803D]">
          <Check className="size-5" strokeWidth={3} /> Sent to Ada · just now
        </div>
      </div>
      <div className="px-5 pt-4 pb-10">
        <span className="js-sx flex items-center justify-center gap-2 rounded-[14px] bg-coral-600 py-4 text-[15px] font-semibold text-white">
          <Send className="size-4" /> Send invoice
        </span>
      </div>
    </Screen>
  );
}

/** What the client sees when they open the magic link (Safari). Also used in the Client portal section. */
export function ClientScreen() {
  return (
    <Screen>
      <div className="bg-white px-4 pt-[60px] pb-3">
        <div className="flex items-center justify-center gap-1.5 rounded-[12px] bg-surface py-2.5 text-[14px] text-ink-muted">
          <Lock className="size-3.5" /> pay.flowbill.app
        </div>
      </div>
      <div className="bg-navy-900 px-5 pt-6 pb-20 text-white">
        <div className="js-sx flex items-center gap-3">
          <span className="grid size-12 place-items-center rounded-full bg-coral-500 font-display text-[15px] font-bold">KO</span>
          <div className="leading-tight">
            <p className="text-[16px] font-semibold">{inv.issuer}</p>
            <p className="text-[12px] text-navy-300">Lagos · Invoice from your designer</p>
          </div>
        </div>
      </div>
      <div className="-mt-14 flex-1 px-4">
        <div className="js-sx rounded-[22px] bg-white p-5 shadow-[0_20px_40px_-20px_rgb(20_28_66/0.35)]">
          <p className="text-[12px] tracking-[0.12em] text-ink-muted uppercase">{inv.number}</p>
          <p className="mt-1 font-display text-[36px] leading-none font-bold tabular">{formatMoney(inv.total)}</p>
          <p className="mt-1.5 text-[13px] text-ink-muted">Due 23 Nov 2026 · {inv.client}</p>
          <ul className="mt-4 space-y-2 border-t border-line pt-4 text-[14px]">
            {inv.items.map((it) => (
              <li key={it.label} className="flex justify-between">
                <span className="text-ink-muted">{it.label}</span>
                <span className="font-medium tabular">{formatMoney(it.price)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-5 text-[13px] font-semibold">Pay with</p>
          <div className="js-sx mt-2 grid grid-cols-3 gap-2 text-[12px]">
            {[
              { I: CreditCard, l: "Card", on: true },
              { I: Building2, l: "Transfer" },
              { I: Smartphone, l: "USSD" },
            ].map(({ I, l, on }) => (
              <span
                key={l}
                className={`flex flex-col items-center gap-1.5 rounded-[12px] border py-3 ${on ? "border-coral-600 bg-coral-100 font-semibold text-coral-600" : "border-line text-ink-muted"}`}
              >
                <I className="size-5" /> {l}
              </span>
            ))}
          </div>
          <span className="js-sx mt-5 flex items-center justify-center rounded-[14px] bg-coral-600 py-4 text-[16px] font-semibold text-white">
            Pay {formatMoney(inv.total)}
          </span>
          <p className="mt-3 flex items-center justify-center gap-1.5 text-[13px] text-ink-muted">
            <Download className="size-3.5" /> Download PDF
          </p>
        </div>
        <p className="mt-4 text-center text-[12px] text-ink-muted">Secured by Paystack</p>
      </div>
    </Screen>
  );
}

export function PaidScreen() {
  const events = [
    { I: Send, l: "Sent to client", t: "Mon 09:14" },
    { I: Eye, l: "Viewed by client", t: "Mon 11:40" },
    { I: Check, l: "Paid by card · Paystack", t: "Tue 08:03", paid: true },
  ];
  return (
    <Screen>
      <div className="flex flex-1 flex-col items-center px-6 pt-[110px] text-center">
        <span className="js-check grid size-24 place-items-center rounded-full bg-[#16A34A] text-white shadow-[0_20px_40px_-12px_rgb(22_163_74/0.6)]">
          <Check className="size-12" strokeWidth={3} />
        </span>
        <p className="js-sx mt-8 text-[15px] font-semibold text-ink-muted">Payment received</p>
        <p className="js-sx mt-2 font-display text-[44px] leading-none font-bold tabular">{formatMoney(inv.total)}</p>
        <p className="js-sx mt-3 text-[14px] text-ink-muted">
          from <span className="font-semibold text-ink">{inv.client}</span>
        </p>
        <span className="js-sx mt-5">
          <StatusBadge status="paid" />
        </span>

        <ol className="js-sx mt-10 w-full space-y-3 rounded-[18px] bg-white p-5 text-left shadow-sm">
          {events.map((e) => (
            <li key={e.l} className="flex items-center gap-3 text-[14px]">
              <span className={`grid size-8 place-items-center rounded-full ${e.paid ? "bg-[#DCFCE7] text-[#15803D]" : "bg-surface text-ink-muted"}`}>
                <e.I className="size-4" />
              </span>
              <span className="flex-1">{e.l}</span>
              <span className="text-[12px] text-ink-muted">{e.t}</span>
            </li>
          ))}
        </ol>
        <p className="js-sx mt-5 text-[13px] text-ink-muted">Receipt emailed to you and Ada.</p>
      </div>
      <div className="px-5 pb-10">
        <span className="block rounded-[14px] border border-line bg-white py-4 text-center text-[15px] font-semibold">View invoice</span>
      </div>
    </Screen>
  );
}
