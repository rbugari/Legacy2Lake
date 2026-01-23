"use client";

import { useState, useEffect } from "react";
import { fetchWithAuth } from "../../lib/auth-client";
import { Database, Zap, Plus, X, Power, Edit2, Save, RefreshCw, Check, Trash2 } from "lucide-react";

interface Model {
    id: string;
    provider: string;
    label: string;
    context_window: number;
    deployment_id?: string;
    api_version?: string;
    api_url?: string;
    is_active?: boolean;
}

export default function ModelCatalog() {
    const [models, setModels] = useState<Model[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [filter, setFilter] = useState("all");

    // Form State
    const [currentModelId, setCurrentModelId] = useState("");
    const [currentModelName, setCurrentModelName] = useState("");
    const [currentModelProvider, setCurrentModelProvider] = useState("");
    const [currentModelContext, setCurrentModelContext] = useState<string>("0");
    const [deploymentId, setDeploymentId] = useState("");
    const [apiVersion, setApiVersion] = useState("");
    const [apiUrl, setApiUrl] = useState("");

    const [availableProviders, setAvailableProviders] = useState<string[]>([]);
    const [saving, setSaving] = useState(false);

    const fetchCatalog = () => {
        Promise.all([
            fetchWithAuth("catalog").then(res => res.json()),
            fetchWithAuth("vault").then(res => res.json())
        ]).then(([catalogData, vaultData]) => {
            const mapped = (catalogData.catalog || []).map((m: any) => ({
                id: m.model_id,
                provider: m.provider,
                label: m.label,
                context_window: m.context_window,
                deployment_id: m.deployment_id,
                api_version: m.api_version,
                api_url: m.api_url,
                is_active: m.is_active
            }));
            setModels(mapped);

            const vaultProviders = (vaultData.credentials || []).map((c: any) => c.provider_name);
            const unique = Array.from(new Set([...vaultProviders, "openai", "azure", "anthropic", "groq", "deepseek", "ollama"]));
            setAvailableProviders(unique);

            setLoading(false);
        }).catch(err => console.error("Failed to fetch data", err));
    };

    useEffect(() => {
        fetchCatalog();
    }, []);

    const handleDelete = async (id: string) => {
        if (!confirm("¿Eliminar este modelo?")) return;
        try {
            await fetchWithAuth(`catalog/${id}`, { method: "DELETE" });
            fetchCatalog();
        } catch (e) {
            console.error("Failed to delete model", e);
        }
    };

    const toggleModel = async (id: string, currentState: boolean) => {
        const newState = !currentState;
        setModels(models.map(m => m.id === id ? { ...m, is_active: newState } : m));

        try {
            await fetchWithAuth(`catalog/${id}/toggle`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: newState })
            });
        } catch (e) {
            console.error("Failed to toggle model", e);
            fetchCatalog();
        }
    };

    const handleOpenAdd = () => {
        setEditMode(false);
        setCurrentModelId("");
        setCurrentModelName("");
        setCurrentModelProvider(availableProviders[0] || "azure");
        setCurrentModelContext("128000");
        setDeploymentId("");
        setApiVersion("2024-05-01-preview");
        setApiUrl("");
        setShowModal(true);
    };

    const handleOpenEdit = (model: Model) => {
        setEditMode(true);
        setCurrentModelId(model.id);
        setCurrentModelName(model.label);
        setCurrentModelProvider(model.provider);
        setCurrentModelContext(model.context_window.toString());
        setDeploymentId(model.deployment_id || "");
        setApiVersion(model.api_version || "");
        setApiUrl(model.api_url || "");
        setShowModal(true);
    };

    const handleSubmit = async () => {
        setSaving(true);
        const payload = {
            id: currentModelId,
            name: currentModelName,
            provider: currentModelProvider,
            context: parseInt(currentModelContext) || 0,
            deployment_id: deploymentId,
            api_version: apiVersion,
            api_url: apiUrl
        };

        try {
            const endpoint = editMode ? `catalog/${currentModelId}/update` : "catalog";
            await fetchWithAuth(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            fetchCatalog();
            setShowModal(false);
        } catch (e) {
            alert("Failed to save model. Make sure ID is unique.");
        } finally {
            setSaving(false);
        }
    };

    const filteredModels = models.filter(m => filter === "all" || m.provider.toLowerCase() === filter.toLowerCase());

    if (loading) return <div className="p-4 text-center text-[var(--text-secondary)]">Cargando Catálogo...</div>;

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={() => setFilter("all")}
                        className={`px-3 py-1 rounded-full text-xs font-bold border transition-all ${filter === "all" ? "bg-[var(--color-primary)] text-white border-[var(--color-primary)]" : "bg-[var(--surface)] border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--color-primary)]/50"}`}
                    >
                        TODOS
                    </button>
                    {availableProviders.map(p => (
                        <button
                            key={p}
                            onClick={() => setFilter(p)}
                            className={`px-3 py-1 rounded-full text-xs font-bold border transition-all uppercase ${filter === p ? "bg-slate-700 text-white border-slate-700" : "bg-[var(--surface)] border-[var(--border)] text-[var(--text-secondary)] hover:border-slate-400"}`}
                        >
                            {p}
                        </button>
                    ))}
                </div>
                <button
                    onClick={handleOpenAdd}
                    className="flex items-center gap-2 bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--text-primary)]/5 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                    <Plus size={16} /> Cargar Nuevo Modelo
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredModels.map(model => (
                    <div key={model.id} className={`bg-[var(--surface)] border rounded-xl p-4 transition-all group ${model.is_active !== false ? 'border-[var(--border)]' : 'border-red-200 dark:border-red-900/30 opacity-60'}`}>
                        <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-bold px-2 py-0.5 rounded bg-[var(--text-primary)]/5 text-[var(--text-secondary)] uppercase">
                                {model.provider}
                            </span>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleOpenEdit(model)}
                                    className="p-1 rounded text-slate-400 hover:text-blue-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors opacity-0 group-hover:opacity-100"
                                    title="Edit Model"
                                >
                                    <Edit2 size={14} />
                                </button>
                                <button
                                    onClick={() => handleDelete(model.id)}
                                    className="p-1 rounded text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors opacity-0 group-hover:opacity-100"
                                    title="Borrar Modelo"
                                >
                                    <Trash2 size={14} />
                                </button>
                                <button
                                    onClick={() => toggleModel(model.id, model.is_active !== false)}
                                    className={`h-6 w-6 rounded-full flex items-center justify-center transition-colors ${model.is_active !== false
                                        ? "bg-green-100 dark:bg-green-900/20 text-green-600 hover:bg-red-100 hover:text-red-600"
                                        : "bg-red-100 dark:bg-red-900/20 text-red-600 hover:bg-green-100 hover:text-green-600"
                                        }`}
                                    title={model.is_active !== false ? "Click to Deactivate" : "Click to Activate"}
                                >
                                    <Power size={12} />
                                </button>
                            </div>
                        </div>
                        <h3 className="font-bold text-lg">{model.label}</h3>
                        <p className="text-xs font-mono text-[var(--text-secondary)] mb-3">{model.id}</p>

                        <div className="space-y-1 mt-auto">
                            <div className="flex items-center gap-4 text-xs text-[var(--text-secondary)]">
                                <span className="flex items-center gap-1"><Database size={12} /> {(model.context_window / 1000).toFixed(0)}k context</span>
                            </div>
                            {model.deployment_id && (
                                <p className="text-[10px] text-[var(--text-secondary)] font-mono truncate">Deploy: {model.deployment_id}</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Combined Add/Edit Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
                    <div className="bg-[var(--surface)] rounded-xl p-6 w-full max-w-md shadow-2xl border border-[var(--border)] overflow-y-auto max-h-[90vh]">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-lg font-bold">{editMode ? "Actualizar Modelo" : "Cargar Nuevo Modelo"}</h3>
                            <button onClick={() => setShowModal(false)} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs font-bold text-[var(--text-secondary)] uppercase block mb-1">Proveedor</label>
                                    <select
                                        className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:border-[var(--color-primary)]"
                                        value={currentModelProvider}
                                        onChange={e => setCurrentModelProvider(e.target.value)}
                                    >
                                        {availableProviders.map(p => (
                                            <option key={p} value={p}>{p.toUpperCase()}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-[var(--text-secondary)] uppercase block mb-1">Nombre del Modelo</label>
                                    <input
                                        className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm"
                                        placeholder="e.g. GPT-4o (Prod)"
                                        value={currentModelName}
                                        onChange={e => setCurrentModelName(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-bold text-[var(--text-secondary)] uppercase block mb-1">Model ID (API String)</label>
                                <input
                                    className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm font-mono disabled:opacity-50"
                                    placeholder="e.g. gpt-4o"
                                    value={currentModelId}
                                    disabled={editMode}
                                    onChange={e => setCurrentModelId(e.target.value)}
                                />
                            </div>

                            <div className="border-t border-[var(--border)] pt-4 mt-4">
                                <h4 className="text-[10px] font-black text-[var(--text-secondary)] uppercase mb-3 tracking-widest">Configuración Técnica</h4>
                                <div className="space-y-3">
                                    {currentModelProvider.toLowerCase() === "azure" && (
                                        <>
                                            <div>
                                                <label className="text-[10px] font-bold text-[var(--text-secondary)] uppercase block mb-1">Deployment ID</label>
                                                <input
                                                    className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-xs font-mono"
                                                    placeholder="gpt-4"
                                                    value={deploymentId}
                                                    onChange={e => setDeploymentId(e.target.value)}
                                                />
                                            </div>
                                            <div>
                                                <label className="text-[10px] font-bold text-[var(--text-secondary)] uppercase block mb-1">API Version</label>
                                                <input
                                                    className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-xs font-mono"
                                                    placeholder="2024-05-01-preview"
                                                    value={apiVersion}
                                                    onChange={e => setApiVersion(e.target.value)}
                                                />
                                            </div>
                                        </>
                                    )}
                                    <div>
                                        <label className="text-[10px] font-bold text-[var(--text-secondary)] uppercase block mb-1">Endpoint URL (Opcional)</label>
                                        <input
                                            className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-xs font-mono"
                                            placeholder="https://your-resource.openai.azure.com/"
                                            value={apiUrl}
                                            onChange={e => setApiUrl(e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-bold text-[var(--text-secondary)] uppercase block mb-1">Context Window (Tokens)</label>
                                        <input
                                            type="number"
                                            className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-xs"
                                            placeholder="128000"
                                            value={currentModelContext}
                                            onChange={e => setCurrentModelContext(e.target.value)}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 mt-8">
                                <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm border border-[var(--border)] rounded-lg font-medium">Cancelar</button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={saving || !currentModelId || !currentModelName}
                                    className="px-4 py-2 bg-[var(--color-primary)] text-white text-sm font-bold rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
                                >
                                    {saving ? <RefreshCw size={16} className="animate-spin" /> : <Check size={16} />}
                                    {editMode ? "Actualizar Modelo" : "Crear Modelo"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
