"use client";

import { Plus } from "lucide-react";
import { useRef } from "react";
import { faqs, footer } from "@/content/landing";
import { gsap, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";

export function Faq() {
  const root = useRef<HTMLElement>(null);
  useReveal(root);

  /* Native <details>, with GSAP animating the panel height (design.md §3.9). */
  const { contextSafe } = useGSAP({ scope: root });

  const onToggle = contextSafe((e: React.MouseEvent<HTMLElement>) => {
    const details = e.currentTarget.parentElement as HTMLDetailsElement;
    const panel = details.querySelector<HTMLElement>(".js-panel");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!panel || reduce) return;
    e.preventDefault();
    if (details.open) {
      gsap.to(panel, {
        height: 0,
        autoAlpha: 0,
        duration: 0.35,
        ease: "power2.inOut",
        onComplete: () => {
          details.open = false;
          gsap.set(panel, { clearProps: "height,opacity,visibility" });
        },
      });
    } else {
      details.open = true;
      gsap.fromTo(panel, { height: 0, autoAlpha: 0 }, { height: "auto", autoAlpha: 1, duration: 0.45, ease: "power3.out" });
    }
  });

  return (
    <section ref={root} id="faq" aria-labelledby="faq-title" className="section-pad bg-white">
      <div className="container grid gap-14 lg:grid-cols-12 lg:gap-8">
        <div className="lg:col-span-4">
          <p className="js-fade text-eyebrow text-coral-600">FAQ</p>
          <h2 id="faq-title" className="js-heading text-section mt-5">
            Questions, answered.
          </h2>
          <p className="js-fade text-lead mt-6 text-ink-muted">
            Still curious?{" "}
            <a href={`mailto:${footer.email}`} className="link-draw font-medium text-ink">
              Email us
            </a>
            .
          </p>
        </div>

        <ul className="border-t border-line lg:col-span-7 lg:col-start-6">
          {faqs.map((f) => (
            <li key={f.q} className="js-card border-b border-line">
              <details className="group">
                <summary
                  onClick={onToggle}
                  className="flex min-h-11 cursor-pointer items-center justify-between gap-6 py-7 text-left font-display text-[1.25rem] font-medium tracking-[-0.01em] transition-colors hover:text-coral-600 sm:text-[1.375rem]"
                >
                  {f.q}
                  <span className="grid size-10 shrink-0 place-items-center rounded-full border border-line transition-[rotate,background-color,border-color] duration-300 group-open:rotate-45 group-open:border-navy-900 group-open:bg-navy-900 group-open:text-white">
                    <Plus className="size-4" aria-hidden />
                  </span>
                </summary>
                <div className="js-panel overflow-hidden">
                  <p className="max-w-[60ch] pr-14 pb-8 text-[1.0625rem] leading-relaxed text-ink-muted">{f.a}</p>
                </div>
              </details>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
