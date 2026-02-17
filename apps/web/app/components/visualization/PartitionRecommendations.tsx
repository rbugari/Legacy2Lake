"use client";
import { useEffect, useState } from 'react';
import { Database, TrendingUp, Calendar, Hash, Clock, Zap, AlertCircle, CheckCircle2, Info } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface PartitionRecommendation {
    asset_id: string;
    asset_name: string;
    column_name: string;
    data_type: string;
    cardinality_ratio: number;
    partition_score: number;
    partition_reason: string;
}

export default function PartitionRecommendations({ projectId }: { projectId: string }) {
    const [data, setData] = useState<PartitionRecommendation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [sortBy, setSortBy] = useState<'score' | 'name'>('score');

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);
                const res = await fetchWithAuth(`projects/${projectId}/partition-recommendations`);
                
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                
                const result = await res.json();
                setData(result.recommendations || []);
            } catch (e) {
                console.error('Partition Recommendations error:', e);
                setError(e instanceof Error ? e.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [projectId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-sm text-gray-500">Analyzing partition candidates...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl p-8 text-center">
                <AlertCircle size={48} className="mx-auto text-red-500 mb-4" />
                <h3 className="text-lg font-bold text-red-700 dark:text-red-400 mb-2">Analysis Failed</h3>
                <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-8 text-center">
                <Database size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-bold mb-2">No Partition Recommendations</h3>
                <p className="text-sm text-gray-500">Run column analysis to generate partition suggestions.</p>
            </div>
        );
    }

    const sortedData = [...data].sort((a, b) => {
        if (sortBy === 'score') return b.partition_score - a.partition_score;
        return a.asset_name.localeCompare(b.asset_name);
    });

    const getScoreColor = (score: number) => {
        if (score >= 80) return { 
            bg: 'bg-green-50 dark:bg-green-900/10', 
            border: 'border-green-200 dark:border-green-800',
            text: 'text-green-600 dark:text-green-400',
            badge: 'bg-green-500'
        };
        if (score >= 60) return { 
            bg: 'bg-amber-50 dark:bg-amber-900/10', 
            border: 'border-amber-200 dark:border-amber-800',
            text: 'text-amber-600 dark:text-amber-400',
            badge: 'bg-amber-500'
        };
        return { 
            bg: 'bg-gray-50 dark:bg-gray-900/50', 
            border: 'border-gray-200 dark:border-gray-800',
            text: 'text-gray-600 dark:text-gray-400',
            badge: 'bg-gray-400'
        };
    };

    const getDataTypeIcon = (type: string) => {
        const lowerType = type.toLowerCase();
        if (lowerType.includes('date') || lowerType.includes('time')) return <Calendar size={16} className="text-blue-500" />;
        if (lowerType.includes('int') || lowerType.includes('num')) return <Hash size={16} className="text-purple-500" />;
        return <Database size={16} className="text-gray-400" />;
    };

    const highValue = sortedData.filter(r => r.partition_score >= 80).length;
    const mediumValue = sortedData.filter(r => r.partition_score >= 60 && r.partition_score < 80).length;
    const lowValue = sortedData.filter(r => r.partition_score < 60).length;

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-emerald-500/10 rounded-2xl flex items-center justify-center">
                        <TrendingUp size={24} className="text-emerald-500" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-[var(--text-primary)]">Partition Recommendations</h2>
                        <p className="text-sm text-[var(--text-tertiary)]">Query optimization and cost reduction strategies</p>
                    </div>
                </div>

                {/* Sort Controls */}
                <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Sort by:</span>
                    <button
                        onClick={() => setSortBy('score')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                            sortBy === 'score'
                                ? 'bg-emerald-500 text-white shadow-sm'
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                        }`}
                    >
                        Score
                    </button>
                    <button
                        onClick={() => setSortBy('name')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                            sortBy === 'name'
                                ? 'bg-emerald-500 text-white shadow-sm'
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                        }`}
                    >
                        Asset Name
                    </button>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                        <Database size={20} className="text-gray-500" />
                        <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Total Candidates</span>
                    </div>
                    <p className="text-4xl font-black text-[var(--text-primary)]">{data.length}</p>
                </div>
                
                <div className="bg-green-50 dark:bg-green-900/10 rounded-xl p-6 border border-green-200 dark:border-green-800 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                        <CheckCircle2 size={20} className="text-green-500" />
                        <span className="text-xs font-bold uppercase tracking-wider text-green-600 dark:text-green-400">High Priority</span>
                    </div>
                    <p className="text-4xl font-black text-green-600 dark:text-green-400">{highValue}</p>
                    <p className="text-xs text-gray-500 mt-1">Score ≥ 80</p>
                </div>

                <div className="bg-amber-50 dark:bg-amber-900/10 rounded-xl p-6 border border-amber-200 dark:border-amber-800 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                        <Clock size={20} className="text-amber-500" />
                        <span className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">Medium Priority</span>
                    </div>
                    <p className="text-4xl font-black text-amber-600 dark:text-amber-400">{mediumValue}</p>
                    <p className="text-xs text-gray-500 mt-1">Score 60-79</p>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                        <Info size={20} className="text-gray-500" />
                        <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Low Priority</span>
                    </div>
                    <p className="text-4xl font-black text-gray-600 dark:text-gray-400">{lowValue}</p>
                    <p className="text-xs text-gray-500 mt-1">Score &lt; 60</p>
                </div>
            </div>

            {/* Recommendations Table */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-800">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Asset</th>
                                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Column</th>
                                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Type</th>
                                <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider text-gray-500">Score</th>
                                <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-500">Reason</th>
                                <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider text-gray-500">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                            {sortedData.map((rec, index) => {
                                const colors = getScoreColor(rec.partition_score);
                                return (
                                    <tr 
                                        key={`${rec.asset_id}-${rec.column_name}-${index}`}
                                        className="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors"
                                    >
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <Database size={16} className="text-gray-400 shrink-0" />
                                                <span className="font-mono text-sm font-medium text-[var(--text-primary)] truncate max-w-xs">
                                                    {rec.asset_name}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="font-mono text-sm font-bold text-cyan-600 dark:text-cyan-400">
                                                {rec.column_name}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                {getDataTypeIcon(rec.data_type)}
                                                <span className="text-xs font-bold uppercase text-gray-600 dark:text-gray-400">
                                                    {rec.data_type}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center justify-center">
                                                <div className={`relative w-16 h-16 flex items-center justify-center`}>
                                                    <svg className="w-full h-full transform -rotate-90">
                                                        <circle
                                                            cx="32"
                                                            cy="32"
                                                            r="28"
                                                            stroke="currentColor"
                                                            strokeWidth="4"
                                                            fill="none"
                                                            className="text-gray-200 dark:text-gray-700"
                                                        />
                                                        <circle
                                                            cx="32"
                                                            cy="32"
                                                            r="28"
                                                            stroke="currentColor"
                                                            strokeWidth="4"
                                                            fill="none"
                                                            strokeDasharray={`${(rec.partition_score / 100) * 176} 176`}
                                                            className={colors.text}
                                                        />
                                                    </svg>
                                                    <span className={`absolute text-sm font-black ${colors.text}`}>
                                                        {rec.partition_score}
                                                    </span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <p className="text-sm text-gray-600 dark:text-gray-400 max-w-sm">
                                                {rec.partition_reason}
                                            </p>
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                className={`px-4 py-2 ${colors.bg} border ${colors.border} rounded-lg text-xs font-bold ${colors.text} hover:opacity-80 transition-all`}
                                                title="Apply partition (coming soon)"
                                            >
                                                <Zap size={14} className="inline mr-1" />
                                                Apply
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Cost Savings Estimate */}
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/10 dark:to-teal-900/10 rounded-xl p-6 border border-emerald-200 dark:border-emerald-800">
                <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                    <TrendingUp className="text-emerald-600" size={20} />
                    Estimated Impact
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider font-bold mb-1">Query Performance</p>
                        <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                            {highValue > 0 ? '2-5x' : 'Up to 2x'} faster
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider font-bold mb-1">Cost Reduction</p>
                        <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                            {highValue > 0 ? '30-50%' : '10-20%'}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider font-bold mb-1">Implementation Effort</p>
                        <p className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                            {data.length} columns
                        </p>
                    </div>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-4 italic">
                    * Estimates based on typical Databricks/Snowflake workloads with date-based partitioning
                </p>
            </div>
        </div>
    );
}
