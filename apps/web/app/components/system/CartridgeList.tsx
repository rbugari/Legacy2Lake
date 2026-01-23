"use client";

import { CheckCircle, XCircle, Database, Server, Settings, Trash2, Edit2, Save, X } from "lucide-react";
import { useState } from "react";

interface Cartridge {
    id: string;
    name: string;
    version?: string;
    type?: string;
    status: string;
    config: any;
}

interface CartridgeListProps {
    items: Cartridge[];
    type: "origin" | "destination";
    onToggle: (id: string, status: string) => void;
    onUpdateConfig: (id: string, config: any) => void;
    onDelete: (id: string) => void;
}

export default function CartridgeList({ items, type, onToggle, onUpdateConfig, onDelete }: CartridgeListProps) {
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editConfig, setEditConfig] = useState("");
    const [jsonError, setJsonError] = useState<string | null>(null);

    const startEditing = (cart: Cartridge) => {
        setEditingId(cart.id);
        setEditConfig(JSON.stringify(cart.config, null, 2));
        setJsonError(null);
    };

    const handleSave = () => {
        if (!editingId) return;
        try {
            const parsed = JSON.parse(editConfig);
            onUpdateConfig(editingId, parsed);
            setEditingId(null);
            setJsonError(null);
        } catch (e) {
            setJsonError("Invalid JSON Format");
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {items.map(cart => {
                const isActive = cart.status === "active";
                const isEditing = editingId === cart.id;

                return (
                    <div key={cart.id} className={`border rounded-xl p-4 transition-all bg-[var(--surface)] ${isActive ? 'border-green-900/30' : 'border-[var(--border)] opacity-80'}`}>
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${isActive ? 'bg-green-100 dark:bg-green-900/20 text-green-600' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
                                    {type === "origin" ? <Database size={20} /> : <Server size={20} />}
                                </div>
                                <div>
                                    <h3 className="font-semibold">{cart.name}</h3>
                                    <p className="text-xs text-[var(--text-secondary)]">
                                        {cart.version ? `v${cart.version}` : cart.type}
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => onToggle(cart.id, isActive ? 'disabled' : 'active')}
                                    className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 transition-colors ${isActive
                                            ? "bg-green-100 dark:bg-green-900/20 text-green-600 hover:bg-yellow-100 hover:text-yellow-600"
                                            : "bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-green-100 hover:text-green-600"
                                        }`}
                                    title={isActive ? "Click to Disable" : "Click to Activate"}
                                >
                                    {isActive ? <><CheckCircle size={12} /> Active</> : <><XCircle size={12} /> Disabled</>}
                                </button>
                                <button
                                    onClick={() => onDelete(cart.id)}
                                    className="p-1 rounded text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                    title="Delete Cartridge"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <div className="bg-[var(--background)] rounded p-3 text-xs font-mono text-[var(--text-secondary)] border border-[var(--border)] relative group">
                            <div className="flex justify-between items-center mb-1 text-[var(--text-primary)] font-bold uppercase tracking-wider text-[10px]">
                                <span>Configuration</span>
                                {!isEditing && (
                                    <button
                                        onClick={() => startEditing(cart)}
                                        className="text-[var(--text-secondary)] hover:text-[var(--color-primary)] transition-colors opacity-0 group-hover:opacity-100"
                                        title="Edit Configuration"
                                    >
                                        <Edit2 size={12} />
                                    </button>
                                )}
                            </div>

                            {isEditing ? (
                                <div className="mt-2">
                                    <textarea
                                        value={editConfig}
                                        onChange={(e) => setEditConfig(e.target.value)}
                                        className={`w-full h-32 bg-[var(--input-background)] border ${jsonError ? 'border-red-500' : 'border-[var(--border)]'} rounded p-2 text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)] font-mono text-xs`}
                                    />
                                    {jsonError && <p className="text-red-500 text-[10px] mt-1">{jsonError}</p>}
                                    <div className="flex gap-2 mt-2 justify-end">
                                        <button
                                            onClick={() => setEditingId(null)}
                                            className="px-3 py-1 rounded text-xs border border-[var(--border)] hover:bg-[var(--surface-hover)]"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            className="px-3 py-1 rounded text-xs bg-[var(--color-primary)] text-white hover:opacity-90 flex items-center gap-1"
                                        >
                                            <Save size={12} /> Save
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <pre className="whitespace-pre-wrap overflow-x-auto cursor-text text-[var(--text-primary)]" onClick={() => startEditing(cart)}>
                                    {JSON.stringify(cart.config, null, 2)}
                                </pre>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
