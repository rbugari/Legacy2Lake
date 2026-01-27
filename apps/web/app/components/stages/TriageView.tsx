"use client";
import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
    ReactFlowProvider,
    useNodesState,
    useEdgesState,
    addEdge,
    useReactFlow,
    MarkerType
} from '@xyflow/react';
import MeshGraph from '../MeshGraph';
import StageHeader from '../StageHeader';
import { Map, CheckCircle, Layout, List, Terminal, MessageSquare, Play, FileText, RotateCcw, PanelLeftClose, PanelLeftOpen, Expand, Shrink, Save, ShieldCheck, AlertTriangle, Shield, ShieldAlert, Zap, Clock, Database, Infinity, FileEdit, Activity, RefreshCw } from 'lucide-react';
import DiscoveryDashboard from '../DiscoveryDashboard';
import { API_BASE_URL } from '../../lib/config';
import PromptsExplorer from '../PromptsExplorer'; // Added Phase 0
import ColumnMappingEditor from '../ColumnMappingEditor'; // Added Phase A

// Tab Definitions
const TABS = [
    { id: 'graph', label: 'Graph', icon: <Layout size={14} />, group: 'Views' },
    { id: 'grid', label: 'Grid', icon: <List size={14} />, group: 'Views' },
    { id: 'mapping', label: 'Mapping', icon: <Database size={14} />, group: 'Views' },
    { id: 'prompt', label: 'AI Prompts', icon: <Terminal size={14} />, group: 'Config' },
    { id: 'context', label: 'Manual Input', icon: <MessageSquare size={14} />, group: 'Config' },
    { id: 'logs', label: 'Execution', icon: <FileText size={14} />, group: 'Config' },
];

