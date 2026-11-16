"use client";

import { AlertCircle, Check, ChevronDown, Loader2, X } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { PROFESSIONS } from "@/content/landing";
import { gsap } from "@/lib/gsap";
import { cn } from "@/lib/utils";

type Intent = "signup" | "login";
type OpenOptions = { source: string; intent?: Intent; crypto?: boolean };
type State = "idle" | "submitting" | "success" | "duplicate" | "error";
type FieldErrors = Partial<Record<"name" | "email" | "profession", string>>;


const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const WaitlistContext = createContext<{ open: (o: OpenOptions) => void } | null>(null);

export function useWaitlist() {
  const ctx = useContext(WaitlistContext);
  if (!ctx) throw new Error("useWaitlist must be used inside <WaitlistProvider>");
  return ctx;
}

/** Wraps the page; renders one accessible <dialog> that every CTA opens (design.md §5). */
export function WaitlistProvider({ children }: { children: ReactNode }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [opts, setOpts] = useState<OpenOptions>({ source: "unknown" });
  const [session, setSession] = useState(0);

  const reduce = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const open = useCallback((o: OpenOptions) => {
    setOpts(o);
    setSession((s) => s + 1);
    const d = dialogRef.current;
    if (!d || d.open) return;
    d.showModal();
    document.documentElement.style.overflow = "hidden";
    if (!reduce()) {
      gsap.fromTo(d, { opacity: 0 }, { opacity: 1, duration: 0.25, ease: "power2.out" });
      gsap.fromTo(panelRef.current, { y: 28, scale: 0.97 }, { y: 0, scale: 1, duration: 0.5, ease: "expo.out" });
    }
  }, []);

  const close = useCallback(() => {
    const d = dialogRef.current;
    if (!d?.open) return;
    const done = () => {
      d.close();
      document.documentElement.style.overflow = "";
      gsap.set([d, panelRef.current], { clearProps: "all" });
    };
    if (reduce()) return done();
    gsap.to(panelRef.current, { y: 16, scale: 0.98, duration: 0.22, ease: "power2.in" });
    gsap.to(d, { opacity: 0, duration: 0.22, ease: "power2.in", onComplete: done });
  }, []);

  useEffect(() => {
    const d = dialogRef.current;
    if (!d) return;
    const onCancel = (e: Event) => {
      e.preventDefault();
      close();
    };
    d.addEventListener("cancel", onCancel);
    return () => d.removeEventListener("cancel", onCancel);
  }, [close]);

  const intent = opts.intent ?? "signup";

  return (
    <WaitlistContext.Provider value={{ open }}>
      {children}
      <dialog
        ref={dialogRef}
        aria-labelledby="waitlist-title"
        aria-describedby="waitlist-desc"
        onClick={(e) => e.target === e.currentTarget && close()}
        className="m-auto w-[min(calc(100vw-2rem),30rem)] overflow-visible bg-transparent p-0 backdrop:bg-navy-950/70 backdrop:backdrop-blur-sm"
      >
        <div ref={panelRef} className="relative rounded-frame bg-white p-7 text-ink shadow-[0_40px_80px_-20px_rgb(10_15_40/0.5)] sm:p-10">
          <button
            type="button"
            onClick={close}
            aria-label="Close"
            className="absolute top-4 right-4 grid size-11 place-items-center rounded-full text-ink-muted transition-colors hover:bg-surface hover:text-ink"
          >
            <X className="size-5" aria-hidden />
          </button>
          <WaitlistForm key={session} opts={opts} intent={intent} onDone={close} />
        </div>
      </dialog>
    </WaitlistContext.Provider>
  );
}

const fieldBase =
  "h-12 w-full rounded-btn border-[1.5px] border-line bg-white px-4 text-[1rem] text-ink transition-colors outline-none placeholder:text-ink-muted/70 hover:border-ink/30 focus-visible:border-navy-700 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-coral-400";

