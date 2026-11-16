import { cn } from "@/lib/utils";

/** FlowBill wordmark: Space Grotesk 700 with a coral payment dot. */
export function Logo({ className, tone = "ink" }: { className?: string; tone?: "ink" | "white" }) {
  return (
    <span
      className={cn(
        "inline-flex items-baseline font-display font-bold tracking-[-0.03em]",
        tone === "white" ? "text-white" : "text-ink",
        className,
      )}
    >
      Flow<span className="relative">Bill</span>
      <span aria-hidden className="ml-[0.12em] inline-block size-[0.32em] rounded-full bg-coral-500" />
    </span>
  );
}
