"use client";
import React, { useState, useEffect } from 'react';
import { FileCode, Database, Search, Copy, Check, Loader, AlertCircle } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface QueryItem {
    component_type: string;
    component_name: string;
    query: string;
    language: string;
}

interface PackageData {
    package_id: string;
    package_name: string;
    queries: QueryItem[];
    query_count: number;
}

interface SourceQueriesData {
    total_packages: number;
    total_queries: number;
    packages: PackageData[];
    timestamp: string | null;
    message?: string;
}

interface SourceQueriesViewerProps {
    projectId: string;
}

// Component type badge styles
const COMPONENT_TYPE_STYLES: Record<string, { bgColor: string; textColor: string; label: string }> = {
    'SOURCE_DB': { bgColor: 'bg-blue-100 dark:bg-blue-900/30', textColor: 'text-blue-700 dark:text-blue-300', label: 'SOURCE' },
    'LOOKUP': { bgColor: 'bg-purple-100 dark:bg-purple-900/30', textColor: 'text-purple-700 dark:text-purple-300', label: 'LOOKUP' },
};

export default function SourceQueriesViewer({ projectId }: SourceQueriesViewerProps) {
    const [data, setData] = useState<SourceQueriesData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

    useEffect(() => {
        const fetchQueries = async () => {
            try {
                setLoading(true);
                setError(null);

                const res = await fetchWithAuth(`projects/${projectId}/source-queries`);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch source queries: ${res.statusText}`);
                }

                const queriesData = await res.json();
                setData(queriesData);
            } catch (err: any) {
                console.error('Error fetching source queries:', err);
                setError(err.message || 'Failed to load source queries');
            } finally {
                setLoading(false);
            }
        };

        fetchQueries();
    }, [projectId]);

    const handleCopyQuery = async (query: string, index: string) => {
        try {
            await navigator.clipboard.writeText(query);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        } catch (err) {
            console.error('Failed to copy query:', err);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3">
                    <Loader className="animate-spin text-emerald-500" size={32} />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                        Loading source queries...
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
                            Error Loading Queries
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {error}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!data || data.total_queries === 0) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center gap-3 text-center px-4">
                    <FileCode className="text-gray-400" size={32} />
                    <div>
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                            No Source Queries Found
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {data?.message || 'Run Discovery and Triage to extract SQL queries'}
                        </div>
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
                    <div className="w-12 h-12 bg-emerald-500/10 rounded-2xl flex items-center justify-center">
                        <FileCode size={24} className="text-emerald-500" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-[var(--text-primary)]">Source Queries</h2>
                        <p className="text-sm text-[var(--text-tertiary)]">
                            SQL extracted from {data.total_packages} {data.total_packages === 1 ? 'package' : 'packages'} across the project
                        </p>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center gap-3 mb-2">
                            <Database size={20} className="text-emerald-500" />
                            <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Total Queries</span>
                        </div>
                        <p className="text-4xl font-black text-emerald-600">{data.total_queries}</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center gap-3 mb-2">
                            <FileCode size={20} className="text-blue-500" />
                            <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Packages</span>
                        </div>
                        <p className="text-4xl font-black text-blue-600">{data.total_packages}</p>
                    </div>
                </div>

                {/* Packages with Queries */}
                <div className="space-y-6">
                    {data.packages.map((pkg, pkgIdx) => (
                        <div key={pkgIdx} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
                            {/* Package Header */}
                            <div className="px-6 py-4 bg-gradient-to-r from-emerald-500/10 to-blue-500/10 border-b border-gray-200 dark:border-gray-700">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                                            <FileCode size={18} className="text-emerald-500" />
                                            {pkg.package_name}
                                        </h3>
                                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                            {pkg.query_count} {pkg.query_count === 1 ? 'query' : 'queries'} extracted
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Queries in Package */}
                            <div className="p-6 space-y-4">
                                {pkg.queries.map((query, queryIdx) => {
                                    const typeStyle = COMPONENT_TYPE_STYLES[query.component_type] || COMPONENT_TYPE_STYLES['SOURCE_DB'];
                                    const idx = `${pkgIdx}-${queryIdx}`;
                                    const isCopied = copiedIndex === idx;

                                    return (
                                        <div key={queryIdx} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                                            {/* Query Header */}
                                            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-semibold ${typeStyle.bgColor} ${typeStyle.textColor}`}>
                                                        {typeStyle.label}
                                                    </span>
                                                    <span className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                                                        {query.component_name}
                                                    </span>
                                                </div>
                                                <button
                                                    onClick={() => handleCopyQuery(query.query, idx)}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors"
                                                >
                                                    {isCopied ? (
                                                        <>
                                                            <Check size={14} />
                                                            Copied
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Copy size={14} />
                                                            Copy
                                                        </>
                                                    )}
                                                </button>
                                            </div>

                                            {/* Query Code */}
                                            <div className="relative">
                                                <SyntaxHighlighter
                                                    language={query.language || 'sql'}
                                                    style={vscDarkPlus}
                                                    customStyle={{
                                                        margin: 0,
                                                        padding: '1rem',
                                                        fontSize: '0.8125rem',
                                                        lineHeight: '1.5',
                                                        background: 'transparent'
                                                    }}
                                                    showLineNumbers={true}
                                                >
                                                    {query.query}
                                                </SyntaxHighlighter>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Timestamp Footer */}
                {data.timestamp && (
                    <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
                        Last extracted: {new Date(data.timestamp).toLocaleString()}
                    </div>
                )}
            </div>
        </div>
    );
}
