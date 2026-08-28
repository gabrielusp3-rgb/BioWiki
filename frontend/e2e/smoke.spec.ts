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

test("home page renders the catalogue title", async ({ page }) => {
  await page.goto("/");
  await waitForSplash(page);
  await expect(page.getByRole("link", { name: /biowiki/i }).first()).toBeVisible();
});

test("primary navigation reaches DNA, search, license; API is not a catalogue item", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await waitForSplash(page);
  await page.getByRole("banner").getByRole("link", { name: "DNA", exact: true }).click();
  await expect(page).toHaveURL(/\/dna/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: /DNA/i }).first()).toBeVisible();
  await expect(page.getByRole("banner").getByRole("link", { name: "API", exact: true })).toHaveCount(0);

  await page.goto("/search");
  await waitForSplash(page);
  await expect(page.getByLabel("Search catalogue")).toBeVisible();

  await page.goto("/license");
  await waitForSplash(page);
  await expect(page.getByText(/DDBJ/i).first()).toBeVisible();
});

test("home page does not embed the developer API", async ({ page }) => {
  await page.goto("/");
  await waitForSplash(page);
  await expect(page.getByText(/A REST API BUILT FOR BIOINFORMATICS/i)).toHaveCount(0);
});

test("legacy /api path redirects to the public OpenAPI", async ({ request, baseURL }) => {
  const res = await request.get(`${baseURL}/api`, { maxRedirects: 0 });
  expect([301, 302, 307, 308]).toContain(res.status());
  expect(res.headers()["location"] ?? "").toContain("biowiki-api.vercel.app/docs");
});

test("catalogue sections render without crashing", async ({ page }) => {
  test.setTimeout(120_000);
  const routes: Array<{ path: string; heading: string }> = [
    { path: "/rna", heading: "RNA sequence database" },
    { path: "/proteins", heading: "Protein sequence database" },
    { path: "/crispr", heading: "CRISPR guide database" },
    { path: "/genomes", heading: "Genome sequence database" },
    { path: "/virus", heading: "Virus sequence database" },
    { path: "/organisms", heading: "Organism catalogue" },
    { path: "/publications", heading: "Publication catalogue" },
    { path: "/downloads", heading: "Downloads" },
  ];
  for (const route of routes) {
    await page.goto(route.path);
    await waitForSplash(page);
    await expect(page.getByRole("heading", { name: route.heading }).first()).toBeVisible();
  }
});

test("unknown routes show the not-found page", async ({ page }) => {
  await page.goto("/this-route-does-not-exist");
  await waitForSplash(page);
  await expect(page.getByRole("heading", { name: /not found/i })).toBeVisible();
});

test("search reports empty or real results without fabricating records", async ({ page }) => {
  await page.goto("/search");
  await waitForSplash(page);
  const input = page.getByLabel("Search catalogue");
  const searchResponse = page
    .waitForResponse(
      (res) => res.url().includes("/search") && !res.url().includes("suggest"),
      { timeout: 15_000 },
    )
    .catch(() => null);
  await input.fill("insulin");
  await searchResponse;
  await expect(
    page.getByRole("main").getByText(
      /ordered by relevance|No matches found in the database|temporarily unavailable|sequence database is connected/,
    ),
  ).toBeVisible({ timeout: 20_000 });
  const firstHit = page.getByRole("main").locator('a[href*="/sequences/"]').first();
  if ((await firstHit.count()) > 0) {
    await firstHit.click();
    await expect(page).toHaveURL(/\/sequences\//, { timeout: 30_000 });
  }
});

test("API liveness probe responds when the backend is running", async ({ request }) => {
  const apiBase = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8000/api/v1";
  const response = await request.get(`${apiBase}/health`);
  test.skip(response.status() === 0 || response.status() >= 500, "API is not running");
  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toMatchObject({ status: "ok" });
});
