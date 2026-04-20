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
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Activity, AlertTriangle, ArrowLeftRight, ArrowRight, Brain, Bot, CheckCircle, ChevronDown, ChevronRight, Clock, Cpu, Database, Expand, FileCode, FileEdit, FileText, Folder, FolderOpen, GitBranch, Infinity, Layout, Layers, List, Map, Maximize2, MessageSquare, Minimize2, PanelLeftClose, PanelLeftOpen, Play, RefreshCw, RotateCcw, Save, Search, Settings, Shield, ShieldAlert, ShieldCheck, Shrink, Terminal, X, Zap, Server } from 'lucide-react';
import DiscoveryDashboard from '../DiscoveryDashboard';
import { fetchWithAuth } from '../../lib/auth-client';
import UnifiedLogViewer from "../UnifiedLogViewer";
import UnifiedFileExplorer from "../UnifiedFileExplorer";

import ColumnMappingEditor from '../ColumnMappingEditor'; // Added Phase A
import OriginAnalysisPanel from '../visualization/OriginAnalysisPanel'; // Sprint 8.5
import TransformationsMatrix from '../visualization/TransformationsMatrix'; // Sprint 8.5
import SourceQueriesViewer from '../visualization/SourceQueriesViewer'; // Sprint 8.5
import CodeQualityAnalysis from '../visualization/CodeQualityAnalysis'; // Sprint 14 - Legacy schema issues
import SchemaViewer from '../visualization/SchemaViewer'; // Sprint 13
import PIIHeatmap from '../visualization/PIIHeatmap'; // Sprint 11 - Advanced Triage
import TableRegistry from '../visualization/TableRegistry'; // Sprint 14 - Table Impact Registry
import UnderstandingPanel from '../UnderstandingPanel'; // Block 3 - Project Understanding
import ExportPanel from '../ExportPanel'; // Block 4 - Documentation Exports
import RuleRefinementPanel from '../RuleRefinementPanel'; // Block 5 - Rule Refinement & Snapshots
import GovernancePanel from '../GovernancePanel'; // Block 6 - Governance & Versioning
import ReactMarkdown from 'react-markdown';
import { useConfirm } from '@/app/hooks/useConfirm';
import ReadinessBadge from '../ReadinessBadge';
import ProjectAssistantModal from '../ProjectAssistantModal';

// Lazy mismatch badge for Grid rows
function MismatchBadge({ projectId, objectId, onClickSchema }: { projectId: string; objectId: string; onClickSchema: () => void }) {
    const [count, setCount] = React.useState<number | null>(null);
    useEffect(() => {
        if (!objectId) return;
        fetchWithAuth(`projects/${projectId}/objects/${objectId}/type-mismatches`)
            .then(r => r.ok ? r.json() : null)
            .then(d => { if (d) setCount(d.mismatch_count ?? 0); })
            .catch(() => { });
    }, [projectId, objectId]);

    if (count === null) return <span className="text-gray-600 text-[9px]">—</span>;
    if (count === 0) return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-black bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
            ✓ OK
        </span>
    );
    return (
        <button
            onClick={(e) => { e.stopPropagation(); onClickSchema(); }}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-black bg-orange-500/15 text-orange-400 border border-orange-500/30 hover:bg-orange-500/25 transition-colors"
            title={`${count} type mismatch${count !== 1 ? 'es' : ''} — click to view`}
        >
            <AlertTriangle size={9} />
            {count} mismatch{count !== 1 ? 'es' : ''}
        </button>
    );
}

// Tab Definitions
const TABS = [
    { id: 'graph', label: 'Graph', icon: <Layout size={14} />, group: 'Views' },
    { id: 'grid', label: 'Grid', icon: <List size={14} />, group: 'Views' },
    { id: 'schema', label: 'Schema', icon: <Database size={14} />, group: 'Views' }, // Sprint 13
    { id: 'origin', label: 'Origin', icon: <Server size={14} />, group: 'Analysis' }, // Sprint 8.5
    { id: 'transform', label: 'Transform', icon: <Zap size={14} />, group: 'Analysis' }, // Sprint 8.5
    { id: 'queries', label: 'Queries', icon: <FileCode size={14} />, group: 'Analysis' }, // Sprint 8.5
    { id: 'quality', label: 'Quality', icon: <Shield size={14} />, group: 'Analysis' }, // Sprint 11
    { id: 'pii', label: 'PII Heatmap', icon: <ShieldAlert size={14} />, group: 'Analysis' }, // Sprint 11 Advanced
    { id: 'tables', label: 'Table Registry', icon: <GitBranch size={14} />, group: 'Analysis' }, // Sprint 14 - Table Impacts
    { id: 'partitions', label: 'Partitions', icon: <Layers size={14} />, group: 'Analysis' }, // Sprint 11 Advanced
    { id: 'mapping', label: 'Mapping', icon: <Database size={14} />, group: 'Views' },
    { id: 'context', label: 'Manual Input', icon: <MessageSquare size={14} />, group: 'Config' },
    { id: 'logs', label: 'Execution', icon: <FileText size={14} />, group: 'Config' },
    { id: 'files', label: 'File Explorer', icon: <FolderOpen size={14} />, group: 'Config' }, // Added per request
    { id: 'understanding', label: 'Understanding', icon: <Brain size={14} />, group: 'Analysis' }, // Block 3
    { id: 'export', label: 'Export', icon: <FileEdit size={14} />, group: 'Analysis' }, // Block 4
    { id: 'refinement', label: 'Refinement', icon: <Zap size={14} />, group: 'Analysis' }, // Block 5 - Rule Refinement
    { id: 'governance', label: 'Governance', icon: <Shield size={14} />, group: 'Analysis' }, // Block 6 - Governance & Versioning
];

const TRIAGE_AGENTS = [
    { id: 'A', name: 'The Architect', role: 'Asset classifier & strategy advisor' },
    { id: 'B', name: 'The Privacy Guard', role: 'PII detection & risk labelling' },
];

type StructuredContextEntry = {
    notes: string;
    rules: Record<string, any>;
};

