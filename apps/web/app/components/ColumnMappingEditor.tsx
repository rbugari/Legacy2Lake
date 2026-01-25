"use client";
import { useState, useEffect } from "react";
import { Save, Trash2, Sparkles, Shield, AlertCircle } from "lucide-react";
import { API_BASE_URL } from "../lib/config";

interface ColumnMapping {
    id?: string;
    source_column: string;
    source_datatype?: string;
    target_column?: string;
    target_datatype?: string;
    transformation_rule?: string;
    is_pii: boolean;
    is_nullable: boolean;
    default_value?: string;
    logic?: string;
}

interface ColumnMappingEditorProps {
    assetId: string;
    onSave?: () => void;
}

const TRANSFORMATION_OPTIONS = [
    { value: "", label: "None" },
    { value: "CAST", label: "Cast Type" },
    { value: "TRIM", label: "Trim Whitespace" },
    { value: "COALESCE", label: "Coalesce NULL" },
    { value: "UPPER", label: "Uppercase" },
    { value: "LOWER", label: "Lowercase" },
    { value: "CUSTOM", label: "Custom SQL" }
];

export default function ColumnMappingEditor({ assetId, onSave }: ColumnMappingEditorProps) {
    const [mappings, setMappings] = useState<ColumnMapping[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [editingRow, setEditingRow] = useState<number | null>(null);

    useEffect(() => {
        fetchMappings();
    }, [assetId]);

    const fetchMappings = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/assets/${assetId}/column-mappings`);
            const data = await res.json();
            setMappings(data.mappings || []);
        } catch (e) {
            console.error("Failed to load mappings", e);
        } finally {
            setLoading(false);
        }
    };

    const handleAddRow = () => {
        setMappings([...mappings, {
            source_column: "",
            source_datatype: "",
            target_column: "",
            target_datatype: "",
            transformation_rule: "",
            is_pii: false,
            is_nullable: true,
            default_value: ""
        }]);
        setEditingRow(mappings.length);
    };

    const handleUpdateRow = (index: number, field: keyof ColumnMapping, value: any) => {
        const updated = [...mappings];
        updated[index] = { ...updated[index], [field]: value };
        setMappings(updated);
    };

    const handleDeleteRow = async (index: number) => {
        const mapping = mappings[index];
        if (mapping.id) {
            try {
                await fetch(`${API_BASE_URL}/assets/${assetId}/column-mappings/${mapping.source_column}`, {
                    method: "DELETE"
                });
            } catch (e) {
                console.error("Failed to delete mapping", e);
            }
        }
        setMappings(mappings.filter((_, i) => i !== index));
    };

    const handleAutoSuggest = async (index: number) => {
        const mapping = mappings[index];
        if (!mapping.source_column || !mapping.source_datatype) return;

        try {
            const res = await fetch(`${API_BASE_URL}/assets/${assetId}/column-mappings/suggest`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    source_column: mapping.source_column,
                    source_datatype: mapping.source_datatype
                })
            });
            const suggestion = await res.json();

            handleUpdateRow(index, "target_column", suggestion.target_column);
            handleUpdateRow(index, "target_datatype", suggestion.target_datatype);
            handleUpdateRow(index, "is_pii", suggestion.is_pii);
            handleUpdateRow(index, "transformation_rule", suggestion.transformation_rule);
        } catch (e) {
            console.error("Failed to get suggestion", e);
        }
    };

    const handleSaveAll = async () => {
        setSaving(true);
        try {
            await fetch(`${API_BASE_URL}/assets/${assetId}/column-mappings/bulk`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(mappings.filter(m => m.source_column))
            });
            onSave?.();
            fetchMappings();
        } catch (e) {
            console.error("Failed to save mappings", e);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return <div className="text-center p-10 text-[var(--text-secondary)]">Loading column mappings...</div>;
    }

    return (
        <div className="flex flex-col gap-4 h-full">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-bold">Column Mapping</h3>
                    <p className="text-sm text-[var(--text-tertiary)]">
                        Map source columns to target schema with transformations
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleAddRow}
                        className="btn-secondary px-4 py-2 text-sm"
                    >
                        + Add Column
                    </button>
                    <button
                        onClick={handleSaveAll}
                        disabled={saving}
                        className="btn-primary px-4 py-2 text-sm flex items-center gap-2 disabled:opacity-50"
                    >
                        <Save size={16} />
                        {saving ? "Saving..." : "Save All"}
                    </button>
                </div>
            </div>

            {/* Grid */}
            <div className="flex-1 overflow-auto border border-[var(--border)] rounded-lg">
                <table className="w-full text-sm">
                    <thead className="bg-[var(--surface-elevated)] sticky top-0 z-10">
                        <tr className="border-b border-[var(--border)]">
                            <th className="px-3 py-2 text-left font-semibold">Source Column</th>
                            <th className="px-3 py-2 text-left font-semibold">Source Type</th>
                            <th className="px-3 py-2 text-left font-semibold">Target Column</th>
                            <th className="px-3 py-2 text-left font-semibold">Target Type</th>
                            <th className="px-3 py-2 text-left font-semibold">Transform</th>
                            <th className="px-3 py-2 text-left font-semibold">Logic</th>
                            <th className="px-3 py-2 text-center font-semibold">PII</th>
                            <th className="px-3 py-2 text-center font-semibold">Nullable</th>
                            <th className="px-3 py-2 text-center font-semibold w-24">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {mappings.length === 0 ? (
                            <tr>
                                <td colSpan={8} className="text-center py-10 text-[var(--text-tertiary)]">
                                    No column mappings yet. Click "Add Column" to start.
                                </td>
                            </tr>
                        ) : (
                            mappings.map((mapping, index) => (
                                <tr
                                    key={index}
                                    className="border-b border-[var(--border)] hover:bg-[var(--surface-elevated)] transition-colors"
                                >
                                    <td className="px-3 py-2">
                                        <input
                                            type="text"
                                            value={mapping.source_column}
                                            onChange={(e) => handleUpdateRow(index, "source_column", e.target.value)}
                                            className="input-antigravity text-sm py-1"
                                            placeholder="column_name"
                                        />
                                    </td>
                                    <td className="px-3 py-2">
                                        <input
                                            type="text"
                                            value={mapping.source_datatype || ""}
                                            onChange={(e) => handleUpdateRow(index, "source_datatype", e.target.value)}
                                            className="input-antigravity text-sm py-1"
                                            placeholder="VARCHAR"
                                        />
                                    </td>
                                    <td className="px-3 py-2">
                                        <input
                                            type="text"
                                            value={mapping.target_column || ""}
                                            onChange={(e) => handleUpdateRow(index, "target_column", e.target.value)}
                                            className="input-antigravity text-sm py-1"
                                            placeholder="target_name"
                                        />
                                    </td>
                                    <td className="px-3 py-2">
                                        <input
                                            type="text"
                                            value={mapping.target_datatype || ""}
                                            onChange={(e) => handleUpdateRow(index, "target_datatype", e.target.value)}
                                            className="input-antigravity text-sm py-1"
                                            placeholder="STRING"
                                        />
                                    </td>
                                    <td className="px-3 py-2">
                                        <select
                                            value={mapping.transformation_rule || ""}
                                            onChange={(e) => handleUpdateRow(index, "transformation_rule", e.target.value)}
                                            className="input-antigravity text-sm py-1"
                                        >
                                            {TRANSFORMATION_OPTIONS.map(opt => (
                                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                                            ))}
                                        </select>
                                    </td>
                                    <td className="px-3 py-2">
                                        <input
                                            type="text"
                                            value={mapping.logic || ""}
                                            onChange={(e) => handleUpdateRow(index, "logic", e.target.value)}
                                            className="input-antigravity text-sm py-1 font-mono text-cyan-500"
                                            placeholder="Expression"
                                        />
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                        <input
                                            type="checkbox"
                                            checked={mapping.is_pii}
                                            onChange={(e) => handleUpdateRow(index, "is_pii", e.target.checked)}
                                            className="w-4 h-4 accent-[var(--accent)]"
                                        />
                                        {mapping.is_pii && <Shield size={14} className="inline ml-1 text-red-500" />}
                                    </td>
                                    <td className="px-3 py-2 text-center">
                                        <input
                                            type="checkbox"
                                            checked={mapping.is_nullable}
                                            onChange={(e) => handleUpdateRow(index, "is_nullable", e.target.checked)}
                                            className="w-4 h-4 accent-[var(--accent)]"
                                        />
                                    </td>
                                    <td className="px-3 py-2">
                                        <div className="flex items-center justify-center gap-1">
                                            <button
                                                onClick={() => handleAutoSuggest(index)}
                                                className="p-1.5 rounded hover:bg-[var(--accent)]/10 transition-colors"
                                                title="Auto-suggest mapping"
                                            >
                                                <Sparkles size={16} className="text-[var(--accent)]" />
                                            </button>
                                            <button
                                                onClick={() => handleDeleteRow(index)}
                                                className="p-1.5 rounded hover:bg-red-500/10 transition-colors"
                                                title="Delete mapping"
                                            >
                                                <Trash2 size={16} className="text-red-500" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* PII Warning */}
            {mappings.some(m => m.is_pii) && (
                <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <AlertCircle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                        <p className="font-semibold text-red-500">PII Columns Detected</p>
                        <p className="text-[var(--text-secondary)]">
                            {mappings.filter(m => m.is_pii).length} column(s) contain personally identifiable information.
                            Ensure proper data masking is applied in transformations.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
