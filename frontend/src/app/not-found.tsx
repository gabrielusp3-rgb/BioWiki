import Link from "next/link";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Button, Container } from "@/components/ui";
import { HelixIcon, ChevronRightIcon } from "@/components/ui/Icons";

export default function NotFound() {
  return (
    <>
      <SiteHeader />
      <main id="main" className="flex min-h-[100dvh] items-center justify-center pt-16">
        <Container width="narrow" className="flex flex-col items-center gap-6 text-center">
          <span className="grid h-16 w-16 place-items-center border border-glass-border bg-glass-surface text-category-dna shadow-glow-dna">
            <HelixIcon className="h-8 w-8" />
          </span>
          <span className="eyebrow">404 · Not Found</span>
          <h1 className="font-display text-4xl font-bold uppercase tracking-tightest text-content-primary sm:text-5xl">
            Sequence not found
          </h1>
          <p className="max-w-md text-balance text-base leading-relaxed text-content-secondary">
            The page you are looking for does not exist, or the record has moved. Try searching the
            database or return to the homepage.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link href="/">
              <Button variant="primary" trailingIcon={<ChevronRightIcon className="h-4 w-4" />}>
                Back to home
              </Button>
            </Link>
            <Link href="/search">
              <Button variant="outline">Search the database</Button>
            </Link>
          </div>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
