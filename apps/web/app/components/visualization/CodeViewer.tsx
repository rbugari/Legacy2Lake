"use client";
import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Download, Check, Code, FileCode, Maximize2, Minimize2 } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface CodeViewerProps {
    projectId: string;
    objectId?: string;
    language?: string;
    showHeader?: boolean;
}

export default function CodeViewer({ 
    projectId, 
    objectId, 
    language = 'python',
    showHeader = true 
}: CodeViewerProps) {
    const [code, setCode] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [metadata, setMetadata] = useState<any>(null);

    useEffect(() => {
        const fetchCode = async () => {
            try {
                setLoading(true);
                setError(null);

                // Fetch generated code from backend
                const endpoint = objectId 
                    ? `projects/${projectId}/objects/${objectId}/code`
                    : `projects/${projectId}/generated-code`;

                const res = await fetchWithAuth(endpoint);
                
                if (!res.ok) {
                    throw new Error(`Failed to fetch code: ${res.statusText}`);
                }

                const data = await res.json();

                if (data.code) {
                    setCode(data.code);
                    setMetadata(data.metadata || null);
                } else if (data.generated_code) {
                    setCode(data.generated_code);
                } else {
                    setCode('// No code available yet\n// Run migration to generate code');
                }
            } catch (err: any) {
                console.error('Error fetching code:', err);
                setError(err.message);
                setCode('// Error loading code\n// Please try again');
            } finally {
                setLoading(false);
            }
        };

        fetchCode();
    }, [projectId, objectId]);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(code);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const handleDownload = () => {
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${objectId || projectId}_generated_code.${language === 'python' ? 'py' : 'sql'}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const detectLanguage = (code: string): string => {
        if (code.includes('spark.read') || code.includes('from pyspark')) {
            return 'python';
        } else if (code.includes('SELECT') || code.includes('CREATE TABLE')) {
            return 'sql';
        }
        return language;
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-900">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-gray-400 text-sm">Loading generated code...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-900">
                <div className="text-center">
                    <Code className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <p className="text-red-400 text-sm mb-2">Error loading code</p>
                    <p className="text-gray-500 text-xs">{error}</p>
                </div>
            </div>
        );
    }

    const detectedLang = detectLanguage(code);

    return (
        <div className={`flex flex-col h-full bg-gray-900 ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
            {/* Header */}
            {showHeader && (
                <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
                    <div className="flex items-center gap-3">
                        <FileCode className="w-5 h-5 text-blue-400" />
                        <div>
                            <h3 className="text-sm font-semibold text-white">
                                Generated Code
                            </h3>
                            {metadata && (
                                <p className="text-xs text-gray-400">
                                    {metadata.tech_id || detectedLang.toUpperCase()} • 
                                    {metadata.layer && ` ${metadata.layer} layer`} • 
                                    Generated: {new Date(metadata.timestamp || Date.now()).toLocaleString()}
                                </p>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleCopy}
                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs font-medium flex items-center gap-2 transition-colors"
                        >
                            {copied ? (
                                <>
                                    <Check className="w-3.5 h-3.5 text-green-400" />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <Copy className="w-3.5 h-3.5" />
                                    Copy
                                </>
                            )}
                        </button>

                        <button
                            onClick={handleDownload}
                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs font-medium flex items-center gap-2 transition-colors"
                        >
                            <Download className="w-3.5 h-3.5" />
                            Download
                        </button>

                        <button
                            onClick={() => setIsFullscreen(!isFullscreen)}
                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs font-medium flex items-center gap-2 transition-colors"
                        >
                            {isFullscreen ? (
                                <Minimize2 className="w-3.5 h-3.5" />
                            ) : (
                                <Maximize2 className="w-3.5 h-3.5" />
                            )}
                        </button>
                    </div>
                </div>
            )}

            {/* Code Display */}
            <div className="flex-1 overflow-auto custom-scrollbar">
                <SyntaxHighlighter
                    language={detectedLang}
                    style={vscDarkPlus}
                    showLineNumbers
                    wrapLines
                    customStyle={{
                        margin: 0,
                        padding: '1rem',
                        background: '#1e1e1e',
                        fontSize: '0.875rem',
                        lineHeight: '1.5',
                        minHeight: '100%'
                    }}
                    codeTagProps={{
                        style: {
                            fontFamily: 'var(--font-mono), Consolas, Monaco, "Courier New", monospace'
                        }
                    }}
                >
                    {code}
                </SyntaxHighlighter>
            </div>

            {/* Footer stats */}
            {metadata && (
                <div className="px-4 py-2 bg-gray-800 border-t border-gray-700 flex items-center justify-between text-xs text-gray-400">
                    <div className="flex items-center gap-4">
                        <span>Lines: {code.split('\n').length}</span>
                        <span>Size: {(code.length / 1024).toFixed(2)} KB</span>
                        {metadata.validation && (
                            <span className={metadata.validation.is_valid ? 'text-green-400' : 'text-red-400'}>
                                Validation: {metadata.validation.is_valid ? '✓ Passed' : '✗ Failed'}
                            </span>
                        )}
                    </div>
                    {metadata.optimization && (
                        <div className="flex items-center gap-2">
                            <span>Optimizations: {metadata.optimization.optimizations_applied?.length || 0}</span>
                            {metadata.optimization.estimated_speedup && (
                                <span className="text-blue-400">
                                    {metadata.optimization.estimated_speedup}x speedup
                                </span>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
