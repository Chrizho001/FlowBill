import { ArrowRight } from "lucide-react";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary-dark" | "secondary-light" | "white";
type Size = "md" | "lg";

const base =
  "group/btn relative inline-flex items-center justify-center gap-2.5 rounded-btn font-sans font-medium whitespace-nowrap select-none " +
  "transition-[translate,scale,transform,background-color,border-color,box-shadow,color] duration-300 ease-[var(--ease-out-expo)] " +
  "hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.97] disabled:pointer-events-none disabled:opacity-60";

const variants: Record<Variant, string> = {
  primary:
    "bg-coral-600 text-white shadow-[0_10px_30px_-10px_rgb(217_58_67/0.7)] hover:bg-[#c9323b] hover:shadow-[0_16px_36px_-12px_rgb(217_58_67/0.8)]",
  "secondary-dark":
    "border-[1.5px] border-navy-700 text-white hover:border-navy-300 hover:bg-white/5",
  "secondary-light":
    "border-[1.5px] border-ink/15 text-ink hover:border-ink/40 hover:bg-white",
  white: "bg-white text-navy-900 shadow-[0_8px_24px_-12px_rgb(0_0_0/0.4)] hover:bg-surface",
};

const sizes: Record<Size, string> = {
  md: "h-[52px] px-6 text-base",
  lg: "h-14 px-7 text-[1.0625rem]",
};

type Common = { variant?: Variant; size?: Size; arrow?: boolean; children: ReactNode; className?: string };

function Inner({ children, arrow }: { children: ReactNode; arrow?: boolean }) {
  return (
    <>
      <span>{children}</span>
      {arrow && (
        <ArrowRight
          aria-hidden
          className="size-[18px] transition-transform duration-300 ease-[var(--ease-out-expo)] group-hover/btn:translate-x-1"
          strokeWidth={2}
        />
      )}
    </>
  );
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  arrow = false,
  className,
  children,
  ...rest
}: Common & AnchorHTMLAttributes<HTMLAnchorElement>) {
  return (
    <a className={cn(base, variants[variant], sizes[size], className)} {...rest}>
      <Inner arrow={arrow}>{children}</Inner>
    </a>
  );
}

export function Button({
  variant = "primary",
  size = "md",
  arrow = false,
  className,
  children,
  ...rest
}: Common & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...rest}>
      <Inner arrow={arrow}>{children}</Inner>
    </button>
  );
}
