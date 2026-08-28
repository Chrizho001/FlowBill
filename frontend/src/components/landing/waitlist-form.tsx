"use client";

import { useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Check, Loader2 } from "lucide-react";

type FormState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success"; position: number }
  | { kind: "error"; message: string };

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/**
 * Waitlist signup — glass input with a magnetic emerald CTA.
 * Posts to the local API stub at /api/waitlist.
 */
export function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<FormState>({ kind: "idle" });
  const [shakeKey, setShakeKey] = useState(0);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [magnet, setMagnet] = useState({ x: 0, y: 0 });
  const reduced = useReducedMotion();

  function fail(message: string) {
    setState({ kind: "error", message });
    setShakeKey((k) => k + 1);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (state.kind === "submitting" || state.kind === "success") return;

    const trimmed = email.trim().toLowerCase();
    if (!trimmed) return fail("Please enter your email address.");
    if (!EMAIL_RE.test(trimmed)) return fail("That email doesn't look right — mind checking it?");

    setState({ kind: "submitting" });
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: trimmed }),
      });
      const json = (await res.json()) as
        | { status: "success"; data: { position: number } }
        | { status: "error"; message: string };

      if (res.ok && json.status === "success") {
        setState({ kind: "success", position: json.data.position });
      } else {
        fail(json.status === "error" ? json.message : "Something went wrong. Please try again.");
      }
    } catch {
      fail("Network hiccup — please try again in a moment.");
    }
  }

  // Magnetic CTA: translate toward the cursor while hovering.
  function handleButtonMove(e: React.PointerEvent) {
    if (reduced || !buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    const dx = e.clientX - (rect.left + rect.width / 2);
    const dy = e.clientY - (rect.top + rect.height / 2);
    setMagnet({ x: dx * 0.25, y: dy * 0.35 });
  }

  if (state.kind === "success") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 22 }}
        className="mx-auto flex w-full max-w-md items-center gap-4 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 px-5 py-4 backdrop-blur-md"
        role="status"
      >
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 320, damping: 16, delay: 0.1 }}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-400 shadow-glow-mint"
        >
          <Check className="h-5 w-5 text-emerald-950" strokeWidth={3} />
        </motion.span>
        <div className="text-left">
          <p className="font-display font-semibold text-white">You&apos;re on the list!</p>
          <p className="text-sm text-emerald-200/80">
            You&apos;re #{state.position} in line — we&apos;ll email you at launch.
          </p>
        </div>
      </motion.div>
    );
  }

  const submitting = state.kind === "submitting";

  return (
    <motion.form
      key={shakeKey}
      onSubmit={handleSubmit}
      noValidate
      initial={false}
      animate={shakeKey > 0 && !reduced ? { x: [0, -10, 10, -6, 6, 0] } : { x: 0 }}
      transition={{ duration: 0.4 }}
      className="mx-auto flex w-full max-w-md flex-col gap-3"
    >
      <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-2 backdrop-blur-md transition-colors duration-300 focus-within:border-emerald-400/40 sm:flex-row">
        <label htmlFor="waitlist-email" className="sr-only">
          Email address
        </label>
        <input
          id="waitlist-email"
          type="email"
          autoComplete="email"
          placeholder="you@studio.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (state.kind === "error") setState({ kind: "idle" });
          }}
          disabled={submitting}
          className="min-w-0 flex-1 rounded-xl bg-transparent px-4 py-3 text-zinc-100 placeholder:text-zinc-500 focus:outline-none disabled:opacity-60"
        />
        <motion.button
          ref={buttonRef}
          type="submit"
          disabled={submitting}
          onPointerMove={handleButtonMove}
          onPointerLeave={() => setMagnet({ x: 0, y: 0 })}
          style={{ x: magnet.x, y: magnet.y }}
          whileTap={{ scale: 0.97 }}
          className="group relative inline-flex shrink-0 items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 px-6 py-3 text-sm font-semibold text-emerald-950 shadow-glow-mint transition-shadow duration-300 hover:shadow-glow-deep disabled:cursor-wait disabled:opacity-80"
        >
          {/* Shimmer sweep */}
          <span
            aria-hidden
            className="pointer-events-none absolute inset-y-0 w-1/3 bg-white/30 blur-sm [animation:shimmer-sweep_3.5s_ease-in-out_infinite]"
          />
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              Join the waitlist
              <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
            </>
          )}
        </motion.button>
      </div>

      {state.kind === "error" && (
        <motion.p
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-2 text-left text-sm text-rose-300/90"
          role="alert"
        >
          {state.message}
        </motion.p>
      )}
    </motion.form>
  );
}
