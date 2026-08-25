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

function fixtureAssemblies() {
  return [
    {
      id: "00000000-0000-4000-a000-000000000001",
      accession: "BW_E2E_GCA_001",
      assemblyName: "E2E fixture assembly 1",
      description: null,
      organism: "E2E fixture organism A",
      taxId: 1,
      source: "NCBI GenBank",
      assemblyLevel: "chromosome",
      totalLength: 1_000_000,
      chromosomeCount: 1,
      gcContent: null,
      releaseDate: null,
      sourceUrl: null,
      updatedAt: null,
    },
    {
      id: "00000000-0000-4000-a000-000000000002",
      accession: "BW_E2E_GCA_002",
      assemblyName: "E2E fixture assembly 2",
      description: null,
      organism: "E2E fixture organism B",
      taxId: 2,
      source: "NCBI GenBank",
      assemblyLevel: "complete",
      totalLength: 2_000_000,
      chromosomeCount: 1,
      gcContent: null,
      releaseDate: null,
      sourceUrl: null,
      updatedAt: null,
    },
    {
      id: "00000000-0000-4000-a000-000000000003",
      accession: "BW_E2E_GCA_003",
      assemblyName: "E2E fixture assembly 3",
      description: null,
      organism: "E2E fixture organism B",
      taxId: 2,
      source: "NCBI GenBank",
      assemblyLevel: "chromosome",
      totalLength: 3_000_000,
      chromosomeCount: 1,
      gcContent: null,
      releaseDate: null,
      sourceUrl: null,
      updatedAt: null,
    },
  ];
}

test("genome stat cards follow live list totals instead of remaining at zero", async ({
  page,
}) => {
  const assemblies = fixtureAssemblies();
  const stored = assemblies.length;
  const distinctOrganisms = new Set(assemblies.map((row) => row.organism)).size;
  const trackedOrganisms = 11;

  await page.route(/\/api\/v1\/genomes(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: assemblies,
        total: stored,
        nextCursor: null,
      }),
    });
  });
  await page.route(/\/api\/v1\/statistics(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        totalSequences: 0,
        totalResidues: 0,
        organisms: trackedOrganisms,
        genes: 0,
        genomes: stored,
        publications: 0,
        linkedPublications: 0,
        categories: [],
        sync: {
          status: "updated",
          activeImports: 0,
          countsInSync: true,
          lastRun: null,
        },
        lastUpdated: null,
      }),
    });
  });

  await page.goto("/genomes");
  await waitForSplash(page);

  await expect(page.getByText("BW_E2E_GCA_001")).toBeVisible();
  await expect(page.getByText("Complete assemblies stored")).toBeVisible();

  const storedCard = page.getByText("Complete assemblies stored").locator("xpath=ancestor::div[contains(@class,'relative')][1]");
  await expect(storedCard.getByText(String(stored), { exact: true })).toBeVisible();

  const genomeOrganismCard = page
    .getByText("Organisms with genome-level data")
    .locator("xpath=ancestor::div[contains(@class,'relative')][1]");
  await expect(genomeOrganismCard.getByText(String(distinctOrganisms), { exact: true })).toBeVisible();

  const trackedCard = page
    .getByText("Organisms tracked (database)")
    .locator("xpath=ancestor::div[contains(@class,'relative')][1]");
  await expect(trackedCard.getByText(String(trackedOrganisms), { exact: true })).toBeVisible();
});
