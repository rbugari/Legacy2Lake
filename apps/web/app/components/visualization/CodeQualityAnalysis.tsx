"use client";
import React, { useState, useEffect } from 'react';
import { AlertTriangle, Shield, Info, XCircle, AlertCircle, Loader } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface SchemaIssue {
    severity: 'high' | 'medium' | 'low';
    category: 'missing_primary_key' | 'no_foreign_keys' | 'high_null_column' | 'orphaned_column';
    asset_name: string;
    column_name?: string;
    description: string;
    impact: string;
}

interface CodeQualityData {
    total_assets: number;
    total_issues: number;
    issues: SchemaIssue[];
    summary: {
        missing_primary_keys: number;
        no_foreign_keys: number;
        high_null_columns: number;
        orphaned_columns: number;
    };
    message?: string;
}

interface CodeQualityAnalysisProps {
    projectId: string;
}

// Severity styles
const SEVERITY_STYLES = {
    'high': { 
        icon: XCircle, 
        color: 'text-red-700 dark:text-red-300', 
        bgColor: 'bg-red-100 dark:bg-red-900/30',
        borderColor: 'border-red-200 dark:border-red-800',
        label: 'High'
    },
    'medium': { 
        icon: AlertTriangle, 
        color: 'text-orange-700 dark:text-orange-300', 
        bgColor: 'bg-orange-100 dark:bg-orange-900/30',
        borderColor: 'border-orange-200 dark:border-orange-800',
        label: 'Medium'
    },
    'low': { 
        icon: Info, 
        color: 'text-blue-700 dark:text-blue-300', 
        bgColor: 'bg-blue-100 dark:bg-blue-900/30',
        borderColor: 'border-blue-200 dark:border-blue-800',
        label: 'Low'
    }
};

// Category styles (keys must match backend summary keys)
const CATEGORY_STYLES = {
    'missing_primary_keys': { emoji: '🔑', label: 'Missing PK' },
    'no_foreign_keys': { emoji: '🔗', label: 'No FKs' },
    'high_null_columns': { emoji: '⚠️', label: 'High Nulls' },
    'orphaned_columns': { emoji: '🗑️', label: 'Orphaned' }
};

export default function CodeQualityAnalysis({ projectId }: CodeQualityAnalysisProps) {
    const [data, setData] = useState<CodeQualityData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filterSeverity, setFilterSeverity] = useState<string>('all');

    useEffect(() => {
        const fetchQuality = async () => {
            try {
                setLoading(true);
                setError(null);

                const res = await fetchWithAuth(`projects/${projectId}/quality`);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch quality data: ${res.statusText}`);
                }

                const qualityData = await res.json();
                setData(qualityData);
            } catch (err: any) {
                console.error('Error fetching quality data:', err);
                setError(err.message || 'Failed to load quality analysis');
            } finally {
                setLoading(false);
            }
        };

        fetchQuality();
    }, [projectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3">
                    <Loader className="animate-spin text-amber-500" size={32} />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                        Analyzing schema quality...
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
                            Error Loading Quality Analysis
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {error}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!data || data.total_issues === 0) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3 text-center px-4">
                    <Shield className="text-emerald-500" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            No Schema Issues Found
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {data?.message || 'All legacy assets meet schema quality standards'}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const filteredIssues = filterSeverity === 'all' 
        ? data.issues 
        : data.issues.filter(i => i.severity === filterSeverity);

    return (
        <div className="h-full overflow-y-auto bg-gray-50 dark:bg-gray-900 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 bg-amber-500/10 rounded-2xl flex items-center justify-center">
                        <Shield size={24} className="text-amber-500" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-[var(--text-primary)]">Legacy Schema Issues</h2>
                        <p className="text-sm text-[var(--text-tertiary)]">
                            Detected problems in {data.total_assets} source {data.total_assets === 1 ? 'asset' : 'assets'}
                        </p>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(data.summary).map(([key, count]) => {
                        const categoryKey = key as keyof typeof CATEGORY_STYLES;
                        const style = CATEGORY_STYLES[categoryKey];
                        
                        // Skip if style not found (defensive programming)
                        if (!style) {
                            console.warn(`Missing style definition for category: ${key}`);
                            return null;
                        }
                        
                        return (
                            <div key={key} className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-2xl">{style.emoji}</span>
                                    <span className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400">
                                        {style.label}
                                    </span>
                                </div>
                                <p className="text-3xl font-black text-gray-900 dark:text-gray-100">{count}</p>
                            </div>
                        );
                    })}
                </div>

                {/* Severity Filter */}
                <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                    <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Filter:</span>
                    <div className="flex gap-2">
                        {['all', 'high', 'medium', 'low'].map(severity => (
                            <button
                                key={severity}
                                onClick={() => setFilterSeverity(severity)}
                                className={`px-3 py-1 rounded text-xs font-bold transition-colors ${
                                    filterSeverity === severity
                                        ? 'bg-amber-500 text-white'
                                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                }`}
                            >
                                {severity.charAt(0).toUpperCase() + severity.slice(1)}
                            </button>
                        ))}
                    </div>
                    <span className="ml-auto text-xs text-gray-500">
                        Showing {filteredIssues.length} of {data.total_issues} issues
                    </span>
                </div>

                {/* Issues List */}
                <div className="space-y-3">
                    {filteredIssues.map((issue, idx) => {
                        const severityStyle = SEVERITY_STYLES[issue.severity];
                        const categoryStyle = CATEGORY_STYLES[issue.category];
                        const Icon = severityStyle.icon;
                        
                        // Defensive check: Skip if categoryStyle is undefined
                        if (!categoryStyle) {
                            console.warn(`Missing CATEGORY_STYLES definition for category: ${issue.category}`);
                            return null;
                        }

                        return (
                            <div
                                key={idx}
                                className={`bg-white dark:bg-gray-800 rounded-xl border ${severityStyle.borderColor} overflow-hidden shadow-sm`}
                            >
                                <div className={`px-6 py-4 ${severityStyle.bgColor} border-b ${severityStyle.borderColor}`}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <Icon size={20} className={severityStyle.color} />
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-gray-900 dark:text-gray-100">
                                                        {issue.asset_name}
                                                    </span>
                                                    {issue.column_name && (
                                                        <>
                                                            <span className="text-gray-400">→</span>
                                                            <span className="font-mono text-sm text-gray-700 dark:text-gray-300">
                                                                {issue.column_name}
                                                            </span>
                                                        </>
                                                    )}
                                                </div>
                                                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                                                    {issue.description}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold ${severityStyle.bgColor} ${severityStyle.color}`}>
                                                {categoryStyle.emoji} {categoryStyle.label}
                                            </span>
                                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold ${severityStyle.bgColor} ${severityStyle.color}`}>
                                                {severityStyle.label}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900/50">
                                    <div className="flex items-start gap-2">
                                        <Info size={14} className="text-gray-500 mt-0.5 flex-shrink-0" />
                                        <span className="text-xs text-gray-600 dark:text-gray-400">
                                            <strong>Impact:</strong> {issue.impact}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {filteredIssues.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                        No issues match the selected severity filter
                    </div>
                )}
            </div>
        </div>
    );
}
