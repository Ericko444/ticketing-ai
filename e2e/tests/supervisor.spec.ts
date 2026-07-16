import { test, expect } from "@playwright/test";
import { injectSupervisorTicket, getTicket } from "../helpers/api";
import { fixtures } from "../helpers/fixtures";

test.describe("Supervisor queue", () => {
  test("shows empty state when no tickets are pending", async ({ page }) => {
    await page.goto("/supervisor");
    await page.waitForLoadState("domcontentloaded");

    // Wait for the async fetch to settle — either cards or empty state will appear
    await expect(
      page.locator('[data-testid="supervisor-card"]').first().or(page.getByText(/all clear/i))
    ).toBeVisible({ timeout: 10_000 });

    const isEmpty = (await page.locator('[data-testid="supervisor-card"]').count()) === 0;
    if (isEmpty) {
      await expect(page.getByText(/all clear/i)).toBeVisible();
      await expect(page.getByText(/no tickets pending review/i)).toBeVisible();
    }
  });

  test("pending ticket appears in the supervisor queue with expected fields", async ({ page }) => {
    const fixture = fixtures.ambiguous();
    const { ticket_id } = await injectSupervisorTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto("/supervisor");

    const card = page.locator(`[data-ticket-id="${ticket_id}"]`);
    await expect(card).toBeVisible();

    // "Needs review" badge
    await expect(card.getByText("Needs review")).toBeVisible();

    // Proposed team badge
    await expect(card.getByText(fixture.team)).toBeVisible();

    // Confidence: 35%
    await expect(card.getByText("35%")).toBeVisible();

    // Evaluator verdict: uncertain
    await expect(card.getByText("uncertain")).toBeVisible();

    // Action buttons
    await expect(card.getByRole("button", { name: "Approve" })).toBeVisible();
    await expect(card.getByRole("button", { name: "Override team" })).toBeVisible();

    console.log(`Supervisor ticket ${ticket_id}: ${fixture.subject}`);
  });

  test("supervisor approves routing — ticket leaves the queue and becomes routed", async ({
    page,
  }) => {
    const fixture = fixtures.it();
    const { ticket_id } = await injectSupervisorTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto("/supervisor");

    const card = page.locator(`[data-ticket-id="${ticket_id}"]`);
    await expect(card).toBeVisible();

    await card.getByRole("button", { name: "Approve" }).click();

    // Optimistic UI — this specific card should disappear immediately
    await expect(card).not.toBeVisible({ timeout: 5_000 });

    // Poll until the graph finishes updating the DB
    await expect.poll(() => getTicket(ticket_id).then((t) => t.status), { timeout: 15_000 }).toBe("routed");

    const updated = await getTicket(ticket_id);
    expect(updated.supervisor_action).toBe("approved");
    expect(updated.final_team).toBe(fixture.team);

    console.log(`Approved ticket ${ticket_id} → ${updated.final_team}`);
  });

  test("supervisor overrides team — ticket is routed to the chosen team", async ({
    page,
  }) => {
    const fixture = fixtures.ambiguous();
    // Inject as IT, but supervisor will override to HR
    const { ticket_id } = await injectSupervisorTicket({
      ...fixture,
      assigned_team: "IT",
    });

    await page.goto("/supervisor");

    const card = page.locator(`[data-ticket-id="${ticket_id}"]`);
    await expect(card).toBeVisible();

    await card.getByRole("button", { name: "Override team" }).click();

    // Override modal should open
    const modal = page.getByRole("heading", { name: "Override Team Assignment" });
    await expect(modal).toBeVisible();

    // Select HR
    await page.getByRole("button", { name: "HR" }).click();

    // Confirm
    await page.getByRole("button", { name: "Confirm override" }).click();

    // Modal should close and this specific card should disappear
    await expect(modal).not.toBeVisible({ timeout: 5_000 });
    await expect(card).not.toBeVisible({ timeout: 5_000 });

    // Poll until the graph finishes updating the DB
    await expect.poll(() => getTicket(ticket_id).then((t) => t.status), { timeout: 15_000 }).toBe("routed");

    const updated = await getTicket(ticket_id);
    expect(updated.supervisor_action).toBe("overridden");
    expect(updated.final_team).toBe("HR");

    console.log(`Overridden ticket ${ticket_id}: IT → ${updated.final_team}`);
  });

  test("override modal — all four team buttons are selectable", async ({ page }) => {
    const fixture = fixtures.ambiguous();
    const { ticket_id } = await injectSupervisorTicket({ ...fixture, assigned_team: "IT" });

    await page.goto("/supervisor");

    const card = page.locator(`[data-ticket-id="${ticket_id}"]`);
    await card.getByRole("button", { name: "Override team" }).click();

    const modal = page.getByRole("heading", { name: "Override Team Assignment" });
    await expect(modal).toBeVisible();

    for (const team of ["IT", "Support", "Helpdesk", "HR"]) {
      const btn = page.getByRole("button", { name: team });
      await expect(btn).toBeVisible();
      await btn.click();
      await expect(btn).toBeVisible();
    }

    // Cancel closes the modal without acting
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(modal).not.toBeVisible();
  });

  test("override modal closes on backdrop click", async ({ page }) => {
    const fixture = fixtures.ambiguous();
    const { ticket_id } = await injectSupervisorTicket({ ...fixture, assigned_team: "IT" });

    await page.goto("/supervisor");

    const card = page.locator(`[data-ticket-id="${ticket_id}"]`);
    await card.getByRole("button", { name: "Override team" }).click();

    await expect(
      page.getByRole("heading", { name: "Override Team Assignment" })
    ).toBeVisible();

    // Click the backdrop (fixed overlay — click top-left corner outside modal)
    await page.mouse.click(10, 10);

    await expect(
      page.getByRole("heading", { name: "Override Team Assignment" })
    ).not.toBeVisible();
  });

  test("'View details' link navigates to the ticket detail page", async ({ page }) => {
    const fixture = fixtures.helpdesk();
    const { ticket_id } = await injectSupervisorTicket({
      ...fixture,
      assigned_team: fixture.team,
    });

    await page.goto("/supervisor");

    const card = page.locator(`[data-ticket-id="${ticket_id}"]`);
    await card.getByRole("link", { name: /view details/i }).click();

    await expect(page).toHaveURL(`/tickets/${ticket_id}`);
    await expect(page.getByRole("heading", { name: fixture.subject })).toBeVisible();
  });

  test("multiple pending tickets all appear in the queue", async ({ page }) => {
    const ticketData = [fixtures.ambiguous(), fixtures.ambiguous(), fixtures.ambiguous()];

    for (const fixture of ticketData) {
      await injectSupervisorTicket({ ...fixture, assigned_team: fixture.team });
    }

    await page.goto("/supervisor");

    // At least the 3 we just injected should be present
    const cards = page.locator('[data-testid="supervisor-card"]');
    await expect(cards.first()).toBeVisible();
    expect(await cards.count()).toBeGreaterThanOrEqual(3);
  });
});
