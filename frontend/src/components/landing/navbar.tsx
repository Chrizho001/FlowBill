import { Droplets } from "lucide-react";

/**
 * Minimal glass navbar. Links are inert anchors for now —
 * they point at section ids that later landing phases will add.
 */
export function Navbar() {
  return (
    <header className="absolute inset-x-0 top-0 z-20">
      <nav className="container flex items-center justify-between px-4 py-5 sm:px-6">
        <a href="#" className="group flex items-center gap-2.5" aria-label="FlowBill home">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 shadow-glow-mint transition-transform duration-300 group-hover:scale-105">
            <Droplets className="h-5 w-5 text-emerald-950" strokeWidth={2.5} />
          </span>
          <span className="font-display text-lg font-bold tracking-tight text-white">
            FlowBill
          </span>
        </a>

        <div className="hidden items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2 py-1.5 backdrop-blur-md md:flex">
          {["Features", "Pricing", "FAQ"].map((label) => (
            <a
              key={label}
              href="#"
              className="rounded-full px-4 py-1.5 text-sm text-zinc-400 transition-colors duration-200 hover:bg-white/5 hover:text-white"
            >
              {label}
            </a>
          ))}
        </div>

        <a
          href="#waitlist"
          className="rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm font-medium text-zinc-200 backdrop-blur-md transition-all duration-300 hover:border-emerald-400/40 hover:bg-emerald-400/10 hover:text-white"
        >
          Sign In
        </a>
      </nav>
    </header>
  );
}
