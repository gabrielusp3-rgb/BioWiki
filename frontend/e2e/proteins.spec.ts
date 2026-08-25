import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 1280, height: 720 });
});

async function waitForSplash(page: Page) {
  await page.waitForFunction(
    () => !document.documentElement.dataset.biowikiSplash,
    null,
    { timeout: 45_000 },
  );
}

const SEQUENCE =
  "MKKEKAIVVFSGGQDSTTCLLWALKEFEEVETVTFHYNQRSQEVEVAKSIAEKLGVKNH".repeat(4).slice(0, 219);

const PROTEIN = {
  id: "00000000-0000-4000-a000-000000000075",
  accession: "O31675",
  name: "7-cyano-7-deazaguanine synthase",
  gene: "queC",
  organism: "Bacillus subtilis (strain 168)",
  taxId: 224308,
  source: "UniProt",
  reviewed: true,
  length: SEQUENCE.length,
  molecularWeight: 24500,
  function:
    "Catalyzes the ATP-dependent conversion of 7-carboxy-7-deazaguanine (CDG) to 7-cyano-7-deazaguanine (preQ0).",
  pdbIds: ["3BLS"],
  domains: ["QueC"],
  updatedAt: null,
  sequence: null as string | null,
};

test("protein preview overlay keeps the residue view scrollable inside the viewport", async ({
  page,
}) => {
  await page.route(/\/api\/v1\/statistics(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        totalSequences: 1,
        totalResidues: SEQUENCE.length,
        organisms: 1,
        genes: 1,
        genomes: 0,
        publications: 0,
        linkedPublications: 0,
        categories: [{ key: "protein", label: "Protein", count: 1, totalResidues: SEQUENCE.length }],
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
  await page.route(/\/api\/v1\/proteins\/O31675(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ...PROTEIN, sequence: SEQUENCE }),
    });
  });
  await page.route(/\/api\/v1\/proteins(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ results: [PROTEIN], total: 1, nextCursor: null }),
    });
  });

  await page.goto("/proteins");
  await waitForSplash(page);
  await page.getByRole("button", { name: "View", exact: true }).click();

  await expect(page.getByRole("heading", { name: PROTEIN.name })).toBeVisible();
  const lengthValue = page.getByTitle("219 aa");
  const massValue = page.getByTitle("24.5 kDa");
  await expect(lengthValue).toBeVisible();
  await expect(massValue).toBeVisible();
  await expect(page.getByText("Sequence · Residue view")).toBeVisible();
  await expect(page.getByRole("button", { name: "Download FASTA" })).toBeInViewport();

  const functionBody = page.getByText(/ATP-dependent conversion of 7-carboxy-7-deazaguanine/);
  await expect(functionBody).toBeVisible();
  const lengthBox = await lengthValue.boundingBox();
  const functionBox = await functionBody.boundingBox();
  expect(lengthBox).toBeTruthy();
  expect(functionBox).toBeTruthy();
  expect(functionBox!.y).toBeGreaterThan(lengthBox!.y + lengthBox!.height - 2);

  const firstLine = SEQUENCE.slice(0, 60);
  const firstResidues = page.getByText(firstLine, { exact: true });
  await expect(firstResidues).toBeVisible();
  const firstBox = await firstResidues.boundingBox();
  expect(firstBox).toBeTruthy();
  expect(firstBox!.width).toBeGreaterThan(280);
  expect(firstBox!.height).toBeLessThan(40);

  const lastLine = SEQUENCE.slice(-SEQUENCE.length % 60 || 60);
  const lastResidues = page.getByText(lastLine, { exact: true });
  await lastResidues.scrollIntoViewIfNeeded();
  await expect(lastResidues).toBeInViewport();
  await expect(page.getByRole("button", { name: "Download FASTA" })).toBeInViewport();
});
