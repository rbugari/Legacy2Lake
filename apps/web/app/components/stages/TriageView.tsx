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
import { CheckCircle, Layout, List, Terminal, MessageSquare, Play, FileText, RotateCcw, PanelLeftClose, PanelLeftOpen, Expand, Shrink, Save, ShieldCheck, AlertTriangle } from 'lucide-react';

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

export default function TriageView({ projectId, onStageChange }: { projectId: string, onStageChange?: (stage: number) => void }) {
    const [activeTab, setActiveTab] = useState('graph');
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

    // Initialization
    useEffect(() => {
        const init = async () => {
            try {
                // Check Status first
                const resStatus = await fetch(`${API_BASE_URL}/projects/${projectId}/status`);
                const dataStatus = await resStatus.json();
                const readOnly = dataStatus.status === 'DRAFTING' || dataStatus.status === 'LOCKED';
                setIsReadOnly(readOnly);

                // Fetch Assets
                const resAssets = await fetch(`${API_BASE_URL}/projects/${projectId}/assets`);
                const dataAssets = await resAssets.json();
                if (dataAssets.assets) {
                    // Normalize: DB uses 'filename', Frontend uses 'name'
                    const normalized = dataAssets.assets.map((a: any) => ({
                        ...a,
                        name: a.name || a.filename || "Unnamed Asset"
                    }));
                    setAssets(normalized);
                }

                // Fetch Layout
                const resLayout = await fetch(`${API_BASE_URL}/projects/${projectId}/layout`);
                const dataLayout = await resLayout.json();
                if (dataLayout.nodes) {
                    // Re-enrich with potentially new isReadOnly state
                    // Note: enrichNodes depends on isReadOnly, so we need to process it after setting state or use local var?
                    // React state updates are async, so use 'readOnly' local var for the immediate call
                    const enriched = dataLayout.nodes.map((n: any) => ({
                        ...n,
                        data: {
                            ...n.data,
                            onDelete: handleDeleteNode,
                            id: n.id,
                            isReadOnly: readOnly
                        },
                        draggable: !readOnly,
                        selectable: !readOnly,
                        deletable: !readOnly
                    }));
                    setNodes(enriched);
                    setEdges(dataLayout.edges || []);
                }
                // Fetch Prompt
                const resPrompt = await fetch(`${API_BASE_URL}/prompts/agent-a`);
                if (resPrompt.ok) {
                    const dataPrompt = await resPrompt.json();
                    if (dataPrompt.prompt) setSystemPrompt(dataPrompt.prompt);
                } else {
                    // Fallback to a hardcoded default if the backend is older/unavailable
                    setSystemPrompt("Analyze the SSIS packages and determine the optimal PySpark architecture...");
                }

            } catch (err) {
                console.error("Init failed", err);
            } finally {
                setIsLoading(false);
            }
        };
        init();
    }, [projectId, setNodes, setEdges, handleDeleteNode]); // Removed isReadOnly from dependency to avoid loop if not handled carefully, but handleSelection needed it.

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
                                            <th className="px-6 py-4">Nombre del Paquete</th>
                                            <th className="px-6 py-4">Tipo</th>
                                            <th className="px-6 py-4 text-center">Incluir en Migración</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                        {assets.map(asset => (
                                            <tr key={asset.id} className="hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors">
                                                <td className="px-6 py-4 font-medium">{asset.name}</td>
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
                                                        className="w-5 h-5 text-primary rounded border-gray-300 focus:ring-primary cursor-pointer transition-all"
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                        {assets.length === 0 && (
                                            <tr>
                                                <td colSpan={3} className="px-6 py-8 text-center text-gray-400">
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
                            <div className="max-w-4xl mx-auto space-y-6">
                                <h2 className="text-xl font-bold flex items-center gap-2">
                                    <MessageSquare className="text-primary" /> Contexto del Usuario
                                </h2>
                                <p className="text-sm text-gray-500">
                                    Proporciona contexto adicional, reglas de negocio o restricciones que el agente debe considerar.
                                </p>
                                <textarea
                                    value={userContext}
                                    onChange={(e) => setUserContext(e.target.value)}
                                    placeholder="Ej: Ignorar tablas de auditoría, priorizar paquetes de Ventas, usar prefijo 'stg_' para tablas staging..."
                                    className="w-full h-64 p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-sm leading-relaxed focus:ring-2 focus:ring-primary outline-none shadow-sm"
                                />
                                <div className="flex justify-end">
                                    <button className="px-6 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg font-bold hover:bg-gray-50 transition-colors">
                                        Guardar Contexto
                                    </button>
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
        </ReactFlowProvider>
    );
}
