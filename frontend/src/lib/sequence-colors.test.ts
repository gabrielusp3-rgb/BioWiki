import { describe, expect, it } from "vitest";
import { rnaLetters } from "./sequence-colors";

describe("rnaLetters", () => {
  it("maps NCBI transcript T to RNA U without inventing residues", () => {
    expect(rnaLetters("ATGCU")).toBe("AUGCU");
    expect(rnaLetters("atgc")).toBe("augc");
    expect(rnaLetters("ACGU")).toBe("ACGU");
  });
});
