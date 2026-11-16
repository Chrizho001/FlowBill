"use client";

import { ArrowLeft, ArrowRight, Pause, Play } from "lucide-react";
import Image from "next/image";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { IPhone16 } from "@/components/ui/iphone16";
import { steps } from "@/content/landing";
import { gsap, MOTION, ScrollTrigger, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";
import { cn } from "@/lib/utils";
import {
  ClientScreen,
  CreateScreen,
  PaidScreen,
  SendScreen,
} from "./app-screens";

export type StepKey = (typeof steps)[number]["key"];
const SCREENS: Record<StepKey, () => ReactNode> = {
  create: CreateScreen,
  send: SendScreen,
  client: ClientScreen,
  paid: PaidScreen,
};
const AUTOPLAY_S = 6;
const N = steps.length;

/** Shortest circular offset of slide i from the active slide (…, -1, 0, 1, …). */
const offsetOf = (i: number, active: number) =>
  ((i - active + N + Math.floor(N / 2)) % N) - Math.floor(N / 2);

export function HowItWorks({
  images,
}: {
  images: Partial<Record<StepKey, boolean>>;
}) {
  const root = useRef<HTMLElement>(null);
  const slides = useRef<(HTMLDivElement | null)[]>([]);
  const fills = useRef<(HTMLSpanElement | null)[]>([]);
  const autoplay = useRef<gsap.core.Tween | null>(null);
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [inView, setInView] = useState(false);
  const [phoneW, setPhoneW] = useState(300);
  useReveal(root);

  const go = useCallback((i: number) => setActive(((i % N) + N) % N), []);

  /* Phone size follows the viewport. */
  useEffect(() => {
    const onResize = () =>
      setPhoneW(
        window.innerWidth < 640 ? 240 : window.innerWidth < 1024 ? 270 : 300,
      );
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  /* Lay slides out around the active one (coverflow). */
  const layout = useCallback(
    (animate: boolean) => {
      const reduce = window.matchMedia(MOTION.reduce).matches;
      const gap = phoneW * (window.innerWidth < 640 ? 0.9 : 1.08);
      slides.current.forEach((el, i) => {
        if (!el) return;
        const off = offsetOf(i, active);
        const far = Math.abs(off) > 1;
        const vars = {
          x: off * gap,
          y: off === 0 ? 0 : 36,
          scale: off === 0 ? 1 : 0.8,
          rotate: off * 2.5,
          autoAlpha: off === 0 ? 1 : far ? 0 : 0.5,
          zIndex: 10 - Math.abs(off),
        };
        if (!animate || reduce || far) gsap.set(el, vars);
        else
          gsap.to(el, {
            ...vars,
            duration: 0.9,
            ease: "expo.out",
            overwrite: "auto",
          });
      });

      // The active screen comes alive
      const cur = slides.current[active];
      if (cur && animate && !reduce) {
        const sx = cur.querySelectorAll(".js-sx");
        const checks = cur.querySelectorAll(".js-check");
        if (sx.length)
          gsap.fromTo(
            sx,
            { y: 18, autoAlpha: 0 },
            {
              y: 0,
              autoAlpha: 1,
              duration: 0.6,
              stagger: 0.07,
              delay: 0.25,
              ease: "power3.out",
              overwrite: "auto",
            },
          );
        if (checks.length)
          gsap.fromTo(
            checks,
            { scale: 0, rotate: -45 },
            {
              scale: 1,
              rotate: 0,
              duration: 0.7,
              delay: 0.3,
              ease: "back.out(2.2)",
            },
          );
      }
    },
    [active, phoneW],
  );

  useEffect(() => layout(true), [layout]);

  /* Section entrance + in-view tracking. */
  useGSAP(
    () => {
      ScrollTrigger.create({
        trigger: root.current,
        start: "top 70%",
        end: "bottom 20%",
        onToggle: (self) => setInView(self.isActive),
      });
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        gsap.from(".js-stage", {
          y: 90,
          autoAlpha: 0,
          duration: 1.2,
          ease: "expo.out",
          clearProps: "transform,translate,opacity,visibility",
          scrollTrigger: { trigger: ".js-stage", start: "top 85%", once: true },
        });
      });
    },
    { scope: root },
  );

  /* Autoplay: the active tab's progress bar fills, then advances. */
  useEffect(() => {
    fills.current.forEach(
      (f, i) => f && gsap.set(f, { scaleX: i === active ? 0 : 0 }),
    );
    autoplay.current?.kill();
    const reduce = window.matchMedia(MOTION.reduce).matches;
    const fill = fills.current[active];
    if (!fill) return;
    if (reduce || !playing || !inView) {
      gsap.set(fill, { scaleX: reduce || !playing ? 1 : 0 });
      return;
    }
    autoplay.current = gsap.fromTo(
      fill,
      { scaleX: 0 },
      {
        scaleX: 1,
        duration: AUTOPLAY_S,
        ease: "none",
        onComplete: () => go(active + 1),
      },
    );
    return () => {
      autoplay.current?.kill();
    };
  }, [active, playing, inView, go]);

  /* Swipe / drag. */
  const startX = useRef<number | null>(null);
  const onPointerDown = (e: React.PointerEvent) => {
    startX.current = e.clientX;
  };
  const onPointerUp = (e: React.PointerEvent) => {
    if (startX.current == null) return;
    const dx = e.clientX - startX.current;
    startX.current = null;
    if (Math.abs(dx) > 40) go(active + (dx < 0 ? 1 : -1));
  };

  const stageH = Math.round(phoneW * 2.06) + 60;
  const step = steps[active];
  const arrowBtn =
    "grid size-12 place-items-center rounded-full border-[1.5px] border-ink/15 text-ink transition-[translate,border-color,background-color,color] duration-300 hover:border-ink hover:bg-ink hover:text-white";

  return (
    <section
      ref={root}
      id="how-it-works"
      aria-labelledby="how-title"
      className="section-pad relative overflow-hidden bg-white"
    >
      <div className="container">
        <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <p className="js-fade text-eyebrow text-coral-600">How it works</p>
            <h2 id="how-title" className="js-heading text-section mt-5">
              From draft to paid in four steps.
            </h2>
          </div>
          <div className="js-fade flex items-center gap-3">
            <button
              type="button"
              onClick={() => setPlaying((p) => !p)}
              aria-label={playing ? "Pause autoplay" : "Play autoplay"}
              aria-pressed={!playing}
              className="grid size-12 place-items-center rounded-full text-ink-muted transition-colors hover:bg-surface hover:text-ink"
            >
              {playing ? (
                <Pause className="size-4" aria-hidden />
              ) : (
                <Play className="size-4" aria-hidden />
              )}
            </button>
            <button
              type="button"
              onClick={() => go(active - 1)}
              aria-label="Previous step"
              className={cn(arrowBtn, "hover:-translate-x-0.5")}
            >
              <ArrowLeft className="size-5" aria-hidden />
            </button>
            <button
              type="button"
              onClick={() => go(active + 1)}
              aria-label="Next step"
              className={cn(arrowBtn, "hover:translate-x-0.5")}
            >
              <ArrowRight className="size-5" aria-hidden />
            </button>
          </div>
        </div>

        {/* Stage */}
        <div
          className="js-stage relative mt-16 touch-pan-y select-none lg:mt-20"
          style={{ height: stageH }}
          onPointerDown={onPointerDown}
          onPointerUp={onPointerUp}
          role="group"
          aria-roledescription="carousel"
          aria-label="FlowBill in four steps"
        >
          <div
            aria-hidden
            className="absolute top-[42%] left-1/2 size-[min(620px,95vw)] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgb(242_84_91/0.13),transparent_65%)]"
          />
          {steps.map((s, i) => {
            const Screen = SCREENS[s.key];
            return (
              <div
                key={s.key}
                ref={(el) => {
                  slides.current[i] = el;
                }}
                className="absolute top-0 left-1/2 cursor-grab will-change-transform active:cursor-grabbing"
                style={{ marginLeft: images[s.key] ? -Math.round((phoneW * 2.06 * 9) / 16) / 2 : -phoneW / 2 }}
                aria-hidden={i !== active}
                onClick={() => i !== active && go(i)}
              >
                {images[s.key] ? (
                  <Image
                    src={s.image}
                    alt=""
                    width={1080}
                    height={1920}
                    sizes="(min-width: 1024px) 340px, 280px"
                    style={{ height: Math.round(phoneW * 2.06), width: "auto", maxWidth: "none" }}
                    draggable={false}
                  />
                ) : (
                  <IPhone16 width={phoneW}>
                    <Screen />
                  </IPhone16>
                )}
              </div>
            );
          })}
          <p className="sr-only" aria-live="polite">
            Step {active + 1} of {N}: {step.title}. {step.body}
          </p>
        </div>

        {/* Step tabs */}
        <div
          role="tablist"
          aria-label="Steps"
          className="mt-14 hidden grid-cols-4 gap-8 md:grid"
        >
          {steps.map((s, i) => (
            <button
              key={s.key}
              type="button"
              role="tab"
              aria-selected={i === active}
              onClick={() => go(i)}
              className="group text-left"
            >
              <span className="relative block h-[3px] overflow-hidden rounded-full bg-line">
                <span
                  ref={(el) => {
                    fills.current[i] = el;
                  }}
                  className="absolute inset-0 origin-left scale-x-0 rounded-full bg-coral-500"
                />
              </span>
              <span className="mt-6 flex items-baseline gap-3">
                <span className="font-display text-[0.9375rem] font-medium text-coral-600 tabular">
                  {s.index}
                </span>
                <span
                  className={cn(
                    "font-display text-[1.5rem] font-bold tracking-tight transition-colors duration-300",
                    i === active
                      ? "text-ink"
                      : "text-ink/35 group-hover:text-ink/70",
                  )}
                >
                  {s.title}
                </span>
              </span>
              <span
                className={cn(
                  "mt-2 block text-[0.9375rem] leading-relaxed transition-colors duration-300",
                  i === active ? "text-ink-muted" : "text-ink-muted/50",
                )}
              >
                {s.body}
              </span>
            </button>
          ))}
        </div>

        {/* Mobile caption + dots */}
        <div className="mt-10 text-center md:hidden">
          <p className="font-display text-[1.5rem] font-bold tracking-tight">
            <span className="mr-2 text-[1rem] font-medium text-coral-600">
              {step.index}
            </span>
            {step.title}
          </p>
          <p className="mx-auto mt-2 max-w-sm text-ink-muted">{step.body}</p>
          <div className="mt-6 flex justify-center">
            {steps.map((s, i) => (
              <button
                key={s.key}
                type="button"
                onClick={() => go(i)}
                aria-label={`Step ${i + 1}: ${s.title}`}
                aria-current={i === active}
                className="grid size-11 place-items-center"
              >
                <span
                  className={cn(
                    "block h-2 rounded-full transition-all duration-300",
                    i === active ? "w-7 bg-coral-500" : "w-2 bg-ink/20",
                  )}
                />
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
