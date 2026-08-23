"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";

export interface CodeTab {
  id: string;
  label: string;
  language: string;
  code: string;
}

export interface CodeBlockProps {
  tabs: CodeTab[];
  className?: string;
}

export function CodeBlock({ tabs, className }: CodeBlockProps) {
  const [active, setActive] = useState(tabs[0]?.id ?? "");
  const { copied, copy } = useCopyToClipboard();
  const current = tabs.find((t) => t.id === active) ?? tabs[0];

  if (!current) return null;

  return (
    <div className={cn("glass-strong flex flex-col overflow-hidden", className)}>
      <div className="flex items-center justify-between border-b border-glass-divider">
        <div className="flex">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActive(tab.id)}
              className={cn(
                "border-b-2 px-4 py-3 font-display text-[11px] font-semibold uppercase tracking-wide transition-colors",
                tab.id === active
                  ? "border-b-category-dna text-content-primary"
                  : "border-b-transparent text-content-secondary hover:text-content-primary",
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => copy(current.code)}
          className="mr-3 border border-glass-border px-3 py-1.5 font-display text-[10px] font-semibold uppercase tracking-wider text-content-secondary transition-colors hover:border-white/30 hover:text-content-primary"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="no-scrollbar overflow-x-auto p-5 text-sm leading-relaxed">
        <code className="font-mono text-content-primary [&_*]:font-mono">{current.code}</code>
      </pre>
    </div>
  );
}
