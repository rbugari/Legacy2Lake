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
    EyeOff,
    Server,
    Plus,
    Rocket,
    Code2,
    FileText,
    Pencil
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
                        label="Platform Cartridges"
                        icon={<Database size={18} />}
                        active={activeTab === "cartridges"}
                        onClick={() => setActiveTab("cartridges")}
                    />
                    <NavButton
                        id="sources"
                        label="Source Connections"
                        icon={<Server size={18} />}
                        active={activeTab === "sources"}
                        onClick={() => setActiveTab("sources")}
                    />
                    <NavButton
                        id="generators"
                        label="Target Generators"
                        icon={<Rocket size={18} />}
                        active={activeTab === "generators"}
                        onClick={() => setActiveTab("generators")}
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
                    {activeTab === "sources" && <SourceManager />}
                    {activeTab === "generators" && <DestinationManager />}
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
                            className="flex-1 w-full border border-gray-300 dark:border-gray-700 rounded-xl p-6 font-mono text-sm leading-relaxed focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-y bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-all shadow-inner min-h-[400px]"
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

function SourceManager() {
    const [sources, setSources] = useState<any[]>([]);
    const [availableTech, setAvailableTech] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // Modal Form State (Knowledge Profile)
    const [formData, setFormData] = useState({
        name: "",
        type: "", // Will default to first available
        version: "",
        description: "",
        context_prompt: ""
    });

    const fetchMetadata = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/config/technologies`);
            const data = await res.json();
            const filtered = data.filter((t: any) => t.role === "SOURCE");
            setAvailableTech(filtered);
            if (filtered.length > 0) {
                setFormData(prev => ({ ...prev, type: filtered[0].tech_id }));
            }
        } catch (e) {
            console.error("Error fetching tech metadata", e);
        }
    };

    const fetchSources = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/config/sources`);
            const data = await res.json();
            setSources(data);
        } catch (e) {
            console.error("Error fetching sources", e);
        } finally {
            setLoading(false);
        }
    };

    const handleOpenDefine = (techId?: string) => {
        setFormData({
            name: "",
            type: techId || (availableTech[0]?.tech_id || ""),
            version: "",
            description: "",
            context_prompt: ""
        });
        setShowModal(true);
    };

    useEffect(() => {
        fetchSources();
        fetchMetadata();
    }, []);

    const handleSave = async () => {
        const id = "src_" + Math.random().toString(36).substr(2, 9);
        const payload = { ...formData, id };

        try {
            await fetch(`${API_BASE_URL}/config/sources`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            setShowModal(false);
            setFormData({ name: "", type: "sqlserver", version: "", description: "", context_prompt: "" });
            fetchSources();
        } catch (e) {
            console.error(e);
        }
    };

    const handleDelete = async (id: string, e: any) => {
        e.stopPropagation(); // prevent other clicks
        if (!confirm("Are you sure you want to delete this profile?")) return;

        try {
            await fetch(`${API_BASE_URL}/config/sources/${id}`, { method: "DELETE" });
            fetchSources();
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold mb-1">Source Knowledge Profiles</h2>
                    <p className="text-gray-500">Define context for source systems to guide analysis agents.</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="bg-black dark:bg-white text-white dark:text-black px-4 py-2 rounded-lg font-bold flex items-center gap-2 hover:opacity-80 transition-opacity"
                >
                    <Plus size={18} /> Define Profile
                </button>
            </div>

            {loading ? <div className="p-8 text-center text-gray-500">Loading connectors...</div> : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {availableTech.map(tech => {
                        const techProfiles = sources.filter(s => s.type.toUpperCase() === tech.tech_id.toUpperCase());

                        return (
                            <div key={tech.tech_id} className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm flex flex-col">
                                <div className="p-5 border-b border-gray-50 dark:border-gray-800 bg-gray-50/30 dark:bg-gray-800/20 flex justify-between items-start">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl font-black shadow-inner ${tech.tech_id === 'SSIS' ? 'bg-blue-100 text-blue-600' :
                                            tech.tech_id === 'ORACLE' ? 'bg-red-100 text-red-600' :
                                                'bg-orange-100 text-orange-600'
                                            }`}>
                                            {tech.tech_id.substring(0, 3)}
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">{tech.label}</h3>
                                            <p className="text-xs text-gray-400 font-mono">{tech.version || 'Universal'}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleOpenDefine(tech.tech_id)}
                                        className="p-1.5 hover:bg-white dark:hover:bg-gray-800 rounded-full text-gray-400 hover:text-primary transition-all"
                                        title="Add New Profile"
                                    >
                                        <Plus size={20} />
                                    </button>
                                </div>

                                <div className="flex-1 p-5 space-y-3">
                                    <p className="text-xs text-gray-500 italic mb-4">{tech.description}</p>

                                    {techProfiles.length === 0 ? (
                                        <div className="py-6 border-2 border-dashed border-gray-100 dark:border-gray-800 rounded-xl flex flex-col items-center justify-center gap-2 opacity-50">
                                            <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">No Profiles Defined</span>
                                            <button
                                                onClick={() => handleOpenDefine(tech.tech_id)}
                                                className="text-[10px] font-bold text-primary hover:underline"
                                            >
                                                Define First Profile
                                            </button>
                                        </div>
                                    ) : (
                                        techProfiles.map(src => (
                                            <div key={src.id} className="p-3 rounded-lg border border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30 flex justify-between items-center group/item">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                                                    <div>
                                                        <h4 className="font-bold text-sm text-gray-800 dark:text-gray-200">{src.name}</h4>
                                                        <p className="text-[10px] text-gray-500">{src.version || 'Base'}</p>
                                                    </div>
                                                </div>
                                                <button onClick={(e) => handleDelete(src.id, e)} className="text-gray-300 hover:text-red-500 p-1.5 opacity-0 group-hover/item:opacity-100 transition-opacity">
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {sources.length === 0 && !loading && (
                <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-xl">
                    <p className="text-gray-400">No source profiles defined.</p>
                </div>
            )}

            {/* Add Profile Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6 w-[800px] max-w-full border border-gray-200 dark:border-gray-700 flex flex-col max-h-[90vh]">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold">Define Source Knowledge</h3>
                            <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-900"><X size={20} /></button>
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Profile Name</label>
                                    <input
                                        type="text"
                                        className="w-full border p-2 rounded-lg text-sm bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300"
                                        placeholder="e.g. Legacy CRM"
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Tech Stack</label>
                                    <select
                                        className="w-full border p-2 rounded-lg text-sm bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300"
                                        value={formData.type}
                                        onChange={e => setFormData({ ...formData, type: e.target.value })}
                                    >
                                        {availableTech.map(t => (
                                            <option key={t.tech_id} value={t.tech_id}>{t.label}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Version / Dialect Info</label>
                                <input
                                    type="text"
                                    className="w-full border p-2 rounded-lg text-sm bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300"
                                    placeholder="e.g. SQL Server 2008 R2, heavily uses CTEs"
                                    value={formData.version}
                                    onChange={e => setFormData({ ...formData, version: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Description</label>
                                <input
                                    type="text"
                                    className="w-full border p-2 rounded-lg text-sm bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300"
                                    placeholder="Brief context about this system..."
                                    value={formData.description}
                                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Context Instructions (For Scanner Agent)</label>
                                <textarea
                                    className="w-full border p-4 rounded-lg text-sm font-mono bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300 h-64 resize-y focus:ring-2 focus:ring-primary outline-none"
                                    placeholder="e.g. 'Pay attention to naming conventions. Procedures starting with usp_ are critical.'"
                                    value={formData.context_prompt}
                                    onChange={e => setFormData({ ...formData, context_prompt: e.target.value })}
                                />
                                <p className="text-xs text-gray-400 mt-1">These instructions will be injected into the Analysis Agent prompt.</p>
                            </div>
                        </div>

                        <div className="flex justify-end items-center mt-8 pt-4 border-t gap-3">
                            <button onClick={() => setShowModal(false)} className="px-4 py-2 text-gray-600 font-bold hover:bg-gray-100 rounded-lg">Cancel</button>
                            <button onClick={handleSave} className="px-6 py-2 bg-black text-white font-bold rounded-lg hover:bg-gray-800">Save Profile</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function DestinationManager() {
    const [generators, setGenerators] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [editModal, setEditModal] = useState<string | null>(null);
    const [editPrompt, setEditPrompt] = useState("");
    const [saving, setSaving] = useState(false);

    const fetchConfig = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/config/generators`);
            const data = await res.json();
            setGenerators(data.generators || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConfig();
    }, []);

    const handleSetDefault = async (type: string) => {
        try {
            await fetch(`${API_BASE_URL}/config/generators/default`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ default: type })
            });
            fetchConfig(); // Refresh
        } catch (e) {
            console.error(e);
        }
    };

    const handleOpenEdit = (gen: any) => {
        setEditModal(gen.id);
        setEditPrompt(gen.instruction_prompt || "");
    };

    const handleSavePrompt = async () => {
        if (!editModal) return;
        setSaving(true);
        const gen = generators.find(g => g.id === editModal);
        try {
            await fetch(`${API_BASE_URL}/config/generators/update`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ type: gen.type, instruction_prompt: editPrompt })
            });
            setEditModal(null);
            fetchConfig();
        } catch (e) {
            console.error(e);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold mb-1">Target Knowledge Profiles</h2>
                    <p className="text-gray-500">Configure code generation engines and specific instructions.</p>
                </div>
            </div>

            {loading ? <div className="p-8 text-center text-gray-500">Loading configuration...</div> : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {generators.map(gen => (
                        <div key={gen.id} className={`p-5 rounded-xl border transition-all ${gen.status === 'active'
                            ? "border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10"
                            : "border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 opacity-80"
                            }`}>
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white ${gen.type === 'spark' ? 'bg-[#E35A38]' : 'bg-[#29B5E8]'
                                        }`}>
                                        <Code2 size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">{gen.name}</h3>
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs font-mono text-gray-500">{gen.version}</span>
                                            {gen.instruction_prompt && (
                                                <span className="flex items-center gap-0.5 text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-bold">
                                                    <FileText size={8} /> Custom Instructions
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div className={`w-4 h-4 rounded-full border-2 ${gen.status === 'active' ? 'bg-blue-500 border-white shadow-sm' : 'border-gray-300'}`}></div>
                            </div>

                            <p className="text-sm text-gray-500 mb-4 h-10 line-clamp-2">
                                {gen.instruction_prompt
                                    ? `"${gen.instruction_prompt}"`
                                    : (gen.type === 'spark'
                                        ? "Generates optimized PySpark code compatible with Delta Lake."
                                        : "Generates Snowpark Python logic and native SQL DDLs.")}
                            </p>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleSetDefault(gen.type)}
                                    className={`flex-1 py-1.5 rounded-lg text-sm font-bold transition-colors ${gen.status === 'active'
                                        ? "bg-blue-600 text-white shadow-md cursor-default"
                                        : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200"
                                        }`}>
                                    {gen.status === 'active' ? 'Default Generator' : 'Set as Default'}
                                </button>
                                <button
                                    onClick={() => handleOpenEdit(gen)}
                                    className="p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:text-primary hover:border-primary transition-colors"
                                    title="Edit Generation Instructions"
                                >
                                    <Pencil size={18} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-800 rounded-xl flex gap-3">
                <AlertCircle className="text-gray-400 shrink-0" />
                <div className="text-sm text-gray-500">
                    <p className="font-bold text-gray-700 dark:text-gray-300 mb-1">How it works</p>
                    <p>The selected engine determines the syntax used during the <strong>Drafting</strong> and <strong>Refinement</strong> phases. You can customize the technical instructions (e.g., "Use specific naming conventions") by editing the profile.</p>
                </div>
            </div>

            {/* Edit Instruction Modal */}
            {editModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6 w-[900px] max-w-full border border-gray-200 dark:border-gray-700 flex flex-col max-h-[95vh]">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold">Edit Generator Instructions</h3>
                            <button onClick={() => setEditModal(null)} className="text-gray-400 hover:text-gray-900"><X size={20} /></button>
                        </div>

                        <div className="space-y-4">
                            <div className="p-4 bg-blue-50 text-blue-800 rounded-lg text-sm border border-blue-100 flex gap-2">
                                <Bot size={16} className="shrink-0 mt-0.5" />
                                <p>These instructions are injected into the <strong>Architect Agent</strong> and <strong>Coder Agent</strong> to guide code generation style, libraries, and best practices.</p>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Technical Context & Instructions</label>
                                <textarea
                                    className="w-full border p-4 rounded-lg text-sm font-mono bg-gray-50 dark:bg-gray-100 text-gray-900 border-gray-300 h-[500px] min-h-[300px] resize-y focus:ring-2 focus:ring-primary outline-none"
                                    placeholder="e.g. 'Always use the logging decorator. Prefer functional programming style. Use CamelCase for variables.'"
                                    value={editPrompt}
                                    onChange={e => setEditPrompt(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="flex justify-end items-center mt-8 pt-4 border-t gap-3">
                            <button onClick={() => setEditModal(null)} className="px-4 py-2 text-gray-600 font-bold hover:bg-gray-100 rounded-lg">Cancel</button>
                            <button
                                onClick={handleSavePrompt}
                                disabled={saving}
                                className="px-6 py-2 bg-black text-white font-bold rounded-lg hover:bg-gray-800 disabled:opacity-50"
                            >
                                {saving ? "Saving..." : "Save Instructions"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
