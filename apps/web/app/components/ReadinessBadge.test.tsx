import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import ReadinessBadge from "./ReadinessBadge";
import { fetchWithAuth } from "@/app/lib/auth-client";

vi.mock("@/app/lib/auth-client", () => ({
  fetchWithAuth: vi.fn(),
}));

const mockedFetchWithAuth = vi.mocked(fetchWithAuth);

const readinessReady = {
  status: "READY",
  confidence_score: 84,
  top_reasons: ["Viability assessment is GREEN (84% score)"],
  blockers: [],
  warnings: [],
  next_steps: ["Proceed to Drafting and monitor governance findings during refinement."],
  recommended_next_action: "Project is ready for automated migration. Proceed to Drafting or Refinement.",
  source_signals: {
    quick_assessment_present: true,
    triage_complete: true,
    source_tech_set: true,
    target_tech_set: true,
    project_stage: 2,
  },
  computed_at: "2026-04-05T00:00:00Z",
};

const readinessWithWarnings = {
  status: "BASELINE_READY",
  confidence_score: 65,
  top_reasons: ["Viability assessment is YELLOW (65% score) — review warnings"],
  blockers: [],
  warnings: [
    "Quick assessment is YELLOW — proceed with guarded review",
    "Using default migration prompt — add project-specific prompt for better precision",
  ],
  next_steps: [
    "Address the top warnings and recompute readiness.",
    "Create project-specific prompt.",
  ],
  recommended_next_action: "Project is baseline ready. Proceed to Drafting for code generation.",
  source_signals: {
    quick_assessment_present: true,
    triage_complete: true,
    source_tech_set: true,
    target_tech_set: true,
    project_stage: 1,
  },
  computed_at: "2026-04-05T00:00:00Z",
};

const readinessWithBlockers = {
  status: "REQUIRES_CONTEXT",
  confidence_score: 30,
  top_reasons: ["Source technology not configured", "Viability assessment not yet run"],
  blockers: ["Source technology not configured", "Target technology not configured"],
  warnings: [],
  next_steps: [
    "Configure source technology in project settings.",
    "Configure target technology in project settings.",
  ],
  recommended_next_action: "Configure source and target technology in project settings before proceeding.",
  source_signals: {
    quick_assessment_present: false,
    triage_complete: false,
    source_tech_set: false,
    target_tech_set: false,
    project_stage: 0,
  },
  computed_at: "2026-04-05T00:00:00Z",
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("ReadinessBadge", () => {
  describe("badge variant", () => {
    it("renders status label and confidence score", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessReady,
      } as Response);

      render(<ReadinessBadge projectId="proj-1" variant="badge" />);

      expect(await screen.findByText("Ready")).toBeInTheDocument();
      expect(await screen.findByText("84%")).toBeInTheDocument();
    });

    it("renders BASELINE_READY status label", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessWithWarnings,
      } as Response);

      render(<ReadinessBadge projectId="proj-2" variant="badge" />);

      expect(await screen.findByText("Baseline Ready")).toBeInTheDocument();
      expect(await screen.findByText("65%")).toBeInTheDocument();
    });
  });

  describe("card variant", () => {
    it("renders warnings when present", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessWithWarnings,
      } as Response);

      render(<ReadinessBadge projectId="proj-3" variant="card" />);

      expect(await screen.findByText("Quick assessment is YELLOW — proceed with guarded review")).toBeInTheDocument();
      expect(await screen.findByText("Using default migration prompt — add project-specific prompt for better precision")).toBeInTheDocument();
    });

    it("renders next steps when present", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessWithWarnings,
      } as Response);

      render(<ReadinessBadge projectId="proj-4" variant="card" />);

      expect(await screen.findByText("Next steps")).toBeInTheDocument();
      expect(await screen.findByText("Address the top warnings and recompute readiness.")).toBeInTheDocument();
      expect(await screen.findByText("Create project-specific prompt.")).toBeInTheDocument();
    });

    it("renders blockers when present", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessWithBlockers,
      } as Response);

      render(<ReadinessBadge projectId="proj-5" variant="card" />);

      expect(await screen.findByText("Source technology not configured")).toBeInTheDocument();
      expect(await screen.findByText("Target technology not configured")).toBeInTheDocument();
    });

    it("does not render warnings section when warnings array is empty", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessReady,
      } as Response);

      render(<ReadinessBadge projectId="proj-6" variant="card" />);

      expect(await screen.findByText("Ready")).toBeInTheDocument();
      // No warnings heading — warnings list uses inline icons, not a section title
      // Verify warnings icons are absent by checking amber text is not present
      expect(screen.queryByText("Quick assessment is YELLOW — proceed with guarded review")).not.toBeInTheDocument();
    });

    it("renders recommended next action", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessReady,
      } as Response);

      render(<ReadinessBadge projectId="proj-7" variant="card" />);

      expect(
        await screen.findByText("Project is ready for automated migration. Proceed to Drafting or Refinement.")
      ).toBeInTheDocument();
    });

    it("toggles signal reasons on expandable button click", async () => {
      mockedFetchWithAuth.mockResolvedValueOnce({
        ok: true,
        json: async () => readinessReady,
      } as Response);

      render(<ReadinessBadge projectId="proj-8" variant="card" />);

      const toggle = await screen.findByText("Show 1 signal(s)");
      expect(screen.queryByText("Viability assessment is GREEN (84% score)")).not.toBeInTheDocument();

      fireEvent.click(toggle);
      expect(screen.getByText("Viability assessment is GREEN (84% score)")).toBeInTheDocument();
      expect(screen.getByText("Hide reasons")).toBeInTheDocument();
    });
  });
});
