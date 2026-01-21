
"use client";
import { useState, useEffect } from 'react';
import { Play, FileText, Database, GitBranch, Terminal, Layers, CheckCircle, Search } from 'lucide-react';
import { API_BASE_URL } from '../../lib/config';
import CodeDiffViewer from '../CodeDiffViewer';
import PromptsExplorer from '../PromptsExplorer';

interface RefinementViewProps {
    projectId: string;
    onStageChange?: (stage: number) => void;
}

const TABS = [
    { id: 'orchestrator', label: 'Orchestration', icon: <Layers size={18} /> },
    { id: 'prompts', label: 'Intelligence', icon: <Terminal size={18} /> },
    { id: 'workbench', label: 'Workbench (Diff)', icon: <GitBranch size={18} /> },
    { id: 'artifacts', label: 'Artifacts', icon: <Database size={18} /> },
];

export default function RefinementView({ projectId, onStageChange }: RefinementViewProps) {
    const [activeTab, setActiveTab] = useState('orchestrator');
    const [isRunning, setIsRunning] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [profile, setProfile] = useState<any>(null);

    // Workbench State
    const [fileTree, setFileTree] = useState<any[]>([]);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [fileContent, setFileContent] = useState<string>("");
    const [originalContent, setOriginalContent] = useState<string>("");
    const [isLoadingFile, setIsLoadingFile] = useState(false);

    // State Restoration on Mount
    useEffect(() => {
        const fetchState = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/projects/${projectId}/refinement/state`);
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

    const fetchRefinementLogs = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/logs?type=refinement`);
            const data = await res.json();
            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");
                setLogs(logLines);
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    };

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRunning) {
            interval = setInterval(fetchRefinementLogs, 2000);
        }
        return () => clearInterval(interval);
    }, [isRunning, projectId]);

    // Initial load of logs if we are restoring state
    useEffect(() => {
        // If we restored logs from state, that's good, but we can also fetch latest file content
        fetchRefinementLogs();
    }, [projectId]);


    const handleRunRefinement = async () => {
        const confirmMsg = "Esta acción ejecutará la fase de Refinamiento (Agentes P, A, R, O). Esto incurre en costos de tokens y tiempo de procesamiento.\n\n¿Deseas continuar?";
        if (!confirm(confirmMsg)) return;

        setIsRunning(true);
        setLogs(["Starting Refinement Phase...", "Initializing Agents..."]);
        try {
            const res = await fetch(`${API_BASE_URL}/refine/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: projectId })
            });
            const data = await res.json();

            if (data.log) {
                // Final sync
                setLogs(data.log);
            }
            if (data.profile) {
                setProfile(data.profile);
            }
        } catch (e) {
            setLogs(prev => [...prev, `[Network Error] ${e}`]);
        } finally {
            setIsRunning(false);
            fetchRefinementLogs(); // Final check
        }
    };

    const handleApprove = async () => {
        if (!confirm("Are you sure you want to approve this architecture and move to Governance?")) return;
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/stage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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

    // Fetch files when changing to Workbench or Artifacts tab
    useEffect(() => {
        if (activeTab === 'workbench' || activeTab === 'artifacts') {
            fetch(`${API_BASE_URL}/projects/${projectId}/files`)
                .then(res => res.json())
                .then(data => setFileTree(data))
                .catch(err => console.error("Failed to load file tree", err));
        }
    }, [activeTab, projectId, logs]); // Refresh when logs change (pipeline done)

    const resolveOriginalPath = (refinedPath: string) => {
        // Heuristic to find original file in Output/ from a Refined/ file
        // Refined: .../Refined/Bronze/DimCategory_bronze.py -> Output/DimCategory.py
        if (!refinedPath.includes('Refined')) return null;

        // Extract filename and clean layer suffixes
        let filename = refinedPath.split(/[\\/]/).pop() || "";
        filename = filename.replace('_bronze.py', '.py')
            .replace('_silver.py', '.py')
            .replace('_gold.py', '.py');

        // Replace Refined/... with Output/
        const basePath = refinedPath.split('Refined')[0];
        return `${basePath}Output/${filename}`;
    };

    const handleFileSelect = async (path: string) => {
        setSelectedFile(path);
        setIsLoadingFile(true);
        setFileContent("");
        setOriginalContent("");

        try {
            // Load Refined Content
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/files/content?path=${encodeURIComponent(path)}`);
            const data = await res.json();
            setFileContent(data.content || "");

            // If in Workbench (Diff), try to load original
            if (activeTab === 'workbench') {
                const origPath = resolveOriginalPath(path);
                if (origPath) {
                    const resOrig = await fetch(`${API_BASE_URL}/projects/${projectId}/files/content?path=${encodeURIComponent(origPath)}`);
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

    const renderFileTree = (nodes: any[], filterDir?: string) => {
        // Validation check
        if (!nodes || !Array.isArray(nodes)) {
            return <div className="p-4 text-xs text-gray-400 italic">No files available</div>;
        }

        // Option to filter tree to a specific root directory (e.g. "Refined")
        const visibleNodes = filterDir ? nodes.filter(n => n.name === filterDir) : nodes;

        const renderNodes = (nds: any[]) => (
            <ul className="pl-4 border-l border-gray-200 dark:border-gray-800 space-y-1">
                {nds.map((node: any) => (
                    <li key={node.path}>
                        {node.type === 'directory' ? (
                            <details open={node.name === 'Refined' || node.name === 'Bronze' || node.name === 'Silver'}>
                                <summary className="cursor-pointer text-sm font-bold text-gray-700 dark:text-gray-300 hover:text-primary list-none flex items-center gap-1">
                                    <span className="text-xs">📂</span> {node.name}
                                </summary>
                                {node.children && renderNodes(node.children)}
                            </details>
                        ) : (
                            <button
                                onClick={() => handleFileSelect(node.path)}
                                className={`text-sm py-1 px-2 rounded w-full text-left truncate flex items-center gap-2 ${selectedFile === node.path
                                    ? 'bg-primary/10 text-primary font-bold'
                                    : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                                    }`}
                            >
                                <FileText size={14} />
                                {node.name}
                            </button>
                        )}
                    </li>
                ))}
            </ul>
        );

        return renderNodes(visibleNodes);
    };

    const isComplete = logs.some(l => l.includes("Pipeline Complete") || l.includes("COMPLETED"));

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
            {/* Top Operational Bar (Toolbar) */}
            <div className="flex items-center justify-between px-4 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 shadow-sm z-10 transition-all">
                {/* Left: Tabs */}
                <div className="flex">
                    {TABS.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id
                                ? 'border-primary text-primary bg-primary/5'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                                }`}
                        >
                            {tab.icon} <span>{tab.label}</span>
                        </button>
                    ))}
                </div>

                {/* Right: Operational Controls */}
                <div className="flex items-center gap-4">
                    {/* Group A: View/State Controls (Placeholder for consistency or Reset) */}
                    {/* We can add a Reset Log button here if we want, for now just keeping structure consistent */}
                    <div className="flex items-center gap-1 bg-gray-50 dark:bg-gray-900 p-1 rounded-lg border border-gray-100 dark:border-gray-800">
                        <span className="text-[10px] uppercase font-bold text-gray-400 px-2 select-none">Refinement Ops</span>
                    </div>

                    <div className="h-8 w-px bg-gray-200 dark:bg-gray-800" />

                    {/* Group B: Actions */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleRunRefinement}
                            disabled={isRunning}
                            className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${isRunning
                                ? "bg-gray-400 cursor-not-allowed"
                                : "bg-purple-600 hover:bg-purple-700 text-white shadow-purple-200 dark:shadow-none"
                                }`}
                        >
                            <Play size={14} className={isRunning ? "animate-spin" : ""} />
                            {isRunning ? "Refining..." : "Refine & Modernize"}
                        </button>

                        {isComplete && (
                            <button
                                onClick={handleApprove}
                                className="px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all bg-green-600 hover:bg-green-700 text-white shadow-green-200 dark:shadow-none"
                            >
                                <CheckCircle size={14} /> Approve Phase 3
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 p-8 overflow-hidden">
                {activeTab === 'orchestrator' && (
                    <div className="max-w-4xl mx-auto space-y-6 flex flex-col h-full">
                        {/* Control Panel */}
                        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 flex justify-between items-center shrink-0">
                            <div>
                                <h2 className="text-xl font-bold flex items-center gap-2"><Layers className="text-primary" /> Phase 3: Refinement</h2>
                                <p className="text-gray-500 text-sm mt-1">Transform Draft Code into Medallion Architecture (Bronze/Silver/Gold).</p>
                            </div>
                            {/* Actions moved to Top Toolbar */}
                        </div>

                        {/* Console Output */}
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

                        {/* Profile Summary */}
                        {profile && (
                            <div className="grid grid-cols-2 gap-4 shrink-0">
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 shadow-sm">
                                    <h3 className="font-bold text-gray-500 text-xs uppercase mb-2">Files Analyzed</h3>
                                    <p className="text-2xl font-bold text-primary">{profile.total_files}</p>
                                </div>
                                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 shadow-sm">
                                    <h3 className="font-bold text-gray-500 text-xs uppercase mb-2">Shared Connections</h3>
                                    <p className="text-2xl font-bold text-orange-500">{Object.keys(profile.shared_connections || {}).length}</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'prompts' && (
                    <div className="h-full bg-white dark:bg-gray-950 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                        <div className="mb-6">
                            <h2 className="text-xl font-bold flex items-center gap-2"><Terminal className="text-primary" /> Intelligence Hub</h2>
                            <p className="text-gray-500 text-sm">System Prompts for cross-phase orchestration.</p>
                        </div>
                        <PromptsExplorer />
                    </div>
                )}

                {(activeTab === 'workbench' || activeTab === 'artifacts') && (
                    <div className="flex h-full gap-4">
                        {/* File Tree */}
                        <div className="w-1/4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center">
                                <h3 className="font-bold text-sm uppercase text-gray-400">{activeTab === 'workbench' ? 'Files to Review' : 'Artifacts Explorer'}</h3>
                                <button className="text-gray-400 hover:text-primary"><Search size={14} /></button>
                            </div>
                            <div className="flex-1 overflow-y-auto p-2">
                                {fileTree.length === 0 ? (
                                    <p className="text-gray-400 text-sm text-center mt-10">No files generated yet.</p>
                                ) : (
                                    renderFileTree(fileTree, activeTab === 'artifacts' ? 'Refined' : undefined)
                                )}
                            </div>
                        </div>

                        {/* Right Content Pane (Diff or Artifact Viewer) */}
                        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden shadow-lg">
                            <div className="p-3 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50">
                                <h3 className="font-bold text-sm flex items-center gap-2">
                                    <FileText size={16} className="text-primary" />
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
                                        <CodeDiffViewer originalCode={originalContent} modifiedCode={fileContent} />
                                    ) : (
                                        <div className="p-4 bg-[#1e1e1e] text-gray-200 font-mono text-sm leading-relaxed h-full overflow-auto">
                                            <pre className="whitespace-pre-wrap">{fileContent}</pre>
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
