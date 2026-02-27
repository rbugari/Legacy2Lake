"use client";

import { useState, useEffect } from "react";
import { fetchWithAuth } from "../../lib/auth-client";
import {
    Bot,
    Save,
    RefreshCw,
    Sparkles,
    CheckCircle,
    Cpu,
    Globe,
    Zap,
    MessageSquareCode,
    Search,
    Maximize2,
    Minimize2
} from "lucide-react";
import { getAgentDisplayName, getAgentDescription, AGENT_METADATA } from "../../lib/constants";

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

export default function StrategicIntelligenceHub() {
    const [matrix, setMatrix] = useState<MatrixEntry[]>([]);
    const [catalog, setCatalog] = useState<Model[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Intelligence Hub State
    const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

    // UI State
    const [searchTerm, setSearchTerm] = useState("");
    const [globalProvider, setGlobalProvider] = useState("");
    const [globalModel, setGlobalModel] = useState("");
    const [isMaximized, setIsMaximized] = useState(false);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [matrixData, catalogData, vaultData] = await Promise.all([
                fetchWithAuth("system/matrix").then(res => res.json()),
                fetchWithAuth("system/catalog").then(res => res.json()),
                fetchWithAuth("system/vault").then(res => res.json())
            ]);

            const matrixList = matrixData.matrix || [];

            // Only keep active agents from metadata to avoid "un millon de agentes"
            const filteredMatrix = matrixList.filter((m: any) =>
                m.agent === 'agent-helper' ||
                (AGENT_METADATA[m.agent.toLowerCase()]?.status === 'active')
            );
            setMatrix(filteredMatrix);

            const activeProviders = (vaultData.credentials || [])
                .filter((c: any) => c.is_active)
                .map((c: any) => c.provider_name.toLowerCase());

            const mappedCatalog = (catalogData.catalog || [])
                .filter((m: any) => activeProviders.includes(m.provider.toLowerCase()))
                .map((m: any) => ({
                    id: m.model_id,
                    provider: m.provider,
                    label: m.label
                }));
            setCatalog(mappedCatalog);

            // Use configured model from first agent in matrix as default
            const providers = Array.from(new Set(mappedCatalog.map((m: any) => m.provider))) as string[];
            if (filteredMatrix.length > 0 && providers.length > 0) {
                const firstAgent = filteredMatrix[0];
                const configuredProvider = firstAgent.provider;
                const configuredModel = firstAgent.model;

                // Check if configured values exist in catalog
                if (providers.includes(configuredProvider)) {
                    setGlobalProvider(configuredProvider);
                    const modelExists = mappedCatalog.find((m: any) => m.id === configuredModel);
                    if (modelExists) {
                        setGlobalModel(configuredModel);
                    } else {
                        // Fallback to first model of provider
                        const firstM = mappedCatalog.find((m: any) => m.provider === configuredProvider);
                        if (firstM) setGlobalModel(firstM.id);
                    }
                } else {
                    // Fallback to first available provider
                    const firstP = providers[0];
                    setGlobalProvider(firstP);
                    const firstM = mappedCatalog.find((m: any) => m.provider === firstP);
                    if (firstM) setGlobalModel(firstM.id);
                }
            } else if (providers.length > 0) {
                // No matrix entries, use first provider
                const firstP = providers[0];
                setGlobalProvider(firstP);
                const firstM = mappedCatalog.find((m: any) => m.provider === firstP);
                if (firstM) setGlobalModel(firstM.id);
            }

            if (filteredMatrix.length > 0) {
                const firstAgentId = filteredMatrix[0].agent;
                setSelectedAgent(firstAgentId);
            }

            setLoading(false);
        } catch (e) {
            console.error("Failed to load hub data", e);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleAgentSelect = (agentId: string) => {
        setSelectedAgent(agentId);
    };

    const handleMatrixChange = (agentId: string, field: 'provider' | 'model', value: string) => {
        setMatrix(prev => prev.map(entry => {
            if (entry.agent === agentId) {
                const updated = { ...entry, [field]: value };
                if (field === 'provider') {
                    const firstModel = catalog.find(m => m.provider === value);
                    updated.model = firstModel ? firstModel.id : "";
                }
                return updated;
            }
            return entry;
        }));
    };

    const applyToAllAgents = () => {
        if (!globalProvider || !globalModel) return;
        setMatrix(prev => prev.map(entry => {
            if (entry.agent === 'agent-helper') return entry;
            return { ...entry, provider: globalProvider, model: globalModel };
        }));
    };

    const setAsHelper = () => {
        if (!globalProvider || !globalModel) return;
        setMatrix(prev => {
            const exists = prev.find(m => m.agent === 'agent-helper');
            if (exists) {
                return prev.map(m => m.agent === 'agent-helper' ? { ...m, provider: globalProvider, model: globalModel } : m);
            }
            return [...prev, { agent: 'agent-helper', provider: globalProvider, model: globalModel }];
        });
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const updates = matrix.map(entry =>
                fetchWithAuth("system/matrix", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(entry)
                })
            );
            await Promise.all(updates);
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (e) {
            console.error("Failed to save matrix", e);
            alert("Could not save configuration");
        } finally {
            setSaving(false);
        }
    };

    const availableProviders = Array.from(new Set(catalog.map(m => m.provider)));
    const selectedMatrixEntry = matrix.find(m => m.agent === selectedAgent);
    const helperModel = matrix.find(m => m.agent === 'agent-helper');

    if (loading) return (
        <div className="flex flex-col items-center justify-center p-20 space-y-4">
            <RefreshCw size={32} className="animate-spin text-blue-500" />
            <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">Initializing Strategic Intelligence Hub...</p>
        </div>
    );

    return (
        <div className={`space-y-6 transition-all duration-300 ${isMaximized ? "fixed inset-0 z-[100] bg-[#0B0F19] flex items-center justify-center" : ""}`}>
            <div className={isMaximized ? "w-[90%] h-[90%] overflow-y-auto p-6" : "w-full"}>
                {/* Top Toolbar: Global Preview Params */}
                <div className="bg-slate-900/50 border border-white/5 p-6 rounded-2xl flex flex-wrap items-center justify-between gap-6 shadow-xl">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
                            <Globe size={24} />
                        </div>
                        <div>
                            <h3 className="text-sm font-black uppercase tracking-widest text-white">Hub Preview Context</h3>
                            <p className="text-[10px] text-gray-500 font-bold uppercase mt-1">Manage model assignments</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-6 border-l border-white/5 pl-6 flex-1">
                        <div className="space-y-2">
                            <label className="text-[9px] font-black uppercase tracking-widest text-gray-400 ml-1 flex items-center gap-2">
                                <Sparkles size={10} className="text-blue-400" />
                                Quick Global Strategy
                            </label>
                            <div className="flex items-center gap-3">
                                <select
                                    value={globalProvider}
                                    onChange={(e) => {
                                        setGlobalProvider(e.target.value);
                                        const first = catalog.find(m => m.provider === e.target.value);
                                        if (first) setGlobalModel(first.id);
                                    }}
                                    className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-[10px] font-bold text-gray-200 uppercase outline-none focus:ring-1 focus:ring-blue-500/30 w-[120px]"
                                >
                                    {availableProviders.map(p => <option key={p} value={p} className="bg-slate-800 text-white">{p.toUpperCase()}</option>)}
                                </select>
                                <select
                                    value={globalModel}
                                    onChange={(e) => setGlobalModel(e.target.value)}
                                    className="bg-slate-800 border border-white/10 rounded-xl px-3 py-2 text-[10px] font-bold text-gray-200 uppercase outline-none max-w-[150px] truncate focus:ring-1 focus:ring-blue-500/30"
                                >
                                    {catalog.filter(m => m.provider === globalProvider).map(m => (
                                        <option key={m.id} value={m.id} className="bg-slate-800 text-white">{m.label}</option>
                                    ))}
                                </select>

                                <div className="flex gap-1">
                                    <button
                                        onClick={applyToAllAgents}
                                        title="Apply this model to all agents"
                                        className="p-2 bg-white/5 hover:bg-blue-600/20 border border-white/10 rounded-lg text-gray-400 hover:text-blue-400 transition-all active:scale-90"
                                    >
                                        <Zap size={14} />
                                    </button>
                                    <button
                                        onClick={setAsHelper}
                                        title="Set as Default Workspace Helper"
                                        className={`p-2 border rounded-lg transition-all active:scale-90 ${helperModel?.model === globalModel
                                            ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400"
                                            : "bg-white/5 hover:bg-emerald-600/20 border-white/10 text-gray-400 hover:text-emerald-400"
                                            }`}
                                    >
                                        <Cpu size={14} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col items-end gap-2 ml-auto">
                        {helperModel && (
                            <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/20 rounded-full">
                                <span className="text-[8px] font-black text-emerald-500 uppercase tracking-widest">Active Helper:</span>
                                <span className="text-[8px] font-bold text-gray-400 uppercase">{helperModel.model}</span>
                            </div>
                        )}
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className={`px-8 py-3 rounded-xl text-xs font-black uppercase tracking-widest flex items-center gap-3 transition-all shadow-lg ${saved
                                ? "bg-emerald-600 text-white shadow-emerald-500/20"
                                : "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-500/20 active:scale-95 disabled:opacity-50"
                                }`}
                        >
                            {saving ? <RefreshCw className="animate-spin" size={16} /> : saved ? <CheckCircle size={16} /> : <Save size={16} />}
                            {saving ? "Saving Hub" : saved ? "All Policies Applied" : "Save Strategy"}
                        </button>
                        <button
                            onClick={() => setIsMaximized(!isMaximized)}
                            className="p-3 rounded-xl bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 transition-all shadow-lg"
                            title={isMaximized ? "Exit Full Screen" : "Maximize Hub"}
                        >
                            {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                        </button>
                    </div>
                </div>

                {/* Main Hub Content */}
                <div className={`grid grid-cols-1 md:grid-cols-12 gap-6 ${isMaximized ? "h-full" : "h-[calc(100vh-theme(spacing.80))] min-h-[600px]"}`}>
                    {/* 1. Agent & Model Sidebar */}
                    <div className="col-span-4 flex flex-col gap-4">
                        <div className="bg-slate-900/30 border border-white/5 rounded-2xl p-4 flex-1 flex flex-col min-h-0">
                            <div className="flex items-center gap-2 mb-4 px-2">
                                <Bot size={16} className="text-blue-400" />
                                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Agent Strategy Canvas</span>
                            </div>

                            <div className="relative mb-4">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" size={14} />
                                <input
                                    type="text"
                                    placeholder="Search agents..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full bg-black/40 border border-white/5 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-gray-700 outline-none focus:border-blue-500/50"
                                />
                            </div>

                            <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-1">
                                {matrix
                                    .filter(m => m.agent !== 'agent-helper')
                                    .filter(m => getAgentDisplayName(m.agent).toLowerCase().includes(searchTerm.toLowerCase()))
                                    .map(entry => (
                                        <div
                                            key={entry.agent}
                                            onClick={() => handleAgentSelect(entry.agent)}
                                            className={`p-4 rounded-2xl border cursor-pointer transition-all group ${selectedAgent === entry.agent
                                                ? "bg-blue-600/10 border-blue-500/50 shadow-lg shadow-blue-500/5"
                                                : "bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/20"
                                                }`}
                                        >
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="flex items-center gap-3">
                                                    <div className={`p-2 rounded-lg transition-colors ${selectedAgent === entry.agent ? "bg-blue-500 text-white" : "bg-black/40 text-gray-500 group-hover:text-blue-400"
                                                        }`}>
                                                        <Bot size={16} />
                                                    </div>
                                                    <span className={`text-[11px] font-black uppercase tracking-wider ${selectedAgent === entry.agent ? "text-blue-400" : "text-gray-300"
                                                        }`}>
                                                        {getAgentDisplayName(entry.agent)}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Inline Matrix Controls */}
                                            <div className="grid grid-cols-2 gap-2 mt-2" onClick={e => e.stopPropagation()}>
                                                <div className="space-y-1">
                                                    <label className="text-[8px] font-black text-gray-600 uppercase tracking-widest ml-1">Provider</label>
                                                    <select
                                                        value={entry.provider}
                                                        onChange={(e) => handleMatrixChange(entry.agent, 'provider', e.target.value)}
                                                        className="w-full bg-slate-800 border border-white/10 rounded-lg px-2 py-1 text-[10px] text-gray-200 hover:text-white outline-none focus:ring-1 focus:ring-blue-500/50"
                                                    >
                                                        {availableProviders.map(p => <option key={p} value={p} className="bg-slate-800 text-white">{p.toUpperCase()}</option>)}
                                                    </select>
                                                </div>
                                                <div className="space-y-1">
                                                    <label className="text-[8px] font-black text-gray-600 uppercase tracking-widest ml-1">Model</label>
                                                    <select
                                                        value={entry.model}
                                                        onChange={(e) => handleMatrixChange(entry.agent, 'model', e.target.value)}
                                                        className="w-full bg-slate-800 border border-white/10 rounded-lg px-2 py-1 text-[10px] text-gray-200 hover:text-white outline-none truncate focus:ring-1 focus:ring-blue-500/50"
                                                    >
                                                        {catalog.filter(m => m.provider === entry.provider).map(m => (
                                                            <option key={m.id} value={m.id} className="bg-slate-800 text-white">{m.label}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                            </div>
                        </div>
                    </div>

                    {/* 2. Intelligence Explorer Panel (Simplified) */}
                    <div className="col-span-8 flex flex-col gap-4">
                        <div className="bg-slate-900/30 border border-white/5 rounded-3xl flex-1 flex flex-col min-h-0 overflow-hidden shadow-2xl">
                            {/* Panel Header */}
                            <div className="px-8 py-4 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-500">
                                        <MessageSquareCode size={20} />
                                    </div>
                                    <div>
                                        <h3 className="text-xs font-black uppercase tracking-widest text-white">{selectedAgent ? getAgentDisplayName(selectedAgent) : 'Agent Details'}</h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">Assigned Model:</span>
                                            <span className="text-[9px] font-black text-blue-400 uppercase tracking-widest">
                                                {selectedMatrixEntry?.provider || 'NONE'} / {selectedMatrixEntry?.model || 'NONE'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Prompt Display (Now Just Abstract Description) */}
                            <div className="flex-1 relative bg-black/20 p-8 flex items-center justify-center">
                                {selectedAgent ? (
                                    <div className="text-center space-y-4 max-w-lg">
                                        <div className="mx-auto w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 mb-6">
                                            <Bot size={32} />
                                        </div>
                                        <h2 className="text-xl font-black text-white">{getAgentDisplayName(selectedAgent)}</h2>
                                        <p className="text-gray-400 leading-relaxed text-sm">
                                            {getAgentDescription(selectedAgent) || "No description available for this agent's core function."}
                                        </p>

                                        <div className="pt-6 mt-6 border-t border-white/5">
                                            <div className="grid grid-cols-2 gap-4 text-left p-4 bg-black/40 rounded-xl border border-white/5">
                                                <div>
                                                    <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Provider</div>
                                                    <div className="text-xs text-white font-medium">{selectedMatrixEntry?.provider || 'Unknown'}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Model</div>
                                                    <div className="text-xs text-white font-medium">{selectedMatrixEntry?.model || 'Unknown'}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-center text-gray-500">
                                        <MessageSquareCode size={48} className="mx-auto mb-4 opacity-50" />
                                        <p className="text-sm">Select an agent to view its configuration</p>
                                    </div>
                                )}
                            </div>

                            {/* Feedback / Warning Area */}
                            <div className="px-8 py-4 bg-blue-500/5 border-t border-white/5 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <Zap size={14} className="text-blue-500" />
                                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                                        Engine Ready
                                    </p>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                        <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Active</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            `}</style>
        </div>
    );
}
