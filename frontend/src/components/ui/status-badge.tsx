import { cn } from "@/lib/utils";

export type Status = "draft" | "pending" | "paid" | "overdue" | "cancelled";

/* Status palette (design.md §1.1) — always a label + dot, never colour alone. */
const tone: Record<Status, string> = {
  draft: "bg-[#F1F5F9] text-[#475569]",
  pending: "bg-[#FEF3C7] text-[#B45309]",
  paid: "bg-[#DCFCE7] text-[#15803D]",
  overdue: "bg-[#FFE4E6] text-[#BE123C]",
  cancelled: "bg-[#F1F5F9] text-[#64748B]",
};

export function StatusBadge({
  status,
  className,
  ...rest
}: { status: Status; className?: string } & React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] leading-none font-medium tracking-[0.08em] uppercase",
        tone[status],
        className,
      )}
      {...rest}
    >
      <span aria-hidden className="size-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}
