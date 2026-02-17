"use client";
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Play, FileText, Database, Terminal, Layers, CheckCircle, Search, FolderOpen, ChevronRight, ChevronDown, FileCode, Folder, Settings, Brain, Bot, RefreshCw, ArrowRight, Maximize2, Minimize2, RotateCcw, X, Code, Shield, Zap } from 'lucide-react';
import StageHeader from "../StageHeader";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { fetchWithAuth } from '../../lib/auth-client';
import ProcessProgress from '../ProcessProgress';
import PromptsExplorer from '../PromptsExplorer';
import DesignRegistryPanel from './DesignRegistryPanel';
import TechnologyMixer from './TechnologyMixer';
import CodeViewer from '../visualization/CodeViewer'; // V3.9
import SchemaViewer from '../visualization/SchemaViewer'; // V3.9
import QualityDashboard from '../visualization/QualityDashboard'; // V3.9
import PerformanceDashboard from '../visualization/PerformanceDashboard'; // V3.9

interface RefinementViewProps {
    projectId: string;
    onStageChange?: (stage: number) => void;
    isReadOnly?: boolean;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void;    activeSection: string;
    onSectionChange: (section: string) => void;}

interface FileNode {
    name: string;
    path: string;
    type: "file" | "folder";
    children?: FileNode[];
    last_modified?: string | number;
}

