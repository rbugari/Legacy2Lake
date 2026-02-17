import { useState, useEffect, useCallback, useRef } from "react";
import { Play, FileText, Folder, CheckCircle, Terminal, RefreshCw, FolderOpen, FileCode, Lock, ChevronRight, ChevronDown, Settings, Brain, Code, PanelLeftClose, PanelLeftOpen, X, Database } from "lucide-react";
import { fetchWithAuth } from "../../lib/auth-client";
import ProcessProgress from "../ProcessProgress";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import PromptsExplorer from "../PromptsExplorer";
import DesignRegistryPanel from "./DesignRegistryPanel";
import TechnologyMixer from "./TechnologyMixer";
import ProjectSettingsPanel from "./ProjectSettingsPanel";
import ProcessLockModal from "../ProcessLockModal";
import CodeViewer from "../visualization/CodeViewer";
import SchemaViewer from "../visualization/SchemaViewer";
import PerformanceDashboard from "../visualization/PerformanceDashboard"; // Sprint 12
import QualityDashboard from "../visualization/QualityDashboard"; // Sprint 11 - V3.9

// --- Types ---
interface FileNode {
    name: string;
    path: string;
    type: "file" | "folder";
    children?: FileNode[];
    last_modified?: number;
}

import StageHeader from "../StageHeader";

