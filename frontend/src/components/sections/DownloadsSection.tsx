"use client";

import Link from "next/link";
import { Button } from "@/components/ui";
import { ChevronRightIcon, ExternalIcon } from "@/components/ui/Icons";
import { CodeBlock } from "@/components/api/CodeBlock";
import { CATEGORY_CARDS } from "@/lib/category-cards";
import { CATEGORY_META } from "@/lib/categories";
import { FORMAT_SAMPLES } from "@/lib/api-docs";

export function DownloadsSection() {
  return (
    <div className="flex flex-col gap-10">
      <p className="max-w-2xl text-balance text-base leading-relaxed text-content-secondary">
        Every record in BIOWIKI can be exported in <strong className="text-content-primary">FASTA</strong>,{" "}
        <strong className="text-content-primary">JSON</strong> or{" "}
        <strong className="text-content-primary">CSV</strong>. Open any explorer below to download
        individual records directly, or use the <code className="font-mono text-content-primary">/download</code>{" "}
        endpoint to script bulk exports.
      </p>

      {/* Per-category entry points */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CATEGORY_CARDS.map((data) => {
          const meta = CATEGORY_META[data.key];
          const { Icon } = data;
          return (
            <Link key={data.key} href={data.href} className="block h-full">
              <div
                className="glass hairline group flex h-full flex-col gap-4 p-5 transition-colors duration-300 hover:border-white/20"
                style={{ boxShadow: "none" }}
              >
                <div className="flex items-center justify-between">
                  <span
                    className="grid h-10 w-10 place-items-center border"
                    style={{
                      color: meta.color,
                      borderColor: `${meta.color}59`,
                      backgroundColor: `${meta.color}14`,
                    }}
                  >
                    <Icon className="h-5 w-5" />
                  </span>
                  <ChevronRightIcon className="h-4 w-4 text-content-muted transition-transform duration-300 group-hover:translate-x-1" />
                </div>
                <div>
                  <h3 className="font-display text-sm font-bold uppercase tracking-wide text-content-primary">
                    {data.label}
                  </h3>
                  <p className="mt-1 text-xs leading-relaxed text-content-secondary">
                    FASTA · JSON · CSV
                  </p>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Response formats */}
      <div className="flex flex-col gap-3">
        <span className="eyebrow">Export Formats</span>
        <CodeBlock tabs={FORMAT_SAMPLES} />
      </div>

      {/* Bulk export via API */}
      <div className="glass hairline flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1.5">
          <span className="eyebrow">Bulk exports</span>
          <p className="max-w-lg text-sm leading-relaxed text-content-secondary">
            Scripted, large-scale downloads are served through the authenticated REST API —
            consistent with how every individual record is exported.
          </p>
        </div>
        <a href="https://biowiki-api.vercel.app/docs" target="_blank" rel="noopener noreferrer">
          <Button variant="glass" trailingIcon={<ExternalIcon className="h-4 w-4" />}>
            OpenAPI reference
          </Button>
        </a>
      </div>
    </div>
  );
}
