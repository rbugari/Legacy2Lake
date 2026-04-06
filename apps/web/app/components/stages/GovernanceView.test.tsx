import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import GovernanceView from "./GovernanceView";
import { fetchWithAuth } from "../../lib/auth-client";

vi.mock("../StageHeader", () => ({
  default: () => <div data-testid="stage-header">StageHeader</div>,
}));

vi.mock("../visualization/QualityDashboard", () => ({
  default: () => <div data-testid="quality-dashboard">QualityDashboard</div>,
}));

vi.mock("../UnifiedLogViewer", () => ({
  default: () => <div data-testid="log-viewer">UnifiedLogViewer</div>,
}));

vi.mock("../GapWorkspace", () => ({
  default: () => <div data-testid="gap-workspace">GapWorkspace</div>,
}));

vi.mock("@/app/hooks/useConfirm", () => ({
  useConfirm: () => ({
    confirm: vi.fn(async () => true),
    ConfirmDialog: <div data-testid="confirm-dialog" />,
  }),
}));

vi.mock("../ExecutiveSummaryPanel", () => ({
  default: (props: { projectId: string; variant?: string }) => (
    <div
      data-testid="executive-summary-panel"
      data-project-id={props.projectId}
      data-variant={props.variant ?? "full"}
    >
      ExecutiveSummaryPanelMock
    </div>
  ),
}));

vi.mock("../../lib/auth-client", () => ({
  fetchWithAuth: vi.fn(),
}));

const mockedFetchWithAuth = vi.mocked(fetchWithAuth);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("GovernanceView", () => {
  it("renders ExecutiveSummaryPanel in overview/report flow with full variant", async () => {
    const projectId = "project-gov-1";

    mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
      if (endpoint === `discovery/status/${projectId}`) {
        return { ok: true, json: async () => ({ status: "CERTIFIED" }) } as Response;
      }
      if (endpoint === `projects/${projectId}`) {
        return { ok: true, json: async () => ({ id: projectId, origin: "SQL", destination: "Fabric" }) } as Response;
      }
      if (endpoint === `projects/${projectId}/governance`) {
        return {
          ok: true,
          json: async () => ({
            score: 91,
            stats: { bronze_count: 1, silver_count: 1, gold_count: 1, total_files: 3, total_lines: 120 },
          }),
        } as Response;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    render(
      <GovernanceView
        projectId={projectId}
        onStageChange={vi.fn()}
        activeSection="overview"
        onSectionChange={vi.fn()}
      />
    );

    const panel = await screen.findByTestId("executive-summary-panel");
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveAttribute("data-project-id", projectId);
    expect(panel).toHaveAttribute("data-variant", "full");

    await waitFor(() => {
      expect(mockedFetchWithAuth).toHaveBeenCalledWith(`projects/${projectId}/governance`, { headers: {} });
    });
  });
});
