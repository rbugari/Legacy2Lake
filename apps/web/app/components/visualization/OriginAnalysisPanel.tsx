"use client";
import React, { useState, useEffect } from 'react';
import { Database, Server, HardDrive, Link2, CheckCircle, AlertCircle, Loader, Package } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface SourceSystem {
    server: string;
    database: string;
    table_count: number;
    tables: string[];
}

interface Connection {
    name: string;
    id: string;
    type: string;
    server: string;
    database: string;
}

interface OriginAnalysisData {
    source_systems: SourceSystem[];
    total_packages: number;
    total_tables: number;
    total_connections: number;
    connections: Connection[];
    all_tables: string[];
    timestamp: string | null;
    message?: string;
}

interface OriginAnalysisPanelProps {
    projectId: string;
}

export default function OriginAnalysisPanel({ projectId }: OriginAnalysisPanelProps) {
    const [data, setData] = useState<OriginAnalysisData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchOriginAnalysis = async () => {
            try {
                setLoading(true);
                setError(null);

                const res = await fetchWithAuth(`projects/${projectId}/origin-analysis`);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch origin analysis: ${res.statusText}`);
                }

                const analysisData = await res.json();
                setData(analysisData);
            } catch (err: any) {
                console.error('Error fetching origin analysis:', err);
                setError(err.message || 'Failed to load origin analysis');
            } finally {
                setLoading(false);
            }
        };

        fetchOriginAnalysis();
    }, [projectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3">
                    <Loader className="animate-spin text-emerald-500" size={32} />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                        Loading origin analysis...
                    </span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3 text-center px-4">
                    <AlertCircle className="text-red-500" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            Error Loading Origin Analysis
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {error}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!data || data.source_systems.length === 0) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3 text-center px-4">
                    <Database className="text-gray-400" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            No Origin Analysis Available
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {data?.message || "Run Discovery and Triage to analyze source systems"}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-auto bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center">
                        <Server size={24} className="text-blue-500" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-[var(--text-primary)]">Origin Analysis</h2>
                        <p className="text-sm text-[var(--text-tertiary)]">Consolidated source systems across all packages</p>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center gap-3 mb-2">
                            <Package size={20} className="text-purple-500" />
                            <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Packages</span>
                        </div>
                        <p className="text-4xl font-black text-[var(--text-primary)]">{data.total_packages}</p>
                    </div>
                    
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center gap-3 mb-2">
                            <Database size={20} className="text-emerald-500" />
                            <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Source Tables</span>
                        </div>
                        <p className="text-4xl font-black text-emerald-600">{data.total_tables}</p>
                    </div>
                    
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center gap-3 mb-2">
                            <Link2 size={20} className="text-cyan-500" />
                            <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Connections</span>
                        </div>
                        <p className="text-4xl font-black text-cyan-600">{data.total_connections}</p>
                    </div>
                </div>

                {/* Source Systems List */}
                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                        <Server size={18} className="text-blue-500" />
                        Source Systems
                    </h3>
                    
                    {data.source_systems.map((system, idx) => (
                        <div key={idx} className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <HardDrive size={16} className="text-blue-500" />
                                        <span className="font-bold text-[var(--text-primary)]">{system.server}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                        <Database size={14} />
                                        {system.database}
                                    </div>
                                </div>
                                <div className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                    <span className="text-xs font-bold text-blue-700 dark:text-blue-300">
                                        {system.table_count} {system.table_count === 1 ? 'table' : 'tables'}
                                    </span>
                                </div>
                            </div>
                            
                            {system.tables.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                                    <p className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Tables:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {system.tables.map((table, tidx) => (
                                            <span 
                                                key={tidx}
                                                className="px-2 py-1 bg-gray-100 dark:bg-gray-900 rounded text-xs font-mono text-gray-700 dark:text-gray-300"
                                            >
                                                {table}
                                            </span>
                                        ))}
                                        {system.table_count > system.tables.length && (
                                            <span className="px-2 py-1 text-xs text-gray-500">
                                                +{system.table_count - system.tables.length} more
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Connections Detail */}
                {data.connections.length > 0 && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                            <Link2 size={18} className="text-cyan-500" />
                            Connection Strings
                        </h3>
                        
                        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50 dark:bg-gray-900">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Name</th>
                                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Type</th>
                                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Server</th>
                                        <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Database</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {data.connections.map((conn, idx) => (
                                        <tr key={idx}>
                                            <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{conn.name}</td>
                                            <td className="px-4 py-3">
                                                <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 rounded text-xs font-bold text-purple-700 dark:text-purple-300">
                                                    {conn.type}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{conn.server}</td>
                                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{conn.database}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
