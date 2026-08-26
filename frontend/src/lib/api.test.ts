import { describe, expect, it } from "vitest";
import { buildQuery, readNextCursor } from "./api";

describe("buildQuery", () => {
  it("omits empty and null values", () => {
    expect(buildQuery({ q: "insulin", cursor: null, limit: 20 })).toBe(
      "?q=insulin&limit=20",
    );
  });

  it("returns an empty string when there is nothing to send", () => {
    expect(buildQuery(undefined)).toBe("");
    expect(buildQuery({})).toBe("");
  });
});

describe("readNextCursor", () => {
  it("prefers nextCursor and ignores a missing snake_case twin", () => {
    expect(readNextCursor({ nextCursor: "Mg" })).toBe("Mg");
    expect(readNextCursor({ next_cursor: "Mg" })).toBe("Mg");
    expect(readNextCursor({ nextCursor: null, next_cursor: undefined })).toBe(null);
    expect(readNextCursor({})).toBe(null);
  });
});
