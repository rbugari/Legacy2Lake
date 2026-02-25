"use client";
import React, { useState, useEffect } from 'react';
import { Database, Key, Link2, ChevronDown, ChevronRight, AlertCircle, Table2, Search, X, Package, ArrowLeftRight } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';
import TypeMismatchViewer from './TypeMismatchViewer';

interface Column {
    name: string;
    type: string;
    nullable: boolean;
    is_pk: boolean;
    is_fk: boolean;
    is_used?: boolean;
    description?: string;
}

interface ForeignKey {
    column: string;
    ref_table: string;
    ref_column: string;
}

interface TableEntry {
    table_name: string;
    columns: Column[];
    primary_key?: string;
    foreign_keys?: ForeignKey[];
    source_file?: string;
    layer?: 'bronze' | 'silver' | 'gold';  // Medallion Architecture layer
}

interface SchemaResponse {
    source_name: string;
    target_name: string;
    tables: TableEntry[];
    source_tables: TableEntry[];
    target_tables: TableEntry[];
    total_tables: number;
    schema_available: boolean;
}

interface Asset {
    object_id?: string;
    id?: string;
    source_name?: string;
    filename?: string;
    target_name?: string;
    category?: string;
    type?: string;
}

interface SchemaViewerProps {
    projectId: string;
    objectId?: string;
    assets?: Asset[];
    onObjectSelect?: (id: string) => void;
    showHistory?: boolean;
    initialTab?: 'schema' | 'mapping';
}

