import { useState, useEffect, useCallback, useRef } from "react";
import { Play, FileText, Folder, CheckCircle, Terminal, RefreshCw, FolderOpen, FileCode, Lock, ChevronRight, ChevronDown, Settings, Brain, Code, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import { fetchWithAuth } from "../../lib/auth-client";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import PromptsExplorer from "../PromptsExplorer";
import DesignRegistryPanel from "./DesignRegistryPanel";
import TechnologyMixer from "./TechnologyMixer";
import ProjectSettingsPanel from "./ProjectSettingsPanel";

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
    onBackToCurrent
}: DraftingViewProps) {
    const [activeTab, setActiveTab] = useState<"execution" | "files" | "config">("execution");
    const [isRunning, setIsRunning] = useState(false);
    const [logs, setLogs] = useState<string[]>([]); // Simple log stream simulation
    const [progress, setProgress] = useState(0);
    const [migrationLimit, setMigrationLimit] = useState(0); // [NEW] Batch Limit control
    const [isApproving, setIsApproving] = useState(false);

    // Helper: Fetch Logs
    const fetchLogs = async () => {
        try {
            // Release 3.5: Switch to robust DB-backed execution logs
            const res = await fetchWithAuth(`projects/${projectId}/execution-logs?type=migration`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });
            const data = await res.json();
            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");
                setLogs(logLines);

                // Check for completion
                if (data.logs.includes("Migration Complete.")) {
                    setProgress(100);
                    if (onCompletion && !isRunning) onCompletion(true); // Only trigger if not currently running to avoid races
                }
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    };

    // Load base data on mount
    useEffect(() => {
        fetchLogs();

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
    }, [projectId]);

    // Poll logs when running
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRunning) {
            interval = setInterval(fetchLogs, 2000);
        }
        return () => clearInterval(interval);
    }, [isRunning, projectId]);

    // --- Tab 1: Execution Handlers ---
    const handleRunMigration = async () => {
        // Confirmation for cost
        const confirmMsg = "Esta acción ejecutará la migración completa (Agentes A, B, C, F, G). Esto incurre en costos de tokens y tiempo de procesamiento.\n\n¿Deseas continuar?";
        if (!window.confirm(confirmMsg)) return;

        setIsRunning(true);
        // Initial feedback
        setLogs(["Creating Migration Orchestrator...", "Validating Governance Status: DRAFTING... OK"]);
        setProgress(10);

        try {
            const res = await fetchWithAuth("transpile/orchestrate", {
                method: "POST",
                headers: {
                    ...(activeTenantId ? { "X-Tenant-ID": activeTenantId } : {})
                },
                body: JSON.stringify({ project_id: projectId, limit: migrationLimit }) // Dynamic limit from state
            });
            const data = await res.json();

            if (data.error) {
                setLogs(prev => [...prev, `[ERROR] ${data.error}`]);
            } else {
                // Success: Do one final log fetch to ensure we have the latest
                await fetchLogs();
                setProgress(100);
                if (onCompletion) onCompletion(true);
            }
        } catch (e) {
            setLogs(prev => [...prev, `[Network Error] ${e}`]);
        } finally {
            setIsRunning(false);
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
                setLogs(prev => [...prev, `[ERROR] Failed to cancel: ${data.error || 'Unknown error'}`]);
            }
        } catch (e) {
            console.error("Failed to cancel process", e);
            setLogs(prev => [...prev, `[ERROR] Network error during cancellation: ${e}`]);
        }
    };


    return (
        <div className="flex flex-col h-full bg-[var(--background)]">
            <StageHeader
                title="Stage 3: Cloud Drafting"
                subtitle="Agent C: Cloud-native Medallion code generator"
                icon={<Code className="text-emerald-500" />}
                helpText="Generation of optimized PySpark, dbt or Snowflake code based on the approved design."
                onApprove={handleApprove}
                approveLabel="Finalize & Refine"
                isApproveDisabled={isRunning || progress < 100}
                isExecuting={isApproving}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            >
                <div className="flex gap-2">
                    <button
                        onClick={handleRunMigration}
                        disabled={isRunning || isReadOnly}
                        className={`px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-xl transition-all active:scale-95 ${isRunning || isReadOnly
                            ? "bg-gray-100 text-gray-400 cursor-not-allowed active:scale-100"
                            : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20 dark:shadow-none"
                            }`}
                    >
                        <Play size={12} className={isRunning ? "animate-spin" : ""} />
                        {isRunning ? "Running..." : "Run Pipeline"}
                    </button>

                    {isRunning && (
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

            {/* Tab Navigation Area */}
            <div className="flex bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 px-4">
                <TabButton
                    active={activeTab === "execution"}
                    onClick={() => setActiveTab("execution")}
                    icon={<Terminal size={16} />}
                    label="Orchestration"
                />
                <TabButton
                    active={activeTab === "files"}
                    onClick={() => setActiveTab("files")}
                    icon={<FolderOpen size={16} />}
                    label="Output Explorer"
                />

            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden p-6">
                {activeTab === "execution" && (
                    <ExecutionTab
                        isRunning={isRunning}
                        logs={logs}
                        progress={progress}
                        limit={migrationLimit}
                        setLimit={setMigrationLimit}
                    />
                )}
                {activeTab === "files" && <FileManagerTab projectId={projectId} activeTenantId={activeTenantId} />}
            </div>
        </div >
    );
}

// --- Sub-Components ---

function TabButton({ active, onClick, icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-8 py-5 text-[10px] font-bold uppercase tracking-[0.2em] border-b-2 transition-all ${active
                ? "border-emerald-500 text-emerald-500 bg-emerald-500/5"
                : "border-transparent text-[var(--text-tertiary)] hover:text-emerald-500 hover:bg-emerald-500/5"
                }`}
        >
            {icon} {label}
        </button>
    );
}

function ExecutionTab({ isRunning, logs, progress, limit }: any) {
    return (
        <div className="h-full flex flex-col gap-6 max-w-7xl mx-auto">
            {/* Control Panel: Shows current persistence status */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 flex justify-between items-center gap-8">
                <div className="flex-1">
                    <h2 className="text-xl font-bold flex items-center gap-2"><Play className="text-emerald-500" /> Start Migration</h2>
                    <p className="text-[var(--text-secondary)] text-sm mt-1">Execute the full pipeline: Librarian → Topology → Developer → Compliance.</p>
                </div>

                <div className="flex items-center gap-4 bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                    <div className="text-right">
                        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block">Persistent Batch Limit</label>
                        <span className="text-lg font-mono font-bold text-emerald-500">{limit === 0 ? "UNLIMITED" : limit}</span>
                    </div>
                    <div className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
                        <Lock size={16} className="text-gray-400" />
                    </div>
                </div>
            </div>

            {/* Console Output */}
            <div className="flex-1 bg-black text-green-400 rounded-xl p-4 font-mono text-sm overflow-y-auto shadow-inner border border-gray-800">
                <div className="flex justify-between items-center mb-2 border-b border-gray-800 pb-2">
                    <span className="font-bold text-gray-400">CONSOLE OUTPUT</span>
                    {isRunning && <RefreshCw size={14} className="animate-spin" />}
                </div>
                <div className="space-y-1">
                    {logs.length === 0 && <span className="text-gray-600 italic">Waiting for execution...</span>}
                    {logs.map((line: string, i: number) => (
                        <div key={i} className="whitespace-pre-wrap">{`> ${line}`}</div>
                    ))}
                </div>
            </div>
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
        <div id="file-explorer-container" className="h-full bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
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
                <div className="flex-1 bg-white dark:bg-gray-950 overflow-hidden flex flex-col">
                    {selectedFile ? (
                        <>
                            <div className="p-2 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 text-xs font-mono text-gray-500 flex justify-between">
                                <span>{selectedFile.name}</span>
                                {selectedFile.last_modified && (
                                    <span>Generated: {new Date(selectedFile.last_modified * 1000).toLocaleString()}</span>
                                )}
                            </div>
                            <div className="flex-1 overflow-auto p-4 custom-scrollbar">
                                {loadingContent ? (
                                    <div className="flex items-center justify-center h-full text-gray-400 gap-2">
                                        <RefreshCw size={16} className="animate-spin" /> Loading content...
                                    </div>
                                ) : (
                                    <SyntaxHighlighter
                                        language={selectedFile.name.endsWith('.py') ? 'python' : selectedFile.name.endsWith('.sql') ? 'sql' : selectedFile.name.endsWith('.json') ? 'json' : selectedFile.name.endsWith('.md') ? 'markdown' : 'text'}
                                        style={vscDarkPlus}
                                        customStyle={{ margin: 0, padding: '1.5rem', background: '#0a0a0a', fontSize: '13px', lineHeight: '1.5', minHeight: '100%' }}
                                        showLineNumbers={true}
                                        wrapLines={true}
                                    >
                                        {fileContent}
                                    </SyntaxHighlighter>
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
