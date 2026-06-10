import { render, screen, waitFor } from "@testing-library/react";
import TicketDetail from "@/components/TicketDetail";
import type { Ticket } from "@/lib/api";

const mockTicket: Ticket = {
  id: "t1",
  email_id: "e1",
  subject: "VPN access request",
  body: "I need VPN access for remote work.",
  sender: "bob@example.com",
  assigned_team: "IT",
  routing_confidence: 0.88,
  evaluator_verdict: "correct",
  supervisor_action: "",
  final_team: "IT",
  status: "routed",
  created_at: "2026-06-10T12:00:00Z",
};

jest.mock("@/lib/api", () => ({
  getTicket: jest.fn(),
}));

// eslint-disable-next-line @typescript-eslint/no-require-imports
const { getTicket } = require("@/lib/api");

describe("tickets/ — TicketDetail", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders ticket details after loading", async () => {
    getTicket.mockResolvedValue(mockTicket);
    render(<TicketDetail id="t1" />);

    await waitFor(() =>
      expect(screen.getByText("VPN access request")).toBeInTheDocument()
    );
    expect(screen.getByText("bob@example.com")).toBeInTheDocument();
    expect(
      screen.getByText("I need VPN access for remote work.")
    ).toBeInTheDocument();
    expect(screen.getByText("88%")).toBeInTheDocument();
  });

  it("shows not found message when fetch fails", async () => {
    getTicket.mockRejectedValue(new Error("Ticket not found"));
    render(<TicketDetail id="bad-id" />);

    await waitFor(() =>
      expect(screen.getByText("Ticket not found.")).toBeInTheDocument()
    );
  });

  it("shows back link to dashboard", async () => {
    getTicket.mockResolvedValue(mockTicket);
    render(<TicketDetail id="t1" />);

    await waitFor(() =>
      expect(screen.getByText(/Back to dashboard/)).toBeInTheDocument()
    );
  });
});