export default function TriageView({
    projectId,
    activeTenantId,
    onStageChange,
    isReadOnly: propReadOnly,
    onStatsUpdate
}: {
    projectId: string,
    activeTenantId?: string,
    onStageChange?: (stage: number) => void,
    isReadOnly?: boolean,
    onStatsUpdate?: (stats: any) => void
}) {
    // Safety check: prioritize Prop ReadOnly (from parent) but keep internal state for fallback
    const isReadOnly = propReadOnly ?? false;
    const [activeTab, setActiveTab] = useState('graph');
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Data State
    const [assets, setAssets] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // Graph State
    const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);

    // Prompt & Context State
    const [systemPrompt, setSystemPrompt] = useState("");
    const [userContext, setUserContext] = useState("");
    const [triageLog, setTriageLog] = useState("");

    // Heatmap State
    const [activeHeatmap, setActiveHeatmap] = useState<'none' | 'pii' | 'criticality' | 'volume'>('none');
    const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);

    // DnD (Keep for Graph Tab logic if needed, though split pane is gone)
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

    const [showSidebar, setShowSidebar] = useState(true);

    // Release 1.1: Context State
    const [assetContexts, setAssetContexts] = useState<Record<string, { notes: string, rules: any }>>({});
    const [selectedAssetForContext, setSelectedAssetForContext] = useState<any | null>(null);
    const [isSavingContext, setIsSavingContext] = useState(false);
    const [editingAsset, setEditingAsset] = useState<any | null>(null);
    const [assetNote, setAssetNote] = useState("");

    const handleDeleteNode = useCallback((id: string) => {
        if (isReadOnly) return;
        setNodes(nds => nds.filter(n => n.id !== id));
        setAssets(prev => prev.map(a => a.id === id ? { ...a, type: 'IGNORED' } : a));
    }, [setNodes, setAssets, isReadOnly]);

    const enrichNodes = useCallback((nds: any[], heatmapMode: string = 'none') => {
        return nds.map(n => ({
            ...n,
            data: {
                ...n.data,
                onDelete: handleDeleteNode,
                id: n.id,
                isReadOnly: isReadOnly,
                heatmapMode: heatmapMode // Pass current heatmap mode
            },
            draggable: !isReadOnly,
            selectable: !isReadOnly,
            deletable: !isReadOnly
        }));
    }, [handleDeleteNode, isReadOnly]);

    // Handle Heatmap Change
    useEffect(() => {
        setNodes(nds => enrichNodes(nds, activeHeatmap));
    }, [activeHeatmap, setNodes, enrichNodes]);

    const handleCategoryChange = useCallback(async (assetId: string, newCategory: string) => {
        if (isReadOnly) return;

        // Optimistic UI Update
        setAssets(prev => prev.map(a =>
            a.id === assetId ? { ...a, type: newCategory } : a
        ));

        setNodes(nds => {
            const exists = nds.some(n => n.id === assetId);
            if (newCategory === 'CORE' && !exists) {
                const asset = assets.find(a => a.id === assetId);
                const newNode = {
                    id: assetId,
                    type: 'custom',
                    position: { x: 300, y: 300 },
                    data: { label: asset?.name || assetId, category: newCategory, complexity: 'LOW', status: 'pending' }
                };
                return enrichNodes([...nds, newNode]);
            } else if (newCategory === 'IGNORED' && exists) {
                return nds.filter(n => n.id !== assetId);
            }
            return nds.map(n => n.id === assetId ? { ...n, data: { ...n.data, category: newCategory } } : n);
        });

        // Persist to Backend
        try {
            await fetch(`${API_BASE_URL}/assets/${assetId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: newCategory })
            });
        } catch (e) {
            console.error("Failed to persist category change", e);
        }
    }, [assets, setNodes, setAssets, enrichNodes, isReadOnly]);

    const handleMetadataChange = useCallback(async (assetId: string, updates: any) => {
        if (isReadOnly) return;

        // Optimistic UI Update
        setAssets(prev => prev.map(a =>
            a.id === assetId ? { ...a, ...updates } : a
        ));

        // Persist to Backend
        try {
            await fetch(`${API_BASE_URL}/assets/${assetId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });
        } catch (e) {
            console.error("Failed to persist metadata change", e);
        }
    }, [setAssets, isReadOnly]);

    const handleSelectionChange = useCallback(async (assetId: string, isSelected: boolean) => {
        if (isReadOnly) return;

        // Optimistic Update
        setAssets(prev => prev.map(a =>
            a.id === assetId ? { ...a, selected: isSelected } : a
        ));

        // Persist (Batch update or per-check? Current UI does per-check persistence)
        try {
            await fetch(`${API_BASE_URL}/assets/${assetId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ selected: isSelected })
            });
        } catch (e) {
            console.error("Failed to persist selection change", e);
        }
    }, [isReadOnly]);

    const handleSyncGraph = useCallback(async () => {
        if (isReadOnly) return;
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/sync-graph`, {
                method: 'POST'
            });
            if (res.ok) {
                const data = await res.json();
                if (data.nodes) setNodes(enrichNodes(data.nodes));
                if (data.edges) setEdges(data.edges);
            }
        } catch (e) {
            console.error("Failed to sync graph", e);
        }
    }, [projectId, isReadOnly, enrichNodes, setNodes, setEdges]);


    // Initialization
    const fetchProject = useCallback(async () => {
        try {
            // Check Status first
            const statusRes = await fetch(`${API_BASE_URL}/discovery/status/${projectId}`);
            const statusData = await statusRes.json();

            if (statusData.status === 'COMPLETED' || statusData.status === 'TRIAGED' || statusData.status === 'TRIAGE' || statusData.status === 'DRAFTING') {
                const projectRes = await fetch(`${API_BASE_URL}/discovery/project/${projectId}`);
                const projectData = await projectRes.json();
                setAssets(projectData.assets || []);
                setSystemPrompt(projectData.prompt || "");
            }
        } catch (error) {
            console.error("Init error:", error);
        } finally {
            setIsLoading(false);
        }
    }, [projectId]);

    const fetchLayout = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/layout`);
            if (res.ok) {
                const data = await res.json();
                if (data.nodes) setNodes(enrichNodes(data.nodes));
                if (data.edges) setEdges(data.edges);
            }
        } catch (e) {
            console.error("Layout fetch error", e);
        }
    }, [projectId, enrichNodes]);

    useEffect(() => {
        if (projectId && projectId !== 'undefined' && projectId !== '') {
            fetchProject();
            fetchLayout();
        } else {
            setIsLoading(false);
        }
    }, [projectId, fetchProject, fetchLayout]);

    // Update parent stats whenever assets change
    const lastSidebarStatsReported = useRef("");
    useEffect(() => {
        if (onStatsUpdate && assets.length >= 0) {
            const stats = {
                core: assets.filter(a => a.type === 'CORE' || a.category === 'CORE').length,
                ignored: assets.filter(a => a.type === 'IGNORED').length,
                pending: assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT').length
            };
            const statsStr = JSON.stringify(stats);
            if (lastSidebarStatsReported.current !== statsStr) {
                lastSidebarStatsReported.current = statsStr;
                onStatsUpdate(stats);
            }
        }
    }, [assets, onStatsUpdate]);
    // Logic below the useEffect

    // Autosave
    const saveLayout = useCallback(async (nds: any[], eds: any[]) => {
        if (isReadOnly) return; // Block saves in read-only
        try {
            await fetch(`${API_BASE_URL}/projects/${projectId}/layout`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nodes: nds, edges: eds })
            });
        } catch (e) {
            console.error("Autosave failed", e);
        }
    }, [projectId, isReadOnly]);

    const handleSaveContext = useCallback(async (sourcePath: string, notes: string) => {
        setIsSavingContext(true);
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/context`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_path: sourcePath,
                    notes,
                    rules: assetContexts[sourcePath]?.rules || {}
                })
            });
            if (res.ok) {
                setAssetContexts(prev => ({
                    ...prev,
                    [sourcePath]: { ...prev[sourcePath], notes }
                }));
            }
        } catch (e) {
            console.error("Failed to save context", e);
        } finally {
            setIsSavingContext(false);
            setSelectedAssetForContext(null);
        }
    }, [projectId, assetContexts]);

    const onConnect = useCallback((params: any) => {
        if (isReadOnly) return;
        setEdges((eds) => {
            const newEdges = addEdge({ ...params, markerEnd: { type: MarkerType.ArrowClosed } }, eds);
            saveLayout(nodes, newEdges);
            return newEdges;
        });
    }, [setEdges, nodes, saveLayout, isReadOnly]);

    // Graph Drop Logic (if we still enable DnD from somewhere, though less likely without side panel)
    const onDrop = useCallback((event: React.DragEvent) => {
        if (isReadOnly) return;
        event.preventDefault();

        const assetData = event.dataTransfer.getData('application/reactflow');
        if (!assetData || !reactFlowInstance) return;

        try {
            const asset = JSON.parse(assetData);

            // React Flow instance from onInit
            const position = reactFlowInstance.screenToFlowPosition({
                x: event.clientX,
                y: event.clientY,
            });

            const newNode = {
                id: asset.id,
                type: 'custom',
                position,
                data: {
                    label: asset.name,
                    category: asset.type === 'IGNORED' ? 'CORE' : asset.type,
                    complexity: asset.complexity || 'LOW',
                    status: 'pending'
                },
            };

            setNodes((nds) => {
                // Check if already exists to avoid duplicates
                if (nds.some(n => n.id === asset.id)) return nds;
                // Re-apply enrichment with current read-only state
                return nds.concat([{
                    ...newNode,
                    data: { ...newNode.data, onDelete: handleDeleteNode, id: newNode.id, isReadOnly: isReadOnly },
                    draggable: !isReadOnly
                }]);
            });

            // If it was ignored, make it CORE now that it's in the graph
            if (asset.type === 'IGNORED') {
                setAssets(prev => prev.map(a => a.id === asset.id ? { ...a, type: 'CORE' } : a));
            }
        } catch (e) {
            console.error("Drop failed", e);
        }
    }, [reactFlowInstance, setNodes, setAssets, isReadOnly, handleDeleteNode]);

    const onDragOver = useCallback((event: React.DragEvent) => {
        if (isReadOnly) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, [isReadOnly]);

    // Approve Design
    // Approve Design
    const handleApprove = async () => {
        try {
            // 1. Save final layout
            await saveLayout(nodes, edges);

            // 2. Call Approve Endpoint (updates status to DRAFTING)
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (res.ok) {
                // 3. Also update stage for UI stepper consistency (optional if backend does it, but safer here for now)
                await fetch(`${API_BASE_URL}/projects/${projectId}/stage`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ stage: '3' })
                });

                if (onStageChange) onStageChange(3);
            } else {
                console.error("Approve failed", await res.text());
                alert("Error approving design. Please try again.");
            }
        } catch (e) {
            console.error("Failed to approve", e);
            alert("Connection error while approving.");
        }
    };

    const fetchTriageLogs = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/logs?type=triage`);
            const data = await res.json();
            if (data.logs) {
                setTriageLog(data.logs);
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    }, [projectId]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isLoading) {
            // Poll more frequently during active loading
            interval = setInterval(fetchTriageLogs, 2000);
        }
        return () => clearInterval(interval);
    }, [isLoading, fetchTriageLogs]);


    const handleRunTriage = async () => {
        console.log("DEBUG: handleRunTriage called for projectId:", projectId);
        // Confirmation for cost
        const confirmMsg = "This action will run AI agents to analyze the repository. This incurs token costs and processing time.\n\nDo you want to continue?";

        try {
            if (!window.confirm(confirmMsg)) {
                console.log("DEBUG: Triage cancelled by user");
                return;
            }
        } catch (confirmError) {
            console.error("DEBUG: window.confirm error:", confirmError);
        }

        if (!projectId || projectId === 'undefined' || projectId === '') {
            console.error("DEBUG: Invalid projectId in handleRunTriage:", projectId);
            alert("Error: Invalid Project ID. Returning to dashboard...");
            window.location.href = '/dashboard';
            return;
        }

        console.log("DEBUG: Starting Triage process...");
        setIsLoading(true);
        setActiveTab('logs'); // Show logs initially to see progress
        setTriageLog("Initializing Triage Agent..."); // Reset log

        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/triage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    system_prompt: systemPrompt,
                    user_context: userContext
                })
            });
            const data = await res.json();
            console.log("DEBUG: Triage API response received:", data);

            if (data.error) {
                console.error("Triage error from API:", data.error);
                alert(`Analysis error: ${data.error}`);
                if (data.log) setTriageLog(data.log);
                return;
            }

            if (data.assets) {
                setAssets(data.assets);
            }
            if (data.nodes) {
                setNodes(enrichNodes(data.nodes));
            }
            if (data.edges) {
                setEdges(data.edges);
            }
            // data.log is final summary, but we are polling now.
            // We can do one final fetch to be sure.
            await fetchTriageLogs();

        } catch (e) {
            console.error("Triage failed", e);
            alert("Connection error running triage. Please verify backend server is running.");
        } finally {
            console.log("DEBUG: Triage process finished.");
            setIsLoading(false);
        }
    };


    const handleReset = async () => {
        if (!window.confirm("Are you sure you want to reset the project? All triage results and current design will be lost.")) return;

        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/reset`, {
                method: 'POST'
            });
            if (res.ok) {
                setAssets([]);
                setNodes([]);
                setEdges([]);
                setTriageLog("");
                alert("Project reset successfully.");
            }
        } catch (e) {
            console.error("Reset failed", e);
            alert("Error resetting project.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ReactFlowProvider>
            <div className={`flex flex-col h-full bg-[var(--background)] transition-all duration-500 ease-in-out ${isFullscreen ? 'fixed inset-0 z-[100] !h-screen !w-screen' : 'relative'
                }`}>
                <StageHeader
                    title="Stage 2: Structural Triage"
                    subtitle="Asset classification and contextual enrichment"
                    icon={<FileEdit className="text-cyan-500" />}
                    helpText="Define which assets are CORE, SUPPORT or IGNORE. You can inject business context to improve AI precision."
                    onApprove={handleApprove}
                    approveLabel="Approve Design"
                >
                    <div className="flex gap-2">
                        <button
                            onClick={handleRunTriage}
                            disabled={isLoading}
                            className="px-6 py-2.5 bg-primary text-white rounded-xl text-xs font-bold flex items-center gap-2 hover:bg-secondary transition-all shadow-xl shadow-primary/20 disabled:opacity-50"
                        >
                            {isLoading ? <RefreshCw size={14} className="animate-spin" /> : <Activity size={14} />}
                            {isLoading ? "Processing..." : "Run Analysis"}
                        </button>
                        <button
                            onClick={() => saveLayout(nodes, edges)}
                            className="px-6 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-bold flex items-center gap-2 hover:bg-white/10 transition-all"
                        >
                            <Save size={14} /> Save Design
                        </button>
                    </div>
                </StageHeader>

                {/* GRAPH INTELLIGENCE (HEATMAPS) */}
                {/* TODO v4+: Graph Intelligence Heatmaps - Feature incomplete, hidden for now */}
                {/*
                <div className="bg-black/20 border-b border-white/5 px-8 py-2 flex items-center justify-between">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <Activity size={14} className="text-gray-500" />
                            <span className="text-[9px] font-black uppercase tracking-widest text-gray-500">Graph Intelligence</span>
                        </div>
                        <div className="flex bg-white/5 p-1 rounded-lg border border-white/5 gap-1">
                            {[
                                { id: 'none', label: 'Default', icon: <Map size={12} /> },
                                { id: 'pii', label: 'PII Heatmap', icon: <ShieldAlert size={12} /> },
                                { id: 'criticality', label: 'Criticality', icon: <AlertTriangle size={12} /> },
                                { id: 'volume', label: 'Load Volume', icon: <Infinity size={12} /> },
                            ].map(h => (
                                <button
                                    key={h.id}
                                    onClick={() => setActiveHeatmap(h.id as any)}
                                    className={`px-4 py-1.5 rounded-md text-[9px] font-black uppercase tracking-widest flex items-center gap-2 transition-all ${activeHeatmap === h.id ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/20' : 'text-gray-500 hover:text-cyan-500'
                                        }`}
                                >
                                    {h.icon} {h.label}
                                </button>
                            ))}
                        </div>
                    </div>
                    {isLoading && (
                        <div className="flex items-center gap-3">
                            <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping" />
                            <span className="text-[9px] font-bold text-cyan-500 uppercase tracking-widest">Architect Analyzing Flow...</span>
                        </div>
                    )}
                </div>
                */}
                {/* Tab Navigation - Grouped Structure */}
                <div className="flex items-center gap-8 border-b border-gray-100 dark:border-white/5 bg-white dark:bg-[#0a0a0a] px-8 py-3 overflow-x-auto no-scrollbar">
                    {['Views', 'Config'].map(group => (
                        <div key={group} className="flex items-center gap-3">
                            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-[var(--text-tertiary)] vertical-text opacity-50 pl-2">
                                {group}
                            </span>
                            <div className="flex bg-gray-50 dark:bg-black/20 p-1.5 rounded-2xl border border-gray-100 dark:border-white/5">
                                {TABS.filter(t => t.group === group).map(tab => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.15em] transition-all whitespace-nowrap ${activeTab === tab.id
                                            ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/20 active:scale-95'
                                            : 'text-[var(--text-tertiary)] hover:text-cyan-500 hover:bg-cyan-500/5'
                                            }`}
                                    >
                                        <span className={activeTab === tab.id ? 'text-white' : 'text-gray-400'}>{tab.icon}</span>
                                        <span>{tab.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-hidden relative">

                    {/* 1. GRAPH TAB */}
                    {activeTab === 'graph' && (
                        <div className="h-full w-full flex relative">
                            {/* Drag Source Sidebar (Small Grid) */}
                            {!isReadOnly && (
                                <div
                                    className={`h-full border-r border-gray-100 dark:border-white/5 bg-white dark:bg-[#121212]/30 backdrop-blur-md flex flex-col z-20 shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${showSidebar ? 'w-72' : 'w-0'
                                        }`}
                                >
                                    <div className="p-4 border-b border-gray-100 dark:border-white/5 text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--text-tertiary)] bg-gray-50 dark:bg-black/20 flex justify-between items-center whitespace-nowrap">
                                        <span>Available Components</span>
                                        <button
                                            onClick={() => setShowSidebar(false)}
                                            className="p-1 px-2 hover:bg-cyan-500/10 hover:text-cyan-500 rounded-lg transition-colors"
                                            title="Hide Panel"
                                        >
                                            <PanelLeftClose size={16} />
                                        </button>
                                    </div>
                                    <div className="flex-1 overflow-hidden min-w-[288px] custom-scrollbar">
                                        <div className="p-4 border-b border-gray-100 dark:border-white/5">
                                            <DiscoveryDashboard assets={assets} nodes={nodes} />
                                        </div>

                                        {isLoading ? (
                                            <div className="p-12 text-center">
                                                <div className="w-6 h-6 border-2 border-cyan-500 border-b-transparent rounded-full animate-spin mx-auto mb-3" />
                                                <span className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-widest animate-pulse">Scanning...</span>
                                            </div>
                                        ) : (
                                            <div className="overflow-y-auto max-h-[calc(100vh-350px)] p-4 space-y-6">
                                                {/* PENDING REVIEW SECTION */}
                                                {assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT').length > 0 && (
                                                    <div className="space-y-3">
                                                        <h5 className="text-[9px] font-black text-amber-500 uppercase tracking-widest pl-2">
                                                            Pending Review ({assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT').length})
                                                        </h5>
                                                        {assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT').map(asset => (
                                                            <div
                                                                key={asset.id}
                                                                draggable
                                                                onDragStart={(e) => {
                                                                    e.dataTransfer.setData('application/reactflow', JSON.stringify(asset));
                                                                    e.dataTransfer.effectAllowed = 'move';
                                                                }}
                                                                className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl hover:border-amber-500/50 hover:shadow-xl hover:shadow-amber-500/5 cursor-grab flex items-center gap-4 transition-all group scale-100 hover:scale-[1.02] active:scale-95"
                                                            >
                                                                <div className="w-10 h-10 bg-amber-500/20 rounded-xl flex items-center justify-center group-hover:bg-amber-500 group-hover:text-white transition-all">
                                                                    <Activity size={18} className="text-amber-500 group-hover:text-white" />
                                                                </div>
                                                                <div className="flex flex-col min-w-0">
                                                                    <span className="text-sm font-bold truncate text-[var(--text-primary)] group-hover:text-amber-500 transition-colors">{asset.name}</span>
                                                                    <div className="flex items-center gap-1">
                                                                        <span className="text-[9px] font-bold text-amber-600/80 uppercase tracking-tight">Action Required</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}

                                                {/* ALL OTHER ITEMS */}
                                                <div className="space-y-3">
                                                    <h5 className="text-[9px] font-black text-[var(--text-tertiary)] uppercase tracking-widest pl-2">
                                                        Unassigned Items
                                                    </h5>
                                                    {assets.filter(a => false).length === 0 && assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT').length === 0 && (
                                                        <div className="text-center text-gray-400 text-[10px] font-bold uppercase tracking-widest py-10 italic">All items classified</div>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                </div>
                            )}

                            {/* Floating Sidebar Toggle (Only when hidden) */}
                            {!showSidebar && (
                                <button
                                    onClick={() => setShowSidebar(true)}
                                    className="absolute top-6 left-6 z-30 p-3 bg-white/90 dark:bg-[#121212]/90 rounded-2xl border border-gray-100 dark:border-white/10 shadow-2xl backdrop-blur-xl text-cyan-500 hover:scale-110 active:scale-95 transition-all"
                                    title="Show Panel"
                                >
                                    <PanelLeftOpen size={20} />
                                </button>
                            )}

                            {/* Graph Area */}
                            <div className="flex-1 h-full bg-gray-50 dark:bg-[#0a0a0a] relative" ref={setReactFlowInstance}>
                                <MeshGraph
                                    nodes={nodes}
                                    edges={edges}
                                    onNodesChange={onNodesChange}
                                    onEdgesChange={onEdgesChange}
                                    onConnect={onConnect}
                                    onInit={setReactFlowInstance}
                                    onDrop={onDrop}
                                    onDragOver={onDragOver}
                                    onNodeClick={(node) => setSelectedNodeData(node.data)}
                                    onNodeDragStop={(_: any, __: any, allNodes: any[]) => {
                                        if (allNodes) saveLayout(allNodes, edges);
                                        else saveLayout(nodes, edges);
                                    }}
                                    onNodesDelete={(deletedNodes: any[]) => {
                                        const deletedIds = deletedNodes.map((n: any) => n.id);
                                        setAssets(prev => prev.map(a => deletedIds.includes(a.id) ? { ...a, type: 'IGNORED' } : a));
                                    }}
                                />

                                {/* HIGH-RES DETAIL PANEL */}
                                {selectedNodeData && (
                                    <div className="absolute top-6 bottom-6 right-6 w-96 bg-white/95 dark:bg-[#121212]/95 backdrop-blur-2xl border border-white/10 rounded-3xl shadow-2xl z-50 flex flex-col overflow-hidden animate-in slide-in-from-right duration-300">
                                        <div className="p-6 border-b border-white/5 flex items-center justify-between bg-white/5">
                                            <div className="flex items-center gap-3">
                                                <Activity size={18} className="text-cyan-500" />
                                                <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[var(--text-primary)]">Asset Intelligence</h3>
                                            </div>
                                            <button
                                                onClick={() => setSelectedNodeData(null)}
                                                className="p-2 hover:bg-white/10 rounded-xl text-gray-400 font-bold text-[10px] uppercase"
                                            >
                                                Close
                                            </button>
                                        </div>

                                        <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar-slim">
                                            {/* Header Info */}
                                            <div>
                                                <span className="text-[10px] font-black text-cyan-600 uppercase tracking-widest">{selectedNodeData.category}</span>
                                                <h2 className="text-xl font-bold text-[var(--text-primary)] mt-1 break-all">{selectedNodeData.label}</h2>
                                                <p className="text-xs text-[var(--text-tertiary)] font-medium mt-2">{selectedNodeData.id}</p>
                                            </div>

                                            {/* Metadata Grid */}
                                            <div className="grid grid-cols-2 gap-4">
                                                {[
                                                    { label: 'Volume', value: selectedNodeData.metadata?.volume || 'LOW', color: 'text-emerald-500' },
                                                    { label: 'Latency', value: selectedNodeData.metadata?.latency || 'BATCH', color: 'text-cyan-500' },
                                                    { label: 'Criticality', value: selectedNodeData.metadata?.criticality || 'P3', color: 'text-amber-500' },
                                                    { label: 'Lineage', value: selectedNodeData.metadata?.lineage_group || 'Bronze', color: 'text-purple-500' },
                                                ].map(m => (
                                                    <div key={m.label} className="p-4 bg-white/5 rounded-2xl border border-white/5">
                                                        <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest block mb-1">{m.label}</span>
                                                        <span className={`text-xs font-black uppercase ${m.color}`}>{m.value}</span>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Design Decisions */}
                                            <div className="space-y-4">
                                                <div className="p-5 bg-black/40 border border-white/5 rounded-2xl">
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <ShieldCheck size={14} className="text-emerald-500" />
                                                        <span className="text-[10px] font-black text-white uppercase tracking-widest">Architect Suggestion</span>
                                                    </div>
                                                    <div className="space-y-4">
                                                        <div>
                                                            <span className="text-[9px] font-bold text-gray-600 uppercase">Target Name:</span>
                                                            <p className="text-xs font-mono text-cyan-500 mt-1">{selectedNodeData.target_name || 'N/A'}</p>
                                                        </div>
                                                        <div>
                                                            <span className="text-[9px] font-bold text-gray-600 uppercase">Partition Strategy:</span>
                                                            <p className="text-xs font-bold text-white mt-1">{selectedNodeData.metadata?.partition_key || 'No partitioning suggested'}</p>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="p-5 bg-black/40 border border-white/5 rounded-2xl">
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <Zap size={14} className="text-amber-500" />
                                                        <span className="text-[10px] font-black text-white uppercase tracking-widest">Actionable Intel</span>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <div className={`w-3 h-3 rounded-full ${selectedNodeData.metadata?.is_pii ? 'bg-red-500' : 'bg-gray-700'}`} />
                                                        <span className="text-[10px] font-bold text-gray-400 uppercase">
                                                            PII Content: {selectedNodeData.metadata?.is_pii ? 'YES (High Risk)' : 'NO (Clean)'}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                {nodes.length === 0 && (
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                        <div className="bg-white/80 dark:bg-black/40 p-8 rounded-3xl border border-dashed border-gray-200 dark:border-white/10 text-center backdrop-blur-sm">
                                            <div className="w-16 h-16 bg-cyan-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                                <Expand className="text-cyan-500" size={32} />
                                            </div>
                                            <h4 className="text-lg font-bold mb-1">Empty Canvas</h4>
                                            <p className="text-sm text-[var(--text-tertiary)]">Drag components from the left to orchestrate resolution.</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* 2. GRID TAB */}
                    {activeTab === 'grid' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-[var(--background)]">
                            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-[var(--text-primary)]">
                                <List className="text-blue-500" /> Package Inventory
                            </h2>
                            <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] shadow-sm overflow-hidden">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-[var(--background)] text-[var(--text-secondary)] uppercase text-sm">
                                        <tr>
                                            <th className="px-6 py-4">Source</th>
                                            <th className="px-6 py-4">Target Name</th>
                                            <th className="px-6 py-4">Entity</th>
                                            <th className="px-6 py-4">Sovereignty</th>
                                            <th className="px-6 py-4">Strategy</th>
                                            <th className="px-6 py-4">Type</th>
                                            <th className="px-6 py-4 text-center">Include</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[var(--border)] text-[var(--text-primary)]">
                                        {assets.map(asset => (
                                            <tr key={asset.id} className="hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors">
                                                <td className="px-6 py-4 font-medium group">
                                                    <div className="flex items-center gap-2">
                                                        <div className="truncate max-w-[150px]" title={asset.name}>
                                                            {asset.name}
                                                        </div>
                                                        {assetContexts[asset.id]?.notes && (
                                                            <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse shrink-0" title="Tiene notas de negocio" />
                                                        )}
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setEditingAsset(asset);
                                                                setAssetNote(asset.business_notes || '');
                                                            }}
                                                            className="p-1 px-2 bg-white/5 hover:bg-white/10 rounded-md text-gray-500 hover:text-white transition-all order-2"
                                                            title="Edit business notes"
                                                        >
                                                            <div className="flex items-center gap-1">
                                                                <FileEdit size={10} />
                                                                <span className="text-[10px] uppercase font-black">Edit</span>
                                                            </div>
                                                        </button>
                                                        <button
                                                            onClick={() => {
                                                                setSelectedAssetForContext(asset.id);
                                                                setActiveTab('mapping');
                                                            }}
                                                            className="p-1 text-gray-400 hover:text-primary transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                                                            title="Column Mapping"
                                                        >
                                                            <Database size={12} />
                                                        </button>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <input
                                                        type="text"
                                                        value={asset.target_name || ''}
                                                        placeholder={asset.name.split('.')[0].toLowerCase()}
                                                        onChange={(e) => handleMetadataChange(asset.id, { target_name: e.target.value })}
                                                        className="bg-transparent border-b border-gray-200 dark:border-gray-800 text-[11px] focus:border-primary focus:ring-0 w-full transition-colors"
                                                    />
                                                </td>
                                                <td className="px-6 py-4">
                                                    <input
                                                        type="text"
                                                        value={asset.business_entity || ''}
                                                        placeholder="e.g. CUSTOMER"
                                                        onChange={(e) => handleMetadataChange(asset.id, { business_entity: e.target.value.toUpperCase() })}
                                                        className="bg-gray-50 dark:bg-gray-900 border-none rounded px-2 py-1 text-xs font-bold uppercase focus:ring-1 focus:ring-primary w-24 transition-all"
                                                    />
                                                </td>
                                                <td className="px-6 py-4">
                                                    <button
                                                        onClick={() => handleMetadataChange(asset.id, { is_pii: !asset.is_pii })}
                                                        className={`p-1.5 rounded-lg transition-all flex items-center gap-2 ${asset.is_pii
                                                            ? 'bg-red-50 text-red-600 border border-red-100 animate-pulse'
                                                            : 'text-gray-300 hover:text-gray-500 hover:bg-gray-100'
                                                            }`}
                                                        title={asset.is_pii ? "PII Detected" : "Mark as PII"}
                                                    >
                                                        {asset.is_pii ? <ShieldAlert size={14} /> : <Shield size={14} />}
                                                        {asset.is_pii && <span className="text-xs font-bold">PII</span>}
                                                    </button>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-1">
                                                        <select
                                                            value={asset.load_strategy || 'FULL_OVERWRITE'}
                                                            onChange={(e) => handleMetadataChange(asset.id, { load_strategy: e.target.value })}
                                                            className={`text-xs font-bold uppercase rounded px-1.5 py-0.5 border-none focus:ring-1 focus:ring-primary w-24 cursor-pointer ${asset.load_strategy === 'INCREMENTAL' ? 'bg-blue-100 text-blue-700' :
                                                                asset.load_strategy === 'SCD_2' ? 'bg-indigo-100 text-indigo-700' :
                                                                    'bg-gray-100 text-gray-600'
                                                                }`}
                                                        >
                                                            <option value="FULL_OVERWRITE">FULL</option>
                                                            <option value="INCREMENTAL">INCREMENTAL</option>
                                                            <option value="SCD_2">SCD TYPE 2</option>
                                                        </select>
                                                        <div className="flex items-center gap-1 text-xs text-gray-400 font-mono">
                                                            <Clock size={8} /> {asset.frequency || 'DAILY'}
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <select
                                                        value={asset.type}
                                                        onChange={(e) => handleCategoryChange(asset.id, e.target.value)}
                                                        className={`text-xs font-bold uppercase rounded-md border border-[var(--border)] px-2 py-1 focus:ring-2 focus:ring-blue-500 cursor-pointer transition-colors ${asset.type === 'CORE' ? 'bg-blue-500/10 text-blue-600' :
                                                            asset.type === 'SUPPORT' ? 'bg-purple-500/10 text-purple-600' :
                                                                'bg-[var(--background)] text-[var(--text-secondary)]'
                                                            }`}
                                                    >
                                                        <option value="CORE">CORE</option>
                                                        <option value="SUPPORT">SUPPORT</option>
                                                        <option value="IGNORED">IGNORED</option>
                                                        <option value="OTHER">OTHER</option>
                                                    </select>
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    <input
                                                        type="checkbox"
                                                        checked={asset.selected || false}
                                                        onChange={(e) => handleSelectionChange(asset.id, e.target.checked)}
                                                        className="w-4 h-4 text-primary rounded border-gray-300 focus:ring-primary cursor-pointer transition-all"
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                        {assets.length === 0 && (
                                            <tr>
                                                <td colSpan={7} className="px-6 py-8 text-center text-gray-400">
                                                    No assets found.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}


                    {/* 3. MAPPING TAB */}
                    {activeTab === 'mapping' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-[var(--background-secondary)]">
                            <div className="max-w-7xl mx-auto space-y-6">
                                <div className="flex justify-between items-center mb-4">
                                    <div>
                                        <h2 className="text-2xl font-black flex items-center gap-3">
                                            <div className="p-2 bg-primary/10 rounded-xl">
                                                <Database className="text-primary" size={24} />
                                            </div>
                                            Granular Column Mapping
                                        </h2>
                                        <p className="text-sm text-[var(--text-secondary)] mt-1">
                                            Define transformations, data types, and security tags (PII) for each column.
                                        </p>
                                    </div>
                                </div>

                                {selectedAssetForContext ? (
                                    <div className="card-glass border-[var(--primary)]/20 shadow-2xl">
                                        <ColumnMappingEditor assetId={selectedAssetForContext} />
                                    </div>
                                ) : (
                                    <div className="card-glass flex flex-col items-center justify-center py-20 text-center border-dashed border-2">
                                        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full mb-4">
                                            <Layout size={40} className="text-gray-400" />
                                        </div>
                                        <h3 className="text-lg font-bold">No Asset Selected</h3>
                                        <p className="text-sm text-gray-500 max-w-sm mt-2">
                                            Select an asset from the Grid or Graph to edit its column mapping.
                                        </p>
                                        <button
                                            onClick={() => setActiveTab('grid')}
                                            className="mt-6 px-4 py-2 bg-primary text-white rounded-lg font-bold text-xs shadow-lg shadow-primary/20"
                                        >
                                            Go to Grid
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* 4. PROMPT TAB */}
                    {activeTab === 'prompt' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-[var(--background-secondary)]">
                            <div className="max-w-7xl mx-auto space-y-6">
                                <div className="flex items-center justify-between mb-8">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2.5 bg-cyan-500/10 rounded-2xl text-cyan-500 border border-cyan-500/20">
                                            <Zap size={20} />
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-black text-white uppercase tracking-wider">GLOBAL BUSINESS CONTEXT</h3>
                                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">AI Instruction Overrides</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleRunTriage}
                                        className="flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/20 text-primary rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-primary/20 transition-all"
                                    >
                                        <Play size={16} /> Re-Run Triage
                                    </button>
                                </div>

                                <div className="card-glass overflow-hidden p-0 border-none shadow-2xl h-[700px]">
                                    <PromptsExplorer
                                        projectId={projectId}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 4. USER INPUT TAB */}
                    {activeTab === 'context' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-gray-50 dark:bg-gray-950">
                            <div className="max-w-7xl mx-auto space-y-10">
                                {/* Global Context */}
                                <div className="space-y-6">
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        <MessageSquare className="text-primary" /> Global Project Context
                                    </h2>
                                    <p className="text-sm text-gray-500">
                                        Provide general rules that the agent must apply to the whole project (e.g., "Use CamelCase", "Ignore QA schemas").
                                    </p>
                                    <textarea
                                        value={userContext}
                                        onChange={(e) => setUserContext(e.target.value)}
                                        placeholder="e.g. Ignore audit tables, prioritize Sales packages, use 'stg_' prefix..."
                                        className="w-full h-40 p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-sm leading-relaxed focus:ring-2 focus:ring-primary outline-none shadow-sm"
                                    />
                                    <div className="flex justify-end">
                                        <button
                                            onClick={() => handleSaveContext('__global__', userContext)}
                                            className="px-6 py-2 bg-primary text-white rounded-lg font-bold hover:bg-secondary transition-colors flex items-center gap-2"
                                            disabled={isSavingContext}
                                        >
                                            <Save size={16} /> {isSavingContext ? 'Saving...' : 'Save Global Context'}
                                        </button>
                                    </div>
                                </div>

                                <hr className="border-gray-200 dark:border-gray-800" />

                                {/* Virtual Step Builder */}
                                {/* Virtual Step Builder */}
                                <div className="space-y-6 pb-20">
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        <RotateCcw className="text-primary" /> Virtual Step Builder
                                    </h2>
                                    <p className="text-sm text-gray-500">
                                        Create manual nodes for processes not in the code. The Agent will logically connect them upon re-triage.
                                    </p>

                                    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <label className="text-sm font-bold text-gray-400 uppercase">Step Name</label>
                                                <input id="v-step-name" type="text" placeholder="e.g. Manual Validation" className="w-full p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-bold text-gray-400 uppercase">Depends On (Path)</label>
                                                <input id="v-step-dep" type="text" placeholder="e.g. schema/table.sql" className="w-full p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-gray-400 uppercase">Agent Instructions</label>
                                            <textarea id="v-step-desc" placeholder="Describe what this step does and how it connects..." className="w-full h-24 p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
                                        </div>
                                        <div className="flex justify-end">
                                            <button
                                                onClick={() => {
                                                    const name = (document.getElementById('v-step-name') as HTMLInputElement).value;
                                                    const dep = (document.getElementById('v-step-dep') as HTMLInputElement).value;
                                                    const desc = (document.getElementById('v-step-desc') as HTMLTextAreaElement).value;
                                                    const virtualId = `virtual_${name.toLowerCase().replace(/\s+/g, '_')}`;
                                                    const fullNotes = `VIRTUAL_STEP: ${name}\nDEPENDENCY: ${dep}\nINSTRUCTIONS: ${desc}`;
                                                    handleSaveContext(virtualId, fullNotes);
                                                }}
                                                className="px-6 py-2 bg-gray-900 text-white dark:bg-primary dark:text-white rounded-lg font-bold hover:bg-black transition-colors"
                                                disabled={isSavingContext}
                                            >
                                                + Add Step to Mesh
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 5. LOGS TAB */}
                    {activeTab === 'logs' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-gray-950 text-gray-300 font-mono text-sm leading-relaxed">
                            <div className="max-w-5xl mx-auto">
                                <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-white">
                                    <FileText className="text-primary" /> Agent Execution Log
                                </h2>
                                <div className="bg-black/50 p-6 rounded-xl border border-gray-800 shadow-inner whitespace-pre-wrap">
                                    {triageLog}
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            </div>

            {/* Release 1.1: Context Sidebar Overlay */}
            {
                selectedAssetForContext && (
                    <div className="fixed inset-0 bg-black/50 z-50 flex justify-end">
                        <div className="w-96 bg-white dark:bg-gray-900 h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
                            <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
                                <div>
                                    <h3 className="font-bold text-lg dark:text-white">Business Context</h3>
                                    <p className="text-sm text-gray-500 truncate w-64">
                                        {assets.find(a => a.id === selectedAssetForContext)?.name || 'Asset'}
                                    </p>
                                </div>
                                <button onClick={() => setSelectedAssetForContext(null)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                                    <PanelLeftClose size={20} />
                                </button>
                            </div>

                            <div className="flex-1 p-6 space-y-6 overflow-y-auto">
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-400 uppercase">Description / Notes</label>
                                    <textarea
                                        className="w-full h-48 p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Add specific rules for this file..."
                                        defaultValue={assetContexts[selectedAssetForContext]?.notes || ''}
                                        id="context-notes"
                                    />
                                </div>

                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-gray-400 uppercase">Suggested Rules</label>
                                    <div className="space-y-2">
                                        <label className="flex items-center gap-2 text-sm cursor-pointer">
                                            <input type="checkbox" className="rounded" defaultChecked={assetContexts[selectedAssetForContext]?.rules?.ignore_duplicates} id="rule-dedup" />
                                            <span>Ignore Duplicates</span>
                                        </label>
                                        <label className="flex items-center gap-2 text-sm cursor-pointer">
                                            <input type="checkbox" className="rounded" defaultChecked={assetContexts[selectedAssetForContext]?.rules?.strict_types} id="rule-types" />
                                            <span>Strict Types</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <div className="p-6 border-t border-gray-100 dark:border-gray-800 grid grid-cols-2 gap-3">
                                <button
                                    onClick={() => setSelectedAssetForContext(null)}
                                    className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg font-bold text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => {
                                        const notes = (document.getElementById('context-notes') as HTMLTextAreaElement).value;
                                        const rules = {
                                            ignore_duplicates: (document.getElementById('rule-dedup') as HTMLInputElement).checked,
                                            strict_types: (document.getElementById('rule-types') as HTMLInputElement).checked,
                                        };
                                        // Local state update first
                                        setAssetContexts(prev => ({
                                            ...prev,
                                            [selectedAssetForContext]: { notes, rules }
                                        }));
                                        // Save to backend
                                        handleSaveContext(selectedAssetForContext, notes);
                                    }}
                                    className="px-4 py-2 bg-primary text-white rounded-lg font-bold text-sm flex items-center justify-center gap-2"
                                    disabled={isSavingContext}
                                >
                                    {isSavingContext ? 'Saving...' : <><Save size={16} /> Save</>}
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
        </ReactFlowProvider >
    );
}
