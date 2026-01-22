"use client";
import { useState, useCallback, useRef, useEffect } from 'react';
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
import { Map, CheckCircle, Layout, List, Terminal, MessageSquare, Play, FileText, RotateCcw, PanelLeftClose, PanelLeftOpen, Expand, Shrink, Save, ShieldCheck, AlertTriangle, Shield, ShieldAlert, Zap, Clock, Database, Infinity } from 'lucide-react';
import DiscoveryDashboard from '../DiscoveryDashboard';
import { API_BASE_URL } from '../../lib/config';

// Tab Definitions
const TABS = [
    { id: 'graph', label: 'Gráfico', icon: <Layout size={18} /> },
    { id: 'grid', label: 'Grilla', icon: <List size={18} /> },
    { id: 'prompt', label: 'Refine Prompt', icon: <Terminal size={18} /> },
    { id: 'context', label: 'User Input', icon: <MessageSquare size={18} /> },
    { id: 'logs', label: 'Logs', icon: <FileText size={18} /> },
];

export default function TriageView({ projectId, onStageChange, isReadOnly: propReadOnly }: { projectId: string, onStageChange?: (stage: number) => void, isReadOnly?: boolean }) {
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

    // DnD (Keep for Graph Tab logic if needed, though split pane is gone)
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

    const [showSidebar, setShowSidebar] = useState(true);

    // Release 1.1: Context State
    const [assetContexts, setAssetContexts] = useState<Record<string, { notes: string, rules: any }>>({});
    const [selectedAssetForContext, setSelectedAssetForContext] = useState<any | null>(null);
    const [isSavingContext, setIsSavingContext] = useState(false);

    const handleDeleteNode = useCallback((id: string) => {
        if (isReadOnly) return;
        setNodes(nds => nds.filter(n => n.id !== id));
        setAssets(prev => prev.map(a => a.id === id ? { ...a, type: 'IGNORED' } : a));
    }, [setNodes, setAssets, isReadOnly]);

    const enrichNodes = useCallback((nds: any[]) => {
        return nds.map(n => ({
            ...n,
            data: {
                ...n.data,
                onDelete: handleDeleteNode,
                id: n.id,
                isReadOnly: isReadOnly // Pass readOnly to node
            },
            draggable: !isReadOnly, // Disable dragging
            selectable: !isReadOnly,
            deletable: !isReadOnly
        }));
    }, [handleDeleteNode, isReadOnly]);

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
        if (projectId) {
            fetchProject();
            fetchLayout();
        }
    }, [projectId, fetchProject, fetchLayout]);
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
                    body: JSON.stringify({ stage: '2' })
                });

                if (onStageChange) onStageChange(2);
            } else {
                console.error("Approve failed", await res.text());
                alert("Error al aprobar el diseño. Intente nuevamente.");
            }
        } catch (e) {
            console.error("Failed to approve", e);
            alert("Error de conexión al aprobar.");
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


    const handleReTriage = async () => {
        // Confirmation for cost
        const confirmMsg = "Esta acción ejecutará agentes de IA para analizar el repositorio. Esto incurre en costos de tokens y tiempo de procesamiento.\n\n¿Deseas continuar?";
        if (!window.confirm(confirmMsg)) return;

        if (!projectId || projectId === 'undefined') {
            alert("Error: ID de proyecto inválido. Volviendo al dashboard...");
            window.location.href = '/dashboard';
            return;
        }

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
            alert("Error al ejecutar el triaje");
        } finally {
            setIsLoading(false);
        }
    };


    const handleReset = async () => {
        if (!window.confirm("¿Estás seguro de que deseas limpiar el proyecto? Se eliminarán todos los resultados del triaje y el diseño actual.")) return;

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
                alert("Proyecto reiniciado correctamente.");
            }
        } catch (e) {
            console.error("Reset failed", e);
            alert("Error al reiniciar el proyecto.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ReactFlowProvider>
            <div className={`flex flex-col h-full bg-[var(--background)] transition-all duration-500 ease-in-out ${isFullscreen ? 'fixed inset-0 z-[100] !h-screen !w-screen' : 'relative'
                }`}>
                <StageHeader
                    title="Análisis & Triaje"
                    subtitle="Escaneo de código legado y definición de malla operativa"
                    icon={<Map className="text-primary" />}
                    isReadOnly={isReadOnly}
                    onApprove={handleApprove}
                    approveLabel="Aprobar Diseño"
                    isExecuting={isLoading}
                    onRestart={handleReset}
                >
                    <button
                        onClick={handleReTriage}
                        disabled={isReadOnly || isLoading}
                        className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${isReadOnly ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-primary hover:bg-primary/90 text-white shadow-blue-200 dark:shadow-none'
                            }`}
                    >
                        <Play size={12} className={isLoading ? "animate-spin" : ""} />
                        {isLoading ? "Procesando..." : "Ejecutar Análisis"}
                    </button>
                    <button
                        onClick={async () => {
                            await saveLayout(nodes, edges);
                            if (activeTab === 'grid') await handleSyncGraph();
                        }}
                        disabled={isReadOnly}
                        className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all border ${isReadOnly
                            ? 'bg-gray-50 text-gray-400 border-gray-100 cursor-not-allowed hidden'
                            : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'
                            }`}
                    >
                        <Save size={12} /> Guardar
                    </button>
                </StageHeader>

                {/* Tab Navigation */}
                <div className="flex border-b border-[var(--border)] bg-[var(--surface)] px-4">
                    {TABS.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-6 py-4 text-xs font-bold border-b-2 transition-colors ${activeTab === tab.id
                                ? 'border-primary text-primary bg-primary/5 font-bold'
                                : 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-gray-200'
                                }`}
                        >
                            {tab.icon}
                            <span>{tab.label}</span>
                        </button>
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
                                    className={`h-full border-r border-[var(--border)] bg-[var(--surface)] flex flex-col z-20 shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${showSidebar ? 'w-64' : 'w-0'
                                        }`}
                                >
                                    <div className="p-3 border-b border-[var(--border)] text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)] bg-[var(--background)] flex justify-between items-center whitespace-nowrap">
                                        <span>Activos</span>
                                        <button
                                            onClick={() => setShowSidebar(false)}
                                            className="p-1 hover:bg-[var(--text-primary)]/10 rounded transition-colors"
                                            title="Ocultar Panel"
                                        >
                                            <PanelLeftClose size={14} />
                                        </button>
                                    </div>
                                    <div className="flex-1 overflow-hidden min-w-[256px] custom-scrollbar">
                                        <div className="p-4 border-b border-[var(--border)]">
                                            <DiscoveryDashboard assets={assets} nodes={nodes} />
                                        </div>

                                        {isLoading ? (
                                            <div className="p-4 text-center text-gray-400 text-sm">Cargando...</div>
                                        ) : (
                                            <div className="overflow-y-auto max-h-[calc(100vh-350px)] p-3 space-y-2">
                                                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest px-1 mb-2">Available Components</h4>
                                                {assets.map(asset => (
                                                    <div
                                                        key={asset.id}
                                                        draggable
                                                        onDragStart={(e) => {
                                                            e.dataTransfer.setData('application/reactflow', JSON.stringify(asset));
                                                            e.dataTransfer.effectAllowed = 'move';
                                                        }}
                                                        className="p-3 text-sm bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl hover:border-primary/50 hover:shadow-md cursor-grab flex items-center gap-3 transition-all group"
                                                    >
                                                        <div className="p-1.5 bg-gray-50 dark:bg-gray-950 rounded-lg group-hover:bg-primary/10 transition-colors">
                                                            <Layout size={14} className="text-gray-400 group-hover:text-primary" />
                                                        </div>
                                                        <div className="flex flex-col min-w-0">
                                                            <span className="font-bold truncate text-gray-700 dark:text-gray-200">{asset.name}</span>
                                                            <span className="text-xs text-gray-400 uppercase">{asset.complexity || 'Low'} Complexity</span>
                                                        </div>
                                                    </div>
                                                ))}
                                                {assets.length === 0 && <div className="text-center text-gray-400 text-sm py-10 italic">No assets found in manifest</div>}
                                            </div>
                                        )}
                                    </div>

                                </div>
                            )}

                            {/* Floating Sidebar Toggle (Only when hidden) */}
                            {!showSidebar && (
                                <button
                                    onClick={() => setShowSidebar(true)}
                                    className="absolute top-4 left-4 z-30 p-2 bg-white/80 dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700 shadow-md backdrop-blur-md text-gray-500 hover:text-primary transition-all"
                                    title="Mostrar Panel"
                                >
                                    <PanelLeftOpen size={18} />
                                </button>
                            )}

                            {/* Graph Area */}
                            <div className="flex-1 h-full bg-gray-100 dark:bg-gray-900 relative" ref={setReactFlowInstance}>
                                <MeshGraph
                                    nodes={nodes}
                                    edges={edges}
                                    onNodesChange={onNodesChange}
                                    onEdgesChange={onEdgesChange}
                                    onConnect={onConnect}
                                    onInit={setReactFlowInstance}
                                    onDrop={onDrop}
                                    onDragOver={onDragOver}
                                    onNodeDragStop={(_: any, __: any, allNodes: any[]) => {
                                        // Auto-save on drag stop
                                        if (allNodes) {
                                            saveLayout(allNodes, edges);
                                        } else {
                                            // Fallback if third arg is missing/lazy
                                            saveLayout(nodes, edges);
                                        }
                                    }}
                                    onNodesDelete={(deletedNodes: any[]) => {
                                        const deletedIds = deletedNodes.map((n: any) => n.id);
                                        setAssets(prev => prev.map(a => deletedIds.includes(a.id) ? { ...a, type: 'IGNORED' } : a));
                                    }}

                                />
                                {nodes.length === 0 && (
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                        <div className="bg-white/80 dark:bg-black/50 p-6 rounded-xl border border-dashed border-gray-300 text-center">
                                            <p className="text-gray-500 text-sm">Arrastra paquetes desde la izquierda.</p>
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
                                <List className="text-blue-500" /> Inventario de Paquetes
                            </h2>
                            <div className="bg-[var(--surface)] rounded-xl border border-[var(--border)] shadow-sm overflow-hidden">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-[var(--background)] text-[var(--text-secondary)] uppercase text-sm">
                                        <tr>
                                            <th className="px-6 py-4">Origen</th>
                                            <th className="px-6 py-4">Nombre Destino</th>
                                            <th className="px-6 py-4">Entidad</th>
                                            <th className="px-6 py-4">Soberanía</th>
                                            <th className="px-6 py-4">Estrategia</th>
                                            <th className="px-6 py-4">Tipo</th>
                                            <th className="px-6 py-4 text-center">Incluir</th>
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
                                                            onClick={() => setSelectedAssetForContext(asset.id)}
                                                            className="p-1 text-gray-400 hover:text-primary transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                                                            title="Editar notas de negocio"
                                                        >
                                                            <MessageSquare size={12} />
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
                                                        title={asset.is_pii ? "PII Detectado" : "Marcar como PII"}
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
                                                        <option value="SUPPORT">SOPORTE</option>
                                                        <option value="IGNORED">IGNORADO</option>
                                                        <option value="OTHER">OTRO</option>
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
                                                    No se encontraron activos.
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}


                    {/* 3. PROMPT TAB */}
                    {activeTab === 'prompt' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-gray-50 dark:bg-gray-950">
                            <div className="max-w-7xl mx-auto space-y-6">
                                <div className="flex justify-between items-center">
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        <Terminal className="text-primary" /> System Prompt
                                    </h2>
                                    <button
                                        onClick={handleReTriage}
                                        className="bg-primary text-white px-4 py-2 rounded-lg font-bold hover:bg-secondary flex items-center gap-2"
                                    >
                                        <Play size={16} /> Re-Ejecutar Triaje
                                    </button>
                                </div>
                                <p className="text-sm text-gray-500">
                                    Edita el prompt del sistema utilizado por el Agente de Triaje para clasificar y organizar los paquetes.
                                </p>
                                <textarea
                                    value={systemPrompt}
                                    onChange={(e) => setSystemPrompt(e.target.value)}
                                    className="w-full h-96 p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 font-mono text-sm leading-relaxed focus:ring-2 focus:ring-primary outline-none shadow-sm"
                                />
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
                                        <MessageSquare className="text-primary" /> Contexto Global del Proyecto
                                    </h2>
                                    <p className="text-sm text-gray-500">
                                        Proporciona reglas generales que el agente debe aplicar a todo el proyecto (ej: "Usar CamelCase", "Ignorar esquemas de QA").
                                    </p>
                                    <textarea
                                        value={userContext}
                                        onChange={(e) => setUserContext(e.target.value)}
                                        placeholder="Ej: Ignorar tablas de auditoría, priorizar paquetes de Ventas, usar prefijo 'stg_' para tablas staging..."
                                        className="w-full h-40 p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-sm leading-relaxed focus:ring-2 focus:ring-primary outline-none shadow-sm"
                                    />
                                    <div className="flex justify-end">
                                        <button
                                            onClick={() => handleSaveContext('__global__', userContext)}
                                            className="px-6 py-2 bg-primary text-white rounded-lg font-bold hover:bg-secondary transition-colors flex items-center gap-2"
                                            disabled={isSavingContext}
                                        >
                                            <Save size={16} /> {isSavingContext ? 'Guardando...' : 'Guardar Contexto Global'}
                                        </button>
                                    </div>
                                </div>

                                <hr className="border-gray-200 dark:border-gray-800" />

                                {/* Virtual Step Builder */}
                                <div className="space-y-6 pb-20">
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        <RotateCcw className="text-primary" /> Constructor de Pasos Virtuales
                                    </h2>
                                    <p className="text-sm text-gray-500">
                                        Crea nodos manuales para procesos que no están en el código. El Agente los conectará lógicamente al re-ejecutar el triaje.
                                    </p>

                                    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <label className="text-sm font-bold text-gray-400 uppercase">Nombre del Paso</label>
                                                <input id="v-step-name" type="text" placeholder="Ej: Validación Manual" className="w-full p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-bold text-gray-400 uppercase">Depende de (Path)</label>
                                                <input id="v-step-dep" type="text" placeholder="Ej: schema/table.sql" className="w-full p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-gray-400 uppercase">Instrucciones para el Agente</label>
                                            <textarea id="v-step-desc" placeholder="Describe qué hace este paso y cómo se conecta..." className="w-full h-24 p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
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
                                                + Añadir Paso al Mesh
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
                                    <FileText className="text-primary" /> Log de Ejecución del Agente
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
            {selectedAssetForContext && (
                <div className="fixed inset-0 bg-black/50 z-50 flex justify-end">
                    <div className="w-96 bg-white dark:bg-gray-900 h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
                        <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
                            <div>
                                <h3 className="font-bold text-lg dark:text-white">Contexto de Negocio</h3>
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
                                <label className="text-sm font-bold text-gray-400 uppercase">Descripción / Notas</label>
                                <textarea
                                    className="w-full h-48 p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary"
                                    placeholder="Indica reglas específicas para este archivo..."
                                    defaultValue={assetContexts[selectedAssetForContext]?.notes || ''}
                                    id="context-notes"
                                />
                            </div>

                            <div className="space-y-4">
                                <label className="text-sm font-bold text-gray-400 uppercase">Reglas Sugeridas</label>
                                <div className="space-y-2">
                                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                                        <input type="checkbox" className="rounded" defaultChecked={assetContexts[selectedAssetForContext]?.rules?.ignore_duplicates} id="rule-dedup" />
                                        <span>Ignorar Duplicados</span>
                                    </label>
                                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                                        <input type="checkbox" className="rounded" defaultChecked={assetContexts[selectedAssetForContext]?.rules?.strict_types} id="rule-types" />
                                        <span>Tipado Estricto</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-gray-100 dark:border-gray-800 grid grid-cols-2 gap-3">
                            <button
                                onClick={() => setSelectedAssetForContext(null)}
                                className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg font-bold text-sm"
                            >
                                Cancelar
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
                                {isSavingContext ? 'Guardando...' : <><Save size={16} /> Guardar</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </ReactFlowProvider>
    );
}
