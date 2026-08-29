"""CRISPRCasdb is evaluated, not scraped.

Official site: https://crisprcas.i2bc.paris-saclay.fr/

The project publishes downloadable SQL / repeat / spacer dumps for academic
use, typically behind an explicit download agreement rather than a public
unauthenticated bulk API. BioWiki therefore does not scrape CRISPRCasdb HTML
and does not invent arrays, spacers, or Cas clusters from family names.

Natural CRISPR records in this expansion come from NCBI records that are
already annotated as CRISPR. Computational Cas9 NGG sites are labeled
COMPUTATIONAL_TARGET and are never experimental.
"""

from __future__ import annotations

CRISPRCASDB_STATUS = "EXTERNAL_LIMITATION"
CRISPRCASDB_REASON = (
    "Official CRISPRCasdb bulk dumps require an academic download agreement; "
    "no unauthenticated public dump is ingested. NCBI-annotated CRISPR loci "
    "and computational NGG scans remain the CRISPR sources."
)


def crisprcasdb_integration_status() -> dict[str, str]:
    return {"status": CRISPRCASDB_STATUS, "reason": CRISPRCASDB_REASON}
