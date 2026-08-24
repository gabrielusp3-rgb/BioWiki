import { describe, expect, it } from "vitest";
import { buildQuery } from "./api";

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
