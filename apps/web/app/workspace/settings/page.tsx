"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { API_BASE_URL } from "../../lib/config";
import { ArrowLeft, Save, Loader2, CheckCircle, Settings, ShieldCheck, Terminal } from "lucide-react";
import Link from "next/link";
import DesignRegistryPanel from "../../components/stages/DesignRegistryPanel";
import PromptsExplorer from "../../components/PromptsExplorer";

function ProjectSettingsContent() {
    const searchParams = useSearchParams();
    const id = searchParams.get('id') || '';

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [config, setConfig] = useState<{ source_tech: string; target_tech: string }>({
        source_tech: "SSIS",
        target_tech: "Databricks"
    });
    const [activeTab, setActiveTab] = useState<"general" | "standards" | "intelligence">("general");
    const [availableTech, setAvailableTech] = useState<any>({ sources: [], targets: [] });
    const [project, setProject] = useState<any>(null);

    useEffect(() => {
        if (!id) return;

        const loadData = async () => {
            try {
                // 1. Fetch Tech Options
                const techRes = await fetch(`${API_BASE_URL}/config/technologies`);
                if (techRes.ok) {
                    const techData = await techRes.json();
                    // Map flat list to {sources, targets} expected by the UI
                    const mappedData = {
                        sources: techData.filter((t: any) => t.role === "SOURCE"),
                        targets: techData.filter((t: any) => t.role === "TARGET")
                    };
                    setAvailableTech(mappedData);
                }

                // 2. Fetch Project Details to get current settings
                const projectRes = await fetch(`${API_BASE_URL}/projects/${id}`);
                if (projectRes.ok) {
                    const pData = await projectRes.json();
                    setProject(pData);
                    if (pData.settings) {
                        setConfig({
                            source_tech: pData.settings.source_tech || "SSIS",
                            target_tech: pData.settings.target_tech || "Databricks"
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
            const res = await fetch(`${API_BASE_URL}/projects/${id}/settings`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config)
            });

            if (res.ok) {
                alert("Configuración guardada correctamente.");
            } else {
                alert("Error al guardar la configuración.");
            }
        } catch (error) {
            console.error(error);
            alert("Error de conexión.");
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
                        <h1 className="text-2xl font-bold">Configuración de Solución</h1>
                        <p className="text-gray-500 text-sm">Define las tecnologías y estándares de diseño.</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-200 dark:border-gray-800 mb-8 overflow-x-auto whitespace-nowrap scrollbar-hide">
                    <button
                        onClick={() => setActiveTab("general")}
                        className={`px-6 py-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${activeTab === "general" ? "border-primary text-primary bg-primary/5" : "border-transparent text-gray-500 hover:text-gray-700"}`}
                    >
                        <Settings size={16} /> Configuración General
                    </button>
                    <button
                        onClick={() => setActiveTab("standards")}
                        className={`px-6 py-3 text-sm font-bold flex items-center gap-2 border-b-2 transition-all ${activeTab === "standards" ? "border-primary text-primary bg-primary/5" : "border-transparent text-gray-500 hover:text-gray-700"}`}
                    >
                        <ShieldCheck size={16} /> Estándares de Diseño
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
                        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm p-6 space-y-6 animate-in fade-in duration-300">
                            {/* Source Tech */}
                            <div>
                                <label className="block text-sm font-medium mb-2">Tecnología de Origen (Legacy)</label>
                                <select
                                    value={config.source_tech}
                                    onChange={(e) => setConfig({ ...config, source_tech: e.target.value })}
                                    className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary outline-none"
                                >
                                    {availableTech.sources?.map((t: any) => (
                                        <option key={t.tech_id} value={t.tech_id}>{t.label}</option>
                                    )) || <option value="SSIS">SQL Server Integration Services (SSIS)</option>}
                                </select>
                                <p className="text-xs text-gray-400 mt-1">El formato de los paquetes que subirás.</p>
                            </div>

                            {/* Target Tech */}
                            <div>
                                <label className="block text-sm font-medium mb-2">Tecnología de Destino (Lakehouse)</label>
                                <select
                                    value={config.target_tech}
                                    onChange={(e) => setConfig({ ...config, target_tech: e.target.value })}
                                    className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary outline-none"
                                >
                                    {availableTech.targets?.map((t: any) => (
                                        <option key={t.tech_id} value={t.tech_id}>{t.label}</option>
                                    )) || <option value="Databricks">Databricks (PySpark)</option>}
                                </select>
                                <p className="text-xs text-gray-400 mt-1">La plataforma donde se ejecutará el código modernizado.</p>
                            </div>

                            <div className="pt-4 border-t border-gray-100 dark:border-gray-800 flex justify-end">
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="bg-primary text-white px-6 py-2 rounded-lg font-bold hover:bg-secondary transition-all flex items-center gap-2 shadow-lg shadow-primary/20 disabled:opacity-50"
                                >
                                    {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                                    Guardar Cambios
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
                            <PromptsExplorer />
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
