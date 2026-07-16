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
    await page.goto("/");

    // Wait for the async fetch to settle — either tickets or empty state will appear
    await expect(
      page.locator("ul li").first().or(page.getByText("No tickets yet"))
    ).toBeVisible({ timeout: 10_000 });

    const hasTickets = (await page.locator("ul li").count()) > 0;
    if (!hasTickets) {
      await expect(page.getByText("No tickets yet")).toBeVisible();
    }
  });

  test("IT ticket appears in the list after injection", async ({ page }) => {
    const fixture = fixtures.it();
    const { ticket_id } = await injectRoutedTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto("/");
    const card = page.locator(`[data-testid="${ticket_id}"]`);

    await expect(card).toBeVisible();
    await expect(card.getByText("IT")).toBeVisible();
    await expect(card.getByText("Routed")).toBeVisible();
    await expect(card.getByText(/confidence/i)).toBeVisible();

    console.log(`IT ticket ${ticket_id}: ${fixture.subject}`);
  });

  test("Support ticket appears with correct badge", async ({ page }) => {
    const fixture = fixtures.support();
    const { ticket_id } = await injectRoutedTicket({ ...fixture, assigned_team: fixture.team });

    await page.goto("/");
    await expect(page.locator(`[data-testid="${ticket_id}"]`).getByText("Support")).toBeVisible();
  });

  test("HR ticket appears with correct badge", async ({ page }) => {
    const fixture = fixtures.hr();
    const { ticket_id } = await injectRoutedTicket({ ...fixture, assigned_team: fixture.team });

    await page.goto("/");
    await expect(page.locator(`[data-testid="${ticket_id}"]`).getByText("HR")).toBeVisible();
  });

  test("Helpdesk ticket appears with correct badge", async ({ page }) => {
    const fixture = fixtures.helpdesk();
    const { ticket_id } = await injectRoutedTicket({ ...fixture, assigned_team: fixture.team });

    await page.goto("/");
    await expect(page.locator(`[data-testid="${ticket_id}"]`).getByText("Helpdesk")).toBeVisible();
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
    await page.locator(`[data-testid="${ticket_id}"]`).click();
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
