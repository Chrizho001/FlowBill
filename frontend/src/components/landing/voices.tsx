"use client";

import { ArrowLeft, ArrowRight, Pause, Play, Quote } from "lucide-react";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { founderNote, testimonials, type Testimonial } from "@/content/landing";
import { gsap, MOTION, ScrollTrigger, SplitText, useGSAP } from "@/lib/gsap";
import { useReveal } from "@/lib/use-reveal";
import { cn } from "@/lib/utils";
import { useWaitlist } from "./waitlist-modal";

/**
 * Testimonial carousel (design.md §3.7). Items are SAMPLES with generated portraits: they show in
 * development, or in production only with NEXT_PUBLIC_SHOW_SAMPLE_TESTIMONIALS=true. Otherwise the
 * founder's note renders in the same card.
 */
const showSamples =
  process.env.NODE_ENV !== "production" ||
  process.env.NEXT_PUBLIC_SHOW_SAMPLE_TESTIMONIALS === "true";
const AUTOPLAY_S = 7;

function Portrait({
  t,
  has,
  className,
  sizes,
}: {
  t: Testimonial;
  has: boolean;
  className?: string;
  sizes: string;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden bg-gradient-to-br from-navy-700 to-navy-900",
        className,
      )}
    >
      {has ? (
        <Image
          src={t.photo}
          alt={`Portrait of ${t.name}`}
          fill
          sizes={sizes}
          className="object-cover"
        />
      ) : (
        <span className="absolute inset-0 grid place-items-center font-display text-5xl font-bold text-white/90">
          {t.initials}
        </span>
      )}
    </div>
  );
}

