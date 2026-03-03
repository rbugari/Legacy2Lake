"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { fetchWithAuth } from "../../lib/auth-client";
import { ArrowLeft, Save, Loader2, CheckCircle, Settings, ShieldCheck, Terminal, Database, Zap, Box, Cloud, Server, Code, Snowflake, PackageCheck } from "lucide-react";
import Link from "next/link";
import DesignRegistryPanel from "../../components/stages/DesignRegistryPanel";
import PromptsExplorer from "../../components/PromptsExplorer";

function ProjectSettingsContent() {
    const searchParams = useSearchParams();
    const id = searchParams.get('id') || '';

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [config, setConfig] = useState<{ source_tech: string; target_tech: string }>({
        source_tech: "ssis",
        target_tech: "pyspark"
    });
    const [activeTab, setActiveTab] = useState<"general" | "standards" | "intelligence">("general");
    const [availableTech, setAvailableTech] = useState<any>({ sources: [], targets: [] });
    const [project, setProject] = useState<any>(null);

    // Helper function to get icon and color for tech options
    const getTechIcon = (techId: string, techName: string, size: number = 20) => {
        const lowerName = (techName || techId || '').toLowerCase();

        // Input/Source technologies
        if (lowerName.includes('sql server') || techId === 'sqlserver') return { icon: <Database size={size} />, color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500' };
        if (lowerName.includes('oracle') || techId === 'oracle') return { icon: <Database size={size} />, color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500' };
        if (lowerName.includes('ssis') || techId === 'ssis') return { icon: <PackageCheck size={size} />, color: 'text-blue-600', bg: 'bg-blue-600/10', border: 'border-blue-600' };
        if (lowerName.includes('informatica') || techId === 'informatica') return { icon: <Zap size={size} />, color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500' };
        if (lowerName.includes('datastage') || techId === 'datastage') return { icon: <Server size={size} />, color: 'text-purple-500', bg: 'bg-purple-500/10', border: 'border-purple-500' };
        if (lowerName.includes('talend') || techId === 'talend') return { icon: <Code size={size} />, color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500' };
        if (lowerName.includes('mysql') || techId === 'mysql') return { icon: <Database size={size} />, color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400' };
        if (lowerName.includes('postgres') || techId === 'postgresql') return { icon: <Database size={size} />, color: 'text-blue-700', bg: 'bg-blue-700/10', border: 'border-blue-700' };

        // Output/Target technologies
        if (techId === 'databricks') return { icon: <Database size={size} />, color: 'text-orange-600', bg: 'bg-orange-600/10', border: 'border-orange-600' };
        if (techId === 'pyspark') return { icon: <Zap size={size} />, color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500' };
        if (techId === 'cloudera') return { icon: <Cloud size={size} />, color: 'text-blue-400', bg: 'bg-blue-400/10', border: 'border-blue-400' };
        if (lowerName.includes('fabric') || techId === 'fabric') return { icon: <Box size={size} />, color: 'text-blue-600', bg: 'bg-blue-600/10', border: 'border-blue-600' };
        if (lowerName.includes('snowflake') || techId === 'snowflake') return { icon: <Snowflake size={size} />, color: 'text-cyan-500', bg: 'bg-cyan-500/10', border: 'border-cyan-500' };
        if (lowerName.includes('google') || lowerName.includes('gcp') || lowerName.includes('bigquery') || techId === 'gcp' || techId === 'bigquery') return { icon: <Cloud size={size} />, color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500' };
        if (lowerName.includes('aws') || lowerName.includes('glue') || lowerName.includes('redshift') || techId === 'aws' || techId === 'redshift') return { icon: <Server size={size} />, color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500' };
        if (lowerName.includes('salesforce') || techId === 'salesforce') return { icon: <Cloud size={size} />, color: 'text-sky-500', bg: 'bg-sky-500/10', border: 'border-sky-500' };
        if (lowerName.includes('sql') || techId === 'sql') return { icon: <Code size={size} />, color: 'text-gray-500', bg: 'bg-gray-500/10', border: 'border-gray-500' };

        // Default
        return { icon: <Database size={size} />, color: 'text-gray-500', bg: 'bg-gray-500/10', border: 'border-gray-500' };
    };

    useEffect(() => {
        if (!id) return;

        const loadData = async () => {
            try {
                // Run both fetches in parallel — avoids race condition
                const [techRes, projectRes] = await Promise.all([
                    fetchWithAuth("/config/technologies"),
                    fetchWithAuth(`/projects/${id}`)
                ]);

                // 1. Process Tech catalog first
                let mappedData: { sources: any[], targets: any[] } = { sources: [], targets: [] };
                if (techRes.ok) {
                    const techData = await techRes.json();
                    mappedData = {
                        sources: techData.filter((t: any) => t.role === "SOURCE"),
                        targets: techData.filter((t: any) => t.role === "TARGET")
                    };
                    setAvailableTech(mappedData);
                }

                // 2. Process project settings — normalize against actual catalog IDs
                if (projectRes.ok) {
                    const pData = await projectRes.json();
                    setProject(pData);

                    if (pData.settings) {
                        // Case-insensitive match against actual catalog tech_ids
                        const normalizeTechId = (value: string, catalog: any[]) => {
                            if (!value) return '';
                            const lower = value.toLowerCase().trim();
                            // Try exact match first
                            const exact = catalog.find((t: any) => t.tech_id === value);
                            if (exact) return exact.tech_id;
                            // Try case-insensitive match
                            const ci = catalog.find((t: any) =>
                                t.tech_id?.toLowerCase() === lower ||
                                t.name?.toLowerCase() === lower ||
                                t.name?.toLowerCase().includes(lower) ||
                                lower.includes(t.tech_id?.toLowerCase())
                            );
                            if (ci) return ci.tech_id;
                            return value.toLowerCase(); // fallback
                        };

                        const savedSource = pData.settings.source_tech;
                        const savedTarget = pData.settings.target_tech;

                        setConfig({
                            source_tech: normalizeTechId(savedSource, mappedData.sources),
                            target_tech: normalizeTechId(savedTarget, mappedData.targets)
                        });
                    } else {
                        // No settings saved yet — default to first available tech
                        setConfig({
                            source_tech: mappedData.sources[0]?.tech_id || "ssis",
                            target_tech: mappedData.targets[0]?.tech_id || "pyspark"
                        });
                    }
                }
            } catch (error) {
                console.error("Error loading settings:", error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [id]);

    const handleSave = async () => {
        setSaving(true);
        try {
            const res = await fetchWithAuth(`/projects/${id}/settings`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config)
            });

            if (res.ok) {
                alert("Settings saved successfully.");
            } else {
                alert("Error saving settings.");
            }
        } catch (error) {
            console.error(error);
            alert("Connection error.");
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
                <Loader2 className="animate-spin text-primary" size={32} />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 p-8">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6 flex items-center gap-4">
                    <Link href={`/workspace?id=${id}`} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-full transition-colors">
                        <ArrowLeft size={20} />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold">Solution Settings</h1>
                        <p className="text-gray-500 text-sm">Define technologies and design standards.</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-200 dark:border-gray-800 mb-8 overflow-x-auto whitespace-nowrap scrollbar-hide">
                    <button
                        onClick={() => setActiveTab("general")}
                        className={`px-6 py-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${activeTab === "general" ? "border-primary text-primary bg-primary/5" : "border-transparent text-gray-500 hover:text-gray-700"}`}
                    >
                        <Settings size={16} /> General Settings
                    </button>
                    <button
                        onClick={() => setActiveTab("standards")}
                        className={`px-6 py-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${activeTab === "standards" ? "border-primary text-primary bg-primary/5" : "border-transparent text-gray-500 hover:text-gray-700"}`}
                    >
                        <ShieldCheck size={16} /> Design Standards
                    </button>
                    <button
                        onClick={() => setActiveTab("intelligence")}
                        className={`px-6 py-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${activeTab === "intelligence" ? "border-primary text-primary bg-primary/5" : "border-transparent text-gray-500 hover:text-gray-700"}`}
                    >
                        <Terminal size={16} /> Intelligence Hub (Prompts)
                    </button>
                </div>

                <div className="space-y-6">
                    {activeTab === "general" && (
                        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm p-6 space-y-8 animate-in fade-in duration-300">
                            {/* Source Tech */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <label className="block text-sm font-bold">Origin Technology (Legacy)</label>
                                    <span className="text-xs text-gray-500 uppercase tracking-wider">Input Technology</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {availableTech.sources?.length > 0 ? (
                                        availableTech.sources.map((t: any) => {
                                            const isActive = config.source_tech === t.tech_id;
                                            const techStyle = getTechIcon(t.tech_id, t.label, 20);
                                            return (
                                                <button
                                                    key={t.tech_id}
                                                    onClick={() => setConfig({ ...config, source_tech: t.tech_id })}
                                                    className={`flex flex-col p-4 rounded-xl border-2 text-left transition-all ${isActive
                                                        ? `${techStyle.bg} ${techStyle.border} shadow-md`
                                                        : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                                                        }`}
                                                    title={t.label}
                                                >
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className={`p-2 rounded-lg ${isActive ? 'bg-white/20 dark:bg-white/10' : 'bg-gray-200 dark:bg-gray-700'}`}>
                                                            <span className={isActive ? techStyle.color : 'text-gray-500'}>
                                                                {techStyle.icon}
                                                            </span>
                                                        </div>
                                                        {isActive && <CheckCircle size={16} className={techStyle.color} />}
                                                    </div>
                                                    <span className={`font-bold text-xs leading-tight ${isActive ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'}`}>
                                                        {t.label}
                                                    </span>
                                                </button>
                                            );
                                        })
                                    ) : (
                                        <div className="col-span-4 text-center py-4 text-sm text-gray-500">No sources configured</div>
                                    )}
                                </div>
                                <p className="text-xs text-gray-400 mt-2">The format of the packages you will upload to the project.</p>
                            </div>

                            {/* Target Tech */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <label className="block text-sm font-bold">Target Technology (Lakehouse)</label>
                                    <span className="text-xs text-gray-500 uppercase tracking-wider">Output Technology</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {availableTech.targets?.length > 0 ? (
                                        availableTech.targets.map((t: any) => {
                                            const isActive = config.target_tech === t.tech_id;
                                            const techStyle = getTechIcon(t.tech_id, t.label, 20);
                                            return (
                                                <button
                                                    key={t.tech_id}
                                                    onClick={() => setConfig({ ...config, target_tech: t.tech_id })}
                                                    className={`flex flex-col p-4 rounded-xl border-2 text-left transition-all ${isActive
                                                        ? `${techStyle.bg} ${techStyle.border} shadow-md`
                                                        : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                                                        }`}
                                                    title={t.label}
                                                >
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className={`p-2 rounded-lg ${isActive ? 'bg-white/20 dark:bg-white/10' : 'bg-gray-200 dark:bg-gray-700'}`}>
                                                            <span className={isActive ? techStyle.color : 'text-gray-500'}>
                                                                {techStyle.icon}
                                                            </span>
                                                        </div>
                                                        {isActive && <CheckCircle size={16} className={techStyle.color} />}
                                                    </div>
                                                    <span className={`font-bold text-xs leading-tight ${isActive ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'}`}>
                                                        {t.label}
                                                    </span>
                                                </button>
                                            );
                                        })
                                    ) : (
                                        <div className="col-span-4 text-center py-4 text-sm text-gray-500">No targets configured</div>
                                    )}
                                </div>
                                <p className="text-xs text-gray-400 mt-2">The platform where the modernized code will be executed.</p>
                            </div>

                            <div className="pt-4 border-t border-gray-100 dark:border-gray-800 flex justify-end">
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="bg-primary text-white px-6 py-2 rounded-lg font-bold hover:bg-secondary transition-all flex items-center gap-2 shadow-lg shadow-primary/20 disabled:opacity-50"
                                >
                                    {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === "standards" && (
                        <div className="animate-in fade-in duration-300">
                            <DesignRegistryPanel projectId={id} />
                        </div>
                    )}

                    {activeTab === "intelligence" && (
                        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm p-6 animate-in fade-in duration-300 min-h-[500px]">
                            <PromptsExplorer projectId={id} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function ProjectSettings() {
    return (
        <Suspense fallback={<div>Loading Settings...</div>}>
            <ProjectSettingsContent />
        </Suspense>
    );
}
