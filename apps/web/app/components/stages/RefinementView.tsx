"use client";
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Play, FileText, Database, Terminal, Layers, CheckCircle, Search, FolderOpen, ChevronRight, ChevronDown, FileCode, Folder, Settings, Brain, Bot, RefreshCw, ArrowRight, Maximize2, Minimize2, RotateCcw, X, Code, Shield, Zap, AlertCircle, BarChart3 } from 'lucide-react';
import StageHeader from "../StageHeader";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { fetchWithAuth } from '../../lib/auth-client';
import UnifiedLogViewer from '../UnifiedLogViewer';
import CartridgePromptsEditor from '../CartridgePromptsEditor';
import DesignRegistryPanel from './DesignRegistryPanel';
import CodeViewer from '../visualization/CodeViewer'; // V3.9
import SchemaViewer from '../visualization/SchemaViewer'; // V3.9
import QualityDashboard from '../visualization/QualityDashboard'; // V3.9
import { useConfirm } from '@/app/hooks/useConfirm';

const REFINEMENT_AGENTS = [
    { id: 'P', name: 'The Performance Optimizer', role: 'Performance pattern optimizer' },
    { id: 'A', name: 'The Critic', role: 'Code quality & best-practice enforcer' },
    { id: 'R', name: 'The Refiner', role: 'Schema alignment & type safety validator' },
    { id: 'O', name: 'The Output Packager', role: 'Output file packager' },
];