function buildContextSummary(
    userContext: string,
    assetContexts: Record<string, StructuredContextEntry>,
    preClassification: Record<string, any>
) {
    const assetEntries = Object.entries(assetContexts);

    return {
        hasGlobalContext: Boolean(userContext.trim()),
        assetContextCount: assetEntries.length,
        assetContextWithNotes: assetEntries.filter(([, value]) => Boolean(value.notes?.trim())).length,
        assetContextWithRules: assetEntries.filter(([, value]) => Boolean(value.rules) && Object.keys(value.rules || {}).length > 0).length,
        overrideCount: Object.keys(preClassification || {}).length,
    };
}

export default function TriageView({
    projectId,
    projectName,
    activeTenantId,
    projectStage,
    onStageChange,
    isReadOnly: propReadOnly,
    onStatsUpdate,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent,
    activeSection,
    onSectionChange
}: {
    projectId: string,
    projectName?: string,
    activeTenantId?: string,
    projectStage?: number,
    onStageChange?: (stage: number) => void,
    isReadOnly?: boolean,
    onStatsUpdate?: (stats: any) => void,
    isFullscreen?: boolean,
    onToggleFullscreen?: () => void,
    onReset?: () => void,
    onBackToCurrent?: () => void,
    activeSection: string,
    onSectionChange: (section: string) => void
}) {
    // Safety check: prioritize Prop ReadOnly (from parent) but keep internal state for fallback
    const isReadOnly = propReadOnly ?? false;

    // Data State
    const [assets, setAssets] = useState<any[]>([]);
    const [isInitialLoading, setIsInitialLoading] = useState(true); // Only for initial load
    const { confirm, ConfirmDialog } = useConfirm();
    const [isTriageRunning, setIsTriageRunning] = useState(false); // For active triage/regenerate processes
    const [isTriageComplete, setIsTriageComplete] = useState(false); // True once triage finishes successfully

    // Graph State
    const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);

    // Files state removed - now using UnifiedFileExplorer

    // Prompt & Context State
    const [systemPrompt, setSystemPrompt] = useState("");
    const [userContext, setUserContext] = useState("");
    const [triageLog, setTriageLog] = useState("");

    // Heatmap State
    const [activeHeatmap, setActiveHeatmap] = useState<'none' | 'pii' | 'criticality' | 'volume'>('none');
    const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
    const [selectedAssetForSchema, setSelectedAssetForSchema] = useState<string | null>(null); // Sprint 13

    // Technology State
    const [sourceTech, setSourceTech] = useState<string | undefined>();
    const [destTech, setDestTech] = useState<string | undefined>();

    // DnD (Keep for Graph Tab logic if needed, though split pane is gone)
    const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

    const [showSidebar, setShowSidebar] = useState(true);
    const [showAssistant, setShowAssistant] = useState(false);

    // Release 1.1: Context State
    const [assetContexts, setAssetContexts] = useState<Record<string, StructuredContextEntry>>({});
    const [selectedAssetForContext, setSelectedAssetForContext] = useState<any | null>(null);
    const [isSavingContext, setIsSavingContext] = useState(false);
    const [editingAsset, setEditingAsset] = useState<any | null>(null);
    const [assetNote, setAssetNote] = useState("");
    const [isApproving, setIsApproving] = useState(false);
    const [schemaInitialTab, setSchemaInitialTab] = useState<'schema' | 'mapping'>('schema');

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
            await fetchWithAuth(`assets/${assetId}`, {
                method: 'PATCH',
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
            await fetchWithAuth(`assets/${assetId}`, {
                method: 'PATCH',
                body: JSON.stringify(updates)
            });
        } catch (e) {
            console.error("Failed to persist metadata change", e);
        }
    }, [setAssets, isReadOnly]);

    const handleSyncGraph = useCallback(async () => {
        if (isReadOnly) return;
        try {
            const res = await fetchWithAuth(`projects/${projectId}/sync-graph`, {
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

    // Debounced Sync to avoid overloading the backend during rapid toggling
    const syncTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
    const debouncedSync = useCallback(() => {
        if (syncTimeoutRef.current) clearTimeout(syncTimeoutRef.current);
        syncTimeoutRef.current = setTimeout(() => {
            handleSyncGraph();
        }, 1000); // 1 second debounce
    }, [handleSyncGraph]);

    const handleSelectionChange = useCallback(async (assetId: string, isSelected: boolean) => {
        if (isReadOnly) return;

        // 1. Optimistic Assets Update
        setAssets(prev => prev.map(a =>
            a.id === assetId ? { ...a, selected: isSelected } : a
        ));

        // 2. Optimistic Nodes Update
        setNodes(nds => {
            const exists = nds.some(n => n.id === assetId);
            if (isSelected && !exists) {
                // Find asset data to build a new node
                const asset = assets.find(a => a.id === assetId);
                if (asset) {
                    const newNode = {
                        id: assetId,
                        type: 'custom',
                        position: { x: 300, y: 300 }, // Default position, sync will fix it
                        data: {
                            label: asset.name,
                            category: asset.type || 'CORE',
                            complexity: asset.complexity || 'LOW',
                            status: 'pending'
                        }
                    };
                    return enrichNodes([...nds, newNode]);
                }
            } else if (!isSelected && exists) {
                // Remove from graph if unselected
                return nds.filter(n => n.id !== assetId);
            }
            return nds;
        });

        // 3. Persist and Re-sync (Debounced)
        try {
            await fetchWithAuth(`assets/${assetId}`, {
                method: 'PATCH',
                body: JSON.stringify({ selected: isSelected })
            });
            debouncedSync();
        } catch (e) {
            console.error("Failed to persist selection change", e);
        }
    }, [isReadOnly, assets, enrichNodes, debouncedSync, setNodes, setAssets]);


    // Initialization
    const fetchProject = useCallback(async () => {
        try {
            console.log('[TriageView fetchProject] Starting fetch for projectId:', projectId);

            // Check Status first
            const statusRes = await fetchWithAuth(`discovery/status/${projectId}`);
            const statusData = await statusRes.json();
            console.log('[TriageView fetchProject] Status response:', statusData);

            // Allow loading for any post-discovery status
            const validStatuses = ['COMPLETED', 'TRIAGED', 'TRIAGE', 'DRAFTING', 'DRAFTED', 'REFINING', 'REFINED', 'DELIVERED'];
            if (validStatuses.includes(statusData.status)) {
                // Mark triage complete for TRIAGED or any later stage so the
                // completion banner is visible even if the user returns after advancing.
                const TRIAGED_OR_BEYOND = ['TRIAGED', 'DRAFTING', 'DRAFTED', 'REFINING', 'REFINED', 'CERTIFYING', 'CERTIFIED', 'GOVERNED', 'DELIVERED'];
                if (TRIAGED_OR_BEYOND.includes(statusData.status)) {
                    setIsTriageComplete(true);
                }
                const projectRes = await fetchWithAuth(`discovery/project/${projectId}`);
                const projectData = await projectRes.json();
                console.log('[TriageView fetchProject] Project data:', {
                    assetsCount: projectData.assets?.length || 0,
                    assets: projectData.assets,
                    source_tech: projectData.source_tech,
                    target_tech: projectData.target_tech
                });

                // Filter out system assets like LAYOUT from the UI list if needed, 
                // or just rely on the pending filter.
                setAssets(projectData.assets || []);
                setSystemPrompt(projectData.prompt || "");
                setSourceTech(projectData.source_tech);
                setDestTech(projectData.target_tech);

                try {
                    const contextRes = await fetchWithAuth(`projects/${projectId}/context`);
                    if (contextRes.ok) {
                        const contextData = await contextRes.json();
                        const nextAssetContexts: Record<string, StructuredContextEntry> = {};

                        (contextData.contexts || []).forEach((entry: any) => {
                            if (entry.source_path === '__global__') {
                                if (typeof entry.notes === 'string') {
                                    setUserContext(entry.notes);
                                }
                                return;
                            }

                            nextAssetContexts[entry.source_path] = {
                                notes: entry.notes || '',
                                rules: entry.rules || {},
                            };
                        });

                        setAssetContexts(nextAssetContexts);
                    }
                } catch (contextError) {
                    console.warn('[TriageView fetchProject] Failed to load project context:', contextError);
                }
            } else {
                console.warn('[TriageView fetchProject] Status not eligible for loading:', statusData.status);
            }
        } catch (error) {
            console.error("[TriageView fetchProject] Init error:", error);
        } finally {
            setIsInitialLoading(false);
        }
    }, [projectId]);

    const fetchLayout = useCallback(async () => {
        try {
            const res = await fetchWithAuth(`projects/${projectId}/layout`);
            if (res.ok) {
                const data = await res.json();
                if (data.nodes) setNodes(enrichNodes(data.nodes));
                if (data.edges) setEdges(data.edges);
            }
        } catch (e) {
            console.error("Layout fetch error", e);
        }
    }, [projectId, enrichNodes]);

    const refreshTriagedSnapshot = useCallback(async () => {
        if (activeSection === 'context') return;

        await Promise.all([
            fetchProject(),
            fetchLayout()
        ]);
    }, [activeSection, fetchProject, fetchLayout]);

    useEffect(() => {
        if (projectId && projectId !== 'undefined' && projectId !== '') {
            fetchProject();
            fetchLayout();
        } else {
            setIsInitialLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectId]); // Only re-run when projectId changes, not when callbacks change

    useEffect(() => {
        if (!isTriageRunning) return;

        // Keep the visible triage data fresh while the background run is active.
        let cancelled = false;
        const tick = async () => {
            if (cancelled) return;
            await refreshTriagedSnapshot();
        };

        tick();
        const interval = setInterval(tick, 15000);

        return () => {
            cancelled = true;
            clearInterval(interval);
        };
    }, [isTriageRunning, refreshTriagedSnapshot]);

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
            await fetchWithAuth(`projects/${projectId}/layout`, {
                method: 'POST',
                body: JSON.stringify({ nodes: nds, edges: eds })
            });
        } catch (e) {
            console.error("Autosave failed", e);
        }
    }, [projectId, isReadOnly]);

    const handleSaveContext = useCallback(async (
        sourcePath: string,
        notes: string,
        rules: Record<string, any> = {},
        rerunAfterSave: boolean = true
    ) => {
        setIsSavingContext(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/context`, {
                method: 'POST',
                body: JSON.stringify({
                    source_path: sourcePath,
                    notes,
                    rules
                })
            });
            if (res.ok) {
                setAssetContexts(prev => ({
                    ...prev,
                    [sourcePath]: { notes, rules }
                }));

                if (sourcePath === '__global__') {
                    setUserContext(notes);
                }

                if (rerunAfterSave) {
                    await handleRunTriage();
                }
            }
        } catch (e) {
            console.error("Failed to save context", e);
        } finally {
            setIsSavingContext(false);
            setSelectedAssetForContext(null);
        }
    }, [projectId, handleRunTriage]);

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
        setIsApproving(true);
        try {
            // 1. Save final layout
            await saveLayout(nodes, edges);

            // 2. Lock triage and move the project into Drafting stage
            const res = await fetchWithAuth(`projects/${projectId}/approve`, {
                method: 'POST'
            });

            if (res.ok) {
                if (onStageChange) onStageChange(2);
            } else {
                console.error("Approve failed", await res.text());
                alert("Error approving design. Please try again.");
                setIsApproving(false);
            }
        } catch (e) {
            console.error("Failed to approve", e);
            alert("Connection error while approving.");
            setIsApproving(false);
        }
    };

    const fetchTriageLogs = useCallback(async () => {
        try {
            const res = await fetchWithAuth(`projects/${projectId}/execution-logs?type=triage`);
            const data = await res.json();
            if (data.logs) {
                setTriageLog(data.logs);
            }

            // Check project status to detect completion
            const statusRes = await fetchWithAuth(`discovery/status/${projectId}`);
            const statusData = await statusRes.json();

            // If status changed to TRIAGED, stop polling
            if (statusData.status === "TRIAGED" && isTriageRunning) {
                console.log("DEBUG: Triage completed, stopping polling...");

                // Stop polling - data will reload via useEffect when isTriageRunning changes
                setIsTriageRunning(false);
                setIsTriageComplete(true);
                // Stay on log view — user reviews results and navigates manually
            }
        } catch (e) {
            console.error("Failed to load logs", e);
        }
    }, [projectId, isTriageRunning]); // Removed fetchProject, fetchLayout dependencies

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isTriageRunning) {
            const pollIntervalMs = activeSection === 'logs' ? 5000 : 15000;

            // Poll faster when the execution log is visible; slow down elsewhere to reduce noise.
            fetchTriageLogs(); // Fetch immediately
            interval = setInterval(fetchTriageLogs, pollIntervalMs);
        }
        return () => clearInterval(interval);
    }, [activeSection, isTriageRunning, fetchTriageLogs]);

    // Load historical logs when logs tab is opened
    useEffect(() => {
        if (activeSection === 'logs' && !isTriageRunning) {
            fetchTriageLogs(); // Load historical logs
        }
    }, [activeSection]); // Only trigger when section changes

    // Reload data when triage completes (isTriageRunning changes from true to false)
    const prevTriageRunning = useRef(false);
    useEffect(() => {
        // Only reload if we just finished running (transition from true to false)
        if (prevTriageRunning.current === true && isTriageRunning === false) {
            console.log("DEBUG: Triage just completed, reloading project data...");
            fetchProject();
            fetchLayout();
        }
        prevTriageRunning.current = isTriageRunning;
    }, [isTriageRunning, fetchProject, fetchLayout]);

    // Legacy files loading code removed - now using UnifiedFileExplorer

    async function handleRunTriage() {
        console.log("DEBUG: handleRunTriage called for projectId:", projectId);

        // Check if re-executing a previous stage (rollback warning)
        const CURRENT_STAGE = 1; // Triage is stage 1
        if (projectStage !== undefined && projectStage > CURRENT_STAGE) {
            const phaseNames = ['Discovery', 'Triage', 'Drafting', 'Refinement', 'Governance', 'Handover'];
            const lostPhases: string[] = [];
            for (let i = CURRENT_STAGE + 1; i <= projectStage; i++) {
                if (i < phaseNames.length) lostPhases.push(phaseNames[i]);
            }
            const rollbackOk = await confirm({
                variant: 'rollback',
                title: 'Re-running Triage will roll back progress',
                description: 'The project will return to Stage 1. Discovery data is preserved.',
                lostPhases,
                confirmLabel: 'Yes, roll back & re-run',
            });
            if (!rollbackOk) return;
        }

        // Execution confirmation
        const runOk = await confirm({
            variant: 'execute',
            title: 'Run Triage Analysis?',
            description: 'The following AI agents will analyse every asset in your repository and produce a classification and strategy recommendation.',
            agents: TRIAGE_AGENTS,
            confirmLabel: 'Run Triage',
        });
        if (!runOk) return;

        if (!projectId || projectId === 'undefined' || projectId === '') {
            console.error("DEBUG: Invalid projectId in handleRunTriage:", projectId);
            alert("Error: Invalid Project ID. Returning to dashboard...");
            window.location.href = '/dashboard';
            return;
        }

        console.log("DEBUG: Starting Triage process...");
        setIsTriageRunning(true);
        setIsTriageComplete(false);
        onSectionChange('logs'); // Show logs initially to see progress
        setTriageLog("Initializing Triage process in background..."); // Reset log

        try {
            let preClassification = {};
            try {
                const settingsRes = await fetchWithAuth(`projects/${projectId}/settings`);
                const settings = await settingsRes.json();
                preClassification = settings?.pre_classification || {};
            } catch (settingsError) {
                console.warn("DEBUG: Could not load pre-classification settings:", settingsError);
            }

            const contextSummary = buildContextSummary(userContext, assetContexts, preClassification);

            const res = await fetchWithAuth(`projects/${projectId}/triage`, {
                method: 'POST',
                body: JSON.stringify({
                    system_prompt: systemPrompt,
                    user_context: userContext,
                    pre_classification: preClassification
                })
            });
            const data = await res.json();
            console.log("DEBUG: Triage API response received:", data);

            if (!res.ok) {
                const message = data?.detail?.message || data?.detail?.error || data?.message || data?.error || 'Unable to start triage.';
                console.error("Triage API rejected the request:", data);
                alert(message);
                setIsTriageRunning(false);
                return;
            }

            if (data.error) {
                console.error("Triage error from API:", data.error);
                alert(`Analysis error: ${data.error}`);
                setIsTriageRunning(false);
                return;
            }

            // NEW: Background task started, polling will handle progress
            if (data.status === "RUNNING") {
                console.log("DEBUG: Triage started in background, polling for progress...");
                setTriageLog(`✅ ${data.message || "Triage process started in background"}\n\nFetching logs...`);
                // Polling is active via useEffect, will auto-reload when status changes to TRIAGED
            } else if (data.status === "COMPLETED" || data.assets) {
                // Fallback: synchronous response (backward compatibility)
                console.log("DEBUG: Received synchronous triage response");
                if (data.assets) setAssets(data.assets);
                if (data.nodes) setNodes(enrichNodes(data.nodes));
                if (data.edges) setEdges(data.edges);
                if (data.log) setTriageLog(data.log);

                await fetchProject();
                await fetchLayout();
                // onSectionChange('grid'); // Removed auto-redirect to keep user on logs
                setIsTriageRunning(false);
            }

        } catch (e) {
            console.error("Triage failed", e);
            alert("Connection error running triage. Please verify backend server is running.");
            setIsTriageRunning(false);
        }
    }


    const handleReset = async () => {
        const resetOk = await confirm({ variant: 'danger', title: 'Reset project?', description: 'All triage results and current design will be permanently lost. This cannot be undone.', confirmLabel: 'Reset project' });
        if (!resetOk) return;

        setIsTriageRunning(true);
        setIsTriageComplete(false);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/reset`, {
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
            setIsTriageRunning(false);
        }
    };

    const handleCancelTriage = async () => {
        const cancelOk = await confirm({ variant: 'danger', title: 'Cancel analysis?', description: 'The running process will be stopped. Partial results may be incomplete.', confirmLabel: 'Cancel analysis', cancelLabel: 'Keep running' });
        if (!cancelOk) return;

        try {
            const res = await fetchWithAuth(`projects/${projectId}/cancel`, {
                method: "POST",
                headers: {
                    ...(activeTenantId ? { "X-Tenant-ID": activeTenantId } : {})
                }
            });
            const data = await res.json();

            if (data.success) {
                setTriageLog(prev => prev + '\n[INFO] Triage cancellation requested successfully.');
            } else {
                setTriageLog(prev => prev + `\n[ERROR] Failed to cancel: ${data.error || 'Unknown error'}`);
            }
        } catch (e) {
            console.error("Failed to cancel process", e);
            setTriageLog(prev => prev + `\n[ERROR] Network error during cancellation: ${e}`);
        }
    };

    // Watch for sidebar action triggers
    useEffect(() => {
        if (activeSection === 'run-triage') {
            if (!isTriageRunning) {
                handleRunTriage();
            }
            // Divert back to logs or origin to show progress
            onSectionChange('logs');
        }
    }, [activeSection, isTriageRunning, onSectionChange]);

    return (
        <>
            <ReactFlowProvider>
                <div className={`flex flex-col h-full bg-[var(--background)] transition-all duration-500 ease-in-out ${isFullscreen ? 'fixed inset-0 z-[100] !h-screen !w-screen' : 'relative'}`}>
                    <StageHeader
                        title="Stage 1: Technical Triage"
                        subtitle="Classify assets, review relationships, and prepare a safer baseline for generation"
                        icon={<Cpu className="text-blue-500" />}
                        helpText="Use Triage to decide what matters, what can be ignored, and what needs special handling before Drafting."
                        onApprove={handleApprove}
                        approveLabel="Next Phase: Drafting"
                        isApproveDisabled={isTriageRunning || assets.length === 0}
                        isExecuting={isApproving}
                        isFullscreen={isFullscreen}
                        onToggleFullscreen={onToggleFullscreen}
                        onReset={onReset}
                        onBackToCurrent={onBackToCurrent}
                    />

                    {activeSection === 'graph' && (
                        <div className="bg-black/20 border-b border-white/5 px-8 py-2 flex items-center justify-between gap-4">
                            <div className="flex items-center gap-6 overflow-x-auto custom-scrollbar">
                                <div className="flex items-center gap-2 shrink-0">
                                    <Activity size={14} className="text-gray-500" />
                                    <span className="text-[9px] font-black uppercase tracking-widest text-gray-500">Graph Intelligence</span>
                                </div>
                                <div className="flex bg-white/5 p-1 rounded-lg border border-white/5 gap-1 shrink-0">
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
                                <div className="hidden xl:flex items-center gap-2 text-[10px] text-gray-500 max-w-3xl">
                                    <span className="font-black uppercase tracking-widest text-gray-400">Overlay guide:</span>
                                    <span>
                                        {activeHeatmap === 'none' && 'Default layout. Use this view to inspect structure before applying a risk overlay.'}
                                        {activeHeatmap === 'pii' && 'Highlights assets that carry PII sensitivity and deserve review before handoff.'}
                                        {activeHeatmap === 'criticality' && 'Emphasizes nodes with higher business or migration criticality.'}
                                        {activeHeatmap === 'volume' && 'Surfaces heavier-load assets that may dominate processing windows.'}
                                    </span>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 shrink-0">
                                {isTriageRunning && (
                                    <>
                                        <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping" />
                                        <span className="text-[9px] font-bold text-cyan-500 uppercase tracking-widest">Architect Analyzing Flow...</span>
                                    </>
                                )}
                                {activeHeatmap !== 'none' && (
                                    <span className="text-[9px] font-bold uppercase tracking-widest text-cyan-300 bg-cyan-500/10 border border-cyan-500/20 rounded-full px-3 py-1">
                                        {activeHeatmap === 'pii' && 'PII overlay'}
                                        {activeHeatmap === 'criticality' && 'Criticality overlay'}
                                        {activeHeatmap === 'volume' && 'Volume overlay'}
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Main Content Area - Sprint 14: Sidebar managed at workspace level */}
                    <div className="flex-1 overflow-hidden relative">

                        {activeSection === 'overview' && (
                            <div className="h-full w-full p-8 overflow-y-auto bg-[var(--background)]">
                                <div className="max-w-6xl mx-auto space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                            <p className="text-[11px] font-black uppercase tracking-widest text-cyan-400">Triage Status</p>
                                            <p className="mt-3 text-2xl font-black text-white">{isTriageRunning ? 'Analyzing' : isTriageComplete ? 'Complete' : 'Ready'}</p>
                                            <p className="mt-2 text-sm text-gray-400">Classification, topology and technical inventory.</p>
                                        </div>
                                        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                            <p className="text-[11px] font-black uppercase tracking-widest text-cyan-400">Assets</p>
                                            <p className="mt-3 text-2xl font-black text-white">{assets.length}</p>
                                            <p className="mt-2 text-sm text-gray-400">Objects detected and available for analysis.</p>
                                        </div>
                                        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                            <p className="text-[11px] font-black uppercase tracking-widest text-cyan-400">Context</p>
                                            <p className="mt-3 text-2xl font-black text-white">{Object.keys(assetContexts).length + (userContext.trim() ? 1 : 0)}</p>
                                            <p className="mt-2 text-sm text-gray-400">Manual notes and project-specific guidance captured.</p>
                                        </div>
                                    </div>

                                    <div className="rounded-3xl border border-white/10 bg-black/20 p-8">
                                        <h2 className="text-xl font-black text-white">Stage Home</h2>
                                        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-gray-400">
                                            Use Triage to classify assets, inspect lineage and schema, and lock the final migration scope before Drafting.
                                        </p>

                                        {/* Sprint 1: Readiness summary */}
                                        <div className="mt-6">
                                            <ReadinessBadge projectId={projectId} variant="card" />
                                        </div>

                                        <div className="mt-6 flex flex-wrap gap-3">
                                            <button
                                                onClick={() => onSectionChange('run-triage')}
                                                disabled={isTriageRunning}
                                                className="px-5 py-2.5 bg-cyan-600 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-cyan-500 disabled:opacity-50"
                                            >
                                                {isTriageRunning ? 'Running Analysis...' : 'Run Analysis'}
                                            </button>
                                            <button
                                                onClick={() => onSectionChange('grid')}
                                                className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                            >
                                                Open Grid
                                            </button>
                                            <button
                                                onClick={() => onSectionChange('graph')}
                                                className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                            >
                                                Open Graph
                                            </button>
                                            <button
                                                onClick={() => onSectionChange('context')}
                                                className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                            >
                                                Project Context
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ORIGIN ANALYSIS TAB */}
                        {activeSection === 'origin' && (
                            <div className="h-full w-full overflow-hidden">
                                <OriginAnalysisPanel projectId={projectId} />
                            </div>
                        )}

                        {/* TRANSFORMATIONS MATRIX TAB */}
                        {activeSection === 'transform' && (
                            <div className="h-full w-full overflow-hidden">
                                <TransformationsMatrix projectId={projectId} />
                            </div>
                        )}

                        {/* SOURCE QUERIES TAB */}
                        {activeSection === 'queries' && (
                            <div className="h-full w-full overflow-hidden">
                                <SourceQueriesViewer projectId={projectId} />
                            </div>
                        )}

                        {/* QUALITY DASHBOARD TAB */}
                        {activeSection === 'quality' && (
                            <div className="h-full w-full overflow-hidden">
                                <CodeQualityAnalysis projectId={projectId} />
                            </div>
                        )}

                        {/* SCHEMA VIEWER TAB */}
                        {activeSection === 'schema' && (
                            <div className="h-full w-full overflow-hidden bg-[var(--background)]">
                                <SchemaViewer
                                    projectId={projectId}
                                    objectId={selectedAssetForSchema ?? undefined}
                                    assets={assets.filter(a => a.type !== 'LAYOUT')}
                                    initialTab={schemaInitialTab}
                                    onObjectSelect={(id) => setSelectedAssetForSchema(id || null)}
                                />
                            </div>
                        )}

                        {/* PII HEATMAP TAB */}
                        {activeSection === 'pii' && (
                            <div className="h-full w-full p-8 overflow-y-auto bg-[var(--background)]">
                                <PIIHeatmap projectId={projectId} />
                            </div>
                        )}

                        {/* TABLE REGISTRY TAB */}
                        {activeSection === 'tables' && (
                            <div className="h-full w-full p-8 overflow-y-auto bg-[var(--background)]">
                                <TableRegistry projectId={projectId} />
                            </div>
                        )}

                        {/* UNDERSTANDING TAB — Block 3 */}
                        {activeSection === 'understanding' && (
                            <div className="h-full w-full overflow-hidden">
                                <UnderstandingPanel projectId={projectId} />
                            </div>
                        )}

                        {/* EXPORT TAB — Block 4 */}
                        {activeSection === 'export' && (
                            <div className="h-full w-full overflow-y-auto p-8 bg-[var(--background)]">
                                <ExportPanel projectId={projectId} projectName={projectName || 'Project'} />
                            </div>
                        )}

                        {/* REFINEMENT TAB — Block 5 */}
                        {activeSection === 'refinement' && (
                            <div className="h-full w-full overflow-y-auto p-8 bg-[var(--background)]">
                                <RuleRefinementPanel projectId={projectId} />
                            </div>
                        )}

                        {/* GOVERNANCE TAB — Block 6 */}
                        {activeSection === 'governance' && (
                            <div className="h-full w-full overflow-y-auto p-8 bg-[var(--background)]">
                                <GovernancePanel projectId={projectId} />
                            </div>
                        )}

                        {/* 1. SCHEMA GRAPH / VISUALIZATION */}
                        {activeSection === 'graph' && (
                            <div className="h-full w-full bg-gray-50 dark:bg-gray-900 relative flex overflow-hidden">
                                {/* Graph Sidebar (Left) */}
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

                                            {isInitialLoading ? (
                                                <div className="p-12 text-center">
                                                    <div className="w-6 h-6 border-2 border-cyan-500 border-b-transparent rounded-full animate-spin mx-auto mb-3" />
                                                    <span className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-widest animate-pulse">Scanning...</span>
                                                </div>
                                            ) : (
                                                <div className="overflow-y-auto max-h-[calc(100vh-350px)] p-4 space-y-6">
                                                    {/* PENDING REVIEW SECTION */}
                                                    {assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT' && a.type !== 'LAYOUT').length > 0 && (
                                                        <div className="space-y-3">
                                                            <h5 className="text-[9px] font-black text-amber-500 uppercase tracking-widest pl-2">
                                                                Pending Review ({assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT' && a.type !== 'LAYOUT').length})
                                                            </h5>
                                                            {assets.filter(a => a.type !== 'CORE' && a.type !== 'IGNORED' && a.type !== 'SUPPORT' && a.type !== 'LAYOUT').map(asset => (
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
                                        onNodeClick={(node) => {
                                            setSelectedNodeData(node.data);
                                            setSelectedAssetForSchema(node.id);
                                        }}
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
                                                    <p className="text-xs text-[var(--text-tertiary)] mt-3 leading-relaxed">
                                                        This panel summarizes the selected asset, the target shape being proposed, and any risk flags worth reviewing before moving to schema details.
                                                    </p>
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
                                                        <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-4">Use this as the draft target shape for the asset.</p>
                                                        <div className="space-y-4">
                                                            <div>
                                                                <span className="text-[9px] font-bold text-gray-600 uppercase">Proposed Target:</span>
                                                                <p className="text-xs font-mono text-cyan-500 mt-1">{selectedNodeData.target_name || 'N/A'}</p>
                                                            </div>
                                                            <div>
                                                                <span className="text-[9px] font-bold text-gray-600 uppercase">Partitioning Hint:</span>
                                                                <p className="text-xs font-bold text-white mt-1">{selectedNodeData.metadata?.partition_key || 'No partitioning suggested'}</p>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <div className="p-5 bg-black/40 border border-white/5 rounded-2xl">
                                                        <div className="flex items-center gap-2 mb-3">
                                                            <Zap size={14} className="text-amber-500" />
                                                            <span className="text-[10px] font-black text-white uppercase tracking-widest">Actionable Intel</span>
                                                        </div>
                                                        <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-4">Quick flags that can change the migration path or review order.</p>
                                                        <div className="flex items-center gap-3">
                                                            <div className={`w-3 h-3 rounded-full ${selectedNodeData.metadata?.is_pii ? 'bg-red-500' : 'bg-gray-700'}`} />
                                                            <span className="text-[10px] font-bold text-gray-400 uppercase">
                                                                Sensitive Data Flag: {selectedNodeData.metadata?.is_pii ? 'YES (High Risk)' : 'NO (Clean)'}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* ACTION SHORTCUTS */}
                                                <div className="flex flex-col gap-2 pt-2 pb-4">
                                                    <button
                                                        onClick={() => {
                                                            // ✅ FIXED: Set selected asset FIRST, then navigate
                                                            setSelectedAssetForSchema(selectedNodeData.id);
                                                            setSchemaInitialTab('schema');
                                                            onSectionChange('schema');
                                                        }}
                                                        className="w-full py-3 bg-cyan-500 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-cyan-600 transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
                                                    >
                                                        <Layers size={14} /> View Schema Details
                                                    </button>
                                                    <button
                                                        onClick={() => {
                                                            // ✅ FIXED: Set selected asset FIRST, then navigate to mapping
                                                            setSelectedAssetForSchema(selectedNodeData.id);
                                                            setSchemaInitialTab('mapping');
                                                            onSectionChange('schema');
                                                        }}
                                                        className="w-full py-3 bg-white/5 border border-white/10 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-all flex items-center justify-center gap-2"
                                                    >
                                                        <Database size={14} /> Audit Mapping
                                                    </button>
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
                        {activeSection === 'grid' && (
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
                                                <th className="px-6 py-4">Schema</th>
                                                <th className="px-6 py-4 text-center">Include</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-[var(--border)] text-[var(--text-primary)]">
                                            {(() => {
                                                // Filter out LAYOUT type (system assets)
                                                const displayAssets = assets.filter(a => a.type !== 'LAYOUT');
                                                console.log('[TriageView Grid] assets:', assets.length, 'displayAssets:', displayAssets.length);
                                                return displayAssets.map(asset => (
                                                    <tr
                                                        key={asset.id}
                                                        onClick={() => {
                                                            setSelectedAssetForSchema(asset.id);
                                                            setSchemaInitialTab('schema');
                                                            onSectionChange('schema');
                                                        }}
                                                        className={`hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors cursor-pointer group ${selectedAssetForSchema === asset.id ? 'bg-blue-50/50 dark:bg-blue-900/10 ring-1 ring-inset ring-blue-500/30' : ''
                                                            }`}
                                                    >
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
                                                                        setSelectedAssetForSchema(asset.id);
                                                                        setSchemaInitialTab('mapping');
                                                                        onSectionChange('schema');
                                                                    }}
                                                                    className="p-1 text-gray-400 hover:text-primary transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                                                                    title="Column Mapping (Audit)"
                                                                >
                                                                    <Database size={12} />
                                                                </button>
                                                                <button
                                                                    onClick={() => {
                                                                        setSelectedAssetForSchema(asset.id);
                                                                        setSchemaInitialTab('schema');
                                                                        onSectionChange('schema');
                                                                    }}
                                                                    className="p-1 text-gray-400 hover:text-cyan-500 transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                                                                    title="View Schema"
                                                                >
                                                                    <Layers size={12} />
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
                                                        {/* Schema / Mismatch badge */}
                                                        <td className="px-6 py-4">
                                                            <MismatchBadge
                                                                projectId={projectId}
                                                                objectId={asset.id}
                                                                onClickSchema={() => {
                                                                    setSelectedAssetForSchema(asset.id);
                                                                    setSchemaInitialTab('mapping');
                                                                    onSectionChange('schema');
                                                                }}
                                                            />
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
                                                ));
                                            })()}
                                            {assets.filter(a => a.type !== 'LAYOUT').length === 0 && (
                                                <tr>
                                                    <td colSpan={8} className="px-6 py-8 text-center text-gray-400">
                                                        No assets found. {assets.length > 0 && `(${assets.length} system assets hidden)`}
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}



                        {/* 3. MAPPING TAB (Same as Schema but with mapping tab open) */}
                        {activeSection === 'mapping' && (
                            <div className="h-full w-full overflow-hidden bg-[var(--background)]">
                                <SchemaViewer
                                    projectId={projectId}
                                    objectId={selectedAssetForSchema ?? undefined}
                                    assets={assets.filter(a => a.type !== 'LAYOUT')}
                                    initialTab='mapping'
                                    onObjectSelect={(id) => setSelectedAssetForSchema(id || null)}
                                />
                            </div>
                        )}

                        {/* 4. MANUAL CONTEXT / BUSINESS CONTEXT TAB */}
                        {activeSection === 'context' && (
                            <div className="h-full w-full p-8 overflow-y-auto bg-gray-50 dark:bg-gray-950">
                                <div className="max-w-7xl mx-auto space-y-10">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                        <div className="rounded-xl border border-yellow-400/30 bg-yellow-50 dark:bg-yellow-900/20 p-4">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-yellow-700 dark:text-yellow-300">Global Context</p>
                                            <p className="mt-2 text-xl font-black text-yellow-900 dark:text-yellow-100">{userContext.trim() ? 'Captured' : 'Empty'}</p>
                                        </div>
                                        <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-4">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-cyan-400">Asset Contexts</p>
                                            <p className="mt-2 text-xl font-black text-white">{Object.keys(assetContexts).length}</p>
                                        </div>
                                        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-emerald-400">Guided Re-run</p>
                                            <p className="mt-2 text-xl font-black text-white">{userContext.trim() || Object.keys(assetContexts).length > 0 ? 'Ready' : 'Waiting'}</p>
                                        </div>
                                    </div>

                                    {/* Global Context */}
                                    <div className="space-y-6 pb-20">
                                        {/* Warning Banner */}
                                        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-400 dark:border-yellow-600 rounded-xl p-4 flex items-start gap-4">
                                            <div className="p-2 bg-yellow-400 dark:bg-yellow-600 rounded-lg shrink-0">
                                                <FileEdit size={24} className="text-white" />
                                            </div>
                                            <div>
                                                <h3 className="font-bold text-yellow-900 dark:text-yellow-200 mb-1 flex items-center gap-2">
                                                    <AlertTriangle size={18} className="text-yellow-600 dark:text-yellow-400" />
                                                    Editable Area: Source Code Analysis Instructions
                                                </h3>
                                                <p className="text-sm text-yellow-800 dark:text-yellow-300 leading-relaxed">
                                                    <strong className="font-bold">Everything highlighted in this section is editable.</strong> Define global rules that the Agent will apply during <strong>source code analysis and triage</strong>.
                                                    These instructions directly affect how the system interprets your legacy assets. <strong>After modifying, you must re-execute the Triage</strong> for changes to take effect.
                                                </p>
                                            </div>
                                        </div>

                                        <h2 className="text-xl font-bold flex items-center gap-2">
                                            <MessageSquare className="text-primary" /> Global Project Context
                                        </h2>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">
                                            Provide analysis guidelines for the agent (e.g., ignore specific schemas, prioritize certain packages, naming conventions). Markdown formatting supported.
                                        </p>

                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                            <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 p-4">
                                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Project-level guidance</p>
                                                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 leading-relaxed">Saved once and reused automatically on the next Triage run.</p>
                                            </div>
                                            <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 p-4">
                                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Per-asset notes</p>
                                                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 leading-relaxed">Each asset can carry notes and structured rules that travel with the rerun.</p>
                                            </div>
                                            <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 p-4">
                                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Preview before run</p>
                                                <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 leading-relaxed">The re-run dialog now shows how many context blocks and overrides will be applied.</p>
                                            </div>
                                        </div>

                                        {/* Split Panel: Editor (Left) + Preview (Right) */}
                                        <div className="grid grid-cols-2 gap-4">
                                            {/* Editor - HIGHLIGHTED IN YELLOW */}
                                            <div className="space-y-2">
                                                <label className="text-xs font-bold text-yellow-700 dark:text-yellow-400 uppercase flex items-center gap-2">
                                                    <FileEdit size={14} className="text-yellow-600" />
                                                    Markdown Editor (Editable)
                                                </label>
                                                <textarea
                                                    value={userContext}
                                                    onChange={(e) => setUserContext(e.target.value)}
                                                    placeholder="# Global Rules for Source Analysis\n\n## Exclusions\n- Ignore all 'audit_*' tables\n- Skip 'temp_' schemas\n\n## Priorities\n- Focus on Sales and Finance packages\n\n## Naming Conventions\n- Use 'stg_' prefix for staging layers\n- Use 'dim_' / 'fact_' for data warehouse"
                                                    className="w-full h-96 p-4 rounded-xl border-2 border-yellow-400 dark:border-yellow-600 bg-yellow-50 dark:bg-yellow-900/10 text-sm font-mono leading-relaxed focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 outline-none shadow-lg resize-none transition-all"
                                                />
                                            </div>

                                            {/* Preview */}
                                            <div className="space-y-2">
                                                <label className="text-xs font-bold text-gray-400 uppercase">Preview</label>
                                                <div className="w-full h-96 p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950 overflow-y-auto shadow-sm">
                                                    {userContext.trim() ? (
                                                        <div className="prose prose-sm dark:prose-invert max-w-none">
                                                            <ReactMarkdown>{userContext}</ReactMarkdown>
                                                        </div>
                                                    ) : (
                                                        <p className="text-xs text-gray-400 italic">Start typing to see preview...</p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex justify-between items-center">
                                            <p className="text-xs text-yellow-700 dark:text-yellow-400 flex items-center gap-2">
                                                <AlertTriangle size={14} />
                                                <span className="font-bold">Remember: Save changes and re-run Triage to apply new rules</span>
                                            </p>
                                            <button
                                                onClick={() => handleSaveContext('__global__', userContext, {}, true)}
                                                className="px-6 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-bold transition-colors flex items-center gap-2 shadow-lg"
                                                disabled={isSavingContext}
                                            >
                                                <Save size={16} /> {isSavingContext ? 'Saving...' : 'Save Context & Re-run Triage'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 5. LOGS TAB */}
                        {activeSection === 'logs' && (
                            <div className="h-full w-full p-8 overflow-y-auto bg-gray-50 dark:bg-gray-950">
                                <div className="max-w-5xl mx-auto space-y-4">

                                    {/* ── Completion Banner ── */}
                                    {isTriageComplete && !isTriageRunning && (
                                        <div className="flex items-center justify-between px-6 py-4 bg-sky-500/10 border border-sky-500/30 rounded-2xl animate-in fade-in slide-in-from-top-2 duration-300">
                                            <div className="flex items-center gap-3">
                                                <CheckCircle size={18} className="text-sky-400 shrink-0" />
                                                <div>
                                                    <p className="text-sm font-black text-sky-400 uppercase tracking-wide">Triage Complete</p>
                                                    <p className="text-xs text-gray-500 mt-0.5">All assets classified — review the grid or proceed to Drafting.</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => onSectionChange('grid')}
                                                    className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-sky-500/10 border border-white/10 hover:border-sky-500/30 text-sky-300 text-xs font-black uppercase tracking-wider rounded-xl transition-all active:scale-95"
                                                >
                                                    View Grid
                                                </button>
                                                <button
                                                    onClick={handleApprove}
                                                    className="flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-white text-xs font-black uppercase tracking-wider rounded-xl transition-all active:scale-95"
                                                >
                                                    Next: Drafting <ArrowRight size={13} />
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    <div className="flex items-center justify-between mb-6">
                                        <h2 className="text-xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
                                            <Terminal className="text-primary" /> Triage Execution Logs
                                        </h2>
                                        {!isTriageRunning && triageLog && (
                                            <button
                                                onClick={fetchTriageLogs}
                                                className="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 rounded-lg flex items-center gap-2 transition-colors"
                                            >
                                                <RefreshCw size={14} /> Refresh Logs
                                            </button>
                                        )}
                                    </div>
                                    <UnifiedLogViewer
                                        mode="realtime"
                                        projectId={projectId}
                                        isRunning={isTriageRunning}
                                        logs={triageLog ? triageLog.split('\n').filter(l => l.trim()) : []}
                                        processName={isTriageRunning ? "Triage Analysis (Running)" : "Triage Analysis (Last Execution)"}
                                        variant="panel"
                                    />
                                </div>
                            </div>
                        )}
                        {/* 6. FILES TAB */}
                        {activeSection === 'files' && (
                            <UnifiedFileExplorer projectId={projectId} activeTenantId={activeTenantId} />
                        )}
                    </div> {/* Close tab content div (flex-1 overflow-hidden relative) */}

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
                                                handleSaveContext(selectedAssetForContext, notes, rules, true);
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
                </div>
            </ReactFlowProvider>
            {ConfirmDialog}
            {showAssistant && (
                <ProjectAssistantModal
                    projectId={projectId}
                    projectName={projectName}
                    onClose={() => setShowAssistant(false)}
                />
            )}
        </>
    );
}
