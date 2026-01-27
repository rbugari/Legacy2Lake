"use client";
import React, { useEffect, useState } from 'react';
import { Settings, Save, RefreshCw, Zap, Sliders, Code } from 'lucide-react';
import { fetchWithAuth } from '../../lib/auth-client';
import VariableEditor from '../VariableEditor';

interface ProjectSettingsPanelProps {
    projectId: string;
    onSettingsChange?: (settings: any) => void;
}

export default function ProjectSettingsPanel({ projectId, onSettingsChange }: ProjectSettingsPanelProps) {
    const [settings, setSettings] = useState<any>({
        migration_limit: 0
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const fetchSettings = async () => {
        setLoading(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/settings`);
            const data = await res.json();
            if (data.settings) {
                setSettings(data.settings);
                if (onSettingsChange) onSettingsChange(data.settings);
            }
        } catch (e) {
            console.error("Failed to fetch settings", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSettings();
    }, [projectId]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await fetchWithAuth(`projects/${projectId}/settings`, {
                method: 'PATCH',
                body: JSON.stringify({ settings })
            });
            if (onSettingsChange) onSettingsChange(settings);
        } catch (e) {
            console.error("Failed to save settings", e);
            alert("Error saving settings");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="h-32 animate-pulse bg-gray-50 dark:bg-gray-900/50 rounded-2xl" />;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-gray-800 pb-4">
                <div>
                    <h3 className="text-lg font-bold flex items-center gap-2">
                        <Settings size={20} className="text-primary" />
                        Project Settings
                    </h3>
                    <p className="text-sm text-gray-500">Global execution parameters for this solution.</p>
                </div>
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-dark transition-colors disabled:opacity-50"
                >
                    {saving ? <RefreshCw size={18} className="animate-spin" /> : <Save size={18} />}
                    Save Changes
                </button>
            </div>

            {/* Batch Limit Control */}
            <div className="bg-gray-50 dark:bg-gray-900/40 p-6 rounded-2xl border border-gray-100 dark:border-gray-800">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h4 className="font-bold flex items-center gap-2">
                            <Sliders size={18} className="text-primary" />
                            Batch Limit (Orchestration)
                        </h4>
                        <p className="text-xs text-gray-500 mt-1 max-w-md">
                            Defines how many files to process in a single run.
                            Useful for controlled testing before massive migration.
                        </p>
                    </div>
                    <div className="text-right">
                        <span className="text-2xl font-mono font-bold text-primary">
                            {settings.migration_limit === 0 ? "UNLIMITED" : settings.migration_limit}
                        </span>
                    </div>
                </div>

                <div className="space-y-4">
                    <input
                        type="range"
                        min="0"
                        max="50"
                        step="1"
                        value={settings.migration_limit || 0}
                        onChange={(e) => setSettings({ ...settings, migration_limit: parseInt(e.target.value) })}
                        className="w-full h-2 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <div className="flex justify-between text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">
                        <span>Unlimited</span>
                        <span>5 Files</span>
                        <span>10 Files</span>
                        <span>25 Files</span>
                        <span>50 Files</span>
                    </div>
                </div>
            </div>

            {/* Variable Injection (Phase 8) */}
            <div className="bg-gray-50 dark:bg-gray-900/40 p-6 rounded-2xl border border-gray-100 dark:border-gray-800">
                <div className="mb-6">
                    <h4 className="font-bold flex items-center gap-2">
                        <Code size={18} className="text-secondary" />
                        Variables & Environment Parameters
                    </h4>
                    <p className="text-xs text-gray-500 mt-1">
                        Define global variables (e.g., S3 buckets, connection strings) to be automatically injected into the generated code.
                    </p>
                </div>

                <VariableEditor
                    variables={settings.variables || []}
                    onChange={(vars) => setSettings({ ...settings, variables: vars })}
                />
            </div>
            {/* Other settings can be added here in the future */}
        </div >
    );
}
