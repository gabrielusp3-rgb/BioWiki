"use client";

import { motion } from "framer-motion";
import { Badge, Card, CardBody, CardFooter, CardHeader, CardTitle, Button } from "@/components/ui";
import { hoverLift } from "@/lib/animations";
import { formatAa, formatMw } from "@/lib/protein";
import type { ProteinSequence } from "@/types/protein";

interface ProteinCardProps {
  protein: ProteinSequence;
  onView: (protein: ProteinSequence) => void;
}

export function ProteinCard({ protein, onView }: ProteinCardProps) {
  return (
    <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
      <Card category="protein" className="flex h-full flex-col">
        <CardHeader>
          <div className="flex min-w-0 flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge category="protein" />
              {protein.reviewed ? (
                <Badge tone="success">Reviewed</Badge>
              ) : (
                <Badge tone="neutral">Unreviewed</Badge>
              )}
              {protein.pdbIds.length > 0 && <Badge tone="info">3D · {protein.pdbIds.length}</Badge>}
            </div>
            <CardTitle className="truncate" title={protein.name}>
              {protein.name}
            </CardTitle>
            <span className="font-mono text-xs text-content-secondary">
              {protein.accession}
              {protein.gene ? ` · ${protein.gene}` : ""}
            </span>
          </div>
        </CardHeader>

        <CardBody className="flex-1">
          <span className="italic text-content-secondary">{protein.organism}</span>
          {protein.function && (
            <p className="mt-2 line-clamp-2 text-sm text-content-secondary">{protein.function}</p>
          )}
        </CardBody>

        <CardFooter>
          <span className="flex flex-col">
            <span className="font-mono text-sm text-content-primary">{formatAa(protein.length)}</span>
            <span className="text-[10px] uppercase tracking-wider text-content-muted">
              {formatMw(protein.molecularWeight)}
            </span>
          </span>
          <Button variant="ghost" size="sm" onClick={() => onView(protein)}>
            View
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  );
}
