import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ConfidenceBreakdownPanel, { type ConfidenceBreakdown } from "./ConfidenceBreakdownPanel";

const makeBreakdown = (
  overrides: Partial<ConfidenceBreakdown> = {}
): ConfidenceBreakdown => ({
  baseline_score: 50,
  adjustments: [],
  final_score: 50,
  ...overrides,
});

describe("ConfidenceBreakdownPanel", () => {
  it("renders baseline and final scores", () => {
    render(<ConfidenceBreakdownPanel breakdown={makeBreakdown({ baseline_score: 60, final_score: 75 })} />);

    // Baseline appears in summary row and header description
    const fifties = screen.getAllByText(/60%/);
    expect(fifties.length).toBeGreaterThanOrEqual(1);

    // Final score appears in big number and footer
    const finals = screen.getAllByText(/75%/);
    expect(finals.length).toBeGreaterThanOrEqual(1);
  });

  it("shows +net delta when final > baseline", () => {
    render(<ConfidenceBreakdownPanel breakdown={makeBreakdown({ baseline_score: 50, final_score: 75 })} />);
    expect(screen.getByText("+25 net")).toBeInTheDocument();
  });

  it("shows negative net delta when final < baseline", () => {
    render(<ConfidenceBreakdownPanel breakdown={makeBreakdown({ baseline_score: 70, final_score: 55 })} />);
    expect(screen.getByText("-15 net")).toBeInTheDocument();
  });

  it("shows zero net correctly", () => {
    render(<ConfidenceBreakdownPanel breakdown={makeBreakdown({ baseline_score: 60, final_score: 60 })} />);
    expect(screen.getByText("+0 net")).toBeInTheDocument();
  });

  it("shows 'No signal adjustments' when adjustments list is empty", () => {
    render(<ConfidenceBreakdownPanel breakdown={makeBreakdown()} />);
    const msgs = screen.getAllByText("No signal adjustments were applied.");
    expect(msgs.length).toBeGreaterThanOrEqual(1);
  });

  it("renders adjustment label, reason and +delta for positive adjustment", () => {
    const breakdown = makeBreakdown({
      baseline_score: 50,
      final_score: 70,
      adjustments: [{ label: "Triage complete", delta: 20, reason: "Full triage run detected" }],
    });
    render(<ConfidenceBreakdownPanel breakdown={breakdown} />);

    expect(screen.getByText("Triage complete")).toBeInTheDocument();
    expect(screen.getByText("Full triage run detected")).toBeInTheDocument();
    expect(screen.getByText("+20")).toBeInTheDocument();
  });

  it("renders negative delta for penalty adjustment", () => {
    const breakdown = makeBreakdown({
      baseline_score: 70,
      final_score: 55,
      adjustments: [{ label: "Missing source tech", delta: -15, reason: "source_tech not set" }],
    });
    render(<ConfidenceBreakdownPanel breakdown={breakdown} />);

    expect(screen.getByText("Missing source tech")).toBeInTheDocument();
    expect(screen.getByText("-15")).toBeInTheDocument();
  });

  it("renders neutral delta (zero) correctly", () => {
    const breakdown = makeBreakdown({
      adjustments: [{ label: "Context neutral", delta: 0, reason: "No impact signals found" }],
    });
    render(<ConfidenceBreakdownPanel breakdown={breakdown} />);

    expect(screen.getByText("Context neutral")).toBeInTheDocument();
    expect(screen.getByText("+0")).toBeInTheDocument();
  });

  it("renders multiple adjustments independently", () => {
    const breakdown = makeBreakdown({
      baseline_score: 50,
      final_score: 72,
      adjustments: [
        { label: "Quick assessment", delta: 15, reason: "QA score high" },
        { label: "PII detected", delta: -8, reason: "Sensitive columns found" },
        { label: "Source tech set", delta: 15, reason: "SQLSERVER detected" },
      ],
    });
    render(<ConfidenceBreakdownPanel breakdown={breakdown} />);

    expect(screen.getByText("Quick assessment")).toBeInTheDocument();
    expect(screen.getByText("PII detected")).toBeInTheDocument();
    expect(screen.getByText("Source tech set")).toBeInTheDocument();
    expect(screen.getAllByText("+15")).toHaveLength(2);
    expect(screen.getByText("-8")).toBeInTheDocument();
  });
});
