"use client";
import React, { useState, useEffect, useCallback } from 'react';
import { Play, FileText, Database, GitBranch, Terminal, Layers, CheckCircle, Search, FolderOpen, ChevronRight, ChevronDown, FileCode, Folder, Settings, Brain, Bot, RefreshCw, ArrowRight, Maximize2, Minimize2, RotateCcw, X } from 'lucide-react';
import StageHeader from "../StageHeader";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { fetchWithAuth } from '../../lib/auth-client';
import CodeDiffViewer from '../CodeDiffViewer';
import PromptsExplorer from '../PromptsExplorer';
import DesignRegistryPanel from './DesignRegistryPanel';
import TechnologyMixer from './TechnologyMixer';

interface RefinementViewProps {
    projectId: string;
    onStageChange?: (stage: number) => void;
    isReadOnly?: boolean;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void;
}

interface FileNode {
    name: string;
    path: string;
    type: "file" | "folder";
    children?: FileNode[];
    last_modified?: string | number;
}

const TABS = [
    { id: 'orchestrator', label: 'Orchestration', icon: <Layers size={18} /> },
    { id: 'workbench', label: 'Workbench (Diff)', icon: <GitBranch size={18} /> },
    { id: 'artifacts', label: 'Artifacts', icon: <Database size={18} /> },
];

