"use client";

import React from 'react';
import {
    X,
    Settings2,
    Cpu,
    Zap,
    Wand2,
    ShieldCheck,
    Save,
    Layers,
    MessageSquareCode
} from 'lucide-react';

interface ConfigDrawerProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function SolutionConfigDrawer({ isOpen, onClose }: ConfigDrawerProps) {
    const [showAdvanced, setShowAdvanced] = React.useState(false);
    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] transition-opacity animate-in fade-in duration-300"
                onClick={onClose}
            />

            {/* Drawer */}
            <div className="fixed top-0 right-0 h-full w-[600px] bg-[#0a0a0a] border-l border-white/5 z-[101] shadow-2xl flex flex-col animate-in slide-in-from-right duration-500 ease-out">
                {/* Header */}
                <div className="flex items-center justify-between px-8 py-6 border-b border-white/5 bg-black/40 backdrop-blur-xl">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-cyan-500/10 rounded-2xl text-cyan-500">
                            <Settings2 size={24} />
                        </div>
                        <div>
                            <h3 className="text-sm font-black uppercase tracking-[0.2em] text-white">Solution Configuration</h3>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Cross-Stage Orchestration & AI Strategy</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-3 hover:bg-white/5 rounded-2xl transition-all text-gray-500 hover:text-white"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 space-y-10 custom-scrollbar">
                    {/* Technology Stack Section */}
                    <div className="space-y-6">
                        <Header title="Modernization Target" icon={<Cpu size={14} />} />
                        <div className="grid grid-cols-2 gap-4">
                            <ConfigCard
                                label="Execution Engine"
                                value="Databricks / Spark"
                                icon={<Zap size={16} className="text-cyan-500" />}
                            />
                            <ConfigCard
                                label="Output Language"
                                value="Python (PySpark)"
                                icon={<CodeIcon size={16} className="text-emerald-500" />}
                            />
                        </div>
                    </div>

                    {/* Advanced Settings Toggle */}
                    <div className="pt-4 flex justify-center">
                        <button
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-xl border border-white/5 bg-white/5 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-all shadow-sm"
                        >
                            {showAdvanced ? "Hide Advanced Settings" : "Show Advanced Technical Settings"}
                        </button>
                    </div>

                    {showAdvanced && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            {/* AI Strategy Section */}
                            <div className="space-y-6">
                                <Header title="Agent Intelligence Policy" icon={<Wand2 size={14} />} />
                                <div className="space-y-4">
                                    <DropdownField
                                        label="Primary LLM Model"
                                        description="Select the core model for code generation"
                                        options={["GPT-4o (Standard)", "Claude 3.5 Sonnet", "DeepSeek Coder"]}
                                    />
                                    <ToggleField
                                        label="Automated Self-Correction"
                                        description="Allow Agent F to iterate on failed outputs"
                                        checked={true}
                                    />
                                    <ToggleField
                                        label="Architectural Alignment"
                                        description="Strict compliance with Medallion architecture"
                                        checked={true}
                                    />
                                </div>
                            </div>

                            {/* Prompts Section */}
                            <div className="space-y-6">
                                <Header title="System Foundation Instructions" icon={<MessageSquareCode size={14} />} />
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Universal Triage Directive</label>
                                        <textarea
                                            className="w-full h-32 bg-white/5 border border-white/5 rounded-2xl p-4 text-xs text-gray-300 font-mono outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all font-bold"
                                            defaultValue="ACT as a Data Engineering Architect. ANALYZE complexity. CLASSIFY based on Medallion standards."
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-8 border-t border-white/5 bg-black/40 flex justify-end gap-4">
                    <button
                        onClick={onClose}
                        className="px-8 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-white transition-colors"
                    >
                        Discard Changes
                    </button>
                    <button
                        className="px-10 py-3 bg-cyan-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 active:scale-95 flex items-center gap-3"
                    >
                        <Save size={16} /> Update Solution
                    </button>
                </div>
            </div>
        </>
    );
}

function Header({ title, icon }: any) {
    return (
        <h4 className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-cyan-500/80 border-b border-white/5 pb-4">
            {icon} {title}
        </h4>
    );
}

function ConfigCard({ label, value, icon }: any) {
    return (
        <div className="bg-white/5 border border-white/5 rounded-2xl p-5 space-y-3 hover:bg-white/10 transition-colors group cursor-pointer">
            <div className="flex items-center justify-between">
                <span className="p-2 bg-black/20 rounded-lg">{icon}</span>
                <span className="text-[9px] font-black text-white/20 group-hover:text-cyan-500 transition-colors uppercase tracking-widest">Active</span>
            </div>
            <div className="space-y-1">
                <p className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">{label}</p>
                <p className="text-xs font-black text-white uppercase tracking-wider">{value}</p>
            </div>
        </div>
    );
}

function DropdownField({ label, description, options }: any) {
    return (
        <div className="flex items-center justify-between p-2 hover:bg-white/5 rounded-2xl transition-all group">
            <div className="space-y-1">
                <p className="text-[10px] font-black text-gray-300 uppercase tracking-widest">{label}</p>
                <p className="text-[9px] text-gray-500 uppercase font-bold tracking-widest">{description}</p>
            </div>
            <select className="bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-[10px] font-black text-cyan-500 uppercase tracking-widest outline-none cursor-pointer">
                {options.map((opt: string) => <option key={opt}>{opt}</option>)}
            </select>
        </div>
    );
}

function ToggleField({ label, description, checked }: any) {
    return (
        <div className="flex items-center justify-between p-2 hover:bg-white/5 rounded-2xl transition-all group">
            <div className="space-y-1">
                <p className="text-[10px] font-black text-gray-300 uppercase tracking-widest">{label}</p>
                <p className="text-[9px] text-gray-500 uppercase font-bold tracking-widest">{description}</p>
            </div>
            <button className={`w-12 h-6 rounded-full relative transition-all ${checked ? 'bg-cyan-600' : 'bg-white/10'}`}>
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${checked ? 'left-7' : 'left-1'}`} />
            </button>
        </div>
    );
}

function CodeIcon({ size, className }: any) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <polyline points="16 18 22 12 16 6" />
            <polyline points="8 6 2 12 8 18" />
        </svg>
    );
}
