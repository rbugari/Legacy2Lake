import { useState, useEffect, useCallback, useRef } from "react";
import { Play, X, Code } from "lucide-react";
import { fetchWithAuth } from "../../lib/auth-client";
import UnifiedLogViewer from "../UnifiedLogViewer";
import UnifiedFileExplorer from "../UnifiedFileExplorer";
import CartridgePromptEditor from "../CartridgePromptEditor";
import TechnologyMixer from "./TechnologyMixer";
import ProcessLockModal from "../ProcessLockModal";
import SchemaViewer from "../visualization/SchemaViewer";
import GenerationStats from "../visualization/GenerationStats";
import CodeGenerationSummary from "../visualization/CodeGenerationSummary";
import StageHeader from "../StageHeader";
import { useConfirm } from '@/app/hooks/useConfirm';

const DRAFTING_AGENTS = [
    { id: 'A', name: 'The Architect', role: 'Schema & DDL generation' },
    { id: 'B', name: 'The Builder', role: 'Data transformation scripting' },
    { id: 'C', name: 'The Orchestrator', role: 'Pipeline orchestration code' },
    { id: 'F', name: 'The Framework Generator', role: 'Framework boilerplate & helpers' },
    { id: 'G', name: 'The Governor', role: 'Governance metadata injection' },
];

