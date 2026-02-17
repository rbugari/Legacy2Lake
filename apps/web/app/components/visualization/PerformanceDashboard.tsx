"use client";
import React, { useState, useEffect } from 'react';
import { 
    Zap, 
    Database, 
    TrendingUp, 
    Clock,
    Cpu,
    HardDrive,
    Activity,
    BarChart3,
    GitBranch,
    CheckCircle,
    XCircle
} from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface CacheStats {
    hit_rate: number;
    total_requests: number;
    cache_hits: number;
    cache_misses: number;
    avg_response_time_ms: number;
    avg_cached_response_time_ms: number;
}

interface OptimizationStats {
    total_optimizations_applied: number;
    query_rewrites: number;
    index_suggestions: number;
    partition_optimizations: number;
    estimated_speedup: number;
    cost_reduction_percent: number;
}

interface ParallelStats {
    concurrent_tasks: number;
    parallel_efficiency: number;
    avg_task_duration_ms: number;
    total_tasks_executed: number;
    failed_tasks: number;
}

interface PerformanceDashboardProps {
    projectId: string;
}

export default function PerformanceDashboard({ projectId }: PerformanceDashboardProps) {
    const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
    const [optimizationStats, setOptimizationStats] = useState<OptimizationStats | null>(null);
    const [parallelStats, setParallelStats] = useState<ParallelStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeSection, setActiveSection] = useState<'cache' | 'optimization' | 'parallel'>('cache');

    useEffect(() => {
        const fetchPerformanceData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch performance metrics (Sprint 12)
                const res = await fetchWithAuth(`projects/${projectId}/performance`);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch performance data: ${res.statusText}`);
                }

                const data = await res.json();
                
                if (data.cache) {
                    setCacheStats(data.cache);
                }
                if (data.optimization) {
                    setOptimizationStats(data.optimization);
                }
                if (data.parallel) {
                    setParallelStats(data.parallel);
                }
            } catch (err: any) {
                console.error('Error fetching performance data:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchPerformanceData();
    }, [projectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Loading performance metrics...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="text-center">
                    <Zap className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <p className="text-red-500 text-sm mb-2">Error loading performance data</p>
                    <p className="text-gray-500 text-xs">{error}</p>
                </div>
            </div>
        );
    }

    if (!cacheStats && !optimizationStats && !parallelStats) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="text-center">
                    <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 text-sm">No performance metrics available</p>
                    <p className="text-gray-400 text-xs mt-2">Run migration to collect performance data</p>
                </div>
            </div>
        );
    }

    const getHitRateColor = (rate: number) => {
        if (rate >= 80) return 'text-green-500';
        if (rate >= 60) return 'text-blue-500';
        if (rate >= 40) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getEfficiencyColor = (efficiency: number) => {
        if (efficiency >= 90) return 'text-green-500';
        if (efficiency >= 75) return 'text-blue-500';
        if (efficiency >= 60) return 'text-yellow-500';
        return 'text-orange-500';
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-950">
            {/* Header */}
            <div className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <Zap className="w-5 h-5 text-yellow-500" />
                            Performance Dashboard
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Cache efficiency, query optimization, and parallel processing metrics
                        </p>
                    </div>

                    {/* Quick Stats */}
                    {cacheStats && (
                        <div className="text-center">
                            <div className={`text-3xl font-bold ${getHitRateColor(cacheStats.hit_rate)}`}>
                                {cacheStats.hit_rate.toFixed(1)}%
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                Cache Hit Rate
                            </div>
                        </div>
                    )}
                </div>

                {/* Section Tabs */}
                <div className="flex gap-4 mt-4 border-b border-gray-200 dark:border-gray-800">
                    <button
                        onClick={() => setActiveSection('cache')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeSection === 'cache'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Cache Performance
                    </button>
                    <button
                        onClick={() => setActiveSection('optimization')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeSection === 'optimization'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Query Optimization
                    </button>
                    <button
                        onClick={() => setActiveSection('parallel')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeSection === 'parallel'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Parallel Processing
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto custom-scrollbar p-6">
                {/* Cache Performance Section */}
                {activeSection === 'cache' && cacheStats && (
                    <div className="max-w-7xl mx-auto space-y-6">
                        {/* Hit Rate Visualization */}
                        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                            <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                <Database className="w-5 h-5 text-blue-500" />
                                Cache Hit Rate
                            </h4>
                            
                            {/* Circular Progress */}
                            <div className="flex items-center justify-center mb-6">
                                <div className="relative w-48 h-48">
                                    <svg className="transform -rotate-90 w-48 h-48">
                                        <circle
                                            cx="96"
                                            cy="96"
                                            r="88"
                                            stroke="currentColor"
                                            strokeWidth="12"
                                            fill="transparent"
                                            className="text-gray-200 dark:text-gray-800"
                                        />
                                        <circle
                                            cx="96"
                                            cy="96"
                                            r="88"
                                            stroke="currentColor"
                                            strokeWidth="12"
                                            fill="transparent"
                                            strokeDasharray={`${2 * Math.PI * 88}`}
                                            strokeDashoffset={`${2 * Math.PI * 88 * (1 - cacheStats.hit_rate / 100)}`}
                                            className={getHitRateColor(cacheStats.hit_rate)}
                                            strokeLinecap="round"
                                        />
                                    </svg>
                                    <div className="absolute inset-0 flex items-center justify-center flex-col">
                                        <div className={`text-4xl font-bold ${getHitRateColor(cacheStats.hit_rate)}`}>
                                            {cacheStats.hit_rate.toFixed(1)}%
                                        </div>
                                        <div className="text-sm text-gray-500 dark:text-gray-400">Hit Rate</div>
                                    </div>
                                </div>
                            </div>

                            {/* Stats Grid */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <StatCard
                                    label="Total Requests"
                                    value={cacheStats.total_requests.toLocaleString()}
                                    icon={<Activity className="w-4 h-4" />}
                                />
                                <StatCard
                                    label="Cache Hits"
                                    value={cacheStats.cache_hits.toLocaleString()}
                                    icon={<CheckCircle className="w-4 h-4 text-green-500" />}
                                    valueColor="text-green-500"
                                />
                                <StatCard
                                    label="Cache Misses"
                                    value={cacheStats.cache_misses.toLocaleString()}
                                    icon={<XCircle className="w-4 h-4 text-red-500" />}
                                    valueColor="text-red-500"
                                />
                                <StatCard
                                    label="Avg Response Time"
                                    value={`${cacheStats.avg_response_time_ms.toFixed(0)}ms`}
                                    icon={<Clock className="w-4 h-4" />}
                                />
                            </div>

                            {/* Response Time Comparison */}
                            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-900/30">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Cached Response Time</p>
                                        <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                            {cacheStats.avg_cached_response_time_ms.toFixed(0)}ms
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Speedup</p>
                                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                                            {(cacheStats.avg_response_time_ms / cacheStats.avg_cached_response_time_ms).toFixed(2)}x
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Optimization Section */}
                {activeSection === 'optimization' && optimizationStats && (
                    <div className="max-w-7xl mx-auto space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Optimizations Applied */}
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-green-500" />
                                    Optimizations Applied
                                </h4>
                                <div className="space-y-4">
                                    <OptimizationMetric
                                        label="Query Rewrites"
                                        value={optimizationStats.query_rewrites}
                                        total={optimizationStats.total_optimizations_applied}
                                    />
                                    <OptimizationMetric
                                        label="Index Suggestions"
                                        value={optimizationStats.index_suggestions}
                                        total={optimizationStats.total_optimizations_applied}
                                    />
                                    <OptimizationMetric
                                        label="Partition Optimizations"
                                        value={optimizationStats.partition_optimizations}
                                        total={optimizationStats.total_optimizations_applied}
                                    />
                                </div>
                            </div>

                            {/* Performance Impact */}
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                    <BarChart3 className="w-5 h-5 text-purple-500" />
                                    Performance Impact
                                </h4>
                                <div className="space-y-6">
                                    <div className="text-center p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg">
                                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Estimated Speedup</p>
                                        <p className="text-5xl font-bold text-green-600 dark:text-green-400">
                                            {optimizationStats.estimated_speedup.toFixed(1)}x
                                        </p>
                                    </div>
                                    <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-lg">
                                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Cost Reduction</p>
                                        <p className="text-5xl font-bold text-blue-600 dark:text-blue-400">
                                            {optimizationStats.cost_reduction_percent.toFixed(0)}%
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Parallel Processing Section */}
                {activeSection === 'parallel' && parallelStats && (
                    <div className="max-w-7xl mx-auto space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* Concurrency */}
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                        <GitBranch className="w-5 h-5 text-purple-500" />
                                        Concurrency
                                    </h4>
                                </div>
                                <div className="text-center">
                                    <p className="text-5xl font-bold text-purple-600 dark:text-purple-400 mb-2">
                                        {parallelStats.concurrent_tasks}
                                    </p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Concurrent Tasks</p>
                                </div>
                            </div>

                            {/* Efficiency */}
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                        <Cpu className="w-5 h-5 text-blue-500" />
                                        Efficiency
                                    </h4>
                                </div>
                                <div className="text-center">
                                    <p className={`text-5xl font-bold mb-2 ${getEfficiencyColor(parallelStats.parallel_efficiency)}`}>
                                        {parallelStats.parallel_efficiency.toFixed(1)}%
                                    </p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Parallel Efficiency</p>
                                </div>
                            </div>

                            {/* Task Duration */}
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                        <Clock className="w-5 h-5 text-orange-500" />
                                        Duration
                                    </h4>
                                </div>
                                <div className="text-center">
                                    <p className="text-5xl font-bold text-orange-600 dark:text-orange-400 mb-2">
                                        {parallelStats.avg_task_duration_ms.toFixed(0)}
                                    </p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Avg Task Duration (ms)</p>
                                </div>
                            </div>
                        </div>

                        {/* Task Execution Summary */}
                        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                            <h4 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                                <Activity className="w-5 h-5 text-blue-500" />
                                Task Execution Summary
                            </h4>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="text-center p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                    <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                        {parallelStats.total_tasks_executed}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Total Tasks</p>
                                </div>
                                <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                    <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                                        {parallelStats.total_tasks_executed - parallelStats.failed_tasks}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Successful</p>
                                </div>
                                <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                                    <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                                        {parallelStats.failed_tasks}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Failed</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// Utility Components
function StatCard({ label, value, icon, valueColor = 'text-gray-900 dark:text-white' }: any) {
    return (
        <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-2">
                {icon}
                <p className="text-xs font-medium uppercase tracking-wider">{label}</p>
            </div>
            <p className={`text-2xl font-bold ${valueColor}`}>{value}</p>
        </div>
    );
}

function OptimizationMetric({ label, value, total }: { label: string; value: number; total: number }) {
    const percentage = total > 0 ? (value / total) * 100 : 0;
    
    return (
        <div>
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">{value}</span>
            </div>
            <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}
