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

function fixturePublications() {
  return [
    {
      id: "00000000-0000-4000-a000-000000000201",
      pubmedId: 900000001,
      doi: null,
      pmcId: null,
      title: "E2E fixture publication one",
      abstract: "Fixture abstract one.",
      authors: ["Fixture Author A", "Fixture Author B"],
      journal: "E2E Journal",
      year: 2020,
      volume: "1",
      pages: "1-2",
      url: null,
    },
    {
      id: "00000000-0000-4000-a000-000000000202",
      pubmedId: 900000002,
      doi: null,
      pmcId: null,
      title: "E2E fixture publication two",
      abstract: null,
      authors: ["Fixture Author C"],
      journal: "E2E Journal",
      year: 2021,
      volume: null,
      pages: null,
      url: null,
    },
  ];
}

test("publication catalogue lists stored records and opens a PMID page", async ({ page }) => {
  const records = fixturePublications();

  await page.route(/\/api\/v1\/publications(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: records,
        total: records.length,
        nextCursor: null,
      }),
    });
  });
  await page.route(/\/api\/v1\/publications\/900000001(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ...records[0],
        sequenceAccessions: ["BW_E2E_NM_001"],
      }),
    });
  });

  await page.goto("/publications");
  await waitForSplash(page);

  await expect(page.getByRole("heading", { name: "Publication catalogue" })).toBeVisible();
  await expect(page.getByText("E2E fixture publication one")).toBeVisible();
  await expect(page.getByText("PMID 900000001")).toBeVisible();

  await page.getByRole("link", { name: /E2E fixture publication one/ }).click();
  await expect(page).toHaveURL(/\/publications\/900000001/);
  await expect(page.getByText("E2E fixture publication one")).toBeVisible();
  await expect(page.getByText("BW_E2E_NM_001")).toBeVisible();
});

test("publication catalogue paginates with nextCursor from the API", async ({ page }) => {
  const first = fixturePublications()[0];
  const second = fixturePublications()[1];

  await page.route(/\/api\/v1\/publications(\?|$)/, async (route) => {
    const url = new URL(route.request().url());
    const cursor = url.searchParams.get("cursor");
    if (cursor === "page-2") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          results: [second],
          total: 2,
          nextCursor: null,
        }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [first],
        total: 2,
        nextCursor: "page-2",
      }),
    });
  });

  await page.goto("/publications");
  await waitForSplash(page);

  await expect(page.getByText("E2E fixture publication one")).toBeVisible();
  await expect(page.getByText("E2E fixture publication two")).toHaveCount(0);
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByText("E2E fixture publication two")).toBeVisible();
  await expect(page.getByText("Page 2")).toBeVisible();
});

test("publication catalogue shows an empty state when the API has no matches", async ({
  page,
}) => {
  await page.route(/\/api\/v1\/publications(\?|$)/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ results: [], total: 0, nextCursor: null }),
    });
  });

  await page.goto("/publications");
  await waitForSplash(page);

  await expect(
    page.getByText("The database is connected but no publication records have been imported yet."),
  ).toBeVisible();
});

test("publication catalogue shows an error state when the list request fails", async ({
  page,
}) => {
  await page.route(/\/api\/v1\/publications(\?|$)/, async (route) => {
    await route.fulfill({ status: 500, contentType: "application/json", body: "{}" });
  });

  await page.goto("/publications");
  await waitForSplash(page);

  await expect(page.getByText("Publications could not be loaded. Please try again.")).toBeVisible();
});
