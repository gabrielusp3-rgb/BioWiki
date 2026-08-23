"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { API_BASE, API_ENDPOINTS, type ApiEndpoint } from "@/lib/api-docs";
import { ChevronRightIcon } from "@/components/ui/Icons";

function EndpointRow({ endpoint }: { endpoint: ApiEndpoint }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-glass-divider last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-white/[0.03]"
      >
        <span className="w-12 shrink-0 border border-category-dna/40 bg-category-dna/10 px-2 py-1 text-center font-display text-[10px] font-bold uppercase tracking-wider text-category-dna">
          {endpoint.method}
        </span>
        <code className="shrink-0 font-mono text-sm text-content-primary">{endpoint.path}</code>
        <span className="hidden flex-1 truncate text-sm text-content-secondary md:block">
          {endpoint.summary}
        </span>
        <ChevronRightIcon
          className={cn(
            "ml-auto h-4 w-4 shrink-0 text-content-muted transition-transform duration-200",
            open && "rotate-90",
          )}
        />
      </button>

      {open && (
        <div className="border-t border-glass-divider bg-black/30 px-5 py-4">
          <p className="mb-4 text-sm text-content-secondary md:hidden">{endpoint.summary}</p>
          <code className="mb-4 block font-mono text-xs text-content-muted">
            {API_BASE}
            {endpoint.path}
          </code>
          {endpoint.params.length > 0 && (
            <div className="flex flex-col gap-2">
              <span className="eyebrow">Parameters</span>
              <div className="flex flex-col divide-y divide-glass-divider/60">
                {endpoint.params.map((param) => (
                  <div key={param.name} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 py-2">
                    <code className="font-mono text-xs text-category-dna">{param.name}</code>
                    <span className="font-mono text-[11px] text-content-muted">{param.type}</span>
                    {param.required && (
                      <span className="font-display text-[10px] uppercase tracking-wider text-state-danger">
                        required
                      </span>
                    )}
                    <span className="w-full text-xs text-content-secondary sm:w-auto sm:flex-1">
                      {param.description}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function EndpointList() {
  return (
    <div className="glass overflow-hidden">
      {API_ENDPOINTS.map((endpoint) => (
        <EndpointRow key={endpoint.path} endpoint={endpoint} />
      ))}
    </div>
  );
}
