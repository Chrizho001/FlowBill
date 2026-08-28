"use client";

import type { ReactNode } from "react";
import { motion, useSpring, useTransform, type MotionValue } from "framer-motion";

/**
 * A glass card floating near the dashboard mockup. Reacts to the hero's
 * shared mouse-parallax with a depth multiplier (further layers move less),
 * plus a gentle idle float loop.
 */
export function FloatingCard({
  mx,
  my,
  depth = 1,
  delay = 0,
  icon,
  title,
  subtitle,
  className = "",
}: {
  mx: MotionValue<number>;
  my: MotionValue<number>;
  depth?: number;
  delay?: number;
  icon: ReactNode;
  title: string;
  subtitle: string;
  className?: string;
}) {
  const x = useSpring(useTransform(mx, [-0.5, 0.5], [-24 * depth, 24 * depth]), {
    stiffness: 50,
    damping: 16,
  });
  const y = useSpring(useTransform(my, [-0.5, 0.5], [-16 * depth, 16 * depth]), {
    stiffness: 50,
    damping: 16,
  });

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.6, y: 24 }}
      whileInView={{ opacity: 1, scale: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ type: "spring", stiffness: 200, damping: 18, delay }}
      style={{ x, y }}
      className={`pointer-events-none absolute z-10 ${className}`}
    >
      <div
        className="animate-idle-float flex items-center gap-3 rounded-2xl border border-white/10 bg-abyss/80 px-4 py-3 shadow-glow-mint backdrop-blur-xl"
        style={{ animationDelay: `${delay}s` }}
      >
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-400/15 text-emerald-300">
          {icon}
        </span>
        <div className="text-left">
          <p className="whitespace-nowrap text-xs font-semibold text-white">{title}</p>
          <p className="whitespace-nowrap text-[11px] text-zinc-400">{subtitle}</p>
        </div>
      </div>
    </motion.div>
  );
}
