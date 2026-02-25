"use client";
import React, { useState, useEffect } from 'react';
import { Zap, TrendingUp, AlertTriangle, CheckCircle, Loader, Info, ArrowRight } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface TransformationsData {
    total_assets: number;
    total_transformations: number;
    transformations: Array<{
        asset_name: string;
        source_column: string;
        target_column: string;
        source_datatype: string;
        target_datatype: string;
        transformation_type: string;
        description: string;
        logic?: string;
    }>;
    transformation_types: Record<string, number>;
    recommendations: string[];
    timestamp: string | null;
    message?: string;
}

interface TransformationsMatrixProps {
    projectId: string;
}

// Map transformation types to colors and icons
const TRANSFORMATION_STYLES: Record<string, { color: string; bgColor: string; label: string; emoji: string }> = {
    'rename': { color: 'text-blue-700 dark:text-blue-300', bgColor: 'bg-blue-100 dark:bg-blue-900/30', label: 'Rename', emoji: '✏️' },
    'type_conversion': { color: 'text-orange-700 dark:text-orange-300', bgColor: 'bg-orange-100 dark:bg-orange-900/30', label: 'Type Cast', emoji: '🔄' },
    'business_logic': { color: 'text-purple-700 dark:text-purple-300', bgColor: 'bg-purple-100 dark:bg-purple-900/30', label: 'Business Logic', emoji: '⚙️' },
    'derived': { color: 'text-pink-700 dark:text-pink-300', bgColor: 'bg-pink-100 dark:bg-pink-900/30', label: 'Derived', emoji: '📝' },
    'passthrough': { color: 'text-gray-700 dark:text-gray-300', bgColor: 'bg-gray-100 dark:bg-gray-900/30', label: 'Passthrough', emoji: '➡️' },
};

export default function TransformationsMatrix({ projectId }: TransformationsMatrixProps) {
    const [data, setData] = useState<TransformationsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTransformations = async () => {
            try {
                setLoading(true);
                setError(null);

                const res = await fetchWithAuth(`projects/${projectId}/transformations`);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch transformations: ${res.statusText}`);
                }

                const transformData = await res.json();
                setData(transformData);
            } catch (err: any) {
                console.error('Error fetching transformations:', err);
                setError(err.message || 'Failed to load transformations');
            } finally {
                setLoading(false);
            }
        };

        fetchTransformations();
    }, [projectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3">
                    <Loader className="animate-spin text-emerald-500" size={32} />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                        Loading transformations...
                    </span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3 text-center px-4">
                    <AlertTriangle className="text-red-500" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            Error Loading Transformations
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {error}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!data || data.total_transformations === 0) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3 text-center px-4 max-w-md">
                    <Info className="text-blue-400" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            {data?.total_assets && data.total_assets > 0 
                                ? 'Column Mappings Pending Configuration' 
                                : 'No Column Transformations Found'}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {data?.message || 'All columns are passthrough (no renames, type changes, or logic)'}
                        </div>
                        {data?.total_assets && data.total_assets > 0 && (
                            <div className="mt-3 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                                <p className="text-xs text-blue-700 dark:text-blue-300">
                                    💡 This feature will be enabled in a future update
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 bg-purple-500/10 rounded-2xl flex items-center justify-center">
                        <Zap size={24} className="text-purple-500" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-[var(--text-primary)]">Column Transformations</h2>
                        <p className="text-sm text-[var(--text-tertiary)]">
                            Field-level changes across {data.total_assets} {data.total_assets === 1 ? 'asset' : 'assets'} 
                            (excludes simple passthrough)
                        </p>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(data.transformation_types).map(([type, count]) => {
                        const style = TRANSFORMATION_STYLES[type] || TRANSFORMATION_STYLES['passthrough'];
                        return (
                            <div key={type} className={`${style.bgColor} rounded-xl p-4 border border-gray-200 dark:border-gray-700`}>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-2xl">{style.emoji}</span>
                                    <span className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400">
                                        {style.label}
                                    </span>
                                </div>
                                <p className={`text-3xl font-black ${style.color}`}>{count}</p>
                            </div>
                        );
                    })}
                </div>

                {/* Transformations Table */}
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Asset</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Source</th>
                                    <th className="px-4 py-3 text-center text-xs font-bold uppercase tracking-wider text-gray-500"></th>
                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Target</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Type</th>
                                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Description</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                {data.transformations.map((trans, idx) => {
                                    const style = TRANSFORMATION_STYLES[trans.transformation_type] || TRANSFORMATION_STYLES['passthrough'];
                                    return (
                                        <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-900/50">
                                            <td className="px-4 py-3 text-gray-900 dark:text-gray-100 font-medium text-xs">
                                                {trans.asset_name}
                                            </td>
                                            <td className="px-4 py-3">
                                                <div>
                                                    <div className="font-mono text-xs font-bold text-gray-900 dark:text-gray-100">
                                                        {trans.source_column}
                                                    </div>
                                                    {trans.source_datatype && (
                                                        <div className="text-xs text-gray-500">{trans.source_datatype}</div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                <ArrowRight size={14} className="text-gray-400 inline" />
                                            </td>
                                            <td className="px-4 py-3">
                                                <div>
                                                    <div className="font-mono text-xs font-bold text-gray-900 dark:text-gray-100">
                                                        {trans.target_column}
                                                    </div>
                                                    {trans.target_datatype && (
                                                        <div className="text-xs text-gray-500">{trans.target_datatype}</div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold ${style.bgColor} ${style.color}`}>
                                                    {style.emoji} {style.label}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-xs text-gray-600 dark:text-gray-400">
                                                {trans.description}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                    {data.transformations.length >= 100 && (
                        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 text-center text-xs text-gray-500">
                            Showing first 100 transformations. Total: {data.total_transformations}
                        </div>
                    )}
                </div>

                {/* Recommendations */}
                {data.recommendations && data.recommendations.length > 0 && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
                        <div className="flex items-center gap-2 mb-3">
                            <Info size={18} className="text-blue-600 dark:text-blue-400" />
                            <h3 className="font-bold text-blue-900 dark:text-blue-100">Recommendations</h3>
                        </div>
                        <ul className="space-y-2">
                            {data.recommendations.map((rec, idx) => (
                                <li key={idx} className="text-sm text-blue-800 dark:text-blue-200">
                                    {rec}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}
