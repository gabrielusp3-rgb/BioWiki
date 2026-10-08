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

test("language menu lists eleven locales and Arabic switches direction", async ({ page }) => {
  await page.goto("/");
  await waitForSplash(page);
  const selector = page.getByTestId("language-selector").first();
  await expect(selector).toBeVisible();
  const menu = page.getByTestId("language-menu").first();
  await expect(async () => {
    await selector.click();
    await expect(menu.getByRole("option")).toHaveCount(11);
  }).toPass();
  await expect(menu.getByTestId("locale-en-GB")).toBeVisible();
  await expect(menu.getByTestId("locale-pt-BR")).toBeVisible();
  await expect(menu.getByTestId("locale-hi-IN")).toBeVisible();
  await menu.getByTestId("locale-ar-SA").click();
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar-SA");
  await expect(selector).toHaveAttribute("aria-label", /العربية/);
});
