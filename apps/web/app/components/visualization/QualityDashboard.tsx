"use client";
import React, { useState, useEffect } from 'react';
import { 
    Activity, 
    AlertTriangle, 
    CheckCircle, 
    Info,
    AlertCircle,
    AlertOctagon,
    Key,
    GitBranch,
    Layers,
    Database
} from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface SchemaIssue {
    severity: 'critical' | 'high' | 'medium' | 'low';
    category: string;
    asset_name: string;
    column_name?: string;
    description: string;
    impact: string;
}

interface QualitySummary {
    missing_primary_keys: number;
    no_foreign_keys: number;
    high_null_columns: number;
    orphaned_columns: number;
}

interface QualityData {
    total_assets: number;
    total_issues: number;
    issues: SchemaIssue[];
    summary: QualitySummary;
    message?: string;
}

interface QualityDashboardProps {
    projectId: string;
    objectId?: string;
}

export default function QualityDashboard({ projectId, objectId }: QualityDashboardProps) {
    const [qualityData, setQualityData] = useState<QualityData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeSection, setActiveSection] = useState<'overview' | 'issues'>('overview');

    useEffect(() => {
        const fetchQualityData = async () => {
            try {
                setLoading(true);
                setError(null);

                const endpoint = objectId
                    ? `projects/${projectId}/objects/${objectId}/quality`
                    : `projects/${projectId}/quality`;

                const res = await fetchWithAuth(endpoint);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch quality data: ${res.statusText}`);
                }

                const data = await res.json();
                setQualityData(data);
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
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Loading schema analysis...</p>
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

    if (!qualityData || qualityData.total_assets === 0) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="text-center max-w-md">
                    <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 text-sm font-medium">No Schema Analysis Available</p>
                    <p className="text-gray-400 text-xs mt-2">
                        {qualityData?.message || "Run Discovery and Triage to analyze database schemas"}
                    </p>
                </div>
            </div>
        );
    }

    const getSeverityIcon = (severity: string) => {
        switch (severity) {
            case 'critical':
                return <AlertOctagon className="w-4 h-4 text-red-500" />;
            case 'high':
                return <AlertTriangle className="w-4 h-4 text-orange-500" />;
            case 'medium':
                return <AlertCircle className="w-4 h-4 text-yellow-500" />;
            case 'low':
                return <Info className="w-4 h-4 text-blue-500" />;
            default:
                return <Info className="w-4 h-4 text-gray-500" />;
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return 'border-l-red-500 bg-red-50 dark:bg-red-900/10';
            case 'high': return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/10';
            case 'medium': return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/10';
            case 'low': return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10';
            default: return 'border-l-gray-500 bg-gray-50 dark:bg-gray-900/10';
        }
    };

    const getSeverityBadge = (severity: string) => {
        switch (severity) {
            case 'critical': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
            case 'high': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
            case 'medium': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
            case 'low': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
            default: return 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400';
        }
    };

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case 'missing_primary_key':
                return <Key className="w-5 h-5 text-red-500" />;
            case 'no_foreign_keys':
                return <GitBranch className="w-5 h-5 text-orange-500" />;
            case 'orphaned_column':
                return <Layers className="w-5 h-5 text-blue-500" />;
            default:
                return <Database className="w-5 h-5 text-gray-500" />;
        }
    };

    const criticalIssues = qualityData.issues.filter(i => i.severity === 'critical').length;
    const highIssues = qualityData.issues.filter(i => i.severity === 'high').length;
    const mediumIssues = qualityData.issues.filter(i => i.severity === 'medium').length;
    const lowIssues = qualityData.issues.filter(i => i.severity === 'low').length;

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-950">
            {/* Header */}
            <div className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <Database className="w-5 h-5 text-blue-500" />
                            Schema Quality Analysis
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Database structure issues detected during discovery and triage
                        </p>
                    </div>

                    {/* Quick Stats */}
                    <div className="text-right">
                        <div className="text-3xl font-bold text-gray-900 dark:text-white">
                            {qualityData.total_issues}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Total Issues
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                            {qualityData.total_assets} assets analyzed
                        </div>
                    </div>
                </div>

                {/* Section Tabs */}
                <div className="flex gap-4 border-b border-gray-200 dark:border-gray-800">
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
                        onClick={() => setActiveSection('issues')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeSection === 'issues'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        All Issues ({qualityData.total_issues})
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-6">
                {/* Overview Section */}
                {activeSection === 'overview' && (
                    <div className="max-w-7xl mx-auto space-y-6">
                        {/* Summary Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {/* Missing PKs */}
                            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 bg-red-100 dark:bg-red-900/20 rounded-lg">
                                        <Key className="w-6 h-6 text-red-600 dark:text-red-400" />
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                                            {qualityData.summary.missing_primary_keys}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">High</div>
                                    </div>
                                </div>
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                                    Missing Primary Keys
                                </h4>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    Tables without unique row identifiers
                                </p>
                            </div>

                            {/* No FKs */}
                            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
                                        <GitBranch className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                                            {qualityData.summary.no_foreign_keys}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">Medium</div>
                                    </div>
                                </div>
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                                    No Foreign Keys
                                </h4>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    Isolated tables without relationships
                                </p>
                            </div>

                            {/* Orphaned Columns */}
                            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                                        <Layers className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                                            {qualityData.summary.orphaned_columns}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">Low</div>
                                    </div>
                                </div>
                                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                                    Orphaned Columns
                                </h4>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    Columns not mapped to target
                                </p>
                            </div>

                            {/* Issue Breakdown */}
                            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                <div className="mb-4">
                                    <div className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                                        Issue Breakdown
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">By severity level</p>
                                </div>
                                <div className="space-y-2">
                                    {criticalIssues > 0 && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-red-600 dark:text-red-400 font-medium">Critical</span>
                                            <span className="font-bold">{criticalIssues}</span>
                                        </div>
                                    )}
                                    {highIssues > 0 && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-orange-600 dark:text-orange-400 font-medium">High</span>
                                            <span className="font-bold">{highIssues}</span>
                                        </div>
                                    )}
                                    {mediumIssues > 0 && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-yellow-600 dark:text-yellow-400 font-medium">Medium</span>
                                            <span className="font-bold">{mediumIssues}</span>
                                        </div>
                                    )}
                                    {lowIssues > 0 && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-blue-600 dark:text-blue-400 font-medium">Low</span>
                                            <span className="font-bold">{lowIssues}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Recent Issues Preview */}
                        {qualityData.issues.length > 0 && (
                            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800">
                                <h4 className="font-bold text-gray-900 dark:text-white mb-4">Top Issues (Most Critical)</h4>
                                <div className="space-y-3">
                                    {qualityData.issues.slice(0, 5).map((issue, index) => (
                                        <div 
                                            key={index} 
                                            className={`border-l-4 p-3 rounded-r-lg ${getSeverityColor(issue.severity)}`}
                                        >
                                            <div className="flex items-start gap-3">
                                                {getSeverityIcon(issue.severity)}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${getSeverityBadge(issue.severity)}`}>
                                                            {issue.severity}
                                                        </span>
                                                        <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                                                            {issue.asset_name}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-900 dark:text-white font-medium">
                                                        {issue.description}
                                                    </p>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                        Impact: {issue.impact}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                {qualityData.issues.length > 5 && (
                                    <button
                                        onClick={() => setActiveSection('issues')}
                                        className="mt-4 text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
                                    >
                                        View all {qualityData.issues.length} issues →
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* All Issues Section */}
                {activeSection === 'issues' && (
                    <div className="max-w-7xl mx-auto space-y-3">
                        {qualityData.issues.length === 0 ? (
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-12 text-center">
                                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                    No Schema Issues Detected
                                </p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    All database schemas meet quality standards
                                </p>
                            </div>
                        ) : (
                            qualityData.issues.map((issue, index) => (
                                <div 
                                    key={index}
                                    className={`bg-white dark:bg-gray-900 rounded-lg border-l-4 border-r border-t border-b border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition-shadow ${getSeverityColor(issue.severity)}`}
                                >
                                    <div className="flex items-start gap-4">
                                        <div className="mt-1">
                                            {getCategoryIcon(issue.category)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className={`px-2 py-1 rounded text-xs font-semibold uppercase ${getSeverityBadge(issue.severity)}`}>
                                                    {issue.severity}
                                                </span>
                                                <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                                                    {issue.category.replace(/_/g, ' ').toUpperCase()}
                                                </span>
                                            </div>
                                            <div className="mb-2">
                                                <span className="text-sm font-mono text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                                                    {issue.asset_name}
                                                </span>
                                                {issue.column_name && (
                                                    <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                                                        • Column: <span className="font-mono">{issue.column_name}</span>
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-900 dark:text-white mb-2 font-medium">
                                                {issue.description}
                                            </p>
                                            <div className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 p-2 rounded">
                                                <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                                                <span><strong>Impact:</strong> {issue.impact}</span>
                                            </div>
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
