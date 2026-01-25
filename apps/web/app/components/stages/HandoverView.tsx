"use client";

import React, { useState } from 'react';
import {
    Package,
    Settings2,
    FileText,
    ExternalLink,
    CheckCircle2,
    ArrowRight,
    Zap,
    Box,
    Terminal,
    Globe,
    HardDrive,
    Trash2,
    Plus,
    Download,
    Eye,
    Database
} from 'lucide-react';
import StageHeader from '../StageHeader';

interface Variable {
    key: string;
    value: string;
    description: string;
}

interface HandoverViewProps {
    projectId: string;
    onStageChange: (stage: number) => void;
}

export default function HandoverView({ projectId, onStageChange }: HandoverViewProps) {
    const [variables, setVariables] = useState<Variable[]>([
        { key: "ENV", value: "prod", description: "Environment tag for naming" },
        { key: "ROOT_PATH", value: "/mnt/data/modernized", description: "Base path for Lakehouse tables" },
        { key: "CATALOG", value: "main", description: "Unity Catalog destination" }
    ]);
    const [selectedCartridge, setSelectedCartridge] = useState<'dbc' | 'sql' | 'yaml'>('dbc');
    const [isExporting, setIsExporting] = useState(false);
    const [showRunbook, setShowRunbook] = useState(false);

    const addVariable = () => {
        setVariables([...variables, { key: "", value: "", description: "" }]);
    };

    const updateVariable = (idx: number, field: keyof Variable, val: string) => {
        const newVars = [...variables];
        newVars[idx][field] = val;
        setVariables(newVars);
    };

    const removeVariable = (idx: number) => {
        setVariables(variables.filter((_, i) => i !== idx));
    };

    const handleExport = () => {
        setIsExporting(true);
        setTimeout(() => {
            setIsExporting(false);
            alert("Handover Bundle Ready! Downloading legacy2lake_modernized.zip...");
        }, 3000);
    };

    return (
        <div className="flex flex-col h-full bg-[#050505]">
            <StageHeader
                title="SaaS Handover"
                subtitle="Phase 5: Operational Context Injection and Final Bundling"
                icon={<Package className="text-emerald-500" />}
                helpText="Finalize the process by injecting environment variables and generating technical deployment documentation."
                onApprove={() => alert("Project finalized and closed successfully.")}
                approveLabel="Close Project"
            >
                <div className="flex gap-2">
                    <button
                        onClick={() => setShowRunbook(!showRunbook)}
                        className="px-6 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-bold flex items-center gap-2 hover:bg-white/10 transition-all"
                    >
                        <Eye size={14} /> {showRunbook ? "Edit Variables" : "View Runbook"}
                    </button>
                    <button
                        onClick={handleExport}
                        disabled={isExporting}
                        className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-xs font-bold flex items-center gap-2 hover:bg-emerald-500 transition-all shadow-xl shadow-emerald-600/20 disabled:opacity-50"
                    >
                        {isExporting ? <Zap size={14} className="animate-pulse" /> : <Download size={14} />}
                        {isExporting ? "Bundling..." : "Export Delivery"}
                    </button>
                </div>
            </StageHeader>

            <div className="flex-1 overflow-y-auto p-8 max-w-7xl mx-auto w-full custom-scrollbar">

                {showRunbook ? (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="bg-black/40 border border-white/5 rounded-3xl p-8 font-mono text-sm text-gray-300 leading-relaxed shadow-2xl">
                            <h2 className="text-white text-lg font-black uppercase tracking-widest mb-6 border-b border-white/5 pb-4"># Modernization Runbook: {projectId}</h2>
                            <p className="mb-4">Generated on: {new Date().toLocaleDateString()}</p>
                            <h3 className="text-emerald-500 font-bold mb-4 mt-8">## 1. Environment Injection Summary</h3>
                            <ul className="space-y-2 mb-8">
                                {variables.map((v, i) => (
                                    <li key={i} className="flex gap-4">
                                        <span className="text-gray-500">[{v.key}]</span>
                                        <span className="text-white">{v.value}</span>
                                        <span className="text-gray-600 italic">// {v.description}</span>
                                    </li>
                                ))}
                            </ul>
                            <h3 className="text-emerald-500 font-bold mb-4">## 2. Deployment Instructions</h3>
                            <p>1. Unzip the bundle into your root artifact workspace.</p>
                            <p>2. Configure the <code>{"${ROOT_PATH}"}</code> to point to your ADLS/S3 bucket.</p>
                            <p>3. Execute the <code>modernization_catalyst.py</code> entry point.</p>

                            <div className="mt-12 p-6 bg-white/5 rounded-2xl border border-white/5 text-center">
                                <FileText size={48} className="mx-auto text-white/20 mb-4" />
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">End of Documentation</p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-12 gap-8">

                        {/* Left: Variable Grid */}
                        <div className="col-span-12 lg:col-span-8 space-y-6">
                            <div className="bg-black/40 border border-white/5 rounded-3xl p-8 shadow-2xl">
                                <div className="flex items-center justify-between mb-8">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2.5 bg-emerald-500/10 rounded-2xl text-emerald-500 border border-emerald-500/20">
                                            <Settings2 size={20} />
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-black text-white uppercase tracking-wider">Environment Variable Injection</h3>
                                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Global logic overrides</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={addVariable}
                                        className="p-2.5 bg-white/5 hover:bg-white/10 rounded-2xl text-gray-400 hover:text-white transition-all border border-white/5"
                                    >
                                        <Plus size={20} />
                                    </button>
                                </div>

                                <div className="space-y-4">
                                    {variables.map((v, idx) => (
                                        <div key={idx} className="grid grid-cols-12 gap-4 items-center group animate-in slide-in-from-left duration-300" style={{ animationDelay: `${idx * 50}ms` }}>
                                            <div className="col-span-3">
                                                <input
                                                    className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-xs font-bold text-emerald-400 placeholder:text-gray-700 outline-none focus:ring-1 focus:ring-emerald-500/50"
                                                    placeholder="VARIABLE_KEY"
                                                    value={v.key}
                                                    onChange={e => updateVariable(idx, 'key', e.target.value.toUpperCase())}
                                                />
                                            </div>
                                            <div className="col-span-3">
                                                <input
                                                    className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-xs text-white placeholder:text-gray-700 outline-none focus:ring-1 focus:ring-emerald-500/50"
                                                    placeholder="Value"
                                                    value={v.value}
                                                    onChange={e => updateVariable(idx, 'value', e.target.value)}
                                                />
                                            </div>
                                            <div className="col-span-5">
                                                <input
                                                    className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-xs text-gray-400 placeholder:text-gray-700 outline-none focus:ring-1 focus:ring-emerald-500/50"
                                                    placeholder="Description..."
                                                    value={v.description}
                                                    onChange={e => updateVariable(idx, 'description', e.target.value)}
                                                />
                                            </div>
                                            <div className="col-span-1 flex justify-end">
                                                <button onClick={() => removeVariable(idx)} className="p-2.5 text-gray-600 hover:text-red-500 hover:bg-red-500/10 rounded-xl transition-all opacity-0 group-hover:opacity-100">
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                    {variables.length === 0 && (
                                        <div className="py-12 text-center border-2 border-dashed border-white/5 rounded-2xl opacity-30">
                                            <p className="text-[10px] font-black uppercase tracking-widest">No variables defined. Using defaults.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Right: Cartridge & Summary */}
                        <div className="col-span-12 lg:col-span-4 space-y-6">

                            {/* Bundle Type */}
                            <div className="bg-black/40 border border-white/5 rounded-3xl p-8 shadow-2xl">
                                <h3 className="text-xs font-black text-white uppercase tracking-widest mb-6">Execution Cartridge</h3>
                                <div className="space-y-3">
                                    <CartridgeOption
                                        active={selectedCartridge === 'dbc'}
                                        onClick={() => setSelectedCartridge('dbc')}
                                        title="Databricks Archive"
                                        ext=".dbc"
                                        icon={<Globe size={18} />}
                                    />
                                    <CartridgeOption
                                        active={selectedCartridge === 'sql'}
                                        onClick={() => setSelectedCartridge('sql')}
                                        title="Snowflake Script"
                                        ext=".sql"
                                        icon={<Database size={18} />}
                                    />
                                    <CartridgeOption
                                        active={selectedCartridge === 'yaml'}
                                        onClick={() => setSelectedCartridge('yaml')}
                                        title="Airflow Pipeline"
                                        ext=".yaml"
                                        icon={<HardDrive size={18} />}
                                    />
                                </div>
                            </div>

                            {/* Summary Card */}
                            <div className="bg-gradient-to-br from-emerald-600 to-emerald-900 rounded-3xl p-8 text-white relative overflow-hidden group hover:scale-[1.02] transition-all">
                                <Box className="absolute -right-4 -bottom-4 w-32 h-32 text-white/10 group-hover:rotate-12 transition-transform" />
                                <h3 className="text-xs font-black uppercase tracking-[0.2em] mb-2 opacity-60">Ready for Handover</h3>
                                <div className="text-3xl font-black mb-6">Final Bundle</div>
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">
                                        <CheckCircle2 size={12} className="text-emerald-300" /> 148 Optimized Files
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">
                                        <CheckCircle2 size={12} className="text-emerald-300" /> Compliance Certificate Included
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">
                                        <CheckCircle2 size={12} className="text-emerald-300" /> Variable Payload Attached
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function CartridgeOption({ active, onClick, title, ext, icon }: any) {
    return (
        <button
            onClick={onClick}
            className={`w-full p-4 rounded-2xl border flex items-center justify-between transition-all ${active ? 'bg-emerald-600/10 border-emerald-500 shadow-lg shadow-emerald-500/10' : 'bg-white/5 border-white/5 hover:border-white/10 opacity-60 hover:opacity-100'}`}
        >
            <div className="flex items-center gap-4">
                <div className={`p-2.5 rounded-xl ${active ? 'bg-emerald-500 text-white' : 'bg-white/5 text-gray-500'}`}>
                    {icon}
                </div>
                <div className="text-left">
                    <div className={`text-xs font-black uppercase tracking-wider ${active ? 'text-white' : 'text-gray-400'}`}>{title}</div>
                    <div className="text-[9px] font-bold text-gray-500 uppercase tracking-widest">{ext} format</div>
                </div>
            </div>
            {active && <Zap size={14} className="text-emerald-500" />}
        </button>
    );
}
