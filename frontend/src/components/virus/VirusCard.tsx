"use client";

import { motion } from "framer-motion";
import { Badge, Card, CardBody, CardFooter, CardHeader, CardTitle, Button } from "@/components/ui";
import { hoverLift } from "@/lib/animations";
import { formatBases } from "@/lib/virus";
import type { VirusSequence } from "@/types/virus";

interface VirusCardProps {
  virus: VirusSequence;
  onView: (virus: VirusSequence) => void;
}

export function VirusCard({ virus, onView }: VirusCardProps) {
  return (
    <motion.div variants={hoverLift} initial="rest" whileHover="hover" className="h-full">
      <Card category="virus" className="flex h-full flex-col">
        <CardHeader>
          <div className="flex min-w-0 flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge category="virus" />
              <Badge tone="danger">{virus.genomeType}</Badge>
              {virus.segment && <Badge tone="neutral">Seg {virus.segment}</Badge>}
            </div>
            <CardTitle className="truncate" title={virus.name}>
              {virus.name}
            </CardTitle>
            <span className="font-mono text-xs text-content-secondary">
              {virus.accession}
              {virus.version ? `.${virus.version}` : ""}
            </span>
          </div>
        </CardHeader>

        <CardBody className="flex-1">
          <span className="italic text-content-secondary">{virus.organism}</span>
          <div className="mt-2 flex flex-col gap-1 text-xs text-content-secondary">
            <span>Family · {virus.family}</span>
            {virus.host && <span>Host · {virus.host}</span>}
          </div>
        </CardBody>

        <CardFooter>
          <span className="flex flex-col">
            <span className="font-mono text-sm text-content-primary">{formatBases(virus)}</span>
            <span className="text-[10px] uppercase tracking-wider text-content-muted">Length</span>
          </span>
          <Button variant="ghost" size="sm" onClick={() => onView(virus)}>
            View
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  );
}
