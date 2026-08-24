"use client";

import { useMemo, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

function classFor(ch: string): string {
  const c = ch.toUpperCase();
  if (c === "A") return "res-A";
  if (c === "T") return "res-T";
  if (c === "U") return "res-U";
  if (c === "G") return "res-G";
  if (c === "C") return "res-C";
  return "res-N";
}

export function SequenceViewer({
  residues,
  accession,
  isProtein = false,
}: {
  residues?: string | null;
  accession: string;
  isProtein?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const perLine = 60;

  const lines = useMemo(() => {
    const seq = (residues ?? "").replace(/\s+/g, "");
    const out: { start: number; chunk: string }[] = [];
    for (let i = 0; i < seq.length; i += perLine) {
      out.push({ start: i + 1, chunk: seq.slice(i, i + perLine) });
    }
    return out;
  }, [residues]);

  if (!residues) {
    return (
      <div className="glass p-6 text-sm text-neutral-500">
        No residue data stored for this record.
      </div>
    );
  }

  const copy = () => {
    navigator.clipboard.writeText(residues).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <div className="glass">
      <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
        <span className="eyebrow">Sequence · {residues.length} {isProtein ? "aa" : "nt"}</span>
        <div className="flex gap-2">
          <button
            onClick={copy}
            className="glass glass-hover px-3 py-1.5 text-[0.6rem] uppercase tracking-widest text-white"
          >
            {copied ? "Copied" : "Copy"}
          </button>
          {API_BASE_URL ? (
            <a
              href={`${API_BASE_URL}/download/sequence/${encodeURIComponent(accession)}?format=fasta`}
              className="glass glass-hover px-3 py-1.5 text-[0.6rem] uppercase tracking-widest text-white"
            >
              FASTA
            </a>
          ) : null}
        </div>
      </div>
      <div className="max-h-96 overflow-auto p-5 font-mono text-xs leading-6">
        {lines.map((l) => (
          <div key={l.start} className="flex gap-4">
            <span className="w-12 shrink-0 select-none text-right text-neutral-700">
              {l.start}
            </span>
            <span className="break-all">
              {l.chunk.split("").map((ch, i) => (
                <span key={i} className={isProtein ? "text-neutral-300" : classFor(ch)}>
                  {ch}
                </span>
              ))}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
