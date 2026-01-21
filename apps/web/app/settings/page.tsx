"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { API_BASE_URL } from "../lib/config";
import {
    Settings,
    Database,
    Bot,
    Cpu,
    Save,
    ArrowLeft,
    CheckCircle,
    AlertCircle,
    X,
    Eye,
    EyeOff
} from "lucide-react";

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState("general");

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 font-sans">
            {/* Header */}
            <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-8 py-4 flex justify-between items-center sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <Link
                        href="/dashboard"
                        className="p-2 -ml-2 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
                        title="Volver al Dashboard"
                    >
                        <ArrowLeft size={20} />
                    </Link>
                    <div>
                        <h1 className="text-xl font-bold flex items-center gap-2">
                            <Settings className="text-primary" size={24} />
                            Platform Configuration
                        </h1>
                        <p className="text-xs text-gray-500">Manage global settings for all projects (Admin Area)</p>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto p-8 flex gap-8 items-start">
                {/* Sidebar Navigation */}
                <nav className="w-64 flex-shrink-0 space-y-1">
                    <NavButton
                        id="general"
                        label="General"
                        icon={<Settings size={18} />}
                        active={activeTab === "general"}
                        onClick={() => setActiveTab("general")}
                    />
                    <NavButton
                        id="cartridges"
                        label="Cartridges"
                        icon={<Database size={18} />}
                        active={activeTab === "cartridges"}
                        onClick={() => setActiveTab("cartridges")}
                    />
                    <NavButton
                        id="agents"
                        label="Prompt Studio"
                        icon={<Bot size={18} />}
                        active={activeTab === "agents"}
                        onClick={() => setActiveTab("agents")}
                    />
                    <NavButton
                        id="providers"
                        label="LLM Providers"
                        icon={<Cpu size={18} />}
                        active={activeTab === "providers"}
                        onClick={() => setActiveTab("providers")}
                    />
                </nav>

                {/* Content Area */}
                <main className="flex-1 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm min-h-[600px] p-8 relative">
                    {activeTab === "general" && <GeneralSettings />}
                    {activeTab === "cartridges" && <CartridgeManager />}
                    {activeTab === "agents" && <PromptStudio />}
                    {activeTab === "providers" && <ProviderSettings />}
                </main>
            </div>
        </div>
    );
}

