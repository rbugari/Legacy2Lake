"use client";
import React, { useState, useEffect } from 'react';
import { Database, Server, HardDrive, Link2, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface Connection {
    name: string;
    id: string;
    type: string;
    server: string;
    database: string;
}

interface OriginAnalysisData {
    source_type: string | null;
    server: string | null;
    database: string | null;
    package_name: string | null;
    connections: Connection[];
    statistics: {
        source_tables: number;
        total_rows: number | null;
        columns_detected: number | null;
    };
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

    if (!data || !data.source_type) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3 text-center px-4">
                    <Database className="text-gray-400" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            No Origin Analysis Available
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {data?.message || 'Run Discovery and Triage to analyze the source system'}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <Database size={24} className="text-emerald-500" />
                    Origin Analysis
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Detected source system information from SSIS package analysis
                </p>
            </div>

            {/* Main Origin Info */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6 shadow-sm">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Source System */}
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
                            Source System
                        </div>
                        <div className="flex items-center gap-2">
                            <Database size={20} className="text-blue-500" />
                            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                {data.source_type}
                            </span>
                        </div>
                    </div>

                    {/* Server */}
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
                            Server
                        </div>
                        <div className="flex items-center gap-2">
                            <Server size={20} className="text-purple-500" />
                            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                {data.server || 'N/A'}
                            </span>
                        </div>
                    </div>

                    {/* Database */}
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
                            Database
                        </div>
                        <div className="flex items-center gap-2">
                            <HardDrive size={20} className="text-orange-500" />
                            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                {data.database || 'N/A'}
                            </span>
                        </div>
                    </div>

                    {/* Package */}
                    <div>
                        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">
                            Package
                        </div>
                        <div className="flex items-center gap-2">
                            <CheckCircle size={20} className="text-emerald-500" />
                            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                {data.package_name || 'N/A'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Statistics */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6 shadow-sm">
                <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                    <Database size={16} />
                    Statistics
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 border border-emerald-200 dark:border-emerald-800">
                        <div className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold mb-1">
                            Source Tables
                        </div>
                        <div className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">
                            {data.statistics.source_tables || 0}
                        </div>
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                        <div className="text-xs text-blue-600 dark:text-blue-400 font-semibold mb-1">
                            Total Rows
                        </div>
                        <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                            {data.statistics.total_rows?.toLocaleString() || 'N/A'}
                        </div>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                        <div className="text-xs text-purple-600 dark:text-purple-400 font-semibold mb-1">
                            Columns Detected
                        </div>
                        <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                            {data.statistics.columns_detected || 'N/A'}
                        </div>
                    </div>
                </div>
            </div>

            {/* Connections */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
                <h3 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                    <Link2 size={16} />
                    Connections ({data.connections.length})
                </h3>
                
                {data.connections.length === 0 ? (
                    <div className="text-sm text-gray-500 dark:text-gray-400 italic">
                        No connections detected
                    </div>
                ) : (
                    <div className="space-y-3">
                        {data.connections.map((conn, idx) => (
                            <div
                                key={idx}
                                className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                                            {conn.name}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                                            <div>
                                                <span className="font-semibold">Type:</span> {conn.type}
                                            </div>
                                            <div>
                                                <span className="font-semibold">Server:</span> {conn.server}
                                            </div>
                                            <div>
                                                <span className="font-semibold">Database:</span> {conn.database}
                                            </div>
                                            <div className="text-xs text-gray-400 dark:text-gray-500 font-mono truncate">
                                                ID: {conn.id}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="ml-4">
                                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                                            {conn.type}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Timestamp Footer */}
            {data.timestamp && (
                <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
                    Last analyzed: {new Date(data.timestamp).toLocaleString()}
                </div>
            )}
        </div>
    );
}
