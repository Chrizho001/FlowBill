import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** iPhone 16 logical screen size in points. Screens are authored at this size and scaled. */
export const SCREEN_W = 393;
export const SCREEN_H = 852;

/**
 * An iPhone 16 rendered in CSS: titanium edge, black bezel, Dynamic Island, side buttons
 * and an iOS status bar. `children` is the screen content, authored at 393×852.
 */
export function IPhone16({
  width = 300,
  children,
  className,
  statusTone = "dark",
}: {
  width?: number;
  children: ReactNode;
  className?: string;
  statusTone?: "dark" | "light";
}) {
  const height = Math.round(width * 2.06);
  const edge = width * 0.016;
  const bezel = width * 0.03;
  const screenW = width - 2 * (edge + bezel);
  const scale = screenW / SCREEN_W;
  const radius = width * 0.17;

  return (
    <div className={cn("relative shrink-0", className)} style={{ width, height }}>
      {/* Side buttons */}
      <span aria-hidden className="absolute rounded-l-sm bg-[#9a9ea6]" style={{ left: -width * 0.012, top: height * 0.17, width: width * 0.014, height: height * 0.04 }} />
      <span aria-hidden className="absolute rounded-l-sm bg-[#9a9ea6]" style={{ left: -width * 0.012, top: height * 0.25, width: width * 0.014, height: height * 0.075 }} />
      <span aria-hidden className="absolute rounded-l-sm bg-[#9a9ea6]" style={{ left: -width * 0.012, top: height * 0.34, width: width * 0.014, height: height * 0.075 }} />
      <span aria-hidden className="absolute rounded-r-sm bg-[#9a9ea6]" style={{ right: -width * 0.012, top: height * 0.27, width: width * 0.014, height: height * 0.11 }} />
      <span aria-hidden className="absolute rounded-r-sm bg-[#9a9ea6]" style={{ right: -width * 0.012, top: height * 0.55, width: width * 0.014, height: height * 0.06 }} />

      {/* Titanium edge */}
      <div
        className="absolute inset-0 shadow-[0_50px_90px_-30px_rgb(15_20_45/0.45),0_20px_40px_-20px_rgb(15_20_45/0.35)]"
        style={{
          borderRadius: radius,
          padding: edge,
          background: "linear-gradient(145deg,#b9bdc4 0%,#eceef1 22%,#8d929a 48%,#d7dadf 74%,#7f848c 100%)",
        }}
      >
        {/* Bezel */}
        <div className="h-full w-full bg-[#0b0b0d]" style={{ borderRadius: radius - edge, padding: bezel }}>
          {/* Screen */}
          <div className="relative h-full w-full overflow-hidden bg-white" style={{ borderRadius: radius - edge - bezel }}>
            <div className="absolute top-0 left-0 origin-top-left" style={{ width: SCREEN_W, height: SCREEN_H, transform: `scale(${scale})` }}>
              {children}
              <StatusBar tone={statusTone} />
              <div aria-hidden className="absolute top-[11px] left-1/2 h-[37px] w-[125px] -translate-x-1/2 rounded-full bg-black" />
              <div aria-hidden className="absolute bottom-[8px] left-1/2 h-[5px] w-[140px] -translate-x-1/2 rounded-full bg-black/80" />
            </div>
            {/* Glass sheen */}
            <div aria-hidden className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgb(255_255_255/0.14)_0%,transparent_35%)]" />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusBar({ tone }: { tone: "dark" | "light" }) {
  const c = tone === "light" ? "#fff" : "#0b0b0d";
  return (
    <div aria-hidden className="absolute inset-x-0 top-0 flex h-[54px] items-center justify-between px-[34px] pt-[6px]" style={{ color: c }}>
      <span className="text-[17px] font-semibold tracking-tight" style={{ fontFamily: "-apple-system, 'SF Pro Text', var(--font-sans)" }}>
        9:41
      </span>
      <span className="flex items-center gap-[6px]">
        <svg width="19" height="12" viewBox="0 0 19 12" fill={c}>
          <rect x="0" y="8" width="3.5" height="4" rx="1" />
          <rect x="5" y="5.5" width="3.5" height="6.5" rx="1" />
          <rect x="10" y="3" width="3.5" height="9" rx="1" />
          <rect x="15" y="0" width="3.5" height="12" rx="1" />
        </svg>
        <svg width="17" height="12" viewBox="0 0 17 12" fill={c}>
          <path d="M8.5 2.4c2.3 0 4.4.9 6 2.4l1.2-1.2A10.2 10.2 0 0 0 8.5.7 10.2 10.2 0 0 0 1.3 3.6l1.2 1.2a8.5 8.5 0 0 1 6-2.4Zm0 3.4c1.4 0 2.6.5 3.6 1.4l1.2-1.2a6.8 6.8 0 0 0-9.6 0l1.2 1.2c1-.9 2.2-1.4 3.6-1.4Zm0 3.4c.5 0 1 .2 1.3.5L8.5 11 7.2 9.7c.3-.3.8-.5 1.3-.5Z" />
        </svg>
        <svg width="27" height="13" viewBox="0 0 27 13" fill="none">
          <rect x="0.5" y="0.5" width="23" height="12" rx="3.5" stroke={c} strokeOpacity="0.4" />
          <rect x="2" y="2" width="20" height="9" rx="2" fill={c} />
          <path d="M25 4.5v4c.8-.3 1.3-1.1 1.3-2s-.5-1.7-1.3-2Z" fill={c} fillOpacity="0.45" />
        </svg>
      </span>
    </div>
  );
}