export function Voices({ photos }: { photos: Record<string, boolean> }) {
  const root = useRef<HTMLElement>(null);
  const card = useRef<HTMLDivElement>(null);
  const timer = useRef<gsap.core.Tween | null>(null);
  const first = useRef(true);
  const items = testimonials.filter((t) => !t.isSample || showSamples);
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [hover, setHover] = useState(false);
  const [inView, setInView] = useState(false);
  const { open } = useWaitlist();
  useReveal(root);

  const n = items.length;
  const go = useCallback((i: number) => setActive(((i % n) + n) % n), [n]);

  /* In-view tracking for autoplay. */
  useGSAP(
    () => {
      ScrollTrigger.create({
        trigger: root.current,
        start: "top 75%",
        end: "bottom 25%",
        onToggle: (s) => setInView(s.isActive),
      });
    },
    { scope: root },
  );

  /* Slide transition: portrait wipes in, quote lines rise, meta fades. */
  useGSAP(
    () => {
      if (first.current) {
        first.current = false;
        return;
      }
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        const split = SplitText.create(".js-quote", {
          type: "lines",
          mask: "lines",
          linesClass: "split-line",
        });
        const tl = gsap.timeline({ defaults: { ease: "expo.out" } });
        tl.fromTo(
          ".js-portrait",
          { clipPath: "inset(100% 0% 0% 0%)" },
          { clipPath: "inset(0% 0% 0% 0%)", duration: 0.9 },
          0,
        )
          .fromTo(
            ".js-portrait img",
            { scale: 1.15 },
            { scale: 1, duration: 1.2 },
            0,
          )
          .from(
            split.lines,
            { yPercent: 105, stagger: 0.06, duration: 0.8 },
            0.1,
          )
          .from(".js-meta", { autoAlpha: 0, y: 10, duration: 0.5 }, 0.35);
        return () => split.revert();
      });
    },
    { dependencies: [active], scope: card },
  );

  /* Autoplay with pause (WCAG 2.2.2): pauses on hover/focus, off-screen, or by the button. */
  useEffect(() => {
    timer.current?.kill();
    if (
      n < 2 ||
      !playing ||
      hover ||
      !inView ||
      window.matchMedia(MOTION.reduce).matches
    )
      return;
    timer.current = gsap.delayedCall(AUTOPLAY_S, () =>
      go(active + 1),
    ) as unknown as gsap.core.Tween;
    return () => {
      timer.current?.kill();
    };
  }, [active, playing, hover, inView, n, go]);

  const t = items[active];
  const navBtn =
    "grid size-12 place-items-center rounded-full border-[1.5px] transition-[background-color,border-color,color,translate] duration-300";

  return (
    <section
      ref={root}
      id="voices"
      aria-labelledby="voices-title"
      className="section-pad relative overflow-hidden bg-white"
    >
      <div className="container grid items-center gap-16 lg:grid-cols-12 lg:gap-8">
        <div className="lg:col-span-5">
          <p className="js-fade text-eyebrow text-coral-600">Why FlowBill</p>
          <h2 id="voices-title" className="js-heading text-section mt-5">
            Built with freelancers, for freelancers.
          </h2>
          <p className="js-fade text-lead mt-6 max-w-md text-ink-muted">
            Designers, developers, writers and agencies across Africa helped
            shape how FlowBill gets them paid.
          </p>
          <div className="js-fade mt-10">
            <Button
              size="lg"
              className="px-9"
              onClick={() => open({ source: "voices" })}
            >
              Get early access
            </Button>
          </div>
        </div>

        <div className="relative lg:col-span-7 lg:pl-8">
          {/* Decorations from the inspiration: coral circle + navy hexagon */}
          <div
            aria-hidden
            className="absolute -top-10 -left-4 size-32 rounded-full bg-coral-400/35 sm:-top-12 sm:left-0 sm:size-40"
          />
          <div
            aria-hidden
            className="absolute -right-1 top-[46%] size-12 bg-navy-900 [clip-path:polygon(25%_5%,75%_5%,100%_50%,75%_95%,25%_95%,0_50%)] sm:right-4"
          />

          {t ? (
            <div
              ref={card}
              className="relative"
              onMouseEnter={() => setHover(true)}
              onMouseLeave={() => setHover(false)}
              onFocus={() => setHover(true)}
              onBlur={() => setHover(false)}
            >
              <div className="relative">
                {/* Stacked cards behind for depth */}
                <div
                  aria-hidden
                  className="absolute inset-0 translate-x-3 translate-y-4 rotate-[1.5deg] rounded-[28px] bg-coral-100/80"
                />
                <div
                  aria-hidden
                  className="absolute inset-0 translate-x-6 translate-y-8 rotate-[3deg] rounded-[28px] bg-surface shadow-[var(--shadow-card)]"
                />

                <figure
                  className="js-card relative grid gap-8 rounded-[28px] border border-line bg-white p-6 shadow-[0_40px_80px_-30px_rgb(20_28_66/0.28)] sm:grid-cols-[200px_1fr] sm:p-10"
                  aria-roledescription="slide"
                  aria-label={`${active + 1} of ${n}`}
                >
                  <Portrait
                    t={t}
                    has={!!photos[t.photo]}
                    sizes="(min-width: 640px) 200px, 100vw"
                    className="js-portrait aspect-[4/5] w-full max-w-[220px] rounded-[20px] sm:w-[200px]"
                  />
                  <div className="flex flex-col">
                    <Quote
                      className="size-9 fill-coral-500 text-coral-500"
                      aria-hidden
                    />
                    <blockquote
                      key={active}
                      className="js-quote mt-5 font-display text-[clamp(1.25rem,1.1vw+0.9rem,1.625rem)] leading-[1.4] font-medium tracking-[-0.01em] text-ink"
                    >
                      “{t.quote}”
                    </blockquote>
                    <figcaption className="js-meta mt-auto flex items-center justify-between gap-4 pt-8">
                      <span>
                        <span className="block text-[1.0625rem] font-bold">
                          {t.name}
                        </span>
                        <span className="block text-[0.9375rem] text-ink-muted">
                          {t.role} · {t.location}
                        </span>
                      </span>
                      <span className="font-display text-[0.9375rem] text-ink-muted tabular">
                        {String(active + 1).padStart(2, "0")} /{" "}
                        {String(n).padStart(2, "0")}
                      </span>
                    </figcaption>
                  </div>
                </figure>
              </div>

              {/* Controls */}
              <div className="relative mt-12 flex flex-wrap items-center justify-between gap-6">
                <div
                  className="flex -space-x-3"
                  role="tablist"
                  aria-label="Choose a testimonial"
                >
                  {items.map((it, i) => (
                    <button
                      key={it.name}
                      type="button"
                      role="tab"
                      aria-selected={i === active}
                      aria-label={it.name}
                      onClick={() => go(i)}
                      className={cn(
                        "relative size-12 overflow-hidden rounded-full border-[3px] border-white transition-[translate,box-shadow] duration-300 hover:-translate-y-1",
                        i === active
                          ? "z-10 shadow-[0_0_0_2px_var(--color-coral-500)]"
                          : "opacity-70 hover:opacity-100",
                      )}
                    >
                      <Portrait
                        t={it}
                        has={!!photos[it.photo]}
                        sizes="48px"
                        className="absolute inset-0 [&_span]:text-[13px]"
                      />
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setPlaying((p) => !p)}
                    aria-label={
                      playing ? "Pause testimonials" : "Play testimonials"
                    }
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
                    aria-label="Previous testimonial"
                    className={cn(
                      navBtn,
                      "border-ink/15 text-ink hover:-translate-x-0.5 hover:border-ink",
                    )}
                  >
                    <ArrowLeft className="size-5" aria-hidden />
                  </button>
                  <button
                    type="button"
                    onClick={() => go(active + 1)}
                    aria-label="Next testimonial"
                    className={cn(
                      navBtn,
                      "border-ink bg-ink text-white hover:translate-x-0.5 hover:bg-navy-800",
                    )}
                  >
                    <ArrowRight className="size-5" aria-hidden />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <figure className="js-card relative rounded-[28px] border border-line bg-white p-8 shadow-[0_40px_80px_-30px_rgb(20_28_66/0.28)] sm:p-12">
              <Quote
                className="size-10 fill-coral-500 text-coral-500"
                aria-hidden
              />
              <blockquote className="mt-6 font-display text-[clamp(1.5rem,1.4vw+1rem,2rem)] leading-[1.35] font-medium tracking-[-0.015em]">
                {founderNote.quote}
              </blockquote>
              <figcaption className="mt-8 text-ink-muted">
                <span className="font-bold text-ink">{founderNote.name}</span> ·{" "}
                {founderNote.role}
              </figcaption>
            </figure>
          )}
        </div>
      </div>
    </section>
  );
}
