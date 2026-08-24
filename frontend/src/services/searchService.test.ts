import { describe, expect, it } from "vitest";
import { toParams } from "./searchService";
import { DEFAULT_FILTERS } from "@/types/search";

describe("toParams", () => {
  it("maps a query and default filters to API parameters", () => {
    const params = toParams("NM_000207", DEFAULT_FILTERS, 20);
    expect(params.q).toBe("NM_000207");
    expect(params.limit).toBe(20);
    expect(params.types).toBeUndefined();
    expect(params.source).toBeUndefined();
  });

  it("joins selected sequence types", () => {
    const params = toParams(
      "insulin",
      { ...DEFAULT_FILTERS, types: ["protein", "dna"] },
      10,
    );
    expect(params.types).toBe("protein,dna");
    expect(params.limit).toBe(10);
  });
});
