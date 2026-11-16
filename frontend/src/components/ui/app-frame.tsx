import { Search } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Logo } from "./logo";

/** A FlowBill window that frames live product UI (design.md §2). */
export function AppFrame({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-frame border border-line bg-white shadow-[0_40px_80px_-30px_rgb(20_28_66/0.35)]",
        className,
      )}
    >
      <div className="flex h-11 items-center gap-4 border-b border-line bg-surface/70 px-4">
        <div className="flex gap-1.5" aria-hidden>
          <span className="size-2.5 rounded-full bg-[#E3E7F2]" />
          <span className="size-2.5 rounded-full bg-[#E3E7F2]" />
          <span className="size-2.5 rounded-full bg-[#E3E7F2]" />
        </div>
        <Logo className="text-[15px]" />
        <div className="ml-auto hidden h-7 w-48 items-center gap-2 rounded-chip border border-line bg-white px-2.5 text-[12px] text-ink-muted sm:flex">
          <Search className="size-3.5" aria-hidden />
          Search invoices
        </div>
      </div>
      {children}
    </div>
  );
}
