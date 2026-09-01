import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
});

async function waitForSplash(page: Page) {
  await page.waitForFunction(
    () => !document.documentElement.dataset.biowikiSplash,
    null,
    { timeout: 45_000 },
  );
}

function rnaRow(accession: string, name: string) {
  return {
    id: `00000000-0000-4000-a000-${accession.replace(/\D/g, "").padStart(12, "0").slice(-12)}`,
    accession,
    version: "1",
    name,
    organism: "E2E fixture organism",
    source: "NCBI RefSeq",
    rnaClass: "mrna",
    isCoding: true,
    length: 120,
    gcContent: 0.42,
    sequence: null,
  };
}

test("RNA catalogue Next loads the following page", async ({ page }) => {
  const first = rnaRow("NM_E2E_001", "E2E RNA page one");
  const second = rnaRow("NM_E2E_002", "E2E RNA page two");

  await page.route(/\/api\/v1\/statistics(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        totalSequences: 2,
        totalResidues: 240,
        organisms: 1,
        genes: 1,
        genomes: 0,
        publications: 0,
        linkedPublications: 0,
        categories: [{ key: "rna", label: "RNA", count: 2, totalResidues: 240, distinctOrganisms: 1 }],
        sync: { status: "updated", activeImports: 0, countsInSync: true, lastRun: null },
        lastUpdated: null,
      }),
    });
  });
  await page.route(/\/api\/v1\/sequences(\?|$)/, async (route) => {
    const url = new URL(route.request().url());
    if (url.searchParams.get("type") !== "rna") {
      await route.continue();
      return;
    }
    const cursor = url.searchParams.get("cursor");
    if (cursor === "page-2") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ results: [second], total: 2, nextCursor: null }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ results: [first], total: 2, nextCursor: "page-2" }),
    });
  });

  await page.goto("/rna");
  await waitForSplash(page);
  await expect(page.getByText("E2E RNA page one")).toBeVisible();
  await expect(page.getByText("E2E RNA page two")).toHaveCount(0);
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("E2E RNA page two")).toBeVisible();
  await expect(page.getByText("Page 2")).toBeVisible();
});
