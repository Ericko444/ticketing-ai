import { render, screen } from "@testing-library/react";
import TicketCard from "@/components/TicketCard";
import type { Ticket } from "@/lib/api";

const base: Ticket = {
  id: "t1",
  email_id: "e1",
  subject: "Printer is broken",
  body: "The office printer stopped working.",
  sender: "alice@example.com",
  assigned_team: "IT",
  routing_confidence: 0.92,
  evaluator_verdict: "correct",
  supervisor_action: "",
  final_team: "IT",
  status: "routed",
  created_at: "2026-06-10T10:00:00Z",
};

describe("TicketCard", () => {
  it("renders subject and sender", () => {
    render(<TicketCard ticket={base} />);
    expect(screen.getByText("Printer is broken")).toBeInTheDocument();
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
  });

  it("renders team badge with final_team", () => {
    render(<TicketCard ticket={base} />);
    expect(screen.getByText("IT")).toBeInTheDocument();
  });

  it("falls back to assigned_team when final_team is empty", () => {
    render(<TicketCard ticket={{ ...base, final_team: "" }} />);
    expect(screen.getByText("IT")).toBeInTheDocument();
  });

  it("shows pending review warning for pending_supervisor status", () => {
    render(<TicketCard ticket={{ ...base, status: "pending_supervisor" }} />);
    expect(screen.getByText(/Pending review/)).toBeInTheDocument();
  });

  it("does not show pending review warning for routed status", () => {
    render(<TicketCard ticket={base} />);
    expect(screen.queryByText(/Pending review/)).not.toBeInTheDocument();
  });

  it("renders a formatted timestamp", () => {
    render(<TicketCard ticket={base} />);
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });
});
