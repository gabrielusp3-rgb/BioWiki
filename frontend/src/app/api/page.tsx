import type { Metadata } from "next";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Container, Section } from "@/components/ui";
import { EndpointList } from "@/components/api/EndpointList";
import { ApiKeyPanel } from "@/components/api/ApiKeyPanel";
import { CodeBlock } from "@/components/api/CodeBlock";
import { REQUEST_SAMPLES } from "@/lib/api-docs";

export const metadata: Metadata = {
  title: "API",
  description:
    "Programmatic access to real BIOWIKI sequence records. Versioned under /api/v1 with cursor pagination.",
  alternates: { canonical: "/api" },
};

export default function ApiPage() {
  return (
    <>
      <SiteHeader activeHref="/api" />
      <main id="main" className="pt-16">
        <Container width="wide">
          <Section
            eyebrow="Developer API"
            title="REST API reference"
            description="Versioned under /api/v1. Cursor pagination via nextCursor. Optional API key via the X-API-Key header."
          >
            <div className="flex flex-col gap-10">
              <EndpointList />
              <ApiKeyPanel />
              <CodeBlock tabs={REQUEST_SAMPLES} />
            </div>
          </Section>
        </Container>
      </main>
      <SiteFooter />
    </>
  );
}
