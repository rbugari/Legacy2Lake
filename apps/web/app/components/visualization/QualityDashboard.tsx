"use client";
import React, { useState, useEffect } from 'react';
import { 
    Activity, 
    AlertTriangle, 
    CheckCircle, 
    TrendingUp, 
    TrendingDown,
    Info,
    AlertCircle,
    XCircle,
    Target,
    BarChart3,
    AlertOctagon
} from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface QualityMetrics {
    overall_score: number;
    completeness: number;
    accuracy: number;
    consistency: number;
    conformity: number;
    uniqueness: number;
    timeliness: number;
}

interface Violation {
    rule_id: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    object_name?: string;
    column_name?: string;
    count?: number;
}

interface Anomaly {
    type: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    description: string;
    detected_at: string;
    affected_objects: string[];
}

interface QualityDashboardProps {
    projectId: string;
    objectId?: string;
}

export default function QualityDashboard({ projectId, objectId }: QualityDashboardProps) {
    const [metrics, setMetrics] = useState<QualityMetrics | null>(null);
    const [violations, setViolations] = useState<Violation[]>([]);
    const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeSection, setActiveSection] = useState<'overview' | 'violations' | 'anomalies'>('overview');

    useEffect(() => {
        const fetchQualityData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch quality metrics (Sprint 11)
                const endpoint = objectId
                    ? `projects/${projectId}/objects/${objectId}/quality`
                    : `projects/${projectId}/quality`;

                const res = await fetchWithAuth(endpoint);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch quality data: ${res.statusText}`);
                }

                const data = await res.json();
                
                if (data.metrics) {
                    setMetrics(data.metrics);
                }
                if (data.violations) {
                    setViolations(data.violations);
                }
                if (data.anomalies) {
                    setAnomalies(data.anomalies);
                }
            } catch (err: any) {
                console.error('Error fetching quality data:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchQualityData();
    }, [projectId, objectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Loading quality metrics...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="text-center">
                    <Activity className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <p className="text-red-500 text-sm mb-2">Error loading quality data</p>
                    <p className="text-gray-500 text-xs">{error}</p>
                </div>
            </div>
        );
    }

    if (!metrics) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="text-center">
                    <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 text-sm">No quality metrics available</p>
                    <p className="text-gray-400 text-xs mt-2">Run audit to generate quality report</p>
                </div>
            </div>
        );
    }

    const getScoreColor = (score: number) => {
        if (score >= 90) return 'text-green-500';
        if (score >= 75) return 'text-blue-500';
        if (score >= 60) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getScoreBgColor = (score: number) => {
        if (score >= 90) return 'bg-green-500';
        if (score >= 75) return 'bg-blue-500';
        if (score >= 60) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case 'critical':
                return <AlertOctagon className="w-4 h-4 text-red-500" />;
            case 'high':
                return <XCircle className="w-4 h-4 text-orange-500" />;
            case 'medium':
                return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
            case 'low':
                return <Info className="w-4 h-4 text-blue-500" />;
            default:
                return <AlertCircle className="w-4 h-4 text-gray-500" />;
        }
    };

    const getSeverityBadgeColor = (severity: string) => {
        switch (severity) {
            case 'critical':
                return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
            case 'high':
                return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
            case 'medium':
                return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
            case 'low':
                return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
            default:
                return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-950">
            {/* Header */}
            <div className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <Activity className="w-5 h-5 text-blue-500" />
                            Quality Dashboard
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Data quality metrics, violations, and anomaly detection
                        </p>
                    </div>

                    {/* Overall Score Badge */}
                    <div className="text-center">
                        <div className={`text-3xl font-bold ${getScoreColor(metrics.overall_score)}`}>
                            {metrics.overall_score.toFixed(1)}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Overall Score
                        </div>
                    </div>
                </div>

                {/* Section Tabs */}
                <div className="flex gap-4 mt-4 border-b border-gray-200 dark:border-gray-800">
                    <button
                        onClick={() => setActiveSection('overview')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeSection === 'overview'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveSection('violations')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeSection === 'violations'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Violations ({violations.length})
                    </button>
                    <button
                        onClick={() => setActiveSection('anomalies')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeSection === 'anomalies'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Anomalies ({anomalies.length})
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto custom-scrollbar p-6">
                {/* Overview Section */}
                {activeSection === 'overview' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-7xl mx-auto">
                        {/* Completeness */}
                        <MetricCard
                            title="Completeness"
                            score={metrics.completeness}
                            description="Percentage of non-null values"
                            icon={<CheckCircle className="w-5 h-5" />}
                        />

                        {/* Accuracy */}
                        <MetricCard
                            title="Accuracy"
                            score={metrics.accuracy}
                            description="Data type and format correctness"
                            icon={<Target className="w-5 h-5" />}
                        />

                        {/* Consistency */}
                        <MetricCard
                            title="Consistency"
                            score={metrics.consistency}
                            description="Cross-table referential integrity"
                            icon={<BarChart3 className="w-5 h-5" />}
                        />

                        {/* Conformity */}
                        <MetricCard
                            title="Conformity"
                            score={metrics.conformity}
                            description="Adherence to naming conventions"
                            icon={<CheckCircle className="w-5 h-5" />}
                        />

                        {/* Uniqueness */}
                        <MetricCard
                            title="Uniqueness"
                            score={metrics.uniqueness}
                            description="Duplicate detection rate"
                            icon={<Target className="w-5 h-5" />}
                        />

                        {/* Timeliness */}
                        <MetricCard
                            title="Timeliness"
                            score={metrics.timeliness}
                            description="Data freshness and currency"
                            icon={<Activity className="w-5 h-5" />}
                        />
                    </div>
                )}

                {/* Violations Section */}
                {activeSection === 'violations' && (
                    <div className="max-w-7xl mx-auto space-y-3">
                        {violations.length === 0 ? (
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-12 text-center">
                                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                    No Violations Detected
                                </p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    All quality rules passed successfully
                                </p>
                            </div>
                        ) : (
                            violations.map((violation, index) => (
                                <div 
                                    key={index}
                                    className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition-shadow"
                                >
                                    <div className="flex items-start gap-3">
                                        <div className="mt-1">
                                            {getSeverityIcon(violation.severity)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${getSeverityBadgeColor(violation.severity)}`}>
                                                    {violation.severity}
                                                </span>
                                                <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                                                    {violation.rule_id}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-900 dark:text-white mb-1">
                                                {violation.message}
                                            </p>
                                            {(violation.object_name || violation.column_name) && (
                                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                                    {violation.object_name && <span>Object: {violation.object_name}</span>}
                                                    {violation.object_name && violation.column_name && <span> • </span>}
                                                    {violation.column_name && <span>Column: {violation.column_name}</span>}
                                                    {violation.count && <span> • Count: {violation.count}</span>}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}

                {/* Anomalies Section */}
                {activeSection === 'anomalies' && (
                    <div className="max-w-7xl mx-auto space-y-3">
                        {anomalies.length === 0 ? (
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-12 text-center">
                                <Activity className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                    No Anomalies Detected
                                </p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    Data patterns are within expected ranges
                                </p>
                            </div>
                        ) : (
                            anomalies.map((anomaly, index) => (
                                <div 
                                    key={index}
                                    className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition-shadow"
                                >
                                    <div className="flex items-start gap-3">
                                        <div className="mt-1">
                                            {getSeverityIcon(anomaly.severity)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${getSeverityBadgeColor(anomaly.severity)}`}>
                                                    {anomaly.severity}
                                                </span>
                                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                                    {anomaly.type}
                                                </span>
                                                <span className="text-xs text-gray-400">
                                                    {new Date(anomaly.detected_at).toLocaleString()}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-900 dark:text-white mb-2">
                                                {anomaly.description}
                                            </p>
                                            {anomaly.affected_objects.length > 0 && (
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="text-xs text-gray-500 dark:text-gray-400">Affected:</span>
                                                    {anomaly.affected_objects.map((obj, i) => (
                                                        <span 
                                                            key={i}
                                                            className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded text-xs font-mono"
                                                        >
                                                            {obj}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// Metric Card Component
function MetricCard({ title, score, description, icon }: { title: string; score: number; description: string; icon: React.ReactNode }) {
    const getScoreColor = (score: number) => {
        if (score >= 90) return 'text-green-500';
        if (score >= 75) return 'text-blue-500';
        if (score >= 60) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getScoreBgGradient = (score: number) => {
        if (score >= 90) return 'from-green-500 to-emerald-500';
        if (score >= 75) return 'from-blue-500 to-cyan-500';
        if (score >= 60) return 'from-yellow-500 to-orange-500';
        return 'from-red-500 to-pink-500';
    };

    return (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-5 hover:shadow-lg transition-all">
            <div className="flex items-start justify-between mb-4">
                <div className={`p-2 rounded-lg bg-gradient-to-br ${getScoreBgGradient(score)} bg-opacity-10`}>
                    {icon}
                </div>
                <div className={`text-2xl font-bold ${getScoreColor(score)}`}>
                    {score.toFixed(1)}%
                </div>
            </div>
            <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                {title}
            </h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">
                {description}
            </p>
            
            {/* Progress Bar */}
            <div className="mt-3 h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                <div 
                    className={`h-full bg-gradient-to-r ${getScoreBgGradient(score)} transition-all duration-500`}
                    style={{ width: `${score}%` }}
                />
            </div>
        </div>
    );
}