// Helper: Extract generated files from drafting folder
function extractDraftingFiles(children: any[]): any[] {
    const assets: any[] = [];

    const traverseFolder = (nodes: any[], currentPath: string = '') => {
        for (const node of nodes) {
            const fullPath = currentPath ? `${currentPath}/${node.name}` : node.name;

            // Include only files from drafting/ folder
            if (node.type === 'file' && fullPath.includes('/drafting/')) {
                // Extract file extension
                const ext = node.name.split('.').pop()?.toUpperCase() || 'FILE';

                // Create asset object compatible with SchemaViewer
                assets.push({
                    object_id: fullPath.replace(/\//g, '_'), // Unique ID from path
                    id: fullPath.replace(/\//g, '_'),
                    source_name: node.name,
                    filename: node.name,
                    target_name: node.name.replace(/\.(py|sql|scala|java)$/, ''),
                    category: 'CORE',
                    type: ext,
                    path: fullPath // Store full path for schema lookup
                });
            }

            // Recurse into subfolders
            if (node.type === 'folder' && node.children) {
                traverseFolder(node.children, fullPath);
            }
        }
    };

    traverseFolder(children);
    return assets;
}

interface DraftingViewProps {
    projectId: string;
    projectStage?: number;
    onStageChange: (stage: number) => void;
    onCompletion?: (completed: boolean) => void;
    isReadOnly?: boolean;
    activeTenantId?: string; // [NEW] Contextual Execution
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void;
    activeSection: string;
    onSectionChange: (section: string) => void;
}

export default function DraftingView({
    projectId,
    projectStage,
    onStageChange,
    onCompletion,
    isReadOnly,
    activeTenantId,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent,
    activeSection,
    onSectionChange
}: DraftingViewProps) {
    const [isInitialLoading, setIsInitialLoading] = useState(true); // Initial data fetch
    const [isOrchestrationRunning, setIsOrchestrationRunning] = useState(false); // Active orchestration process
    const { confirm, ConfirmDialog } = useConfirm();
    const [logs, setLogs] = useState<string[]>([]); // Simple log stream simulation
    const [progress, setProgress] = useState(0);
    const [migrationLimit, setMigrationLimit] = useState(0); // [NEW] Batch Limit control
    const [isApproving, setIsApproving] = useState(false);
    const [assets, setAssets] = useState<any[]>([]); // Objects/assets for SchemaViewer

    // Process Lock Modal state
    const [isLockModalOpen, setIsLockModalOpen] = useState(false);
    const [lockDetails, setLockDetails] = useState<{ processType: string; lockedBy: string; message: string }>(
        { processType: '', lockedBy: '', message: '' }
    );

    // Helper: Fetch Logs with status detection
    const fetchOrchestrationLogs = useCallback(async () => {
        try {
            // Fetch execution logs
            const res = await fetchWithAuth(`projects/${projectId}/execution-logs?type=migration`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const data = await res.json();
            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");
                setLogs(logLines);
            }

            // Check project status to detect completion
            const statusRes = await fetchWithAuth(`discovery/status/${projectId}`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const statusData = await statusRes.json();

            // If status is DRAFTED and we're currently running, process is complete
            if (statusData.status === "DRAFTED" && isOrchestrationRunning) {
                console.log("[DraftingView] Orchestration complete, stopping polling");
                setProgress(100);
                setIsOrchestrationRunning(false);
                // onCompletion will be called in separate useEffect to avoid re-render issues
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    }, [projectId, activeTenantId, isOrchestrationRunning]);

    // Load base data on mount
    useEffect(() => {
        fetchOrchestrationLogs();

        // Fetch Project Settings to sync migration limit
        const loadSettings = async () => {
            try {
                const res = await fetchWithAuth(`projects/${projectId}/settings`);
                const data = await res.json();
                if (data.settings && data.settings.migration_limit !== undefined) {
                    setMigrationLimit(data.settings.migration_limit);
                }
            } catch (e) { console.error("Error syncing settings", e); }
        };
        loadSettings();

        // Load assets from discovery for SchemaViewer
        // In Drafting, we want GENERATED files (drafting folder), not original assets
        const loadAssets = async () => {
            try {
                const filesRes = await fetchWithAuth(`projects/${projectId}/files`);
                const filesData = await filesRes.json();

                // Extract files from drafting folder
                const extractedAssets = extractDraftingFiles(filesData.children || []);
                console.log('[DraftingView] Loaded generated files:', extractedAssets.length);
                setAssets(extractedAssets);
            } catch (err) {
                console.warn('[DraftingView] Could not load generated files:', err);
            }
        };
        loadAssets();

        setIsInitialLoading(false);
    }, [projectId]);

    // Poll logs when orchestration is running (every 3 seconds)
    useEffect(() => {
        let interval: NodeJS.Timeout;
        let initialTimeout: NodeJS.Timeout;

        if (isOrchestrationRunning) {
            // Wait 1.5 seconds before first fetch to allow backend to clear old logs
            initialTimeout = setTimeout(() => {
                fetchOrchestrationLogs();
                // Then poll every 3 seconds
                interval = setInterval(fetchOrchestrationLogs, 3000);
            }, 1500);
        }

        return () => {
            if (interval) clearInterval(interval);
            if (initialTimeout) clearTimeout(initialTimeout);
        };
    }, [isOrchestrationRunning, fetchOrchestrationLogs]);

    // Call onCompletion when orchestration finishes (separate useEffect to avoid re-render loops)
    const prevOrchestrationRunning = useRef(false);
    useEffect(() => {
        if (prevOrchestrationRunning.current === true && isOrchestrationRunning === false && progress === 100) {
            console.log("[DraftingView] Orchestration completed, calling onCompletion");
            if (onCompletion) onCompletion(true);
        }
        prevOrchestrationRunning.current = isOrchestrationRunning;
    }, [isOrchestrationRunning, progress, onCompletion]);

    // --- Tab 1: Execution Handlers ---
    const handleRunMigration = async () => {
        // Check if re-executing a previous stage (rollback warning)
        const CURRENT_STAGE = 2; // Drafting is stage 2
        if (projectStage !== undefined && projectStage > CURRENT_STAGE) {
            const phaseNames = ['Discovery', 'Triage', 'Drafting', 'Refinement', 'Governance', 'Handover'];
            const lostPhases: string[] = [];
            for (let i = CURRENT_STAGE + 1; i <= projectStage; i++) {
                if (i < phaseNames.length) lostPhases.push(phaseNames[i]);
            }
            const rollbackOk = await confirm({
                variant: 'rollback',
                title: 'Re-running Drafting will roll back progress',
                description: 'The project will return to Stage 2. Triage data is preserved.',
                lostPhases,
                confirmLabel: 'Yes, roll back & re-run',
            });
            if (!rollbackOk) return;
        }

        const runOk = await confirm({
            variant: 'execute',
            title: 'Run Migration Pipeline?',
            description: 'The following AI agents will generate all migration code for your project.',
            agents: DRAFTING_AGENTS,
            confirmLabel: 'Run Pipeline',
        });
        if (!runOk) return;

        // Auto-navigate to logs view after confirmation
        if (onSectionChange) {
            onSectionChange('logs');
        }

        setIsOrchestrationRunning(true);
        setProgress(0); // Reset progress to 0% at start
        // Initial feedback
        setLogs(["Starting Migration Orchestrator in background..."]);
        setProgress(10);

        try {
            const res = await fetchWithAuth("transpile/orchestrate", {
                method: "POST",
                headers: {
                    ...(activeTenantId ? { "X-Tenant-ID": activeTenantId } : {})
                },
                body: JSON.stringify({ project_id: projectId, limit: migrationLimit }) // Dynamic limit from state
            });

            // Check for lock error (423)
            if (res.status === 423) {
                const data = await res.json();
                setLockDetails({
                    processType: 'drafting',
                    lockedBy: data.detail?.locked_by || data.locked_by || 'Unknown User',
                    message: data.detail?.message || data.message || 'Process is already running on this project'
                });
                setIsLockModalOpen(true);
                setIsOrchestrationRunning(false);
                return;
            }

            const data = await res.json();

            if (data.error) {
                const errorMsg = typeof data.error === 'string' ? data.error : JSON.stringify(data.error, null, 2);
                setLogs(prev => [...prev, `[ERROR] ${errorMsg}`]);
                setIsOrchestrationRunning(false);
            } else if (data.status === "RUNNING") {
                // Background task started successfully
                setLogs(prev => [...prev, data.message || "Orchestration started in background. Monitor logs for progress."]);
                // Polling will continue until status changes to DRAFTED
            } else {
                // Unexpected response format (backwards compatibility)
                await fetchOrchestrationLogs();
                setProgress(100);
                setIsOrchestrationRunning(false);
                if (onCompletion) onCompletion(true);
            }
        } catch (e) {
            const errorMsg = e instanceof Error ? e.message : typeof e === 'string' ? e : JSON.stringify(e);
            setLogs(prev => [...prev, `[Network Error] ${errorMsg}`]);
            setIsOrchestrationRunning(false);
        }
    };

    const handleApprove = async () => {
        setIsApproving(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/stage`, {
                method: "POST",
                headers: {
                    ...(activeTenantId ? { "X-Tenant-ID": activeTenantId } : {})
                },
                body: JSON.stringify({ stage: "3" })
            });
            const data = await res.json();
            if (data.success) {
                onStageChange(3);
            } else {
                setIsApproving(false);
            }
        } catch (e) {
            console.error("Failed to update stage", e);
            setIsApproving(false);
        }
    };

    const handleCancelMigration = async () => {
        const cancelOk = await confirm({ variant: 'danger', title: 'Cancel migration?', description: 'The running pipeline will be stopped. Partial files already generated will remain.', confirmLabel: 'Yes, cancel', cancelLabel: 'Keep running' });
        if (!cancelOk) return;

        try {
            const res = await fetchWithAuth(`projects/${projectId}/cancel`, {
                method: "POST",
                headers: {
                    ...(activeTenantId ? { "X-Tenant-ID": activeTenantId } : {})
                }
            });
            const data = await res.json();

            if (data.success) {
                setIsOrchestrationRunning(false);
                setLogs(prev => [...prev, "[SYSTEM] Process cancelled by user."]);
            } else {
                const errorMsg = typeof data.error === 'string' ? data.error : JSON.stringify(data.error || 'Unknown error');
                setLogs(prev => [...prev, `[ERROR] Failed to cancel: ${errorMsg}`]);
            }
        } catch (e) {
            console.error("Failed to cancel process", e);
            const errorMsg = e instanceof Error ? e.message : (typeof e === 'string' ? e : JSON.stringify(e));
            setLogs(prev => [...prev, `[ERROR] Network error during cancellation: ${errorMsg}`]);
        }
    };


    // Watch for sidebar action triggers
    useEffect(() => {
        if (activeSection === 'run-translation') {
            if (!isOrchestrationRunning) {
                handleRunMigration();
            }
            onSectionChange('logs');
        }
    }, [activeSection, isOrchestrationRunning, onSectionChange]);

    return (
        <div className="flex flex-col h-full bg-[var(--background)]">
            <StageHeader
                title="Stage 2: Cloud Drafting"
                subtitle="Code Generator: Cloud-native Medallion code generator"
                icon={<Code className="text-emerald-500" />}
                helpText="Generation of optimized PySpark, dbt or Snowflake code based on the approved design."
                onApprove={handleApprove}
                approveLabel="Next Phase: Refinement"
                isApproveDisabled={isOrchestrationRunning || progress < 100}
                isExecuting={isApproving}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            />

            {/* Main Content Area - Sprint 14: Sidebar managed at workspace level */}
            <div className="flex-1 overflow-hidden p-6">
                {/* EXECUTION GROUP */}
                {/* Logs Section (handles both 'logs' and 'progress' from sidebar) */}
                {(activeSection === "logs" || activeSection === "progress") && (
                    <div className="h-full max-w-7xl mx-auto">
                        <UnifiedLogViewer
                            mode="realtime"
                            projectId={projectId}
                            isRunning={isOrchestrationRunning}
                            logs={logs}
                            processName="Drafting Pipeline"
                            variant="panel"
                        />
                    </div>
                )}

                {/* OUTPUT GROUP */}
                {/* Code Preview Section - Generation Summary */}
                {activeSection === "code" && (
                    <div className="h-full">
                        <CodeGenerationSummary
                            projectId={projectId}
                            activeTenantId={activeTenantId}
                        />
                    </div>
                )}

                {/* Output Files Section - UnifiedFileExplorer */}
                {activeSection === "files" && (
                    <UnifiedFileExplorer projectId={projectId} activeTenantId={activeTenantId} title="Generated Output Files" />
                )}

                {/* Generation Stats Section - NEW */}
                {activeSection === "stats" && (
                    <div className="h-full">
                        <GenerationStats projectId={projectId} activeTenantId={activeTenantId} />
                    </div>
                )}

                {/* TARGET CONFIGURATION GROUP */}
                {/* Cartridge Settings (Technology Mixer repurposed) */}
                {activeSection === "cartridge" && (
                    <div className="h-full">
                        <TechnologyMixer projectId={projectId} />
                    </div>
                )}

                {/* Generation Prompts (Cartridge) */}
                {activeSection === "prompts" && (
                    <div className="h-full">
                        <CartridgePromptEditor projectId={projectId} />
                    </div>
                )}

                {/* Target Schema Preview */}
                {activeSection === "schema" && (
                    <div className="h-full">
                        <SchemaViewer
                            projectId={projectId}
                            assets={assets}
                            showHistory={true}
                        />
                    </div>
                )}
            </div>

            {/* Process Lock Modal */}
            <ProcessLockModal
                isOpen={isLockModalOpen}
                onClose={() => setIsLockModalOpen(false)}
                processType={lockDetails.processType}
                lockedBy={lockDetails.lockedBy}
                message={lockDetails.message}
            />
            {ConfirmDialog}
        </div>
    );
}
