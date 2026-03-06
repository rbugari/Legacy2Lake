"use client";
import React, { useEffect, useState } from 'react';
import { Database, Code, Zap, CheckCircle, RefreshCw, Cloud, Server, Box, Snowflake } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';

interface TechnologyMixerProps {
    projectId: string;
}

interface DestinationOption {
    tech_id: string;
    label: string;
    description?: string;
    is_active: boolean;
}

// Icon map by tech_id — only visuals, not business logic
const ICON_MAP: Record<string, React.ReactNode> = {
    pyspark: <Zap className="text-blue-500" />,
    snowflake: <Snowflake className="text-cyan-500" />,
    snowflake_sql: <Code className="text-cyan-400" />,
    fabric: <Box className="text-blue-600" />,
    ms_fabric_sql: <Database className="text-indigo-500" />,
    gcp: <Cloud className="text-red-500" />,
    aws: <Server className="text-orange-500" />,
    salesforce: <Cloud className="text-sky-500" />,
    dbt: <Code className="text-orange-400" />,
    base: <Code className="text-gray-500" />,
};

const COLOR_MAP: Record<string, string> = {
    pyspark: 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/10',
    snowflake: 'border-cyan-500 bg-cyan-50/50 dark:bg-cyan-900/10',
    snowflake_sql: 'border-cyan-400 bg-cyan-50/50 dark:bg-cyan-900/10',
    fabric: 'border-blue-600 bg-blue-50/50 dark:bg-blue-900/10',
    ms_fabric_sql: 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/10',
    gcp: 'border-red-500 bg-red-50/50 dark:bg-red-900/10',
    aws: 'border-orange-500 bg-orange-50/50 dark:bg-orange-900/10',
    salesforce: 'border-sky-500 bg-sky-50/50 dark:bg-sky-900/10',
    dbt: 'border-orange-400 bg-orange-50/50 dark:bg-orange-900/10',
    base: 'border-gray-500 bg-gray-50/50 dark:bg-gray-900/10',
};

const DEFAULT_ICON = <Database className="text-gray-400" />;
const DEFAULT_COLOR = 'border-gray-400 bg-gray-50/50 dark:bg-gray-900/10';

export default function TechnologyMixer({ projectId }: TechnologyMixerProps) {
    const [stack, setStack] = useState<string>("pyspark");
    const [destinations, setDestinations] = useState<DestinationOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            // Load both in parallel: available destinations from catalog + current project stack
            const [catalogRes, registryRes, settingsRes] = await Promise.all([
                fetchWithAuth('/config/technologies'),
                fetchWithAuth(`/projects/${projectId}/registry`),
                fetchWithAuth(`/projects/${projectId}/settings`),
            ]);

            // 1. Build destination list from utm_system_catalog (TARGET role only)
            if (catalogRes.ok) {
                const catalog: DestinationOption[] = await catalogRes.json();
                const targets = catalog.filter(t => t.is_active && t.role?.toUpperCase() === 'TARGET');
                setDestinations(targets);
            }

            // 2. Resolve current project tech (registry > settings)
            let fromRegistry: string | null = null;
            let fromSettings: string | null = null;

            if (registryRes.ok) {
                const data = await registryRes.json();
                const target = data.registry?.find((r: any) => r.key === 'target_stack');
                if (target?.value) fromRegistry = target.value.toLowerCase().trim();
            }

            if (settingsRes.ok) {
                const settingsData = await settingsRes.json();
                const targetTech = settingsData.settings?.target_tech || settingsData.target_tech;
                if (targetTech) fromSettings = targetTech.toLowerCase().trim();
            }

            // Priority: explicit registry override > settings > default
            const resolved = (fromRegistry && fromRegistry !== 'pyspark')
                ? fromRegistry
                : fromSettings || fromRegistry || 'pyspark';

            setStack(resolved);

        } catch (e) {
            console.error("TechnologyMixer: Failed to fetch data", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
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

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h4 className="text-sm font-bold text-gray-400 uppercase tracking-widest">Technology Mixer</h4>
                    <p className="text-xs text-gray-500 mt-0.5">Choose the output dialect for code generation</p>
                </div>
                {saving && <RefreshCw size={14} className="text-primary animate-spin" />}
            </div>

            {destinations.length === 0 ? (
                <div className="p-6 border border-dashed border-gray-300 dark:border-gray-700 rounded-2xl text-center">
                    <p className="text-xs text-gray-500">No active destinations configured. Add them in the System Catalog.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {destinations.map((opt) => {
                        const isActive = stack === opt.tech_id;
                        const icon = ICON_MAP[opt.tech_id] || DEFAULT_ICON;
                        const color = COLOR_MAP[opt.tech_id] || DEFAULT_COLOR;
                        return (
                            <button
                                key={opt.tech_id}
                                onClick={() => handleSelect(opt.tech_id)}
                                disabled={saving}
                                className={`flex flex-col p-4 rounded-2xl border-2 text-left transition-all ${isActive
                                    ? `${color} shadow-sm border-current`
                                    : 'bg-white dark:bg-gray-900 border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="p-2 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
                                        {icon}
                                    </div>
                                    {isActive && <CheckCircle size={16} className="text-current" />}
                                </div>
                                <span className={`font-bold text-sm ${isActive ? 'text-gray-900 dark:text-white' : 'text-gray-500'}`}>
                                    {opt.label}
                                </span>
                                <span className="text-[10px] text-gray-400 mt-1 leading-tight">
                                    {opt.description || opt.tech_id}
                                </span>
                            </button>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
