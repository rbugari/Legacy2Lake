"use client";
import { useState, useEffect } from "react";
import { Play, FileText, Folder, CheckCircle, Terminal, RefreshCw, FolderOpen, FileCode, Lock, ChevronRight, ChevronDown } from "lucide-react";
import { API_BASE_URL } from "../../lib/config";
import PromptsExplorer from "../PromptsExplorer";

// --- Types ---
interface FileNode {
    name: string;
    path: string;
    type: "file" | "folder";
    children?: FileNode[];
    last_modified?: number;
}

interface DraftingViewProps {
    projectId: string;
    onStageChange: (stage: number) => void;
    onCompletion?: (completed: boolean) => void;
}

export default function DraftingView({ projectId, onStageChange, onCompletion }: DraftingViewProps) {
    const [activeTab, setActiveTab] = useState<"execution" | "prompts" | "files">("execution");
    const [isRunning, setIsRunning] = useState(false);
    const [logs, setLogs] = useState<string[]>([]); // Simple log stream simulation
    const [progress, setProgress] = useState(0);

    // Helper: Fetch Logs
    const fetchLogs = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/logs`);
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

    // Load logs on mount
    useEffect(() => {
        fetchLogs();
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
            const res = await fetch(`${API_BASE_URL}/transpile/orchestrate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ project_id: projectId, limit: 5 }) // Limit 5 for demo speed
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
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/stage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ stage: "3" })
            });
            const data = await res.json();
            if (data.success) {
                onStageChange(3);
            }
        } catch (e) {
            console.error("Failed to update stage", e);
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
            {/* Top Operational Bar (Toolbar) */}
            <div className="flex items-center justify-between px-4 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 shadow-sm z-10 transition-all">
                {/* Left: Tabs */}
                <div className="flex">
                    <TabButton
                        active={activeTab === "execution"}
                        onClick={() => setActiveTab("execution")}
                        icon={<Play size={16} />}
                        label="Orchestration"
                    />
                    <TabButton
                        active={activeTab === "prompts"}
                        onClick={() => setActiveTab("prompts")}
                        icon={<Terminal size={16} />}
                        label="Agent Prompts"
                    />
                    <TabButton
                        active={activeTab === "files"}
                        onClick={() => setActiveTab("files")}
                        icon={<FolderOpen size={16} />}
                        label="Output Explorer"
                    />
                </div>

                {/* Right: Operational Controls */}
                <div className="flex items-center gap-4">
                    {/* Group A: View/State Controls */}
                    <div className="flex items-center gap-1 bg-gray-50 dark:bg-gray-900 p-1 rounded-lg border border-gray-100 dark:border-gray-800">
                        <span className="text-[10px] uppercase font-bold text-gray-400 px-2 select-none">Pipeline Ops</span>
                    </div>

                    <div className="h-8 w-px bg-gray-200 dark:bg-gray-800" />

                    {/* Group B: Actions */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleRunMigration}
                            disabled={isRunning}
                            className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${isRunning
                                    ? "bg-gray-400 cursor-not-allowed"
                                    : "bg-primary hover:bg-primary/90 text-white shadow-blue-200 dark:shadow-none"
                                }`}
                        >
                            <Play size={14} className={isRunning ? "animate-spin" : ""} />
                            {isRunning ? "Running..." : "Execute Pipeline"}
                        </button>

                        {progress === 100 && (
                            <button
                                onClick={handleApprove}
                                className="px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all bg-green-600 hover:bg-green-700 text-white shadow-green-200 dark:shadow-none"
                            >
                                <CheckCircle size={14} /> Approve & Refine
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden p-6">
                {activeTab === "execution" && (
                    <ExecutionTab
                        isRunning={isRunning}
                        logs={logs}
                        progress={progress}
                    />
                )}
                {activeTab === "prompts" && <div className="h-full bg-white dark:bg-gray-950 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm"><PromptsExplorer /></div>}
                {activeTab === "files" && <FileManagerTab projectId={projectId} />}
            </div>
        </div>
    );
}

// --- Sub-Components ---

function TabButton({ active, onClick, icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${active
                ? "border-primary text-primary bg-primary/5"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                }`}
        >
            {icon} {label}
        </button>
    );
}

function ExecutionTab({ isRunning, logs, progress }: any) {
    return (
        <div className="h-full flex flex-col gap-6 max-w-4xl mx-auto">
            {/* Control Panel (Info Only now) */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold flex items-center gap-2"><Play className="text-primary" /> Start Migration</h2>
                    <p className="text-gray-500 text-sm mt-1">Execute the full pipeline: Librarian → Topology → Developer → Compliance.</p>
                </div>
                {/* Actions moved to Top Toolbar */}
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

function FileManagerTab({ projectId }: { projectId: string }) {
    const [tree, setTree] = useState<FileNode | null>(null);
    const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
    const [fileContent, setFileContent] = useState<string>("");
    const [loadingContent, setLoadingContent] = useState(false);

    const loadFiles = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/files`);
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
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/files/content?path=${encodeURIComponent(node.path)}`);
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
        <div className="h-full bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
            {/* Toolbar */}
            <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900 shrink-0">
                <span className="font-bold text-sm flex items-center gap-2"><Folder size={16} /> Solution Output</span>
                <button onClick={loadFiles} className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"><RefreshCw size={14} /></button>
            </div>

            {/* Split Pane Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Pane: File Tree (30%) */}
                <div className="w-[30%] border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-2 bg-gray-50/50 dark:bg-gray-900/50">
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

                {/* Right Pane: Code Preview (70%) */}
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
                                    <pre className="text-xs font-mono text-gray-800 dark:text-gray-300 whitespace-pre-wrap">
                                        {fileContent}
                                    </pre>
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