function WaitlistForm({ opts, intent, onDone }: { opts: OpenOptions; intent: Intent; onDone: () => void }) {
  const [state, setState] = useState<State>("idle");
  const [errors, setErrors] = useState<FieldErrors>({});

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const name = String(data.get("name") ?? "").trim();
    const email = String(data.get("email") ?? "").trim();
    const profession = String(data.get("profession") ?? "");
    const next: FieldErrors = {};
    if (name.length < 2) next.name = "Enter your name.";
    if (!EMAIL_RE.test(email)) next.email = "Enter a valid email address, like you@studio.com.";
    if (!profession) next.profession = "Choose what you do.";
    setErrors(next);
    if (Object.keys(next).length) {
      (e.currentTarget.querySelector(`[name=${Object.keys(next)[0]}]`) as HTMLElement | null)?.focus();
      return;
    }
    setState("submitting");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, profession, source: opts.source, crypto_interest: data.get("crypto_interest") === "on" }),
      });
      setState(res.status === 409 ? "duplicate" : res.ok ? "success" : "error");
    } catch {
      setState("error");
    }
  }

  if (state === "success" || state === "duplicate") {
    return (
      <div role="status" className="py-4 text-center">
        <span className="mx-auto grid size-14 place-items-center rounded-full bg-[#16A34A] text-white">
          <Check className="size-7" strokeWidth={3} aria-hidden />
        </span>
        <h2 id="waitlist-title" className="mt-6 text-[1.75rem] font-bold tracking-tight">
          {state === "success" ? "You're on the list." : "You're already on the list."}
        </h2>
        <p id="waitlist-desc" className="mt-3 text-ink-muted">
          We&apos;ll email you once, when FlowBill opens.
        </p>
        <Button type="button" variant="secondary-light" arrow={false} onClick={onDone} className="mt-8">
          Close
        </Button>
      </div>
    );
  }

  const err = (k: keyof FieldErrors) =>
    errors[k] ? (
      <p id={`wl-${k}-err`} className="mt-2 flex items-center gap-1.5 text-sm font-medium text-[#BE123C]">
        <AlertCircle className="size-4 shrink-0" aria-hidden /> {errors[k]}
      </p>
    ) : null;

  return (
    <form onSubmit={onSubmit} noValidate>
      <p className="text-eyebrow text-coral-600">Early access</p>
      <h2 id="waitlist-title" className="mt-3 pr-10 text-[1.875rem] leading-tight font-bold tracking-[-0.02em]">
        {intent === "login" ? "We're not open yet" : "Get early access"}
      </h2>
      <p id="waitlist-desc" className="mt-3 text-ink-muted">
        {intent === "login"
          ? "FlowBill is in early access. Join the list and we'll email you when you can log in."
          : "FlowBill opens soon. Tell us a little about you and we'll email you once, at launch."}
      </p>

      <div className="mt-8 space-y-5">
        <div>
          <label htmlFor="wl-name" className="mb-2 block text-sm font-medium">
            Full name
          </label>
          <input
            id="wl-name"
            name="name"
            autoFocus
            autoComplete="name"
            maxLength={80}
            placeholder="Ada Okafor"
            aria-invalid={errors.name ? true : undefined}
            aria-describedby={errors.name ? "wl-name-err" : undefined}
            className={cn(fieldBase, errors.name && "border-[#BE123C]")}
          />
          {err("name")}
        </div>
        <div>
          <label htmlFor="wl-email" className="mb-2 block text-sm font-medium">
            Email
          </label>
          <input
            id="wl-email"
            name="email"
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="you@studio.com"
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? "wl-email-err" : undefined}
            className={cn(fieldBase, errors.email && "border-[#BE123C]")}
          />
          {err("email")}
        </div>
        <div>
          <label htmlFor="wl-profession" className="mb-2 block text-sm font-medium">
            What do you do?
          </label>
          <div className="relative">
            <select
              id="wl-profession"
              name="profession"
              defaultValue=""
              aria-invalid={errors.profession ? true : undefined}
              aria-describedby={errors.profession ? "wl-profession-err" : undefined}
              className={cn(fieldBase, "appearance-none pr-10", errors.profession && "border-[#BE123C]")}
            >
              <option value="" disabled>
                Choose your profession
              </option>
              {PROFESSIONS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute top-1/2 right-3.5 size-4 -translate-y-1/2 text-ink-muted" aria-hidden />
          </div>
          {err("profession")}
        </div>
        <label className="flex min-h-11 cursor-pointer items-center gap-3 text-[0.9375rem] text-ink-muted">
          <input type="checkbox" name="crypto_interest" defaultChecked={!!opts.crypto} className="size-5 rounded accent-navy-900" />
          I&apos;m interested in crypto payments
        </label>
      </div>

      {state === "error" && (
        <p role="alert" className="mt-4 flex items-center gap-2 text-sm font-medium text-[#BE123C]">
          <AlertCircle className="size-4 shrink-0" aria-hidden /> Something went wrong. Please try again.
        </p>
      )}

      <Button type="submit" size="lg" className="mt-8 w-full" disabled={state === "submitting"}>
        {state === "submitting" ? (
          <span className="inline-flex items-center gap-2">
            <Loader2 className="size-4 animate-spin" aria-hidden /> Joining…
          </span>
        ) : (
          "Join the waitlist"
        )}
      </Button>
      <p className="mt-4 text-center text-[13px] text-ink-muted">No spam. One email at launch.</p>
    </form>
  );
}
