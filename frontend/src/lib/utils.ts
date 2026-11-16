import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type Currency = "NGN" | "USD";

const SYMBOL: Record<Currency, string> = { NGN: "₦", USD: "$" };

/** ₦450,000 / $1,200 — whole units, grouped (design.md §4). */
export function formatMoney(amount: number, currency: Currency = "NGN") {
  return `${SYMBOL[currency]}${Math.round(amount).toLocaleString("en-US")}`;
}

/** ₦1.2M / ₦620K for compact stat displays. */
export function formatCompact(amount: number, currency: Currency = "NGN") {
  if (amount >= 1_000_000) return `${SYMBOL[currency]}${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${SYMBOL[currency]}${Math.round(amount / 1_000)}K`;
  return formatMoney(amount, currency);
}
