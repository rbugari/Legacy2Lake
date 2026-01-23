"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchWithAuth } from "../lib/auth-client";
import Link from "next/link";
import { ArrowLeft, Shield, Lock, Eye, Brain, Save, Copy, Database, Server, Plus, X, Terminal } from "lucide-react";
import CartridgeList from "../components/system/CartridgeList";

interface Prompt {
    id: string;
    name: string;
    content: string;
}

export default function SystemPage() {
    const { user } = useAuth();
    const isAdmin = user?.role === "ADMIN";

    const [activeTab, setActiveTab] = useState<"prompts" | "origins" | "destinations">("prompts");

    // Data State
    const [prompts, setPrompts] = useState<Prompt[]>([]);
    const [origins, setOrigins] = useState([]);
    const [destinations, setDestinations] = useState([]);

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
            fetchWithAuth("system/destinations").then(res => res.json())
        ]).then(([promptsData, originsData, destData]) => {
            setPrompts(promptsData.prompts || []);
            if (!selectedPromptId && promptsData.prompts?.length > 0) setSelectedPromptId(promptsData.prompts[0].id);

            setOrigins(originsData.origins || []);
            setDestinations(destData.destinations || []);

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
                            <Shield className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                            System Administration
                        </h1>
                    </div>
                </div>

                {/* Top Tabs */}
                <div className="flex bg-[var(--background)] p-1 rounded-lg border border-[var(--border)]">
                    <button
                        onClick={() => setActiveTab("prompts")}
                        className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${activeTab === "prompts" ? "bg-[var(--surface)] shadow text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
                    >
                        <span className="flex items-center gap-2"><Brain size={14} /> Agent Brains</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("origins")}
                        className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${activeTab === "origins" ? "bg-[var(--surface)] shadow text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
                    >
                        <span className="flex items-center gap-2"><Database size={14} /> Origins</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("destinations")}
                        className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${activeTab === "destinations" ? "bg-[var(--surface)] shadow text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
                    >
                        <span className="flex items-center gap-2"><Server size={14} /> Destinations</span>
                    </button>
                </div>

                {!isAdmin && (
                    <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs font-bold">
                        <Eye size={12} /> Inspector
                    </div>
                )}
            </header>

            {/* TABS CONTENT */}

            {activeTab === "prompts" && (
                <div className="flex-1 flex overflow-hidden">
                    {/* Sidebar: Agent List */}
                    <aside className="w-64 border-r border-[var(--border)] bg-[var(--surface)] flex flex-col overflow-y-auto">
                        <div className="p-4 text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                            System Agents
                        </div>
                        <div className="space-y-1 px-2 pb-4">
                            {prompts.map(p => (
                                <button
                                    key={p.id}
                                    onClick={() => setSelectedPromptId(p.id)}
                                    className={`w-full text-left px-3 py-3 rounded-lg text-sm font-medium transition-colors flex items-center justify-between group ${selectedPromptId === p.id
                                        ? "bg-[var(--color-primary)] text-white"
                                        : "text-[var(--text-secondary)] hover:bg-[var(--text-primary)]/5 hover:text-[var(--text-primary)]"
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
                                        <button className="p-2 hover:bg-[var(--text-primary)]/5 rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)]" title="Copy Prompt">
                                            <Copy size={18} />
                                        </button>
                                        {isAdmin && (
                                            <button className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-bold flex items-center gap-2 hover:opacity-90">
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
                                <div className="max-w-4xl mx-auto mt-6 bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-sm p-6">
                                    <h4 className="font-bold text-sm mb-4 flex items-center gap-2">
                                        <Terminal size={14} className="text-purple-500" />
                                        Validation Playground
                                    </h4>
                                    <div className="flex gap-2 mb-4">
                                        <input
                                            className="flex-1 p-3 text-sm border border-[var(--border)] rounded bg-[var(--background)]"
                                            placeholder="Enter test message (e.g. 'Analyze this table structure...')"
                                            value={testInput}
                                            onChange={e => setTestInput(e.target.value)}
                                            onKeyDown={e => e.key === 'Enter' && handleRunTest()}
                                        />
                                        <button
                                            onClick={handleRunTest}
                                            disabled={isTesting}
                                            className="px-6 py-2 bg-[var(--color-primary)] text-white text-sm font-bold rounded hover:brightness-110 disabled:opacity-50"
                                        >
                                            {isTesting ? "Testing..." : "Run Test"}
                                        </button>
                                    </div>
                                    {testOutput && (
                                        <div className="p-4 bg-[var(--background)] rounded border border-[var(--border)] text-xs font-mono max-h-48 overflow-y-auto whitespace-pre-wrap">
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
                                        className="bg-[var(--color-primary)] text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 text-sm hover:brightness-110"
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
