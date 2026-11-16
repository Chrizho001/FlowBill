"use client";

import { CheckCircle2 } from "lucide-react";
import { useRef } from "react";
import { AppFrame } from "@/components/ui/app-frame";
import { dashboard } from "@/content/landing";
import { gsap, MOTION, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";
import { cn, formatCompact, formatMoney } from "@/lib/utils";

const toneDot: Record<string, string> = {
  paid: "bg-[#16A34A]",
  pending: "bg-[#F59E0B]",
  overdue: "bg-[#BE123C]",
  neutral: "bg-navy-700",
};

const bullets = ["Total earned, pending and overdue", "Six months of revenue", "Top clients by revenue"];

export function Insights() {
  const root = useRef<HTMLElement>(null);
  useReveal(root);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        const tl = gsap.timeline({
          scrollTrigger: { trigger: ".js-dash", start: "top 92%", once: true },
        });
        tl.from(".js-dash", { y: 40, autoAlpha: 0, duration: 0.6, ease: "expo.out" });

        root.current?.querySelectorAll<HTMLElement>(".js-count").forEach((el) => {
          const target = Number(el.dataset.value);
          const plain = el.dataset.plain === "true";
          const o = { v: 0 };
          tl.to(
            o,
            {
              v: target,
              duration: 0.9,
              ease: "power2.out",
              onUpdate: () => {
                el.textContent = plain ? String(Math.round(o.v)) : formatCompact(o.v);
              },
            },
            0.15,
          );
        });
        tl.from(".js-bar", { scaleY: 0, transformOrigin: "bottom center", duration: 0.6, stagger: 0.05, ease: "expo.out" }, 0.2);
        tl.from(".js-share", { scaleX: 0, transformOrigin: "left center", duration: 0.6, stagger: 0.05, ease: "expo.out" }, 0.3);
      });
    },
    { scope: root },
  );

  const max = Math.max(...dashboard.revenue.map((r) => r.value));

  return (
    <section ref={root} id="insights" aria-labelledby="insights-title" className="section-pad overflow-hidden bg-white">
      <div className="container grid grid-cols-1 items-center gap-16 lg:grid-cols-12 lg:gap-8">
        <div className="lg:col-span-5 lg:pr-8">
          <p className="js-fade text-eyebrow text-coral-600">Insights</p>
          <h2 id="insights-title" className="js-heading text-section mt-5">
            Know where your money is.
          </h2>
          <p className="js-fade text-lead mt-6 text-ink-muted">
            Earned, pending and overdue at a glance, with six months of revenue and the clients who bring it in.
          </p>
          <ul className="mt-10 space-y-4">
            {bullets.map((b) => (
              <li key={b} className="js-fade flex items-center gap-3 text-[1.0625rem]">
                <CheckCircle2 className="size-5 shrink-0 text-coral-600" aria-hidden /> {b}
              </li>
            ))}
          </ul>
        </div>

        <div className="lg:col-span-7">
          <AppFrame className="js-dash lg:mr-[-2.5rem] xl:mr-[-5rem]">
            <div className="grid gap-5 bg-surface/50 p-5 sm:p-7" aria-hidden>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {dashboard.stats.map((s) => (
                  <div key={s.label} className="rounded-chip border border-line bg-white p-4">
                    <p className="flex items-center gap-2 text-[12px] text-ink-muted">
                      <span className={cn("size-2 rounded-full", toneDot[s.tone])} /> {s.label}
                    </p>
                    <p
                      className="js-count mt-2 font-display text-[22px] font-bold tabular sm:text-[24px]"
                      data-value={s.value}
                      data-plain={s.plain ? "true" : "false"}
                    >
                      {s.plain ? s.value : formatCompact(s.value)}
                    </p>
                  </div>
                ))}
              </div>

              <div className="grid gap-5 md:grid-cols-5">
                <div className="flex flex-col rounded-chip border border-line bg-white p-5 md:col-span-3">
                  <div className="flex items-baseline justify-between">
                    <p className="text-[13px] font-medium">Revenue · last 6 months</p>
                    <p className="text-[12px] text-ink-muted">₦ thousands</p>
                  </div>
                  <div className="mt-6 flex min-h-40 flex-1 items-end gap-3">
                    {dashboard.revenue.map((r, i) => {
                      const current = i === dashboard.revenue.length - 1;
                      return (
                        <div key={r.month} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                          <span className={cn("text-[11px] tabular", current ? "font-medium text-ink" : "text-ink-muted")}>
                            {r.value}
                          </span>
                          <div
                            className={cn("js-bar w-full rounded-t-[6px]", current ? "bg-coral-600" : "bg-coral-100")}
                            style={{ height: `${(r.value / max) * 100}%` }}
                          />
                          <span className="text-[11px] text-ink-muted">{r.month}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="flex flex-col gap-5 md:col-span-2">
                  <div className="rounded-chip border border-line bg-white p-5">
                    <p className="text-[13px] font-medium">Top clients</p>
                    <ul className="mt-4 space-y-3.5">
                      {dashboard.topClients.map((c) => (
                        <li key={c.name} className="text-[12px]">
                          <div className="flex justify-between">
                            <span>{c.name}</span>
                            <span className="text-ink-muted tabular">{c.share}%</span>
                          </div>
                          <div className="mt-1.5 h-1.5 rounded-full bg-surface">
                            <div className="js-share h-full rounded-full bg-navy-900" style={{ width: `${c.share}%` }} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="rounded-chip border border-line bg-white p-5">
                    <p className="text-[13px] font-medium">Due this week</p>
                    <ul className="mt-3 space-y-2.5">
                      {dashboard.dueSoon.map((d) => (
                        <li key={d.number} className="flex justify-between gap-2 text-[12px]">
                          <span className="truncate text-ink-muted">{d.client}</span>
                          <span className="font-medium tabular">
                            {formatMoney(d.amount)} · {d.due}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </AppFrame>
          <p className="sr-only">
            FlowBill dashboard showing total earned, pending and overdue amounts, a six-month revenue chart, top clients and invoices due this week.
          </p>
        </div>
      </div>
    </section>
  );
}
