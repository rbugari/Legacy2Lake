"use client";
import React, { useEffect, useState } from 'react';
import { Save, RefreshCw, Settings, Type, Folder, Lock, AlertTriangle } from 'lucide-react';
import { API_BASE_URL } from '../../lib/config';

interface DesignRegistryPanelProps {
    projectId: string;
}

export default function DesignRegistryPanel({ projectId }: DesignRegistryPanelProps) {
    const [registry, setRegistry] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [edits, setEdits] = useState<Record<string, string>>({});

    const fetchRegistry = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/registry`);
            const data = await res.json();
            if (data.registry) {
                setRegistry(data.registry);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRegistry();
    }, [projectId]);

    const handleSave = async (category: string, key: string) => {
        const newValue = edits[`${category}-${key}`];
        if (newValue === undefined) return; // No change

        setSaving(true);
        try {
            await fetch(`${API_BASE_URL}/projects/${projectId}/registry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category, key, value: newValue })
            });
            // Refresh to confirm
            await fetchRegistry();
            // Clear edit state for this item
            const newEdits = { ...edits };
            delete newEdits[`${category}-${key}`];
            setEdits(newEdits);
        } catch (e) {
            alert("Failed to save.");
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (category: string, key: string, val: string) => {
        setEdits(prev => ({ ...prev, [`${category}-${key}`]: val }));
    };

    // Group by Category
    const grouped = registry.reduce((acc: any, item: any) => {
        const cat = item.category || "GENERAL";
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(item);
        return acc;
    }, {});

    const renderIcon = (cat: string) => {
        switch (cat) {
            case "NAMING": return <Type size={16} className="text-blue-500" />;
            case "PATHS": return <Folder size={16} className="text-orange-500" />;
            case "PRIVACY": return <Lock size={16} className="text-red-500" />;
            default: return <Settings size={16} className="text-gray-500" />;
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500 animate-pulse">Loading Registry...</div>;

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-8">
            <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-sm">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold flex items-center gap-2">
                            <Settings className="text-primary" /> Design Registry
                        </h2>
                        <p className="text-gray-500 text-sm mt-1">
                            Define the architectural standards for your solution.
                            These rules are injected into the Architect Agents.
                        </p>
                    </div>
                    <button onClick={fetchRegistry} className="p-2 hover:bg-gray-100 rounded-full text-gray-400 hover:text-gray-700 transition">
                        <RefreshCw size={20} />
                    </button>
                </div>

                <div className="space-y-6">
                    {Object.keys(grouped).map(cat => (
                        <div key={cat} className="space-y-3">
                            <div className="flex items-center gap-2 text-sm font-bold text-gray-400 uppercase tracking-wider border-b border-gray-100 dark:border-gray-800 pb-2">
                                {renderIcon(cat)} {cat} Rules
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {grouped[cat].map((item: any) => {
                                    if (item.key === 'target_stack') return null; // Handled by TechnologyMixer
                                    const editKey = `${cat}-${item.key}`;
                                    const value = edits[editKey] !== undefined ? edits[editKey] : item.value;
                                    const isDirty = edits[editKey] !== undefined && edits[editKey] !== item.value;

                                    return (
                                        <div key={item.key} className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-xl border border-gray-200 dark:border-gray-800 flex flex-col gap-2">
                                            <label className="text-xs font-bold text-gray-500">{item.key.replace(/_/g, ' ').toUpperCase()}</label>
                                            <div className="flex gap-2">
                                                <textarea
                                                    value={value}
                                                    onChange={(e) => handleChange(cat, item.key, e.target.value)}
                                                    className="flex-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none transition-all h-20 resize-y"
                                                    rows={2}
                                                />
                                                {isDirty && (
                                                    <button
                                                        onClick={() => handleSave(cat, item.key)}
                                                        disabled={saving}
                                                        className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg shadow-lg shadow-blue-200 dark:shadow-none transition-all"
                                                    >
                                                        <Save size={16} className={saving ? "animate-spin" : ""} />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl flex items-start gap-4 border border-blue-100 dark:border-blue-900/20">
                <AlertTriangle className="text-blue-500 shrink-0 mt-1" size={20} />
                <div className="text-sm text-blue-800 dark:text-blue-200">
                    <strong>Note:</strong> Changes to the Design Registry will affect future code generation.
                    Existing code will not be updated automatically until you re-run the <strong>Refinement Phase</strong>.
                </div>
            </div>
        </div>
    );
}
