"use client";

import React, { useState, useEffect } from 'react';
import { FileCode, CheckCircle, AlertCircle, XCircle, RefreshCw } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface CodeGenerationSummaryProps {
    projectId: string;
    activeTenantId?: string;
}

interface GenerationSummary {
    total_files: number;
    files_by_type: {
        python?: number;
        sql?: number;
        config?: number;
        yaml?: number;
        json?: number;
    };
    files_by_category: {
        dimensions?: number;
        facts?: number;
        staging?: number;
        transformations?: number;
        utilities?: number;
    };
    structure: {
        folders: string[];
        config_files: Array<{
            name: string;
            size: string;
            description?: string;
        }>;
    };
    objects_processed: Array<{
        name: string;
        type: string;
        file: string;
        status: 'success' | 'warning' | 'error';
    }>;
    cartridge_used: string;
    generation_timestamp: string;
}

const CodeGenerationSummary: React.FC<CodeGenerationSummaryProps> = ({ 
    projectId, 
    activeTenantId 
}) => {
    const [summary, setSummary] = useState<GenerationSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadSummary();
    }, [projectId]);

    const loadSummary = async () => {
        if (!projectId) return;

        setIsLoading(true);
        setError(null);

        try {
            const res = await fetchWithAuth(`projects/${projectId}/generation/summary`);
            
            if (!res.ok) {
                if (res.status === 404) {
                    setSummary(null);
                    setIsLoading(false);
                    return;
                }
                throw new Error(`Failed to load generation summary: ${res.status}`);
            }

            const data = await res.json();
            setSummary(data);
        } catch (err) {
            console.error('[CodeGenerationSummary] Load failed:', err);
            setError(err instanceof Error ? err.message : 'Failed to load generation summary');
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-48 bg-gray-900">
                <RefreshCw className="w-5 h-5 animate-spin text-gray-400" />
            </div>
        );
    }

    if (!summary) {
        return (
            <div className="flex items-center justify-center h-48 bg-gray-900">
                <p className="text-xs text-gray-500">No code generated</p>
            </div>
        );
    }

    const successCount = summary.objects_processed.filter(obj => obj.status === 'success').length;
    const warningCount = summary.objects_processed.filter(obj => obj.status === 'warning').length;
    const errorCount = summary.objects_processed.filter(obj => obj.status === 'error').length;

    return (
        <div className="h-full bg-gray-900 text-white p-4 overflow-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <FileCode className="text-blue-400" size={20} />
                    <h3 className="text-sm font-semibold">Code Summary</h3>
                </div>
                <button
                    onClick={loadSummary}
                    className="p-1.5 hover:bg-gray-800 rounded transition-colors"
                    title="Refresh"
                >
                    <RefreshCw size={14} className="text-gray-400" />
                </button>
            </div>

            {/* Files by Type (Compact) */}
            <div className="mb-4">
                <div className="text-xs text-gray-400 mb-2">Files by Type</div>
                <div className="grid grid-cols-3 gap-2">
                    {Object.entries(summary.files_by_type).map(([type, count]) => (
                        <div key={type} className="bg-gray-800 rounded p-2 border border-gray-700">
                            <div className="text-lg font-bold text-white">{count}</div>
                            <div className="text-xs text-gray-400 capitalize">{type}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Objects Status Summary */}
            <div className="mb-4">
                <div className="text-xs text-gray-400 mb-2">Objects Status</div>
                <div className="grid grid-cols-3 gap-2">
                    <div className="bg-green-900/20 rounded p-2 border border-green-800">
                        <div className="flex items-center gap-1 mb-1">
                            <CheckCircle size={12} className="text-green-500" />
                            <span className="text-xs text-green-400">Success</span>
                        </div>
                        <div className="text-lg font-bold text-green-400">{successCount}</div>
                    </div>
                    <div className="bg-yellow-900/20 rounded p-2 border border-yellow-800">
                        <div className="flex items-center gap-1 mb-1">
                            <AlertCircle size={12} className="text-yellow-500" />
                            <span className="text-xs text-yellow-400">Warning</span>
                        </div>
                        <div className="text-lg font-bold text-yellow-400">{warningCount}</div>
                    </div>
                    <div className="bg-red-900/20 rounded p-2 border border-red-800">
                        <div className="flex items-center gap-1 mb-1">
                            <XCircle size={12} className="text-red-500" />
                            <span className="text-xs text-red-400">Error</span>
                        </div>
                        <div className="text-lg font-bold text-red-400">{errorCount}</div>
                    </div>
                </div>
            </div>

            {/* Cartridge Info */}
            {summary.cartridge_used && (
                <div className="bg-blue-900/20 rounded p-2 border border-blue-800 mb-4">
                    <div className="text-xs text-blue-400 mb-1">Cartridge</div>
                    <div className="text-xs font-mono text-blue-300">{summary.cartridge_used}</div>
                </div>
            )}

            {/* Objects List (Compact) */}
            <div className="text-xs text-gray-400 mb-2">Generated Objects ({summary.objects_processed.length})</div>
            <div className="space-y-1 max-h-64 overflow-y-auto">
                {summary.objects_processed.map((obj, idx) => (
                    <div key={idx} className="flex items-center gap-2 bg-gray-800 rounded p-2 text-xs border border-gray-700">
                        <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                            obj.status === 'success' ? 'bg-green-500' :
                            obj.status === 'warning' ? 'bg-yellow-500' :
                            'bg-red-500'
                        }`}></div>
                        <div className="flex-1 truncate text-white">{obj.name}</div>
                        <span className="text-gray-500 uppercase text-xs">{obj.type}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CodeGenerationSummary;
