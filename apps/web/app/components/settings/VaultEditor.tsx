
"use client";

import { useState, useEffect } from "react";
import { fetchWithAuth } from "../../lib/auth-client";
import { CheckCircle, XCircle, Key, Save, Loader2 } from "lucide-react";

interface Credential {
    provider_name: string;
    is_active: boolean;
    base_url?: string;
}

export default function VaultEditor() {
    const [credentials, setCredentials] = useState<Credential[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingProvider, setEditingProvider] = useState<string | null>(null);

    // Form State
    const [apiKey, setApiKey] = useState("");
    const [baseUrl, setBaseUrl] = useState("");
    const [newProviderName, setNewProviderName] = useState("");
    const [saving, setSaving] = useState(false);

    // Dynamic State
    const [allProviders, setAllProviders] = useState<{ id: string, label: string, description: string }[]>([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newProviderId, setNewProviderId] = useState("");
    const [newProviderLabel, setNewProviderLabel] = useState("");

    // Static defaults to ensure UI is never empty
    const DEFAULT_PROVIDERS = [
        { id: "azure", label: "AZURE OPENAI", description: "Standard Enterprise AI" },
        { id: "openai", label: "OPENAI", description: "Direct API Access" },
        { id: "deepseek", label: "DEEPSEEK", description: "High Efficiency Models" },
        { id: "ollama", label: "OLLAMA", description: "Local Inference" },
    ];

    const fetchVault = async () => {
        try {
            const res = await fetchWithAuth("system/vault");
            if (res.ok) {
                const data = await res.json();
                const creds = data.credentials || [];
                setCredentials(creds);

                // Merge configured credentials with defaults
                // Only show what is explicitly in the DB
                const providers = creds.map((c: Credential) => ({
                    id: c.provider_name,
                    label: c.provider_name.toUpperCase(),
                    description: DEFAULT_PROVIDERS.find(p => p.id === c.provider_name.toLowerCase())?.description || "Custom Provider"
                }));

                setAllProviders(providers);
            }
        } catch (err) {
            console.error("Failed to fetch vault", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVault();
    }, []);

    const handleEdit = (providerId: string) => {
        const cred = credentials.find(c => c.provider_name.toLowerCase() === providerId.toLowerCase());
        setApiKey("");
        setBaseUrl(cred?.base_url || "");
        setNewProviderName(providerId);
        setEditingProvider(providerId);
    };

    const handleSave = async () => {
        if (!editingProvider || !apiKey) return;

        setSaving(true);
        try {
            const payload = {
                provider: editingProvider,
                api_key: apiKey,
                base_url: baseUrl || undefined,
                new_provider_name: newProviderName
            };

            const res = await fetchWithAuth("system/vault/update", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                await fetchVault();
                setEditingProvider(null);
                setEditingProvider(null);
                setApiKey("");
                setNewProviderName("");
            } else {
                const err = await res.json();
                alert(err.detail || "Error saving credentials");
            }
        } catch (error) {
            console.error(error);
            alert("Connection error");
        } finally {
            setSaving(false);
        }
    };

    const handleAddCustomProvider = async () => {
        if (!newProviderId || !newProviderLabel) return;

        // Add to local list immediately so it appears card
        const newP = { id: newProviderId.toLowerCase(), label: newProviderLabel, description: "Custom Provider" };
        setAllProviders([...allProviders, newP]);

        // Open edit mode for it
        setEditingProvider(newP.id);
        setShowAddModal(false);
        setNewProviderId("");
        setNewProviderLabel("");
    };

    if (loading) return <div className="p-4"><Loader2 className="animate-spin" /> Loading Vault...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <p className="text-xs text-[var(--text-secondary)] italic">
                    * These settings are <strong>Tenant-Wide</strong> (Global). They apply to all your projects.
                </p>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="text-xs px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded hover:bg-[var(--text-primary)]/5 font-medium"
                >
                    + Add New Provider
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {allProviders.map(p => {
                    const cred = credentials.find(c => c.provider_name.toLowerCase() === p.id.toLowerCase());
                    const isActive = cred?.is_active;
                    const isEditing = editingProvider === p.id;

                    return (
                        <div key={p.id} className={`border rounded-xl p-4 transition-all ${isActive ? 'bg-[var(--surface)] border-green-900/30' : 'bg-[var(--surface)] border-[var(--border)]'}`}>
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${isActive ? 'bg-green-100 dark:bg-green-900/20 text-green-600' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
                                        <Key className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">{p.label}</h3>
                                        <p className="text-xs text-[var(--text-secondary)]">{p.description}</p>
                                    </div>
                                </div>
                                {isActive ? (
                                    <span className="flex items-center text-xs font-medium text-green-600 gap-1 bg-green-100 dark:bg-green-900/20 px-2 py-1 rounded-full">
                                        <CheckCircle className="w-3 h-3" /> Active
                                    </span>
                                ) : (
                                    <span className="flex items-center text-xs font-medium text-slate-500 gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-full">
                                        <XCircle className="w-3 h-3" /> Missing
                                    </span>
                                )}
                            </div>

                            {isEditing ? (
                                <div className="space-y-3 animate-in fade-in slide-in-from-top-2">
                                    <input
                                        type="text"
                                        placeholder="Provider Name (ID)"
                                        className="w-full text-sm p-2 rounded-md border border-[var(--border)] bg-[var(--background)] font-medium"
                                        value={newProviderName}
                                        onChange={(e) => setNewProviderName(e.target.value)}
                                    />
                                    <input
                                        type="password"
                                        placeholder="Paste API Key here..."
                                        className="w-full text-sm p-2 rounded-md border border-[var(--border)] bg-[var(--background)]"
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                    />
                                    <input
                                        type="text"
                                        placeholder="Base URL for all models (e.g. https://your-resource.openai.azure.com/)"
                                        className="w-full text-sm p-2 rounded-md border border-[var(--border)] bg-[var(--background)]"
                                        value={baseUrl}
                                        onChange={(e) => setBaseUrl(e.target.value)}
                                    />
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={() => setEditingProvider(null)}
                                            className="text-xs px-3 py-1 text-[var(--text-secondary)] hover:bg-[var(--text-primary)]/5 rounded"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            disabled={saving || !apiKey}
                                            className="text-xs px-3 py-1 bg-[var(--color-primary)] text-white rounded flex items-center gap-1 disabled:opacity-50"
                                        >
                                            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                                            Save
                                        </button>
                                        <button
                                            onClick={async () => {
                                                if (!confirm("Are you sure you want to delete these credentials?")) return;
                                                const res = await fetchWithAuth("system/vault/delete", { method: "POST", body: JSON.stringify({ provider: p.id }) });

                                                if (res.ok) {
                                                    await fetchVault();
                                                    setEditingProvider(null);
                                                } else {
                                                    const err = await res.json();
                                                    alert(err.detail || "Cannot delete provider");
                                                }
                                            }}
                                            className="text-xs px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 rounded hover:bg-red-200"
                                            title="Delete Credentials"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <button
                                    onClick={() => handleEdit(p.id)}
                                    className="w-full text-xs py-2 border border-dashed border-[var(--border)] rounded hover:bg-[var(--text-primary)]/5 text-[var(--text-secondary)] transition-colors"
                                >
                                    {isActive ? "Update Credentials" : "Add Credentials"}
                                </button>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Add Provider Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-[var(--surface)] rounded-xl p-6 w-full max-w-sm shadow-2xl border border-[var(--border)]">
                        <h3 className="text-lg font-bold mb-4">Add Provider</h3>

                        <div className="mb-4">
                            <label className="text-xs font-bold text-[var(--text-secondary)] uppercase block mb-2">Quick Add Standard</label>
                            <div className="flex flex-wrap gap-2">
                                {DEFAULT_PROVIDERS.map(dp => {
                                    // Don't show if already added
                                    const exists = allProviders.find(p => p.id.toLowerCase() === dp.id.toLowerCase());
                                    if (exists) return null;

                                    return (
                                        <button
                                            key={dp.id}
                                            onClick={() => {
                                                setNewProviderId(dp.id);
                                                setNewProviderLabel(dp.label);
                                                // Trigger add immediately? Or just fill form? Let's just fill form for clarity
                                            }}
                                            className="px-2 py-1 text-[10px] font-bold border rounded hover:bg-white/5 active:scale-95 transition-all"
                                        >
                                            {dp.label}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="space-y-4 border-t border-[var(--border)] pt-4">
                            <div>
                                <label className="text-xs font-bold text-[var(--text-secondary)] uppercase block mb-1">Provider Label</label>
                                <input
                                    className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm"
                                    placeholder="e.g. Ollama Local"
                                    value={newProviderLabel}
                                    onChange={e => setNewProviderLabel(e.target.value)}
                                />
                            </div>
                            <div>
                                <label className="text-xs font-bold text-[var(--text-secondary)] uppercase block mb-1">Internal ID</label>
                                <input
                                    className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm font-mono"
                                    placeholder="e.g. ollama"
                                    value={newProviderId}
                                    onChange={e => setNewProviderId(e.target.value)}
                                />
                            </div>
                            <div className="flex justify-end gap-2 mt-4">
                                <button onClick={() => setShowAddModal(false)} className="px-3 py-1 text-sm hover:bg-[var(--text-primary)]/5 rounded">Cancel</button>
                                <button
                                    onClick={handleAddCustomProvider}
                                    disabled={!newProviderId || !newProviderLabel}
                                    className="px-3 py-1 bg-[var(--color-primary)] text-white text-sm font-bold rounded hover:opacity-90 disabled:opacity-50"
                                >
                                    Continue
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
