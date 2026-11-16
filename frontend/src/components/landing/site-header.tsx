"use client";

import { Menu, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";
import { nav } from "@/content/landing";
import { gsap, MOTION, ScrollTrigger, useGSAP } from "@/lib/gsap";
import { cn } from "@/lib/utils";
import { useWaitlist } from "./waitlist-modal";

const CLEAR = "transform,translate,rotate,scale,opacity,visibility";

/** Navbar mirroring the inspiration: logo + links on the left, Log in + Sign up on the right. */
export function SiteHeader() {
  const ref = useRef<HTMLElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { open: openWaitlist } = useWaitlist();

  useGSAP(
    () => {
      ScrollTrigger.create({ start: 24, end: "max", onToggle: (self) => setScrolled(self.isActive) });
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        gsap.from(".js-nav-item", { y: -12, autoAlpha: 0, duration: 0.6, stagger: 0.05, delay: 0.15, clearProps: CLEAR });
      });
    },
    { scope: ref },
  );

  useGSAP(
    () => {
      if (!open) return;
      const mm = gsap.matchMedia();
      mm.add(MOTION.ok, () => {
        gsap.from(".js-menu-link", { y: 32, autoAlpha: 0, duration: 0.6, stagger: 0.06, ease: "expo.out", clearProps: CLEAR });
      });
    },
    { dependencies: [open], scope: menuRef },
  );

  useEffect(() => {
    document.documentElement.style.overflow = open ? "hidden" : "";
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const login = () => {
    setOpen(false);
    openWaitlist({ source: "nav-login", intent: "login" });
  };
  const signup = () => {
    setOpen(false);
    openWaitlist({ source: "nav-signup" });
  };

  return (
    <header
      ref={ref}
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-500",
        scrolled && !open ? "border-b border-white/10 bg-navy-900/[0.97] backdrop-blur-md shadow-[0_10px_30px_-15px_rgb(10_15_40/0.5)]" : "border-b border-transparent",
      )}
    >
      <div className="container flex h-20 items-center">
        <a href="#hero" className="js-nav-item -m-2 p-2" aria-label="FlowBill home">
          <Logo tone="white" className="text-[22px]" />
        </a>

        <nav aria-label="Main" className="ml-14 hidden lg:block">
          <ul className="flex items-center gap-9">
            {nav.map((item) => (
              <li key={item.href} className="js-nav-item">
                <a href={item.href} className="link-draw py-2 text-[0.9375rem] text-white/80 transition-colors hover:text-white">
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="ml-auto flex items-center gap-3 sm:gap-5">
          <button
            type="button"
            onClick={login}
            className="js-nav-item link-draw hidden py-2 text-[0.9375rem] font-medium text-white sm:inline-block"
          >
            Log in
          </button>
          <Button variant="white" arrow={false} onClick={signup} className="js-nav-item hidden h-11 px-6 text-[0.9375rem] sm:inline-flex">
            Sign up
          </Button>
          <button
            type="button"
            className="js-nav-item -mr-2 grid size-11 place-items-center rounded-btn text-white lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="size-6" aria-hidden /> : <Menu className="size-6" aria-hidden />}
          </button>
        </div>
      </div>

      {open && (
        <div id="mobile-menu" ref={menuRef} className="fixed inset-x-0 top-20 bottom-0 z-40 overflow-y-auto bg-navy-950 lg:hidden">
          <nav aria-label="Mobile" className="container flex min-h-full flex-col pt-10 pb-12">
            <ul className="flex flex-col gap-2">
              {nav.map((item) => (
                <li key={item.href} className="js-menu-link">
                  <a
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className="block py-3 font-display text-[2rem] font-medium tracking-tight text-white"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
            <div className="js-menu-link mt-auto grid gap-3 pt-12">
              <Button variant="white" size="lg" arrow={false} className="w-full" onClick={signup}>
                Sign up
              </Button>
              <Button variant="secondary-dark" size="lg" arrow={false} className="w-full" onClick={login}>
                Log in
              </Button>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
