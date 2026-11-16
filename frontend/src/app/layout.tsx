import type { Metadata, Viewport } from "next";
import { Montserrat, Space_Grotesk } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FlowBill · Invoicing that gets freelancers paid faster",
  description:
    "FlowBill turns every invoice into a secure payment link. Clients pay by card, bank transfer or USSD in NGN, USD, GBP or EUR. No login, no chasing.",
  other: {
    "page-type": "software",
    "site-kind": "software",
  },
  openGraph: {
    title: "FlowBill · Invoicing that gets freelancers paid faster",
    description:
      "Send the invoice. Get paid in days, not weeks. Join the FlowBill waitlist.",
    type: "website",
  },
  twitter: { card: "summary_large_image" },
};

export const viewport: Viewport = {
  themeColor: "#27325E",
};

/* Direction contract (design.md §0), emitted as an HTML comment so it survives the build. */
const CONTRACT = `<!--
THESIS     The invoice is the payment page. Show money moving from "Sent" to "Paid" on the first screen.
WORLD      Navy ledger at night, with coral as the moment of payment. Space Grotesk numerals, Montserrat prose, lots of air.
FIRST VIEW Diagonal navy field with drifting moons. Two-line headline left. On the right, a rotated live FlowBill dashboard with floating cards.
SIGNATURE  Pinned "Create, Send, Paid" scroll story: one invoice card changes state as you scroll.
RISK       Mirrors the inspiration by owner request; FlowBill copy, data and UI keep it ours.
-->`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      data-type="software"
      className={`${spaceGrotesk.variable} ${montserrat.variable}`}
    >
      <body>
        <div hidden dangerouslySetInnerHTML={{ __html: CONTRACT }} />
        <a
          href="#main"
          className="sr-only z-[100] rounded-btn bg-white px-5 py-3 font-medium text-ink focus:not-sr-only focus:fixed focus:top-4 focus:left-4"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
