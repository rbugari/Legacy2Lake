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
                    <div key={cart.id} className={`border rounded-2xl p-6 transition-all bg-white dark:bg-white/5 border-gray-100 dark:border-white/5 shadow-sm hover:shadow-xl hover:shadow-cyan-500/5 ${isActive ? 'ring-1 ring-cyan-500/10' : 'opacity-80'}`}>
                        <div className="flex justify-between items-start mb-6">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-xl transition-colors ${isActive ? 'bg-cyan-500/10 text-cyan-600' : 'bg-gray-100 dark:bg-black/20 text-gray-400'}`}>
                                    {type === "origin" ? <Database size={22} /> : <Server size={22} />}
                                </div>
                                <div className="space-y-0.5">
                                    <h3 className="text-sm font-black uppercase tracking-widest">{cart.name}</h3>
                                    <p className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-[0.2em]">
                                        {cart.version ? `Version ${cart.version}` : cart.type}
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => onToggle(cart.id, isActive ? 'disabled' : 'active')}
                                    className={`px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5 transition-all outline-none ${isActive
                                        ? "bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500 hover:text-white"
                                        : "bg-gray-100 dark:bg-black/20 text-gray-500 hover:bg-cyan-500 hover:text-white"
                                        }`}
                                    title={isActive ? "Deactivate Cartridge" : "Activate Cartridge"}
                                >
                                    {isActive ? <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> ONLINE</div> : <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-gray-400" /> OFFLINE</div>}
                                </button>
                                <button
                                    onClick={() => onDelete(cart.id)}
                                    className="p-2 rounded-xl text-gray-400 hover:text-red-500 hover:bg-red-500/10 transition-all active:scale-90"
                                    title="Delete Cartridge"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <div className="bg-gray-50 dark:bg-black/20 rounded-2xl p-5 text-xs font-mono text-[var(--text-tertiary)] border border-gray-100 dark:border-white/5 relative group/code overflow-hidden">
                            <div className="flex justify-between items-center mb-3 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400">
                                <span className="flex items-center gap-2"><Settings size={12} className="text-cyan-500" /> Runtime Engine</span>
                                {!isEditing && (
                                    <button
                                        onClick={() => startEditing(cart)}
                                        className="text-cyan-500 hover:text-cyan-400 transition-colors opacity-0 group-hover/code:opacity-100 flex items-center gap-1"
                                        title="Modify Configuration"
                                    >
                                        <Edit2 size={12} /> EDIT
                                    </button>
                                )}
                            </div>

                            {isEditing ? (
                                <div className="mt-2">
                                    <textarea
                                        value={editConfig}
                                        onChange={(e) => setEditConfig(e.target.value)}
                                        className={`w-full h-40 bg-gray-50 dark:bg-black/20 border ${jsonError ? 'border-red-500' : 'border-gray-200 dark:border-white/5'} rounded-xl p-4 text-[var(--text-primary)] outline-none focus:ring-2 focus:ring-cyan-500/30 font-mono text-xs transition-all`}
                                    />
                                    {jsonError && <p className="text-red-500 text-[10px] font-bold mt-2 uppercase tracking-widest pl-2">{jsonError}</p>}
                                    <div className="flex gap-2 mt-4 justify-end">
                                        <button
                                            onClick={() => setEditingId(null)}
                                            className="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border border-gray-200 dark:border-white/5 hover:bg-gray-100 dark:hover:bg-white/5 transition-all"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            className="px-5 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest bg-cyan-600 text-white hover:bg-cyan-500 transition-all flex items-center gap-2 shadow-lg shadow-cyan-600/10"
                                        >
                                            <Save size={12} /> Save Config
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
