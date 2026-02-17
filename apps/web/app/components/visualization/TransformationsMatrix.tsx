"use client";
import React, { useState, useEffect } from 'react';
import { Zap, TrendingUp, AlertTriangle, CheckCircle, Loader, Info } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface TransformationItem {
    type: string;
    count: number;
    details: string;
}

interface TransformationsData {
    package_name: string | null;
    complexity_score: number;
    transformations_matrix: TransformationItem[];
    total_transformations: number;
    recommendations: (string | null)[];
    timestamp: string | null;
    message?: string;
}

interface TransformationsMatrixProps {
    projectId: string;
}

// Map transformation types to colors and icons
const TRANSFORMATION_STYLES: Record<string, { color: string; bgColor: string; label: string; emoji: string }> = {
    'SOURCE_DB': { color: 'text-blue-700 dark:text-blue-300', bgColor: 'bg-blue-100 dark:bg-blue-900/30', label: 'Source', emoji: '📥' },
    'DESTINATION_DB': { color: 'text-green-700 dark:text-green-300', bgColor: 'bg-green-100 dark:bg-green-900/30', label: 'Destination', emoji: '📤' },
    'LOOKUP': { color: 'text-purple-700 dark:text-purple-300', bgColor: 'bg-purple-100 dark:bg-purple-900/30', label: 'Lookup', emoji: '🔍' },
    'DERIVED_COLUMN': { color: 'text-orange-700 dark:text-orange-300', bgColor: 'bg-orange-100 dark:bg-orange-900/30', label: 'Derived Col', emoji: '📝' },
    'MERGE': { color: 'text-pink-700 dark:text-pink-300', bgColor: 'bg-pink-100 dark:bg-pink-900/30', label: 'Merge', emoji: '🔀' },
    'AGGREGATE': { color: 'text-yellow-700 dark:text-yellow-300', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30', label: 'Aggregate', emoji: '⚙️' },
    'CONDITIONAL': { color: 'text-indigo-700 dark:text-indigo-300', bgColor: 'bg-indigo-100 dark:bg-indigo-900/30', label: 'Conditional', emoji: '🔄' },
    'DATA_CONVERSION': { color: 'text-teal-700 dark:text-teal-300', bgColor: 'bg-teal-100 dark:bg-teal-900/30', label: 'Convert', emoji: '📊' },
    'SORT': { color: 'text-cyan-700 dark:text-cyan-300', bgColor: 'bg-cyan-100 dark:bg-cyan-900/30', label: 'Sort', emoji: '⬆️' },
    'UNKNOWN': { color: 'text-gray-700 dark:text-gray-300', bgColor: 'bg-gray-100 dark:bg-gray-900/30', label: 'Other', emoji: '❓' },
};

// Complexity score color mapping
const getComplexityColor = (score: number) => {
    if (score >= 70) return { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', label: 'High' };
    if (score >= 40) return { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', label: 'Medium' };
    return { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', label: 'Low' };
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
                <div className="flex flex-col items-center gap-3 text-center px-4">
                    <Zap className="text-gray-400" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            No Transformations Detected
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {data?.message || 'Run Discovery and Triage to detect transformations'}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const complexityColor = getComplexityColor(data.complexity_score);

    return (
        <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <Zap size={24} className="text-emerald-500" />
                    Transformations Detected
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Analysis of transformations found in {data.package_name || 'SSIS package'}
                </p>
            </div>

            {/* Complexity Score */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6 shadow-sm">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
                            Complexity Score
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                                {data.complexity_score}
                            </span>
                            <span className="text-2xl text-gray-500">/100</span>
                        </div>
                    </div>
                    <div className={`px-4 py-2 rounded-lg ${complexityColor.bg}`}>
                        <div className={`text-sm font-bold ${complexityColor.text}`}>
                            {complexityColor.label} Complexity
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            {data.total_transformations} transformations
                        </div>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${
                            data.complexity_score >= 70
                                ? 'bg-red-500'
                                : data.complexity_score >= 40
                                ? 'bg-yellow-500'
                                : 'bg-green-500'
                        } transition-all duration-500`}
                        style={{ width: `${data.complexity_score}%` }}
                    />
                </div>
            </div>

            {/* Transformations Matrix */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm mb-6">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <TrendingUp size={16} />
                        Transformations Matrix
                    </h3>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-900">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                                    Type
                                </th>
                                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                                    Count
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                                    Details
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {data.transformations_matrix.map((trans, idx) => {
                                const style = TRANSFORMATION_STYLES[trans.type] || TRANSFORMATION_STYLES['UNKNOWN'];
                                return (
                                    <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center gap-2">
                                                <span className="text-lg">{style.emoji}</span>
                                                <span className={`font-semibold ${style.color}`}>
                                                    {style.label}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${style.bgColor} ${style.color} font-bold text-sm`}>
                                                {trans.count}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-sm text-gray-600 dark:text-gray-400">
                                                {trans.details || 'N/A'}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Recommendations */}
            {data.recommendations && data.recommendations.filter(Boolean).length > 0 && (
                <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800 p-6 shadow-sm">
                    <h3 className="text-sm font-bold text-amber-900 dark:text-amber-100 mb-3 flex items-center gap-2">
                        <Info size={16} />
                        Recommendations
                    </h3>
                    <ul className="space-y-2">
                        {data.recommendations.filter(Boolean).map((rec, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-amber-800 dark:text-amber-200">
                                <AlertTriangle size={14} className="mt-0.5 flex-shrink-0" />
                                <span>{rec}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Timestamp Footer */}
            {data.timestamp && (
                <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
                    Last analyzed: {new Date(data.timestamp).toLocaleString()}
                </div>
            )}
        </div>
    );
}
