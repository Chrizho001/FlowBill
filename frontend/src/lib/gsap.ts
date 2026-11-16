"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";
import { useGSAP } from "@gsap/react";

if (typeof window !== "undefined") {
  gsap.registerPlugin(useGSAP, ScrollTrigger, SplitText);
  gsap.defaults({ ease: "power3.out", duration: 0.6 });
}

/** Media-query conditions shared by every animated section (design.md §6.1). */
export const MOTION = {
  ok: "(prefers-reduced-motion: no-preference)",
  reduce: "(prefers-reduced-motion: reduce)",
  pinOk: "(prefers-reduced-motion: no-preference) and (min-width: 768px)",
  pinOff: "(prefers-reduced-motion: no-preference) and (max-width: 767px)",
  hover: "(prefers-reduced-motion: no-preference) and (hover: hover) and (pointer: fine)",
} as const;

export { gsap, ScrollTrigger, SplitText, useGSAP };
