import { useState, useEffect, useCallback, useRef } from "react";
import { Play, X, Code, CheckCircle } from "lucide-react";
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
    const isOrchestrationRunningRef = useRef(false); // Ref to read in callbacks without adding to deps
    const [isDraftingComplete, setIsDraftingComplete] = useState(false); // True when project is in DRAFTED status
    const { confirm, ConfirmDialog } = useConfirm();
    const [logs, setLogs] = useState<string[]>([]); // Simple log stream simulation
    const [progress, setProgress] = useState(0);
    const [migrationLimit, setMigrationLimit] = useState(0); // [NEW] Batch Limit control
    const [isApproving, setIsApproving] = useState(false);
    const [assets, setAssets] = useState<any[]>([]); // Objects/assets for SchemaViewer

    // Keep ref in sync with state
    useEffect(() => { isOrchestrationRunningRef.current = isOrchestrationRunning; }, [isOrchestrationRunning]);

    // Process Lock Modal state
    const [isLockModalOpen, setIsLockModalOpen] = useState(false);
    const [lockDetails, setLockDetails] = useState<{ processType: string; lockedBy: string; message: string }>(
        { processType: '', lockedBy: '', message: '' }
    );

    const getMigrationLogLines = useCallback(async (): Promise<string[]> => {
        const res = await fetchWithAuth(`projects/${projectId}/execution-logs?type=migration`, {
            headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
        });
        const data = await res.json();
        return (data.logs || "")
            .split("\n")
            .map((line: string) => line.trimEnd())
            .filter((line: string) => line.trim() !== "");
    }, [projectId, activeTenantId]);

    // Helper: Fetch Logs with status detection
    const fetchOrchestrationLogs = useCallback(async () => {
        try {
            const logLines = await getMigrationLogLines();
            if (logLines.length > 0) {
                setLogs(logLines);
            }

            // Check project status to detect completion
            const statusRes = await fetchWithAuth(`discovery/status/${projectId}`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const statusData = await statusRes.json();

            // Always mark complete when status is DRAFTED or any later stage
            // (e.g. user moves to Refinement stage then comes back — status will be REFINED)
            const DRAFTED_OR_BEYOND = ['DRAFTED', 'REFINING', 'REFINED', 'CERTIFYING', 'CERTIFIED', 'GOVERNED', 'DELIVERED'];
            if (DRAFTED_OR_BEYOND.includes(statusData.status)) {
                setIsDraftingComplete(true);
                setProgress(100);
                if (isOrchestrationRunningRef.current) {
                    console.log("[DraftingView] Orchestration complete, stopping polling");
                    setIsOrchestrationRunning(false);
                }
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    }, [projectId, activeTenantId, getMigrationLogLines]); // Stable ref: no isOrchestrationRunning dependency

    // Load base data on mount
    useEffect(() => {
        // Only load previous logs if there's an active run or a completed run.
        // If status is TRIAGED (just entered Drafting), start with empty logs.
        const initLogs = async () => {
            try {
                const statusRes = await fetchWithAuth(`discovery/status/${projectId}`, {
                    headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
                });
                const statusData = await statusRes.json();
                const status = statusData.status;

                const DRAFTED_OR_BEYOND = ['DRAFTED', 'REFINING', 'REFINED', 'CERTIFYING', 'CERTIFIED', 'GOVERNED', 'DELIVERED'];
                if (status === 'DRAFTING') {
                    // Treat DRAFTING as "running" only if migration logs already exist.
                    // This avoids false polling loops when the user has entered Stage 2
                    // but orchestration has not actually been started yet.
                    const existingLogs = await getMigrationLogLines();
                    if (existingLogs.length > 0) {
                        setLogs(existingLogs);
                        await fetchOrchestrationLogs();
                        setIsOrchestrationRunning(true);
                    }
                } else if (DRAFTED_OR_BEYOND.includes(status)) {
                    // Completed run — load final logs and show completion state
                    await fetchOrchestrationLogs();
                    setIsDraftingComplete(true);
                    setProgress(100);
                }
                // Otherwise (TRIAGED, etc.) — leave logs empty, fresh start
            } catch (e) {
                console.error("Failed to init logs", e);
            }
        };
        initLogs();

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
    }, [projectId, activeTenantId, fetchOrchestrationLogs, getMigrationLogLines]);

    // Poll logs when orchestration is running (every 3 seconds)
    // Safety: auto-stop after 45 minutes to prevent infinite polling if backend dies
    const MAX_POLL_MS = 45 * 60 * 1000;
    useEffect(() => {
        let interval: NodeJS.Timeout;
        let initialTimeout: NodeJS.Timeout;
        let safetyTimeout: NodeJS.Timeout;

        if (isOrchestrationRunning) {
            // Wait 1.5 seconds before first fetch to allow backend to clear old logs
            initialTimeout = setTimeout(() => {
                fetchOrchestrationLogs();
                // Then poll every 3 seconds
                interval = setInterval(fetchOrchestrationLogs, 3000);
            }, 1500);

            // Safety timeout: stop polling after MAX_POLL_MS even if backend never responds
            safetyTimeout = setTimeout(() => {
                console.warn('[DraftingView] Safety timeout reached — stopping polling.');
                setIsOrchestrationRunning(false);
                setLogs(prev => [...prev, '[TIMEOUT] Process monitoring stopped after 45 minutes. Check server logs.']);
            }, MAX_POLL_MS);
        }

        return () => {
            if (interval) clearInterval(interval);
            if (initialTimeout) clearTimeout(initialTimeout);
            if (safetyTimeout) clearTimeout(safetyTimeout);
        };
    }, [isOrchestrationRunning]); // fetchOrchestrationLogs is now stable (no state in its deps)

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
        setIsDraftingComplete(false); // Reset completion flag on new run
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
    // IMPORTANT: clear the section FIRST to avoid re-trigger loop, THEN run the confirm dialog
    useEffect(() => {
        if (activeSection === 'run-translation') {
            onSectionChange('logs'); // Go to logs immediately so user sees the confirm dialog
            if (!isOrchestrationRunning) {
                handleRunMigration(); // This already has confirm() inside — user must approve
            }
        }
    }, [activeSection]); // Only trigger on section change, NOT on isOrchestrationRunning

    return (
        <div className="flex flex-col h-full bg-[var(--background)]">
            <StageHeader
                title="Stage 2: Cloud Drafting"
                subtitle="Generate the first working target implementation from the approved triage baseline"
                icon={<Code className="text-emerald-500" />}
                helpText="Use Drafting to produce a reviewable target baseline, inspect generated artifacts, and adjust cartridge settings before refinement."
                onApprove={handleApprove}
                approveLabel="Next Phase: Refinement"
                isApproveDisabled={isOrchestrationRunning || !isDraftingComplete}
                isExecuting={isApproving}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            />

            {/* Main Content Area - Sprint 14: Sidebar managed at workspace level */}
            <div className="flex-1 overflow-hidden p-6">
                {activeSection === "overview" && (
                    <div className="h-full max-w-6xl mx-auto overflow-y-auto space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <p className="text-[11px] font-black uppercase tracking-widest text-emerald-400">Drafting Status</p>
                                <p className="mt-3 text-2xl font-black text-white">{isOrchestrationRunning ? 'Running' : isDraftingComplete ? 'Complete' : 'Ready'}</p>
                                <p className="mt-2 text-sm text-gray-400">Direct translation and generation of target artifacts.</p>
                            </div>
                            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <p className="text-[11px] font-black uppercase tracking-widest text-emerald-400">Generated Files</p>
                                <p className="mt-3 text-2xl font-black text-white">{assets.length}</p>
                                <p className="mt-2 text-sm text-gray-400">Artifacts currently detected in the Drafting output.</p>
                            </div>
                            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <p className="text-[11px] font-black uppercase tracking-widest text-emerald-400">Execution Limit</p>
                                <p className="mt-3 text-2xl font-black text-white">{migrationLimit || 'All'}</p>
                                <p className="mt-2 text-sm text-gray-400">Current batch limit for orchestration.</p>
                            </div>
                        </div>

                        <div className="rounded-3xl border border-white/10 bg-black/20 p-8">
                            <h2 className="text-xl font-black text-white">Stage Home</h2>
                            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-gray-400">
                                Use Drafting to generate the first working target implementation, review the output, and adjust cartridge settings before moving into refinement.
                            </p>
                            <div className="mt-6 flex flex-wrap gap-3">
                                <button
                                    onClick={() => onSectionChange('run-translation')}
                                    className="px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-emerald-500"
                                >
                                    {isOrchestrationRunning ? 'View Running Pipeline' : 'Run Pipeline'}
                                </button>
                                <button
                                    onClick={() => onSectionChange('code')}
                                    className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                >
                                    Generation Summary
                                </button>
                                <button
                                    onClick={() => onSectionChange('files')}
                                    className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                >
                                    Output Files
                                </button>
                                <button
                                    onClick={() => onSectionChange('cartridge')}
                                    className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                >
                                    Configure Target
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* EXECUTION GROUP */}
                {/* Logs Section (handles both 'logs' and 'progress' from sidebar) */}
                {(activeSection === "logs" || activeSection === "progress") && (
                    <div className="h-full max-w-7xl mx-auto flex flex-col gap-4">

                        {/* ── Running Banner with Cancel button ── */}
                        {isOrchestrationRunning && (
                            <div className="flex items-center justify-between gap-3 px-6 py-3 bg-amber-500/10 border border-amber-500/30 rounded-2xl shrink-0">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                                    <p className="text-sm font-semibold text-amber-400">Pipeline running...</p>
                                    <p className="text-xs text-gray-500">AI agents are generating your migration code</p>
                                </div>
                                <button
                                    onClick={handleCancelMigration}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/10 transition-colors"
                                >
                                    <X size={12} />
                                    Stop
                                </button>
                            </div>
                        )}

                        {/* ── Completion Banner ── informational only; Next button is in StageHeader */}
                        {isDraftingComplete && !isOrchestrationRunning && (
                            <div className="flex items-center gap-3 px-6 py-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl shrink-0 animate-in fade-in slide-in-from-top-2 duration-300">
                                <CheckCircle size={18} className="text-emerald-400 shrink-0" />
                                <div>
                                    <p className="text-sm font-black text-emerald-400 uppercase tracking-wide">Drafting Complete</p>
                                    <p className="text-xs text-gray-500 mt-0.5">All assets processed successfully — review the output or use the <strong className="text-gray-400">Next Phase</strong> button above to proceed to Refinement.</p>
                                </div>
                            </div>
                        )}

                        {!isDraftingComplete && !isOrchestrationRunning && (
                            <div className="flex items-center justify-between gap-3 px-6 py-4 bg-sky-500/10 border border-sky-500/30 rounded-2xl shrink-0">
                                <div>
                                    <p className="text-sm font-black text-sky-400 uppercase tracking-wide">Drafting Ready</p>
                                    <p className="text-xs text-gray-500 mt-0.5">
                                        Stage 2 is open, but the migration pipeline has not started yet. Use
                                        <strong className="text-gray-400"> Run Pipeline</strong> to begin generation.
                                    </p>
                                </div>
                                <button
                                    onClick={() => onSectionChange('run-translation')}
                                    className="flex items-center gap-2 px-4 py-2 bg-sky-500 hover:bg-sky-400 text-white text-xs font-black uppercase tracking-wider rounded-xl transition-all active:scale-95"
                                >
                                    <Play size={13} />
                                    Run Pipeline
                                </button>
                            </div>
                        )}

                        <div className="flex-1 min-h-0">
                            <UnifiedLogViewer
                                mode="realtime"
                                projectId={projectId}
                                isRunning={isOrchestrationRunning}
                                logs={logs}
                                processName="Drafting Pipeline"
                                variant="panel"
                            />
                        </div>
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