export default function SchemaViewer({
    projectId,
    objectId,
    assets = [],
    onObjectSelect,
    showHistory = true,
    initialTab = 'schema'
}: SchemaViewerProps) {
    const [data, setData] = useState<SchemaResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
    const [search, setSearch] = useState('');
    const [schemaTab, setSchemaTab] = useState<'schema' | 'mapping'>(initialTab);

    // Sync tab if prop changes
    useEffect(() => {
        setSchemaTab(initialTab);
    }, [initialTab]);

    // Internal selection state (used when no objectId is pre-selected from grid)
    const [internalObjectId, setInternalObjectId] = useState<string | null>(null);

    const activeObjectId = objectId ?? internalObjectId ?? null;

    useEffect(() => {
        if (!activeObjectId) {
            setData(null);
            return;
        }

        const fetchSchema = async () => {
            try {
                setLoading(true);
                setError(null);

                const res = await fetchWithAuth(
                    `projects/${projectId}/objects/${activeObjectId}/schema`
                );

                if (!res.ok) {
                    throw new Error(`Failed to fetch schema: ${res.statusText}`);
                }

                const json = await res.json();
                setData(json);

                // Auto-expand first table
                if (json.tables && json.tables.length > 0) {
                    setExpandedTables(new Set([json.tables[0].table_name]));
                }
            } catch (err: any) {
                console.error('Error fetching schema:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchSchema();
    }, [projectId, activeObjectId]);

    const toggleTable = (tableName: string) => {
        const next = new Set(expandedTables);
        if (next.has(tableName)) next.delete(tableName);
        else next.add(tableName);
        setExpandedTables(next);
    };

    const handleSelectAsset = (asset: Asset) => {
        const id = asset.object_id ?? asset.id ?? '';
        if (!id) return;
        setInternalObjectId(id);
        onObjectSelect?.(id);
    };

    const handleClearSelection = () => {
        setInternalObjectId(null);
        setData(null);
        setError(null);
        // Notify parent so it also clears its selectedAssetForSchema
        onObjectSelect?.('');
    };

    // Filter assets for the selector (exclude IGNORED, show CORE + SUPPORT)
    const selectableAssets = assets.filter(a => {
        const t = (a.type || '').toUpperCase();
        return t !== 'IGNORED';
    });

    const filteredAssets = selectableAssets.filter(a => {
        const name = (a.source_name || a.filename || '').toLowerCase();
        const target = (a.target_name || '').toLowerCase();
        const q = search.toLowerCase();
        return name.includes(q) || target.includes(q);
    });

    // ─── SELECTOR PANEL (no object selected) ─────────────────────────────────
    if (!activeObjectId) {
        return (
            <div className="flex flex-col h-full">
                {/* Header */}
                <div className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
                    <div className="flex items-center gap-3 mb-3">
                        <Database className="w-5 h-5 text-cyan-500" />
                        <div>
                            <h3 className="text-base font-semibold text-gray-900 dark:text-white">Schema Explorer</h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Select an object to view its DDL schema</p>
                        </div>
                    </div>
                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Filter objects..."
                            className="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:text-white"
                        />
                        {search && (
                            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2">
                                <X className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Asset list */}
                <div className="flex-1 overflow-auto p-3 space-y-1">
                    {filteredAssets.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center py-12">
                            <Package className="w-10 h-10 text-gray-300 dark:text-gray-600 mb-3" />
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                {selectableAssets.length === 0
                                    ? 'No objects available. Run Triage first.'
                                    : 'No objects match your search.'}
                            </p>
                        </div>
                    ) : (
                        filteredAssets.map((asset) => {
                            const id = asset.object_id ?? asset.id ?? '';
                            const name = asset.source_name || asset.filename || 'Unknown';
                            const target = asset.target_name || '';
                            const type = (asset.type || '').toUpperCase();
                            const isCore = type === 'CORE';
                            const ext = name.split('.').pop()?.toLowerCase() || '';

                            return (
                                <button
                                    key={id}
                                    onClick={() => handleSelectAsset(asset)}
                                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left group"
                                >
                                    {/* Icon */}
                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isCore
                                        ? 'bg-cyan-50 dark:bg-cyan-900/20'
                                        : 'bg-gray-100 dark:bg-gray-800'
                                        }`}>
                                        <Database className={`w-4 h-4 ${isCore ? 'text-cyan-500' : 'text-gray-400'}`} />
                                    </div>

                                    {/* Name + target */}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{name}</p>
                                        {target && (
                                            <p className="text-xs text-gray-400 dark:text-gray-500 truncate font-mono">→ {target}</p>
                                        )}
                                    </div>

                                    {/* Badge */}
                                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ${isCore
                                        ? 'bg-cyan-50 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400'
                                        : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                                        }`}>
                                        {ext.toUpperCase() || type}
                                    </span>
                                </button>
                            );
                        })
                    )}
                </div>
            </div>
        );
    }

    // ─── SCHEMA DETAIL VIEW (object selected) ────────────────────────────────

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Loading schema...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex flex-col">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
                    <button onClick={handleClearSelection} className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1">
                        ← Back to list
                    </button>
                </div>
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
                        <p className="text-red-500 text-sm mb-1">Error loading schema</p>
                        <p className="text-gray-400 text-xs">{error}</p>
                    </div>
                </div>
            </div>
        );
    }

    if (!data || !data.schema_available) {
        return (
            <div className="h-full flex flex-col">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
                    <button onClick={handleClearSelection} className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1">
                        ← Back to list
                    </button>
                </div>
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <Database className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-500 text-sm font-medium">No schema available</p>
                        <p className="text-gray-400 text-xs mt-1">Run Triage to extract DDL schema from SQL files.</p>
                    </div>
                </div>
            </div>
        );
    }

    if (data.tables.length === 0 && data.source_tables.length === 0 && data.target_tables.length === 0) {
        return (
            <div className="h-full flex flex-col">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-800">
                    <button onClick={handleClearSelection} className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1">
                        ← Back to list
                    </button>
                </div>
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <Table2 className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-500 text-sm font-medium">No matching table found</p>
                        <p className="text-gray-400 text-xs mt-1 px-8">
                            We found schema data for the project, but nothing matching <span className="font-mono text-cyan-500 font-bold">{data.target_name || data.source_name}</span>.
                        </p>
                        <button
                            onClick={handleClearSelection}
                            className="mt-6 px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-xs font-bold transition-all"
                        >
                            Explore all Project Tables
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Group tables by Medallion layer (Bronze/Silver/Gold)
    const allTables = data.tables || data.source_tables?.concat(data.target_tables || []) || [];
    const bronzeTables = allTables.filter(t => t.layer === 'bronze');
    const silverTables = allTables.filter(t => t.layer === 'silver');
    const goldTables = allTables.filter(t => t.layer === 'gold');
    const hasLayers = bronzeTables.length > 0 || silverTables.length > 0 || goldTables.length > 0;

    const renderTableCard = (table: TableEntry, accentColor: string) => {
        const isExpanded = expandedTables.has(table.table_name);
        return (
            <div
                key={table.table_name}
                className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden"
            >
                <button
                    onClick={() => toggleTable(table.table_name)}
                    className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                        <Table2 className={`w-3.5 h-3.5 flex-shrink-0 ${accentColor}`} />
                        <span className="font-semibold text-xs text-gray-900 dark:text-white font-mono truncate">
                            {table.table_name}
                        </span>
                        <span className="text-[10px] text-gray-400 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full flex-shrink-0">
                            {table.columns.length} cols
                        </span>
                    </div>
                    {isExpanded
                        ? <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                        : <ChevronRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                    }
                </button>

                {isExpanded && (
                    <div className="border-t border-gray-200 dark:border-gray-800">
                        <table className="w-full text-xs">
                            <thead className="bg-gray-50 dark:bg-gray-800">
                                <tr>
                                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Column</th>
                                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Key</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                {table.columns.map((col, idx) => {
                                    const isUsed = col.is_used !== false; // Default to true if not provided (backward compat)
                                    return (
                                        <tr
                                            key={idx}
                                            className={`hover:bg-gray-50 dark:hover:bg-gray-800/40 ${!isUsed ? 'opacity-40 grayscale-[0.5]' : ''}`}
                                            title={!isUsed ? "This column is not identified as used in the source query" : ""}
                                        >
                                            <td className="px-3 py-1.5 font-mono text-gray-900 dark:text-white">
                                                <div className="flex items-center gap-1">
                                                    {col.name}
                                                    {col.is_pk && <Key className="w-2.5 h-2.5 text-yellow-500 flex-shrink-0" title="Primary Key" />}
                                                    {col.is_fk && <Link2 className="w-2.5 h-2.5 text-blue-500 flex-shrink-0" title="Foreign Key" />}
                                                    {isUsed && col.is_used && <div className="w-1 h-1 rounded-full bg-emerald-500 ml-1" title="Used in Package Query" />}
                                                </div>
                                            </td>
                                            <td className="px-3 py-1.5 font-mono text-gray-500 dark:text-gray-400">{col.type}</td>
                                            <td className="px-3 py-1.5">
                                                <div className="flex items-center gap-1.5">
                                                    {col.is_pk && <span className="text-yellow-600 dark:text-yellow-500 font-bold">PK</span>}
                                                    {col.is_fk && <span className="text-blue-500 font-bold">FK</span>}
                                                    {!isUsed && <span className="text-[10px] text-gray-400 bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">Unused</span>}
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="px-4 py-3 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
                <button
                    onClick={handleClearSelection}
                    className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1 mb-2"
                >
                    ← Back to list
                </button>
                <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-cyan-500" />
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        {data.target_name || data.source_name}
                    </span>
                    {hasLayers && (
                        <>
                            {bronzeTables.length > 0 && (
                                <span className="text-xs text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 px-2 py-0.5 rounded-full">
                                    🥉 {bronzeTables.length} bronze
                                </span>
                            )}
                            {silverTables.length > 0 && (
                                <span className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20 px-2 py-0.5 rounded-full">
                                    🥈 {silverTables.length} silver
                                </span>
                            )}
                            {goldTables.length > 0 && (
                                <span className="text-xs text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 px-2 py-0.5 rounded-full">
                                    🥇 {goldTables.length} gold
                                </span>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Tab bar */}
            <div className="flex border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-black/20 flex-shrink-0">
                <button
                    onClick={() => setSchemaTab('schema')}
                    className={`px-4 py-2 text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border-b-2 transition-all ${schemaTab === 'schema'
                        ? 'border-cyan-500 text-cyan-500'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                        }`}
                >
                    <Database className="w-3 h-3" /> Schema
                </button>
                <button
                    onClick={() => setSchemaTab('mapping')}
                    className={`px-4 py-2 text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 border-b-2 transition-all ${schemaTab === 'mapping'
                        ? 'border-orange-500 text-orange-400'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                        }`}
                >
                    <ArrowLeftRight className="w-3 h-3" /> Type Mapping
                </button>
            </div>
            {/* Tab content */}
            {schemaTab === 'mapping' && activeObjectId ? (
                <div className="flex-1 overflow-hidden">
                    <TypeMismatchViewer projectId={projectId} objectId={activeObjectId} />
                </div>
            ) : (
                <div className="flex-1 overflow-hidden flex">
                    {/* BRONZE layer */}
                    {bronzeTables.length > 0 && (
                        <div className="flex-1 flex flex-col border-r border-gray-200 dark:border-gray-800 min-w-0">
                            <div className="px-3 py-2 bg-orange-50 dark:bg-orange-900/10 border-b border-orange-100 dark:border-orange-900/30 flex-shrink-0">
                                <p className="text-[10px] font-black uppercase tracking-widest text-orange-600 dark:text-orange-400 flex items-center gap-1">
                                    🥉 Bronze Layer
                                </p>
                                <p className="text-[9px] text-orange-500 dark:text-orange-500 mt-0.5">Raw data ingestion</p>
                            </div>
                            <div className="flex-1 overflow-auto p-2 space-y-1.5">
                                {bronzeTables.map(t => renderTableCard(t, 'text-orange-500'))}
                            </div>
                        </div>
                    )}

                    {/* SILVER layer */}
                    {silverTables.length > 0 && (
                        <div className="flex-1 flex flex-col border-r border-gray-200 dark:border-gray-800 min-w-0">
                            <div className="px-3 py-2 bg-gray-50 dark:bg-gray-900/10 border-b border-gray-100 dark:border-gray-900/30 flex-shrink-0">
                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-600 dark:text-gray-400 flex items-center gap-1">
                                    🥈 Silver Layer
                                </p>
                                <p className="text-[9px] text-gray-500 dark:text-gray-500 mt-0.5">Cleaned & validated</p>
                            </div>
                            <div className="flex-1 overflow-auto p-2 space-y-1.5">
                                {silverTables.map(t => renderTableCard(t, 'text-gray-500'))}
                            </div>
                        </div>
                    )}

                    {/* GOLD layer */}
                    {goldTables.length > 0 && (
                        <div className="flex-1 flex flex-col min-w-0">
                            <div className="px-3 py-2 bg-yellow-50 dark:bg-yellow-900/10 border-b border-yellow-100 dark:border-yellow-900/30 flex-shrink-0">
                                <p className="text-[10px] font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
                                    🥇 Gold Layer
                                </p>
                                <p className="text-[9px] text-yellow-500 dark:text-yellow-500 mt-0.5">Business aggregations</p>
                            </div>
                            <div className="flex-1 overflow-auto p-2 space-y-1.5">
                                {goldTables.map(t => renderTableCard(t, 'text-yellow-600'))}
                            </div>
                        </div>
                    )}

                    {/* Fallback: no layer detection available yet */}
                    {!hasLayers && allTables.length > 0 && (
                        <div className="flex-1 overflow-auto p-3 space-y-2">
                            <div className="text-xs text-gray-500 mb-2 p-2 bg-gray-50 dark:bg-gray-800 rounded">
                                ℹ️ Layer information not available - showing all tables
                            </div>
                            {allTables.map(t => renderTableCard(t, 'text-cyan-500'))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
