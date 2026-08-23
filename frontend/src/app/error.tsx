"use client";

import { useEffect } from "react";
import Link from "next/link";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { Button, Container } from "@/components/ui";
import { HelixIcon } from "@/components/ui/Icons";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <>
      <SiteHeader />
      <main id="main" className="flex min-h-[100dvh] items-center justify-center pt-16">
        <Container width="narrow" className="flex flex-col items-center gap-6 text-center">
          <span className="grid h-16 w-16 place-items-center border border-glass-border bg-glass-surface text-state-danger">
            <HelixIcon className="h-8 w-8" />
          </span>
          <span className="eyebrow">Unexpected error</span>
          <h1 className="font-display text-4xl font-bold uppercase tracking-tightest text-content-primary sm:text-5xl">
            Something went wrong
          </h1>
          <p className="max-w-md text-balance text-base leading-relaxed text-content-secondary">
            The application hit an unexpected error. You can try again or return to the homepage.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button variant="primary" onClick={reset}>
              Try again
            </Button>
            <Link href="/">
              <Button variant="outline">Back to home</Button>
            </Link>
          </div>
        </Container>
      </main>
    </>
  );
}
