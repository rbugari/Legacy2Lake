"use client";

import { useEffect, useState } from 'react';
import { Database, ArrowRight, ArrowLeft, Search, ChevronDown, ChevronRight } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface TableSummary {
    full_name: string;
    schema_name: string | null;
    table_name: string;
    readers_count: number;  // Using plural to match backend
    writers_count: number;  // Using plural to match backend
    total_impacts: number;
    operations: string[];
}

interface TableImpact {
    asset_id: string;
    asset_name: string;
    operation: string;
    sql_statement: string | null;
    columns_affected: string[] | null;
}

interface TableDetail {
    full_name: string;
    schema_name: string | null;
    table_name: string;
    readers: TableImpact[];
    writers: TableImpact[];
}

export default function TableRegistry({ projectId }: { projectId: string }) {
    const [tables, setTables] = useState<TableSummary[]>([]);
    const [selectedTable, setSelectedTable] = useState<string | null>(null);
    const [tableDetail, setTableDetail] = useState<TableDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadTables();
    }, [projectId]);

    const loadTables = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const res = await fetchWithAuth(`projects/${projectId}/tables/summary`);
            
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            
            const data = await res.json();
            setTables(data);
        } catch (e) {
            console.error('[TableRegistry] Load failed:', e);
            setError(e instanceof Error ? e.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const loadTableDetail = async (tableName: string) => {
        try {
            setDetailLoading(true);
            
            const res = await fetchWithAuth(`projects/${projectId}/tables/${encodeURIComponent(tableName)}/detail`);
            
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            
            const data = await res.json();
            setTableDetail(data);
            setSelectedTable(tableName);
        } catch (e) {
            console.error('[TableRegistry] Detail load failed:', e);
            setError(e instanceof Error ? e.message : 'Unknown error');
        } finally {
            setDetailLoading(false);
        }
    };

    const toggleTable = (tableName: string) => {
        if (selectedTable === tableName) {
            setSelectedTable(null);
            setTableDetail(null);
        } else {
            loadTableDetail(tableName);
        }
    };

    const filteredTables = tables.filter(t => 
        t.full_name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-sm text-gray-500">Loading table registry...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
                <Database size={32} className="mx-auto text-red-500 mb-2" />
                <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
            </div>
        );
    }

    if (tables.length === 0) {
        return (
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-8 text-center">
                <Database size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-bold mb-2">No Tables Found</h3>
                <p className="text-sm text-gray-500">Run Triage to analyze table impacts.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Database size={20} className="text-blue-600 dark:text-blue-400" />
                    <h3 className="text-lg font-bold">Table Registry</h3>
                    <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold rounded-full">
                        {tables.length}
                    </span>
                </div>
            </div>

            {/* Search */}
            <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search tables..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
            </div>

            {/* Table List */}
            <div className="space-y-2">
                {filteredTables.map((table) => (
                    <div key={table.full_name} className="border border-gray-200 dark:border-gray-800 rounded-lg overflow-hidden">
                        {/* Table Header */}
                        <button
                            onClick={() => toggleTable(table.full_name)}
                            className="w-full px-4 py-3 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-between"
                        >
                            <div className="flex items-center gap-3">
                                {selectedTable === table.full_name ? 
                                    <ChevronDown size={16} className="text-gray-500" /> : 
                                    <ChevronRight size={16} className="text-gray-500" />
                                }
                                <div className="text-left">
                                    <p className="font-mono text-sm font-bold text-gray-900 dark:text-gray-100">
                                        {table.full_name}
                                    </p>
                                    <div className="flex items-center gap-3 mt-1">
                                        <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
                                            <ArrowLeft size={12} />
                                            {table.readers_count} readers
                                        </span>
                                        <span className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
                                            <ArrowRight size={12} />
                                            {table.writers_count} writers
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                {table.operations.map((op) => (
                                    <span 
                                        key={op}
                                        className={`px-2 py-1 rounded text-xs font-bold ${
                                            op === 'SELECT' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                                            op === 'INSERT' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' :
                                            op === 'UPDATE' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400' :
                                            op === 'DELETE' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                                            'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                        }`}
                                    >
                                        {op}
                                    </span>
                                ))}
                            </div>
                        </button>

                        {/* Table Detail (Expanded) */}
                        {selectedTable === table.full_name && (
                            <div className="border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 p-4">
                                {detailLoading ? (
                                    <div className="flex items-center justify-center py-8">
                                        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                    </div>
                                ) : tableDetail ? (
                                    <div className="space-y-4">
                                        {/* Readers */}
                                        {tableDetail.readers.length > 0 && (
                                            <div>
                                                <h4 className="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase mb-2 flex items-center gap-2">
                                                    <ArrowLeft size={14} />
                                                    Readers ({tableDetail.readers.length})
                                                </h4>
                                                <div className="space-y-2">
                                                    {tableDetail.readers.map((reader, idx) => (
                                                        <div key={idx} className="bg-white dark:bg-gray-800 rounded p-3 text-xs">
                                                            <p className="font-mono font-bold text-gray-900 dark:text-gray-100">{reader.asset_name}</p>
                                                            <p className="text-gray-600 dark:text-gray-400 mt-1">
                                                                <span className="font-semibold">{reader.operation}</span>
                                                                {reader.columns_affected && reader.columns_affected.length > 0 && (
                                                                    <span className="ml-2">
                                                                        → {reader.columns_affected.slice(0, 3).join(', ')}
                                                                        {reader.columns_affected.length > 3 && ` +${reader.columns_affected.length - 3} more`}
                                                                    </span>
                                                                )}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Writers */}
                                        {tableDetail.writers.length > 0 && (
                                            <div>
                                                <h4 className="text-xs font-bold text-gray-600 dark:text-gray-400 uppercase mb-2 flex items-center gap-2">
                                                    <ArrowRight size={14} />
                                                    Writers ({tableDetail.writers.length})
                                                </h4>
                                                <div className="space-y-2">
                                                    {tableDetail.writers.map((writer, idx) => (
                                                        <div key={idx} className="bg-white dark:bg-gray-800 rounded p-3 text-xs">
                                                            <p className="font-mono font-bold text-gray-900 dark:text-gray-100">{writer.asset_name}</p>
                                                            <p className="text-gray-600 dark:text-gray-400 mt-1">
                                                                <span className="font-semibold">{writer.operation}</span>
                                                                {writer.columns_affected && writer.columns_affected.length > 0 && (
                                                                    <span className="ml-2">
                                                                        → {writer.columns_affected.slice(0, 3).join(', ')}
                                                                        {writer.columns_affected.length > 3 && ` +${writer.columns_affected.length - 3} more`}
                                                                    </span>
                                                                )}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <p className="text-sm text-gray-500 text-center py-4">No details available</p>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {filteredTables.length === 0 && searchTerm && (
                <div className="text-center py-8">
                    <p className="text-sm text-gray-500">No tables match "{searchTerm}"</p>
                </div>
            )}
        </div>
    );
}
