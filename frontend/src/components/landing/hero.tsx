"use client";

import { useEffect, type ReactNode } from "react";
import {
  motion,
  MotionConfig,
  useMotionValue,
  useReducedMotion,
  useSpring,
} from "framer-motion";
import { Bell, BadgeCheck, Banknote } from "lucide-react";
import { AuroraBackground } from "./aurora-background";
import { Navbar } from "./navbar";
import { WaitlistForm } from "./waitlist-form";
import { DashboardMockup } from "./dashboard-mockup";
import { FloatingCard } from "./floating-card";

/** Overlapping avatar stack — no fake logos, just warm gradient circles. */
function AvatarStack() {
  const gradients = [
    "from-emerald-400 to-teal-600",
    "from-teal-400 to-cyan-600",
    "from-lime-400 to-emerald-600",
    "from-cyan-400 to-blue-600",
    "from-emerald-500 to-green-700",
  ];
  return (
    <span className="flex -space-x-2.5">
      {gradients.map((g) => (
        <span
          key={g}
          className={`h-8 w-8 rounded-full border-2 border-void bg-gradient-to-br ${g}`}
        />
      ))}
    </span>
  );
}

/** One word of the headline, revealed in sequence. */
function HeadlineWord({
  children,
  delay,
}: {
  children: ReactNode;
  delay: number;
}) {
  return (
    <motion.span
      initial={{ opacity: 0, y: 28, filter: "blur(8px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      transition={{ delay, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      className="inline-block"
    >
      {children}
    </motion.span>
  );
}

export function Hero() {
  const reduced = useReducedMotion();

  // Shared mouse-parallax: normalized cursor position (-0.5..0.5),
  // spring-smoothed, consumed by the mockup tilt and floating cards.
  const rawMx = useMotionValue(0);
  const rawMy = useMotionValue(0);
  const mx = useSpring(rawMx, { stiffness: 55, damping: 18 });
  const my = useSpring(rawMy, { stiffness: 55, damping: 18 });

  useEffect(() => {
    if (reduced) return;
    function onMouseMove(e: MouseEvent) {
      rawMx.set(e.clientX / window.innerWidth - 0.5);
      rawMy.set(e.clientY / window.innerHeight - 0.5);
    }
    window.addEventListener("mousemove", onMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", onMouseMove);
  }, [rawMx, rawMy, reduced]);

  // Headline: "Billing that flows while you work."
  const headline: Array<{ text: string; gradient?: boolean }> = [
    { text: "Billing" },
    { text: "that" },
    { text: "flows" },
    { text: "while" },
    { text: "you" },
    { text: "work.", gradient: true },
  ];

  return (
    <MotionConfig reducedMotion="user">
      <section className="relative flex min-h-screen flex-col overflow-hidden">
        <AuroraBackground />
        <Navbar />

        <div className="container relative z-10 flex flex-1 flex-col items-center px-4 pb-16 pt-32 text-center sm:px-6 md:pt-40">
          {/* Eyebrow badge */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="inline-flex items-center gap-2.5 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 backdrop-blur-md"
          >
            <span className="animate-pulse-dot h-2 w-2 rounded-full bg-mint" />
            <span className="text-xs font-medium tracking-wide text-emerald-200/90 sm:text-sm">
              FlowBill is launching soon
            </span>
          </motion.div>

          {/* Headline */}
          <h1 className="mt-7 font-display text-[clamp(2.6rem,7.5vw,5.5rem)] font-bold leading-[1.04] tracking-tight text-white">
            {headline.map((word, i) => (
              <span key={word.text}>
                <HeadlineWord delay={0.25 + i * 0.09}>
                  {word.gradient ? (
                    <span className="text-gradient-mint">{word.text}</span>
                  ) : (
                    word.text
                  )}
                </HeadlineWord>
                {i < headline.length - 1 ? " " : ""}
              </span>
            ))}
          </h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.75, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="mt-6 max-w-xl text-balance text-base leading-relaxed text-zinc-400 sm:text-lg"
          >
            Professional invoices, global payments, and business insights —
            running on autopilot while you do the work you love.
          </motion.p>

          {/* Waitlist */}
          <motion.div
            id="waitlist"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="mt-9 w-full"
          >
            <WaitlistForm />
          </motion.div>

          {/* Social proof */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1, duration: 0.8 }}
            className="mt-6 flex items-center gap-3"
          >
            <AvatarStack />
            <p className="text-sm text-zinc-500">
              Join <span className="font-medium text-zinc-300">500+ freelancers</span> already
              waiting
            </p>
          </motion.div>

          {/* Mockup centerpiece */}
          <div className="relative mt-16 w-full sm:mt-20">
            <DashboardMockup mx={mx} my={my} />

            {/* Floating glass cards — hidden on small screens to avoid clutter */}
            <div className="hidden lg:block">
              <FloatingCard
                mx={mx}
                my={my}
                depth={1.4}
                delay={1.5}
                icon={<Banknote className="h-4 w-4" />}
                title="Payment received — $2,400.00"
                subtitle="Studio Nova · just now"
                className="-left-6 top-8 xl:-left-20"
              />
              <FloatingCard
                mx={mx}
                my={my}
                depth={0.8}
                delay={1.7}
                icon={<Bell className="h-4 w-4" />}
                title="INV-2026-0042 was paid"
                subtitle="Auto-marked · receipt sent"
                className="-right-4 top-1/3 xl:-right-16"
              />
              <FloatingCard
                mx={mx}
                my={my}
                depth={1.1}
                delay={1.9}
                icon={<BadgeCheck className="h-4 w-4" />}
                title="New client — Bright Labs"
                subtitle="Recurring invoice scheduled"
                className="-left-2 bottom-10 xl:-left-12"
              />
            </div>
          </div>

          {/* Scroll cue */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.2, duration: 0.8 }}
            className="mt-14 hidden flex-col items-center gap-2 text-zinc-600 md:flex"
            aria-hidden
          >
            <span className="text-[11px] uppercase tracking-[0.2em]">Scroll</span>
            <span className="animate-scroll-cue block h-8 w-px bg-gradient-to-b from-emerald-400/60 to-transparent" />
          </motion.div>
        </div>
      </section>
    </MotionConfig>
  );
}
