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
    MessagesSquare
} from 'lucide-react';

interface NewsCenterProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function NewsCenter({ isOpen, onClose }: NewsCenterProps) {
    if (!isOpen) return null;

    const news = [
        {
            sprint: "Since v4.0",
            title: "Dual Product Reporting Catalog",
            description: "A single reports surface now clearly separates Source Intelligence from Migration Factory outputs.",
            features: [
                "Reports Access panel integrated into workspace.",
                "Catalog APIs: list, metadata, and summary endpoints.",
                "Product-line grouping with clear user-facing narratives.",
                "Schema Intelligence and Forensic Assessment endpoints exposed.",
                "Handover-focused presentation without polluting Discovery view."
            ],
            icon: <Zap className="text-yellow-400" />,
            color: "from-yellow-500/10 to-transparent"
        },
        {
            sprint: "Since v4.0",
            title: "Flexible Report Formats",
            description: "Reports now support default and optional formats per artifact with cleaner download behavior.",
            features: [
                "Per-report format selector (PDF, Markdown, HTML, JSON).",
                "Knowledge Export consolidated into one entry with dynamic format routing.",
                "HTTP method handling fixed (GET for read endpoints, POST only for triage/final PDFs).",
                "Catalog metadata now includes available_formats.",
                "Project-level validation tested on real tenant/project data."
            ],
            icon: <Cpu className="text-cyan-400" />,
            color: "from-cyan-500/10 to-transparent"
        },
        {
            sprint: "Since v4.0",
            title: "Trust-First Discovery Validation",
            description: "Discovery cross-check now behaves as recommendation, while preserving user intent and known project context.",
            features: [
                "Detected technology ranking now prioritizes dominant evidence (frequency-based).",
                "Manual source-tech selection is explicitly preserved as a valid decision.",
                "Conflict messaging reframed from hard override to guided recommendation.",
                "Category taxonomy standardized to English across UI and API.",
                "Hydration and UX noise reduced during reset/re-run workflows."
            ],
            icon: <MessagesSquare className="text-emerald-400" />,
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
                        Top updates delivered from v4.0 to now.
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
