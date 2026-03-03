"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchWithAuth as baseFetchWithAuth } from "../lib/auth-client";
import Link from "next/link";
import { ArrowLeft, Shield, Lock, Eye, EyeOff, Brain, Save, Copy, Database, Server, Plus, X, Terminal, Users, FlaskConical, Download, Upload, Activity, History, ChevronDown, Key, Code2, FileText, Edit3, Edit2, Briefcase, RefreshCw } from "lucide-react";
import CartridgeList from "../components/admin/CartridgeList";
import { getAgentDisplayName } from "../lib/constants";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface Prompt {
    id: string;
    name: string;
    content: string;
}

const fetchWithAuth = (endpoint: string, options: any = {}) => baseFetchWithAuth(endpoint, { ...options, skipImpersonation: true });

export default function SystemPage() {
    const { user } = useAuth();
    const isAdmin = user?.role === "ADMIN";

    const [activeTab, setActiveTab] = useState<"prompts" | "origins" | "destinations" | "identity" | "agents" | "locks">("identity");

    // Data State
    const [prompts, setPrompts] = useState<Prompt[]>([]);
    const [origins, setOrigins] = useState([]);
    const [destinations, setDestinations] = useState([]);
    const [tenants, setTenants] = useState<any[]>([]);
    const [agents, setAgents] = useState<any[]>([]);
    const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
    const [editingAgent, setEditingAgent] = useState<any>(null);

    const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    // Validation Test State
    const [testInput, setTestInput] = useState("");
    const [testOutput, setTestOutput] = useState("");
    const [isTesting, setIsTesting] = useState(false);
    // Lab State
    const [isExporting, setIsExporting] = useState(false);
    const [showImportModal, setShowImportModal] = useState(false);
    const [labPath, setLabPath] = useState("./prompt_lab_export");
    const [promptVersions, setPromptVersions] = useState<any[]>([]);
    const [showVersionHistory, setShowVersionHistory] = useState(false);
    const [viewMode, setViewMode] = useState<'source' | 'elegant'>('source');
    const [editedContent, setEditedContent] = useState("");

    // Process Locks State
    const [processLocks, setProcessLocks] = useState<any[]>([]);
    const [isLoadingLocks, setIsLoadingLocks] = useState(false);

    // Users Dashboard State
    const [allUsers, setAllUsers] = useState<any[]>([]);
    const [isLoadingUsers, setIsLoadingUsers] = useState(false);
    const [filterTenant, setFilterTenant] = useState<string>("");
    const [filterRole, setFilterRole] = useState<string>("");
    const [filterSearch, setFilterSearch] = useState<string>("");
    const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
    const [resetPasswordUser, setResetPasswordUser] = useState<any>(null);
    const [newPassword, setNewPassword] = useState("");
    const [isResettingPassword, setIsResettingPassword] = useState(false);

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

    // Invitation State
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [isInviting, setIsInviting] = useState(false);
    const [inviteData, setInviteData] = useState({
        username: "",
        email: ""
    });
    const [clients, setClients] = useState<any[]>([]);

    // Client/Tenant Creation State
    const [showCreateTenantModal, setShowCreateTenantModal] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [newTenantData, setNewTenantData] = useState({
        username: "",
        email: "",
        password: "",
        display_name: "",
        tier: "STANDARD"
    });

    // Edit Tenant State
    const [showEditTenantModal, setShowEditTenantModal] = useState(false);
    const [editingTenant, setEditingTenant] = useState<any>(null);
    const [isUpdating, setIsUpdating] = useState(false);

    const fetchData = () => {
        // Parallel Fetch
        Promise.all([
            fetchWithAuth("system/prompts").then(res => res.json()),
            fetchWithAuth("system/origins").then(res => res.json()),
            fetchWithAuth("system/destinations").then(res => res.json()),
            fetchWithAuth("auth/tenants").then(res => res.json()),
            fetchWithAuth("system/agents").then(res => res.json())
        ]).then(([promptsData, originsData, destData, tenantsData, agentsData]) => {
            setPrompts(promptsData.prompts || []);
            if (!selectedPromptId && promptsData.prompts?.length > 0) setSelectedPromptId(promptsData.prompts[0].id);

            setOrigins(originsData.origins || []);
            setDestinations(destData.destinations || []);
            setTenants(Array.isArray(tenantsData) ? tenantsData : []);
            setAgents(agentsData.agents || []);
            if (!selectedAgentId && agentsData.agents?.length > 0) setSelectedAgentId(agentsData.agents[0].agent_id);

            setLoading(false);
        }).catch(err => {
            console.error("Failed to load system data", err);
            setLoading(false);
        });
    };

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        if (selectedPromptId && activeTab === "prompts") {
            fetchWithAuth(`lab/versions/${selectedPromptId}`).then(res => res.json()).then(data => {
                setPromptVersions(data.versions || []);
            }).catch(err => {
                console.error("Error fetching versions:", err);
                setPromptVersions([]);
            });

            // Initialize edited content with selected prompt
            const prompt = prompts.find(p => p.id === selectedPromptId);
            if (prompt) {
                setEditedContent(prompt.content);
            }
        }
    }, [selectedPromptId, activeTab, prompts]);

    const handleExportLab = async () => {
        setIsExporting(true);
        try {
            const res = await fetchWithAuth("lab/export", { method: "POST" });
            const data = await res.json();
            if (data.status === "success") {
                // Trigger Download
                const downloadUrl = `${API_BASE_URL}/lab/download`;
                const link = document.createElement("a");
                link.href = downloadUrl;
                link.setAttribute("download", "prompt_lab_export.zip");
                document.body.appendChild(link);
                link.click();
                link.remove();

                alert(`Export successful! Folder created at: ${data.output_path}\n\nYour download should start automatically.`);
            } else {
                alert("Export failed");
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsExporting(false);
        }
    };

    const handleActivateVersion = async (v: number) => {
        if (!confirm(`Activate version ${v} for ${selectedPromptId}? (Blue-Green Switch)`)) return;
        try {
            const res = await fetchWithAuth(`lab/activate?prompt_id=${selectedPromptId}&version=${v}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "success") {
                fetchData();
                fetchWithAuth(`lab/versions/${selectedPromptId}`).then(res => res.json()).then(d => setPromptVersions(d.versions || []));
            }
        } catch (e) { console.error(e); }
    };

    const handleImportLab = async () => {
        try {
            const res = await fetchWithAuth(`lab/import?prompt_id=${selectedPromptId}&lab_path=${labPath}/${selectedPromptId}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "success") {
                alert(`Imported version ${data.new_version} successfully!`);
                setShowImportModal(false);
                fetchWithAuth(`lab/versions/${selectedPromptId}`).then(res => res.json()).then(d => setPromptVersions(d.versions || []));
            } else {
                alert(`Import failed: ${data.message}`);
            }
        } catch (e) {
            alert("Network error during import");
        }
    };

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

            // Force type to match current context but allow override if needed
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

    const handleInviteUser = async () => {
        if (!inviteData.username || !inviteData.email) {
            alert("Please fill all required fields");
            return;
        }

        setIsInviting(true);
        try {
            const res = await fetchWithAuth("auth/invite", {
                method: "POST",
                body: JSON.stringify(inviteData)
            });
            const data = await res.json();

            if (res.ok) {
                alert("User invited successfully!");
                if (data.temp_password) {
                    alert(`NOTE: Email failed to send, but user and client were created. Temporary password: ${data.temp_password}`);
                }
                setShowInviteModal(false);
                setInviteData({ username: "", email: "" });
                fetchData();
            } else {
                alert(`Error: ${data.detail || "Failed to invite user"}`);
            }
        } catch (err) {
            alert("Network error during invitation");
        } finally {
            setIsInviting(false);
        }
    };

    const handleUpdateAgent = async (agentId: string, updates: { display_name?: string, description?: string }) => {
        try {
            const res = await fetchWithAuth(`system/agents/${agentId}`, {
                method: "PUT",
                body: JSON.stringify(updates)
            });
            const data = await res.json();
            if (res.ok) {
                alert("Agent updated successfully!");
                setEditingAgent(null);
                fetchData();
            } else {
                alert(`Error: ${data.detail || "Failed to update agent"}`);
            }
        } catch (err) {
            alert("Network error");
        }
    };

    const handleCreateTenant = async () => {
        if (!newTenantData.display_name || !newTenantData.username || !newTenantData.email || !newTenantData.password) {
            alert("Please fill all required fields");
            return;
        }
        setIsCreating(true);
        try {
            const res = await fetchWithAuth("auth/tenants", {
                method: "POST",
                body: JSON.stringify(newTenantData)
            });
            const data = await res.json();
            if (res.ok) {
                alert(`Tenant created successfully! Tenant ID: ${data.tenant_id}`);
                setShowCreateTenantModal(false);
                setNewTenantData({ username: "", email: "", password: "", display_name: "", tier: "STANDARD" });
                setShowPassword(false);
                fetchData();
            } else {
                alert(`Error: ${data.detail || "Failed to create tenant"}`);
            }
        } catch (err) {
            alert("Network error");
        } finally {
            setIsCreating(false);
        }
    };

    const handleUpdateTenant = async () => {
        if (!editingTenant?.display_name) {
            alert("Display name cannot be empty");
            return;
        }
        setIsUpdating(true);
        try {
            const res = await fetchWithAuth(`auth/tenants/${editingTenant.tenant_id}`, {
                method: "PATCH",
                body: JSON.stringify({
                    display_name: editingTenant.display_name,
                    tier: editingTenant.tier
                })
            });
            if (res.ok) {
                alert("Tenant updated successfully!");
                setShowEditTenantModal(false);
                setEditingTenant(null);
                fetchData();
            } else {
                const data = await res.json();
                alert(`Error: ${data.detail || "Failed to update tenant"}`);
            }
        } catch (err) {
            alert("Network error");
        } finally {
            setIsUpdating(false);
        }
    };

    // Process Locks Functions
    const fetchProcessLocks = async () => {
        setIsLoadingLocks(true);
        try {
            const res = await fetchWithAuth("locks/all");
            const data = await res.json();
            if (res.ok && data.locks) {
                setProcessLocks(data.locks);
            } else {
                setProcessLocks([]);
            }
        } catch (err) {
            console.error("Failed to fetch locks:", err);
            setProcessLocks([]);
        } finally {
            setIsLoadingLocks(false);
        }
    };

    const handleForceReleaseLock = async (lockId: string, projectId: string, processType: string) => {
        if (!confirm(`Are you sure you want to force-release this ${processType} lock?\n\nThis will allow other users to execute this process on the project.`)) {
            return;
        }

        try {
            const res = await fetchWithAuth(`locks/${lockId}/force-release`, {
                method: "POST"
            });
            const data = await res.json();
            if (res.ok && data.success) {
                alert("Lock released successfully!");
                fetchProcessLocks(); // Refresh
            } else {
                alert(`Error: ${data.error || "Failed to release lock"}`);
            }
        } catch (err) {
            alert("Network error");
        }
    };

    // Load locks when tab is active
    useEffect(() => {
        if (activeTab === "locks" && isAdmin) {
            fetchProcessLocks();
            // Auto-refresh every 30 seconds
            const interval = setInterval(fetchProcessLocks, 30000);
            return () => clearInterval(interval);
        }
    }, [activeTab, isAdmin]);

    // Users Dashboard Functions
    const fetchAllUsers = async () => {
        setIsLoadingUsers(true);
        try {
            const res = await fetchWithAuth("auth/admin/users");
            const data = await res.json();
            if (res.ok && data.users) {
                setAllUsers(data.users);
            } else {
                setAllUsers([]);
            }
        } catch (err) {
            console.error("Failed to fetch users:", err);
            setAllUsers([]);
        } finally {
            setIsLoadingUsers(false);
        }
    };

    const handleResetPassword = async () => {
        if (!resetPasswordUser || !newPassword) {
            alert("Please enter a new password");
            return;
        }
        if (newPassword.length < 8) {
            alert("Password must be at least 8 characters");
            return;
        }
        setIsResettingPassword(true);
        try {
            const res = await fetchWithAuth(`auth/admin/users/${resetPasswordUser.user_id}/reset-password`, {
                method: "POST",
                body: JSON.stringify({ new_password: newPassword })
            });
            if (res.ok) {
                alert(`Password reset successfully for ${resetPasswordUser.username}`);
                setShowResetPasswordModal(false);
                setResetPasswordUser(null);
                setNewPassword("");
            } else {
                const data = await res.json();
                alert(`Error: ${data.detail || "Failed to reset password"}`);
            }
        } catch (err) {
            alert("Network error");
        } finally {
            setIsResettingPassword(false);
        }
    };

    const handleImpersonate = async (targetUserId: string, username: string) => {
        if (!confirm(`Start Ghost Mode as ${username}?\\n\\nYou will impersonate this user and see their tenant/projects.`)) {
            return;
        }
        try {
            const res = await fetchWithAuth("auth/admin/impersonate", {
                method: "POST",
                body: JSON.stringify({ target_user_id: targetUserId })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                alert(`Ghost Mode activated!\\n\\nYou are now: ${data.impersonate.username} (${data.impersonate.role})`);
                // Store impersonate info
                localStorage.setItem("x_impersonate_user_id", targetUserId);
                // Redirect to dashboard to see as that user
                window.location.href = "/dashboard";
            } else {
                alert(`Error: ${data.detail || "Failed to impersonate"}`);
            }
        } catch (err) {
            alert("Network error");
        }
    };

    // Load users when tab is active
    useEffect(() => {
        if (activeTab === "users" && isAdmin) {
            fetchAllUsers();
        }
    }, [activeTab, isAdmin]);

    // Filtered users
    const filteredUsers = allUsers.filter(u => {
        if (filterTenant && !u.tenant_display_name?.toLowerCase().includes(filterTenant.toLowerCase())) return false;
        if (filterRole && u.role !== filterRole) return false;
        if (filterSearch && !(
            u.username?.toLowerCase().includes(filterSearch.toLowerCase()) ||
            u.email?.toLowerCase().includes(filterSearch.toLowerCase())
        )) return false;
        return true;
    });

    // Load locks when tab is active (old code kept for reference)
    useEffect(() => {
        if (activeTab === "locks" && isAdmin) {
            fetchProcessLocks();
            // Auto-refresh every 30 seconds
            const interval = setInterval(fetchProcessLocks, 30000);
            return () => clearInterval(interval);
        }
    }, [activeTab, isAdmin]);

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
                        onClick={() => setActiveTab("identity")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "identity" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Users size={14} /> Identity</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("users")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "users" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Users size={14} /> All Users</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("agents")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "agents" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Activity size={14} /> Agents</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("locks")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "locks" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Lock size={14} /> Process Locks</span>
                    </button>
                    <button
                        onClick={() => setActiveTab("prompts")}
                        className={`px-4 py-1.5 rounded-md transition-all ${activeTab === "prompts" ? "bg-cyan-500 text-white shadow-lg shadow-cyan-500/20" : "text-[var(--text-secondary)] hover:text-cyan-500"}`}
                    >
                        <span className="flex items-center gap-2"><Brain size={14} /> Agent Brains</span>
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

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleExportLab}
                        disabled={isExporting}
                        className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:brightness-110 transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
                    >
                        <FlaskConical size={14} className={isExporting ? "animate-pulse" : ""} />
                        {isExporting ? "Exporting..." : "Export Lab"}
                    </button>
                    {!isAdmin && (
                        <div className="flex items-center gap-2 px-3 py-1 bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 rounded-full text-[10px] font-black uppercase tracking-widest">
                            <Eye size={12} /> Inspector
                        </div>
                    )}
                </div>
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
                                    {getAgentDisplayName(p.id)}
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
                                    <div className="flex items-center gap-4">
                                        <div>
                                            <h2 className="text-xl font-bold">{getAgentDisplayName(selectedPrompt.id)}</h2>
                                            <p className="text-xs text-[var(--text-secondary)] font-mono mt-1">ID: {selectedPrompt.id}</p>
                                        </div>
                                        <div className="flex bg-[var(--surface-elevated)] p-1 rounded-lg border border-[var(--border)] gap-1">
                                            <button
                                                onClick={() => setViewMode('source')}
                                                className={`px-3 py-1 rounded-md text-[9px] font-black uppercase tracking-widest transition-all flex items-center gap-1 ${viewMode === 'source'
                                                    ? "bg-cyan-600 text-white shadow-lg"
                                                    : "text-[var(--text-tertiary)] hover:text-cyan-400"
                                                    }`}
                                            >
                                                <Code2 size={12} />
                                                Source
                                            </button>
                                            <button
                                                onClick={() => setViewMode('elegant')}
                                                className={`px-3 py-1 rounded-md text-[9px] font-black uppercase tracking-widest transition-all flex items-center gap-1 ${viewMode === 'elegant'
                                                    ? "bg-purple-600 text-white shadow-lg"
                                                    : "text-[var(--text-tertiary)] hover:text-purple-400"
                                                    }`}
                                            >
                                                <Edit3 size={12} />
                                                Edit
                                            </button>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <div className="relative group mr-4">
                                            <button
                                                onClick={() => setShowVersionHistory(!showVersionHistory)}
                                                className="px-4 py-2 bg-[var(--background-secondary)] border border-[var(--border)] rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-cyan-500/10 transition-all"
                                            >
                                                <History size={14} />
                                                v{promptVersions.find(v => v.is_active)?.version_number || 1}
                                                <ChevronDown size={14} />
                                            </button>

                                            {showVersionHistory && (
                                                <div className="absolute top-full right-0 mt-2 w-64 bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl z-50 overflow-hidden">
                                                    <div className="p-3 text-[9px] font-black text-[var(--text-tertiary)] uppercase border-b border-[var(--border)]">Version History</div>
                                                    <div className="max-h-64 overflow-y-auto">
                                                        {promptVersions.map(v => (
                                                            <div key={v.version_number} className={`p-4 hover:bg-cyan-500/5 transition-all border-b border-[var(--border)] last:border-0 ${v.is_active ? 'bg-cyan-500/5' : ''}`}>
                                                                <div className="flex justify-between items-center mb-1">
                                                                    <span className="text-[10px] font-black">VERSION {v.version_number}</span>
                                                                    {v.is_active ? (
                                                                        <span className="px-2 py-0.5 bg-green-500 text-white text-[8px] font-black rounded-full uppercase">Active</span>
                                                                    ) : (
                                                                        <button
                                                                            onClick={() => handleActivateVersion(v.version_number)}
                                                                            className="text-[8px] font-black text-cyan-500 uppercase hover:underline"
                                                                        >
                                                                            Activate
                                                                        </button>
                                                                    )}
                                                                </div>
                                                                <p className="text-[9px] text-[var(--text-tertiary)] truncate">{v.changelog || 'No changelog provided'}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        <button
                                            onClick={() => setShowImportModal(true)}
                                            className="px-4 py-2 bg-indigo-600/10 text-indigo-500 border border-indigo-500/30 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-indigo-600 hover:text-white transition-all shadow-lg shadow-indigo-500/10"
                                        >
                                            <Upload size={14} /> Import optimized
                                        </button>

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
                                    <div className="max-w-4xl mx-auto bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-sm min-h-[500px]">
                                        {viewMode === 'source' ? (
                                            <div className="p-8">
                                                <SyntaxHighlighter
                                                    language="markdown"
                                                    style={vscDarkPlus}
                                                    customStyle={{
                                                        background: 'transparent',
                                                        padding: 0,
                                                        margin: 0,
                                                        fontSize: '13px',
                                                        lineHeight: '1.8'
                                                    }}
                                                    wrapLongLines={true}
                                                >
                                                    {selectedPrompt.content}
                                                </SyntaxHighlighter>
                                            </div>
                                        ) : (
                                            <div className="p-8">
                                                {isAdmin ? (
                                                    <textarea
                                                        key={selectedPrompt.id}
                                                        className="w-full h-full min-h-[500px] bg-transparent outline-none resize-none font-mono text-sm leading-relaxed text-[var(--text-primary)]"
                                                        value={editedContent}
                                                        onChange={e => setEditedContent(e.target.value)}
                                                        spellCheck={false}
                                                    />
                                                ) : (
                                                    <pre key={selectedPrompt.id} className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-[var(--text-secondary)]">
                                                        {selectedPrompt.content}
                                                    </pre>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Validation Playground */}
                                <div className="max-w-4xl mx-auto mt-6 bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-8 mb-12 shadow-2xl">
                                    <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--text-tertiary)] mb-6 flex items-center gap-2">
                                        <Terminal size={14} className="text-cyan-500" />
                                        Validation Playground
                                    </h4>
                                    <div className="flex gap-4 mb-6">
                                        <input
                                            className="flex-1 px-4 py-3 text-sm border border-[var(--border)] rounded-2xl bg-[var(--background-secondary)] outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all placeholder-[var(--text-tertiary)]"
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
                                        <div className="p-6 bg-[var(--background-secondary)] rounded-2xl border border-[var(--border)] text-xs font-mono max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed custom-scrollbar">
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

            {/* AGENTS TAB */}
            {activeTab === "agents" && (
                <div className="flex-1 bg-[var(--background)] p-8 overflow-y-auto">
                    <div className="max-w-6xl mx-auto">
                        <div className="mb-8">
                            <h4 className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em] mb-2">Agent Management</h4>
                            <h2 className="text-2xl font-bold mb-2">Agent Catalog</h2>
                            <p className="text-[var(--text-secondary)]">Manage agent display names and descriptions. Changes will reflect in the entire platform.</p>
                        </div>

                        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl overflow-hidden shadow-sm">
                            <table className="w-full text-left">
                                <thead className="bg-[var(--background)]/50 text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] border-b border-[var(--border)]">
                                    <tr>
                                        <th className="px-6 py-4">Agent ID</th>
                                        <th className="px-6 py-4">Display Name</th>
                                        <th className="px-6 py-4">Description</th>
                                        <th className="px-6 py-4">Phases</th>
                                        <th className="px-6 py-4">Status</th>
                                        {isAdmin && <th className="px-6 py-4 text-right">Actions</th>}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[var(--border)]">
                                    {agents.map((agent: any) => (
                                        <tr key={agent.agent_id} className="hover:bg-cyan-500/5 transition-colors group">
                                            <td className="px-6 py-4">
                                                <code className="text-xs font-mono text-[var(--text-secondary)] bg-[var(--background)] px-2 py-1 rounded border border-[var(--border)]">
                                                    {agent.agent_id}
                                                </code>
                                            </td>
                                            <td className="px-6 py-4">
                                                {editingAgent?.agent_id === agent.agent_id ? (
                                                    <input
                                                        type="text"
                                                        value={editingAgent.display_name}
                                                        onChange={e => setEditingAgent({ ...editingAgent, display_name: e.target.value })}
                                                        className="w-full px-3 py-2 text-sm border border-[var(--border)] rounded-lg bg-[var(--background-secondary)] outline-none focus:ring-2 focus:ring-cyan-500/50"
                                                    />
                                                ) : (
                                                    <span className="text-sm font-bold">{agent.display_name}</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4">
                                                {editingAgent?.agent_id === agent.agent_id ? (
                                                    <textarea
                                                        value={editingAgent.description}
                                                        onChange={e => setEditingAgent({ ...editingAgent, description: e.target.value })}
                                                        rows={2}
                                                        className="w-full px-3 py-2 text-xs border border-[var(--border)] rounded-lg bg-[var(--background-secondary)] outline-none focus:ring-2 focus:ring-cyan-500/50 resize-none"
                                                    />
                                                ) : (
                                                    <span className="text-xs text-[var(--text-secondary)]">{agent.description}</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-wrap gap-1">
                                                    {(agent.phases || []).map((phase: string) => (
                                                        <span key={phase} className="px-2 py-0.5 rounded-full text-[8px] font-black uppercase tracking-wider bg-cyan-500/10 text-cyan-500 border border-cyan-500/20">
                                                            {phase}
                                                        </span>
                                                    ))}
                                                    {(!agent.phases || agent.phases.length === 0) && (
                                                        <span className="text-[9px] text-[var(--text-tertiary)] italic">No phases</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${agent.is_active ? 'bg-green-500/10 text-green-500' : 'bg-gray-500/10 text-gray-500'}`}>
                                                    {agent.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                            </td>
                                            {isAdmin && (
                                                <td className="px-6 py-4 text-right">
                                                    {editingAgent?.agent_id === agent.agent_id ? (
                                                        <div className="flex gap-2 justify-end">
                                                            <button
                                                                onClick={() => handleUpdateAgent(agent.agent_id, {
                                                                    display_name: editingAgent.display_name,
                                                                    description: editingAgent.description
                                                                })}
                                                                className="px-4 py-1.5 bg-cyan-600 text-white text-[9px] font-black uppercase tracking-wider rounded-lg hover:bg-cyan-500 transition-all"
                                                            >
                                                                <Save size={12} className="inline mr-1" /> Save
                                                            </button>
                                                            <button
                                                                onClick={() => setEditingAgent(null)}
                                                                className="px-4 py-1.5 bg-[var(--border)] text-[var(--text-secondary)] text-[9px] font-black uppercase tracking-wider rounded-lg hover:bg-[var(--border)]/50 transition-all"
                                                            >
                                                                Cancel
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        <button
                                                            onClick={() => setEditingAgent({ ...agent })}
                                                            className="text-xs text-cyan-500 hover:underline font-bold uppercase tracking-wider"
                                                        >
                                                            Edit
                                                        </button>
                                                    )}
                                                </td>
                                            )}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {agents.length === 0 && !loading && (
                            <div className="text-center py-12 text-[var(--text-tertiary)]">
                                <Activity size={48} className="mx-auto mb-4 opacity-30" />
                                <p>No agents found in catalog</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* IDENTITY TAB */}
            {activeTab === "identity" && (
                <div className="flex-1 bg-[var(--background)] p-8 overflow-y-auto">
                    <div className="max-w-6xl mx-auto">
                        <div className="flex justify-between items-end mb-8">
                            <div>
                                <h4 className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em] mb-2">Platform Administration</h4>
                                <h2 className="text-2xl font-bold mb-2">Tenants & Organizations</h2>
                                <p className="text-[var(--text-secondary)]">Create and manage tenants (organizations) with their first MANAGER users.</p>
                            </div>
                            {isAdmin && (
                                <button
                                    className="bg-cyan-600 text-white px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 active:scale-95"
                                    onClick={() => setShowCreateTenantModal(true)}
                                >
                                    <Plus size={16} /> Create Tenant
                                </button>
                            )}
                        </div>

                        {/* TENANTS VIEW */}
                        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl overflow-hidden shadow-sm">
                            <table className="w-full text-left">
                                <thead className="bg-[var(--background)]/50 text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] border-b border-[var(--border)]">
                                    <tr>
                                        <th className="px-6 py-4">Organization Name</th>
                                        <th className="px-6 py-4">Tier</th>
                                        <th className="px-6 py-4 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[var(--border)]">
                                    {tenants.map((t: any) => (
                                        <tr key={t.tenant_id} className="hover:bg-cyan-500/5 transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="font-bold text-sm">{t.display_name || 'Unknown'}</div>
                                                <div className="text-[10px] font-mono opacity-50 mt-0.5">ID: {t.tenant_id}</div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${t.tier === 'ENTERPRISE' ? 'bg-purple-500/10 text-purple-500' :
                                                    t.tier === 'PREMIUM' ? 'bg-cyan-500/10 text-cyan-500' :
                                                        'bg-gray-500/10 text-gray-500'
                                                    }`}>
                                                    {t.tier || 'STANDARD'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    {isAdmin && (
                                                        <button
                                                            className="p-2 text-[var(--text-tertiary)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-lg transition-all"
                                                            title="Edit Display Name"
                                                            onClick={() => {
                                                                setEditingTenant(t);
                                                                setShowEditTenantModal(true);
                                                            }}
                                                        >
                                                            <Edit2 size={16} />
                                                        </button>
                                                    )}
                                                    {isAdmin && t.tenant_id !== user?.tenant_id && (
                                                        <button
                                                            className="p-2 text-[var(--text-tertiary)] hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                                                            title="Delete Tenant"
                                                            onClick={async () => {
                                                                if (confirm(`Permanently remove tenant ${t.display_name}?`)) {
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
                                    <Database size={48} className="opacity-10" />
                                    <p className="font-bold uppercase text-[10px] tracking-widest">No tenants created yet</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ALL USERS TAB */}
            {activeTab === "users" && (
                <div className="flex-1 bg-[var(--background)] p-8 overflow-y-auto">
                    <div className="max-w-7xl mx-auto">
                        <div className="mb-6">
                            <div className="flex justify-between items-end mb-4">
                                <div>
                                    <h4 className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em] mb-2">System Administration</h4>
                                    <h2 className="text-2xl font-bold mb-2">All Users Dashboard</h2>
                                    <p className="text-[var(--text-secondary)]">
                                        View and manage all users across all tenants. Reset passwords and impersonate users for troubleshooting.
                                    </p>
                                </div>
                                <button
                                    onClick={fetchAllUsers}
                                    disabled={isLoadingUsers}
                                    className="bg-cyan-600 text-white px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 active:scale-95 disabled:opacity-50"
                                >
                                    <RefreshCw size={16} className={isLoadingUsers ? "animate-spin" : ""} /> Refresh
                                </button>
                            </div>

                            {/* Filters */}
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div>
                                    <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Filter by Tenant</label>
                                    <input
                                        type="text"
                                        className="w-full px-4 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                                        placeholder="Search tenant..."
                                        value={filterTenant}
                                        onChange={e => setFilterTenant(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Filter by Role</label>
                                    <select
                                        className="w-full px-4 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                                        value={filterRole}
                                        onChange={e => setFilterRole(e.target.value)}
                                    >
                                        <option value="">All Roles</option>
                                        <option value="ADMIN">ADMIN</option>
                                        <option value="MANAGER">MANAGER</option>
                                        <option value="COLLABORATOR">COLLABORATOR</option>
                                        <option value="VIEWER">VIEWER</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Search User</label>
                                    <input
                                        type="text"
                                        className="w-full px-4 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                                        placeholder="Username or email..."
                                        value={filterSearch}
                                        onChange={e => setFilterSearch(e.target.value)}
                                    />
                                </div>
                            </div>
                        </div>

                        {isLoadingUsers ? (
                            <div className="text-center p-12 text-[var(--text-secondary)]">
                                <Users size={48} className="mx-auto opacity-10 mb-4 animate-pulse" />
                                <p className="font-bold uppercase text-[10px] tracking-widest">Loading users...</p>
                            </div>
                        ) : filteredUsers.length === 0 ? (
                            <div className="text-center p-12 flex flex-col items-center gap-4 bg-[var(--surface)] rounded-2xl border border-[var(--border)]">
                                <Users size={48} className="opacity-10" />
                                <p className="font-bold uppercase text-[10px] tracking-widest text-[var(--text-tertiary)]">No users found</p>
                            </div>
                        ) : (
                            <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl overflow-hidden shadow-sm">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-left">
                                        <thead className="bg-[var(--background)]/50 text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] border-b border-[var(--border)]">
                                            <tr>
                                                <th className="px-6 py-4">Username</th>
                                                <th className="px-6 py-4">Email</th>
                                                <th className="px-6 py-4">Organization</th>
                                                <th className="px-6 py-4">Role</th>
                                                <th className="px-6 py-4">Status</th>
                                                <th className="px-6 py-4 text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-[var(--border)]">
                                            {filteredUsers.map((u: any) => (
                                                <tr key={u.user_id} className="hover:bg-cyan-500/5 transition-colors group">
                                                    <td className="px-6 py-4">
                                                        <div className="font-bold text-sm">{u.username}</div>
                                                        <div className="text-[10px] font-mono opacity-50 mt-0.5">{u.user_id.substring(0, 8)}...</div>
                                                    </td>
                                                    <td className="px-6 py-4 text-sm">{u.email}</td>
                                                    <td className="px-6 py-4">
                                                        <div className="text-sm">{u.tenant_display_name || "Unknown"}</div>
                                                        <div className="text-[10px] font-mono opacity-50 mt-0.5">{u.tenant_id.substring(0, 8)}...</div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${u.role === 'ADMIN' ? 'bg-purple-500/10 text-purple-500' :
                                                            u.role === 'MANAGER' ? 'bg-cyan-500/10 text-cyan-500' :
                                                                u.role === 'COLLABORATOR' ? 'bg-blue-500/10 text-blue-500' :
                                                                    'bg-gray-500/10 text-gray-500'
                                                            }`}>
                                                            {u.role}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${u.is_active ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                                                            }`}>
                                                            {u.is_active ? 'ACTIVE' : 'INACTIVE'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <div className="flex justify-end gap-2">
                                                            <button
                                                                className="p-2 text-[var(--text-tertiary)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-lg transition-all"
                                                                title="Reset Password"
                                                                onClick={() => {
                                                                    setResetPasswordUser(u);
                                                                    setShowResetPasswordModal(true);
                                                                }}
                                                            >
                                                                <Key size={16} />
                                                            </button>
                                                            {u.role !== 'ADMIN' && (
                                                                <button
                                                                    className="p-2 text-[var(--text-tertiary)] hover:text-indigo-500 hover:bg-indigo-500/10 rounded-lg transition-all"
                                                                    title="Impersonate (Ghost Mode)"
                                                                    onClick={() => handleImpersonate(u.user_id, u.username)}
                                                                >
                                                                    <Eye size={16} />
                                                                </button>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <div className="p-4 bg-[var(--background)]/50 border-t border-[var(--border)] text-center text-[10px] text-[var(--text-tertiary)] uppercase font-black tracking-widest">
                                    Showing {filteredUsers.length} of {allUsers.length} users
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* PROCESS LOCKS TAB */}
            {activeTab === "locks" && (
                <div className="flex-1 bg-[var(--background)] p-8 overflow-y-auto">
                    <div className="max-w-6xl mx-auto">
                        <div className="mb-6">
                            <div className="flex justify-between items-end mb-4">
                                <div>
                                    <h4 className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em] mb-2">System Administration</h4>
                                    <h2 className="text-2xl font-bold mb-2">Process Lock Management</h2>
                                    <p className="text-[var(--text-secondary)]">
                                        View and manage active process locks across all projects. Force-release stuck locks when needed.
                                    </p>
                                </div>
                                <button
                                    onClick={fetchProcessLocks}
                                    disabled={isLoadingLocks}
                                    className="bg-cyan-600 text-white px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 active:scale-95 disabled:opacity-50"
                                >
                                    <RefreshCw size={16} className={isLoadingLocks ? "animate-spin" : ""} /> Refresh
                                </button>
                            </div>
                        </div>

                        {isLoadingLocks ? (
                            <div className="text-center p-12 text-[var(--text-secondary)]">
                                <Lock size={48} className="mx-auto opacity-10 mb-4 animate-pulse" />
                                <p className="font-bold uppercase text-[10px] tracking-widest">Loading locks...</p>
                            </div>
                        ) : processLocks.length === 0 ? (
                            <div className="text-center p-12 flex flex-col items-center gap-4 bg-[var(--surface)] rounded-2xl border border-[var(--border)]">
                                <div className="p-4 bg-green-500/10 rounded-full">
                                    <Lock size={48} className="text-green-500" />
                                </div>
                                <div>
                                    <p className="font-bold text-lg mb-1">No Active Locks</p>
                                    <p className="text-[var(--text-secondary)] text-sm">All processes are currently free. This is a healthy state.</p>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-[var(--surface)] rounded-2xl border border-[var(--border)] overflow-hidden">
                                <table className="w-full">
                                    <thead>
                                        <tr className="bg-gradient-to-r from-cyan-500/10 to-transparent border-b border-[var(--border)]">
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-[var(--text-secondary)] uppercase tracking-widest">Process</th>
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-[var(--text-secondary)] uppercase tracking-widest">Project ID</th>
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-[var(--text-secondary)] uppercase tracking-widest">Locked By</th>
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-[var(--text-secondary)] uppercase tracking-widest">Expires At</th>
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-[var(--text-secondary)] uppercase tracking-widest">Status</th>
                                            <th className="px-6 py-4 text-center text-[10px] font-black text-[var(--text-secondary)] uppercase tracking-widest">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-[var(--border)]">
                                        {processLocks.map((lock) => {
                                            const isExpired = new Date(lock.expires_at) < new Date();
                                            const processNames: Record<string, string> = {
                                                'triage': 'Triage',
                                                'drafting': 'Drafting',
                                                'refinement': 'Refinement',
                                                'certification': 'Certification',
                                                'governance': 'Governance'
                                            };
                                            return (
                                                <tr key={lock.lock_id} className="hover:bg-[var(--text-primary)]/5 transition-colors">
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center gap-2">
                                                            <Terminal size={16} className="text-cyan-500" />
                                                            <span className="font-semibold">{processNames[lock.process_type] || lock.process_type}</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <code className="text-[10px] bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded font-mono">
                                                            {lock.project_id.substring(0, 8)}...
                                                        </code>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center gap-2">
                                                            <Users size={14} className="text-gray-400" />
                                                            <span className="font-medium">{lock.locked_by_username}</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="text-sm">
                                                            <div className={isExpired ? "text-red-500 font-semibold" : "text-[var(--text-secondary)]"}>
                                                                {new Date(lock.expires_at).toLocaleString()}
                                                            </div>
                                                            {isExpired && (
                                                                <div className="text-[10px] text-red-400 uppercase tracking-wider mt-1">
                                                                    ⚠️ Expired
                                                                </div>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-2 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider ${lock.status === 'active'
                                                            ? 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400'
                                                            : 'bg-gray-500/20 text-gray-600 dark:text-gray-400'
                                                            }`}>
                                                            {lock.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-center">
                                                        {lock.status === 'active' && (
                                                            <button
                                                                onClick={() => handleForceReleaseLock(lock.lock_id, lock.project_id, lock.process_type)}
                                                                className="bg-red-600 hover:bg-red-500 text-white px-3 py-1.5 rounded-lg text-[9px] font-bold uppercase tracking-wider transition-all active:scale-95 flex items-center gap-1.5 mx-auto"
                                                            >
                                                                <X size={12} />
                                                                Force Release
                                                            </button>
                                                        )}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
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
                                    <h4 className="text-[10px] font-black text-cyan-500 uppercase tracking-[0.3em] mb-2">Global Capabilities</h4>
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
                    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
                        <div className="bg-[var(--surface)] text-[var(--text-primary)] rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden border border-[var(--border)] animate-in fade-in zoom-in duration-200">
                            <div className="p-6 border-b border-[var(--border)] flex justify-between items-center bg-gradient-to-r from-cyan-500/10 to-transparent">
                                <div>
                                    <h3 className="text-xl font-bold">Register New Technology</h3>
                                    <p className="text-xs text-[var(--text-tertiary)] mt-1">Add support for a new {activeTab === "origins" ? "Origin" : "Destination"} in the catalog</p>
                                </div>
                                <button onClick={() => setShowAddModal(false)} className="p-2 hover:bg-[var(--background)] rounded-full transition-colors text-[var(--text-tertiary)]">
                                    <X size={24} />
                                </button>
                            </div>

                            <div className="p-8 space-y-6">
                                <div className="grid grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)]">Display Name</label>
                                        <input
                                            className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all font-bold"
                                            placeholder="e.g. Snowflake Advanced"
                                            value={newCartridge.name}
                                            onChange={e => setNewCartridge({ ...newCartridge, name: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)]">Technical ID (Key)</label>
                                        <input
                                            className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all font-mono"
                                            placeholder="e.g. snowflake"
                                            value={newCartridge.subtype}
                                            onChange={e => setNewCartridge({ ...newCartridge, subtype: e.target.value.toLowerCase() })}
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)]">Version</label>
                                        <input
                                            className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                                            placeholder="e.g. v1.2"
                                            value={newCartridge.version}
                                            onChange={e => setNewCartridge({ ...newCartridge, version: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)]">Capability Role</label>
                                        <select
                                            disabled // Tied to active tab for sanity
                                            className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-xs font-black uppercase tracking-widest outline-none opacity-50"
                                            value={activeTab === "origins" ? "origin" : "destination"}
                                        >
                                            <option value="origin">ORIGIN (Source)</option>
                                            <option value="destination">DESTINATION (Target)</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)]">Engine Configuration (JSON)</label>
                                    <textarea
                                        className="w-full h-40 px-4 py-4 rounded-3xl border border-[var(--border)] bg-[var(--background)] text-xs font-mono outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all resize-none"
                                        placeholder='{"driver": "...", "dialect": "..."}'
                                        value={newCartridge.config}
                                        onChange={e => setNewCartridge({ ...newCartridge, config: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="p-6 bg-[var(--background)]/50 border-t border-[var(--border)] flex justify-end gap-3">
                                <button
                                    onClick={() => setShowAddModal(false)}
                                    className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-[var(--surface)] transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAdd}
                                    className="px-8 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-xl shadow-cyan-600/20 active:scale-95 disabled:opacity-50"
                                    disabled={!newCartridge.name || !newCartridge.subtype}
                                >
                                    Register Technology
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
            {/* IMPORT MODAL */}
            {showImportModal && (
                <div className="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4 backdrop-blur-md">
                    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
                        <div className="p-6 border-b border-[var(--border)] flex justify-between items-center bg-gradient-to-r from-indigo-500/10 to-transparent">
                            <div>
                                <h3 className="text-lg font-bold">Import Optimized Prompt</h3>
                                <p className="text-xs text-[var(--text-tertiary)] mt-1">Select the laboratory path for {selectedPromptId}</p>
                            </div>
                            <button onClick={() => setShowImportModal(false)} className="p-2 hover:bg-[var(--background)] rounded-full transition-colors text-[var(--text-tertiary)]">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-8 space-y-6">
                            <div className="p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-2xl flex items-start gap-4">
                                <Activity size={20} className="text-indigo-500 shrink-0 mt-1" />
                                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                                    The laboratory expected structure is: <br />
                                    <code>{labPath}/{selectedPromptId}/prompt_v2.md</code>
                                </p>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Base Lab Path</label>
                                <div className="flex gap-2">
                                    <input
                                        className="flex-1 px-4 py-3 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500/50"
                                        value={labPath}
                                        onChange={e => setLabPath(e.target.value)}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="p-6 bg-[var(--background)]/50 border-t border-[var(--border)] flex justify-end gap-3">
                            <button
                                onClick={() => setShowImportModal(false)}
                                className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-[var(--surface)] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleImportLab}
                                className="px-8 py-2.5 bg-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
                            >
                                Run Import
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* CREATE TENANT MODAL */}
            {showCreateTenantModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
                    <div className="bg-[var(--surface)] text-[var(--text-primary)] rounded-3xl shadow-2xl w-full max-w-md overflow-hidden border border-[var(--border)] animate-in fade-in zoom-in duration-200">
                        <div className="p-6 border-b border-[var(--border)] flex justify-between items-center bg-gradient-to-r from-cyan-500/10 to-transparent">
                            <div>
                                <h3 className="text-xl font-bold">Create New Tenant</h3>
                                <p className="text-xs text-[var(--text-tertiary)] mt-1">Create organization with first MANAGER user</p>
                            </div>
                            <button onClick={() => setShowCreateTenantModal(false)} className="p-2 hover:bg-[var(--background)] rounded-full transition-colors text-[var(--text-tertiary)]">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="p-8 space-y-4">
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Organization Name *</label>
                                <input
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all font-bold"
                                    placeholder="e.g. Acme Corporation"
                                    value={newTenantData.display_name}
                                    onChange={e => setNewTenantData({ ...newTenantData, display_name: e.target.value })}
                                />
                                <p className="text-[9px] text-[var(--text-tertiary)] mt-1 ml-1">Friendly display name for the organization</p>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Tier</label>
                                <select
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all font-bold"
                                    value={newTenantData.tier}
                                    onChange={e => setNewTenantData({ ...newTenantData, tier: e.target.value })}
                                >
                                    <option value="STANDARD">STANDARD</option>
                                    <option value="PREMIUM">PREMIUM</option>
                                    <option value="ENTERPRISE">ENTERPRISE</option>
                                </select>
                                <p className="text-[9px] text-[var(--text-tertiary)] mt-1 ml-1">Subscription tier for this organization</p>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Manager Username *</label>
                                <input
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all font-bold"
                                    placeholder="e.g. jsmith"
                                    value={newTenantData.username}
                                    onChange={e => setNewTenantData({ ...newTenantData, username: e.target.value })}
                                />
                                <p className="text-[9px] text-[var(--text-tertiary)] mt-1 ml-1">Login username for the first manager</p>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Manager Email *</label>
                                <input
                                    type="email"
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                                    placeholder="manager@company.com"
                                    value={newTenantData.email}
                                    onChange={e => setNewTenantData({ ...newTenantData, email: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Manager Password *</label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        className="w-full px-4 py-3 pr-12 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all font-mono"
                                        placeholder="Strong password"
                                        value={newTenantData.password}
                                        onChange={e => setNewTenantData({ ...newTenantData, password: e.target.value })}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                                        title={showPassword ? "Hide password" : "Show password"}
                                    >
                                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                            </div>
                            <div className="p-4 bg-cyan-500/5 rounded-2xl border border-cyan-500/10">
                                <p className="text-[10px] text-cyan-500 font-bold uppercase tracking-tight">
                                    ℹ️ First user will have MANAGER role with full tenant access
                                </p>
                            </div>
                        </div>

                        <div className="p-6 bg-[var(--background)]/50 border-t border-[var(--border)] flex justify-end gap-3">
                            <button
                                onClick={() => setShowCreateTenantModal(false)}
                                className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-[var(--surface)] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreateTenant}
                                className="px-8 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-xl shadow-cyan-600/20 active:scale-95 disabled:opacity-50"
                                disabled={isCreating || !newTenantData.display_name || !newTenantData.username || !newTenantData.email || !newTenantData.password}
                            >
                                {isCreating ? "Creating..." : "Create Tenant"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* EDIT TENANT MODAL */}
            {showEditTenantModal && editingTenant && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
                    <div className="bg-[var(--surface)] text-[var(--text-primary)] rounded-3xl shadow-2xl w-full max-w-md overflow-hidden border border-[var(--border)] animate-in fade-in zoom-in duration-200">
                        <div className="p-6 border-b border-[var(--border)] flex justify-between items-center bg-gradient-to-r from-indigo-500/10 to-transparent">
                            <div>
                                <h3 className="text-xl font-bold">Edit Tenant</h3>
                                <p className="text-xs text-[var(--text-tertiary)] mt-1">Update organization display name</p>
                            </div>
                            <button onClick={() => { setShowEditTenantModal(false); setEditingTenant(null); }} className="p-2 hover:bg-[var(--background)] rounded-full transition-colors text-[var(--text-tertiary)]">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="p-8 space-y-4">
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Tenant ID</label>
                                <input
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)]/50 text-sm outline-none font-mono text-[var(--text-tertiary)] cursor-not-allowed"
                                    value={editingTenant.tenant_id}
                                    disabled
                                />
                                <p className="text-[9px] text-[var(--text-tertiary)] mt-1 ml-1">Unique identifier (UUID)</p>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Display Name *</label>
                                <input
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-bold"
                                    placeholder="e.g. Acme Corporation"
                                    value={editingTenant.display_name}
                                    onChange={e => setEditingTenant({ ...editingTenant, display_name: e.target.value })}
                                />
                                <p className="text-[9px] text-[var(--text-tertiary)] mt-1 ml-1">Friendly name shown in admin panel</p>
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Tier *</label>
                                <select
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all font-bold"
                                    value={editingTenant.tier}
                                    onChange={e => setEditingTenant({ ...editingTenant, tier: e.target.value })}
                                >
                                    <option value="STANDARD">STANDARD</option>
                                    <option value="PREMIUM">PREMIUM</option>
                                    <option value="ENTERPRISE">ENTERPRISE</option>
                                </select>
                                <p className="text-[9px] text-[var(--text-tertiary)] mt-1 ml-1">Subscription tier for this organization</p>
                            </div>
                        </div>

                        <div className="p-6 bg-[var(--background)]/50 border-t border-[var(--border)] flex justify-end gap-3">
                            <button
                                onClick={() => { setShowEditTenantModal(false); setEditingTenant(null); }}
                                className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-[var(--surface)] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleUpdateTenant}
                                className="px-8 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-xl shadow-indigo-600/20 active:scale-95 disabled:opacity-50"
                                disabled={isUpdating || !editingTenant.display_name}
                            >
                                {isUpdating ? "Updating..." : "Update Tenant"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* INVITE MODAL */}
            {showInviteModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
                    <div className="bg-[var(--surface)] text-[var(--text-primary)] rounded-3xl shadow-2xl w-full max-w-md overflow-hidden border border-[var(--border)] animate-in fade-in zoom-in duration-200">
                        <div className="p-6 border-b border-[var(--border)] flex justify-between items-center bg-gradient-to-r from-cyan-500/10 to-transparent">
                            <div>
                                <h3 className="text-xl font-bold">Invite New User</h3>
                                <p className="text-xs text-[var(--text-tertiary)] mt-1">Credentials will be sent via email</p>
                            </div>
                            <button onClick={() => setShowInviteModal(false)} className="p-2 hover:bg-[var(--background)] rounded-full transition-colors text-[var(--text-tertiary)]">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="p-8 space-y-6">
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Username</label>
                                    <input
                                        className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all font-bold"
                                        placeholder="e.g. jsmith"
                                        value={inviteData.username}
                                        onChange={e => setInviteData({ ...inviteData, username: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Email Address</label>
                                    <input
                                        type="email"
                                        className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                                        placeholder="user@enterprise.com"
                                        value={inviteData.email}
                                        onChange={e => setInviteData({ ...inviteData, email: e.target.value })}
                                    />
                                </div>
                                <div className="p-4 bg-cyan-500/5 rounded-2xl border border-cyan-500/10 mb-4">
                                    <p className="text-[10px] text-cyan-500 font-bold uppercase tracking-tight text-center">
                                        System will automatically create a new Client record for this user.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 bg-[var(--background)]/50 border-t border-[var(--border)] flex justify-end gap-3">
                            <button
                                onClick={() => setShowInviteModal(false)}
                                className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-[var(--surface)] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleInviteUser}
                                className="px-8 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-xl shadow-cyan-600/20 active:scale-95 disabled:opacity-50"
                                disabled={isInviting || !inviteData.username || !inviteData.email}
                            >
                                {isInviting ? "Sending..." : "Send Invitation"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* RESET PASSWORD MODAL */}
            {showResetPasswordModal && resetPasswordUser && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-md">
                    <div className="bg-[var(--surface)] text-[var(--text-primary)] rounded-3xl shadow-2xl w-full max-w-md overflow-hidden border border-[var(--border)] animate-in fade-in zoom-in duration-200">
                        <div className="p-6 border-b border-[var(--border)] flex justify-between items-center bg-gradient-to-r from-orange-500/10 to-transparent">
                            <div>
                                <h3 className="text-xl font-bold">Reset Password</h3>
                                <p className="text-xs text-[var(--text-tertiary)] mt-1">Set new password for {resetPasswordUser.username}</p>
                            </div>
                            <button
                                onClick={() => {
                                    setShowResetPasswordModal(false);
                                    setResetPasswordUser(null);
                                    setNewPassword("");
                                }}
                                className="p-2 hover:bg-[var(--background)] rounded-full transition-colors text-[var(--text-tertiary)]"
                            >
                                <X size={24} />
                            </button>
                        </div>

                        <div className="p-8 space-y-4">
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">User</label>
                                <input
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)]/50 text-sm outline-none font-bold text-[var(--text-tertiary)] cursor-not-allowed"
                                    value={`${resetPasswordUser.username} (${resetPasswordUser.email})`}
                                    disabled
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Organization</label>
                                <input
                                    className="w-full px-4 py-3 rounded-2xl border border-[var(--border)] bg-[var(--background)]/50 text-sm outline-none font-mono text-[var(--text-tertiary)] cursor-not-allowed"
                                    value={resetPasswordUser.tenant_display_name || "Unknown"}
                                    disabled
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-2">New Password *</label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        className="w-full px-4 py-3 pr-12 rounded-2xl border border-[var(--border)] bg-[var(--background)] text-sm outline-none focus:ring-2 focus:ring-orange-500/50 transition-all font-mono"
                                        placeholder="Minimum 8 characters"
                                        value={newPassword}
                                        onChange={e => setNewPassword(e.target.value)}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
                                        title={showPassword ? "Hide password" : "Show password"}
                                    >
                                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                                <p className="text-[9px] text-[var(--text-tertiary)] mt-1 ml-1">User will be able to login with this new password immediately</p>
                            </div>
                        </div>

                        <div className="p-6 bg-[var(--background)]/50 border-t border-[var(--border)] flex justify-end gap-3">
                            <button
                                onClick={() => {
                                    setShowResetPasswordModal(false);
                                    setResetPasswordUser(null);
                                    setNewPassword("");
                                }}
                                className="px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-[var(--surface)] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleResetPassword}
                                className="px-8 py-2.5 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all shadow-xl shadow-orange-600/20 active:scale-95 disabled:opacity-50"
                                disabled={isResettingPassword || !newPassword || newPassword.length < 8}
                            >
                                {isResettingPassword ? "Resetting..." : "Reset Password"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div >
    );
}
