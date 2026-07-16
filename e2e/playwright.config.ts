import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  globalSetup: "./globalSetup.ts",
  testDir: "./tests",
  // Tests share backend state — run sequentially to avoid collisions
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
