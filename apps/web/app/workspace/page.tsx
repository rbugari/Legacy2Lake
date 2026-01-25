"use client";
import React, { useCallback, useState, useEffect, Suspense } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import { useAuth } from "../context/AuthContext";
import { useSearchParams } from "next/navigation"; // [NEW]
import TriageView from "../components/stages/TriageView";
import DiscoveryView from "../components/stages/DiscoveryView";
import DraftingView from "../components/stages/DraftingView";
import GovernanceView from "../components/stages/GovernanceView";
import RefinementView from "../components/stages/RefinementView";
import HandoverView from "../components/stages/HandoverView";
import WorkflowToolbar from "../components/WorkflowToolbar";
import LogsSidePanel from "../components/LogsSidePanel";
import WorkspaceSidebar from "../components/WorkspaceSidebar";
import SolutionConfigDrawer from "../components/SolutionConfigDrawer";

import { API_BASE_URL } from "../lib/config";
import {
    Activity, ArrowRight, CheckCircle, Code, FileText, GitCommit,
    GitPullRequest, Layout, Play, Save, Settings, Share2,
    Terminal, Download, ArrowLeft, RefreshCw, Users, Eye
} from "lucide-react";

function WorkspaceContent() {
    const { user } = useAuth();
    const searchParams = useSearchParams(); // [NEW]
    const id = searchParams.get('id') || '';

    const [nodes, setNodes] = useState<any[]>([]);
    const [edges, setEdges] = useState<any[]>([]);
    const [meshData, setMeshData] = useState<any>({ nodes: [], edges: [] });

    const [isSaving, setIsSaving] = useState(false);
    const [lastSaved, setLastSaved] = useState<Date | null>(null);

    // Split State: projectStage (Backend) vs activeView (UI)
    const [projectStage, setProjectStage] = useState(1);
    const [activeView, setActiveView] = useState(1);

    const [selectedNode, setSelectedNode] = useState<any>(null);
    const [showLogs, setShowLogs] = useState(false);
    const [showConfig, setShowConfig] = useState(false);
    const [sidebarStats, setSidebarStats] = useState({ core: 12, ignored: 4, pending: 8 });

    useEffect(() => {
        if (!id || id === 'undefined') {
            // Wait for hydration or redirect if truly missing
            // window.location.href = '/dashboard'; 
            return;
        }
    }, [id]);

    // Mock data for Stage 3
    const [originalCode, setOriginalCode] = useState("-- SQL Legacy Code\nSELECT * FROM Sales WHERE Date > '2023-01-01'");
    const [optimizedCode, setOptimizedCode] = useState("# PySpark Cloud Native\ndf = spark.read.table('sales')\ndf.filter(df.Date > '2023-01-01').show()");

    // Initial Load
    const [projectName, setProjectName] = useState<string | null>(null);
    const [repoUrl, setRepoUrl] = useState<string | null>(null);
    const [ghostTenantId, setGhostTenantId] = useState<string | null>(null);

    // Initial Load & Project Details
    useEffect(() => {
        if (!id) return;

        // Fetch Project Details
        fetch(`${API_BASE_URL}/projects/${id}`)
            .then(res => res.json())
            .then(data => {
                if (data.name) setProjectName(data.name);
                if (data.repo_url) setRepoUrl(data.repo_url);
                if (data.stage) {
                    const s = parseInt(data.stage);
                    setProjectStage(s);
                    setActiveView(s);
                }

                // Ghost Mode Detection
                if (user?.role === 'ADMIN' && data.tenant_id && data.tenant_id !== user.tenant_id) {
                    setGhostTenantId(data.tenant_id);
                }
            })
            .catch(err => console.error("Failed to fetch project details", err));

        const initialNodes = [
            { id: '1', type: 'package', position: { x: 250, y: 5 }, data: { label: 'SSIS Package A' } },
            { id: '2', type: 'task', position: { x: 100, y: 100 }, data: { label: 'Data Flow' } },
            { id: '3', type: 'script', position: { x: 400, y: 100 }, data: { label: 'Script Task' } }
        ];
        setMeshData({ nodes: initialNodes, edges: [] });
    }, [id]);

    const handleNodeDragStop = useCallback(async (event: any, node: any, nodes: any[]) => {
        if (!id) return;
        setIsSaving(true);
        // Simulate autosave to backend
        try {
            await fetch(`${API_BASE_URL}/projects/${id}/layout`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nodes })
            });
            setLastSaved(new Date());
        } catch (e) {
            console.error("Autosave failed", e);
        } finally {
            setIsSaving(false);
        }
    }, [id]);

    const [isTranspiling, setIsTranspiling] = useState(false);
    const [suggestions, setSuggestions] = useState<string[]>([]);

    const handleNodeClick = async (node: any) => {
        setSelectedNode(node);
        // If in stage 3, load the code for this node
        if (activeView === 3) {
            setIsTranspiling(true);
            setSuggestions([]); // Clear previous suggestions
            setOriginalCode(`-- Loading source for ${node.data.label}...`);
            setOptimizedCode("# Generating PySpark...");

            try {
                const response = await fetch(`${API_BASE_URL}/transpile/task`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        node_data: node.data,
                        context: { project_id: id }
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    setOriginalCode(data.interpreter.original_sql || `-- No SQL source found for ${node.data.label}`);
                    setOptimizedCode(data.final_code || "# No code generated");

                    // Parse suggestions from Agent F if available
                    if (data.critic && data.critic.suggestions) {
                        setSuggestions(data.critic.suggestions);
                    } else if (data.critic && data.critic.review) {
                        // Fallback if structured suggestions aren't there
                        setSuggestions([data.critic.review]);
                    }
                } else {
                    setOriginalCode("-- Error fetching task data");
                    setOptimizedCode(`# Error: ${response.statusText}`);
                }
            } catch (error) {
                console.error("Transpilation error:", error);
                setOptimizedCode(`# Connection Error: ${error}`);
            } finally {
                setIsTranspiling(false);
            }
        }
    };

    const [isStageComplete, setIsStageComplete] = useState(false);

    // Reset completion when stage changes
    useEffect(() => {
        setIsStageComplete(false);
    }, [activeView]);

    const handleApproveStage = async (targetStage: number) => {
        if (!id) return;
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${id}/stage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ stage: targetStage.toString() })
            });
            const data = await res.json();
            if (data.success) {
                setProjectStage(targetStage);
                setActiveView(targetStage);
            }
        } catch (e) {
            console.error("Failed to update stage", e);
        }
    };

    if (!id) return <div className="flex items-center justify-center h-screen">Loading Workspace...</div>;

    return (
        <ReactFlowProvider>
            <div className="flex h-screen bg-[#050505] text-[var(--text-primary)] overflow-hidden">
                <WorkspaceSidebar
                    projectName={projectName || id}
                    activeStage={projectStage}
                    stats={sidebarStats}
                    onAction={(action) => {
                        if (action === 'config') setShowConfig(true);
                        if (action === 'export') window.open(`${API_BASE_URL}/projects/${id}/export`);
                        if (action === 'reset') alert("Reset Phase placeholder");
                    }}
                />

                {/* Main Content */}
                <main className="flex-1 flex flex-col relative">
                    {/* Top Bar */}
                    <header className="bg-[var(--surface)] border-b border-[var(--border)] flex flex-col pt-3 px-6 gap-2">
                        <div className="flex justify-between items-start w-full">
                            <div className="flex flex-col gap-1">
                                <h1 className="font-black text-xs uppercase tracking-[0.3em] text-[var(--text-tertiary)] flex items-center gap-2">
                                    Engineering Console
                                </h1>
                                {repoUrl && (
                                    <a
                                        href={repoUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] hover:text-blue-500 transition-colors hover:underline"
                                    >
                                        <div className="w-4 h-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                                            <GitCommit size={10} />
                                        </div>
                                        {repoUrl}
                                    </a>
                                )}
                            </div>
                            <div className="flex items-center gap-3">
                                {/* Ghost Badge */}
                                {ghostTenantId && (
                                    <div className="flex items-center gap-1.5 px-3 py-1 bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 rounded-full text-xs font-bold animate-pulse">
                                        <Eye size={12} />
                                        <span>Viewing as Tenant</span>
                                    </div>
                                )}
                                {isSaving && <span className="text-xs text-gray-400 animate-pulse flex items-center gap-1"><Save size={12} /> Saving...</span>}
                                {!isSaving && lastSaved && <span className="text-xs text-gray-400">Saved</span>}
                                <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />

                                <button
                                    onClick={() => setShowLogs(true)}
                                    className="p-1.5 text-gray-500 hover:text-cyan-500 hover:bg-cyan-500/10 rounded-md transition-all relative"
                                    title="Agent Terminal"
                                >
                                    <Terminal size={18} />
                                    <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-cyan-500 rounded-full animate-pulse" />
                                </button>
                                <button
                                    onClick={() => setShowConfig(true)}
                                    className="p-1.5 text-gray-500 hover:text-cyan-500 hover:bg-cyan-500/10 rounded-md transition-all"
                                    title="Configure Solution"
                                >
                                    <Settings size={18} />
                                </button>
                                <div className="h-4 w-px bg-gray-200 dark:bg-gray-800 mx-1" />
                                <button
                                    className="p-1.5 text-gray-500 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-all"
                                    title="Collaborate"
                                >
                                    <Users size={18} />
                                </button>
                                <a
                                    href={`${API_BASE_URL}/projects/${id}/export`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-1.5 text-gray-500 hover:text-black dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-all"
                                    title="Export (.zip)"
                                >
                                    <Download size={18} />
                                </a>
                            </div>
                        </div>

                        {/* New Visual Workflow Toolbar */}
                        <WorkflowToolbar
                            currentStage={projectStage}
                            activeView={activeView}
                            onSetView={setActiveView}
                        />
                    </header>

                    {/* Stage Content */}
                    <div className="flex-1 relative overflow-hidden">
                        {/* Inspection Mode Banner */}
                        {activeView < projectStage && (
                            <div className="absolute top-0 left-0 right-0 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 py-1.5 px-6 flex justify-between items-center z-50 animate-in slide-in-from-top duration-300">
                                <p className="text-[10px] font-bold text-amber-700 dark:text-amber-400 uppercase tracking-widest flex items-center gap-2">
                                    <Users size={12} /> Inspection Mode: You are viewing a previous stage.
                                </p>
                                <button
                                    onClick={() => setActiveView(projectStage)}
                                    className="text-[10px] font-bold text-amber-800 dark:text-amber-300 underline"
                                >
                                    Jump to Active Stage
                                </button>
                            </div>
                        )}

                        {activeView === 0 && (
                            <DiscoveryView
                                projectId={id}
                                onStageChange={(s: number) => handleApproveStage(s)}
                            />
                        )}
                        {activeView === 1 && (
                            <TriageView
                                projectId={id}
                                onStageChange={(s: number) => handleApproveStage(s)}
                                isReadOnly={activeView < projectStage}
                            />
                        )}

                        {activeView === 2 && (
                            <DraftingView
                                projectId={id || ""}
                                onStageChange={(s) => handleApproveStage(s)}
                                onCompletion={(completed) => setIsStageComplete(completed)}
                                isReadOnly={activeView < projectStage}
                                activeTenantId={ghostTenantId || undefined}
                            />
                        )}
                        {activeView === 3 && (
                            <RefinementView
                                projectId={id || ""}
                                onStageChange={(s) => handleApproveStage(s)}
                                isReadOnly={activeView < projectStage}
                            />
                        )}


                        {activeView === 4 && (
                            <GovernanceView projectId={id || ""} />
                        )}
                        {activeView === 5 && (
                            <HandoverView
                                projectId={id || ""}
                                onStageChange={(s: number) => handleApproveStage(s)}
                            />
                        )}

                    </div >

                    {/* Global Diagnostics Sidebar */}
                    <LogsSidePanel
                        projectId={id}
                        isOpen={showLogs}
                        onClose={() => setShowLogs(false)}
                    />

                    {/* Global Configuration Drawer */}
                    <SolutionConfigDrawer
                        isOpen={showConfig}
                        onClose={() => setShowConfig(false)}
                    />
                </main >
            </div >
        </ReactFlowProvider >
    );
}

function NavItem({ icon, label, active, onClick }: any) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${active
                ? 'bg-primary/10 text-primary font-bold'
                : 'text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
        >
            {icon}
            <span className="hidden md:block text-sm">{label}</span>
        </button>
    );
}

export default function WorkspacePage() {
    return (
        <Suspense fallback={<div>Loading Workspace...</div>}>
            <WorkspaceContent />
        </Suspense>
    );
}
