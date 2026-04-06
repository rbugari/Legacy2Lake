import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import HandoverView from "./HandoverView";
import { fetchWithAuth } from "../../lib/auth-client";

vi.mock("../StageHeader", () => ({
  default: () => <div data-testid="stage-header">StageHeader</div>,
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

vi.mock("../../lib/config", () => ({
  API_BASE_URL: "http://localhost:8000",
}));

vi.mock("../../lib/auth-client", () => ({
  fetchWithAuth: vi.fn(),
}));

const mockedFetchWithAuth = vi.mocked(fetchWithAuth);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("HandoverView", () => {
  it("renders ExecutiveSummaryPanel in overview with compact variant", async () => {
    const projectId = "project-handover-1";

    mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
      if (endpoint === `/projects/${projectId}`) {
        return {
          ok: true,
          json: async () => ({ id: projectId, name: "Demo", target_tech: "databricks" }),
        } as Response;
      }
      if (endpoint === `/projects/${projectId}/files`) {
        return {
          ok: true,
          json: async () => ({
            children: [
              { type: "file", name: "transform.py" },
              { type: "file", name: "model.sql" },
            ],
          }),
        } as Response;
      }
      return { ok: true, json: async () => ({}) } as Response;
    });

    render(
      <HandoverView
        projectId={projectId}
        projectName="Demo"
        onStageChange={vi.fn()}
        activeSection="overview"
        onSectionChange={vi.fn()}
      />
    );

    const panel = await screen.findByTestId("executive-summary-panel");
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveAttribute("data-project-id", projectId);
    expect(panel).toHaveAttribute("data-variant", "compact");
  });
});
