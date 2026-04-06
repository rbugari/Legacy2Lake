import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import DiscoveryView from "./DiscoveryView";
import { fetchWithAuth } from "../../lib/auth-client";

vi.mock("../StageHeader", () => ({
  default: () => <div data-testid="stage-header">StageHeader</div>,
}));

vi.mock("../UnifiedLogViewer", () => ({
  default: () => <div data-testid="unified-log-viewer">UnifiedLogViewer</div>,
}));

vi.mock("../ReadinessBadge", () => ({
  default: () => <div data-testid="readiness-badge">ReadinessBadge</div>,
}));

vi.mock("../../hooks/useConfirm", () => ({
  useConfirm: () => ({
    confirm: vi.fn(async () => true),
    ConfirmDialog: <div data-testid="confirm-dialog" />,
  }),
}));

vi.mock("../../lib/auth-client", () => ({
  fetchWithAuth: vi.fn(),
}));

const mockedFetchWithAuth = vi.mocked(fetchWithAuth);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DiscoveryView", () => {
  it("shows report-to-admin guidance and hides update button when detected origin is unsupported", async () => {
    const projectId = "project-discovery-1";

    mockedFetchWithAuth.mockImplementation(async (endpoint: string, options?: RequestInit) => {
      if (endpoint === `projects/${projectId}` && !options?.method) {
        return {
          ok: true,
          json: async () => ({ settings: { source_tech: "MySQL" } }),
        } as Response;
      }

      if (endpoint === `projects/${projectId}/source/files`) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            file_count: 3,
            by_extension: { sql: 3 },
          }),
        } as Response;
      }

      if (endpoint === `projects/${projectId}/quick-assessment` && options?.method === "POST") {
        return {
          ok: true,
          json: async () => ({
            score: 70,
            semaforo: "yellow",
            blockers: [],
            detected_techs: ["LegacyCobol"],
            llm_opinion: "Detected non-standard origin.",
          }),
        } as Response;
      }

      if (endpoint === `projects/${projectId}/file-inventory`) {
        return {
          ok: true,
          json: async () => ({ success: true, file_count: 3, files: [] }),
        } as Response;
      }

      if (endpoint === `projects/${projectId}/evidence`) {
        return {
          ok: true,
          json: async () => ({ success: true, items: [] }),
        } as Response;
      }

      return { ok: true, json: async () => ({}) } as Response;
    });

    const { rerender } = render(
      <DiscoveryView
        projectId={projectId}
        onStageChange={vi.fn()}
        activeSection="run-scan"
        onSectionChange={vi.fn()}
      />
    );

    // Wait for settings load
    await waitFor(() => {
      expect(mockedFetchWithAuth).toHaveBeenCalledWith(`projects/${projectId}`);
    });

    // Scan auto-triggers when section is run-scan

    await waitFor(() => {
      expect(mockedFetchWithAuth).toHaveBeenCalledWith(`projects/${projectId}/quick-assessment`, { method: "POST" });
    });

    // Switch to validation to assert Cross-check audit UI state
    rerender(
      <DiscoveryView
        projectId={projectId}
        onStageChange={vi.fn()}
        activeSection="validation"
        onSectionChange={vi.fn()}
      />
    );

    expect(
      await screen.findByText(/is not supported by the configured source cartridges/i)
    ).toBeInTheDocument();

    expect(screen.queryByRole("button", { name: /Update Configuration/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Report to Admin/i })).toBeInTheDocument();
  });
});
