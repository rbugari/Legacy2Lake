"use client";
import React, { useState, useEffect, useCallback } from 'react';
import { Play, FileText, Database, GitBranch, Terminal, Layers, CheckCircle, Search, FolderOpen, ChevronRight, ChevronDown, FileCode, Folder, Settings, Brain } from 'lucide-react';
import { API_BASE_URL } from '../../lib/config';
import CodeDiffViewer from '../CodeDiffViewer';
import StageHeader from "../StageHeader";
import PromptsExplorer from '../PromptsExplorer';
import DesignRegistryPanel from './DesignRegistryPanel';
import TechnologyMixer from './TechnologyMixer';

interface RefinementViewProps {
    projectId: string;
    onStageChange?: (stage: number) => void;
    isReadOnly?: boolean;
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
    { id: 'config', label: 'Solution Config', icon: <Settings size={18} /> },
];

export default function RefinementView({ projectId, onStageChange, isReadOnly }: RefinementViewProps) {
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

    const fetchRefinementLogs = useCallback(async () => {
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
        const confirmMsg = "Esta acción ejecutará la fase de Refinamiento (Agentes P, A, R, O). Esto incurre en costos de tokens y tiempo de procesamiento.\n\n¿Deseas continuar?";
        if (!confirm(confirmMsg)) return;

        setIsRunning(true);
        setIsFinished(false);
        setLogs(["Starting Refinement Phase...", "Initializing Agents..."]);
        try {
            const res = await fetch(`${API_BASE_URL}/refine/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
        if (!confirm("¿Seguro que deseas aprobar la fase de refinamiento y mover el proyecto a Gobernanza?")) return;
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

    useEffect(() => {
        if (activeTab === 'workbench' || activeTab === 'artifacts') {
            fetch(`${API_BASE_URL}/projects/${projectId}/files`)
                .then(res => res.json())
                .then(data => setFileTree(data.children || []))
                .catch(err => console.error("Failed to load file tree", err));
        }
    }, [activeTab, projectId, logs]);

    const resolveOriginalPath = (refinedPath: string) => {
        if (!refinedPath.includes('Refinement')) return null;
        let filename = refinedPath.split(/[\\/]/).pop() || "";
        filename = filename.replace('_bronze.py', '.py')
            .replace('_silver.py', '.py')
            .replace('_gold.py', '.py');
        const basePath = refinedPath.split('Refinement')[0];
        return `${basePath}Drafting/${filename}`;
    };

    const handleFileSelect = async (path: string) => {
        setSelectedFile(path);
        setIsLoadingFile(true);
        setFileContent("");
        setOriginalContent("");

        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/files/content?path=${encodeURIComponent(path)}`);
            const data = await res.json();
            setFileContent(data.content || "");

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

    const FileTree = ({ node, level, onSelect, selectedPath }: { node: FileNode, level: number, onSelect: (n: FileNode) => void, selectedPath?: string }) => {
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
    };

    const [isFinished, setIsFinished] = useState(false);
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
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
            <StageHeader
                title="Refinamiento (Modernization)"
                subtitle="Transformación a arquitectura Medallion (Bronze/Silver/Gold)"
                icon={<Layers className="text-primary" />}
                isReadOnly={isReadOnly}
                isApproveDisabled={!isComplete}
                isExecuting={isRunning}
                onApprove={handleApprove}
                approveLabel="Aprobar Fase 3"
                onRestart={async () => {
                    if (window.confirm("¿Reiniciar Refinamiento? Se perderán las transformaciones actuales.")) {
                        if (onStageChange) onStageChange(3);
                    }
                }}
            >
                <button
                    onClick={handleRunRefinement}
                    disabled={isRunning || isReadOnly}
                    className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${isRunning || isReadOnly
                        ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                        : "bg-purple-600 hover:bg-purple-700 text-white shadow-purple-200 dark:shadow-none"
                        }`}
                >
                    <Play size={12} className={isRunning ? "animate-spin" : ""} />
                    {isRunning ? "Refining..." : "Refinar & Modernizar"}
                </button>
            </StageHeader>

            <div className="flex bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 px-4">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-6 py-4 text-xs font-bold border-b-2 transition-colors ${activeTab === tab.id
                            ? 'border-primary text-primary bg-primary/5'
                            : 'border-transparent text-gray-500 hover:text-gray-700'
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

                {(activeTab === 'workbench' || activeTab === 'artifacts') && (
                    <div className="flex h-full gap-4">
                        {/* Existing Workbench/Artifacts code... */}
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
                                            <FileTree
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

                {activeTab === 'config' && (
                    <div className="h-full flex flex-col gap-6 overflow-y-auto pr-2">
                        <div className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                            <TechnologyMixer projectId={projectId} />
                        </div>
                        <div className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                <Settings size={20} className="text-primary" />
                                Estándares de Arquitectura
                            </h3>
                            <DesignRegistryPanel projectId={projectId} />
                        </div>
                        <div className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                <Brain size={20} className="text-primary" />
                                Configuración de Inteligencia
                            </h3>
                            <PromptsExplorer />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
