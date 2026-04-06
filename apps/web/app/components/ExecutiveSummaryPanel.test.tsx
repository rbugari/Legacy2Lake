import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import ExecutiveSummaryPanel from "./ExecutiveSummaryPanel";
import { fetchWithAuth } from "@/app/lib/auth-client";

vi.mock("@/app/lib/auth-client", () => ({
  fetchWithAuth: vi.fn(),
}));

const mockedFetchWithAuth = vi.mocked(fetchWithAuth);

const summaryWithReadiness = {
  migration_posture: "Moderate - Proceed with monitoring",
  confidence_score: 72,
  source_tech: "SQLSERVER",
  target_tech: "SNOWFLAKE",
  detected_techs: ["SQLSERVER"],
  total_assets: 5,
  migrable_assets: 4,
  pii_assets: 1,
  top_risks: ["Quick assessment is YELLOW - proceed with guarded review"],
  manual_effort_areas: ["Compliance / PII handling (1 item(s))"],
  open_blockers: [],
  readiness_warnings: ["Quick assessment is YELLOW - proceed with guarded review"],
  readiness_next_steps: ["Address the top warnings and recompute readiness."],
  recommended_next_action: "Address the top warnings and recompute readiness.",
  readiness_status: "BASELINE_READY",
  total_gaps: 0,
  decision_queue: [],
  decision_focus: "No pending decision queue detected.",
  decision_open_count: 0,
  computed_at: "2026-04-05T00:00:00Z",
};

const summaryWithoutReadiness = {
  ...summaryWithReadiness,
  readiness_warnings: [],
  readiness_next_steps: [],
};

const emptyGaps = {
  total: 0,
  by_severity: { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 },
  by_category: {},
  grouped: {},
  computed_at: "2026-04-05T00:00:00Z",
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("ExecutiveSummaryPanel", () => {
  it("renders readiness warnings and checklist in full mode", async () => {
    mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
      if (endpoint.includes("executive-summary")) {
        return {
          ok: true,
          json: async () => summaryWithReadiness,
        } as Response;
      }

      return {
        ok: true,
        json: async () => emptyGaps,
      } as Response;
    });

    render(<ExecutiveSummaryPanel projectId="project-1" variant="full" />);

    expect(await screen.findByText("Executive Summary")).toBeInTheDocument();
    expect(await screen.findByText("Readiness Warnings")).toBeInTheDocument();
    expect(await screen.findByText("Execution Checklist")).toBeInTheDocument();
    expect(await screen.findAllByText("Address the top warnings and recompute readiness.")).toHaveLength(2);

    await waitFor(() => {
      expect(mockedFetchWithAuth).toHaveBeenCalledWith("projects/project-1/executive-summary");
      expect(mockedFetchWithAuth).toHaveBeenCalledWith("projects/project-1/gaps-summary");
    });
  });

  it("does not render readiness sections when arrays are empty", async () => {
    mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
      if (endpoint.includes("executive-summary")) {
        return {
          ok: true,
          json: async () => summaryWithoutReadiness,
        } as Response;
      }

      return {
        ok: true,
        json: async () => emptyGaps,
      } as Response;
    });

    render(<ExecutiveSummaryPanel projectId="project-2" variant="full" />);

    expect(await screen.findByText("Executive Summary")).toBeInTheDocument();
    expect(screen.queryByText("Readiness Warnings")).not.toBeInTheDocument();
    expect(screen.queryByText("Execution Checklist")).not.toBeInTheDocument();
  });

  it("renders compact variant with posture, confidence and next action", async () => {
    mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
      if (endpoint.includes("executive-summary")) {
        return {
          ok: true,
          json: async () => summaryWithReadiness,
        } as Response;
      }

      return {
        ok: true,
        json: async () => emptyGaps,
      } as Response;
    });

    render(<ExecutiveSummaryPanel projectId="project-3" variant="compact" />);

    expect(await screen.findByText("Moderate - Proceed with monitoring")).toBeInTheDocument();
    expect(await screen.findByText("72% confidence")).toBeInTheDocument();
    expect(await screen.findByText("Address the top warnings and recompute readiness.")).toBeInTheDocument();
    // compact mode must NOT render section headers
    expect(screen.queryByText("Readiness Warnings")).not.toBeInTheDocument();
    expect(screen.queryByText("Execution Checklist")).not.toBeInTheDocument();
  });

  it("shows open blockers alongside warnings when both are present", async () => {
    const summaryWithBlockersAndWarnings = {
      ...summaryWithReadiness,
      open_blockers: ["Source system access denied"],
      top_risks: ["Source system access denied", "Quick assessment is YELLOW - proceed with guarded review"],
      readiness_warnings: ["Quick assessment is YELLOW - proceed with guarded review"],
      readiness_next_steps: ["Resolve RED quick-assessment blockers before advancing stages."],
      recommended_next_action: "Resolve RED quick-assessment blockers before advancing stages.",
      readiness_status: "REQUIRES_CONTEXT",
    };

    mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
      if (endpoint.includes("executive-summary")) {
        return {
          ok: true,
          json: async () => summaryWithBlockersAndWarnings,
        } as Response;
      }

      return {
        ok: true,
        json: async () => emptyGaps,
      } as Response;
    });

    render(<ExecutiveSummaryPanel projectId="project-4" variant="full" />);

    expect(await screen.findByText("Open Blockers")).toBeInTheDocument();
    // The blocker appears in both Top Risks and Open Blockers sections
    expect(await screen.findAllByText("Source system access denied")).toHaveLength(2);
    expect(await screen.findByText("Readiness Warnings")).toBeInTheDocument();
    expect(await screen.findByText("Execution Checklist")).toBeInTheDocument();
  });
});
