import {
  BarChart3,
  FileText,
  LayoutDashboard,
  Receipt,
  Search,
  Settings,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import { heroDashboard as d } from "@/content/landing";
import { formatCompact, formatMoney } from "@/lib/utils";

export const STAGE_W = 900;
export const STAGE_H = 640;

/**
 * Hero visual, mirroring the inspiration: a desktop FlowBill dashboard with two floating
 * cards, the whole group rotated about -8deg. Drawn at a fixed 900×640 design size and scaled
 * by the Hero. `js-` classes are animation hooks; the resting markup is the final state.
 */
export function HeroDashboard() {
  const total = d.builder.reduce((s, b) => s + b.amount, 0);
  return (
    <div className="relative font-sans text-ink" style={{ width: STAGE_W, height: STAGE_H }}>
      <div className="js-tilt absolute inset-0 origin-center [transform:rotate(-8deg)]">
        {/* Desktop dashboard */}
        <div className="js-dash absolute top-[40px] left-[235px] flex h-[560px] w-[760px] overflow-hidden rounded-[24px] bg-white shadow-[0_50px_100px_-30px_rgb(8_12_35/0.6)]">
          <aside className="flex w-[72px] shrink-0 flex-col items-center gap-7 border-r border-line py-6 text-ink-muted">
            <span className="grid size-9 place-items-center rounded-full bg-coral-500 font-display text-[15px] font-bold text-white">F</span>
            <LayoutDashboard className="size-[18px] text-ink" />
            <FileText className="size-[18px]" />
            <Users className="size-[18px]" />
            <Receipt className="size-[18px]" />
            <BarChart3 className="size-[18px]" />
            <Settings className="mt-auto size-[18px]" />
          </aside>

          <div className="flex-1 bg-surface/60 p-6">
            <div className="flex items-center gap-2 text-[12px] text-ink-muted">
              <Search className="size-3.5" /> Search clients or invoices
            </div>

            <div className="mt-5 grid grid-cols-[1.15fr_1fr] gap-4">
              <div className="js-dcard relative overflow-hidden rounded-[18px] bg-coral-500 p-5 text-white shadow-[0_18px_30px_-14px_rgb(242_84_91/0.8)]">
                <div aria-hidden className="absolute -top-10 -right-10 size-32 rounded-full bg-white/10" />
                <p className="text-[12px] font-medium text-white/85">Total earned</p>
                <p className="js-count mt-2 font-display text-[30px] leading-none font-bold tabular" data-value={d.earned}>
                  {formatCompact(d.earned)}
                </p>
                <div className="mt-8 flex items-end justify-between text-[11px]">
                  <span className="text-white/85">Kemi Okafor Design</span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-white/20 px-2 py-0.5 font-medium">
                    <TrendingUp className="size-3" /> 18%
                  </span>
                </div>
              </div>
              <div className="js-dcard relative overflow-hidden rounded-[18px] bg-navy-900 p-5 text-white">
                <div aria-hidden className="absolute -right-8 -bottom-12 size-28 rounded-full bg-white/5" />
                <p className="flex items-center gap-1.5 text-[12px] font-medium text-navy-300">
                  <Wallet className="size-3.5" /> Pending
                </p>
                <p className="js-count mt-2 font-display text-[30px] leading-none font-bold tabular" data-value={d.pending}>
                  {formatCompact(d.pending)}
                </p>
                <p className="mt-8 text-[11px] text-navy-300">4 invoices · next due Thu</p>
              </div>
            </div>

            <ul className="mt-5 space-y-3">
              {d.rows.map((r) => (
                <li key={r.name} className="js-drow flex items-center gap-4 rounded-[14px] bg-white px-4 py-3 shadow-[0_1px_2px_rgb(20_28_66/0.05)]">
                  <span
                    className={`grid size-10 shrink-0 place-items-center rounded-full bg-gradient-to-br ${r.tone} text-[12px] font-bold text-white`}
                  >
                    {r.initials}
                  </span>
                  <div className="w-44 min-w-0 leading-tight">
                    <p className="truncate text-[14px] font-medium">{r.name}</p>
                    <p className="text-[11px] text-ink-muted">{r.role}</p>
                  </div>
                  <div className="w-20 leading-tight">
                    <p className="text-[14px] font-medium tabular">{r.invoices}</p>
                    <p className="text-[11px] text-ink-muted">Invoices</p>
                  </div>
                  <div className="w-24 leading-tight">
                    <p className="text-[14px] font-medium tabular">{formatCompact(r.billed)}</p>
                    <p className="text-[11px] text-ink-muted">Billed</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Floating card: payment received */}
        <div className="js-float-a absolute top-[30px] left-[60px] w-[190px] rounded-[18px] bg-white p-5 shadow-[0_30px_60px_-20px_rgb(8_12_35/0.55)]">
          <span className="grid size-10 place-items-center rounded-full bg-gradient-to-br from-coral-400 to-coral-600 text-[12px] font-bold text-white">
            AS
          </span>
          <p className="mt-2 text-[12px] text-ink-muted">Adaeze Studio</p>
          <p className="mt-3 font-display text-[28px] leading-none font-bold tabular">₦450K</p>
          <p className="mt-1.5 text-[12px] font-medium text-coral-600">+13% this month</p>
          <svg viewBox="0 0 150 44" className="mt-3 h-11 w-full overflow-visible" aria-hidden>
            <path
              className="js-spark"
              pathLength={1}
              d="M0 30 C 10 30, 14 14, 24 16 S 36 40, 48 34 S 62 6, 74 10 S 88 38, 100 32 S 116 4, 128 12 S 142 26, 150 18"
              fill="none"
              stroke="#2DD4BF"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
        </div>

        {/* Floating card: invoice builder (the inspiration's slider card) */}
        <div className="js-float-b absolute top-[300px] left-0 w-[290px] rounded-[18px] bg-white p-6 shadow-[0_30px_60px_-20px_rgb(8_12_35/0.55)]">
          <p className="text-[14px] font-medium">New invoice</p>
          <ul className="mt-4 space-y-4">
            {d.builder.map((b) => (
              <li key={b.label}>
                <div className="flex justify-between text-[11px] text-ink-muted">
                  <span>{b.label}</span>
                  <span className="tabular">{formatMoney(b.amount)}</span>
                </div>
                <div className="relative mt-2 h-1 rounded-full bg-navy-300/40">
                  <div className="js-fill absolute inset-y-0 left-0 rounded-full bg-navy-900" style={{ width: `${b.fill * 100}%` }} />
                  <span
                    className="js-knob absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-navy-900 bg-white"
                    style={{ left: `${b.fill * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-6 flex items-center justify-between">
            <p className="font-display text-[24px] font-bold tabular">{formatMoney(total)}</p>
            <span className="rounded-[6px] bg-coral-500 px-4 py-2 text-[12px] font-medium text-white">Send</span>
          </div>
        </div>
      </div>
    </div>
  );
}
