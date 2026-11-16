"use client";

import type { RefObject } from "react";
import { gsap, MOTION, ScrollTrigger, SplitText, useGSAP } from "./gsap";

/**
 * Standard section reveals (design.md §6.3):
 *  - `.js-heading` → SplitText line-mask rise
 *  - `.js-fade`    → small rise + fade
 *  - `.js-card`    → batched card reveal with stagger
 * Initial states are set here (never in CSS), so content stays visible without JS
 * and under reduced motion.
 */
export function useReveal(scope: RefObject<HTMLElement | null>) {
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        const root = scope.current;
        if (!root) return;

        root.querySelectorAll<HTMLElement>(".js-heading").forEach((el) => {
          SplitText.create(el, {
            type: "lines",
            mask: "lines",
            linesClass: "split-line",
            autoSplit: true,
            onSplit: (self) =>
              gsap.from(self.lines, {
                yPercent: 105,
                duration: 0.9,
                stagger: 0.1,
                ease: "expo.out",
                scrollTrigger: { trigger: el, start: "top 82%", once: true },
              }),
          });
        });

        root.querySelectorAll<HTMLElement>(".js-fade").forEach((el) => {
          gsap.from(el, {
            y: 24,
            autoAlpha: 0,
            duration: 0.8,
            clearProps: "transform,translate,rotate,scale,opacity,visibility",
            scrollTrigger: { trigger: el, start: "top 85%", once: true },
          });
        });

        const cards = root.querySelectorAll<HTMLElement>(".js-card");
        if (cards.length) {
          gsap.set(cards, { y: 40, autoAlpha: 0 });
          ScrollTrigger.batch(cards, {
            start: "top 88%",
            once: true,
            onEnter: (batch) =>
              gsap.to(batch, {
                y: 0,
                autoAlpha: 1,
                stagger: 0.08,
                duration: 0.75,
                ease: "power3.out",
                overwrite: true,
                clearProps: "transform,translate,rotate,scale,opacity,visibility",
              }),
          });
        }
      });
    },
    { scope },
  );
}
