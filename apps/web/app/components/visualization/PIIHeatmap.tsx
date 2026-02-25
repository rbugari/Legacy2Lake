"use client";
import { useEffect, useState } from 'react';
import { Shield, ShieldAlert, AlertTriangle, Database, Lock, Eye, CreditCard, Phone, Mail } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface PIIHeatmapData {
    total_columns: number;
    pii_columns: number;
    pii_percentage: number;
    pii_by_category: Record<string, number>;
    high_risk_assets: Array<{
        asset_id: string;
        asset_name: string;
        pii_columns: number;
        pii_types: string[];
        pii_column_names: string[];  // NEW: Column names
    }>;
}

export default function PIIHeatmap({ projectId }: { projectId: string }) {
    const [data, setData] = useState<PIIHeatmapData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);
                const res = await fetchWithAuth(`projects/${projectId}/pii-heatmap`);
                
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                
                const result = await res.json();
                setData(result);
            } catch (e) {
                console.error('PII Heatmap error:', e);
                setError(e instanceof Error ? e.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [projectId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="text-sm text-gray-500">Analyzing PII patterns...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl p-8 text-center">
                <AlertTriangle size={48} className="mx-auto text-red-500 mb-4" />
                <h3 className="text-lg font-bold text-red-700 dark:text-red-400 mb-2">PII Analysis Failed</h3>
                <p className="text-sm text-red-600 dark:text-red-300">{error}</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-8 text-center">
                <Shield size={48} className="mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-bold mb-2">No PII Data Available</h3>
                <p className="text-sm text-gray-500">Run column analysis on your assets to detect PII.</p>
            </div>
        );
    }

    const chartData = Object.entries(data.pii_by_category || {}).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').toLowerCase(),
        count: value
    }));

    const getRiskColor = (percentage: number) => {
        if (percentage > 30) return { bg: 'bg-red-500', text: 'text-red-600', border: 'border-red-500' };
        if (percentage > 10) return { bg: 'bg-amber-500', text: 'text-amber-600', border: 'border-amber-500' };
        return { bg: 'bg-green-500', text: 'text-green-600', border: 'border-green-500' };
    };

    const riskColors = getRiskColor(data.pii_percentage);

    const getPIIIcon = (type: string) => {
        const iconMap: Record<string, JSX.Element> = {
            EMAIL: <Mail size={14} />,
            PHONE: <Phone size={14} />,
            SSN: <Lock size={14} />,
            CREDIT_CARD: <CreditCard size={14} />,
        };
        return iconMap[type] || <Eye size={14} />;
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-purple-500/10 rounded-2xl flex items-center justify-center">
                    <ShieldAlert size={24} className="text-purple-500" />
                </div>
                <div>
                    <h2 className="text-2xl font-black text-[var(--text-primary)]">PII Detection Heatmap</h2>
                    <p className="text-sm text-[var(--text-tertiary)]">Personally Identifiable Information risk analysis</p>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                        <Shield size={20} className="text-blue-500" />
                        <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Total Columns</span>
                    </div>
                    <p className="text-4xl font-black text-[var(--text-primary)]">{data.total_columns || 0}</p>
                    <p className="text-xs text-gray-500 mt-1">Analyzed across all assets</p>
                </div>
                
                <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                        <ShieldAlert size={20} className="text-amber-500" />
                        <span className="text-xs font-bold uppercase tracking-wider text-gray-500">PII Columns</span>
                    </div>
                    <p className="text-4xl font-black text-amber-600">{data.pii_columns || 0}</p>
                    <p className="text-xs text-gray-500 mt-1">Contains sensitive information</p>
                </div>
                
                <div className={`bg-white dark:bg-gray-900 rounded-xl p-6 border-2 ${riskColors.border} shadow-sm`}>
                    <div className="flex items-center gap-3 mb-3">
                        <AlertTriangle size={20} className={riskColors.text} />
                        <span className="text-xs font-bold uppercase tracking-wider text-gray-500">Risk Level</span>
                    </div>
                    <p className={`text-4xl font-black ${riskColors.text}`}>
                        {data.pii_percentage?.toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                        {data.pii_percentage > 30 ? 'CRITICAL - Immediate attention required' : 
                         data.pii_percentage > 10 ? 'MEDIUM - Review masking strategy' : 
                         'LOW - Within acceptable limits'}
                    </p>
                </div>
            </div>

            {/* Chart */}
            {chartData.length > 0 && (
                <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                    <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                        <Database className="text-purple-500" size={20} />
                        PII Distribution by Category
                    </h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
                            <XAxis 
                                dataKey="name" 
                                tick={{ fill: 'currentColor', fontSize: 12 }}
                                style={{ textTransform: 'capitalize' }}
                            />
                            <YAxis tick={{ fill: 'currentColor', fontSize: 12 }} />
                            <Tooltip 
                                contentStyle={{ 
                                    backgroundColor: 'var(--surface)', 
                                    border: '1px solid var(--border)',
                                    borderRadius: '8px'
                                }}
                            />
                            <Bar dataKey="count" fill="#8b5cf6" radius={[8, 8, 0, 0]}>
                                {chartData.map((entry, index) => (
                                    <Cell 
                                        key={`cell-${index}`} 
                                        fill={`hsl(${280 - index * 20}, 70%, 60%)`}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* High Risk Assets */}
            {data.high_risk_assets && data.high_risk_assets.length > 0 && (
                <div className="bg-white dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <AlertTriangle className="text-red-500" size={20} />
                        High Risk Assets
                        <span className="ml-2 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-xs font-bold rounded-full">
                            {data.high_risk_assets.length}
                        </span>
                    </h3>
                    <div className="space-y-2">
                        {data.high_risk_assets.map((asset) => (
                            <div 
                                key={asset.asset_id} 
                                className="flex flex-col p-4 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg hover:shadow-md transition-all"
                            >
                                {/* Header: Asset name + PII count */}
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
                                            <Database size={20} className="text-red-600 dark:text-red-400" />
                                        </div>
                                        <div>
                                            <p className="font-mono text-sm font-bold text-[var(--text-primary)]">{asset.asset_name}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                {asset.pii_types?.map((type: string) => (
                                                    <span 
                                                        key={type}
                                                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-white dark:bg-gray-800 border border-red-200 dark:border-red-800 rounded text-xs font-bold text-red-600 dark:text-red-400"
                                                    >
                                                        {getPIIIcon(type)}
                                                        {type}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-2xl font-black text-red-600 dark:text-red-400">{asset.pii_columns}</p>
                                        <p className="text-xs text-gray-500 font-bold">PII columns</p>
                                    </div>
                                </div>
                                
                                {/* NEW: List of PII column names */}
                                {asset.pii_column_names && asset.pii_column_names.length > 0 && (
                                    <div className="mt-2 pt-3 border-t border-red-200 dark:border-red-800">
                                        <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold mb-2">PII Columns:</p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {asset.pii_column_names.map((colName: string, idx: number) => (
                                                <span 
                                                    key={idx}
                                                    className="inline-flex items-center px-2 py-1 bg-white dark:bg-gray-800 border border-red-300 dark:border-red-700 rounded text-xs font-mono text-red-700 dark:text-red-300"
                                                >
                                                    {colName}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Recommendations */}
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/10 dark:to-blue-900/10 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
                <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                    <Lock className="text-purple-600" size={20} />
                    Security Recommendations
                </h3>
                <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                        <span className="text-purple-600 font-bold">•</span>
                        <span>Apply column-level encryption for PII fields before migration</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-purple-600 font-bold">•</span>
                        <span>Implement data masking in non-production environments</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-purple-600 font-bold">•</span>
                        <span>Configure row-level security (RLS) policies for sensitive tables</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-purple-600 font-bold">•</span>
                        <span>Enable audit logging for all PII access patterns</span>
                    </li>
                </ul>
            </div>
        </div>
    );
}
