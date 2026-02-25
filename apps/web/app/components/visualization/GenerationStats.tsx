"use client";

import { useState, useEffect } from "react";
import { CheckCircle, AlertTriangle, XCircle, Code2, RefreshCw } from "lucide-react";
import { fetchWithAuth } from "../../lib/auth-client";

interface GenerationStatsData {
    total_objects: number;
    processed: number;
    successful: number;
    failed: number;
    warnings: number;
    avg_generation_time: string;
    cartridge_used: string;
    tokens_consumed: number;
    extraction_summary?: {
        tables_extracted: number;
        columns_mapped: number;
        transformations_detected: number;
    };
}

interface GenerationStatsProps {
    projectId: string;
    activeTenantId?: string;
}

export default function GenerationStats({ projectId, activeTenantId }: GenerationStatsProps) {
    const [stats, setStats] = useState<GenerationStatsData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadStats();
    }, [projectId]);

    const loadStats = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const res = await fetchWithAuth(`projects/${projectId}/generation/stats`, {
                headers: activeTenantId ? { "X-Tenant-ID": activeTenantId } : {}
            });

            if (!res.ok) {
                // Gracefully handle 404 - endpoint doesn't exist yet
                if (res.status === 404) {
                    setStats(null);
                    setIsLoading(false);
                    return;
                }
                throw new Error(`Failed to load stats: ${res.status}`);
            }

            const data = await res.json();
            setStats(data.stats || data);
        } catch (e) {
            console.error("[GenerationStats] Error:", e);
            // Don't set error for connection issues, just show empty state
            setStats(null);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-48">
                <RefreshCw className="w-5 h-5 animate-spin text-gray-400" />
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="flex items-center justify-center h-48">
                <p className="text-xs text-gray-500">No data</p>
            </div>
        );
    }

    const successRate = stats.processed > 0 
        ? ((stats.successful / stats.processed) * 100).toFixed(0)
        : "0";

    return (
        <div className="h-full bg-gray-900 text-white p-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Code2 className="text-blue-400" size={20} />
                    <h3 className="text-sm font-semibold">Generation Stats</h3>
                </div>
                <button
                    onClick={loadStats}
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Refresh"
                >
                    <RefreshCw size={14} className="text-gray-400" />
                </button>
            </div>

            {/* Compact Stats Grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
                {/* Total/Processed */}
                <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                    <div className="text-xs text-gray-400 mb-1">Total ETL</div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-white">{stats.total_objects}</span>
                        <span className="text-xs text-gray-500">({stats.processed} processed)</span>
                    </div>
                </div>

                {/* Success Rate */}
                <div className="bg-green-900/20 rounded-lg p-3 border border-green-800">
                    <div className="text-xs text-green-400 mb-1">Success Rate</div>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-green-400">{successRate}%</span>
                        <CheckCircle size={16} className="text-green-500" />
                    </div>
                </div>

                {/* Successful */}
                <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400">Approved</span>
                        <CheckCircle size={14} className="text-green-500" />
                    </div>
                    <div className="text-xl font-bold text-green-400">{stats.successful}</div>
                </div>

                {/* Warnings */}
                <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-400">Warnings</span>
                        <AlertTriangle size={14} className="text-yellow-500" />
                    </div>
                    <div className="text-xl font-bold text-yellow-400">{stats.warnings}</div>
                </div>

                {/* Failed */}
                <div className="bg-red-900/20 rounded-lg p-3 border border-red-800 col-span-2">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-red-400">Rejected (Score &lt; 7)</span>
                        <XCircle size={14} className="text-red-500" />
                    </div>
                    <div className="text-xl font-bold text-red-400">{stats.failed}</div>
                </div>
            </div>

            {/* Cartridge Info */}
            {stats.cartridge_used && stats.cartridge_used !== 'N/A' && (
                <div className="bg-blue-900/20 rounded-lg p-3 border border-blue-800">
                    <div className="text-xs text-blue-400 mb-1">Cartridge</div>
                    <div className="text-sm font-mono text-blue-300">{stats.cartridge_used}</div>
                </div>
            )}
        </div>
    );
}
