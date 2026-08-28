"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  animate,
  motion,
  useInView,
  useReducedMotion,
  useSpring,
  useTransform,
  type MotionValue,
} from "framer-motion";
import {
  CheckCircle2,
  Clock,
  Droplets,
  FileText,
  LayoutDashboard,
  Plus,
  Receipt,
  Settings,
  Users,
  Wallet,
} from "lucide-react";

const INVOICE_ROWS = [
  { number: "INV-2026-0042", client: "Studio Nova", amount: "$2,400.00", status: "Paid" },
  { number: "INV-2026-0041", client: "Acme Corp", amount: "$1,850.00", status: "Pending" },
  { number: "INV-2026-0039", client: "Bright Labs", amount: "$3,200.00", status: "Overdue" },
  { number: "INV-2026-0038", client: "Kesi Design", amount: "$960.00", status: "Paid" },
] as const;

const CHART_BARS = [32, 45, 38, 52, 47, 61, 55, 70, 64, 78, 72, 92];

const STATUS_STYLES: Record<string, string> = {
  Paid: "bg-emerald-400/15 text-emerald-300 border-emerald-400/25",
  Pending: "bg-amber-400/10 text-amber-300/90 border-amber-400/20",
  Overdue: "bg-rose-400/10 text-rose-300/90 border-rose-400/20",
};

/** Counts from 0 to target when scrolled into view. */
function Counter({
  target,
  format,
  duration = 1.8,
}: {
  target: number;
  format: (v: number) => string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const reduced = useReducedMotion();
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!inView || reduced) return;
    const controls = animate(0, target, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: setValue,
    });
    return () => controls.stop();
  }, [inView, target, duration, reduced]);

  // With reduced motion, jump straight to the final value once visible.
  const display = inView && reduced ? target : value;

  return (
    <span ref={ref} className="tabular-nums">
      {format(display)}
    </span>
  );
}

function StatCard({
  label,
  children,
  icon,
}: {
  label: string;
  children: ReactNode;
  icon: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.03] p-3 sm:p-4">
      <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wider text-zinc-500 sm:text-[11px]">
        {icon}
        {label}
      </div>
      <div className="mt-1.5 font-mono text-lg font-semibold text-white sm:text-xl">
        {children}
      </div>
    </div>
  );
}

/**
 * 3D-tilting FlowBill dashboard mockup. Rotates with the hero's
 * shared mouse-parallax motion values (mx/my, normalized -0.5..0.5).
 */
