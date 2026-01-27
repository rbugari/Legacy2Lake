"use client";
import { useState, useEffect } from "react";
import { Lock, Sparkles, Save, Trash2, RefreshCw, CheckCircle } from "lucide-react";
import { API_BASE_URL } from "../lib/config";

interface PromptsExplorerProps {
    className?: string;
    projectId?: string; // Optional: if provided, shows user context editing
}

interface AgentInfo {
    id: string;
    name: string;
    systemPrompt: string;
    userContext: string;
}

export default function PromptsExplorer({ className, projectId }: PromptsExplorerProps) {
    const [agents, setAgents] = useState<AgentInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
    const [editingContext, setEditingContext] = useState("");
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        fetchData();
    }, [projectId]);

    const fetchData = async () => {
        try {
            // Fetch system prompts
            const [a, c, f, g] = await Promise.all([
                fetch(`${API_BASE_URL}/prompts/agent-a`).then(r => r.json()),
                fetch(`${API_BASE_URL}/prompts/agent-c`).then(r => r.json()),
                fetch(`${API_BASE_URL}/prompts/agent-f`).then(r => r.json()),
                fetch(`${API_BASE_URL}/prompts/agent-g`).then(r => r.json())
            ]);

            const agentData: AgentInfo[] = [
                { id: "agent_a", name: "Agent A (Detective)", systemPrompt: a.prompt, userContext: "" },
                { id: "agent_c", name: "Agent C (Developer)", systemPrompt: c.prompt, userContext: "" },
                { id: "agent_f", name: "Agent F (Compliance)", systemPrompt: f.prompt, userContext: "" },
                { id: "agent_g", name: "Agent G (Governance)", systemPrompt: g.prompt, userContext: "" }
            ];

            // Fetch user contexts if projectId provided
            if (projectId) {
                const contextRes = await fetch(`${API_BASE_URL}/projects/${projectId}/context`);
                const { contexts } = await contextRes.json();

                // Merge user contexts
                agentData.forEach(agent => {
                    const userCtx = contexts.find((c: any) => c.context_type === agent.id);
                    agent.userContext = userCtx?.user_context || "";
                });
            }

            setAgents(agentData);
            setSelectedAgent(agentData[0].id);
            setEditingContext(agentData[0].userContext);
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
            await fetch(`${API_BASE_URL}/projects/${projectId}/context`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    context_type: selectedAgent,
                    user_context: editingContext
                })
            });

            // Update local state
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
            await fetch(`${API_BASE_URL}/projects/${projectId}/context/${selectedAgent}`, {
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

    if (loading) return <div className="text-center p-10 text-[var(--text-secondary)]">Loading Intelligence Hub...</div>;

    const selectedAgentData = agents.find(a => a.id === selectedAgent);

    return (
        <div className={`h-full grid grid-cols-1 md:grid-cols-4 gap-4 ${className}`}>
            {/* Agent Selector */}
            <div className="col-span-1 space-y-2 border-r border-[var(--border)] pr-4">
                {agents.map(agent => (
                    <div
                        key={agent.id}
                        onClick={() => handleAgentSelect(agent.id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedAgent === agent.id
                            ? "bg-[var(--accent)]/10 border-[var(--accent)] shadow-sm"
                            : "bg-[var(--surface)] border-[var(--border)] hover:border-[var(--accent)]/50"
                            }`}
                    >
                        <h3 className={`font-bold text-sm ${selectedAgent === agent.id ? "text-[var(--accent)]" : ""}`}>
                            {agent.name}
                        </h3>
                        <p className="text-xs text-[var(--text-tertiary)]">
                            {agent.userContext ? "Customized" : "Default"}
                        </p>
                    </div>
                ))}
            </div>

            {/* Dual Panel View */}
            <div className="col-span-3 flex flex-col gap-4">
                {/* System Prompt (Read-Only) */}
                <div className="flex-1 min-h-[250px]">
                    <div className="flex items-center gap-2 mb-2">
                        <Lock size={16} className="text-[var(--text-tertiary)]" />
                        <h4 className="font-bold text-sm text-[var(--text-secondary)]">📖 System Prompt (Read-Only)</h4>
                    </div>
                    <div className="bg-[var(--surface-elevated)] rounded-lg p-4 h-[calc(100%-2rem)] overflow-y-auto border border-[var(--border)] relative">
                        <div className="absolute top-2 right-2 px-2 py-1 rounded text-xs font-mono bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20">
                            {selectedAgentData?.name}
                        </div>
                        <pre className="whitespace-pre-wrap text-xs font-mono text-[var(--text-secondary)] pr-32">
                            {selectedAgentData?.systemPrompt}
                        </pre>
                    </div>
                </div>

                {/* User Context (Editable) */}
                {projectId && (
                    <div className="flex-1 min-h-[250px]">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                                <Sparkles size={16} className="text-[var(--accent)]" />
                                <h4 className="font-bold text-sm">✏️ Your Context for this Solution</h4>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleClearContext}
                                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--surface-elevated)] border border-[var(--border)] hover:border-red-500 hover:bg-red-500/5 transition-all flex items-center gap-1.5"
                                >
                                    <Trash2 size={14} />
                                    Clear
                                </button>
                                <button
                                    onClick={handleSaveContext}
                                    disabled={saving || saved}
                                    className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-2 shadow-xl ${saved
                                        ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/30"
                                        : "bg-cyan-600 text-white hover:bg-cyan-500 shadow-cyan-600/20 active:scale-95 disabled:opacity-50"
                                        }`}
                                >
                                    {saving ? <RefreshCw size={14} className="animate-spin" /> : saved ? <CheckCircle size={14} /> : <Save size={14} />}
                                    {saving ? "Syncing..." : saved ? "Saved!" : "Save Context"}
                                </button>
                            </div>
                        </div>
                        <div className="relative h-[calc(100%-2.5rem)]">
                            {saving && (
                                <div className="absolute top-0 left-0 w-full h-[1px] bg-cyan-500/20 z-10">
                                    <div className="h-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)] animate-[shimmer_2s_infinite_linear] w-1/3" />
                                </div>
                            )}
                            <textarea
                                value={editingContext}
                                onChange={(e) => setEditingContext(e.target.value)}
                                placeholder="Add custom instructions for this agent specific to your solution...
Example:
- Use BIGINT for all ID columns
- Prefix gold tables with 'dim_' or 'fact_'
- Apply data masking to PII fields"
                                className="w-full h-full bg-white/5 border border-white/5 rounded-2xl p-6 text-[13px] text-gray-300 font-mono outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all resize-none"
                            />
                        </div>
                    </div>
                )}

                {!projectId && (
                    <div className="flex-1 min-h-[250px] flex items-center justify-center bg-[var(--surface)]/50 rounded-lg border border-dashed border-[var(--border)]">
                        <p className="text-[var(--text-tertiary)] text-sm">
                            Select a project to customize agent context
                        </p>
                    </div>
                )}
            </div>
            <style jsx>{`
                @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(300%); }
                }
            `}</style>
        </div>
    );
}
