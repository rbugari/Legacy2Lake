"use client";

import { useState, useEffect } from "react";
import { fetchWithAuth } from "../../lib/auth-client";
import {
    Bot,
    Save,
    RefreshCw,
    Sparkles,
    Lock,
    CheckCircle,
    Cpu,
    Globe,
    Zap,
    MessageSquareCode,
    ChevronRight,
    Search,
    Maximize2,
    Minimize2
} from "lucide-react";
import { getAgentDisplayName, AGENT_METADATA } from "../../lib/constants";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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

interface AgentInfo {
    id: string;
    name: string;
    systemPrompt: string;
    basePrompt?: string;
    knowledge?: string;
    isEnriched?: boolean;
}

export default function StrategicIntelligenceHub() {
    const [matrix, setMatrix] = useState<MatrixEntry[]>([]);
    const [catalog, setCatalog] = useState<Model[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Intelligence Hub State
    const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
    const [agentPrompts, setAgentPrompts] = useState<Record<string, AgentInfo>>({});
    const [viewMode, setViewMode] = useState<'merged' | 'base' | 'knowledge'>('merged');
    const [originTech, setOriginTech] = useState("ssis");
    const [destTech, setDestTech] = useState("snowflake");

    // UI State
    const [searchTerm, setSearchTerm] = useState("");
    const [globalProvider, setGlobalProvider] = useState("");
    const [globalModel, setGlobalModel] = useState("");
    const [isMaximized, setIsMaximized] = useState(false);
    const [renderMode, setRenderMode] = useState<'source' | 'vision'>('vision');

    const fetchData = async () => {
        setLoading(true);
        try {
            const [matrixData, catalogData, vaultData] = await Promise.all([
                fetchWithAuth("system/matrix").then(res => res.json()),
                fetchWithAuth("system/catalog").then(res => res.json()),
                fetchWithAuth("system/vault").then(res => res.json())
            ]);

            const matrixList = matrixData.matrix || [];
            setMatrix(matrixList);

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

            // Fix empty dropdown: use newly mapped data immediately
            const providers = Array.from(new Set(mappedCatalog.map((m: any) => m.provider))) as string[];
            if (providers.length > 0) {
                const firstP = providers[0];
                setGlobalProvider(firstP);
                const firstM = mappedCatalog.find((m: any) => m.provider === firstP);
                if (firstM) setGlobalModel(firstM.id);
            }

            if (matrixList.length > 0) {
                const firstAgentId = matrixList[0].agent;
                setSelectedAgent(firstAgentId);
                await fetchAgentPrompt(firstAgentId, originTech, destTech);
            }

            setLoading(false);
        } catch (e) {
            console.error("Failed to load hub data", e);
            setLoading(false);
        }
    };

    const fetchAgentPrompt = async (agentId: string, origin: string, dest: string) => {
        try {
            const url = `/lab/prompts/enriched?agent_id=${agentId}${origin ? `&origin_tech=${origin}` : ''}${dest ? `&dest_tech=${dest}` : ''}`;
            const res = await fetchWithAuth(url);
            const data = await res.json();

            const promptInfo: AgentInfo = {
                id: agentId,
                name: getAgentDisplayName(agentId),
                systemPrompt: data.prompt || "No prompt found.",
                basePrompt: data.base_prompt || data.prompt,
                knowledge: (data.origin_knowledge || data.dest_knowledge)
                    ? `## ORIGIN (${origin.toUpperCase()}):\n\n${data.origin_knowledge || ''}\n\n---\n\n## DESTINATION (${dest.toUpperCase()}):\n\n${data.dest_knowledge || ''}`
                    : "No specific patterns injected for these technologies.",
                isEnriched: !!(data.is_enriched)
            };

            setAgentPrompts(prev => ({ ...prev, [agentId]: promptInfo }));
        } catch (e) {
            console.error(`Failed to fetch prompt for ${agentId}`, e);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // Re-fetch when tech changes
    useEffect(() => {
        if (selectedAgent) {
            fetchAgentPrompt(selectedAgent, originTech, destTech);
        }
    }, [originTech, destTech]);

    const handleAgentSelect = async (agentId: string) => {
        setSelectedAgent(agentId);
        if (!agentPrompts[agentId]) {
            await fetchAgentPrompt(agentId, originTech, destTech);
        }
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
    const selectedAgentData = selectedAgent ? agentPrompts[selectedAgent] : null;
    const selectedMatrixEntry = matrix.find(m => m.agent === selectedAgent);
    const helperModel = matrix.find(m => m.agent === 'agent-helper');

    if (loading) return (
        <div className="flex flex-col items-center justify-center p-20 space-y-4">
            <RefreshCw size={32} className="animate-spin text-blue-500" />
            <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">Initializing Strategic Intelligence Hub...</p>
        </div>
    );

    return (
        <div className={`space-y-6 transition-all duration-300 ${isMaximized ? "fixed inset-0 z-[100] bg-[#0B0F19] p-6 overflow-y-auto" : ""}`}>
            {/* Top Toolbar: Global Preview Params */}
            <div className="bg-slate-900/50 border border-white/5 p-6 rounded-2xl flex flex-wrap items-center justify-between gap-6 shadow-xl">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
                        <Globe size={24} />
                    </div>
                    <div>
                        <h3 className="text-sm font-black uppercase tracking-widest text-white">Hub Preview Context</h3>
                        <p className="text-[10px] text-gray-500 font-bold uppercase mt-1">Simulate technology enrichment across all agents</p>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    <div className="space-y-2">
                        <label className="text-[9px] font-black uppercase tracking-widest text-gray-500 ml-1">Simulated Origin</label>
                        <select
                            value={originTech}
                            onChange={(e) => setOriginTech(e.target.value)}
                            className="bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-xs font-bold text-blue-400 uppercase tracking-widest outline-none focus:ring-1 focus:ring-blue-500/50"
                        >
                            <option value="ssis">SSIS</option>
                            <option value="sqlserver">SQL Server</option>
                            <option value="oracle">Oracle</option>
                            <option value="datastage">DataStage</option>
                            <option value="informatica">Informatica</option>
                        </select>
                    </div>
                    <ChevronRight className="text-gray-700 mt-4" size={16} />
                    <div className="space-y-2">
                        <label className="text-[9px] font-black uppercase tracking-widest text-gray-500 ml-1">Simulated Target</label>
                        <select
                            value={destTech}
                            onChange={(e) => setDestTech(e.target.value)}
                            className="bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-xs font-bold text-emerald-400 uppercase tracking-widest outline-none focus:ring-1 focus:ring-emerald-500/50"
                        >
                            <option value="snowflake">Snowflake</option>
                            <option value="databricks">Databricks</option>
                            <option value="bigquery">BigQuery</option>
                            <option value="fabric">MS Fabric</option>
                        </select>
                    </div>
                </div>

                <div className="flex items-center gap-6 border-l border-white/5 pl-6">
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
                                className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-[10px] font-bold text-gray-300 uppercase outline-none focus:ring-1 focus:ring-blue-500/30"
                            >
                                {availableProviders.map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
                            </select>
                            <select
                                value={globalModel}
                                onChange={(e) => setGlobalModel(e.target.value)}
                                className="bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-[10px] font-bold text-gray-300 uppercase outline-none max-w-[150px] truncate focus:ring-1 focus:ring-blue-500/30"
                            >
                                {catalog.filter(m => m.provider === globalProvider).map(m => (
                                    <option key={m.id} value={m.id}>{m.label}</option>
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
                                            {agentPrompts[entry.agent]?.isEnriched && (
                                                <Sparkles size={12} className="text-blue-500 animate-pulse" />
                                            )}
                                        </div>

                                        {/* Inline Matrix Controls */}
                                        <div className="grid grid-cols-2 gap-2 mt-2" onClick={e => e.stopPropagation()}>
                                            <div className="space-y-1">
                                                <label className="text-[8px] font-black text-gray-600 uppercase tracking-widest ml-1">Provider</label>
                                                <select
                                                    value={entry.provider}
                                                    onChange={(e) => handleMatrixChange(entry.agent, 'provider', e.target.value)}
                                                    className="w-full bg-black/60 border border-white/5 rounded-lg px-2 py-1 text-[10px] text-gray-400 hover:text-white outline-none"
                                                >
                                                    {availableProviders.map(p => <option key={p} value={p}>{p.toUpperCase()}</option>)}
                                                </select>
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-[8px] font-black text-gray-600 uppercase tracking-widest ml-1">Model</label>
                                                <select
                                                    value={entry.model}
                                                    onChange={(e) => handleMatrixChange(entry.agent, 'model', e.target.value)}
                                                    className="w-full bg-black/60 border border-white/5 rounded-lg px-2 py-1 text-[10px] text-gray-400 hover:text-white outline-none truncate"
                                                >
                                                    {catalog.filter(m => m.provider === entry.provider).map(m => (
                                                        <option key={m.id} value={m.id}>{m.label}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                </div>

                {/* 2. Intelligence Explorer Panel */}
                <div className="col-span-8 flex flex-col gap-4">
                    <div className="bg-slate-900/30 border border-white/5 rounded-3xl flex-1 flex flex-col min-h-0 overflow-hidden shadow-2xl">
                        {/* Panel Header */}
                        <div className="px-8 py-4 border-b border-white/5 bg-black/40 backdrop-blur-xl flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-500">
                                    <MessageSquareCode size={20} />
                                </div>
                                <div>
                                    <h3 className="text-xs font-black uppercase tracking-widest text-white">Instruction Audit: {selectedAgentData?.name}</h3>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">Runtime:</span>
                                        <span className="text-[9px] font-black text-blue-400 uppercase tracking-widest">
                                            {selectedMatrixEntry?.provider} / {selectedMatrixEntry?.model}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="flex bg-white/5 p-1 rounded-xl border border-white/5 gap-1">
                                    {/* View Mode Toggle */}
                                    {[
                                        { id: 'merged', label: 'Enriched' },
                                        { id: 'base', label: 'Base' },
                                        { id: 'knowledge', label: 'Patterns' },
                                    ].map(m => (
                                        <button
                                            key={m.id}
                                            onClick={() => setViewMode(m.id as any)}
                                            className={`px-4 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${viewMode === m.id
                                                ? "bg-blue-600 text-white shadow-lg"
                                                : "text-gray-500 hover:text-white"
                                                }`}
                                        >
                                            {m.label}
                                        </button>
                                    ))}
                                </div>

                                <div className="h-4 w-[1px] bg-white/10 mx-1"></div>

                                <div className="flex bg-white/5 p-1 rounded-xl border border-white/5 gap-1">
                                    {/* Render Mode Toggle */}
                                    {[
                                        { id: 'source', label: 'Source', icon: <Lock size={10} /> },
                                        { id: 'vision', label: 'Vision', icon: <Sparkles size={10} /> },
                                    ].map(m => (
                                        <button
                                            key={m.id}
                                            onClick={() => setRenderMode(m.id as any)}
                                            className={`px-4 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all flex items-center gap-2 ${renderMode === m.id
                                                ? "bg-emerald-600 text-white shadow-lg"
                                                : "text-gray-500 hover:text-white"
                                                }`}
                                        >
                                            {m.icon}
                                            {m.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Prompt Display */}
                        <div className="flex-1 relative bg-black/20">
                            {/* Overlay Badge */}
                            <div className="absolute top-4 right-4 z-10 flex items-center gap-3">
                                {selectedAgentData?.isEnriched && (
                                    <div className="px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/30 text-[9px] font-black text-blue-400 uppercase tracking-widest flex items-center gap-2">
                                        <Sparkles size={12} /> Experts Loaded
                                    </div>
                                )}
                                <div className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-[9px] font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                                    <Lock size={12} /> Foundation Core
                                </div>
                            </div>

                            <div className="h-full overflow-y-auto custom-scrollbar">
                                {renderMode === 'source' ? (
                                    <SyntaxHighlighter
                                        language="markdown"
                                        style={vscDarkPlus}
                                        customStyle={{
                                            margin: 0,
                                            padding: '40px',
                                            fontSize: '13px',
                                            lineHeight: '1.7',
                                            background: 'transparent'
                                        }}
                                        wrapLines={true}
                                        wrapLongLines={true}
                                    >
                                        {String(
                                            viewMode === 'knowledge' ? selectedAgentData?.knowledge :
                                                viewMode === 'base' ? selectedAgentData?.basePrompt :
                                                    selectedAgentData?.systemPrompt || "# Select an agent to audit instructions"
                                        )}
                                    </SyntaxHighlighter>
                                ) : (
                                    <div className="p-10 prose prose-invert prose-blue max-w-none text-gray-300">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                h1: ({ node, ...props }) => <h1 className="text-2xl font-black text-white uppercase tracking-tighter mb-6 border-b border-white/10 pb-4" {...props} />,
                                                h2: ({ node, ...props }) => <h2 className="text-lg font-bold text-blue-400 mt-8 mb-4 border-l-4 border-blue-500 pl-4" {...props} />,
                                                h3: ({ node, ...props }) => <h3 className="text-md font-bold text-emerald-400 mt-6 mb-2" {...props} />,
                                                p: ({ node, ...props }) => <p className="leading-relaxed mb-4 text-gray-400 text-sm" {...props} />,
                                                ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-2 mb-4 text-gray-400 text-sm" {...props} />,
                                                ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-400 text-sm" {...props} />,
                                                code: ({ node, inline, className, children, ...props }: any) => {
                                                    const match = /language-(\w+)/.exec(className || '');
                                                    return !inline && match ? (
                                                        <div className="my-6 rounded-xl overflow-hidden border border-white/5 shadow-2xl">
                                                            <div className="bg-black/40 px-4 py-2 border-b border-white/5 flex items-center justify-between">
                                                                <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">{match[1]}</span>
                                                            </div>
                                                            <SyntaxHighlighter
                                                                style={vscDarkPlus}
                                                                language={match[1]}
                                                                PreTag="div"
                                                                customStyle={{ margin: 0, padding: '20px', fontSize: '12px', background: '#0d1117' }}
                                                                {...props}
                                                            >
                                                                {String(children).replace(/\n$/, '')}
                                                            </SyntaxHighlighter>
                                                        </div>
                                                    ) : (
                                                        <code className="bg-white/10 px-1.5 py-0.5 rounded text-blue-300 font-mono text-[11px]" {...props}>
                                                            {children}
                                                        </code>
                                                    );
                                                },
                                                table: ({ node, ...props }) => (
                                                    <div className="overflow-x-auto my-6 border border-white/5 rounded-xl">
                                                        <table className="min-w-full divide-y divide-white/5" {...props} />
                                                    </div>
                                                ),
                                                th: ({ node, ...props }) => <th className="px-4 py-3 bg-white/5 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest" {...props} />,
                                                td: ({ node, ...props }) => <td className="px-4 py-3 text-sm border-t border-white/5" {...props} />,
                                                hr: ({ node, ...props }) => <hr className="my-10 border-white/5" {...props} />,
                                            }}
                                        >
                                            {String(
                                                viewMode === 'knowledge' ? selectedAgentData?.knowledge :
                                                    viewMode === 'base' ? selectedAgentData?.basePrompt :
                                                        selectedAgentData?.systemPrompt || "# Select an agent to audit instructions"
                                            )}
                                        </ReactMarkdown>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Feedback / Warning Area */}
                        <div className="px-8 py-4 bg-blue-500/5 border-t border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Zap size={14} className="text-blue-500" />
                                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                                    Current Configuration optimized for <span className="text-white italic">{selectedAgentData?.isEnriched ? 'Expert Precision' : 'General Logic'}</span>
                                </p>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                    <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Engine Ready</span>
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
