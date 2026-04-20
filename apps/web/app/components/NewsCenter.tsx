"use client";

import React from 'react';
import {
    X,
    Sparkles,
    CheckCircle2,
    Zap,
    Layers,
    LayoutTemplate,
    Cpu,
    MessagesSquare,
    GitCompare,
    Bot,
    Shield
} from 'lucide-react';

interface NewsCenterProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function NewsCenter({ isOpen, onClose }: NewsCenterProps) {
    if (!isOpen) return null;

    const news = [
        {
            sprint: "v4.5 · New",
            title: "Project Intelligence Assistant",
            description: "Chat with your project's source knowledge. The assistant answers questions about assets, PII, dependencies and readiness — backed by real Triage data.",
            features: [
                "Conversation history persisted across sessions.",
                "Chat thread auto-resets on each Triage rerun.",
                "Clear History button to start fresh at any time.",
                "Confidence and intent labels on every answer.",
                "Available from the assistant button in the workspace header."
            ],
            icon: <Bot className="text-indigo-400" />,
            color: "from-indigo-500/10 to-transparent"
        },
        {
            sprint: "v4.5 · New",
            title: "Traceability Review",
            description: "Field-level and table-level traceability from legacy source to generated target output — with PRESERVED / INFERRED / CHANGED / UNRESOLVED badges per column.",
            features: [
                "Per-asset traceability map computed on demand.",
                "Stacked progress bar shows mapping coverage at a glance.",
                "PII column markers surfaced in the detail view.",
                "Transformation hints extracted from understanding payload.",
                "Results cached in Supabase for fast retrieval."
            ],
            icon: <GitCompare className="text-cyan-400" />,
            color: "from-cyan-500/10 to-transparent"
        },
        {
            sprint: "v4.4 → v4.5",
            title: "Intelligent Reengineering Mode",
            description: "A third post-drafting mode that consolidates repeated patterns across assets — shared dimensions, common ingestion paths, reusable transformations.",
            features: [
                "Consolidation manifest links source assets to shared outputs.",
                "Agent C produces consolidated artifacts with traceability.",
                "Agent F validates consolidation explainability and business key preservation.",
                "Medallion Bronze/Silver/Gold contract enforced end-to-end.",
                "Mode selector exposed in Drafting stage settings."
            ],
            icon: <Cpu className="text-yellow-400" />,
            color: "from-yellow-500/10 to-transparent"
        },
        {
            sprint: "v4.0 → v4.5",
            title: "Gap Workspace + Governance Suite",
            description: "A structured workspace for capturing, resolving and tracking gaps and decisions found during Governance review.",
            features: [
                "Gap items with status, owner, priority and resolution notes.",
                "Linked to Governance stage — accessible from the sidebar.",
                "Executive Summary panel with readiness signals.",
                "Audit checks and quality metrics in dedicated sections.",
                "Zero-hardcode prompt architecture with tenant-scoped configuration."
            ],
            icon: <Shield className="text-emerald-400" />,
            color: "from-emerald-500/10 to-transparent"
        }
    ];

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[200] transition-opacity animate-in fade-in duration-300"
                onClick={onClose}
            />

            {/* Drawer */}
            <div className="fixed top-0 right-0 h-full w-[450px] bg-[#0a0a0a] border-l border-white/5 z-[201] shadow-2xl flex flex-col animate-in slide-in-from-right duration-500 ease-out">
                {/* Header */}
                <div className="px-8 py-8 border-b border-white/5 bg-black/40 backdrop-blur-xl">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2.5 bg-cyan-500/10 rounded-2xl text-cyan-500 border border-cyan-500/20">
                                <Sparkles size={20} />
                            </div>
                            <h2 className="text-sm font-black uppercase tracking-[0.2em] text-white">What's New</h2>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-all text-gray-500 hover:text-white">
                            <X size={20} />
                        </button>
                    </div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                        Top updates from v4.0 → v4.5
                    </p>
                </div>

                {/* News Feed */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                    {news.map((item, idx) => (
                        <div key={idx} className={`relative p-6 rounded-3xl border border-white/5 bg-gradient-to-br ${item.color} group hover:border-white/10 transition-all`}>
                            <div className="flex items-start justify-between mb-4">
                                <div className="p-3 bg-black/20 rounded-2xl border border-white/5">
                                    {item.icon}
                                </div>
                                <span className="text-[9px] font-black py-1 px-3 bg-white/5 rounded-full text-gray-500 uppercase tracking-widest border border-white/5">
                                    {item.sprint}
                                </span>
                            </div>

                            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-2">{item.title}</h3>
                            <p className="text-[11px] text-gray-400 leading-relaxed mb-6 font-medium">
                                {item.description}
                            </p>

                            <ul className="space-y-3">
                                {item.features.map((feat, fidx) => (
                                    <li key={fidx} className="flex items-start gap-3">
                                        <CheckCircle2 size={14} className="text-cyan-500 mt-0.5 shrink-0" />
                                        <span className="text-[10px] text-gray-300 font-bold uppercase tracking-widest leading-none pt-0.5">{feat}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                {/* Footer */}
                <div className="p-8 border-t border-white/5 bg-black/40 text-center">
                    <button
                        onClick={onClose}
                        className="w-full py-4 bg-white/5 hover:bg-white/10 text-[10px] font-black uppercase tracking-[0.3em] text-cyan-500 rounded-2xl transition-all border border-white/5"
                    >
                        Got it, thanks!
                    </button>
                </div>
            </div>
        </>
    );
}