function NavButton({ id, label, icon, active, onClick }: any) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${active
                ? "bg-primary text-white shadow-lg shadow-primary/20"
                : "text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
                }`}
        >
            {icon}
            {label}
        </button>
    );
}

// --- Sub-Components ---

function GeneralSettings() {
    return (
        <div>
            <h2 className="text-2xl font-bold mb-6">General Settings</h2>
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/10 text-yellow-800 dark:text-yellow-200 rounded-lg border border-yellow-200 dark:border-yellow-900/30 text-sm mb-6 flex gap-2">
                <AlertCircle size={16} className="mt-0.5" />
                <p>Global settings affect defaults for <strong>new projects</strong> only. Existing projects retain their configuration.</p>
            </div>

            <div className="space-y-6 max-w-lg">
                <div>
                    <label className="block text-sm font-bold mb-1 text-gray-700 dark:text-gray-300">Organization Name</label>
                    <input type="text" className="w-full border p-2 rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-white" defaultValue="My Company" />
                </div>
                <div>
                    <label className="block text-sm font-bold mb-1 text-gray-700 dark:text-gray-300">Default Cloud Region</label>
                    <select className="w-full border p-2 rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-white">
                        <option>US East (N. Virginia)</option>
                        <option>EU West (Ireland)</option>
                        <option>Asia Pacific (Tokyo)</option>
                    </select>
                </div>
                <button className="bg-black text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2">
                    <Save size={16} /> Save Changes
                </button>
            </div>
        </div>
    );
}

function CartridgeManager() {
    const [cartridges, setCartridges] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API_BASE_URL}/cartridges`)
            .then(res => res.json())
            .then(data => {
                setCartridges(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    const toggleCartridge = async (id: string, currentStatus: boolean) => {
        const newStatus = !currentStatus;
        setCartridges(prev => prev.map(c => c.id === id ? { ...c, enabled: newStatus } : c));

        try {
            await fetch(`${API_BASE_URL}/cartridges/update`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id, enabled: newStatus })
            });
        } catch (e) {
            console.error(e);
            setCartridges(prev => prev.map(c => c.id === id ? { ...c, enabled: currentStatus } : c));
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading cartridges...</div>;

    return (
        <div>
            <h2 className="text-2xl font-bold mb-2">Cartridge Manager</h2>
            <p className="text-gray-500 mb-6">Enable or disable code generation engines available to architects.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {cartridges.map(c => (
                    <CartridgeCard
                        key={c.id}
                        {...c}
                        onToggle={() => toggleCartridge(c.id, c.enabled)}
                    />
                ))}
            </div>
        </div>
    );
}

function CartridgeCard({ name, version, desc, enabled, beta, onToggle }: any) {
    return (
        <div className={`p-5 rounded-xl border transition-all ${enabled
            ? "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
            : "border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 opacity-70"
            }`}>
            <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">{name}</h3>
                <div
                    onClick={onToggle}
                    className={`w-10 h-6 rounded-full p-1 transition-colors cursor-pointer ${enabled ? "bg-green-500" : "bg-gray-300"}`}
                >
                    <div className={`w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${enabled ? "translate-x-4" : "translate-x-0"}`} />
                </div>
            </div>
            <div className="flex items-center gap-2 mb-3">
                <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-gray-600 dark:text-gray-300 font-mono">{version}</span>
                {beta && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded font-bold">BETA</span>}
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{desc}</p>
        </div>
    );
}

function PromptStudio() {
    const [activeAgent, setActiveAgent] = useState("agent-a");
    const [promptContent, setPromptContent] = useState("");
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [statusMsg, setStatusMsg] = useState("");

    const agents = [
        { id: "agent-a", name: "Agent A (Architect / Detective)" },
        { id: "agent-c", name: "Agent C (Developer / Coder)" },
        { id: "agent-f", name: "Agent F (Critic / Compliance)" },
        { id: "agent-g", name: "Agent G (Librarian / Docs)" }
    ];

    useEffect(() => {
        const fetchPrompt = async () => {
            setLoading(true);
            try {
                const res = await fetch(`${API_BASE_URL}/prompts/${activeAgent}`);
                const data = await res.json();
                if (data.prompt) setPromptContent(data.prompt);
                else setPromptContent("");
            } catch (e) {
                console.error("Error fetching prompt", e);
                setPromptContent("Error loading prompt.");
            } finally {
                setLoading(false);
            }
        };
        fetchPrompt();
    }, [activeAgent]);

    const handleSave = async () => {
        setSaving(true);
        setStatusMsg("");
        try {
            const res = await fetch(`${API_BASE_URL}/prompts/${activeAgent}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: promptContent })
            });
            const data = await res.json();
            if (data.success) {
                setStatusMsg("Saved successfully!");
                setTimeout(() => setStatusMsg(""), 3000);
            } else {
                setStatusMsg("Error saving.");
            }
        } catch (e) {
            console.error("Error saving prompt", e);
            setStatusMsg("Connection error.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="h-full flex flex-col">
            <h2 className="text-2xl font-bold mb-2">Prompt Studio</h2>
            <p className="text-gray-500 mb-6">Manage system prompts for LLM-based agents.</p>

            <div className="flex-1 flex gap-8 border-t border-gray-100 dark:border-gray-800 pt-6">
                <div className="w-1/3 xl:w-1/4 space-y-2">
                    {agents.map(agent => (
                        <div
                            key={agent.id}
                            onClick={() => setActiveAgent(agent.id)}
                            className={`p-4 rounded-lg text-sm cursor-pointer border transition-all ${activeAgent === agent.id
                                ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 font-bold shadow-sm"
                                : "hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 border-transparent hover:border-gray-200 dark:hover:border-gray-700"
                                }`}
                        >
                            {agent.name}
                        </div>
                    ))}
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg text-xs text-gray-500 italic">
                        Note: Other agents (Profiler, Refactorer, OpsAuditor) use heuristic logic and do not use editable system prompts.
                    </div>
                </div>
                <div className="flex-1 flex flex-col relative">
                    <label className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">
                        System Instructions <span className="text-gray-400 font-normal">({agents.find(a => a.id === activeAgent)?.name})</span>
                    </label>

                    {loading ? (
                        <div className="flex-1 flex items-center justify-center border border-gray-200 rounded-xl bg-gray-50">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                    ) : (
                        <textarea
                            className="flex-1 w-full border border-gray-300 dark:border-gray-700 rounded-xl p-6 font-mono text-sm leading-relaxed focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-all shadow-inner"
                            value={promptContent}
                            onChange={(e) => setPromptContent(e.target.value)}
                            spellCheck={false}
                        />
                    )}

                    <div className="flex justify-between items-center mt-4 h-10">
                        <span className={`text-sm font-bold ${statusMsg.includes("Error") ? "text-red-500" : "text-green-600"}`}>
                            {statusMsg}
                        </span>
                        <button
                            onClick={handleSave}
                            disabled={loading || saving}
                            className="bg-primary text-white px-6 py-2 rounded-lg font-bold hover:bg-secondary disabled:opacity-50 transition-all flex items-center gap-2"
                        >
                            {saving ? (
                                <>Saving...</>
                            ) : (
                                <><Save size={16} /> Update Prompt</>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function ProviderSettings() {
    const [providers, setProviders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [formData, setFormData] = useState<any>({});
    const [showKey, setShowKey] = useState(false);

    const fetchProviders = () => {
        setLoading(true);
        fetch(`${API_BASE_URL}/providers`)
            .then(res => res.json())
            .then(data => {
                setProviders(data);
                setLoading(false);
            })
            .catch(e => {
                console.error(e);
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchProviders();
    }, []);

    const handleEdit = (provider: any) => {
        setEditingId(provider.id);
        setFormData({
            id: provider.id,
            enabled: provider.enabled,
            model: provider.model,
            api_key: "", // Don't show existing key 
            endpoint: provider.endpoint || ""
        });
        setShowKey(false);
    };

    const handleSave = async () => {
        try {
            await fetch(`${API_BASE_URL}/providers/update`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData)
            });
            setEditingId(null);
            fetchProviders();
        } catch (e) {
            console.error(e);
        }
    };

    const handleCancel = () => {
        setEditingId(null);
        setFormData({});
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading providers...</div>;

    return (
        <div>
            <h2 className="text-2xl font-bold mb-4">Model Providers</h2>

            <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 text-gray-500 font-medium border-b">
                        <tr>
                            <th className="px-6 py-3">Provider</th>
                            <th className="px-6 py-3">Model ID</th>
                            <th className="px-6 py-3">Status</th>
                            <th className="px-6 py-3 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {providers.map(p => (
                            <tr key={p.id} className="hover:bg-gray-50/50">
                                <td className="px-6 py-4 font-bold text-gray-800">{p.name}</td>
                                <td className="px-6 py-4 font-mono text-xs text-gray-500">{p.model}</td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        {p.connected ? (
                                            <span className="text-green-600 flex items-center gap-1 text-xs font-bold bg-green-50 px-2 py-1 rounded-full"><CheckCircle size={12} /> Connected</span>
                                        ) : (
                                            <span className="text-gray-400 text-xs bg-gray-100 px-2 py-1 rounded-full">Not Configured</span>
                                        )}
                                        {p.enabled && <span className="text-blue-600 text-xs font-bold bg-blue-50 px-2 py-1 rounded-full">Active</span>}
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => handleEdit(p)}
                                        className="text-primary font-bold hover:underline"
                                    >
                                        {p.connected ? "Configure" : "Connect"}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Edit Modal */}
            {editingId && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6 w-[500px] border border-gray-200 dark:border-gray-700">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold">Configure {providers.find(p => p.id === editingId)?.name}</h3>
                            <button onClick={handleCancel} className="text-gray-400 hover:text-gray-900"><X size={20} /></button>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center gap-2 mb-2">
                                <label className="text-sm font-bold text-gray-700">Enable Provider</label>
                                <input
                                    type="checkbox"
                                    checked={formData.enabled}
                                    onChange={e => setFormData({ ...formData, enabled: e.target.checked })}
                                    className="w-5 h-5 text-primary rounded focus:ring-primary"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Model ID (Deployment Name)</label>
                                <input
                                    type="text"
                                    className="w-full border p-2 rounded-lg text-sm font-mono bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300"
                                    value={formData.model}
                                    onChange={e => setFormData({ ...formData, model: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">API Key</label>
                                <div className="relative">
                                    <input
                                        type={showKey ? "text" : "password"}
                                        className="w-full border p-2 rounded-lg text-sm font-mono pr-10 bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300"
                                        placeholder="Enter new API key to update..."
                                        value={formData.api_key}
                                        onChange={e => setFormData({ ...formData, api_key: e.target.value })}
                                    />
                                    <button
                                        onClick={() => setShowKey(!showKey)}
                                        className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                                    >
                                        {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                                    </button>
                                </div>
                                <p className="text-xs text-gray-400 mt-1">Leave empty to keep existing key.</p>
                            </div>

                            {editingId === "azure" && (
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Endpoint URL</label>
                                    <input
                                        type="text"
                                        className="w-full border p-2 rounded-lg text-sm font-mono bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300"
                                        placeholder="https://your-resource.openai.azure.com/"
                                        value={formData.endpoint}
                                        onChange={e => setFormData({ ...formData, endpoint: e.target.value })}
                                    />
                                </div>
                            )}
                        </div>

                        <div className="flex justify-end gap-3 mt-8 pt-4 border-t">
                            <button onClick={handleCancel} className="px-4 py-2 text-gray-600 font-bold hover:bg-gray-100 rounded-lg">Cancel</button>
                            <button onClick={handleSave} className="px-6 py-2 bg-black text-white font-bold rounded-lg hover:bg-gray-800">Save Configuration</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
