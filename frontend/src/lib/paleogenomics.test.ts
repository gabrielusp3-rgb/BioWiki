import { describe, expect, it } from "vitest";
import { doiUrl, DEEXTINCTION_LABEL, EVIDENCE_LABEL, labelOf, SUBSECTION_LABEL } from "./paleogenomics";

describe("paleogenomics labels", () => {
  it("keeps paleogenomics as a collection, not a molecule type", () => {
    expect(SUBSECTION_LABEL.extinct_species).toBe("Extinct species");
    expect(SUBSECTION_LABEL.archaic_hominin).toBe("Archaic hominins");
    expect(EVIDENCE_LABEL.unknown).toMatch(/insufficient evidence/i);
    expect(labelOf(EVIDENCE_LABEL, "research_discussion")).toBe("research discussion");
    expect(DEEXTINCTION_LABEL.active_research_program).toBe("Active research program");
    expect(DEEXTINCTION_LABEL.no_active_program).toBe("No active program");
  });

  it("builds publisher DOI links without inventing identifiers", () => {
    expect(doiUrl("10.1111/j.1474-919x.2006.00478.x")).toBe(
      "https://doi.org/10.1111/j.1474-919x.2006.00478.x",
    );
    expect(doiUrl("https://doi.org/10.1080/08912960600639400")).toBe(
      "https://doi.org/10.1080/08912960600639400",
    );
  });
});
