import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Hero } from "@/components/sections/Hero";
import { LiveStatistics } from "@/components/sections/LiveStatistics";
import { GlobalSearch } from "@/components/sections/GlobalSearch";
import { Categories } from "@/components/sections/Categories";
import { FeaturedOrganisms } from "@/components/sections/FeaturedOrganisms";
import { ApiSection } from "@/components/sections/ApiSection";

export default function HomePage() {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[400] focus:border focus:border-glass-border focus:bg-bg-secondary focus:px-4 focus:py-2 focus:text-sm focus:text-content-primary"
      >
        Skip to content
      </a>
      <SiteHeader activeHref="/" />
      <main id="main">
        <Hero />
        <LiveStatistics />
        <GlobalSearch />
        <Categories />
        <FeaturedOrganisms />
        <ApiSection />
      </main>
      <SiteFooter />
    </>
  );
}
