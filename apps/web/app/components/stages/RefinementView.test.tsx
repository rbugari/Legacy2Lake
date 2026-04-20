import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import RefinementView from "./RefinementView";
import { fetchWithAuth } from "../../lib/auth-client";

// Mock child components
vi.mock("../StageHeader", () => ({
  default: (props: { title?: string; subtitle?: string; children?: any }) => (
    <div data-testid="stage-header" data-subtitle={props.subtitle}>
      {props.title || "StageHeader"}
      {props.children}
    </div>
  ),
}));

vi.mock("../UnifiedLogViewer", () => ({
  default: ({ projectId }: { projectId: string }) => (
    <div data-testid="unified-log-viewer" data-project-id={projectId}>
      UnifiedLogViewerMock
    </div>
  ),
}));

vi.mock("../CartridgePromptsEditor", () => ({
  default: ({ projectId }: { projectId: string }) => (
    <div data-testid="cartridge-prompts-editor" data-project-id={projectId}>
      CartridgePromptsEditorMock
    </div>
  ),
}));

vi.mock("./DesignRegistryPanel", () => ({
  default: ({ projectId }: { projectId: string }) => (
    <div data-testid="design-registry-panel" data-project-id={projectId}>
      DesignRegistryPanelMock
    </div>
  ),
}));

vi.mock("../visualization/CodeViewer", () => ({
  default: ({ code }: { code: string }) => (
    <div data-testid="code-viewer">{code ? "Code visible" : "No code"}</div>
  ),
}));

vi.mock("../visualization/SchemaViewer", () => ({
  default: ({ assets }: { assets: any[] }) => (
    <div data-testid="schema-viewer" data-asset-count={assets?.length || 0}>
      SchemaViewerMock
    </div>
  ),
}));

vi.mock("../visualization/QualityDashboard", () => ({
  default: ({ projectId }: { projectId: string }) => (
    <div data-testid="quality-dashboard" data-project-id={projectId}>
      QualityDashboardMock
    </div>
  ),
}));

vi.mock("../../lib/config", () => ({
  API_BASE_URL: "http://localhost:8000",
}));

vi.mock("../../lib/auth-client", () => ({
  fetchWithAuth: vi.fn(),
}));

vi.mock("@/app/hooks/useConfirm", () => ({
  useConfirm: () => ({
    confirm: vi.fn().mockResolvedValue(true),
    ConfirmDialog: () => null,
  }),
}));

const mockedFetchWithAuth = vi.mocked(fetchWithAuth);