interface DraftingViewProps {
    projectId: string;
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
    const [logs, setLogs] = useState<string[]>([]); // Simple log stream simulation
    const [progress, setProgress] = useState(0);
    const [migrationLimit, setMigrationLimit] = useState(0); // [NEW] Batch Limit control
    const [isApproving, setIsApproving] = useState(false);
    
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
        setIsInitialLoading(false);
    }, [projectId]);

    // Poll logs when orchestration is running (every 3 seconds)
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isOrchestrationRunning) {
            // Immediate fetch
            fetchOrchestrationLogs();
            // Then poll every 3 seconds
            interval = setInterval(fetchOrchestrationLogs, 3000);
        }
        return () => {
            if (interval) clearInterval(interval);
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
        // Confirmation for cost
        const confirmMsg = "Esta acción ejecutará la migración completa (Agentes A, B, C, F, G). Esto incurre en costos de tokens y tiempo de procesamiento.\n\n¿Deseas continuar?";
        if (!window.confirm(confirmMsg)) return;

        setIsOrchestrationRunning(true);
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
                body: JSON.stringify({ stage: "4" })
            });
            const data = await res.json();
            if (data.success) {
                onStageChange(4);
            } else {
                setIsApproving(false);
            }
        } catch (e) {
            console.error("Failed to update stage", e);
            setIsApproving(false);
        }
    };

    const handleCancelMigration = async () => {
        if (!window.confirm("¿Estás seguro de que deseas cancelar el proceso de migración?")) return;

        try {
            const res = await fetchWithAuth(`projects/${projectId}/cancel`, {
                method: "POST",
                headers: {
                    ...(activeTenantId ? { "X-Tenant-ID": activeTenantId } : {})
                }
            });
            const data = await res.json();

            if (data.success) {
                setIsRunning(false);
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


    return (
        <div className="flex flex-col h-full bg-[var(--background)]">
            <StageHeader
                title="Stage 3: Cloud Drafting"
                subtitle="Code Generator: Cloud-native Medallion code generator"
                icon={<Code className="text-emerald-500" />}
                helpText="Generation of optimized PySpark, dbt or Snowflake code based on the approved design."
                onApprove={handleApprove}
                approveLabel="Finalize & Refine"
                isApproveDisabled={isOrchestrationRunning || progress < 100}
                isExecuting={isApproving}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            >
                <div className="flex gap-2">
                    <button
                        onClick={handleRunMigration}
                        disabled={isOrchestrationRunning || isReadOnly}
                        className={`px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-xl transition-all active:scale-95 ${isOrchestrationRunning || isReadOnly
                            ? "bg-gray-100 text-gray-400 cursor-not-allowed active:scale-100"
                            : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20 dark:shadow-none"
                            }`}
                    >
                        <Play size={12} className={isOrchestrationRunning ? "animate-spin" : ""} />
                        {isOrchestrationRunning ? "Running..." : "Run Pipeline"}
                    </button>

                    {isOrchestrationRunning && (
                        <button
                            onClick={handleCancelMigration}
                            className="px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white shadow-xl shadow-red-600/20 dark:shadow-none transition-all active:scale-95"
                        >
                            <X size={12} />
                            Cancel
                        </button>
                    )}
                </div>
            </StageHeader>

            {/* Main Content Area - Sprint 14: Sidebar managed at workspace level */}
            <div className="flex-1 overflow-hidden p-6">
                {/* Logs Section */}
                {activeSection === "logs" && (
                        <div className="h-full max-w-7xl mx-auto">
                            <ProcessProgress
                                isRunning={isOrchestrationRunning}
                                logs={logs}
                                processName="Drafting Pipeline"
                            />
                        </div>
                    )}

                    {/* Code Section */}
                    {activeSection === "code" && (
                        <div className="h-full">
                            <CodeViewer projectId={projectId} showHeader={false} />
                        </div>
                    )}

                    {/* Schema Section */}
                    {activeSection === "schema" && (
                        <div className="h-full">
                            <SchemaViewer projectId={projectId} showHistory={true} />
                        </div>
                    )}

                    {/* Performance Section */}
                    {activeSection === "performance" && (
                        <div className="h-full">
                            <PerformanceDashboard projectId={projectId} />
                        </div>
                    )}

                    {/* Quality Section */}
                    {activeSection === "quality" && (
                        <div className="h-full">
                            <QualityDashboard projectId={projectId} compact={false} />
                        </div>
                    )}

                    {/* Files/Output Explorer Section */}
                    {activeSection === "files" && (
                        <FileManagerTab projectId={projectId} activeTenantId={activeTenantId} />
                    )}

                    {/* Design Registry Section */}
                    {activeSection === "registry" && (
                        <DesignRegistryPanel projectId={projectId} />
                    )}

                    {/* Technology Mixer Section */}
                    {activeSection === "mixer" && (
                        <TechnologyMixer projectId={projectId} />
                    )}

                    {/* Settings Section */}
                    {activeSection === "settings" && (
                        <ProjectSettingsPanel projectId={projectId} />
                    )}

                    {/* Prompts Section */}
                    {activeSection === "prompts" && (
                        <PromptsExplorer />
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
        </div>
    );
}

// --- Tab 3: File Explorer with Preview ---

function FileManagerTab({ projectId, activeTenantId }: { projectId: string; activeTenantId?: string }) {
    const [tree, setTree] = useState<FileNode | null>(null);
    const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
    const [fileContent, setFileContent] = useState<string>("");
    const [loadingContent, setLoadingContent] = useState(false);

    // UI Logic for Resizing and Toggling
    const [isTreeVisible, setIsTreeVisible] = useState(true);
    const [treeWidth, setTreeWidth] = useState(300); // px
    const isResizing = useRef(false);

    // Persist tree width & visibility
    useEffect(() => {
        const saved = localStorage.getItem(`tree-width-${projectId}`);
        if (saved) setTreeWidth(parseInt(saved));
        const visible = localStorage.getItem(`tree-visible-${projectId}`);
        if (visible !== null) setIsTreeVisible(visible === 'true');
    }, [projectId]);

    const handleToggleTree = () => {
        const next = !isTreeVisible;
        setIsTreeVisible(next);
        localStorage.setItem(`tree-visible-${projectId}`, String(next));
    };

    const startResizing = useCallback((e: React.MouseEvent) => {
        isResizing.current = true;
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', stopResizing);
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        document.body.classList.add('resizing');
    }, []);

    const stopResizing = useCallback(() => {
        isResizing.current = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', stopResizing);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.body.classList.remove('resizing');
        localStorage.setItem(`tree-width-${projectId}`, String(treeWidth));
    }, [projectId, treeWidth]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizing.current) return;
        const container = document.getElementById('file-explorer-container');
        if (container) {
            const rect = container.getBoundingClientRect();
            const newWidth = e.clientX - rect.left;
            if (newWidth > 150 && newWidth < 800) {
                setTreeWidth(newWidth);
            }
        }
    }, [projectId]);

    const loadFiles = async () => {
        try {
            const res = await fetchWithAuth(`projects/${projectId}/files`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const data = await res.json();
            setTree(data);
        } catch (e) {
            console.error("Files error", e);
        }
    };

    const handleFileSelect = async (node: FileNode) => {
        if (node.type !== "file") return;

        setSelectedFile(node);
        setLoadingContent(true);
        setFileContent("");

        try {
            // Encode path to handle slashes correctly
            const res = await fetchWithAuth(`projects/${projectId}/files/content?path=${encodeURIComponent(node.path)}`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const data = await res.json();
            if (data.content !== undefined) {
                setFileContent(data.content);
            } else {
                setFileContent(`Error loading file: ${data.error}`);
            }
        } catch (e) {
            setFileContent(`Network error: ${e}`);
        } finally {
            setLoadingContent(false);
        }
    };

    useEffect(() => {
        loadFiles();
    }, [projectId]);

    return (
        <div id="file-explorer-container" className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Toolbar */}
            <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900 shrink-0">
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleToggleTree}
                        className={`p-1.5 rounded-lg transition-all ${isTreeVisible ? "bg-blue-500/10 text-blue-500 border border-blue-500/20 shadow-sm" : "text-gray-400 hover:text-white border border-transparent hover:bg-gray-800"}`}
                        title={isTreeVisible ? "Hide Library" : "Show Library"}
                    >
                        {isTreeVisible ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
                    </button>
                    <span className="font-bold text-sm flex items-center gap-2 text-gray-700 dark:text-gray-200"><Folder size={16} className="text-blue-500" /> Solution Output</span>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={loadFiles} className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-all" title="Refresh Files"><RefreshCw size={14} /></button>
                </div>
            </div>

            {/* Split Pane Content */}
            <div className="flex-1 flex overflow-hidden relative">
                {/* Left Pane: File Tree */}
                {isTreeVisible && (
                    <div
                        className="border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-2 bg-gray-50/50 dark:bg-gray-900/50 shrink-0"
                        style={{ width: `${treeWidth}px` }}
                    >
                        {tree ? (
                            <div className="space-y-1">
                                <FileTree
                                    node={tree}
                                    level={0}
                                    onSelect={handleFileSelect}
                                    selectedPath={selectedFile?.path}
                                />
                            </div>
                        ) : (
                            <div className="text-center p-4 text-gray-400">Loading files...</div>
                        )}

                        {tree && tree.children?.length === 0 && (
                            <div className="text-center p-10 text-gray-400">
                                <Folder className="mx-auto mb-2 opacity-50" size={32} />
                                <p className="text-sm">Empty Output</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Resize Handle */}
                {isTreeVisible && (
                    <div
                        onMouseDown={startResizing}
                        className="w-1.5 bg-transparent hover:bg-blue-500/30 cursor-col-resize transition-all z-20 absolute top-0 bottom-0 select-none group"
                        style={{ left: `${treeWidth}px`, marginLeft: '-3px' }}
                    >
                        <div className="absolute inset-y-0 left-1/2 w-0.5 bg-gray-200 dark:bg-gray-700 group-hover:bg-blue-500 transition-colors opacity-0 group-hover:opacity-100" />
                    </div>
                )}

                {/* Right Pane: Code Preview (flex-1 covers remaining) */}
                <div className="flex-1 bg-white dark:bg-gray-950 overflow-hidden flex flex-col min-w-0">
                    {selectedFile ? (
                        <>
                            <div className="p-2 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 text-xs font-mono text-gray-500 flex justify-between shrink-0">
                                <span>{selectedFile.name}</span>
                                {selectedFile.last_modified && (
                                    <span>Generated: {new Date(selectedFile.last_modified * 1000).toLocaleString()}</span>
                                )}
                            </div>
                            <div className="flex-1 overflow-auto custom-scrollbar min-h-0">
                                {loadingContent ? (
                                    <div className="flex items-center justify-center h-full text-gray-400 gap-2">
                                        <RefreshCw size={16} className="animate-spin" /> Loading content...
                                    </div>
                                ) : (
                                    <div className="min-w-max">
                                        <SyntaxHighlighter
                                            language={selectedFile.name.endsWith('.py') ? 'python' : selectedFile.name.endsWith('.sql') ? 'sql' : selectedFile.name.endsWith('.json') ? 'json' : selectedFile.name.endsWith('.md') ? 'markdown' : 'text'}
                                            style={vscDarkPlus}
                                            customStyle={{ margin: 0, padding: '1.5rem', background: '#0a0a0a', fontSize: '13px', lineHeight: '1.5', maxWidth: '100%' }}
                                            showLineNumbers={true}
                                            wrapLines={false}
                                        >
                                            {fileContent}
                                        </SyntaxHighlighter>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                            <FileCode size={48} className="mb-4 opacity-20" />
                            <p>Select a file to view content</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function FileTree({ node, level, onSelect, selectedPath }: { node: FileNode, level: number, onSelect: (n: FileNode) => void, selectedPath?: string }) {
    const [isOpen, setIsOpen] = useState(level < 2); // Default open top levels
    const isFolder = node.type === "folder";
    const isSelected = node.path === selectedPath;

    // Helper text for date in list (optional, might be too crowded in 30% view, maybe just show on hover or only in preview header)
    // User asked for "date next to file". Let's try to fit it or use a smaller font.

    return (
        <div className="ml-2">
            <div
                className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer text-sm transition-colors group justify-between ${isSelected
                    ? "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300"
                    : "hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                    }`}
                onClick={(e) => {
                    e.stopPropagation();
                    if (isFolder) setIsOpen(!isOpen);
                    else onSelect(node);
                }}
            >
                <div className="flex items-center gap-2 truncate">
                    <span className="text-gray-400 shrink-0">
                        {isFolder ? (isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <span className="w-3.5" />}
                    </span>
                    {isFolder ? <Folder size={14} className="text-blue-500 shrink-0" /> : <FileCode size={14} className="text-orange-500 shrink-0" />}
                    <span className="truncate">{node.name}</span>
                </div>

                {/* Date Display (Compact) */}
                {!isFolder && node.last_modified && (
                    <span className="text-[10px] text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap hidden xl:block">
                        {new Date(node.last_modified * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                )}
            </div>

            {isFolder && isOpen && node.children && (
                <div className="border-l border-gray-200 dark:border-gray-700 ml-3 pl-1">
                    {node.children.map((child, i) => (
                        <FileTree
                            key={i}
                            node={child}
                            level={level + 1}
                            onSelect={onSelect}
                            selectedPath={selectedPath}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