export default function RefinementView({
    projectId,
    onStageChange,
    isReadOnly,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent,
    activeSection,
    onSectionChange
}: RefinementViewProps) {
    const [isInitialLoading, setIsInitialLoading] = useState(false); // Initial data fetch
    const [isRefinementRunning, setIsRefinementRunning] = useState(false); // Active refinement process
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
            // Fetch execution logs
            const res = await fetchWithAuth(`projects/${projectId}/execution-logs?type=refinement`);
            const data = await res.json();
            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");
                setLogs(logLines);
            }

            // Check project status to detect completion
            const statusRes = await fetchWithAuth(`discovery/status/${projectId}`);
            const statusData = await statusRes.json();
            
            // If status is REFINED and we're currently running, process is complete
            if (statusData.status === "REFINED" && isRefinementRunning) {
                console.log("[RefinementView] Refinement complete, stopping polling");
                setIsRefinementRunning(false);
                // Profile will be reloaded in separate useEffect
            }
        } catch (e) {
            console.error("Failed to load refinement logs", e);
        }
    }, [projectId, isRefinementRunning]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRefinementRunning) {
            // Immediate fetch
            fetchRefinementLogs();
            // Then poll every 3 seconds
            interval = setInterval(fetchRefinementLogs, 3000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [isRefinementRunning, fetchRefinementLogs]);

    // Reload profile data when refinement completes (separate useEffect to avoid loops)
    const prevRefinementRunning = useRef(false);
    useEffect(() => {
        const reloadProfileData = async () => {
            try {
                const stateRes = await fetchWithAuth(`projects/${projectId}/refinement/state`);
                const stateData = await stateRes.json();
                if (stateData.profile) {
                    setProfile(stateData.profile);
                }
            } catch (e) {
                console.error("Failed to reload profile", e);
            }
        };

        if (prevRefinementRunning.current === true && isRefinementRunning === false) {
            console.log("[RefinementView] Refinement completed, reloading profile data");
            reloadProfileData();
        }
        prevRefinementRunning.current = isRefinementRunning;
    }, [isRefinementRunning, projectId]);

    useEffect(() => {
        fetchRefinementLogs();
    }, [fetchRefinementLogs]);


    const handleRunRefinement = async () => {
        const confirmMsg = "This action will execute the Refinement phase (Agents P, A, R, O). This incurs token costs and processing time.\n\nDo you want to continue?";
        if (!confirm(confirmMsg)) return;

        setIsRefinementRunning(true);
        setIsFinished(false);
        setLogs(["Starting Refinement Phase in background..."]);
        try {
            const res = await fetchWithAuth(`refine/start`, {
                method: 'POST',
                body: JSON.stringify({ project_id: projectId })
            });
            const data = await res.json();

            if (data.error) {
                setLogs(prev => [...prev, `[ERROR] ${data.error}`]);
                setIsRefinementRunning(false);
            } else if (data.status === "RUNNING") {
                // Background task started successfully
                setLogs(prev => [...prev, data.message || "Refinement started in background. Monitor logs for progress."]);
                // Polling will continue until status changes to REFINED
            } else {
                // Backwards compatibility: old synchronous response
                if (data.log) {
                    setLogs(data.log);
                }
                if (data.profile) {
                    setProfile(data.profile);
                }
                setIsRefinementRunning(false);
            }
        } catch (e) {
            setLogs(prev => [...prev, `[Network Error] ${e}`]);
            setIsRefinementRunning(false);
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
                setIsRefinementRunning(false);
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
        if (activeSection === 'diff') {
            fetchWithAuth(`projects/${projectId}/files`)
                .then(res => res.json())
                .then(data => setFileTree(data.children || []))
                .catch(err => console.error("Failed to load file tree", err));
        }
    }, [activeSection, projectId, logs]);

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

            if (activeSection === 'diff') {
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
                subtitle="Compliance Auditor: Quality enforcement and pattern optimization"
                icon={<Layers className="text-purple-500" />}
                helpText="Final code refinement ensuring adherence to established architectural patterns."
                onApprove={handleApprove}
                approveLabel="Approve & Governance"
                isApproveDisabled={isRefinementRunning || !isComplete}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            >
                <div className="flex gap-2">
                    <button
                        onClick={handleRunRefinement}
                        disabled={isRefinementRunning || isReadOnly}
                        className={`px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-xl transition-all ${isRefinementRunning || isReadOnly
                            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                            : "bg-purple-600 hover:bg-purple-500 text-white shadow-purple-600/20 dark:shadow-none"
                            }`}
                    >
                        <Play size={12} className={isRefinementRunning ? "animate-spin" : ""} />
                        {isRefinementRunning ? "Refining..." : "Refine & Modernize"}
                    </button>

                    {isRefinementRunning && (
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

            {/* Main Content Area - Sprint 14: Sidebar managed at workspace level */}
            <div className="flex-1 overflow-hidden p-6">
                {activeSection === 'status' && (
                    <div className="max-w-7xl mx-auto space-y-6 flex flex-col h-full">
                        <ProcessProgress
                            isRunning={isRefinementRunning}
                            logs={logs}
                            processName="Refinement Pipeline"
                        />

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

                {activeSection === 'issues' && (
                    <div className="h-full bg-white dark:bg-gray-900 rounded-xl overflow-hidden">
                        <CodeViewer projectId={projectId} showHeader={true} />
                    </div>
                )}

                {activeSection === 'validation' && (
                    <div className="h-full bg-white dark:bg-gray-900 rounded-xl overflow-hidden">
                        <SchemaViewer projectId={projectId} showHistory={true} />
                    </div>
                )}

                {activeSection === 'quality' && (
                    <div className="h-full bg-white dark:bg-gray-900 rounded-xl overflow-hidden">
                        <QualityDashboard projectId={projectId} />
                    </div>
                )}

                {activeSection === 'performance' && (
                    <div className="h-full bg-white dark:bg-gray-900 rounded-xl overflow-hidden">
                        <PerformanceDashboard projectId={projectId} />
                    </div>
                )}

                {activeSection === 'diff' && (
                    <div className="flex h-full gap-4">
                        <div className="w-1/4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center">
                                <h3 className="font-bold text-sm uppercase text-gray-400">Artifacts Explorer</h3>
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
                                    <div className="flex-1 overflow-auto bg-[#1e1e1e]">
                                        <SyntaxHighlighter
                                                language={(() => {
                                                    if (selectedFile.endsWith('.py')) return 'python';
                                                    if (selectedFile.endsWith('.sql')) return 'sql';
                                                    if (selectedFile.endsWith('.json')) return 'json';
                                                    if (selectedFile.endsWith('.md')) return 'markdown';
                                                    return 'text';
                                                })()}
                                                style={vscDarkPlus}
                                                customStyle={{ margin: 0, padding: '1.5rem', background: 'transparent', fontSize: '13px', lineHeight: '1.5' }}
                                                showLineNumbers={true}
                                                wrapLines={true}
                                            >
                                                {fileContent}
                                            </SyntaxHighlighter>
                                        </div>
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
