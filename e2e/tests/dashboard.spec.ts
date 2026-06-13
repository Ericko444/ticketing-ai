import { test, expect } from "@playwright/test";
import { injectRoutedTicket, injectSupervisorTicket } from "../helpers/api";
import { fixtures } from "../helpers/fixtures";

test.describe("Dashboard", () => {
  test("renders header, nav links, and live indicator", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("link", { name: "TicketAI" }).or(page.locator("header span").filter({ hasText: "TicketAI" }))).toBeVisible();
    await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Supervisor Queue" })).toBeVisible();
    await expect(page.getByText("Live")).toBeVisible();
  });

  test("shows empty state when no tickets exist", async ({ page }) => {
    // Navigate directly — if there happen to be tickets this test is informational only
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const list = page.locator("ul li");
    const empty = page.getByText("No tickets yet");
    // Either tickets exist (from previous runs) or the empty state is shown
    const hasTickets = await list.count() > 0;
    if (!hasTickets) {
      await expect(empty).toBeVisible();
    }
  });

  test("IT ticket appears in the list after injection", async ({ page }) => {
    const fixture = fixtures.it();
    const { ticket_id } = await injectRoutedTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto("/");
    await expect(
      page.locator("li").filter({ hasText: fixture.subject })
    ).toBeVisible();

    // IT badge with blue dot should be present
    await expect(
      page.locator("li").filter({ hasText: fixture.subject }).getByText("IT")
    ).toBeVisible();

    // "Routed" status pill
    await expect(
      page.locator("li").filter({ hasText: fixture.subject }).getByText("Routed")
    ).toBeVisible();

    // Confidence bar should exist (confidence was 0.97 → "97% confidence")
    await expect(
      page.locator("li").filter({ hasText: fixture.subject }).getByText(/confidence/i)
    ).toBeVisible();

    // Cleanup hint for logs
    console.log(`IT ticket ${ticket_id}: ${fixture.subject}`);
  });

  test("Support ticket appears with correct badge", async ({ page }) => {
    const fixture = fixtures.support();
    await injectRoutedTicket({ ...fixture, assigned_team: fixture.team });

    await page.goto("/");
    await expect(
      page.locator("li").filter({ hasText: fixture.subject }).getByText("Support")
    ).toBeVisible();
  });

  test("HR ticket appears with correct badge", async ({ page }) => {
    const fixture = fixtures.hr();
    await injectRoutedTicket({ ...fixture, assigned_team: fixture.team });

    await page.goto("/");
    await expect(
      page.locator("li").filter({ hasText: fixture.subject }).getByText("HR")
    ).toBeVisible();
  });

  test("Helpdesk ticket appears with correct badge", async ({ page }) => {
    const fixture = fixtures.helpdesk();
    await injectRoutedTicket({ ...fixture, assigned_team: fixture.team });

    await page.goto("/");
    await expect(
      page.locator("li").filter({ hasText: fixture.subject }).getByText("Helpdesk")
    ).toBeVisible();
  });

  test("pending supervisor ticket shows amber warning banner", async ({ page }) => {
    const fixture = fixtures.ambiguous();
    await injectSupervisorTicket({ ...fixture, assigned_team: fixture.team });

    await page.goto("/");
    await expect(
      page.getByText(/pending supervisor review/i)
    ).toBeVisible();

    // Banner should link to supervisor page
    const banner = page.locator("a", { has: page.getByText(/pending supervisor review/i) });
    await expect(banner).toHaveAttribute("href", "/supervisor");
  });

  test("clicking a ticket navigates to the detail page", async ({ page }) => {
    const fixture = fixtures.it();
    const { ticket_id } = await injectRoutedTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto("/");
    await page.locator("li").filter({ hasText: fixture.subject }).click();
    await expect(page).toHaveURL(`/tickets/${ticket_id}`);
    await expect(page.getByRole("heading", { name: fixture.subject })).toBeVisible();
  });

  test("nav link to Supervisor Queue navigates correctly", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Supervisor Queue" }).click();
    await expect(page).toHaveURL("/supervisor");
    await expect(page.getByRole("heading", { name: "Supervisor Queue" })).toBeVisible();
  });
});
