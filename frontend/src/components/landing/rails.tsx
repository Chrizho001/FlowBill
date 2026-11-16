"use client";

import Image from "next/image";
import { useRef } from "react";
import { rails } from "@/content/landing";
import { useReveal } from "@/lib/use-reveal";

/** Payment methods FlowBill supports or plans to support (owner-supplied logos). Not customer logos. */
const LOGOS = [
  { src: "/logos/paystack.png", alt: "Paystack", w: 1024, h: 181, height: 34 },
  { src: "/logos/visa.png", alt: "Visa", w: 400, h: 254, height: 56 },
  { src: "/logos/mastercard.png", alt: "Mastercard", w: 433, h: 336, height: 64 },
  { src: "/logos/opay.png", alt: "OPay", w: 503, h: 167, height: 44 },
  { src: "/logos/ussd.png", alt: "USSD", w: 334, h: 334, height: 64 },
];

export function Rails() {
  const ref = useRef<HTMLElement>(null);
  useReveal(ref);
  return (
    <section ref={ref} id="rails" aria-labelledby="rails-title" className="relative bg-surface pt-6 pb-24 md:pb-32">
      <div className="container">
        <h2 id="rails-title" className="js-fade mx-auto max-w-xl text-center font-sans text-[1rem] font-medium text-ink-muted">
          {rails.label}
        </h2>
        <ul className="mt-12 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 lg:gap-6">
          {LOGOS.map((l, i) => (
            <li
              key={l.alt}
              className={`js-card group flex h-28 items-center justify-center rounded-card border border-line bg-white px-6 shadow-[var(--shadow-card)] transition-[translate,box-shadow] duration-300 ease-[var(--ease-out-expo)] hover:-translate-y-1 hover:shadow-[var(--shadow-card-hover)] lg:h-32 ${
                i === LOGOS.length - 1 ? "col-span-2 sm:col-span-1" : ""
              }`}
            >
              <Image
                src={l.src}
                alt={l.alt}
                width={l.w}
                height={l.h}
                style={{ height: l.height, width: "auto" }}
                className="max-w-full object-contain transition-transform duration-300 ease-[var(--ease-out-expo)] group-hover:scale-105"
              />
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
