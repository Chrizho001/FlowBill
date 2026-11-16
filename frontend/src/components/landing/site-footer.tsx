import { Logo } from "@/components/ui/logo";
import { footer } from "@/content/landing";

const columns = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "#features" },
      { label: "How it works", href: "#how-it-works" },
      { label: "Pricing", href: "#pricing" },
      { label: "FAQ", href: "#faq" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Join the waitlist", href: "#join" },
      { label: "Contact", href: `mailto:${footer.email}` },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "#" },
      { label: "Terms", href: "#" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-white/10 bg-navy-950 text-white">
      <div className="container grid gap-14 py-20 md:grid-cols-12 md:gap-8 lg:py-24">
        <div className="md:col-span-5">
          <Logo tone="white" className="text-[26px]" />
          <p className="mt-4 max-w-xs text-navy-300">{footer.tagline}</p>
        </div>
        {columns.map((c) => (
          <div key={c.title} className="md:col-span-2">
            <h3 className="font-sans text-[13px] font-medium tracking-[0.14em] text-navy-300 uppercase">{c.title}</h3>
            <ul className="mt-5 space-y-1">
              {c.links.map((l) => (
                <li key={l.label}>
                  <a href={l.href} className="link-draw inline-flex min-h-11 items-center text-[0.9375rem] text-white/85 hover:text-white">
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="container">
        <div className="flex flex-col gap-3 border-t border-white/10 py-8 text-[13px] text-navy-300 sm:flex-row sm:justify-between">
        <p>© 2026 FlowBill · {footer.place}</p>
        <p>Visa, Mastercard and Tether marks via Simple Icons; trademarks belong to their owners.</p>
        </div>
      </div>
    </footer>
  );
}
