"use client";
import React, { useEffect, useState } from 'react';
import { Database, Code, Zap, CheckCircle, RefreshCw, Cloud, Server, Box, Snowflake } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface TechnologyMixerProps {
    projectId: string;
}

export default function TechnologyMixer({ projectId }: TechnologyMixerProps) {
    const [stack, setStack] = useState<string>("pyspark");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const normalizeTargetTech = (value: string) => {
        if (!value) return 'pyspark';

        const mapping: Record<string, string> = {
            'Microsoft Fabric': 'fabric',
            'MS Fabric': 'fabric',
            'Fabric': 'fabric',
            'Databricks': 'databricks',
            'Databricks PySpark': 'databricks',
            'PySpark': 'pyspark',
            'PySpark Generic': 'pyspark',
            'PySpark Native': 'pyspark',
            'Cloudera': 'cloudera',
            'Cloudera Spark': 'cloudera',
            'Snowflake': 'snowflake',
            'Google Cloud': 'gcp',
            'GCP': 'gcp',
            'BigQuery': 'gcp',
            'AWS': 'aws',
            'Amazon Web Services': 'aws',
            'Salesforce': 'salesforce',
            'SQL': 'sql',
            'Pure SQL': 'sql'
        };

        // Try exact match first
        if (mapping[value]) return mapping[value];

        // Try lowercase match (most IDs are already lowercase)
        const lower = value.toLowerCase();
        if (['databricks', 'pyspark', 'cloudera', 'fabric', 'snowflake', 'gcp', 'aws', 'salesforce', 'sql'].includes(lower)) {
            return lower;
        }

        // Default to pyspark if unknown
        return 'pyspark';
    };

    const fetchStack = async () => {
        setLoading(true);
        try {
            // First, try to get from registry
            const res = await fetchWithAuth(`/projects/${projectId}/registry`);
            const data = await res.json();
            console.log('[TechnologyMixer] Registry data:', data);

            if (data.registry) {
                const target = data.registry.find((r: any) => r.key === 'target_stack');
                if (target) {
                    const normalizedTech = normalizeTargetTech(target.value);
                    console.log('[TechnologyMixer] Found target_stack in registry:', target.value, '->', normalizedTech);
                    setStack(normalizedTech);
                    setLoading(false);
                    return;
                }
            }

            // If not found in registry, get from project settings (default configuration)
            const settingsRes = await fetchWithAuth(`/projects/${projectId}/settings`);
            const settings = await settingsRes.json();
            console.log('[TechnologyMixer] Project settings:', settings);

            if (settings.target_tech) {
                const normalizedTech = normalizeTargetTech(settings.target_tech);
                console.log('[TechnologyMixer] Normalized target_tech:', settings.target_tech, '->', normalizedTech);
                setStack(normalizedTech);
            } else {
                console.log('[TechnologyMixer] No target_tech found in settings, using default: pyspark');
            }
        } catch (e) {
            console.error("Failed to fetch stack", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStack();
    }, [projectId]);

    const handleSelect = async (newStack: string) => {
        if (newStack === stack) return;
        setSaving(true);
        try {
            await fetchWithAuth(`/projects/${projectId}/registry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    category: 'PATHS',
                    key: 'target_stack',
                    value: newStack
                })
            });
            setStack(newStack);
        } catch (e) {
            alert("Error saving technology preference");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="h-24 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-2xl" />;

    const options = [
        {
            id: 'databricks',
            label: 'Databricks PySpark',
            desc: 'Databricks Platform & Delta Lake',
            icon: <Database className="text-orange-600" />,
            color: 'border-orange-600 bg-orange-50/50 dark:bg-orange-900/10'
        },
        {
            id: 'pyspark',
            label: 'PySpark Generic',
            desc: 'Standard Apache Spark SQL & Python',
            icon: <Zap className="text-blue-500" />,
            color: 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/10'
        },
        {
            id: 'cloudera',
            label: 'Cloudera Spark',
            desc: 'CDP Datahub & Apache Spark',
            icon: <Cloud className="text-emerald-500" />,
            color: 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/10'
        },
        {
            id: 'fabric',
            label: 'MS Fabric',
            desc: 'Lakehouse + Power BI Semantic',
            icon: <Box className="text-blue-600" />,
            color: 'border-blue-600 bg-blue-50/50 dark:bg-blue-900/10'
        },
        {
            id: 'snowflake',
            label: 'Snowflake',
            desc: 'Snowpark Python + Native Tasks',
            icon: <Snowflake className="text-cyan-500" />,
            color: 'border-cyan-500 bg-cyan-50/50 dark:bg-cyan-900/10'
        },
        {
            id: 'gcp',
            label: 'Google Cloud',
            desc: 'BigQuery + Looker + Airflow',
            icon: <Cloud className="text-red-500" />,
            color: 'border-red-500 bg-red-50/50 dark:bg-red-900/10'
        },
        {
            id: 'aws',
            label: 'AWS',
            desc: 'Glue + Redshift + QuickSight',
            icon: <Server className="text-orange-500" />,
            color: 'border-orange-500 bg-orange-50/50 dark:bg-orange-900/10'
        },
        {
            id: 'salesforce',
            label: 'Salesforce',
            desc: 'Data Cloud + Tableau (.tds)',
            icon: <Cloud className="text-sky-500" />,
            color: 'border-sky-500 bg-sky-50/50 dark:bg-sky-900/10'
        },
        {
            id: 'sql',
            label: 'Pure SQL',
            desc: 'Stored Procedures & DDL (Standard)',
            icon: <Code className="text-gray-500" />,
            color: 'border-gray-500 bg-gray-50/50 dark:bg-gray-900/10'
        }
    ];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h4 className="text-sm font-bold text-gray-400 uppercase tracking-widest">Technology Mixer</h4>
                    <p className="text-xs text-gray-500 mt-0.5">Choose the output dialect for code generation</p>
                </div>
                {saving && <RefreshCw size={14} className="text-primary animate-spin" />}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {options.map((opt) => {
                    const isActive = stack === opt.id;
                    return (
                        <button
                            key={opt.id}
                            onClick={() => handleSelect(opt.id)}
                            disabled={saving}
                            className={`flex flex-col p-4 rounded-2xl border-2 text-left transition-all ${isActive
                                ? `${opt.color} shadow-sm border-current`
                                : 'bg-white dark:bg-gray-900 border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div className="p-2 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
                                    {opt.icon}
                                </div>
                                {isActive && <CheckCircle size={16} className="text-current" />}
                            </div>
                            <span className={`font-bold text-sm ${isActive ? 'text-gray-900 dark:text-white' : 'text-gray-500'}`}>{opt.label}</span>
                            <span className="text-[10px] text-gray-400 mt-1 leading-tight">{opt.desc}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
