"use client";
import React from 'react';
import { 
    Zap, 
    Database, 
    Clock,
    Cpu,
    BarChart3,
    CheckCircle
} from 'lucide-react';

interface PerformanceDashboardProps {
    projectId: string;
}

export default function PerformanceDashboard({ projectId }: PerformanceDashboardProps) {
    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-950">
            {/* Header */}
            <div className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-500" />
                    Performance Analytics
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Code execution profiling and optimization recommendations
                </p>
            </div>

            {/* Coming Soon Content */}
            <div className="flex-1 overflow-auto p-6">
                <div className="max-w-4xl mx-auto">
                    {/* Main Message */}
                    <div className="text-center py-12">
                        <div className="mx-auto w-20 h-20 bg-gradient-to-br from-yellow-100 to-orange-100 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-full flex items-center justify-center mb-6">
                            <Zap size={40} className="text-yellow-600 dark:text-yellow-400" />
                        </div>
                        <h4 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                            Performance Profiling Coming Soon
                        </h4>
                        <p className="text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-8">
                            Advanced runtime profiling, execution analysis, and performance optimization suggestions will be available in Sprint 15.
                        </p>
                    </div>

                    {/* Planned Features Grid */}
                    <div className="grid md:grid-cols-2 gap-6 mb-8">
                        {/* Feature 1: Query Profiling */}
                        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                                    <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                                </div>
                                <div className="flex-1">
                                    <h5 className="font-bold text-gray-900 dark:text-white mb-2">Query Profiling</h5>
                                    <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                                        <li>• Execution time analysis</li>
                                        <li>• Expensive operations detection</li>
                                        <li>• Index usage recommendations</li>
                                        <li>• Join strategy optimization</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Feature 2: Resource Utilization */}
                        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                                    <Cpu className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                                </div>
                                <div className="flex-1">
                                    <h5 className="font-bold text-gray-900 dark:text-white mb-2">Resource Utilization</h5>
                                    <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                                        <li>• Memory consumption tracking</li>
                                        <li>• CPU usage monitoring</li>
                                        <li>• Disk I/O analysis</li>
                                        <li>• Network bandwidth metrics</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Feature 3: Bottleneck Detection */}
                        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                                    <Clock className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                                </div>
                                <div className="flex-1">
                                    <h5 className="font-bold text-gray-900 dark:text-white mb-2">Bottleneck Detection</h5>
                                    <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                                        <li>• Slow query identification</li>
                                        <li>• Data skew analysis</li>
                                        <li>• Shuffle optimization</li>
                                        <li>• Partition tuning suggestions</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Feature 4: Optimization Recommendations */}
                        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                            <div className="flex items-start gap-4">
                                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                                    <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                                </div>
                                <div className="flex-1">
                                    <h5 className="font-bold text-gray-900 dark:text-white mb-2">AI-Powered Recommendations</h5>
                                    <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                                        <li>• Automatic code refactoring</li>
                                        <li>• Cache strategy optimization</li>
                                        <li>• Parallel processing tuning</li>
                                        <li>• Cost reduction opportunities</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Sample Metrics Preview */}
                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/10 dark:to-purple-900/10 rounded-xl p-8 border border-blue-200 dark:border-blue-800">
                        <div className="flex items-start gap-4 mb-6">
                            <BarChart3 className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                            <div>
                                <h5 className="font-bold text-gray-900 dark:text-white text-lg mb-2">What You'll Get</h5>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Real-time performance insights powered by execution telemetry</p>
                            </div>
                        </div>
                        
                        <div className="grid md:grid-cols-3 gap-4">
                            <div className="bg-white/50 dark:bg-gray-900/50 rounded-lg p-4">
                                <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">2.4x</div>
                                <div className="text-xs text-gray-600 dark:text-gray-400 uppercase tracking-wide">Avg Speedup</div>
                            </div>
                            <div className="bg-white/50 dark:bg-gray-900/50 rounded-lg p-4">
                                <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-1">67%</div>
                                <div className="text-xs text-gray-600 dark:text-gray-400 uppercase tracking-wide">Cost Reduction</div>
                            </div>
                            <div className="bg-white/50 dark:bg-gray-900/50 rounded-lg p-4">
                                <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">89%</div>
                                <div className="text-xs text-gray-600 dark:text-gray-400 uppercase tracking-wide">Query Efficiency</div>
                            </div>
                        </div>
                    </div>

                    {/* Roadmap Timeline */}
                    <div className="mt-8 text-center">
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">📅 <strong>Sprint 15 Roadmap:</strong></p>
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 dark:bg-blue-900/20 rounded-full text-sm font-medium text-blue-700 dark:text-blue-300">
                            <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
                            Performance profiling infrastructure development in progress
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
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
