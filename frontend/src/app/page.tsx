import { Suspense } from "react";
import { Faq } from "@/components/landing/faq";
import { ScrollRefresh } from "@/components/scroll-refresh";
import { FeaturesBento } from "@/components/landing/features-bento";
import { FinalCta } from "@/components/landing/final-cta";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { Insights } from "@/components/landing/insights";
import { PortalShowcase } from "@/components/landing/portal-showcase";
import { Pricing } from "@/components/landing/pricing";
import { Rails } from "@/components/landing/rails";
import { SiteFooter } from "@/components/landing/site-footer";
import { SiteHeader } from "@/components/landing/site-header";
import { Voices } from "@/components/landing/voices";
import { WaitlistProvider } from "@/components/landing/waitlist-modal";
import { portalImage, steps, testimonials } from "@/content/landing";
import { publicFileExists } from "@/lib/assets";

export default function Home() {
  // Owner-generated images (see docs/image-prompts.md) replace the coded mockups when present.
  const stepImages = Object.fromEntries(
    steps.map((s) => [s.key, publicFileExists(s.image)]),
  );
  const portalHasImage = publicFileExists(portalImage);
  const photos = Object.fromEntries(
    testimonials.map((t) => [t.photo, publicFileExists(t.photo)]),
  );

  return (
    <WaitlistProvider>
      <SiteHeader />
      <main id="main">
        {/* Each section is its own Suspense boundary so React hydrates them independently and
            prioritises whatever the visitor taps first (selective hydration). */}
        <Hero />
        <Suspense>
          <Rails />
        </Suspense>
        <Suspense>
          <HowItWorks images={stepImages} />
        </Suspense>
        <Suspense>
          <FeaturesBento />
        </Suspense>
        <Suspense>
          <Insights />
        </Suspense>
        <Suspense>
          <PortalShowcase hasImage={portalHasImage} />
        </Suspense>
        <Suspense>
          <Voices photos={photos} />
        </Suspense>
        <Suspense>
          <Pricing />
        </Suspense>
        <Suspense>
          <Faq />
        </Suspense>
        <Suspense>
          <FinalCta />
        </Suspense>
      </main>
      <ScrollRefresh />
      <SiteFooter />
    </WaitlistProvider>
  );
}
