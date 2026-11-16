"use client";

import { useRef } from "react";
import { finalCta } from "@/content/landing";
import { gsap, MOTION, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";
import { Button } from "@/components/ui/button";
import { useWaitlist } from "./waitlist-modal";

export function FinalCta() {
  const root = useRef<HTMLElement>(null);
  const { open } = useWaitlist();
  useReveal(root);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        gsap.to(".js-drift", { x: -30, y: 20, duration: 8, ease: "sine.inOut", yoyo: true, repeat: -1 });
        gsap.from(".js-drift", {
          scale: 0.6,
          autoAlpha: 0,
          duration: 1.4,
          ease: "expo.out",
          scrollTrigger: { trigger: root.current, start: "top 70%", once: true },
        });
      });
    },
    { scope: root },
  );

  return (
    <section ref={root} id="join" aria-labelledby="join-title" className="relative isolate overflow-hidden bg-navy-950 text-white">
      <div aria-hidden className="js-drift blob -right-40 -bottom-44 -z-10 size-[380px] opacity-90 lg:top-1/2 lg:bottom-auto lg:-right-32 lg:size-[720px] lg:-translate-y-1/2" />
      <div aria-hidden className="absolute inset-0 -z-10 opacity-[0.06] [background-image:radial-gradient(#A9B3D9_1px,transparent_1px)] [background-size:28px_28px]" />
      <div className="container flex min-h-[100svh] flex-col justify-center py-32">
        <div className="relative max-w-5xl">
          <p className="js-fade text-eyebrow text-coral-400">Early access</p>
          <h2
            id="join-title"
            className="js-heading mt-6 text-[clamp(2.75rem,5.6vw+0.5rem,5.25rem)] leading-[1.02] font-bold tracking-[-0.04em]"
          >
            {finalCta.titleLine1}
            <br />
            {finalCta.titleLine2}
          </h2>
          <p className="js-fade text-lead mt-8 max-w-xl text-navy-300">{finalCta.lead}</p>
          <div className="js-fade mt-12">
            <Button size="lg" className="px-9" onClick={() => open({ source: "join" })}>
              Get early access
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
