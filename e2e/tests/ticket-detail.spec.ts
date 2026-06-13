import { test, expect } from "@playwright/test";
import { injectRoutedTicket, injectSupervisorTicket } from "../helpers/api";
import { fixtures } from "../helpers/fixtures";

test.describe("Ticket detail page", () => {
  test("shows all core fields for a routed ticket", async ({ page }) => {
    const fixture = fixtures.support();
    const { ticket_id } = await injectRoutedTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto(`/tickets/${ticket_id}`);

    // Subject as heading
    await expect(page.getByRole("heading", { name: fixture.subject })).toBeVisible();

    // Sender
    await expect(page.getByText(fixture.sender)).toBeVisible();

    // Team badge
    await expect(page.getByText(fixture.team)).toBeVisible();

    // Status pill — "routed" (spaces in "routed")
    await expect(page.getByText("routed")).toBeVisible();

    // Email body
    await expect(page.getByText(fixture.body)).toBeVisible();
  });

  test("shows confidence percentage", async ({ page }) => {
    const fixture = fixtures.hr();
    const { ticket_id } = await injectRoutedTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto(`/tickets/${ticket_id}`);
    // confidence was injected as 0.97 → should display "97%"
    await expect(page.getByText("97%")).toBeVisible();
  });

  test("shows evaluator verdict", async ({ page }) => {
    const fixture = fixtures.helpdesk();
    const { ticket_id } = await injectRoutedTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto(`/tickets/${ticket_id}`);
    await expect(page.getByText("correct")).toBeVisible();
  });

  test("pending supervisor ticket shows pending_supervisor status", async ({ page }) => {
    const fixture = fixtures.ambiguous();
    const { ticket_id } = await injectSupervisorTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto(`/tickets/${ticket_id}`);
    await expect(page.getByText(/pending supervisor/i)).toBeVisible();

    // Confidence was injected as 0.35 → "35%"
    await expect(page.getByText("35%")).toBeVisible();

    // Verdict was "uncertain"
    await expect(page.getByText("uncertain")).toBeVisible();
  });

  test("back to dashboard link navigates home", async ({ page }) => {
    const fixture = fixtures.it();
    const { ticket_id } = await injectRoutedTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto(`/tickets/${ticket_id}`);
    await page.getByRole("link", { name: /back to dashboard/i }).click();
    await expect(page).toHaveURL("/");
  });

  test("404 — navigating to a non-existent ticket shows not found", async ({ page }) => {
    await page.goto("/tickets/00000000-0000-0000-0000-000000000000");
    await expect(page.getByText(/ticket not found/i)).toBeVisible();
  });

  test("renders one ticket per each team correctly", async ({ page }) => {
    const teams = fixtures.onePerTeam();

    for (const fixture of teams) {
      const { ticket_id } = await injectRoutedTicket({
        ...fixture,
        assigned_team: fixture.team,
      });

      await page.goto(`/tickets/${ticket_id}`);
      await expect(page.getByRole("heading", { name: fixture.subject })).toBeVisible();
      await expect(page.getByText(fixture.team)).toBeVisible();
      console.log(`  ✓ ${fixture.team}: ${fixture.subject}`);
    }
  });
});
