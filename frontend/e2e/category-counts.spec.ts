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

const STATISTICS = {
  totalSequences: 16433,
  totalResidues: 1,
  organisms: 1881,
  genes: 1,
  genomes: 107,
  publications: 36190,
  linkedPublications: 1,
  categories: [
    { key: "dna", label: "DNA", count: 7442, totalResidues: 1, distinctOrganisms: 412 },
    { key: "rna", label: "RNA", count: 2867, totalResidues: 1, distinctOrganisms: 210 },
    { key: "protein", label: "Proteins", count: 4352, totalResidues: 1, distinctOrganisms: 380 },
    { key: "crispr", label: "CRISPR", count: 443, totalResidues: 1, distinctOrganisms: 40 },
    { key: "virus", label: "Viruses", count: 1329, totalResidues: 1, distinctOrganisms: 190 },
    { key: "genome", label: "Genomes", count: 107, totalResidues: 0, distinctOrganisms: 34 },
  ],
  sync: { status: "updated", activeImports: 0, countsInSync: true, lastRun: null },
  lastUpdated: null,
};

async function mockStatistics(page: Page) {
  await page.route(/\/api\/v1\/statistics/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(STATISTICS),
    });
  });
}

test("DNA page shows the live catalogue total in a stat card, not three times", async ({ page }) => {
  await mockStatistics(page);
  await page.route(/\/api\/v1\/sequences/, async (route) => {
    const type = new URL(route.request().url()).searchParams.get("type");
    if (type !== "dna") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [
          {
            id: "00000000-0000-4000-a000-000000000001",
            accession: "M29350",
            version: "1",
            name: "E2E DNA",
            organism: "E2E organism",
            source: "NCBI GenBank",
            moleculeType: "genomic",
            strand: "+",
            length: 837,
            gcContent: 0.458,
            sequence: null,
          },
        ],
        total: 7442,
        nextCursor: null,
      }),
    });
  });

  await page.goto("/dna");
  await waitForSplash(page);
  await expect(page.getByTestId("category-stat-cards").locator("[data-testid]")).toHaveCount(3);
  await expect(page.getByTestId("live-count-dna")).toHaveAttribute(
    "aria-label",
    /7,442 DNA sequences stored/i,
  );
  await expect(page.getByTestId("live-count-dna-organisms")).toHaveAttribute(
    "aria-label",
    /412 Organisms with DNA-level data/i,
  );
  await expect(page.getByTestId("live-count-organisms-tracked")).toHaveAttribute(
    "aria-label",
    /1,881 Organisms tracked \(database\)/i,
  );
  await expect(page.getByText(/public sources/i)).toHaveCount(0);
  await expect(page.getByText(/export formats/i)).toHaveCount(0);
  await expect(page.getByText(/nucleotides stored/i)).toHaveCount(0);
  await expect(page.getByTestId("catalogue-list-total")).toHaveCount(0);
});

test("RNA, proteins, CRISPR and virus pages show live catalogue totals", async ({ page }) => {
  test.setTimeout(120_000);
  await mockStatistics(page);

  await page.route(/\/api\/v1\/sequences/, async (route) => {
    const type = new URL(route.request().url()).searchParams.get("type");
    if (type === "rna") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          results: [
            {
              id: "00000000-0000-4000-a000-000000000002",
              accession: "NM_E2E",
              version: "1",
              name: "E2E RNA",
              organism: "E2E organism",
              source: "NCBI RefSeq",
              rnaClass: "mrna",
              isCoding: true,
              length: 120,
              gcContent: 0.42,
              sequence: null,
            },
          ],
          total: 2867,
          nextCursor: null,
        }),
      });
      return;
    }
    if (type === "crispr") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          results: [
            {
              id: "00000000-0000-4000-a000-000000000004",
              accession: "CRISPR_E2E",
              name: "E2E CRISPR",
              organism: "E2E organism",
              source: "NCBI",
              system: "cas9",
              evidenceType: "experimental_guide",
              targetGene: "GENE",
              pam: "NGG",
              guideLength: 20,
              onTargetScore: null,
              offTargetScore: null,
            },
          ],
          total: 443,
          nextCursor: null,
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.route(/\/api\/v1\/proteins/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [
          {
            id: "00000000-0000-4000-a000-000000000003",
            accession: "P00000",
            name: "E2E protein",
            organism: "E2E organism",
            source: "UniProt",
            reviewed: true,
            length: 100,
            molecularWeight: null,
            pdbIds: [],
            domains: [],
            sequence: null,
          },
        ],
        total: 4352,
        nextCursor: null,
      }),
    });
  });

  await page.route(/\/api\/v1\/viruses/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [
          {
            id: "00000000-0000-4000-a000-000000000005",
            accession: "NC_E2E",
            version: "1",
            name: "E2E virus",
            organism: "E2E virus",
            source: "NCBI RefSeq",
            family: "Testviridae",
            genomeType: "dsDNA",
            molecule: "dna",
            length: 1000,
            sequence: null,
          },
        ],
        total: 1329,
        nextCursor: null,
      }),
    });
  });

  await page.goto("/rna");
  await waitForSplash(page);
  await expect(page.getByTestId("live-count-rna")).toHaveAttribute(
    "aria-label",
    /2,867 RNA sequences stored/i,
  );
  await expect(page.getByTestId("catalogue-list-total")).toHaveCount(0);

  await page.goto("/proteins");
  await waitForSplash(page);
  await expect(page.getByTestId("live-count-protein")).toHaveAttribute(
    "aria-label",
    /4,352 Proteins stored/i,
  );
  await expect(page.getByTestId("catalogue-list-total")).toHaveCount(0);

  await page.goto("/crispr");
  await waitForSplash(page);
  await expect(page.getByTestId("live-count-crispr")).toHaveAttribute(
    "aria-label",
    /443 CRISPR records stored/i,
  );
  await expect(page.getByTestId("catalogue-list-total")).toHaveCount(0);

  await page.goto("/virus");
  await waitForSplash(page);
  await expect(page.getByTestId("live-count-virus")).toHaveAttribute(
    "aria-label",
    /1,329 Viral sequences stored/i,
  );
  await expect(page.getByTestId("catalogue-list-total")).toHaveCount(0);
});
