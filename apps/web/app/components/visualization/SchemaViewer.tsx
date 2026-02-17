"use client";
import React, { useState, useEffect } from 'react';
import { Database, Key, Link2, Clock, GitBranch, ChevronDown, ChevronRight, AlertCircle, Info } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface Column {
    name: string;
    data_type: string;
    nullable: boolean;
    is_primary_key: boolean;
    is_foreign_key: boolean;
    default_value?: string;
}

interface ForeignKey {
    column: string;
    ref_table: string;
    ref_column: string;
}

interface SchemaVersion {
    version_number: number;
    timestamp: string;
    changes_detected: number;
    is_breaking: boolean;
}

interface SchemaViewerProps {
    projectId: string;
    objectId?: string;
    showHistory?: boolean;
}

export default function SchemaViewer({ 
    projectId, 
    objectId,
    showHistory = true 
}: SchemaViewerProps) {
    const [schema, setSchema] = useState<any>(null);
    const [versions, setVersions] = useState<SchemaVersion[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'columns' | 'relationships' | 'history'>('columns');
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['columns']));

    useEffect(() => {
        const fetchSchema = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch schema metadata from backend (Sprint 9)
                const endpoint = objectId
                    ? `projects/${projectId}/objects/${objectId}/schema`
                    : `projects/${projectId}/schema`;

                const res = await fetchWithAuth(endpoint);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch schema: ${res.statusText}`);
                }

                const data = await res.json();
                setSchema(data);

                // Fetch schema versions if available (Sprint 10)
                if (showHistory && objectId) {
                    try {
                        const versionRes = await fetchWithAuth(
                            `projects/${projectId}/objects/${objectId}/schema/versions`
                        );
                        if (versionRes.ok) {
                            const versionData = await versionRes.json();
                            setVersions(versionData.versions || []);
                        }
                    } catch (err) {
                        console.warn('Schema versions not available:', err);
                    }
                }
            } catch (err: any) {
                console.error('Error fetching schema:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchSchema();
    }, [projectId, objectId, showHistory]);

    const toggleSection = (section: string) => {
        const newExpanded = new Set(expandedSections);
        if (newExpanded.has(section)) {
            newExpanded.delete(section);
        } else {
            newExpanded.add(section);
        }
        setExpandedSections(newExpanded);
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Loading schema...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="text-center">
                    <Database className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <p className="text-red-500 text-sm mb-2">Error loading schema</p>
                    <p className="text-gray-500 text-xs">{error}</p>
                </div>
            </div>
        );
    }

    if (!schema || !schema.columns || schema.columns.length === 0) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <div className="text-center">
                    <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 text-sm">No schema metadata available</p>
                    <p className="text-gray-400 text-xs mt-2">Run migration to extract schema</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-950">
            {/* Header */}
            <div className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                            <Database className="w-5 h-5 text-blue-500" />
                            {schema.table_name || 'Schema Metadata'}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            {schema.columns.length} columns • 
                            {schema.row_count ? ` ${schema.row_count.toLocaleString()} rows` : ' Unknown rows'} • 
                            {schema.primary_key && ` PK: ${schema.primary_key}`}
                        </p>
                    </div>

                    {/* Version badge */}
                    {schema.version_number && (
                        <div className="px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-lg text-xs font-medium">
                            v{schema.version_number}
                        </div>
                    )}
                </div>

                {/* Tabs */}
                <div className="flex gap-4 mt-4 border-b border-gray-200 dark:border-gray-800">
                    <button
                        onClick={() => setActiveTab('columns')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === 'columns'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Columns
                    </button>
                    <button
                        onClick={() => setActiveTab('relationships')}
                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === 'relationships'
                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                        }`}
                    >
                        Relationships
                    </button>
                    {showHistory && versions.length > 0 && (
                        <button
                            onClick={() => setActiveTab('history')}
                            className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === 'history'
                                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                            }`}
                        >
                            History ({versions.length})
                        </button>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto custom-scrollbar p-6">
                {/* Columns Tab */}
                {activeTab === 'columns' && (
                    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
                        <table className="w-full">
                            <thead className="bg-gray-50 dark:bg-gray-800">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Column Name
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Type
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Nullable
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                        Keys
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                                {schema.columns.map((column: Column, index: number) => (
                                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                        <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
                                            {column.name}
                                            {column.is_primary_key && (
                                                <Key className="w-3.5 h-3.5 text-yellow-500" title="Primary Key" />
                                            )}
                                            {column.is_foreign_key && (
                                                <Link2 className="w-3.5 h-3.5 text-blue-500" title="Foreign Key" />
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 font-mono">
                                            {column.data_type}
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                column.nullable
                                                    ? 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                                                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                            }`}>
                                                {column.nullable ? 'NULL' : 'NOT NULL'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                                            {column.is_primary_key && <span className="text-yellow-600 dark:text-yellow-500">PK</span>}
                                            {column.is_primary_key && column.is_foreign_key && ' • '}
                                            {column.is_foreign_key && <span className="text-blue-600 dark:text-blue-500">FK</span>}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Relationships Tab */}
                {activeTab === 'relationships' && (
                    <div className="space-y-4">
                        {/* Primary Key */}
                        {schema.primary_key && (
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                                    <Key className="w-4 h-4 text-yellow-500" />
                                    Primary Key
                                </h4>
                                <div className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                                    {schema.primary_key}
                                </div>
                            </div>
                        )}

                        {/* Foreign Keys */}
                        {schema.foreign_keys && schema.foreign_keys.length > 0 ? (
                            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
                                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                                    <Link2 className="w-4 h-4 text-blue-500" />
                                    Foreign Keys ({schema.foreign_keys.length})
                                </h4>
                                <div className="space-y-2">
                                    {schema.foreign_keys.map((fk: ForeignKey, index: number) => (
                                        <div key={index} className="flex items-center gap-3 text-sm">
                                            <span className="font-mono text-gray-900 dark:text-white">{fk.column}</span>
                                            <span className="text-gray-400">→</span>
                                            <span className="font-mono text-blue-600 dark:text-blue-400">
                                                {fk.ref_table}.{fk.ref_column}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center">
                                <Link2 className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                                <p className="text-sm text-gray-500 dark:text-gray-400">No foreign keys defined</p>
                            </div>
                        )}
                    </div>
                )}

                {/* History Tab */}
                {activeTab === 'history' && (
                    <div className="space-y-3">
                        {versions.map((version, index) => (
                            <div 
                                key={index}
                                className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4"
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-3">
                                        <GitBranch className="w-4 h-4 text-gray-400" />
                                        <span className="font-semibold text-gray-900 dark:text-white">
                                            Version {version.version_number}
                                        </span>
                                        {version.is_breaking && (
                                            <span className="px-2 py-0.5 bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 rounded text-xs font-medium">
                                                Breaking
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                                        <Clock className="w-3.5 h-3.5" />
                                        {new Date(version.timestamp).toLocaleString()}
                                    </div>
                                </div>
                                {version.changes_detected > 0 && (
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        {version.changes_detected} changes detected
                                    </p>
                                )}
                            </div>
                        ))}

                        {versions.length === 0 && (
                            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center">
                                <Clock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                                <p className="text-sm text-gray-500 dark:text-gray-400">No version history available</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
