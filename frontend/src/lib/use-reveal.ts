"use client";

import type { RefObject } from "react";
import { gsap, MOTION, ScrollTrigger, SplitText, useGSAP } from "./gsap";

const CLEAR = "transform,translate,rotate,scale,opacity,visibility";

/** True when the element is already on screen (or above it) when animations are set up. */
const alreadySeen = (el: Element) => el.getBoundingClientRect().top < window.innerHeight * 0.98;

/** Fast flicks get a near-instant reveal so content never lags behind the thumb. */
const isFast = (st?: ScrollTrigger) => Math.abs(st?.getVelocity() ?? 0) > 1800;

/**
 * Standard section reveals (design.md §6.3):
 *  - `.js-heading` → SplitText line-mask rise
 *  - `.js-fade`    → small rise + fade
 *  - `.js-card`    → batched card reveal with stagger
 * Initial states are set here (never in CSS), so content stays visible without JS and under
 * reduced motion. Elements already on screen when this runs (late hydration on slow phones)
 * are left visible instead of hidden and re-animated.
 */
export function useReveal(scope: RefObject<HTMLElement | null>) {
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        const root = scope.current;
        if (!root) return;

        root.querySelectorAll<HTMLElement>(".js-heading").forEach((el) => {
          if (alreadySeen(el)) return;
          SplitText.create(el, {
            type: "lines",
            mask: "lines",
            linesClass: "split-line",
            autoSplit: true,
            onSplit: (self) =>
              gsap.from(self.lines, {
                yPercent: 105,
                duration: 0.6,
                stagger: 0.06,
                ease: "expo.out",
                scrollTrigger: {
                  trigger: el,
                  start: "top 94%",
                  once: true,
                  onEnter: (st) => {
                    if (isFast(st)) st.animation?.progress(1);
                  },
                },
              }),
          });
        });

        root.querySelectorAll<HTMLElement>(".js-fade").forEach((el) => {
          if (alreadySeen(el)) return;
          gsap.from(el, {
            y: 16,
            autoAlpha: 0,
            duration: 0.45,
            clearProps: CLEAR,
            scrollTrigger: {
              trigger: el,
              start: "top 96%",
              once: true,
              onEnter: (st) => {
                if (isFast(st)) st.animation?.progress(1);
              },
            },
          });
        });

        const cards = [...root.querySelectorAll<HTMLElement>(".js-card")].filter((el) => !alreadySeen(el));
        if (cards.length) {
          gsap.set(cards, { y: 24, autoAlpha: 0 });
          ScrollTrigger.batch(cards, {
            start: "top 97%",
            once: true,
            interval: 0.05,
            onEnter: (batch, triggers) => {
              const fast = isFast(triggers[0]);
              gsap.to(batch, {
                y: 0,
                autoAlpha: 1,
                stagger: fast ? 0 : 0.04,
                duration: fast ? 0.15 : 0.45,
                ease: "power3.out",
                overwrite: true,
                clearProps: CLEAR,
              });
            },
          });
        }
      });
    },
    { scope },
  );
}
