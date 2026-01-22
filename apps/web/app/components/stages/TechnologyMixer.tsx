"use client";
import React, { useEffect, useState } from 'react';
import { Database, Code, Zap, CheckCircle, RefreshCw } from 'lucide-react';
import { API_BASE_URL } from '../../lib/config';

interface TechnologyMixerProps {
    projectId: string;
}

export default function TechnologyMixer({ projectId }: TechnologyMixerProps) {
    const [stack, setStack] = useState<string>("pyspark");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const fetchStack = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/registry`);
            const data = await res.json();
            if (data.registry) {
                const target = data.registry.find((r: any) => r.key === 'target_stack');
                if (target) setStack(target.value);
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
            await fetch(`${API_BASE_URL}/projects/${projectId}/registry`, {
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
            id: 'pyspark',
            label: 'PySpark Native',
            desc: 'Delta Lake & Spark SQL (Standard)',
            icon: <Zap className="text-blue-500" />,
            color: 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/10'
        },
        {
            id: 'sql',
            label: 'Pure SQL',
            desc: 'Stored Procedures & DDL (Legacy Native)',
            icon: <Code className="text-orange-500" />,
            color: 'border-orange-500 bg-orange-50/50 dark:bg-orange-900/10'
        },
        {
            id: 'both',
            label: 'Mixed / Dual',
            desc: 'Generate both PySpark and SQL dialects',
            icon: <Database className="text-purple-500" />,
            color: 'border-purple-500 bg-purple-50/50 dark:bg-purple-900/10'
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