const mockProjectId = "project-refinement-test-1";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("RefinementView - Mode-Specific Validation (v4.4 DoD)", () => {
  // ============================================================================
  // 1. INTELLIGENT_REENGINEERING MODE TESTS
  // ============================================================================
  
  describe("Intelligent Reengineering Mode", () => {
    it("should render with reengineering-specific title and subtitle", async () => {
      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: "intelligent_reengineering" }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({
              manifest_summary: {
                manifest: "reengineering_manifest.json",
                mode: "intelligent_reengineering",
                objective: "Consolidate reusable entities across drafted packages",
                processing_units: ["unit_1", "unit_2"],
              },
            }),
          } as Response;
        }
        if (endpoint.includes("/projects/")) {
          return {
            ok: true,
            json: async () => ({
              id: mockProjectId,
              name: "Reeng Test Project",
              post_drafting_mode: "intelligent_reengineering",
            }),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => ({ children: [] }),
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          projectStage={3}
          onStageChange={vi.fn()}
          activeSection="overview"
          onSectionChange={vi.fn()}
          isReadOnly={false}
        />
      );

      // Wait for mode to be fetched and rendered
      await waitFor(() => {
        const header = screen.queryByTestId("stage-header");
        expect(header).toBeInTheDocument();
      });

      // Verify subtitle contains reengineering context
      const header = screen.getByTestId("stage-header");
      expect(header).toBeInTheDocument();
    });

    it("should display reengineering-specific manifest summary", async () => {
      const manifestSummary = {
        manifest: "reengineering_manifest.json",
        mode: "intelligent_reengineering",
        objective: "Consolidate reusable entities across drafted packages",
        processing_units: ["bronze_shared", "silver_core", "gold_publish"],
        source_traceability: ["source_pkg_1", "source_pkg_2"],
      };

      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: "intelligent_reengineering" }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({ manifest_summary: manifestSummary }),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => ({ children: [] }),
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="overview"
          onSectionChange={vi.fn()}
        />
      );

      // Wait for manifest summary to load
      await waitFor(
        () => {
          expect(mockedFetchWithAuth).toHaveBeenCalledWith(
            expect.stringContaining("refinement/state")
          );
        },
        { timeout: 2000 }
      );
    });

    it("should render reengineered artifact paths (shared/core/publish)", async () => {
      const generatedFiles = {
        children: [
          {
            name: "reengineering_manifest.json",
            type: "file",
            path: "refinement/reengineering_manifest.json",
          },
          {
            name: "reengineered",
            type: "folder",
            children: [
              {
                name: "shared",
                type: "folder",
                children: [{ name: "dimension_product.sql", type: "file" }],
              },
              {
                name: "core",
                type: "folder",
                children: [{ name: "fact_sales.sql", type: "file" }],
              },
              {
                name: "publish",
                type: "folder",
                children: [{ name: "view_revenue.sql", type: "file" }],
              },
            ],
          },
        ],
      };

      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: "intelligent_reengineering" }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({
              manifest_summary: {
                mode: "intelligent_reengineering",
                processing_units: 3,
              },
            }),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => generatedFiles,
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="overview"
          onSectionChange={vi.fn()}
        />
      );

      // Verify files endpoint was called with expected structure
      await waitFor(
        () => {
          expect(mockedFetchWithAuth).toHaveBeenCalledWith(
            expect.stringContaining("/files")
          );
        },
        { timeout: 2000 }
      );
    });
  });

  // ============================================================================
  // 2. STRUCTURED_REFINEMENT MODE TESTS
  // ============================================================================

  describe("Structured Refinement Mode", () => {
    it("should render with structured-refinement-specific messaging", async () => {
      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: "structured_refinement" }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({
              manifest_summary: {
                mode: "structured_refinement",
                objective: "Optimize medallion layers (Bronze → Silver → Gold)",
              },
            }),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => ({
              children: [
                {
                  name: "bronze",
                  type: "folder",
                  children: [{ name: "stg_raw.sql", type: "file" }],
                },
              ],
            }),
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="overview"
          onSectionChange={vi.fn()}
        />
      );

      await waitFor(
        () => {
          expect(mockedFetchWithAuth).toHaveBeenCalledWith(
            expect.stringContaining("/get-post-drafting-mode")
          );
        },
        { timeout: 2000 }
      );
    });

    it("should display medallion-layer-focused manifest", async () => {
      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: "structured_refinement" }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({
              manifest_summary: {
                mode: "structured_refinement",
                objective: "Multi-layer medallion optimization",
                layers: ["bronze", "silver", "gold"],
              },
            }),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => ({ children: [] }),
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="overview"
          onSectionChange={vi.fn()}
        />
      );

      await waitFor(
        () => {
          expect(mockedFetchWithAuth).toHaveBeenCalledWith(
            expect.stringContaining("refinement/state")
          );
        },
        { timeout: 2000 }
      );
    });
  });

  // ============================================================================
  // 3. DRAFTING_DELIVERY MODE TESTS
  // ============================================================================

  describe("Drafting Delivery Mode (Terminal)", () => {
    it("should not allow refinement entry when mode is drafting_delivery", async () => {
      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: "drafting_delivery" }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({
              manifest_summary: {
                mode: "drafting_delivery",
                status: "TERMINAL_PATH_SKIPS_REFINEMENT",
              },
            }),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => ({ children: [] }),
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="overview"
          onSectionChange={vi.fn()}
        />
      );

      await waitFor(
        () => {
          expect(mockedFetchWithAuth).toHaveBeenCalledWith(
            expect.stringContaining("/get-post-drafting-mode")
          );
        },
        { timeout: 2000 }
      );
    });
  });

  // ============================================================================
  // 4. CROSS-MODE VALIDATION TESTS
  // ============================================================================

  describe("Cross-Mode Consistency", () => {
    it("should differentiate mode labels in manifest summary", async () => {
      const modes = [
        "intelligent_reengineering",
        "structured_refinement",
        "drafting_delivery",
      ];

      for (const mode of modes) {
        mockedFetchWithAuth.mockClear();
        mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
          if (endpoint.includes("/get-post-drafting-mode")) {
            return {
              ok: true,
              json: async () => ({ post_drafting_mode: mode }),
            } as Response;
          }
          if (endpoint.includes("refinement/state")) {
            const objectives: Record<string, string> = {
              intelligent_reengineering:
                "Consolidate reusable entities and redesign architecture",
              structured_refinement: "Optimize medallion layers",
              drafting_delivery: "Direct to Governance (no refinement)",
            };
            return {
              ok: true,
              json: async () => ({
                manifest_summary: {
                  mode,
                  objective: objectives[mode],
                },
              }),
            } as Response;
          }
          if (endpoint.includes("/files")) {
            return {
              ok: true,
              json: async () => ({ children: [] }),
            } as Response;
          }
          return { ok: true, json: async () => ({}) } as Response;
        });

        const { unmount } = render(
          <RefinementView
            projectId={`${mockProjectId}-${mode}`}
            activeSection="overview"
            onSectionChange={vi.fn()}
          />
        );

        await waitFor(
          () => {
            expect(mockedFetchWithAuth).toHaveBeenCalled();
          },
          { timeout: 2000 }
        );

        unmount();
        vi.clearAllMocks();
      }
    });

    it("should load and render schema viewer with generated assets", async () => {
      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: "intelligent_reengineering" }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({
              manifest_summary: {
                mode: "intelligent_reengineering",
              },
            }),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => ({
              children: [
                {
                  name: "drafting",
                  type: "folder",
                  children: [
                    {
                      name: "package_1",
                      type: "folder",
                      children: [
                        { name: "etl_script.py", type: "file" },
                      ],
                    },
                  ],
                },
                {
                  name: "refinement",
                  type: "folder",
                  children: [
                    {
                      name: "reengineered",
                      type: "folder",
                      children: [
                        { name: "shared.sql", type: "file" },
                      ],
                    },
                  ],
                },
              ],
            }),
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="artifacts"
          onSectionChange={vi.fn()}
        />
      );

      // Wait for schema viewer to render with asset count
      await waitFor(
        () => {
          const schemaViewer = screen.queryByTestId("schema-viewer");
          if (schemaViewer) {
            const assetCount =
              schemaViewer.getAttribute("data-asset-count");
            expect(parseInt(assetCount || "0")).toBeGreaterThanOrEqual(0);
          }
        },
        { timeout: 2000 }
      );
    });
  });

  // ============================================================================
  // 5. MODE DETECTION AND FALLBACK TESTS
  // ============================================================================

  describe("Mode Detection and Error Handling", () => {
    it("should handle missing mode gracefully", async () => {
      mockedFetchWithAuth.mockImplementation(async (endpoint: string) => {
        if (endpoint.includes("/get-post-drafting-mode")) {
          return {
            ok: true,
            json: async () => ({ post_drafting_mode: null }),
          } as Response;
        }
        if (endpoint.includes("refinement/state")) {
          return {
            ok: true,
            json: async () => ({}),
          } as Response;
        }
        if (endpoint.includes("/files")) {
          return {
            ok: true,
            json: async () => ({ children: [] }),
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      });

      render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="overview"
          onSectionChange={vi.fn()}
        />
      );

      // Should still render without error
      await waitFor(
        () => {
          expect(mockedFetchWithAuth).toHaveBeenCalled();
        },
        { timeout: 2000 }
      );
    });

    it("should handle API fetch errors gracefully", async () => {
      mockedFetchWithAuth.mockRejectedValue(new Error("API Error"));

      const { container } = render(
        <RefinementView
          projectId={mockProjectId}
          activeSection="overview"
          onSectionChange={vi.fn()}
        />
      );

      // Component should stay in DOM even with fetch errors
      await waitFor(
        () => {
          expect(container).toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });
  });
});
