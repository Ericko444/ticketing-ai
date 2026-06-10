import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import SupervisorPage from "@/app/supervisor/page";
import type { Ticket } from "@/lib/api";

const pendingTicket: Ticket = {
  id: "t1",
  email_id: "e1",
  subject: "Payroll issue",
  body: "My paycheck was wrong.",
  sender: "carol@example.com",
  assigned_team: "HR",
  routing_confidence: 0.65,
  evaluator_verdict: "uncertain",
  supervisor_action: "",
  final_team: "",
  status: "pending_supervisor",
  created_at: "2026-06-10T09:00:00Z",
};

jest.mock("@/lib/api", () => ({
  getTickets: jest.fn(),
  approveRouting: jest.fn(),
  overrideRouting: jest.fn(),
}));

// eslint-disable-next-line @typescript-eslint/no-require-imports
const { getTickets, approveRouting, overrideRouting } = require("@/lib/api");

describe("SupervisorPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders pending tickets", async () => {
    getTickets.mockResolvedValue([pendingTicket]);
    render(<SupervisorPage />);

    await waitFor(() =>
      expect(screen.getByText("Payroll issue")).toBeInTheDocument()
    );
    expect(screen.getByText("65%")).toBeInTheDocument();
    expect(screen.getByText("uncertain")).toBeInTheDocument();
  });

  it("shows empty state when no pending tickets", async () => {
    getTickets.mockResolvedValue([]);
    render(<SupervisorPage />);

    await waitFor(() =>
      expect(screen.getByText("No tickets pending review.")).toBeInTheDocument()
    );
  });

  it("optimistically removes ticket on approve", async () => {
    approveRouting.mockResolvedValue(undefined);
    getTickets.mockResolvedValue([pendingTicket]);
    render(<SupervisorPage />);

    await waitFor(() =>
      expect(screen.getByText("Payroll issue")).toBeInTheDocument()
    );

    fireEvent.click(screen.getByText("Approve"));
    await waitFor(() =>
      expect(screen.queryByText("Payroll issue")).not.toBeInTheDocument()
    );
    expect(approveRouting).toHaveBeenCalledWith("t1");
  });

  it("opens override modal and calls overrideRouting", async () => {
    overrideRouting.mockResolvedValue(undefined);
    getTickets.mockResolvedValue([pendingTicket]);
    render(<SupervisorPage />);

    await waitFor(() =>
      expect(screen.getByText("Payroll issue")).toBeInTheDocument()
    );

    fireEvent.click(screen.getByText("Override"));
    expect(screen.getByText("Override Team Assignment")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Confirm"));
    await waitFor(() =>
      expect(screen.queryByText("Payroll issue")).not.toBeInTheDocument()
    );
    expect(overrideRouting).toHaveBeenCalledWith("t1", "IT");
  });

  it("closes modal on cancel", async () => {
    getTickets.mockResolvedValue([pendingTicket]);
    render(<SupervisorPage />);

    await waitFor(() =>
      expect(screen.getByText("Override")).toBeInTheDocument()
    );

    fireEvent.click(screen.getByText("Override"));
    expect(screen.getByText("Override Team Assignment")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Cancel"));
    expect(
      screen.queryByText("Override Team Assignment")
    ).not.toBeInTheDocument();
  });
});
