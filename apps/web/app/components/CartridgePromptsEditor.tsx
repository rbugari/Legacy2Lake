"use client";
import React, { useState, useEffect } from 'react';
import { Layers, Save, RefreshCw, FileCode, AlertCircle, Info, Lock, Edit3, ClipboardList } from 'lucide-react';
import { fetchWithAuth } from '../lib/auth-client';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CartridgePromptsEditorProps {
    projectId: string;
}

interface CartridgePrompt {
    layer: 'bronze' | 'silver' | 'gold';
    prompt_id: string;
    core_content: string;
    override_content: string;
    is_loading: boolean;
}

const LAYER_CONFIG = {
    bronze: {
        name: 'Bronze Layer',
        icon: '🟤',
        description: 'Raw data ingestion patterns',
        color: 'orange'
    },
    silver: {
        name: 'Silver Layer',
        icon: '⚪',
        description: 'Data transformation and cleansing patterns',
        color: 'gray'
    },
    gold: {
        name: 'Gold Layer',
        icon: '🟡',
        description: 'Business logic and aggregation patterns',
        color: 'yellow'
    }
};

export default function CartridgePromptsEditor({ projectId }: CartridgePromptsEditorProps) {
    const [targetTech, setTargetTech] = useState<string>('');
    const [cartridges, setCartridges] = useState<CartridgePrompt[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedLayer, setSelectedLayer] = useState<'bronze' | 'silver' | 'gold'>('bronze');
    const [editedOverride, setEditedOverride] = useState<string>('');
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadProjectTechnology();
    }, [projectId]);

    useEffect(() => {
        if (targetTech) {
            loadCartridgePrompts();
        }
    }, [targetTech]);

    useEffect(() => {
        const selected = cartridges.find(c => c.layer === selectedLayer);
        setEditedOverride(selected?.override_content || '');
    }, [selectedLayer, cartridges]);

    const loadProjectTechnology = async () => {
        try {
            const res = await fetchWithAuth(`/projects/${projectId}/settings`);
            const settings = await res.json();

            if (settings.target_tech) {
                setTargetTech(settings.target_tech);
            } else {
                console.error('[CartridgeEditor] No target_tech found in project settings');
            }
        } catch (e) {
            console.error('[CartridgeEditor] Failed to load project technology', e);
        }
    };

    const getNormalizedTechId = (tech: string) => {
        const t = tech.toLowerCase();
        if (t.includes('databricks')) return 'databricks';
        if (t.includes('snowflake')) return 'snowflake';
        if (t.includes('fabric')) return 'fabric';
        if (t.includes('bigquery')) return 'bigquery';
        if (t.includes('redshift')) return 'redshift';
        if (t.includes('glue')) return 'aws_glue';
        if (t.includes('pyspark')) return 'pyspark';
        return t.replace(/[^a-z0-9_]/g, '_');
    };

    const loadCartridgePrompts = async () => {
        setLoading(true);
        try {
            const layers: ('bronze' | 'silver' | 'gold')[] = ['bronze', 'silver', 'gold'];
            const loadedCartridges: CartridgePrompt[] = [];
            const normalizedTech = getNormalizedTechId(targetTech);

            for (const layer of layers) {
                const prompt_id = `cartridge_${normalizedTech}_${layer}`;
                let core_content = '';
                let override_content = '';

                try {
                    // 1. Load CORE prompt
                    const coreRes = await fetchWithAuth(`/api/v1/prompts/${prompt_id}`);
                    if (coreRes.ok) {
                        const coreData = await coreRes.json();
                        core_content = coreData.content || '';
                    } else {
                        core_content = `// Core prompt not found: ${prompt_id}\n// Please contact administrator to initialize this cartridge.`;
                    }

                    // 2. Load PROJECT OVERRIDE
                    const overrideRes = await fetchWithAuth(`/api/v1/prompts/overrides/${projectId}/${prompt_id}`);
                    if (overrideRes.ok) {
                        const overrideData = await overrideRes.json();
                        override_content = overrideData.content || '';
                    }
                } catch (e) {
                    console.warn(`[CartridgeEditor] Error loading data for ${prompt_id}:`, e);
                }

                loadedCartridges.push({
                    layer,
                    prompt_id,
                    core_content,
                    override_content,
                    is_loading: false
                });
            }

            setCartridges(loadedCartridges);
        } catch (e) {
            console.error('[CartridgeEditor] Failed to load cartridge prompts', e);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveOverride = async () => {
        const selected = cartridges.find(c => c.layer === selectedLayer);
        if (!selected) return;

        setSaving(true);
        try {
            const res = await fetchWithAuth(`/api/v1/prompts/overrides/${projectId}/${selected.prompt_id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: editedOverride
                })
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Failed to save override');
            }

            // Update local state
            setCartridges(prev => prev.map(c =>
                c.layer === selectedLayer
                    ? { ...c, override_content: editedOverride }
                    : c
            ));

            alert('✅ Project-specific instructions saved successfully!');
        } catch (e: any) {
            console.error('[CartridgeEditor] Failed to save override', e);
            alert(`❌ Failed to save changes: ${e.message}`);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center p-20 space-y-4">
                <RefreshCw size={32} className="animate-spin text-purple-600" />
                <p className="text-gray-500 font-medium">Loading cartridge architecture...</p>
            </div>
        );
    }

    if (!targetTech) {
        return (
            <div className="bg-yellow-50 dark:bg-yellow-900/10 p-6 rounded-xl border border-yellow-200 dark:border-yellow-900/20 text-center">
                <AlertCircle className="mx-auto mb-4 text-yellow-600" size={48} />
                <h3 className="text-lg font-bold mb-2">Target Tech Not Configured</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                    Target technology is required to load cartridges.
                </p>
            </div>
        );
    }

    const selectedCartridge = cartridges.find(c => c.layer === selectedLayer);

    return (
        <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950">
            {/* Main Header */}
            <div className="bg-white dark:bg-gray-900 p-6 border-b border-gray-200 dark:border-gray-800">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                            <Layers className="text-purple-600" size={24} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold">2-Layer Cartridge Architecture: {targetTech.toUpperCase()}</h2>
                            <p className="text-sm text-gray-500">
                                Combine immutable system logic with project-level adjustments
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Left Sidebar: Layer Navigation */}
                <div className="w-64 border-r border-gray-200 dark:border-gray-800 p-4 space-y-3 overflow-y-auto">
                    {(['bronze', 'silver', 'gold'] as const).map(layer => {
                        const config = LAYER_CONFIG[layer];
                        const isSelected = selectedLayer === layer;
                        const cartridge = cartridges.find(c => c.layer === layer);

                        return (
                            <button
                                key={layer}
                                onClick={() => setSelectedLayer(layer)}
                                className={`w-full p-4 rounded-xl border-2 transition-all text-left ${isSelected
                                        ? `border-${config.color}-500 bg-${config.color}-50 dark:bg-${config.color}-900/10`
                                        : 'border-transparent hover:bg-gray-100 dark:hover:bg-gray-900'
                                    }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xl font-bold">{config.name}</span>
                                    {cartridge?.override_content && <Edit3 size={14} className="text-blue-500" />}
                                </div>
                                <p className="text-xs text-gray-500 line-clamp-2">{config.description}</p>
                            </button>
                        );
                    })}
                </div>

                {/* Right Area: Split Editor */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Layer Header */}
                    <div className="px-6 py-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">{LAYER_CONFIG[selectedLayer].icon}</span>
                            <div>
                                <h3 className="font-bold text-lg">{LAYER_CONFIG[selectedLayer].name}</h3>
                                <code className="text-[10px] text-gray-400 font-mono bg-gray-100 dark:bg-gray-800 px-1 rounded">
                                    {selectedCartridge?.prompt_id}
                                </code>
                            </div>
                        </div>
                        <button
                            onClick={handleSaveOverride}
                            disabled={saving}
                            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-bold shadow-sm transition flex items-center gap-2"
                        >
                            <Save size={18} />
                            {saving ? 'Saving...' : 'Save Rules'}
                        </button>
                    </div>

                    {/* Split Content Area */}
                    <div className="flex-1 flex overflow-hidden">
                        {/* Layer 1: Core System Logic (Read-Only) */}
                        <div className="w-1/2 flex flex-col border-r border-gray-200 dark:border-gray-800">
                            <div className="px-4 py-2 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-800 flex items-center gap-2 text-xs font-bold text-gray-500">
                                <Lock size={12} />
                                1. CORE SYSTEM RULES (READ-ONLY)
                            </div>
                            <div className="flex-1 overflow-auto bg-[#1e1e1e]">
                                <SyntaxHighlighter
                                    language="markdown"
                                    style={vscDarkPlus}
                                    customStyle={{ margin: 0, padding: '1.5rem', fontSize: '12px' }}
                                >
                                    {selectedCartridge?.core_content || '# No core logic found for this layer'}
                                </SyntaxHighlighter>
                            </div>
                        </div>

                        {/* Layer 2: User-Specific Adjustments (Editable) */}
                        <div className="w-1/2 flex flex-col bg-white dark:bg-gray-950">
                            <div className="px-4 py-2 bg-blue-50 dark:bg-blue-900/10 border-b border-blue-100 dark:border-blue-900/20 flex items-center gap-2 text-xs font-bold text-blue-600 dark:text-blue-400">
                                <ClipboardList size={12} />
                                2. PROJECT-SPECIFIC ADJUSTMENTS (EDITABLE)
                            </div>
                            <div className="p-4 flex flex-col gap-4">
                                <div className="text-xs text-gray-500 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg flex items-start gap-2 italic">
                                    <Info size={14} className="shrink-0 mt-0.5" />
                                    Use this area to add specific rules or exceptions for this project.
                                    These instructions will be followed alongside the Core Rules.
                                </div>
                                <textarea
                                    value={editedOverride}
                                    onChange={(e) => setEditedOverride(e.target.value)}
                                    className="flex-1 min-h-[400px] w-full p-4 bg-transparent border border-gray-200 dark:border-gray-800 rounded-xl focus:ring-2 focus:ring-purple-500 outline-none font-mono text-sm resize-none"
                                    placeholder="Ex: - All date columns must use YYYY-MM-DD format&#10;- Add 'raw_' prefix to all ingestion tables&#10;- Apply currency conversion rules for 'amount' field..."
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
