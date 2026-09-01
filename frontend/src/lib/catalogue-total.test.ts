import { describe, expect, it } from "vitest";
import { catalogueTotalDisplay } from "@/lib/catalogue-total";

describe("catalogueTotalDisplay", () => {
  it("uses the live list total once the catalogue has loaded", () => {
    expect(catalogueTotalDisplay("success", 7442, "DNA sequences")).toEqual({
      kind: "ready",
      text: "7,442 DNA sequences",
      total: 7442,
    });
  });

  it("does not invent a count when the API is down", () => {
    expect(catalogueTotalDisplay("unavailable", 0, "RNA sequences")).toEqual({
      kind: "unavailable",
      text: "Live counts unavailable",
    });
    expect(catalogueTotalDisplay("error", 0, "Proteins")).toEqual({
      kind: "unavailable",
      text: "Live counts unavailable",
    });
  });

  it("keeps the previous total visible while a later page request is in flight", () => {
    expect(catalogueTotalDisplay("loading", 2867, "RNA sequences")).toEqual({
      kind: "ready",
      text: "2,867 RNA sequences",
      total: 2867,
    });
  });
});
