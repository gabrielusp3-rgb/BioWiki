"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button, Container, Section } from "@/components/ui";
import { ExternalIcon } from "@/components/ui/Icons";
import { CodeBlock } from "@/components/api/CodeBlock";
import { EndpointList } from "@/components/api/EndpointList";
import { ApiKeyPanel } from "@/components/api/ApiKeyPanel";
import { fadeInUp, staggerContainer } from "@/lib/animations";
import { API_FEATURES, FORMAT_SAMPLES, REQUEST_SAMPLES } from "@/lib/api-docs";

export function ApiSection() {
  return (
    <Container width="wide">
      <Section
        eyebrow="API"
        title="A REST API built for bioinformatics"
        description="Query the local catalogue at /api/v1. JSON on list endpoints; FASTA, CSV, JSON and GenBank on /download. Optional X-API-Key. Rate-limited per process."
      >
        {/* Feature strip */}
        <motion.div
          variants={staggerContainer(0.08, 0.04)}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3"
        >
          {API_FEATURES.map((feature) => (
            <motion.div key={feature.title} variants={fadeInUp} className="glass hairline p-5">
              <h3 className="mb-2 font-display text-sm font-bold uppercase tracking-wide text-content-primary">
                {feature.title}
              </h3>
              <p className="text-sm leading-relaxed text-content-secondary">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Endpoints + examples */}
          <div className="flex flex-col gap-6 lg:col-span-2">
            <div className="flex flex-col gap-3">
              <span className="eyebrow">REST Endpoints</span>
              <EndpointList />
            </div>

            <div className="flex flex-col gap-3">
              <span className="eyebrow">Usage Examples</span>
              <CodeBlock tabs={REQUEST_SAMPLES} />
            </div>

            <div className="flex flex-col gap-3">
              <span className="eyebrow">Response Formats · JSON · FASTA · CSV</span>
              <CodeBlock tabs={FORMAT_SAMPLES} />
            </div>
          </div>

          {/* API key + docs CTA */}
          <div className="flex flex-col gap-6">
            <ApiKeyPanel />

            <div className="glass hairline flex flex-col gap-4 p-6">
              <span className="eyebrow">API Documentation</span>
              <p className="text-sm leading-relaxed text-content-secondary">
                Explore the complete reference: endpoints, schemas, pagination,
                error codes and SDK examples.
              </p>
              <Link href="/api">
                <Button variant="glass" fullWidth trailingIcon={<ExternalIcon className="h-4 w-4" />}>
                  Read the docs
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </Section>
    </Container>
  );
}
