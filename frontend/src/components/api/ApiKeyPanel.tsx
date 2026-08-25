"use client";

import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";

const HEADER_EXAMPLE = "X-API-Key: <YOUR_API_KEY>";

export function ApiKeyPanel() {
  const { copied, copy } = useCopyToClipboard();

  return (
    <div className="glass hairline flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <span className="eyebrow">API Key</span>
        <span className="h-1.5 w-1.5 bg-category-dna shadow-glow-dna" />
      </div>

      <p className="text-sm leading-relaxed text-content-secondary">
        Authentication is optional for the public read-only API; rate limiting
        applies. With an empty
        <code className="mx-1 font-mono text-category-dna">API_KEYS</code>
        list the HTTP API is open. When keys are configured on the server, send
        <code className="mx-1 font-mono text-category-dna">X-API-Key: &lt;YOUR_API_KEY&gt;</code>
        . There is no key signup in this application.
      </p>

      <div className="flex items-center justify-between gap-3 border border-glass-border bg-black/40 px-4 py-3">
        <code className="truncate font-mono text-xs text-content-primary">{HEADER_EXAMPLE}</code>
        <button
          type="button"
          onClick={() => copy(HEADER_EXAMPLE)}
          className="shrink-0 border border-glass-border px-3 py-1.5 font-display text-[10px] font-semibold uppercase tracking-wider text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <div className="flex flex-col gap-3 border-t border-glass-divider pt-4">
        <div className="flex items-baseline justify-between">
          <span className="text-sm text-content-secondary">Default limit</span>
          <span className="font-mono text-sm text-content-primary">120 req / 60 s</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="text-sm text-content-secondary">Scope</span>
          <span className="font-mono text-sm text-content-primary">per process</span>
        </div>
      </div>
    </div>
  );
}
