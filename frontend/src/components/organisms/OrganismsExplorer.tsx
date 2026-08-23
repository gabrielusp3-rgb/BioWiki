"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { OrganismCard, Skeleton } from "@/components/ui";
import { SearchIcon } from "@/components/ui/Icons";
import { Tag } from "@/components/ui/Tag";
import { staggerContainer, fadeInUp } from "@/lib/animations";
import { listOrganisms } from "@/services/organismService";
import { GROUP_LABEL } from "@/lib/organisms";
import type { Organism, OrganismGroup } from "@/types/organism";

const GROUPS: OrganismGroup[] = ["animal", "plant", "fungus", "bacteria", "archaea", "virus", "protozoan"];

export function OrganismsExplorer() {
  const [organisms, setOrganisms] = useState<Organism[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState<OrganismGroup | "all">("all");

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    listOrganisms({ signal: controller.signal })
      .then((response) => {
        setOrganisms(response.organisms);
        setTotal(response.total);
      })
      .catch(() => {
        setOrganisms([]);
        setTotal(0);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return organisms.filter((organism) => {
      if (group !== "all" && organism.group !== group) return false;
      if (!q) return true;
      return (
        organism.scientificName.toLowerCase().includes(q) ||
        organism.commonName?.toLowerCase().includes(q) ||
        String(organism.taxId).includes(q)
      );
    });
  }, [organisms, query, group]);

  return (
    <div className="flex flex-col gap-6">
      <div
        className={cn(
          "glass hairline flex items-center gap-3 px-4 transition-colors duration-200",
          "focus-within:border-category-dna/50",
        )}
      >
        <SearchIcon className="h-5 w-5 shrink-0 text-content-secondary" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search organisms by scientific name, common name or NCBI tax id…"
          className="h-14 w-full bg-transparent font-body text-base text-content-primary outline-none placeholder:text-content-muted"
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="shrink-0 text-xs uppercase tracking-wider text-content-muted hover:text-content-primary"
          >
            Clear
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Tag active={group === "all"} onClick={() => setGroup("all")}>
          All groups
        </Tag>
        {GROUPS.map((g) => (
          <Tag key={g} active={group === g} onClick={() => setGroup(g)}>
            {GROUP_LABEL[g]}
          </Tag>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-content-muted">
          {loading ? "Loading…" : `${filtered.length} of ${total} organisms`}
        </span>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} height={340} />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <motion.div
          variants={staggerContainer(0.05, 0.03)}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {filtered.map((organism) => (
            <motion.div key={organism.id} variants={fadeInUp} className="h-full">
              <OrganismCard organism={organism} />
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <div className="glass hairline p-8 text-center text-sm text-content-secondary">
          No organisms match “{query}”.
        </div>
      )}
    </div>
  );
}
