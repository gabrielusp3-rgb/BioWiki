import { defineConfig, devices } from "@playwright/test";

const skipWebServer = Boolean(process.env.PLAYWRIGHT_SKIP_WEBSERVER);
/** Dedicated local port so e2e never attaches to another app occupying 3000. */
const localPort = process.env.PLAYWRIGHT_PORT ?? "3100";
const localOrigin = `http://127.0.0.1:${localPort}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? localOrigin,
    trace: "on-first-retry",
  },
  webServer: skipWebServer
    ? undefined
    : {
        command: `npx next dev --hostname 127.0.0.1 -p ${localPort}`,
        url: localOrigin,
        reuseExistingServer: process.env.PLAYWRIGHT_REUSE_SERVER === "1",
        timeout: 120_000,
      },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
