import { describe, expect, it } from "vitest";
import { safeHttpUrl } from "./safe-url";

describe("safeHttpUrl", () => {
  it("keeps https provenance links and drops other schemes", () => {
    expect(safeHttpUrl("https://www.wikidata.org/wiki/Q17101")).toBe(
      "https://www.wikidata.org/wiki/Q17101",
    );
    expect(safeHttpUrl("javascript:alert(1)")).toBeNull();
    expect(safeHttpUrl("not a url")).toBeNull();
  });
});
