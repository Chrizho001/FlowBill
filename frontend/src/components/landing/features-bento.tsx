"use client";

import { BellRing, CalendarSync, Download, FileText, Receipt, Users } from "lucide-react";
import { useRef, type ReactNode } from "react";
import { StatusBadge } from "@/components/ui/status-badge";
import { clients, expenses } from "@/content/landing";
import { gsap, MOTION, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";
import { cn, formatMoney } from "@/lib/utils";

function Soon() {
  return (
    <span className="rounded-full bg-coral-100 px-2.5 py-1 text-[11px] font-medium tracking-wide text-coral-600 uppercase">
      Coming soon
    </span>
  );
}

function BentoCard({
  icon,
  title,
  body,
  badge,
  className,
  children,
}: {
  icon: ReactNode;
  title: string;
  body: string;
  badge?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <li
      className={cn(
        "js-card js-bento group flex flex-col overflow-hidden rounded-card border border-line bg-white shadow-[var(--shadow-card)]",
        "transition-[translate,scale,transform,box-shadow] duration-300 ease-[var(--ease-out-expo)] hover:-translate-y-1 hover:shadow-[var(--shadow-card-hover)]",
        className,
      )}
    >
      <div className="p-7 sm:p-10 sm:pb-8">
        <div className="flex items-center justify-between gap-4">
          <span className="grid size-11 place-items-center rounded-btn bg-navy-900 text-white">{icon}</span>
          {badge}
        </div>
        <h3 className="mt-6 text-[1.5rem] font-medium tracking-[-0.01em]">{title}</h3>
        <p className="mt-2 max-w-md text-ink-muted">{body}</p>
      </div>
      <div className="mt-auto px-7 pb-7 sm:px-10 sm:pb-10" aria-hidden>
        {children}
      </div>
    </li>
  );
}

export function FeaturesBento() {
  const root = useRef<HTMLElement>(null);
  useReveal(root);

  /* Each card's UI plays one small loop on hover (design.md §3.4 / §6.4). */
  useGSAP(
    (_c, contextSafe) => {
      const mm = gsap.matchMedia();
      mm.add(MOTION.hover, () => {
        if (!contextSafe) return;
        const cleanups: (() => void)[] = [];
        root.current?.querySelectorAll<HTMLElement>(".js-bento").forEach((card) => {
          const loop = card.querySelectorAll<HTMLElement>(".js-loop");
          if (!loop.length) return;
          const tl = gsap.timeline({ paused: true });
          tl.fromTo(loop, { y: 10, autoAlpha: 0.2 }, { y: 0, autoAlpha: 1, duration: 0.45, stagger: 0.07, ease: "power3.out" });
          const toggle = card.querySelector<HTMLElement>(".js-toggle-knob");
          if (toggle) tl.fromTo(toggle, { x: 0 }, { x: 16, duration: 0.35, ease: "back.out(2)" }, 0.1);
          const enter = contextSafe(() => tl.restart());
          card.addEventListener("pointerenter", enter);
          cleanups.push(() => card.removeEventListener("pointerenter", enter));
        });
        return () => cleanups.forEach((fn) => fn());
      });
    },
    { scope: root },
  );

  return (
    <section ref={root} id="features" aria-labelledby="features-title" className="section-pad bg-surface">
      <div className="container">
        <div className="max-w-2xl">
          <p className="js-fade text-eyebrow text-coral-600">Product</p>
          <h2 id="features-title" className="js-heading text-section mt-5">
            Everything around the invoice.
          </h2>
          <p className="js-fade text-lead mt-6 text-ink-muted">
            Clients, expenses, PDFs and reminders in the same place you bill from.
          </p>
        </div>

        <ul className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-2 lg:mt-20 lg:grid-cols-6 lg:gap-8">
          <BentoCard
            className="lg:col-span-2"
            icon={<Users className="size-5" aria-hidden />}
            title="Clients"
            body="Every client, what they owe and what they've paid."
          >
            <ul className="space-y-2.5">
              {clients.map((c, i) => (
                <li key={c.name} className="js-loop flex items-center gap-3 rounded-chip bg-surface px-3 py-2.5 text-[14px]">
                  <span className="grid size-8 place-items-center rounded-full bg-white text-[11px] font-bold text-ink shadow-sm">
                    {c.initials}
                  </span>
                  <span className="min-w-0 flex-1 truncate font-medium">{c.name}</span>
                  {i === 0 ? (
                    <span className="relative h-5 w-9 rounded-full bg-[#16A34A]">
                      <span className="js-toggle-knob absolute top-0.5 left-0.5 size-4 rounded-full bg-white" />
                    </span>
                  ) : (
                    <span className="text-[13px] text-ink-muted tabular">{c.owed ? formatMoney(c.owed) : "Paid up"}</span>
                  )}
                </li>
              ))}
            </ul>
          </BentoCard>

          <BentoCard
            className="lg:col-span-2"
            icon={<FileText className="size-5" aria-hidden />}
            title="Branded PDFs"
            body="Your logo, bank details and tax ID on every invoice."
          >
            <div className="relative mx-auto max-w-[260px] rounded-chip border border-line bg-white p-5 shadow-[var(--shadow-card)]">
              <div className="js-loop flex items-center justify-between">
                <span className="font-display text-[15px] font-bold">KO Design</span>
                <span className="text-[10px] tracking-widest text-ink-muted uppercase">Invoice</span>
              </div>
              <div className="js-loop mt-4 space-y-1.5">
                <div className="h-1.5 w-3/4 rounded bg-line" />
                <div className="h-1.5 w-1/2 rounded bg-line" />
              </div>
              <div className="js-loop mt-4 space-y-1.5">
                <div className="flex justify-between"><div className="h-1.5 w-1/2 rounded bg-line" /><div className="h-1.5 w-10 rounded bg-line" /></div>
                <div className="flex justify-between"><div className="h-1.5 w-2/5 rounded bg-line" /><div className="h-1.5 w-10 rounded bg-line" /></div>
              </div>
              <div className="js-loop mt-4 flex items-center justify-between border-t border-line pt-3">
                <span className="text-[11px] text-ink-muted">Total</span>
                <span className="font-display text-[15px] font-bold tabular">₦450,000</span>
              </div>
              <span className="js-loop mt-4 flex w-full items-center justify-center gap-1.5 rounded-chip bg-navy-900 py-2.5 text-[12px] font-semibold text-white">
                <Download className="size-3.5" /> Download PDF
              </span>
            </div>
          </BentoCard>

          <BentoCard
            className="md:col-span-2 lg:col-span-2"
            icon={<Receipt className="size-5" aria-hidden />}
            title="Expenses"
            body="Log costs by category and link them to a client."
          >
            <ul className="divide-y divide-line rounded-chip border border-line">
              {expenses.map((e) => (
                <li key={e.note} className="js-loop flex items-center justify-between gap-3 px-4 py-3 text-[14px]">
                  <span>
                    <span className="block font-medium">{e.category}</span>
                    <span className="text-[12px] text-ink-muted">{e.note}</span>
                  </span>
                  <span className="font-medium tabular">−{formatMoney(e.amount)}</span>
                </li>
              ))}
            </ul>
          </BentoCard>

          <BentoCard
            className="lg:col-span-3"
            icon={<CalendarSync className="size-5" aria-hidden />}
            title="Recurring invoices"
            body="Retainers bill themselves weekly, monthly, quarterly or yearly."
            badge={<Soon />}
          >
            <div className="grid grid-cols-7 gap-2 text-center text-[12px]">
              {["N", "D", "J", "F", "M", "A", "M"].map((m, i) => (
                <div
                  key={i}
                  className={cn(
                    "js-loop rounded-chip py-3",
                    i === 1 ? "bg-coral-600 font-medium text-white" : "bg-surface text-ink-muted",
                  )}
                >
                  {m}
                  <span className={cn("mx-auto mt-2 block size-1.5 rounded-full", i === 1 ? "bg-white" : "bg-ink/20")} />
                </div>
              ))}
            </div>
            <p className="mt-4 text-[13px] text-ink-muted">Monthly · next invoice on Dec 1</p>
          </BentoCard>

          <BentoCard
            className="lg:col-span-3"
            icon={<BellRing className="size-5" aria-hidden />}
            title="Overdue reminders"
            body="Late invoices are flagged and your client gets a polite nudge."
            badge={<Soon />}
          >
            <div className="space-y-3">
              <div className="js-loop flex items-center gap-3 rounded-chip border border-line px-4 py-3 text-[14px]">
                <span className="font-medium tabular">INV-2026-0031</span>
                <span className="hidden text-ink-muted sm:inline">Ola & Partners</span>
                <StatusBadge status="overdue" className="ml-auto" />
              </div>
              <div className="js-loop flex items-center gap-3 rounded-chip bg-surface px-4 py-3 text-[14px] text-ink-muted">
                <BellRing className="size-4 text-coral-600" /> Reminder sent · 3 days after due date
              </div>
            </div>
          </BentoCard>
        </ul>
      </div>
    </section>
  );
}
