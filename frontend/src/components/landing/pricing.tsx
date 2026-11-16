"use client";

import { CircleCheck } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { plans } from "@/content/landing";
import { gsap, MOTION, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";
import { cn, formatMoney, type Currency } from "@/lib/utils";
import { useWaitlist } from "./waitlist-modal";

type Billing = "monthly" | "yearly";

/** Pricing, mirroring the inspiration: coral billing switch, centred cards, raised white middle card. */
export function Pricing() {
  const root = useRef<HTMLElement>(null);
  const first = useRef(true);
  const [currency, setCurrency] = useState<Currency>("USD");
  const [billing, setBilling] = useState<Billing>("monthly");
  const { open } = useWaitlist();
  useReveal(root);

  useEffect(() => {
    const lang = navigator.language || "";
    // eslint-disable-next-line react-hooks/set-state-in-effect -- locale is only known on the client
    if (/-NG$/i.test(lang) || Intl.DateTimeFormat().resolvedOptions().timeZone === "Africa/Lagos") setCurrency("NGN");
  }, []);

  /* Prices roll when a toggle changes. */
  useGSAP(
    () => {
      if (first.current) {
        first.current = false;
        return;
      }
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        gsap.fromTo(".js-price", { yPercent: 100, autoAlpha: 0 }, { yPercent: 0, autoAlpha: 1, duration: 0.5, stagger: 0.06, ease: "expo.out" });
      });
    },
    { dependencies: [currency, billing], scope: root },
  );

  const yearly = billing === "yearly";

  return (
    <section ref={root} id="pricing" aria-labelledby="pricing-title" className="section-pad bg-surface">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <p className="js-fade text-eyebrow text-coral-600">Pricing</p>
          <h2 id="pricing-title" className="js-heading text-section mt-5">
            Our pricing
          </h2>
          <p className="js-fade text-lead mt-6 text-ink-muted">Free while you start. Upgrade when your client list grows.</p>
        </div>

        {/* Billing switch, as in the inspiration */}
        <div className="js-fade mt-12 flex flex-col items-center gap-5">
          <div className="flex items-center gap-4 text-[0.9375rem] font-semibold">
            <span className={cn("transition-colors", yearly ? "text-ink-muted" : "text-ink")}>Monthly</span>
            <button
              type="button"
              role="switch"
              aria-checked={yearly}
              aria-label="Bill yearly"
              onClick={() => setBilling(yearly ? "monthly" : "yearly")}
              className="relative h-9 w-[68px] rounded-full bg-coral-500 shadow-[inset_0_2px_4px_rgb(0_0_0/0.12)] transition-colors hover:bg-coral-600"
            >
              <span
                className={cn(
                  "absolute top-1 left-1 size-7 rounded-full bg-white shadow-md transition-transform duration-400 ease-[var(--ease-out-expo)]",
                  yearly && "translate-x-8",
                )}
              />
            </button>
            <span className={cn("transition-colors", yearly ? "text-ink" : "text-ink-muted")}>Yearly</span>
            <span className="rounded-full bg-coral-500 px-3 py-1 text-[12px] font-semibold text-white">Save 20%</span>
          </div>
          <div role="radiogroup" aria-label="Currency" className="flex items-center gap-1 rounded-full border border-line bg-white p-1 text-[13px] font-semibold">
            {(["NGN", "USD"] as const).map((c) => (
              <button
                key={c}
                type="button"
                role="radio"
                aria-checked={currency === c}
                onClick={() => setCurrency(c)}
                className={cn(
                  "h-9 min-w-16 rounded-full px-4 transition-colors",
                  currency === c ? "bg-navy-900 text-white" : "text-ink-muted hover:text-ink",
                )}
              >
                {c === "NGN" ? "₦ NGN" : "$ USD"}
              </button>
            ))}
          </div>
        </div>

        <ul className="relative mx-auto mt-20 grid max-w-md items-center gap-8 lg:mt-24 lg:max-w-5xl lg:grid-cols-3 lg:gap-6">
          {plans.map((p) => {
            const amount = p[billing][currency];
            const featured = !!p.featured;
            return (
              <li key={p.id} className={cn("js-card relative", featured && "order-first lg:order-none")}>
                {featured && <div aria-hidden className="absolute -top-14 -left-12 size-32 rounded-full bg-coral-400/40 lg:size-36" />}
                <div
                  className={cn(
                    "relative flex flex-col items-center rounded-[18px] px-8 text-center transition-[translate,background-color,box-shadow] duration-500 ease-[var(--ease-out-expo)]",
                    featured
                      ? "bg-white py-14 shadow-[0_50px_90px_-30px_rgb(20_28_66/0.28)] lg:-my-6 lg:py-16"
                      : "bg-white py-12 shadow-[var(--shadow-card)] hover:-translate-y-1 lg:bg-transparent lg:shadow-none lg:hover:bg-white lg:hover:shadow-[var(--shadow-card-hover)]",
                  )}
                >
                  <h3 className="text-[1.75rem] font-bold tracking-tight">{p.name}</h3>
                  <p className="mt-2 text-[0.9375rem] text-ink-muted">{p.blurb}</p>
                  <span aria-hidden className="mt-7 block h-px w-full bg-line" />

                  <ul className="mt-7 space-y-3.5 text-left">
                    {p.features.map((f) => (
                      <li key={f} className="flex items-start gap-3 text-[0.9375rem] text-ink-muted">
                        <CircleCheck className="mt-0.5 size-[18px] shrink-0 text-ink/45" aria-hidden />
                        {f}
                      </li>
                    ))}
                  </ul>

                  <span className="mt-10 block overflow-hidden">
                    <span className="js-price block font-display text-[2.5rem] leading-none font-bold tracking-[-0.02em] text-coral-600 tabular">
                      {formatMoney(amount, currency)}
                    </span>
                  </span>
                  <p className="mt-2 text-[0.875rem] text-ink-muted">
                    {amount === 0 ? "Free forever" : yearly ? "Per month, billed yearly" : "Per month"}
                  </p>

                  <Button type="button" onClick={() => open({ source: `pricing-${p.id}` })} className="mt-8 px-9" aria-label={`Get started with ${p.name}`}>
                    Get started
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
        <p className="mt-16 text-center text-[14px] text-ink-muted">Prices are early estimates and may change before launch.</p>
      </div>
    </section>
  );
}
