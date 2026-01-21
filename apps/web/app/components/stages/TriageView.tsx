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
import { CheckCircle, Layout, List, Terminal, MessageSquare, Play, FileText, RotateCcw, PanelLeftClose, PanelLeftOpen, Expand, Shrink, Save, ShieldCheck, AlertTriangle, Shield, ShieldAlert, Zap, Clock, Database, Infinity } from 'lucide-react';

import DiscoveryDashboard from '../DiscoveryDashboard';

import { API_BASE_URL } from '../../lib/config';

// Tab Definitions
const TABS = [
    { id: 'graph', label: 'Gráfico', icon: <Layout size={18} /> },
    { id: 'grid', label: 'Grilla', icon: <List size={18} /> },
    { id: 'prompt', label: 'Refine Prompt', icon: <Terminal size={18} /> },
    { id: 'context', label: 'User Input', icon: <MessageSquare size={18} /> },
    { id: 'settings', label: 'Settings', icon: <Database size={18} /> },
    { id: 'logs', label: 'Logs', icon: <FileText size={18} /> },
];

export default function TriageView({ projectId, onStageChange }: { projectId: string, onStageChange?: (stage: number) => void }) {
    const [activeTab, setActiveTab] = useState('graph');
    const [designRegistry, setDesignRegistry] = useState<any[]>([]);
    const [isSavingRegistry, setIsSavingRegistry] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);

    // Data State
    const [assets, setAssets] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isReadOnly, setIsReadOnly] = useState(false);

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

        // Persist
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

    const fetchRegistry = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}/registry`);
            if (response.ok) {
                const data = await response.json();
                setDesignRegistry(data.registry || []);
            }
        } catch (error) {
            console.error("Error fetching registry:", error);
        }
    }, [projectId]);

    const handleRegistryUpdate = async (category: string, key: string, value: any) => {
        setIsSavingRegistry(true);
        try {
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}/registry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category, key, value })
            });

            if (response.ok) {
                // Update local state optimistically
                setDesignRegistry(prev => {
                    const existingIndex = prev.findIndex(r => r.category === category && r.key === key);
                    if (existingIndex > -1) {
                        const next = [...prev];
                        next[existingIndex] = { ...next[existingIndex], value };
                        return next;
                    }
                    return [...prev, { category, key, value }];
                });
            }
        } catch (error) {
            console.error("Error updating registry:", error);
        } finally {
            setIsSavingRegistry(false);
        }
    };

    const initializeRegistry = async () => {
        setIsSavingRegistry(true);
        try {
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}/registry/initialize`, {
                method: 'POST'
            });
            if (response.ok) {
                fetchRegistry();
            }
        } catch (error) {
            console.error("Error initializing registry:", error);
        } finally {
            setIsSavingRegistry(false);
        }
    };

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
                setIsReadOnly(statusData.status === 'COMPLETED');
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
            fetchRegistry();
            fetchLayout();
        }
    }, [projectId, fetchProject, fetchRegistry, fetchLayout]);
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
            if (data.log) {
                setTriageLog(data.log);
                setActiveTab('logs'); // Show logs initially to see progress
            }
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
            <div className={`flex flex-col h-full bg-gray-50 dark:bg-gray-900 transition-all duration-500 ease-in-out ${isFullscreen ? 'fixed inset-0 z-[100] !h-screen !w-screen' : 'relative'
                }`}>
                {/* Read Only Banner */}
                {isReadOnly && (
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-2.5 text-white flex items-center justify-between shadow-lg z-[60]">
                        <div className="flex items-center gap-3">
                            <div className="p-1.5 bg-white/20 rounded-lg backdrop-blur-sm">
                                <ShieldCheck size={18} />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-[10px] font-bold uppercase tracking-widest opacity-80">Design Status</span>
                                <span className="text-sm font-bold">APPROVED & LOCKED</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <span className="text-xs font-medium text-blue-100 hidden md:block">
                                The scope is finalized and ready for orchestration.
                            </span>
                            <button
                                onClick={onStageChange ? () => onStageChange(2) : undefined}
                                className="bg-white text-blue-700 px-4 py-1.5 rounded-full text-xs font-bold shadow-md hover:bg-blue-50 transition-all flex items-center gap-2"
                            >
                                <Play size={14} fill="currentColor" /> Resume Drafting
                            </button>
                        </div>
                    </div>
                )}


                {/* Top Tabs Bar */}
                <div className={`flex items-center justify-between px-4 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 shadow-sm transition-all ${isFullscreen ? 'py-1 opacity-80 hover:opacity-100' : 'py-0'
                    }`}>
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
                                {tab.icon}
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setIsFullscreen(!isFullscreen)}
                            className="text-gray-500 hover:text-primary p-2 rounded-lg transition-colors"
                            title={isFullscreen ? "Restaurar" : "Maximizar Espacio"}
                        >
                            {isFullscreen ? <Shrink size={18} /> : <Expand size={18} />}
                        </button>
                        <button
                            onClick={handleReset}
                            disabled={isReadOnly}
                            className={`text-gray-500 p-2 rounded-lg transition-colors ${isReadOnly ? 'opacity-50 cursor-not-allowed' : 'hover:text-red-500'}`}
                            title="Limpiar Proyecto (Reiniciar)"
                        >
                            <RotateCcw size={18} />
                        </button>
                        <div className="w-px h-6 bg-gray-200 dark:bg-gray-800 mx-1" />
                        <button
                            onClick={handleReTriage}
                            disabled={isReadOnly}
                            className={`bg-blue-600 text-white px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${isReadOnly ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'}`}
                            title="Reprocesar Triaje"
                        >
                            <Play size={14} /> Triaje
                        </button>
                        <button
                            onClick={() => saveLayout(nodes, edges)}
                            disabled={isReadOnly}
                            className={`bg-gray-100 text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${isReadOnly ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700'}`}
                            title="Guardar Diseño Actual (Auto-save activo)"
                        >
                            <Save size={14} /> Guardar
                        </button>
                        <button
                            onClick={handleApprove}
                            disabled={isReadOnly} // Already approved if read-only
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition-all ${isReadOnly ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700 text-white'}`}
                            title={isReadOnly ? "Diseño Aprobado" : "Aprobar Diseño"}
                        >
                            <CheckCircle size={14} /> {isReadOnly ? "Aprobado" : "Aprobar"}
                        </button>
                    </div>
                </div>

                {/* Tab Content */}
                <div className="flex-1 overflow-hidden relative">

                    {/* 1. GRAPH TAB */}
                    {activeTab === 'graph' && (
                        <div className="h-full w-full flex relative">
                            {/* Drag Source Sidebar (Small Grid) */}
                            {!isReadOnly && (
                                <div
                                    className={`h-full border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex flex-col z-20 shrink-0 transition-all duration-300 ease-in-out overflow-hidden ${showSidebar ? 'w-64' : 'w-0'
                                        }`}
                                >
                                    <div className="p-3 border-b border-gray-100 dark:border-gray-800 text-xs font-bold uppercase tracking-wider text-gray-500 bg-gray-50 dark:bg-gray-950 flex justify-between items-center whitespace-nowrap">
                                        <span>Activos</span>
                                        <button
                                            onClick={() => setShowSidebar(false)}
                                            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-800 rounded transition-colors"
                                            title="Ocultar Panel"
                                        >
                                            <PanelLeftClose size={14} />
                                        </button>
                                    </div>
                                    <div className="flex-1 overflow-hidden min-w-[256px] custom-scrollbar">
                                        <div className="p-4 border-b border-gray-100 dark:border-gray-800">
                                            <DiscoveryDashboard assets={assets} nodes={nodes} />
                                        </div>

                                        {isLoading ? (
                                            <div className="p-4 text-center text-gray-400 text-xs">Cargando...</div>
                                        ) : (
                                            <div className="overflow-y-auto max-h-[calc(100vh-350px)] p-3 space-y-2">
                                                <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1 mb-2">Available Components</h4>
                                                {assets.map(asset => (
                                                    <div
                                                        key={asset.id}
                                                        draggable
                                                        onDragStart={(e) => {
                                                            e.dataTransfer.setData('application/reactflow', JSON.stringify(asset));
                                                            e.dataTransfer.effectAllowed = 'move';
                                                        }}
                                                        className="p-3 text-xs bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-xl hover:border-primary/50 hover:shadow-md cursor-grab flex items-center gap-3 transition-all group"
                                                    >
                                                        <div className="p-1.5 bg-gray-50 dark:bg-gray-950 rounded-lg group-hover:bg-primary/10 transition-colors">
                                                            <Layout size={14} className="text-gray-400 group-hover:text-primary" />
                                                        </div>
                                                        <div className="flex flex-col min-w-0">
                                                            <span className="font-bold truncate text-gray-700 dark:text-gray-200">{asset.name}</span>
                                                            <span className="text-[9px] text-gray-400 uppercase">{asset.complexity || 'Low'} Complexity</span>
                                                        </div>
                                                    </div>
                                                ))}
                                                {assets.length === 0 && <div className="text-center text-gray-400 text-xs py-10 italic">No assets found in manifest</div>}
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
                        <div className="h-full w-full p-8 overflow-y-auto bg-white dark:bg-gray-900">
                            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                                <List className="text-primary" /> Inventario de Paquetes
                            </h2>
                            <div className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-gray-50 dark:bg-gray-800 text-gray-500 uppercase text-xs">
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
                                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
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
                                                        className="bg-gray-50 dark:bg-gray-900 border-none rounded px-2 py-1 text-[10px] font-bold uppercase focus:ring-1 focus:ring-primary w-24 transition-all"
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
                                                        {asset.is_pii && <span className="text-[10px] font-bold">PII</span>}
                                                    </button>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-1">
                                                        <select
                                                            value={asset.load_strategy || 'FULL_OVERWRITE'}
                                                            onChange={(e) => handleMetadataChange(asset.id, { load_strategy: e.target.value })}
                                                            className={`text-[9px] font-bold uppercase rounded px-1.5 py-0.5 border-none focus:ring-1 focus:ring-primary w-24 cursor-pointer ${asset.load_strategy === 'INCREMENTAL' ? 'bg-blue-100 text-blue-700' :
                                                                asset.load_strategy === 'SCD_2' ? 'bg-indigo-100 text-indigo-700' :
                                                                    'bg-gray-100 text-gray-600'
                                                                }`}
                                                        >
                                                            <option value="FULL_OVERWRITE">FULL</option>
                                                            <option value="INCREMENTAL">INCREMENTAL</option>
                                                            <option value="SCD_2">SCD TYPE 2</option>
                                                        </select>
                                                        <div className="flex items-center gap-1 text-[9px] text-gray-400 font-mono">
                                                            <Clock size={8} /> {asset.frequency || 'DAILY'}
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <select
                                                        value={asset.type}
                                                        onChange={(e) => handleCategoryChange(asset.id, e.target.value)}
                                                        className={`text-[10px] font-bold uppercase rounded-md border border-gray-200 dark:border-gray-700 px-2 py-1 focus:ring-2 focus:ring-primary cursor-pointer transition-colors ${asset.type === 'CORE' ? 'bg-blue-100 text-blue-700' :
                                                            asset.type === 'SUPPORT' ? 'bg-purple-100 text-purple-700' :
                                                                'bg-gray-100 text-gray-600'
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

                    {/* 4. SETTINGS TAB - DESIGN REGISTRY */}
                    {activeTab === 'settings' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-gray-50 dark:bg-gray-950">
                            <div className="max-w-4xl mx-auto space-y-8">
                                <div className="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-800">
                                    <div>
                                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                                            <Database className="text-primary" />
                                            Design Registry
                                        </h2>
                                        <p className="text-sm text-gray-500 mt-1">
                                            Define global standards for naming, paths, and privacy policies.
                                        </p>
                                    </div>
                                    <button
                                        onClick={initializeRegistry}
                                        disabled={isSavingRegistry}
                                        className="px-4 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-all font-medium text-sm flex items-center gap-2"
                                    >
                                        <Zap size={16} />
                                        Initialize Defaults
                                    </button>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {/* Naming Standards */}
                                    <div className="bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2 mb-4">
                                            <Terminal size={14} />
                                            Naming Conventions
                                        </h3>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-2">SILVER PREFIX</label>
                                                <input
                                                    type="text"
                                                    value={designRegistry.find(r => r.category === 'NAMING' && r.key === 'silver_prefix')?.value || ''}
                                                    onChange={(e) => handleRegistryUpdate('NAMING', 'silver_prefix', e.target.value)}
                                                    placeholder="stg_"
                                                    className="w-full bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 rounded-lg text-sm px-4 py-2 focus:ring-primary"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-2">GOLD PREFIX</label>
                                                <input
                                                    type="text"
                                                    value={designRegistry.find(r => r.category === 'NAMING' && r.key === 'gold_prefix')?.value || ''}
                                                    onChange={(e) => handleRegistryUpdate('NAMING', 'gold_prefix', e.target.value)}
                                                    placeholder="dim_"
                                                    className="w-full bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 rounded-lg text-sm px-4 py-2 focus:ring-primary"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Infrastructure & Paths */}
                                    <div className="bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2 mb-4">
                                            <Database size={14} />
                                            Target Storage
                                        </h3>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-2">LAKEHOUSE ROOT PATH</label>
                                                <input
                                                    type="text"
                                                    value={designRegistry.find(r => r.category === 'PATHS' && r.key === 'root_path')?.value || ''}
                                                    onChange={(e) => handleRegistryUpdate('PATHS', 'root_path', e.target.value)}
                                                    placeholder="abfss://..."
                                                    className="w-full bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 rounded-lg text-sm px-4 py-2 focus:ring-primary"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Privacy Policies */}
                                    <div className="bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
                                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2 mb-4">
                                            <Shield size={14} />
                                            Data Privacy (PII)
                                        </h3>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-2">MASKING METHOD</label>
                                                <select
                                                    value={designRegistry.find(r => r.category === 'PRIVACY' && r.key === 'masking_method')?.value || 'sha256'}
                                                    onChange={(e) => handleRegistryUpdate('PRIVACY', 'masking_method', e.target.value)}
                                                    className="w-full bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 rounded-lg text-sm px-4 py-2 focus:ring-primary"
                                                >
                                                    <option value="sha256">SHA-256 (Hashing)</option>
                                                    <option value="redact">REDACT (Partial Mask)</option>
                                                    <option value="null">NULL (Remove Column)</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* 3. PROMPT TAB */}
                    {activeTab === 'prompt' && (
                        <div className="h-full w-full p-8 overflow-y-auto bg-gray-50 dark:bg-gray-950">
                            <div className="max-w-4xl mx-auto space-y-6">
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
                            <div className="max-w-4xl mx-auto space-y-10">
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
                                                <label className="text-xs font-bold text-gray-400 uppercase">Nombre del Paso</label>
                                                <input id="v-step-name" type="text" placeholder="Ej: Validación Manual" className="w-full p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-xs font-bold text-gray-400 uppercase">Depende de (Path)</label>
                                                <input id="v-step-dep" type="text" placeholder="Ej: schema/table.sql" className="w-full p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-xs font-bold text-gray-400 uppercase">Instrucciones para el Agente</label>
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
                        <div className="h-full w-full p-8 overflow-y-auto bg-gray-950 text-gray-300 font-mono text-xs leading-relaxed">
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
                                <p className="text-xs text-gray-500 truncate w-64">
                                    {assets.find(a => a.id === selectedAssetForContext)?.name || 'Asset'}
                                </p>
                            </div>
                            <button onClick={() => setSelectedAssetForContext(null)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                                <PanelLeftClose size={20} />
                            </button>
                        </div>

                        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-400 uppercase">Descripción / Notas</label>
                                <textarea
                                    className="w-full h-48 p-3 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary"
                                    placeholder="Indica reglas específicas para este archivo..."
                                    defaultValue={assetContexts[selectedAssetForContext]?.notes || ''}
                                    id="context-notes"
                                />
                            </div>

                            <div className="space-y-4">
                                <label className="text-xs font-bold text-gray-400 uppercase">Reglas Sugeridas</label>
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