export default function RefinementView({
    projectId,
    onStageChange,
    isReadOnly,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent
}: RefinementViewProps) {
    const [activeTab, setActiveTab] = useState<any>("orchestrator");
    const [isRunning, setIsRunning] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [profile, setProfile] = useState<any>(null);

    // Workbench State
    const [fileTree, setFileTree] = useState<any[]>([]);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [fileContent, setFileContent] = useState<string>("");
    const [originalContent, setOriginalContent] = useState<string>("");
    const [isLoadingFile, setIsLoadingFile] = useState(false);
    const [isFinished, setIsFinished] = useState(false);

    // State Restoration on Mount
    useEffect(() => {
        const fetchState = async () => {
            try {
                const res = await fetchWithAuth(`projects/${projectId}/refinement/state`);
                const data = await res.json();

                if (data.log && data.log.length > 0) {
                    setLogs(data.log);
                }
                if (data.profile) {
                    setProfile(data.profile);
                }
            } catch (e) {
                console.error("Failed to restore state", e);
            }
        };
        fetchState();
    }, [projectId]);

    const fetchRefinementLogs = useCallback(async () => {
        try {
            const res = await fetchWithAuth(`projects/${projectId}/logs?type=refinement`);
            const data = await res.json();
            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");
                setLogs(logLines);
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    }, [projectId]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRunning) {
            interval = setInterval(fetchRefinementLogs, 2000);
        }
        return () => clearInterval(interval);
    }, [isRunning, fetchRefinementLogs]);

    useEffect(() => {
        fetchRefinementLogs();
    }, [fetchRefinementLogs]);


    const handleRunRefinement = async () => {
        const confirmMsg = "This action will execute the Refinement phase (Agents P, A, R, O). This incurs token costs and processing time.\n\nDo you want to continue?";
        if (!confirm(confirmMsg)) return;

        setIsRunning(true);
        setIsFinished(false);
        setLogs(["Starting Refinement Phase...", "Initializing Agents..."]);
        try {
            const res = await fetchWithAuth(`refine/start`, {
                method: 'POST',
                body: JSON.stringify({ project_id: projectId })
            });
            const data = await res.json();

            if (data.log) {
                setLogs(data.log);
            }
            if (data.profile) {
                setProfile(data.profile);
            }
        } catch (e) {
            setLogs(prev => [...prev, `[Network Error] ${e}`]);
        } finally {
            setIsRunning(false);
            fetchRefinementLogs();
        }
    };

    const handleApprove = async () => {
        if (!confirm("Are you sure you want to approve the refinement phase and move the project to Governance?")) return;
        try {
            const res = await fetchWithAuth(`projects/${projectId}/stage`, {
                method: "POST",
                body: JSON.stringify({ stage: "5" })
            });
            const data = await res.json();
            if (data.success && onStageChange) {
                onStageChange(5);
            }
        } catch (e) {
            alert("Failed to approve stage.");
        }
    };

    const handleCancelRefinement = async () => {
        if (!window.confirm("¿Estás seguro de que deseas cancelar el proceso de refinamiento?")) return;

        try {
            const res = await fetchWithAuth(`projects/${projectId}/cancel`, {
                method: "POST"
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

    useEffect(() => {
        if (activeTab === 'workbench' || activeTab === 'artifacts') {
            fetchWithAuth(`projects/${projectId}/files`)
                .then(res => res.json())
                .then(data => setFileTree(data.children || []))
                .catch(err => console.error("Failed to load file tree", err));
        }
    }, [activeTab, projectId, logs]);

    const findLegacyFile = (nodes: any[], targetBaseName: string): string | null => {
        for (const node of nodes) {
            if (node.type === "file") {
                if (node.path.includes("Triage")) {
                    const nodeBase = node.name.replace(/\.[^/.]+$/, "");
                    if (nodeBase.toLowerCase() === targetBaseName.toLowerCase()) {
                        return node.path;
                    }
                }
            } else if (node.children) {
                const found = findLegacyFile(node.children, targetBaseName);
                if (found) return found;
            }
        }
        return null;
    };

    const resolveOriginalPath = (refinedPath: string) => {
        if (!refinedPath.includes('Refinement')) return null;
        let filename = refinedPath.split(/[\\/]/).pop() || "";
        const baseName = filename
            .replace(/_bronze\..*$/, "")
            .replace(/_silver\..*$/, "")
            .replace(/_gold\..*$/, "")
            .replace(/\..*$/, "");
        return findLegacyFile(fileTree, baseName);
    };

    const handleFileSelect = async (path: string) => {
        setSelectedFile(path);
        setIsLoadingFile(true);
        setFileContent("");
        setOriginalContent("");

        try {
            const res = await fetchWithAuth(`projects/${projectId}/files/content?path=${encodeURIComponent(path)}`);
            const data = await res.json();
            setFileContent(data.content || "");

            if (activeTab === 'workbench') {
                const origPath = resolveOriginalPath(path);
                if (origPath) {
                    const resOrig = await fetchWithAuth(`projects/${projectId}/files/content?path=${encodeURIComponent(origPath)}`);
                    const dataOrig = await resOrig.json();
                    setOriginalContent(dataOrig.content || "-- Original file not found --");
                }
            }
        } catch (e) {
            console.error("Failed to load file content", e);
            setFileContent("// Failed to load content");
        } finally {
            setIsLoadingFile(false);
        }
    };

    const FileTreeSection = ({ node, level, onSelect, selectedPath }: { node: FileNode, level: number, onSelect: (n: FileNode) => void, selectedPath?: string }) => {
        const [isOpen, setIsOpen] = useState(level < 2);
        const isFolder = node.type === "folder" || (node.children && node.children.length > 0);
        const isSelected = node.path === selectedPath;

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
                        <span className="truncate">
                            {node.name}
                            {!isFolder && node.last_modified && (
                                <span className="ml-2 text-[10px] text-gray-400 font-mono">
                                    ({new Date(typeof node.last_modified === 'number' ? node.last_modified * 1000 : node.last_modified).toLocaleString([], { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })})
                                </span>
                            )}
                        </span>
                    </div>
                </div>

                {isFolder && isOpen && node.children && (
                    <div className="border-l border-gray-200 dark:border-gray-700 ml-3 pl-1">
                        {node.children.map((child, i) => (
                            <FileTreeSection
                                key={i}
                                node={child}
                                level={level + 1}
                                onSelect={onSelect}
                                selectedPath={selectedFile || undefined}
                            />
                        ))}
                    </div>
                )}
            </div>
        );
    };

    const isComplete = isFinished || logs.some(l =>
        l.toUpperCase().includes("PIPELINE COMPLETE") ||
        l.toUpperCase().includes("COMPLETED") ||
        l.toUpperCase().includes("SUCCESS")
    );

    useEffect(() => {
        if (!isFinished && logs.some(l => l.toUpperCase().includes("PIPELINE COMPLETE") || l.toUpperCase().includes("COMPLETED"))) {
            setIsFinished(true);
        }
    }, [logs, isFinished]);

    return (
        <div className="flex flex-col h-full bg-[var(--background)]">
            <StageHeader
                title="Stage 4: Intelligent Refinement"
                subtitle="Agent F: Quality enforcement and pattern optimization"
                icon={<GitBranch className="text-purple-500" />}
                helpText="Final code refinement ensuring adherence to established architectural patterns."
                onApprove={handleApprove}
                approveLabel="Approve & Governance"
                isApproveDisabled={isRunning || !isComplete}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            >
                <div className="flex gap-2">
                    <button
                        onClick={handleRunRefinement}
                        disabled={isRunning || isReadOnly}
                        className={`px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-xl transition-all ${isRunning || isReadOnly
                            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                            : "bg-purple-600 hover:bg-purple-500 text-white shadow-purple-600/20 dark:shadow-none"
                            }`}
                    >
                        <Play size={12} className={isRunning ? "animate-spin" : ""} />
                        {isRunning ? "Refining..." : "Refine & Modernize"}
                    </button>

                    {isRunning && (
                        <button
                            onClick={handleCancelRefinement}
                            className="px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white shadow-xl shadow-red-600/20 dark:shadow-none transition-all active:scale-95"
                        >
                            <X size={12} />
                            Cancel
                        </button>
                    )}
                </div>
            </StageHeader>

            <div className="flex bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 px-4">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-8 py-5 text-[10px] font-bold uppercase tracking-[0.2em] border-b-2 transition-all ${activeTab === tab.id
                            ? 'border-purple-500 text-purple-500 bg-purple-500/5'
                            : 'border-transparent text-[var(--text-tertiary)] hover:text-purple-500 hover:bg-purple-500/5'
                            }`}
                    >
                        {tab.icon} <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            <div className="flex-1 p-8 overflow-hidden">
                {activeTab === 'orchestrator' && (
                    <div className="max-w-7xl mx-auto space-y-6 flex flex-col h-full">
                        <div className="flex-1 bg-black text-green-400 rounded-xl p-6 font-mono text-sm overflow-y-auto shadow-inner border border-gray-800 min-h-0">
                            <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                                <span className="font-bold text-gray-400">AGENT LOGS</span>
                            </div>
                            <div className="space-y-2">
                                {logs.length === 0 && <span className="text-gray-600 italic">Waiting for command...</span>}
                                {logs.map((line: string, i: number) => (
                                    <div key={i} className="whitespace-pre-wrap border-l-2 border-transparent pl-2 hover:border-gray-700 transition-colors">{`> ${line}`}</div>
                                ))}
                            </div>
                        </div>

                        {profile && (
                            <div className="grid grid-cols-2 gap-4 shrink-0">
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 shadow-sm">
                                    <h3 className="font-bold text-gray-500 text-xs uppercase mb-2">Files Analyzed</h3>
                                    <p className="text-2xl font-bold text-purple-500">{profile.total_files}</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 shadow-sm">
                                    <h3 className="font-bold text-gray-500 text-xs uppercase mb-2">Shared Connections</h3>
                                    <p className="text-2xl font-bold text-orange-500">{Object.keys(profile.shared_connections || {}).length}</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {(activeTab === 'workbench' || activeTab === 'artifacts') && (
                    <div className="flex h-full gap-4">
                        <div className="w-1/4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center">
                                <h3 className="font-bold text-sm uppercase text-gray-400">{activeTab === 'workbench' ? 'Files to Review' : 'Artifacts Explorer'}</h3>
                                <button className="text-gray-400 hover:text-primary"><Search size={14} /></button>
                            </div>
                            <div className="flex-1 overflow-y-auto p-2">
                                {fileTree.length === 0 ? (
                                    <p className="text-gray-400 text-sm text-center mt-10">No files generated yet.</p>
                                ) : (
                                    <div className="space-y-1">
                                        {fileTree.map((child, i) => (
                                            <FileTreeSection
                                                key={i}
                                                node={child}
                                                level={0}
                                                onSelect={(n) => handleFileSelect(n.path)}
                                                selectedPath={selectedFile || undefined}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden shadow-lg">
                            <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50">
                                <h3 className="font-bold text-sm flex items-center gap-2">
                                    <FileText size={16} className="text-purple-500" />
                                    {selectedFile ? (
                                        <span>
                                            {selectedFile.split(/[\\/]/).pop()}
                                            {selectedFile.includes("Bronze") && <span className="ml-2 text-[10px] bg-orange-100 text-orange-800 px-1 rounded border border-orange-200">BRONZE</span>}
                                            {selectedFile.includes("Silver") && <span className="ml-2 text-[10px] bg-gray-100 text-gray-800 px-1 rounded border border-gray-200">SILVER</span>}
                                            {selectedFile.includes("Gold") && <span className="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1 rounded border border-yellow-200">GOLD</span>}
                                        </span>
                                    ) : "Select a file"}
                                </h3>
                                {selectedFile && <span className="text-xs text-gray-400 font-mono truncate max-w-[300px]">{selectedFile}</span>}
                            </div>

                            <div className="flex-1 overflow-auto relative">
                                {isLoadingFile ? (
                                    <div className="flex items-center justify-center h-full text-gray-500">Loading content...</div>
                                ) : selectedFile ? (
                                    activeTab === 'workbench' ? (
                                        <div className="flex flex-col h-full">
                                            <div className="flex justify-between px-4 py-2 bg-gray-100 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 text-xs font-bold text-gray-500 uppercase">
                                                <span>Original (Legacy Source)</span>
                                                <span>Refined (Generated Code)</span>
                                            </div>
                                            <div className="flex-1 min-h-0">
                                                <CodeDiffViewer originalCode={originalContent} modifiedCode={fileContent} />
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex-1 overflow-auto bg-[#1e1e1e]">
                                            <SyntaxHighlighter
                                                language={selectedFile.endsWith('.py') ? 'python' : selectedFile.endsWith('.sql') ? 'sql' : selectedFile.endsWith('.json') ? 'json' : selectedFile.endsWith('.md') ? 'markdown' : 'text'}
                                                style={vscDarkPlus}
                                                customStyle={{ margin: 0, padding: '1.5rem', background: 'transparent', fontSize: '13px', lineHeight: '1.5' }}
                                                showLineNumbers={true}
                                                wrapLines={true}
                                            >
                                                {fileContent}
                                            </SyntaxHighlighter>
                                        </div>
                                    )
                                ) : (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-4">
                                        <Layers size={48} className="text-gray-700" />
                                        <p>Select a file to inspect generated code.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
