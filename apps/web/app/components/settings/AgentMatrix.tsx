"use client";

import { useState, useEffect } from "react";
import { fetchWithAuth } from "../../lib/auth-client";
import { Bot, Save, RefreshCw, ChevronDown, Check } from "lucide-react";

interface MatrixEntry {
    agent: string;
    provider: string;
    model: string;
}

interface Model {
    id: string;
    provider: string;
    label: string;
}

export default function AgentMatrix() {
    const [matrix, setMatrix] = useState<MatrixEntry[]>([]);
    const [catalog, setCatalog] = useState<Model[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    // Quick Assign State
    const [batchProvider, setBatchProvider] = useState("");
    const [batchModel, setBatchModel] = useState("");

    const fetchData = () => {
        Promise.all([
            fetchWithAuth("matrix").then(res => res.json()),
            fetchWithAuth("catalog").then(res => res.json())
        ]).then(([matrixData, catalogData]) => {
            setMatrix(matrixData.matrix || []);
            const mappedCatalog = (catalogData.catalog || []).map((m: any) => ({
                id: m.model_id,
                provider: m.provider,
                label: m.label
            }));
            setCatalog(mappedCatalog);

            // Set default batch values if available
            if (mappedCatalog.length > 0) {
                setBatchProvider(mappedCatalog[0].provider);
                setBatchModel(mappedCatalog[0].id);
            }

            setLoading(false);
        });
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleChange = (index: number, field: string, value: string) => {
        const newMatrix = [...matrix];
        (newMatrix[index] as any)[field] = value;

        if (field === 'provider') {
            const validModels = catalog.filter(m => m.provider === value);
            newMatrix[index].model = validModels.length > 0 ? validModels[0].id : "";
        }

        setMatrix(newMatrix);
    };

    const handleApplyAll = () => {
        if (!batchModel) return;
        const newMatrix = matrix.map(entry => ({
            ...entry,
            provider: batchProvider,
            model: batchModel
        }));
        setMatrix(newMatrix);
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const updates = matrix.map(entry =>
                fetchWithAuth("matrix", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(entry)
                })
            );
            await Promise.all(updates);
        } catch (e) {
            console.error("Failed to save matrix", e);
            alert("No se pudo guardar la configuración");
        } finally {
            setSaving(false);
        }
    };

    // Derived providers from catalog
    const availableProviders = Array.from(new Set(catalog.map(m => m.provider)));

    if (loading) return <div className="p-4 text-center text-[var(--text-secondary)]">Cargando Matriz de IA...</div>;

    return (
        <div className="space-y-6">

            {/* Quick Assign Toolbar */}
            <div className="bg-[var(--surface)] border border-blue-100 dark:border-blue-900/30 p-4 rounded-xl flex flex-wrap items-center gap-4 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-bold text-blue-600 dark:text-blue-400">
                    <Zap size={16} /> Assignar a Todos:
                </div>

                <select
                    value={batchProvider}
                    onChange={(e) => {
                        setBatchProvider(e.target.value);
                        const first = catalog.find(m => m.provider === e.target.value);
                        if (first) setBatchModel(first.id);
                    }}
                    className="bg-white dark:bg-slate-900 border border-[var(--border)] rounded-lg px-3 py-1.5 text-sm outline-none focus:border-blue-500"
                >
                    {availableProviders.map(p => (
                        <option key={p} value={p}>{p.toUpperCase()}</option>
                    ))}
                </select>

                <select
                    value={batchModel}
                    onChange={(e) => setBatchModel(e.target.value)}
                    className="bg-white dark:bg-slate-900 border border-[var(--border)] rounded-lg px-3 py-1.5 text-sm outline-none focus:border-blue-500 min-w-[150px]"
                >
                    {catalog.filter(m => m.provider === batchProvider).map(m => (
                        <option key={m.id} value={m.id}>{m.label}</option>
                    ))}
                </select>

                <button
                    onClick={handleApplyAll}
                    disabled={!batchModel}
                    className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                    Aplicar a Todos
                </button>
            </div>

            <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-sm">
                    <thead className="bg-[var(--background)] border-b border-[var(--border)] text-left">
                        <tr>
                            <th className="p-4 font-bold text-[var(--text-secondary)] uppercase tracking-wider text-[10px]">Agente / Rol</th>
                            <th className="p-4 font-bold text-[var(--text-secondary)] uppercase tracking-wider text-[10px]">Proveedor</th>
                            <th className="p-4 font-bold text-[var(--text-secondary)] uppercase tracking-wider text-[10px]">Modelo Asignado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {matrix.map((entry, i) => (
                            <tr key={i} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--background)]/30 transition-colors">
                                <td className="p-4 font-medium flex items-center gap-3">
                                    <div className="p-2 bg-[var(--color-primary)]/10 text-[var(--color-primary)] rounded-lg">
                                        <Bot size={18} />
                                    </div>
                                    <span className="font-semibold">{entry.agent}</span>
                                </td>
                                <td className="p-4">
                                    <select
                                        value={entry.provider}
                                        onChange={(e) => handleChange(i, 'provider', e.target.value)}
                                        className="bg-white dark:bg-slate-900 border border-[var(--border)] rounded-lg px-3 py-1.5 text-sm outline-none focus:border-[var(--color-primary)]"
                                    >
                                        {availableProviders.map(p => (
                                            <option key={p} value={p}>{p.toUpperCase()}</option>
                                        ))}
                                    </select>
                                </td>
                                <td className="p-4">
                                    <select
                                        value={entry.model}
                                        onChange={(e) => handleChange(i, 'model', e.target.value)}
                                        className="bg-white dark:bg-slate-900 border border-[var(--border)] rounded-lg px-3 py-1.5 text-sm outline-none focus:border-[var(--color-primary)] w-full max-w-[250px]"
                                    >
                                        {catalog.filter(m => m.provider === entry.provider).map(m => (
                                            <option key={m.id} value={m.id}>{m.label}</option>
                                        ))}
                                    </select>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="flex justify-end gap-3">
                <button
                    onClick={fetchData}
                    className="px-4 py-2 border border-[var(--border)] rounded-xl text-sm font-medium hover:bg-[var(--background)] transition-colors flex items-center gap-2"
                >
                    <RefreshCw size={16} /> Descartar Cambios
                </button>
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="bg-[var(--color-primary)] text-white px-6 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:opacity-90 shadow-lg shadow-[var(--color-primary)]/20 transition-all disabled:opacity-50"
                >
                    {saving ? <RefreshCw className="animate-spin w-4 h-4" /> : <Save className="w-4 h-4" />}
                    Guardar Configuración
                </button>
            </div>
        </div>
    );
}

const Zap = ({ size }: { size: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></svg>
);