// Helper: Extract generated files from file tree (drafting, refinement folders)
function extractGeneratedFiles(children: any[]): any[] {
    const assets: any[] = [];

    const traverseFolder = (nodes: any[], currentPath: string = '') => {
        for (const node of nodes) {
            const fullPath = currentPath ? `${currentPath}/${node.name}` : node.name;

            // Include files from drafting/ and refinement/ folders
            if (node.type === 'file' && (
                fullPath.includes('/drafting/') ||
                fullPath.includes('/refinement/')
            )) {
                // Extract file extension
                const ext = node.name.split('.').pop()?.toUpperCase() || 'FILE';

                // Create asset object compatible with SchemaViewer
                assets.push({
                    object_id: fullPath.replace(/\//g, '_'), // Unique ID from path
                    id: fullPath.replace(/\//g, '_'),
                    source_name: node.name,
                    filename: node.name,
                    target_name: node.name.replace(/\.(py|sql|scala|java)$/, ''),
                    category: fullPath.includes('/bronze/') ? 'BRONZE' :
                        fullPath.includes('/silver/') ? 'SILVER' :
                            fullPath.includes('/gold/') ? 'GOLD' : 'CORE',
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

interface RefinementViewProps {
    projectId: string;
    projectStage?: number;
    onStageChange?: (stage: number) => void;
    isReadOnly?: boolean;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void; activeSection: string;
    onSectionChange: (section: string) => void;
}

interface FileNode {
    name: string;
    path: string;
    type: "file" | "folder";
    children?: FileNode[];
    last_modified?: string | number;
}

export default function RefinementView({
    projectId,
    projectStage,
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
    const { confirm, ConfirmDialog } = useConfirm();
    const [isRefinementRunning, setIsRefinementRunning] = useState(false); // Active refinement process
    const [isFetchingLogs, setIsFetchingLogs] = useState(false); // True while fetching logs
    const [logs, setLogs] = useState<string[]>([]);
    const [profile, setProfile] = useState<any>(null);
    const [assets, setAssets] = useState<any[]>([]); // Objects/assets for SchemaViewer

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
                // Load refinement state
                const res = await fetchWithAuth(`projects/${projectId}/refinement/state`);
                const data = await res.json();

                if (data.log && data.log.length > 0) {
                    setLogs(data.log);
                }
                if (data.profile) {
                    setProfile(data.profile);
                }

                // Load assets from discovery for SchemaViewer
                // In Refinement, we want GENERATED files (drafting/refinement), not original assets
                try {
                    const filesRes = await fetchWithAuth(`projects/${projectId}/files`);
                    const filesData = await filesRes.json();

                    // Extract files from drafting and refinement folders
                    const extractedAssets = extractGeneratedFiles(filesData.children || []);
                    console.log('[RefinementView] Loaded generated files:', extractedAssets.length);
                    setAssets(extractedAssets);
                } catch (err) {
                    console.warn('[RefinementView] Could not load generated files:', err);
                }
            } catch (e) {
                console.error("Failed to restore state", e);
            }
        };
        fetchState();
    }, [projectId]);

    const fetchRefinementLogs = useCallback(async () => {
        setIsFetchingLogs(true);
        try {
            // Fetch execution logs from backend
            const res = await fetchWithAuth(`projects/${projectId}/execution-logs?type=refinement`);
            const data = await res.json();

            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");

                // Only update if we have logs from backend (avoid overwriting initial messages)
                if (logLines.length > 0) {
                    console.log(`[RefinementView] Fetched ${logLines.length} log lines`);
                    setLogs(logLines);
                }
            }

            // Check project status to detect completion
            const statusRes = await fetchWithAuth(`discovery/status/${projectId}`);
            const statusData = await statusRes.json();

            // If status is REFINED and we're currently running, process is complete
            if (statusData.status === "REFINED" && isRefinementRunning) {
                console.log("[RefinementView] Refinement complete, stopping polling");
                setIsRefinementRunning(false);
                setIsFinished(true);

                // Auto-transition to quality dashboard to see results
                console.log("[RefinementView] Auto-transitioning to quality view");
                setTimeout(() => {
                    onSectionChange('quality');
                }, 1500); // Small delay to see completion message
            }
        } catch (e) {
            console.error("[RefinementView] Failed to load refinement logs", e);
        } finally {
            setIsFetchingLogs(false);
        }
    }, [projectId, isRefinementRunning, onSectionChange]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRefinementRunning) {
            // Auto-navigate to logs section when refinement starts
            console.log("[RefinementView] Refinement started, auto-navigating to logs");
            onSectionChange('logs');

            // Add initial log message
            setLogs(["[INFO] Refinement started - Initializing agents..."]);

            // Start polling after 2 seconds (give backend time to initialize)
            const timeout = setTimeout(() => {
                fetchRefinementLogs(); // First fetch
                interval = setInterval(fetchRefinementLogs, 3000); // Then every 3 seconds
            }, 2000);

            return () => {
                clearTimeout(timeout);
                if (interval) clearInterval(interval);
            };
        }
    }, [isRefinementRunning, fetchRefinementLogs, onSectionChange]);

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
        // Check if re-executing a previous stage (rollback warning)
        const CURRENT_STAGE = 3; // Refinement is stage 3
        if (projectStage !== undefined && projectStage > CURRENT_STAGE) {
            const phaseNames = ['Discovery', 'Triage', 'Drafting', 'Refinement', 'Governance', 'Handover'];
            const lostPhases: string[] = [];
            for (let i = CURRENT_STAGE + 1; i <= projectStage; i++) {
                if (i < phaseNames.length) lostPhases.push(phaseNames[i]);
            }
            const rollbackOk = await confirm({
                variant: 'rollback',
                title: 'Re-running Refinement will roll back progress',
                description: 'The project will return to Stage 3. Drafting output is preserved.',
                lostPhases,
                confirmLabel: 'Yes, roll back & re-run',
            });
            if (!rollbackOk) return;
        }

        const runOk = await confirm({
            variant: 'execute',
            title: 'Run Refinement Phase?',
            description: 'The following AI agents will optimize and validate all generated migration code.',
            agents: REFINEMENT_AGENTS,
            confirmLabel: 'Run Refinement',
        });
        if (!runOk) return;

        // Reset state BEFORE starting
        setIsRefinementRunning(true);
        setIsFinished(false);
        setLogs([]); // Start with empty logs - will be populated by polling
        setProfile(null); // Clear previous profile

        try {
            const res = await fetchWithAuth(`refine/start`, {
                method: 'POST',
                body: JSON.stringify({ project_id: projectId })
            });
            const data = await res.json();

            if (data.error) {
                setLogs([`[ERROR] ${data.error}`]);
                setIsRefinementRunning(false);
            } else if (data.status === "RUNNING") {
                // Background task started successfully
                // Show initial message while waiting for backend logs
                setLogs([
                    "[SYSTEM] Refinement process initializing...",
                    "[SYSTEM] Backend is clearing previous logs and setting up workspace...",
                    "[SYSTEM] Logs will appear shortly..."
                ]);
                // Polling will start automatically via useEffect
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
            setLogs([`[Network Error] ${e}`]);
            setIsRefinementRunning(false);
        }
    };

    const handleApprove = async () => {
        const approveOk = await confirm({ variant: 'default', title: 'Approve Refinement?', description: 'This will move the project to the Governance phase. You can still return if needed.', confirmLabel: 'Approve & advance' });
        if (!approveOk) return;
        try {
            const res = await fetchWithAuth(`projects/${projectId}/stage`, {
                method: "POST",
                body: JSON.stringify({ stage: "4" })
            });
            const data = await res.json();
            if (data.success && onStageChange) {
                onStageChange(4);
            }
        } catch (e) {
            alert("Failed to approve stage.");
        }
    };

    const handleCancelRefinement = async () => {
        const cancelOk = await confirm({ variant: 'danger', title: 'Cancel refinement?', description: 'The running process will be stopped. Partial optimizations already applied will remain.', confirmLabel: 'Yes, cancel', cancelLabel: 'Keep running' });
        if (!cancelOk) return;

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
        if (activeSection === 'diff' || activeSection === 'comparison') {
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

            if (activeSection === 'diff' || activeSection === 'comparison') {
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

    // Watch for sidebar action triggers
    useEffect(() => {
        if (activeSection === 'run-refinement') {
            if (!isRefinementRunning) {
                handleRunRefinement();
            }
            onSectionChange('logs');
        }
    }, [activeSection, isRefinementRunning, onSectionChange]);

    return (
        <>
            <div className="flex flex-col h-full bg-[var(--background)]">
                <StageHeader
                    title="Stage 3: Intelligent Refinement"
                    subtitle="Compliance Auditor: Quality enforcement and pattern optimization"
                    icon={<Layers className="text-purple-500" />}
                    helpText="Final code refinement ensuring adherence to established architectural patterns."
                    onApprove={handleApprove}
                    approveLabel="Next Phase: Governance"
                    isApproveDisabled={isRefinementRunning || !isComplete}
                    isFullscreen={isFullscreen}
                    onToggleFullscreen={onToggleFullscreen}
                    onReset={onReset}
                    onBackToCurrent={onBackToCurrent}
                />

                {/* Main Content Area - Sprint 14: Sidebar managed at workspace level */}
                <div className="flex-1 overflow-hidden p-6">
                    {activeSection === 'status' && (
                        <div className="max-w-7xl mx-auto space-y-6 flex flex-col h-full">
                            {!isRefinementRunning && logs.length === 0 ? (
                                <div className="flex-1 flex items-center justify-center">
                                    <div className="text-center space-y-4">
                                        <div className="mx-auto w-16 h-16 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center">
                                            <RefreshCw size={32} className="text-purple-600 dark:text-purple-400" />
                                        </div>
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Ready to Refine</h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
                                            Click "Refine & Modernize" to apply architectural patterns and optimize the generated code.
                                        </p>
                                        <div className="text-xs text-gray-400 space-y-1 mt-4">
                                            <div>🔍 Profiler: Analyze code patterns</div>
                                            <div>🏗️ Architect: Apply Medallion design</div>
                                            <div>⚡ Refactor: Optimize performance</div>
                                            <div>🚀 Ops: Package for deployment</div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <UnifiedLogViewer
                                        mode="realtime"
                                        projectId={projectId}
                                        isRunning={isRefinementRunning}
                                        logs={logs}
                                        processName="Refinement Pipeline"
                                        variant="panel"
                                    />

                                    {profile && (
                                        <div className="grid grid-cols-2 gap-4 shrink-0">
                                            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
                                                <h3 className="font-bold text-gray-500 text-xs uppercase mb-2">Files Analyzed</h3>
                                                <p className="text-2xl font-bold text-purple-500">{profile.total_files}</p>
                                            </div>
                                            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
                                                <h3 className="font-bold text-gray-500 text-xs uppercase mb-2">Shared Connections</h3>
                                                <p className="text-2xl font-bold text-orange-500">{Object.keys(profile.shared_connections || {}).length}</p>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    )}

                    {/* Refinement Summary */}
                    {activeSection === 'summary' && (
                        <div className="max-w-7xl mx-auto h-full overflow-auto">
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
                                {/* Execution Status Card */}
                                <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <h3 className="font-bold text-gray-900 dark:text-white text-lg">Execution Status</h3>
                                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Current refinement state</p>
                                        </div>
                                        <div className={`p-3 rounded-xl ${isRefinementRunning ? 'bg-blue-100 dark:bg-blue-900/30' : isComplete ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-gray-800'}`}>
                                            <RefreshCw size={24} className={isRefinementRunning ? 'text-blue-600 animate-spin' : isComplete ? 'text-green-600' : 'text-gray-400'} />
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-gray-600 dark:text-gray-400">Status</span>
                                            <span className={`text-sm font-bold ${isRefinementRunning ? 'text-blue-600' : isComplete ? 'text-green-600' : 'text-gray-600'}`}>
                                                {isRefinementRunning ? '🔄 Running' : isComplete ? '✅ Complete' : '⏸️ Ready'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm text-gray-600 dark:text-gray-400">Log Entries</span>
                                            <span className="text-sm font-bold text-purple-600">{logs.length}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Files Analyzed Card */}
                                {profile && (
                                    <>
                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                            <div className="flex items-start justify-between mb-4">
                                                <div>
                                                    <h3 className="font-bold text-gray-900 dark:text-white text-lg">Files Analyzed</h3>
                                                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Processed by profiler</p>
                                                </div>
                                                <div className="p-3 rounded-xl bg-purple-100 dark:bg-purple-900/30">
                                                    <FileCode size={24} className="text-purple-600" />
                                                </div>
                                            </div>
                                            <div className="text-4xl font-black text-purple-600 mb-2">{profile.total_files || 0}</div>
                                            <p className="text-xs text-gray-500 dark:text-gray-400">Analyzed and optimized</p>
                                        </div>

                                        {/* Connections Card */}
                                        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                            <div className="flex items-start justify-between mb-4">
                                                <div>
                                                    <h3 className="font-bold text-gray-900 dark:text-white text-lg">Shared Connections</h3>
                                                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Connection pooling detected</p>
                                                </div>
                                                <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/30">
                                                    <Database size={24} className="text-orange-600" />
                                                </div>
                                            </div>
                                            <div className="text-4xl font-black text-orange-600 mb-2">
                                                {Object.keys(profile.shared_connections || {}).length}
                                            </div>
                                            <p className="text-xs text-gray-500 dark:text-gray-400">Optimized for reuse</p>
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Recent Logs Preview */}
                            {logs.length > 0 && (
                                <div className="mx-6 mb-6">
                                    <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                        <h3 className="font-bold text-gray-900 dark:text-white text-lg mb-4 flex items-center gap-2">
                                            <Terminal size={20} />
                                            Recent Activity
                                        </h3>
                                        <div className="space-y-2">
                                            {logs.slice(-5).map((log, idx) => (
                                                <div key={idx} className="text-xs font-mono text-gray-600 dark:text-gray-400 py-1 px-3 bg-gray-50 dark:bg-gray-800 rounded">
                                                    {log}
                                                </div>
                                            ))}
                                        </div>
                                        <button
                                            onClick={() => onSectionChange('logs')}
                                            className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
                                        >
                                            View all logs →
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Empty State */}
                            {!profile && !isRefinementRunning && logs.length === 0 && (
                                <div className="flex-1 flex items-center justify-center p-6">
                                    <div className="text-center space-y-4">
                                        <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
                                            <BarChart3 size={32} className="text-gray-400" />
                                        </div>
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">No Summary Data</h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
                                            Execute the refinement process to see a summary of results.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Schema Validation */}
                    {(activeSection === 'validation' || activeSection === 'schema') && (
                        <div className="h-full bg-white dark:bg-gray-900 rounded-xl overflow-hidden">
                            <SchemaViewer
                                projectId={projectId}
                                assets={assets}
                                showHistory={true}
                            />
                        </div>
                    )}

                    {activeSection === 'quality' && (
                        <div className="h-full bg-white dark:bg-gray-900 rounded-xl overflow-hidden">
                            <QualityDashboard projectId={projectId} />
                        </div>
                    )}



                    {/* Actions - Design Settings */}
                    {activeSection === 'settings' && (
                        <div className="max-w-7xl mx-auto h-full overflow-auto">
                            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800">
                                <div className="mb-6">
                                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Design Registry</h2>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        Configure architecture patterns, naming conventions, and medallion layer design standards.
                                    </p>
                                </div>
                                <DesignRegistryPanel projectId={projectId} />
                            </div>
                        </div>
                    )}

                    {/* Actions - Prompts */}
                    {activeSection === 'prompts' && (
                        <div className="h-full overflow-hidden">
                            <CartridgePromptsEditor projectId={projectId} />
                        </div>
                    )}



                    {/* Logs Section */}
                    {activeSection === 'logs' && (
                        <div className="max-w-7xl mx-auto space-y-6 flex flex-col h-full">
                            {/* Fetch indicator */}
                            {isFetchingLogs && (
                                <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
                                    <span className="text-sm text-blue-600 dark:text-blue-400">Fetching latest logs...</span>
                                </div>
                            )}

                            {logs.length === 0 ? (
                                <div className="flex-1 flex items-center justify-center">
                                    <div className="text-center space-y-4">
                                        <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
                                            <Terminal size={32} className="text-gray-500" />
                                        </div>
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">No Logs Yet</h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
                                            Execute the refinement process to see orchestrator logs and Agent decisions.
                                        </p>
                                        {isRefinementRunning && (
                                            <div className="flex items-center justify-center gap-2 text-blue-500">
                                                <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
                                                <span className="text-sm">Refinement in progress...</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <UnifiedLogViewer
                                    mode="realtime"
                                    projectId={projectId}
                                    isRunning={isRefinementRunning}
                                    logs={logs}
                                    processName="Refinement Pipeline"
                                    variant="panel"
                                />
                            )}
                        </div>
                    )}

                    {/* Code Comparison */}
                    {(activeSection === 'diff' || activeSection === 'comparison') && (
                        <div className="flex h-full gap-4">
                            <div className="w-1/4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
                                <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center">
                                    <h3 className="font-bold text-sm uppercase text-gray-400">Refined Files</h3>
                                    <button
                                        onClick={() => fetchWithAuth(`projects/${projectId}/files`).then(res => res.json()).then(data => setFileTree(data.children || []))}
                                        className="text-gray-400 hover:text-primary"
                                        title="Refresh"
                                    >
                                        <RefreshCw size={14} />
                                    </button>
                                </div>
                                <div className="flex-1 overflow-y-auto p-2">
                                    {fileTree.length === 0 ? (
                                        <div className="text-center py-10 px-4">
                                            <div className="mx-auto w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-3">
                                                <FolderOpen size={24} className="text-gray-400" />
                                            </div>
                                            <p className="text-gray-500 dark:text-gray-400 text-sm">No refined files yet.</p>
                                            <p className="text-gray-400 text-xs mt-2">Run refinement to generate optimized code.</p>
                                        </div>
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
                                            <span className="flex items-center gap-2">
                                                {selectedFile.split(/[\\/]/).pop()}
                                                {selectedFile.toLowerCase().includes("bronze") && <span className="text-[10px] bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-400 px-2 py-0.5 rounded border border-orange-200 dark:border-orange-800">🟠 BRONZE</span>}
                                                {selectedFile.toLowerCase().includes("silver") && <span className="text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 px-2 py-0.5 rounded border border-gray-200 dark:border-gray-600">⚪ SILVER</span>}
                                                {selectedFile.toLowerCase().includes("gold") && <span className="text-[10px] bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 px-2 py-0.5 rounded border border-yellow-200 dark:border-yellow-800">🟡 GOLD</span>}
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
            {ConfirmDialog}
        </>
    );
}
