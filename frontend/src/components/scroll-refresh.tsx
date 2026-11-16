"use client";

import { useEffect } from "react";
import { ScrollTrigger } from "@/lib/gsap";

/**
 * Keeps ScrollTrigger positions accurate. Sections resize after hydration (phone-sized carousel,
 * scaled hero, web fonts), which shifted the page by ~435px on mobile and made every reveal below
 * fire half a screen late. Re-measure whenever the document height changes.
 */
export function ScrollRefresh() {
  useEffect(() => {
    let timer = 0;
    let lastHeight = document.documentElement.scrollHeight;
    const refresh = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => ScrollTrigger.refresh(), 120);
    };
    const ro = new ResizeObserver(() => {
      const h = document.documentElement.scrollHeight;
      if (Math.abs(h - lastHeight) > 2) {
        lastHeight = h;
        refresh();
      }
    });
    ro.observe(document.body);
    document.fonts?.ready.then(refresh);
    window.addEventListener("load", refresh, { once: true });
    return () => {
      ro.disconnect();
      window.clearTimeout(timer);
    };
  }, []);
  return null;
}
