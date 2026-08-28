/**
 * Ambient aurora backdrop for the hero — layered drifting emerald/mint
 * gradients, a fine grid texture, and a floor glow under the mockup.
 * Pure CSS animation (see globals.css keyframes); no client JS needed.
 */
export function AuroraBackground() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      {/* Drifting gradient blobs */}
      <div className="animate-aurora-1 absolute -top-[30%] -left-[15%] h-[60vh] w-[55vw] rounded-full bg-aurora-1/25 blur-[120px] mix-blend-screen" />
      <div className="animate-aurora-2 absolute top-[10%] -right-[15%] h-[55vh] w-[45vw] rounded-full bg-aurora-2/15 blur-[120px] mix-blend-screen" />
      <div className="animate-aurora-3 absolute -bottom-[25%] left-[20%] h-[50vh] w-[50vw] rounded-full bg-aurora-3/15 blur-[130px] mix-blend-screen" />

      {/* Fine grid texture, fading out downward */}
      <div className="bg-grid-mint absolute inset-0 [mask-image:radial-gradient(ellipse_70%_60%_at_50%_35%,black_30%,transparent_75%)]" />

      {/* Horizon glow — the "floor" the mockup sits on */}
      <div className="absolute top-[62%] left-1/2 h-[40vh] w-[70vw] -translate-x-1/2 rounded-[100%] bg-mint/10 blur-[100px]" />

      {/* Vignette to keep edges dark */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_70%_at_50%_30%,transparent_40%,#020a06_100%)]" />
    </div>
  );
}
