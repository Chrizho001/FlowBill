"use client";

import Image from "next/image";
import { useRef } from "react";
import { Button } from "@/components/ui/button";
import { IPhone16 } from "@/components/ui/iphone16";
import { portalCallouts, portalImage } from "@/content/landing";
import { gsap, MOTION, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";
import { formatMoney } from "@/lib/utils";
import { ClientScreen } from "./app-screens";
import { useWaitlist } from "./waitlist-modal";

export function PortalShowcase({ hasImage }: { hasImage: boolean }) {
  const root = useRef<HTMLElement>(null);
  const { open } = useWaitlist();
  useReveal(root);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        const tl = gsap.timeline({ scrollTrigger: { trigger: ".js-phone", start: "top 72%", once: true } });
        tl.from(".js-phone", { y: 100, rotate: 4, autoAlpha: 0, duration: 1.3, ease: "expo.out" })
          .from(".js-phone .js-sx", { y: 16, autoAlpha: 0, stagger: 0.08, duration: 0.6 }, 0.5)
          .from(".js-connector", { scaleX: 0, duration: 0.6, stagger: 0.12, ease: "power3.inOut" }, 0.6)
          .from(".js-callout", { autoAlpha: 0, y: 12, duration: 0.5, stagger: 0.12 }, 0.85);
        // gentle parallax on the phone while the section scrolls by
        gsap.to(".js-phone-float", {
          y: -40,
          ease: "none",
          scrollTrigger: { trigger: root.current, start: "top bottom", end: "bottom top", scrub: 0.8 },
        });
      });
    },
    { scope: root },
  );

  const left = portalCallouts.slice(0, 2);
  const right = portalCallouts.slice(2);

  return (
    <section ref={root} id="portal" aria-labelledby="portal-title" className="section-pad relative overflow-hidden bg-surface">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <p className="js-fade text-eyebrow text-coral-600">Client portal</p>
          <h2 id="portal-title" className="js-heading text-section mt-5">
            What your client sees.
          </h2>
          <p className="js-fade text-lead mt-6 text-ink-muted">
            One link. Their invoice, your branding, and a Pay button. Nothing to sign up for.
          </p>
        </div>

        <div className="mt-20 grid items-center gap-12 lg:grid-cols-[1fr_auto_1fr] lg:gap-0">
          <ul className="hidden flex-col gap-32 lg:flex">
            {left.map((c) => (
              <li key={c} className="flex items-center justify-end gap-5">
                <span className="js-callout text-right text-[1.125rem] font-semibold">{c}</span>
                <span aria-hidden className="js-connector h-px w-24 origin-right bg-ink/25 xl:w-32" />
                <span aria-hidden className="-ml-5 size-2.5 shrink-0 rounded-full bg-coral-500" />
              </li>
            ))}
          </ul>

          <div className="js-phone-float relative mx-auto">
            <div aria-hidden className="absolute top-1/2 left-1/2 size-[440px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgb(242_84_91/0.18),transparent_65%)]" />
            <div className="js-phone relative">
              {hasImage ? (
                <Image src={portalImage} alt="" width={1080} height={1920} sizes="400px" className="h-[600px] w-auto max-w-none sm:h-[680px]" />
              ) : (
                <IPhone16 width={330}>
                  <ClientScreen />
                </IPhone16>
              )}
            </div>
          </div>

          <ul className="hidden flex-col gap-32 lg:flex">
            {right.map((c) => (
              <li key={c} className="flex items-center gap-5">
                <span aria-hidden className="size-2.5 shrink-0 rounded-full bg-coral-500" />
                <span aria-hidden className="js-connector -ml-5 h-px w-24 origin-left bg-ink/25 xl:w-32" />
                <span className="js-callout text-[1.125rem] font-semibold">{c}</span>
              </li>
            ))}
          </ul>

          <ul className="grid gap-4 sm:grid-cols-2 lg:hidden">
            {portalCallouts.map((c) => (
              <li key={c} className="js-card flex items-center gap-3 rounded-chip border border-line bg-white px-5 py-4 font-semibold">
                <span aria-hidden className="size-2.5 shrink-0 rounded-full bg-coral-500" /> {c}
              </li>
            ))}
          </ul>
        </div>
        <p className="sr-only">
          An iPhone shows the FlowBill payment page a client sees after opening the magic link: the freelancer&apos;s branding, the invoice for
          ₦450,000, a choice of card, transfer or USSD, a Pay button and a PDF download link.
        </p>

        {/* Crypto — coming soon */}
        <div className="js-card mt-24 grid items-center gap-10 overflow-hidden rounded-frame bg-navy-950 p-8 text-white sm:p-12 lg:mt-32 lg:grid-cols-12 lg:p-16">
          <div className="min-w-0 lg:col-span-7">
            <span className="inline-flex rounded-full border border-teal-400/40 bg-teal-400/10 px-3 py-1 text-[12px] font-semibold tracking-[0.1em] text-teal-400 uppercase">
              Coming soon
            </span>
            <h3 className="mt-6 text-[clamp(1.875rem,2.4vw+1rem,2.75rem)] leading-[1.1] font-bold tracking-[-0.025em]">Get paid in stablecoins.</h3>
            <p className="text-lead mt-4 max-w-lg text-navy-300">
              Clients abroad will be able to pay in USDT or USDC. You&apos;ll see the amount in your currency.
            </p>
            <Button type="button" onClick={() => open({ source: "crypto", crypto: true })} variant="secondary-dark" className="mt-10">
              Get crypto early access
            </Button>
          </div>
          <div className="relative min-w-0 lg:col-span-5" aria-hidden>
            <div className="mx-auto flex max-w-[320px] flex-col gap-3">
              <div className="flex items-center gap-4 rounded-card border border-navy-700 bg-navy-900 p-5">
                <span className="grid size-11 place-items-center rounded-full bg-[#50AF95] font-display text-[18px] font-bold">₮</span>
                <div className="flex-1 leading-tight">
                  <p className="font-semibold">USDT</p>
                  <p className="text-[13px] text-navy-300">≈ {formatMoney(450_000)}</p>
                </div>
                <span className="font-display text-lg font-bold tabular">290.32</span>
              </div>
              <div className="ml-8 flex items-center gap-4 rounded-card border border-navy-700 bg-navy-900 p-5">
                <span className="grid size-11 place-items-center rounded-full bg-[#2775CA] font-display text-[12px] font-bold">USDC</span>
                <div className="flex-1 leading-tight">
                  <p className="font-semibold">USDC</p>
                  <p className="text-[13px] text-navy-300">≈ {formatMoney(450_000)}</p>
                </div>
                <span className="font-display text-lg font-bold tabular">290.00</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
