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

interface SourceQueriesData {
    package_name: string | null;
    queries: QueryItem[];
    total_queries: number;
    main_query: string | null;
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
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

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

    const handleCopyQuery = async (query: string, index: number) => {
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
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <FileCode size={24} className="text-emerald-500" />
                    Source Queries Extracted
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    SQL queries extracted from {data.package_name || 'SSIS package'} components
                </p>
            </div>

            {/* Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6 shadow-sm">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Database size={20} className="text-emerald-500" />
                        <span className="font-semibold text-gray-900 dark:text-gray-100">
                            Total Queries: {data.total_queries}
                        </span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                        Package: {data.package_name}
                    </div>
                </div>
            </div>

            {/* Queries List */}
            <div className="space-y-6">
                {data.queries.map((query, idx) => {
                    const typeStyle = COMPONENT_TYPE_STYLES[query.component_type] || COMPONENT_TYPE_STYLES['SOURCE_DB'];
                    const isCopied = copiedIndex === idx;

                    return (
                        <div
                            key={idx}
                            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm"
                        >
                            {/* Query Header */}
                            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-semibold ${typeStyle.bgColor} ${typeStyle.textColor}`}>
                                        {typeStyle.label}
                                    </span>
                                    <span className="font-semibold text-gray-900 dark:text-gray-100">
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
                                        padding: '1.5rem',
                                        fontSize: '0.875rem',
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

            {/* Main Query Highlight (if available) */}
            {data.main_query && data.main_query !== data.queries[0]?.query && (
                <div className="mt-6 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800 p-6">
                    <h3 className="text-sm font-bold text-emerald-900 dark:text-emerald-100 mb-3 flex items-center gap-2">
                        <Search size={16} />
                        Primary Source Query
                    </h3>
                    <div className="bg-white dark:bg-gray-800 rounded-lg overflow-hidden">
                        <SyntaxHighlighter
                            language="sql"
                            style={vscDarkPlus}
                            customStyle={{
                                margin: 0,
                                padding: '1rem',
                                fontSize: '0.8125rem',
                                background: 'transparent'
                            }}
                        >
                            {data.main_query}
                        </SyntaxHighlighter>
                    </div>
                </div>
            )}

            {/* Timestamp Footer */}
            {data.timestamp && (
                <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
                    Last extracted: {new Date(data.timestamp).toLocaleString()}
                </div>
            )}
        </div>
    );
}
