"use client";

import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { hero } from "@/content/landing";
import { gsap, MOTION, ScrollTrigger, useGSAP } from "@/lib/gsap";
import { formatCompact } from "@/lib/utils";
import { HeroDashboard, STAGE_H, STAGE_W } from "./hero-dashboard";
import { openWaitlistAttrs, useWaitlist } from "./waitlist-modal";

/* Small grey "moons" drifting in the navy field, as in the inspiration. Positions in %. */
const MOONS = [
  { top: 9, left: 57, size: 34 },
  { top: 19, left: 47, size: 54 },
  { top: 15, left: 66, size: 84 },
  { top: 50, left: 45, size: 112 },
  { top: 70, left: 52, size: 22 },
  { top: 30, left: 88, size: 40 },
  { top: 78, left: 8, size: 30 },
  { top: 12, left: 22, size: 18 },
];

export function Hero() {
  const root = useRef<HTMLElement>(null);
  const frame = useRef<HTMLDivElement>(null);
  const idle = useRef<gsap.core.Timeline | null>(null);
  const pausedRef = useRef(false);
  const [paused, setPaused] = useState(false);
  const [scale, setScale] = useState(1);
  const { open } = useWaitlist();

  /* Scale the stage to its column; it is allowed to bleed past the right edge like the inspiration. */
  useEffect(() => {
    const el = frame.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setScale(Math.max(0.42, Math.min(1, entry.contentRect.width / 680)));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        const tl = gsap.timeline({ defaults: { ease: "expo.out", duration: 1 } });
        tl.from(".js-h1-line", { yPercent: 110, stagger: 0.12, duration: 1.1 }, 0.1)
          .from(".js-lead", { autoAlpha: 0, y: 20 }, 0.45)
          .from(".js-cta", { autoAlpha: 0, y: 20, clearProps: "transform,translate,opacity,visibility" }, 0.6)
          .from(".js-moon", { autoAlpha: 0, scale: 0.4, stagger: 0.05, duration: 1.4 }, 0.2)
          .from(".js-dash", { autoAlpha: 0, x: 120, duration: 1.3 }, 0.35)
          .from(".js-dcard", { autoAlpha: 0, y: 24, stagger: 0.1, duration: 0.8 }, 0.75)
          .from(".js-drow", { autoAlpha: 0, x: 30, stagger: 0.07, duration: 0.7 }, 0.9)
          .from(".js-float-a", { autoAlpha: 0, y: 50, duration: 1 }, 0.7)
          .from(".js-float-b", { autoAlpha: 0, y: 60, duration: 1 }, 0.85)
          .from(".js-fill", { scaleX: 0, transformOrigin: "left center", stagger: 0.08, duration: 0.9, ease: "power3.inOut" }, 1.2)
          .from(".js-knob", { left: "0%", stagger: 0.08, duration: 0.9, ease: "power3.inOut" }, 1.2)
          .fromTo(".js-spark", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1.4, ease: "power2.inOut" }, 1.1);

        root.current?.querySelectorAll<HTMLElement>(".js-count").forEach((el) => {
          const o = { v: 0 };
          tl.to(o, { v: Number(el.dataset.value), duration: 1.4, ease: "power2.out", onUpdate: () => void (el.textContent = formatCompact(o.v)) }, 0.9);
        });

        // Idle drift: moons hover, cards float. Pausable; pauses off-screen.
        const drift = gsap.timeline({ paused: true });
        root.current?.querySelectorAll<HTMLElement>(".js-moon").forEach((m, i) => {
          drift.to(
            m,
            {
              x: gsap.utils.random(-18, 18),
              y: gsap.utils.random(-22, 22),
              duration: gsap.utils.random(5, 9),
              ease: "sine.inOut",
              yoyo: true,
              repeat: -1,
            },
            i * 0.2,
          );
        });
        drift.to(".js-float-a", { y: -10, duration: 3.2, ease: "sine.inOut", yoyo: true, repeat: -1 }, 0);
        drift.to(".js-float-b", { y: 9, duration: 3.8, ease: "sine.inOut", yoyo: true, repeat: -1 }, 0.4);
        idle.current = drift;
        tl.eventCallback("onComplete", () => {
          if (!pausedRef.current) drift.play();
        });
        // Slow phones hydrate late: the hero is already visible, so don't hide and replay it.
        if (performance.now() > 1500) tl.progress(1);

        ScrollTrigger.create({
          trigger: root.current,
          start: "top top",
          end: "bottom top",
          onToggle: (self) => {
            if (pausedRef.current) return;
            if (self.isActive) drift.play();
            else drift.pause();
          },
        });

        gsap.to(".js-stage", {
          y: -50,
          ease: "none",
          scrollTrigger: { trigger: root.current, start: "top top", end: "bottom top", scrub: 0.6 },
        });

        return () => {
          idle.current = null;
        };
      });
    },
    { scope: root },
  );

  function togglePause() {
    const next = !pausedRef.current;
    pausedRef.current = next;
    setPaused(next);
    if (next) idle.current?.pause();
    else idle.current?.play();
  }

  return (
    <section id="hero" ref={root} aria-labelledby="hero-title" className="relative isolate overflow-hidden bg-surface">
      {/* Navy field with the inspiration's diagonal bottom edge */}
      <div
        aria-hidden
        className="absolute inset-0 -z-10 bg-navy-900 [clip-path:polygon(0_0,100%_0,100%_86%,0_100%)] lg:[clip-path:polygon(0_0,100%_0,100%_70%,0_96%)]"
      >
        {MOONS.map((m, i) => (
          <span
            key={i}
            className={`js-moon absolute rounded-full ${m.size > 60 ? "hidden lg:block" : ""} bg-[radial-gradient(circle_at_32%_30%,rgb(255_255_255/0.16),rgb(255_255_255/0.05)_62%,rgb(255_255_255/0.03))]`}
            style={{ top: `${m.top}%`, left: `${m.left}%`, width: m.size, height: m.size }}
          />
        ))}
      </div>

      <div className="container grid min-h-[100svh] grid-cols-1 content-center items-center gap-14 pt-32 pb-24 lg:grid-cols-12 lg:gap-8 lg:pt-28 lg:pb-40">
        <div className="relative z-10 lg:col-span-6">
          <h1
            id="hero-title"
            className="font-display text-[clamp(2rem,8.4vw,3.25rem)] leading-[1.08] font-bold tracking-[-0.03em] text-white lg:text-[clamp(2.75rem,4.2vw,4rem)]"
          >
            <span className="block overflow-clip pb-[0.06em]">
              <span className="js-h1-line block whitespace-nowrap">{hero.titleLine1}</span>
            </span>
            <span className="block overflow-clip pb-[0.06em]">
              <span className="js-h1-line block whitespace-nowrap">{hero.titleLine2}</span>
            </span>
          </h1>
          <p className="js-lead mt-6 max-w-[30rem] text-[1.0625rem] leading-relaxed text-navy-300 sm:text-[1.125rem]">{hero.lead}</p>
          <div className="js-cta mt-10">
            <Button size="lg" className="px-9" {...openWaitlistAttrs} onClick={() => open({ source: "hero" })}>
              {hero.cta}
            </Button>
          </div>
        </div>

        <div ref={frame} className="relative lg:col-span-6 lg:-ml-10">
          <div className="js-stage relative" style={{ height: STAGE_H * scale }}>
            <div
              className="absolute top-0 left-0 origin-top-left"
              style={{ width: STAGE_W, height: STAGE_H, transform: `scale(${scale})` }}
              aria-hidden
            >
              <HeroDashboard />
            </div>
          </div>
          <p className="sr-only">
            FlowBill dashboard showing total earned and pending amounts, a list of clients with invoices billed, a payment card for
            Adaeze Studio and a new invoice being built.
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={togglePause}
        className="absolute right-5 bottom-5 hidden size-11 place-items-center rounded-full border border-line bg-white/80 text-ink-muted backdrop-blur transition-colors hover:text-ink motion-safe:grid sm:right-8 sm:bottom-8"
        aria-label={paused ? "Play background animation" : "Pause background animation"}
        aria-pressed={paused}
      >
        {paused ? <Play className="size-4" aria-hidden /> : <Pause className="size-4" aria-hidden />}
      </button>
    </section>
  );
}
