"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchWithAuth } from "../lib/auth-client";
import Link from "next/link";
import { ArrowLeft, Shield, Lock, Eye, Brain, Save, Copy, Database, Server, Plus, X, Terminal, Users } from "lucide-react";
import CartridgeList from "../components/admin/CartridgeList";

interface Prompt {
    id: string;
    name: string;
    content: string;
}

export default function SystemPage() {
    const { user } = useAuth();
    const isAdmin = user?.role === "ADMIN";

    const [activeTab, setActiveTab] = useState<"prompts" | "origins" | "destinations" | "identity">("prompts");

    // Data State
    const [prompts, setPrompts] = useState<Prompt[]>([]);
    const [origins, setOrigins] = useState([]);
    const [destinations, setDestinations] = useState([]);
    const [tenants, setTenants] = useState<any[]>([]);

    const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    // Validation Test State
    const [testInput, setTestInput] = useState("");
    const [testOutput, setTestOutput] = useState("");
    const [isTesting, setIsTesting] = useState(false);
    const [API_BASE_URL, setApiBaseUrl] = useState("http://localhost:8085"); // Fallback

    useEffect(() => {
        // Try to get config or just hardcode if needed since this is client
        import("../lib/config").then(m => setApiBaseUrl(m.API_BASE_URL)).catch(() => { });
    }, []);

    const handleRunTest = async () => {
        if (!selectedPromptId) return;
        setIsTesting(true);
        setTestOutput("Running validation...");

        try {
            const res = await fetchWithAuth(`system/validate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    agent_id: selectedPromptId, // "agent-a" etc
                    user_input: testInput || "Hello, verify your system prompt."
                })
            });
            const data = await res.json();
            if (data.success) {
                setTestOutput(data.response);
            } else {
                setTestOutput(`Error: ${data.error}`);
            }
        } catch (e) {
            setTestOutput(`Network Error: ${e}`);
        } finally {
            setIsTesting(false);
        }
    };

    // Add Modal State
    const [showAddModal, setShowAddModal] = useState(false);
    const [newCartridge, setNewCartridge] = useState({
        name: "",
        type: "origin", // default
        subtype: "",
        version: "",
        config: "{\n  \"icon\": \"default\"\n}"
    });

    const fetchData = () => {
        // Parallel Fetch
        Promise.all([
            fetchWithAuth("system/prompts").then(res => res.json()),
            fetchWithAuth("system/origins").then(res => res.json()),
            fetchWithAuth("system/destinations").then(res => res.json()),
            fetchWithAuth("auth/tenants").then(res => res.json())
        ]).then(([promptsData, originsData, destData, tenantsData]) => {
            setPrompts(promptsData.prompts || []);
            if (!selectedPromptId && promptsData.prompts?.length > 0) setSelectedPromptId(promptsData.prompts[0].id);

            setOrigins(originsData.origins || []);
            setDestinations(destData.destinations || []);
            setTenants(Array.isArray(tenantsData) ? tenantsData : []);

            setLoading(false);
        }).catch(err => {
            console.error("Failed to load system data", err);
            setLoading(false);
        });
    };

    useEffect(() => {
        fetchData();
    }, []);

    const selectedPrompt = prompts.find(p => p.id === selectedPromptId);

    // Handlers
    const handleToggle = async (id: string, status: string) => {
        await fetchWithAuth(`system/cartridges/${id}/toggle`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status })
        });
        fetchData();
    };

    const handleUpdateConfig = async (id: string, config: any) => {
        await fetchWithAuth(`system/cartridges/${id}/config`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config })
        });
        fetchData();
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to delete this cartridge?")) return;
        await fetchWithAuth(`system/cartridges/${id}`, { method: "DELETE" });
        fetchData();
    };

    const handleAdd = async () => {
        try {
            const payload = {
                ...newCartridge,
                config: JSON.parse(newCartridge.config)
            };

            // Override type based on active tab so user doesn't have to select if obviously in a tab
            // But let's allow flexibility. For now, force type to match tab if consistent? 
            // Better to let user choose or default to active tab.
            payload.type = activeTab === "origins" ? "origin" : "destination";

            await fetchWithAuth("system/cartridges", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            setShowAddModal(false);
            setNewCartridge({
                name: "",
                type: "origin",
                subtype: "",
                version: "",
                config: "{\n  \"icon\": \"default\"\n}"
            });
            fetchData();
        } catch (e) {
            alert("Invalid Config JSON");
        }
    };

    return (
        <div className="min-h-screen bg-[var(--background)] text-[var(--text-primary)] relative transition-colors duration-300 flex flex-col">

            {/* Header */}
            <header className="border-b border-[var(--border)] bg-[var(--surface)] p-4 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="p-2 -ml-2 rounded-full hover:bg-[var(--text-primary)]/5 transition-colors">
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div>
                        <h1 className="text-lg font-bold flex items-center gap-2">
                            <Shield className="w-5 h-5 text-cyan-500" />
                            Platform Administration
                        </h1>
                    </div>
                </div>

                {/* Top Tabs */}
                <div className="flex bg-[var(--background)] p-1 rounded-lg border border-[var(--border)] text-[10px] uppercase font-black tracking-widest">
                    <button
                        onClick={() => setActiveTab("prompts")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "prompts" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Brain size={14} /> Agent Brains</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("identity")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "identity" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Users size={14} /> Identity</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("origins")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "origins" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Database size={14} /> Origins</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("destinations")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "destinations" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Server size={14} /> Destinations</span>
                    </button>
                </div>

                {!isAdmin && (
                    <div className="flex items-center gap-2 px-3 py-1 bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 rounded-full text-[10px] font-black uppercase tracking-widest">
                        <Eye size={12} /> Inspector
                    </div>
                )}
            </header>

            {/* TABS CONTENT */}

            {activeTab === "prompts" && (
                <div className="flex-1 flex overflow-hidden">
                    {/* Sidebar: Agent List */}
                    <aside className="w-64 border-r border-[var(--border)] bg-[var(--surface)] flex flex-col overflow-y-auto">
                        <div className="p-4 text-[10px] font-black text-[var(--text-secondary)] uppercase tracking-[0.2em]">
                            Global Agents
                        </div>
                        <div className="space-y-1 px-2 pb-4">
                            {prompts.map(p => (
                                <button
                                    key={p.id}
                                    onClick={() => setSelectedPromptId(p.id)}
                                    className={`w-full text-left px-4 py-3 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all flex items-center justify-between group ${selectedPromptId === p.id
                                        ? "bg-cyan-600 text-white shadow-xl shadow-cyan-600/20 translate-x-1"
                                        : "text-[var(--text-tertiary)] hover:bg-cyan-500/5 hover:text-cyan-500 hover:translate-x-1"
                                        }`}
                                >
                                    {p.name}
                                    {!isAdmin && <Lock size={12} className={`opacity-50 group-hover:opacity-100`} />}
                                </button>
                            ))}
                        </div>
                    </aside>

                    {/* Main Content: Prompt Viewer */}
                    <main className="flex-1 bg-[var(--background)] flex flex-col">
                        {selectedPrompt ? (
                            <>
                                <div className="p-4 border-b border-[var(--border)] flex justify-between items-center bg-[var(--surface)]/50">
                                    <div>
                                        <h2 className="text-xl font-bold">{selectedPrompt.name}</h2>
                                        <p className="text-xs text-[var(--text-secondary)] font-mono mt-1">ID: {selectedPrompt.id}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button className="p-2 hover:bg-cyan-500/10 rounded-xl text-[var(--text-tertiary)] hover:text-cyan-500 transition-all" title="Copy Prompt">
                                            <Copy size={18} />
                                        </button>
                                        {isAdmin && (
                                            <button className="px-6 py-2.5 bg-cyan-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/10">
                                                <Save size={16} /> Save Changes
                                            </button>
                                        )}
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto p-6">
                                    <div className="max-w-4xl mx-auto bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-sm p-8 min-h-[500px]">
                                        {isAdmin ? (
                                            <textarea
                                                key={selectedPrompt.id}
                                                className="w-full h-full min-h-[500px] bg-transparent outline-none resize-none font-mono text-sm leading-relaxed"
                                                defaultValue={selectedPrompt.content}
                                                spellCheck={false}
                                            />
                                        ) : (
                                            <pre key={selectedPrompt.id} className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-[var(--text-secondary)]">
                                                {selectedPrompt.content}
                                            </pre>
                                        )}
                                    </div>
                                </div>

                                {/* Validation Playground */}
                                <div className="max-w-4xl mx-auto mt-6 bg-white dark:bg-white/5 border border-gray-100 dark:border-white/5 rounded-3xl p-8 mb-12 shadow-2xl">
                                    <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--text-tertiary)] mb-6 flex items-center gap-2">
                                        <Terminal size={14} className="text-cyan-500" />
                                        Validation Playground
                                    </h4>
                                    <div className="flex gap-4 mb-6">
                                        <input
                                            className="flex-1 px-4 py-3 text-sm border border-gray-100 dark:border-white/5 rounded-2xl bg-gray-50 dark:bg-black/20 outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all placeholder-[var(--text-tertiary)]"
                                            placeholder="Enter test message (e.g. 'Analyze this table structure...')"
                                            value={testInput}
                                            onChange={e => setTestInput(e.target.value)}
                                            onKeyDown={e => e.key === 'Enter' && handleRunTest()}
                                        />
                                        <button
                                            onClick={handleRunTest}
                                            disabled={isTesting}
                                            className="px-8 py-3 bg-cyan-600 text-white text-[10px] font-black uppercase tracking-widest rounded-2xl hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 disabled:opacity-50 active:scale-95"
                                        >
                                            {isTesting ? "Testing..." : "Run Test"}
                                        </button>
                                    </div>
                                    {testOutput && (
                                        <div className="p-6 bg-gray-100 dark:bg-black/40 rounded-2xl border border-gray-200 dark:border-white/5 text-xs font-mono max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed custom-scrollbar">
                                            {testOutput}
                                        </div>
                                    )}
                                </div>

                            </>
                        ) : (
                            <div className="flex items-center justify-center h-full text-[var(--text-secondary)]">
                                {loading ? "Loading System..." : "Select an Agent"}
                            </div>
                        )}
                    </main>
                </div>
            )}

            {/* IDENTITY TAB */}
            {activeTab === "identity" && (
                <div className="flex-1 bg-[var(--background)] p-8 overflow-y-auto">
                    <div className="max-w-6xl mx-auto">
                        <div className="flex justify-between items-end mb-8">
                            <div>
                                <h2 className="text-2xl font-bold mb-2">Identity & Tenant Management</h2>
                                <p className="text-[var(--text-secondary)]">Manage user access, roles, and administrative impersonation (Ghost Mode).</p>
                            </div>
                            {isAdmin && (
                                <button
                                    className="bg-cyan-600 text-white px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 active:scale-95"
                                    onClick={() => alert("Simplified: Creation flow not yet connected to UI modal")}
                                >
                                    <Plus size={16} /> Invite User
                                </button>
                            )}
                        </div>

                        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl overflow-hidden shadow-sm">
                            <table className="w-full text-left">
                                <thead className="bg-[var(--background)]/50 text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] border-b border-[var(--border)]">
                                    <tr>
                                        <th className="px-6 py-4">Username</th>
                                        <th className="px-6 py-4">Role</th>
                                        <th className="px-6 py-4">Client ID</th>
                                        <th className="px-6 py-4">Tenant ID</th>
                                        <th className="px-6 py-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[var(--border)]">
                                    {tenants.map((t: any) => (
                                        <tr key={t.tenant_id} className="hover:bg-cyan-500/5 transition-colors group">
                                            <td className="px-6 py-4 text-sm font-bold">{t.username}</td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${t.role === 'ADMIN' ? 'bg-amber-500/10 text-amber-500' : 'bg-cyan-500/10 text-cyan-500'
                                                    }`}>
                                                    {t.role}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-xs font-mono opacity-50">{t.client_id}</td>
                                            <td className="px-6 py-4 text-xs font-mono opacity-50">{t.tenant_id}</td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <button
                                                        onClick={() => {
                                                            if (confirm(`Activate Ghost Mode for ${t.username}? You will be redirected to the workspace.`)) {
                                                                localStorage.setItem("x_tenant_id", t.tenant_id);
                                                                localStorage.setItem("x_client_id", t.client_id);
                                                                localStorage.setItem("x_username", t.username);
                                                                window.location.href = "/dashboard";
                                                            }
                                                        }}
                                                        className="p-2 text-[var(--text-tertiary)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-lg transition-all"
                                                        title="Ghost Mode (Impersonate)"
                                                    >
                                                        <Eye size={16} />
                                                    </button>
                                                    {isAdmin && t.tenant_id !== user?.tenant_id && (
                                                        <button
                                                            className="p-2 text-[var(--text-tertiary)] hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                                                            title="Delete"
                                                            onClick={async () => {
                                                                if (confirm(`Permanently remove ${t.username}?`)) {
                                                                    await fetchWithAuth(`auth/tenants/${t.tenant_id}`, { method: 'DELETE' });
                                                                    fetchData();
                                                                }
                                                            }}
                                                        >
                                                            <X size={16} />
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {tenants.length === 0 && (
                                <div className="p-12 text-center text-[var(--text-tertiary)] flex flex-col items-center gap-4">
                                    <Users size={48} className="opacity-10" />
                                    <p className="font-bold uppercase text-[10px] tracking-widest">No tenants found or access denied</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ORIGINS / DESTINATIONS TABS */}
            {
                (activeTab === "origins" || activeTab === "destinations") && (
                    <div className="flex-1 bg-[var(--background)] p-8 overflow-y-auto">
                        <div className="max-w-5xl mx-auto">
                            <div className="mb-6 flex justify-between items-end">
                                <div>
                                    <h2 className="text-2xl font-bold mb-2">
                                        {activeTab === "origins" ? "Input Cartridges (Origins)" : "Output Cartridges (Destinations)"}
                                    </h2>
                                    <p className="text-[var(--text-secondary)]">
                                        {activeTab === "origins"
                                            ? "Manage supported Legacy Technologies for ingestion and code analysis."
                                            : "Manage supported Target Cloud Stacks for generating modernization code."}
                                    </p>
                                </div>
                                {isAdmin && (
                                    <button
                                        onClick={() => setShowAddModal(true)}
                                        className="bg-cyan-600 text-white px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 active:scale-95"
                                    >
                                        <Plus size={16} /> Add Cartridge
                                    </button>
                                )}
                            </div>

                            {loading ? (
                                <div className="text-center p-8">Loading Capabilities...</div>
                            ) : (
                                <CartridgeList
                                    items={activeTab === "origins" ? origins : destinations}
                                    type={activeTab === "origins" ? "origin" : "destination"}
                                    onToggle={handleToggle}
                                    onUpdateConfig={handleUpdateConfig}
                                    onDelete={handleDelete}
                                />
                            )}
                        </div>
                    </div>
                )
            }

            {/* ADD MODAL */}
            {
                showAddModal && (
                    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
                        <div className="bg-[var(--surface)] text-[var(--text-primary)] rounded-xl shadow-2xl w-full max-w-lg overflow-hidden border border-[var(--border)]">
                            <div className="p-4 border-b border-[var(--border)] flex justify-between items-center bg-[var(--background)]">
                                <h3 className="font-bold text-lg">Add New Cartridge</h3>
                                <button onClick={() => setShowAddModal(false)} className="p-1 hover:bg-[var(--surface-hover)] rounded-full">
                                    <X size={20} />
                                </button>
                            </div>
                            <div className="p-6 space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-xs font-bold uppercase text-[var(--text-secondary)] mb-1">Name</label>
                                        <input
                                            className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm"
                                            placeholder="e.g. My Custom Oracle"
                                            value={newCartridge.name}
                                            onChange={e => setNewCartridge({ ...newCartridge, name: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold uppercase text-[var(--text-secondary)] mb-1">Subtype/Key</label>
                                        <input
                                            className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm"
                                            placeholder="e.g. oracle-custom"
                                            value={newCartridge.subtype}
                                            onChange={e => setNewCartridge({ ...newCartridge, subtype: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold uppercase text-[var(--text-secondary)] mb-1">Version</label>
                                    <input
                                        className="w-full p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm"
                                        placeholder="e.g. 19c"
                                        value={newCartridge.version}
                                        onChange={e => setNewCartridge({ ...newCartridge, version: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold uppercase text-[var(--text-secondary)] mb-1">Configuration (JSON)</label>
                                    <textarea
                                        className="w-full h-32 p-2 rounded border border-[var(--border)] bg-[var(--background)] text-sm font-mono"
                                        value={newCartridge.config}
                                        onChange={e => setNewCartridge({ ...newCartridge, config: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="p-4 border-t border-[var(--border)] bg-[var(--background)] flex justify-end gap-2">
                                <button
                                    onClick={() => setShowAddModal(false)}
                                    className="px-4 py-2 rounded-lg text-sm font-bold border border-[var(--border)] hover:bg-[var(--surface)]"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAdd}
                                    className="px-4 py-2 rounded-lg text-sm font-bold bg-[var(--color-primary)] text-white hover:brightness-110"
                                    disabled={!newCartridge.name || !newCartridge.subtype}
                                >
                                    Create Cartridge
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    );
}