export function DashboardMockup({
  mx,
  my,
}: {
  mx: MotionValue<number>;
  my: MotionValue<number>;
}) {
  // When reduced motion is preferred, the springs are simply never applied.
  const rotateX = useSpring(useTransform(my, [-0.5, 0.5], [6, -6]), {
    stiffness: 60,
    damping: 18,
  });
  const rotateY = useSpring(useTransform(mx, [-0.5, 0.5], [-6, 6]), {
    stiffness: 60,
    damping: 18,
  });

  return (
    <div className="relative mx-auto w-full max-w-4xl [perspective:1400px]">
      <motion.div
        initial={{ opacity: 0, y: 80, rotateX: 18 }}
        whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ type: "spring", stiffness: 40, damping: 20 }}
        style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
        className="relative overflow-hidden rounded-2xl border border-white/10 bg-abyss/90 shadow-[0_40px_120px_-30px_rgba(16,185,129,0.25)] backdrop-blur-xl"
      >
        {/* Browser chrome */}
        <div className="flex h-10 items-center gap-2 border-b border-white/5 bg-black/40 px-4">
          <span className="h-2.5 w-2.5 rounded-full bg-rose-500/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-amber-500/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/70" />
          <span className="mx-auto hidden rounded-md bg-white/5 px-3 py-0.5 text-[11px] text-zinc-500 sm:block">
            app.flowbill.com
          </span>
        </div>

        <div className="flex">
          {/* Sidebar */}
          <aside className="hidden w-14 flex-col items-center gap-1 border-r border-white/5 py-4 md:flex lg:w-44 lg:items-stretch lg:px-3">
            <div className="mb-4 hidden items-center gap-2 px-2 lg:flex">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-400 to-teal-600">
                <Droplets className="h-4 w-4 text-emerald-950" strokeWidth={2.5} />
              </span>
              <span className="font-display text-sm font-bold text-white">FlowBill</span>
            </div>
            {[
              { icon: LayoutDashboard, label: "Overview", active: true },
              { icon: FileText, label: "Invoices" },
              { icon: Users, label: "Clients" },
              { icon: Receipt, label: "Expenses" },
              { icon: Wallet, label: "Payments" },
              { icon: Settings, label: "Settings" },
            ].map(({ icon: Icon, label, active }) => (
              <div
                key={label}
                className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs ${
                  active
                    ? "bg-emerald-400/10 text-emerald-300"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
                title={label}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="hidden lg:inline">{label}</span>
              </div>
            ))}
          </aside>

          {/* Main panel */}
          <div className="min-w-0 flex-1 p-4 sm:p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate font-display text-sm font-semibold text-white sm:text-base">
                  Good afternoon, Ada
                </p>
                <p className="text-[11px] text-zinc-500">
                  3 invoices were paid while you slept.
                </p>
              </div>
              <span className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 px-3 py-1.5 text-xs font-semibold text-emerald-950">
                <Plus className="h-3.5 w-3.5" strokeWidth={3} />
                <span className="hidden sm:inline">New Invoice</span>
              </span>
            </div>

            {/* Stats */}
            <div className="mt-4 grid grid-cols-3 gap-2 sm:gap-3">
              <StatCard
                label="Total earned"
                icon={<Wallet className="h-3 w-3" />}
              >
                <Counter target={128540} format={(v) => `$${Math.round(v).toLocaleString("en-US")}`} />
              </StatCard>
              <StatCard label="Pending" icon={<Clock className="h-3 w-3" />}>
                <Counter target={12320} format={(v) => `$${Math.round(v).toLocaleString("en-US")}`} />
              </StatCard>
              <StatCard label="Active clients" icon={<Users className="h-3 w-3" />}>
                <Counter target={14} format={(v) => String(Math.round(v))} />
              </StatCard>
            </div>

            {/* Revenue chart + invoice list */}
            <div className="mt-4 grid gap-3 lg:grid-cols-5">
              <div className="rounded-xl border border-white/5 bg-white/[0.03] p-4 lg:col-span-2">
                <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                  Revenue · 12 months
                </p>
                <div className="mt-3 flex h-20 items-end gap-1.5 sm:h-24">
                  {CHART_BARS.map((h, i) => (
                    <motion.div
                      key={i}
                      initial={{ height: "4%" }}
                      whileInView={{ height: `${h}%` }}
                      viewport={{ once: true }}
                      transition={{ delay: 0.5 + i * 0.05, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                      className={`flex-1 rounded-sm ${
                        i === CHART_BARS.length - 1
                          ? "bg-gradient-to-t from-emerald-500 to-teal-300 shadow-glow-mint"
                          : "bg-emerald-500/25"
                      }`}
                    />
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.03] p-2 lg:col-span-3">
                {INVOICE_ROWS.map((row, i) => (
                  <motion.div
                    key={row.number}
                    initial={{ opacity: 0, x: 16 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.6 + i * 0.1, duration: 0.45 }}
                    className="flex items-center gap-3 rounded-lg px-2.5 py-2.5 transition-colors hover:bg-white/[0.04] sm:px-3"
                  >
                    <CheckCircle2
                      className={`h-4 w-4 shrink-0 ${
                        row.status === "Paid" ? "text-emerald-400" : "text-zinc-600"
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-mono text-[11px] text-zinc-300 sm:text-xs">
                        {row.number}
                      </p>
                      <p className="truncate text-[11px] text-zinc-500">{row.client}</p>
                    </div>
                    <span className="shrink-0 font-mono text-xs text-zinc-300">{row.amount}</span>
                    <span
                      className={`hidden shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium sm:inline ${STATUS_STYLES[row.status]}`}
                    >
                      {row.status}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
