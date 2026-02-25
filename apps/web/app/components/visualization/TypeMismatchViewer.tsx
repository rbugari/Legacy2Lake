"use client";
import React, { useState, useEffect, useCallback } from 'react';
import { fetchWithAuth } from '../../lib/auth-client';
import { AlertTriangle, CheckCircle, PlusCircle, MinusCircle, RefreshCw, ArrowRight, Filter } from 'lucide-react';

interface Comparison {
    column: string;
    source_type: string | null;
    target_type: string | null;
    status: 'OK' | 'MISMATCH' | 'NEW' | 'MISSING';
}

interface MismatchData {
    object_id: string;
    source_table: string;
    target_table: string;
    comparisons: Comparison[];
    mismatch_count: number;
    total_columns: number;
    schema_available: boolean;
}

interface Props {
    projectId: string;
    objectId: string;
}

const STATUS_CONFIG = {
    MISMATCH: {
        label: 'Type Mismatch',
        icon: <AlertTriangle className="w-3.5 h-3.5" />,
        row: 'bg-orange-500/5 border-l-2 border-orange-500',
        badge: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
    },
    MISSING: {
        label: 'Missing in Source',
        icon: <MinusCircle className="w-3.5 h-3.5" />,
        row: 'bg-red-500/5 border-l-2 border-red-500',
        badge: 'bg-red-500/15 text-red-400 border border-red-500/30',
    },
    NEW: {
        label: 'Not in Target',
        icon: <PlusCircle className="w-3.5 h-3.5" />,
        row: 'bg-blue-500/5 border-l-2 border-blue-500',
        badge: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
    },
    OK: {
        label: 'Compatible',
        icon: <CheckCircle className="w-3.5 h-3.5" />,
        row: '',
        badge: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
    },
};

export default function TypeMismatchViewer({ projectId, objectId }: Props) {
    const [data, setData] = useState<MismatchData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filterMismatches, setFilterMismatches] = useState(false);

    const load = useCallback(async () => {
        if (!objectId) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/objects/${objectId}/type-mismatches`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            setData(json);
        } catch (e: any) {
            setError(e.message || 'Failed to load mismatch data');
        } finally {
            setLoading(false);
        }
    }, [projectId, objectId]);

    useEffect(() => { load(); }, [load]);

    if (loading) return (
        <div className="flex items-center justify-center h-48 gap-3 text-gray-500">
            <RefreshCw className="w-5 h-5 animate-spin text-cyan-500" />
            <span className="text-sm font-bold uppercase tracking-widest">Analyzing column types...</span>
        </div>
    );

    if (error) return (
        <div className="flex items-center justify-center h-48 text-red-400 text-sm font-mono">{error}</div>
    );

    if (!data || !data.schema_available) return (
        <div className="flex flex-col items-center justify-center h-48 gap-3 text-gray-500">
            <AlertTriangle className="w-8 h-8 text-amber-500/50" />
            <p className="text-sm font-bold uppercase tracking-widest">No schema data available</p>
            <p className="text-xs text-gray-600">Run Triage to generate schema_reference.json</p>
        </div>
    );

    const displayed = filterMismatches
        ? data.comparisons.filter(c => c.status !== 'OK')
        : data.comparisons;

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-black/20 shrink-0">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-xs font-mono text-gray-500">
                        <span className="text-white font-bold">{data.source_table || '—'}</span>
                        <ArrowRight className="w-3 h-3" />
                        <span className="text-cyan-400 font-bold">{data.target_table || '—'}</span>
                    </div>
                    {data.mismatch_count > 0 && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-orange-500/15 text-orange-400 border border-orange-500/30 uppercase tracking-widest">
                            {data.mismatch_count} issue{data.mismatch_count !== 1 ? 's' : ''}
                        </span>
                    )}
                    {data.mismatch_count === 0 && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase tracking-widest">
                            All Compatible
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setFilterMismatches(f => !f)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${filterMismatches
                                ? 'bg-orange-500/20 text-orange-400 border border-orange-500/40'
                                : 'bg-white/5 text-gray-500 hover:text-white border border-white/5'
                            }`}
                    >
                        <Filter className="w-3 h-3" />
                        Issues Only
                    </button>
                    <button onClick={load} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-500 hover:text-white transition-colors">
                        <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-3 px-4 py-2 border-b border-gray-100 dark:border-white/5 shrink-0">
                {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
                    <div key={key} className={`flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest ${cfg.badge}`}>
                        {cfg.icon}
                        {cfg.label}
                    </div>
                ))}
            </div>

            {/* Table */}
            <div className="flex-1 overflow-y-auto">
                <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-gray-50 dark:bg-[#0f0f0f] border-b border-gray-100 dark:border-white/5 z-10">
                        <tr>
                            <th className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-gray-500">Column</th>
                            <th className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-gray-500">Source Type</th>
                            <th className="px-4 py-2.5 text-center text-[10px] font-black uppercase tracking-widest text-gray-500">→</th>
                            <th className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-gray-500">Target Type</th>
                            <th className="px-4 py-2.5 text-left text-[10px] font-black uppercase tracking-widest text-gray-500">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-white/5">
                        {displayed.map((row, i) => {
                            const cfg = STATUS_CONFIG[row.status];
                            return (
                                <tr key={i} className={`${cfg.row} hover:bg-white/5 transition-colors`}>
                                    <td className="px-4 py-2 font-mono text-gray-900 dark:text-white font-medium">
                                        {row.column}
                                    </td>
                                    <td className="px-4 py-2 font-mono text-gray-500 dark:text-gray-400">
                                        {row.source_type ?? <span className="text-gray-600 italic">—</span>}
                                    </td>
                                    <td className="px-4 py-2 text-center text-gray-600">
                                        <ArrowRight className="w-3 h-3 mx-auto" />
                                    </td>
                                    <td className="px-4 py-2 font-mono text-gray-500 dark:text-gray-400">
                                        {row.target_type ?? <span className="text-gray-600 italic">—</span>}
                                    </td>
                                    <td className="px-4 py-2">
                                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest ${cfg.badge}`}>
                                            {cfg.icon}
                                            {cfg.label}
                                        </span>
                                    </td>
                                </tr>
                            );
                        })}
                        {displayed.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-4 py-12 text-center text-gray-500 text-xs font-bold uppercase tracking-widest">
                                    No issues found
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Footer summary */}
            <div className="px-4 py-2 border-t border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-black/20 flex items-center gap-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest shrink-0">
                <span>{data.total_columns} total columns</span>
                <span>·</span>
                <span className={data.mismatch_count > 0 ? 'text-orange-400' : 'text-emerald-400'}>
                    {data.mismatch_count} issues
                </span>
                <span>·</span>
                <span>{data.comparisons.filter(c => c.status === 'OK').length} compatible</span>
            </div>
        </div>
    );
}
