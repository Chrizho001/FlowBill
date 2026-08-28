import { Hero } from "@/components/landing/hero";

export default function Home() {
  return (
    <main className="relative">
      <Hero />
      {/* Later landing phases (features, pricing, footer…) compose here. */}
    </main>
  );
}
