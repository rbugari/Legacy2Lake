"use client";
import { useState, useEffect } from "react";
import { Lock, Sparkles, Save, Trash2, RefreshCw, CheckCircle, Info } from "lucide-react";
import { fetchWithAuth } from "../lib/auth-client";
import { getAgentDisplayName, AGENT_METADATA } from "../lib/constants";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface PromptsExplorerProps {
    className?: string;
    projectId?: string; // Optional: if provided, shows user context editing
    stage?: 'triage' | 'drafting' | 'refinement' | 'all';
    originTech?: string;
    destTech?: string;
}

interface AgentInfo {
    id: string;
    name: string;
    systemPrompt: string;
    basePrompt?: string;
    knowledge?: string;
    userContext: string;
    isEnriched?: boolean;
}

const STAGE_MAP: Record<string, string[]> = {
    triage: ["agent-s", "agent-a"],
    drafting: ["agent-c", "agent-f"],
    refinement: ["agent-b", "agent-p", "agent-r", "agent-o"],
    all: ["agent-s", "agent-a", "agent-c", "agent-f", "agent-g", "agent-b", "agent-p", "agent-r", "agent-o"]
};

export default function PromptsExplorer({ className, projectId, stage = 'all', originTech, destTech }: PromptsExplorerProps) {
    const [agents, setAgents] = useState<AgentInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
    const [editingContext, setEditingContext] = useState("");
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [viewMode, setViewMode] = useState<'merged' | 'base' | 'knowledge'>('merged');
    const [renderMode, setRenderMode] = useState<'source' | 'vision'>('vision');

    useEffect(() => {
        fetchData();
    }, [projectId, stage, originTech, destTech]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const agentIds = STAGE_MAP[stage] || STAGE_MAP.all;

            // Fetch prompts for relevant agents
            const agentData: AgentInfo[] = await Promise.all(agentIds.map(async (id) => {
                let systemPrompt = "No prompt loaded.";
                let isEnriched = false;

                try {
                    // Use enriched endpoint if tech is available
                    if (originTech || destTech) {
                        const url = `/lab/prompts/enriched?agent_id=${id}${originTech ? `&origin_tech=${originTech}` : ''}${destTech ? `&dest_tech=${destTech}` : ''}`;
                        const res = await fetchWithAuth(url);
                        const data = await res.json();

                        const systemPrompt = data.prompt || "No prompt loaded.";
                        const isEnriched = !!(data.is_enriched);
                        const basePrompt = data.base_prompt || systemPrompt;

                        // Combine knowledges if present
                        const knowledgeParts = [];
                        if (data.origin_knowledge) knowledgeParts.push(`## ORIGIN (${originTech?.toUpperCase()}):\n\n${data.origin_knowledge}`);
                        if (data.dest_knowledge) knowledgeParts.push(`## DESTINATION (${destTech?.toUpperCase()}):\n\n${data.dest_knowledge}`);
                        const knowledge = knowledgeParts.join("\n\n---\n\n") || "No specific patterns injected for this technology.";

                        return {
                            id,
                            name: getAgentDisplayName(id),
                            systemPrompt,
                            basePrompt,
                            knowledge,
                            userContext: "",
                            isEnriched
                        };
                    } else {
                        // Standard endpoint
                        const res = await fetchWithAuth(`/prompts/${id}`);
                        const data = await res.json();
                        systemPrompt = data.prompt || systemPrompt;
                    }
                } catch (err) {
                    console.error(`Error loading prompt for ${id}:`, err);
                }

                return {
                    id,
                    name: getAgentDisplayName(id),
                    systemPrompt,
                    userContext: "",
                    isEnriched
                };
            }));

            // Fetch user contexts if projectId provided
            if (projectId) {
                const contextRes = await fetchWithAuth(`/projects/${projectId}/context`);
                const data = await contextRes.json();
                const rawContexts = data.contexts || data.context;
                const contexts = Array.isArray(rawContexts) ? rawContexts : [];

                agentData.forEach(agent => {
                    const userCtx = contexts.find((c: any) => c.context_type === agent.id);
                    agent.userContext = userCtx?.user_context || "";
                });
            }

            setAgents(agentData);
            if (agentData.length > 0) {
                setSelectedAgent(agentData[0].id);
                setEditingContext(agentData[0].userContext);
            }
        } catch (e) {
            console.error("Failed to load prompts", e);
        } finally {
            setLoading(false);
        }
    };

    const handleAgentSelect = (agentId: string) => {
        setSelectedAgent(agentId);
        const agent = agents.find(a => a.id === agentId);
        if (agent) {
            setEditingContext(agent.userContext);
        }
    };

    const handleSaveContext = async () => {
        if (!projectId || !selectedAgent) return;

        setSaving(true);
        try {
            await fetchWithAuth(`/projects/${projectId}/context`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    context_type: selectedAgent,
                    user_context: editingContext
                })
            });

            setAgents(prev => prev.map(a =>
                a.id === selectedAgent ? { ...a, userContext: editingContext } : a
            ));
        } catch (e) {
            console.error("Failed to save context", e);
        } finally {
            setSaving(false);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        }
    };

    const handleClearContext = async () => {
        if (!projectId || !selectedAgent) return;

        try {
            await fetchWithAuth(`/projects/${projectId}/context/${selectedAgent}`, {
                method: "DELETE"
            });
            setEditingContext("");
            setAgents(prev => prev.map(a =>
                a.id === selectedAgent ? { ...a, userContext: "" } : a
            ));
        } catch (e) {
            console.error("Failed to clear context", e);
        }
    };

    if (loading) return (
        <div className="flex flex-col items-center justify-center p-20 space-y-4">
            <RefreshCw size={32} className="animate-spin text-[var(--accent)]" />
            <p className="text-[var(--text-secondary)] font-medium animate-pulse">Filtering Intelligence for {stage.toUpperCase()} Stage...</p>
        </div>
    );

    const selectedAgentData = agents.find(a => a.id === selectedAgent);

    return (
        <div className={`h-full grid grid-cols-1 md:grid-cols-4 gap-4 ${className}`}>
            {/* Agent Selector */}
            <div className="col-span-1 space-y-2 border-r border-[var(--border)] pr-4 overflow-y-auto max-h-[800px]">
                <div className="flex items-center gap-2 mb-4 px-1 py-2 border-b border-[var(--border)]/50">
                    <Sparkles size={16} className="text-[var(--accent)]" />
                    <span className="text-xs font-bold uppercase tracking-widest text-[var(--text-tertiary)]">Relevant Agents</span>
                </div>
                {agents.map(agent => (
                    <div
                        key={agent.id}
                        onClick={() => handleAgentSelect(agent.id)}
                        className={`p-3 rounded-xl border cursor-pointer transition-all ${selectedAgent === agent.id
                            ? "bg-[var(--accent)]/10 border-[var(--accent)] shadow-lg shadow-[var(--accent)]/5 scale-[1.02]"
                            : "bg-[var(--surface)] border-[var(--border)] hover:border-[var(--accent)]/30 hover:bg-[var(--surface-elevated)]"
                            }`}
                    >
                        <h3 className={`font-bold text-sm mb-1 ${selectedAgent === agent.id ? "text-[var(--accent)]" : "text-[var(--text-primary)]"}`}>
                            {agent.name}
                        </h3>
                        <div className="flex items-center justify-between">
                            <p className="text-[10px] text-[var(--text-tertiary)] italic">
                                {AGENT_METADATA[agent.id]?.description || ""}
                            </p>
                            {agent.userContext && (
                                <CheckCircle size={10} className="text-emerald-500" />
                            )}
                        </div>
                    </div>
                ))}

                {agents.length === 0 && (
                    <div className="text-center p-4 border border-dashed border-[var(--border)] rounded-lg">
                        <p className="text-xs text-[var(--text-tertiary)]">No agents assigned to this stage.</p>
                    </div>
                )}
            </div>

            {/* Dual Panel View */}
            <div className="col-span-3 flex flex-col gap-4 overflow-hidden">
                {/* System Prompt (Read-Only) */}
                <div className="flex-1 flex flex-col min-h-0">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <Lock size={14} className="text-[var(--text-tertiary)]" />
                            <h4 className="font-bold text-xs uppercase tracking-tighter text-[var(--text-secondary)]">Engine Core: {selectedAgentData?.id}</h4>
                        </div>
                        {(selectedAgentData?.isEnriched || originTech || destTech) && (
                            <div className="flex bg-[var(--surface-elevated)] p-1 rounded-lg border border-[var(--border)] gap-1">
                                {[
                                    { id: 'merged', label: 'Enriched Prompt' },
                                    { id: 'base', label: 'Base' },
                                    { id: 'knowledge', label: 'Tech Knowledge' },
                                ].map(m => (
                                    <button
                                        key={m.id}
                                        onClick={() => setViewMode(m.id as any)}
                                        className={`px-3 py-1 rounded-md text-[9px] font-black uppercase tracking-widest transition-all ${viewMode === m.id
                                            ? "bg-blue-600 text-white shadow-lg"
                                            : "text-[var(--text-tertiary)] hover:text-blue-400"
                                            }`}
                                    >
                                        {m.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                    <div className="flex-1 bg-[#1e1e1e] rounded-xl overflow-hidden border border-[var(--border)] shadow-2xl relative">
                        <div className="absolute top-3 right-3 z-10 opacity-50 hover:opacity-100 transition-opacity flex items-center gap-2">
                            {(selectedAgentData?.isEnriched || originTech || destTech) && (
                                <div className="px-2 py-1 rounded bg-blue-500/20 text-[9px] text-blue-400 font-black uppercase border border-blue-500/30">
                                    {originTech?.toUpperCase() || 'UNKNOWN'} + {destTech?.toUpperCase() || 'UNKNOWN'} Experts Active
                                </div>
                            )}
                            <div className="px-2 py-1 rounded bg-white/10 text-[10px] text-white font-mono">
                                Read Only
                            </div>
                        </div>
                        <div className="h-full overflow-y-auto custom-scrollbar">
                            <SyntaxHighlighter
                                language="markdown"
                                style={vscDarkPlus}
                                customStyle={{
                                    margin: 0,
                                    padding: '24px',
                                    fontSize: '13px',
                                    lineHeight: '1.6',
                                    background: 'transparent'
                                }}
                                wrapLines={true}
                                wrapLongLines={true}
                            >
                                {String(
                                    viewMode === 'knowledge' ? selectedAgentData?.knowledge :
                                        viewMode === 'base' ? selectedAgentData?.basePrompt :
                                            selectedAgentData?.systemPrompt || ""
                                )}
                            </SyntaxHighlighter>
                        </div>
                    </div>
                </div>

                {/* User Context (Editable) */}
                <div className="h-[220px] flex flex-col">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-cyan-400">
                            <Sparkles size={14} />
                            <h4 className="font-bold text-xs uppercase tracking-tighter">Human Override & Business Context</h4>
                        </div>
                        {projectId && selectedAgent && (
                            <div className="flex gap-2">
                                <button
                                    onClick={handleClearContext}
                                    title="Discard all changes"
                                    className="p-2 rounded-lg text-[var(--text-tertiary)] hover:text-red-500 hover:bg-red-500/10 transition-all"
                                >
                                    <Trash2 size={14} />
                                </button>
                                <button
                                    onClick={handleSaveContext}
                                    disabled={saving || saved || !projectId}
                                    className={`px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all flex items-center gap-2 ${saved
                                        ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/30"
                                        : "bg-cyan-600/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-600 hover:text-white"
                                        }`}
                                >
                                    {saving ? <RefreshCw size={12} className="animate-spin" /> : saved ? <CheckCircle size={12} /> : <Save size={12} />}
                                    {saving ? "Syncing" : saved ? "Applied" : "Apply Override"}
                                </button>
                            </div>
                        )}
                    </div>
                    {projectId ? (
                        <div className="flex-1 relative">
                            {saving && (
                                <div className="absolute top-0 left-0 w-full h-[1px] bg-cyan-500/50 z-10 animate-pulse" />
                            )}
                            <textarea
                                value={editingContext}
                                onChange={(e) => setEditingContext(e.target.value)}
                                placeholder={`Inject solution-specific rules for ${selectedAgentData?.name}...
Examples:
- "Prioritize logic over code density"
- "Specific naming convention: XYZ_*"
- "External dependency: system_auth_api"`}
                                className="w-full h-full bg-[var(--surface-elevated)] border border-[var(--border)] rounded-xl p-4 text-[13px] text-gray-300 font-mono outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all resize-none shadow-inner"
                            />
                        </div>
                    ) : (
                        <div className="flex-1 flex items-center justify-center bg-[var(--surface)]/30 rounded-xl border border-dashed border-[var(--border)]">
                            <p className="text-[var(--text-tertiary)] text-[10px] uppercase tracking-widest">
                                Select a project to enable human context injection
                            </p>
                        </div>
                    )}
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
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(255, 255, 255, 0.2);
                }
            `}</style>
        </div>
    );
}
