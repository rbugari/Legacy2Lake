"use client";

import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from "../lib/auth-client";
import {
    X,
    ArrowRight,
    ArrowLeft,
    Database,
    Github,
    Upload,
    Server,
    Zap,
    CheckCircle2,
    Shield,
    Box,
    Cloud,
    Code,
    Snowflake,
    PackageCheck
} from 'lucide-react';

interface WizardProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (data: any) => void;
    isCreating: boolean;
}

export default function ProjectWizard({ isOpen, onClose, onCreate, isCreating }: WizardProps) {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        name: "",
        sourceType: "github" as "zip" | "github",
        githubUrl: "",
        origin: "SQL Server",
        destination: "Databricks",
        strategy: "Incremental Modernization"
    });
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    // Dynamic Options State
    const [originsInfo, setOrigins] = useState<any[]>([]);
    const [destinationsInfo, setDestinations] = useState<any[]>([]);
    const [loadingOpts, setLoadingOpts] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setLoadingOpts(true);
            Promise.all([
                fetchWithAuth("system/origins").then(res => res.json()),
                fetchWithAuth("system/destinations").then(res => res.json())
            ]).then(([or, de]) => {
                setOrigins(or.origins || []);
                setDestinations(de.destinations || []);
                setLoadingOpts(false);
            }).catch(err => {
                console.error("Failed to load options", err);
                setLoadingOpts(false);
            });
        }
    }, [isOpen]);

    if (!isOpen) return null;

    // Helper function to get icon and color for tech options
    const getTechIcon = (techName: string, size: number = 20) => {
        const lowerName = techName.toLowerCase();
        
        // Input/Origin technologies
        if (lowerName.includes('sql server')) return { icon: <Database size={size} />, color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500' };
        if (lowerName.includes('oracle')) return { icon: <Database size={size} />, color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500' };
        if (lowerName.includes('ssis')) return { icon: <PackageCheck size={size} />, color: 'text-blue-600', bg: 'bg-blue-600/10', border: 'border-blue-600' };
        if (lowerName.includes('informatica')) return { icon: <Zap size={size} />, color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500' };
        if (lowerName.includes('datastage')) return { icon: <Server size={size} />, color: 'text-purple-500', bg: 'bg-purple-500/10', border: 'border-purple-500' };
        if (lowerName.includes('talend')) return { icon: <Code size={size} />, color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500' };
        
        // Output/Destination technologies
        if (lowerName.includes('databricks') || lowerName.includes('pyspark')) return { icon: <Zap size={size} />, color: 'text-orange-600', bg: 'bg-orange-600/10', border: 'border-orange-600' };
        if (lowerName.includes('fabric')) return { icon: <Box size={size} />, color: 'text-blue-600', bg: 'bg-blue-600/10', border: 'border-blue-600' };
        if (lowerName.includes('snowflake')) return { icon: <Snowflake size={size} />, color: 'text-cyan-500', bg: 'bg-cyan-500/10', border: 'border-cyan-500' };
        if (lowerName.includes('google') || lowerName.includes('gcp') || lowerName.includes('bigquery')) return { icon: <Cloud size={size} />, color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500' };
        if (lowerName.includes('aws') || lowerName.includes('glue') || lowerName.includes('redshift')) return { icon: <Server size={size} />, color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500' };
        if (lowerName.includes('salesforce')) return { icon: <Cloud size={size} />, color: 'text-sky-500', bg: 'bg-sky-500/10', border: 'border-sky-500' };
        if (lowerName.includes('sql')) return { icon: <Code size={size} />, color: 'text-gray-500', bg: 'bg-gray-500/10', border: 'border-gray-500' };
        
        // Default
        return { icon: <Database size={size} />, color: 'text-gray-500', bg: 'bg-gray-500/10', border: 'border-gray-500' };
    };

    const nextStep = () => setStep(s => s + 1);
    const prevStep = () => setStep(s => s - 1);

    const handleSubmit = () => {
        onCreate({ ...formData, file: selectedFile });
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-md" onClick={onClose} />

            <div className="bg-[#0a0a0a] border border-white/5 w-full max-w-2xl rounded-3xl shadow-2xl relative flex flex-col overflow-hidden animate-in zoom-in-95 duration-300">
                {/* Progress Bar */}
                <div className="h-1 bg-white/5 w-full">
                    <div
                        className="h-full bg-cyan-500 transition-all duration-500 shadow-[0_0_15px_rgba(6,182,212,0.5)]"
                        style={{ width: `${(step / 4) * 100}%` }}
                    />
                </div>

                <div className="p-8 pb-4 flex justify-between items-center">
                    <div>
                        <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-cyan-500 mb-1">Step {step} of 4</h3>
                        <h2 className="text-xl font-black text-white uppercase tracking-wider">
                            {step === 1 && "Identity & Purpose"}
                            {step === 2 && "Source Connection"}
                            {step === 3 && "Modernization Target"}
                            {step === 4 && "Review & Launch"}
                        </h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-xl transition-colors text-gray-500"><X size={20} /></button>
                </div>

                <div className="flex-1 p-8 pt-4 overflow-y-auto">
                    {step === 1 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <p className="text-sm text-gray-400">Define the name of your modernization project.</p>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Project Name</label>
                                <input
                                    autoFocus
                                    className="w-full bg-white/5 border border-white/5 rounded-2xl p-5 text-sm text-white outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all"
                                    placeholder="e.g. ERP Migration v2"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="grid grid-cols-2 gap-4">
                                <SelectionCard
                                    active={formData.sourceType === 'github'}
                                    onClick={() => setFormData({ ...formData, sourceType: 'github' })}
                                    icon={<Github size={24} />}
                                    title="GitHub Repository"
                                    description="Sync code directly from git"
                                />
                                <SelectionCard
                                    active={formData.sourceType === 'zip'}
                                    onClick={() => setFormData({ ...formData, sourceType: 'zip' })}
                                    icon={<Upload size={24} />}
                                    title="Package Upload"
                                    description="Local .zip/.rar archive"
                                />
                            </div>

                            {formData.sourceType === 'github' ? (
                                <div className="space-y-2 pt-4">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Repository URL</label>
                                    <input
                                        className="w-full bg-white/5 border border-white/5 rounded-2xl p-5 text-sm text-white outline-none focus:ring-2 focus:ring-cyan-500/30 transition-all"
                                        placeholder="https://github.com/..."
                                        value={formData.githubUrl}
                                        onChange={e => setFormData({ ...formData, githubUrl: e.target.value })}
                                    />
                                </div>
                            ) : (
                                <div className="pt-4">
                                    <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/10 rounded-2xl cursor-pointer hover:bg-white/5 hover:border-cyan-500/50 transition-all">
                                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                            <Upload className="w-8 h-8 mb-4 text-gray-500" />
                                            <p className="mb-2 text-sm text-gray-400 font-bold">
                                                {selectedFile ? selectedFile.name : "Clique para subir archivo"}
                                            </p>
                                        </div>
                                        <input type="file" className="hidden" onChange={e => setSelectedFile(e.target.files?.[0] || null)} />
                                    </label>
                                </div>
                            )}
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Legacy Source (Origin)</label>
                                    <span className="text-[9px] text-gray-600 uppercase tracking-wider">Input Technology</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    {loadingOpts ? (
                                        <div className="col-span-3 text-center py-8 text-xs text-gray-500">Loading inputs...</div>
                                    ) : (
                                        originsInfo.length > 0 ? (
                                            originsInfo.filter(o => o.enabled).map(opt => {
                                                const isActive = formData.origin === opt.name;
                                                const techStyle = getTechIcon(opt.name, 22);
                                                return (
                                                    <button
                                                        key={opt.id}
                                                        onClick={() => setFormData({ ...formData, origin: opt.name })}
                                                        className={`flex flex-col p-4 rounded-2xl border-2 text-left transition-all ${
                                                            isActive
                                                                ? `${techStyle.bg} ${techStyle.border} shadow-lg`
                                                                : 'bg-white/5 border-white/10 hover:border-white/20'
                                                        }`}
                                                        title={opt.desc}
                                                    >
                                                        <div className="flex items-center justify-between mb-3">
                                                            <div className={`p-2 rounded-lg ${isActive ? 'bg-white/10' : 'bg-black/20'}`}>
                                                                <span className={isActive ? techStyle.color : 'text-gray-500'}>
                                                                    {techStyle.icon}
                                                                </span>
                                                            </div>
                                                            {isActive && <CheckCircle2 size={16} className={techStyle.color} />}
                                                        </div>
                                                        <span className={`font-bold text-xs ${isActive ? 'text-white' : 'text-gray-400'}`}>
                                                            {opt.name}
                                                        </span>
                                                        {opt.desc && (
                                                            <span className="text-[9px] text-gray-500 mt-1 leading-tight line-clamp-2">
                                                                {opt.desc}
                                                            </span>
                                                        )}
                                                    </button>
                                                );
                                            })
                                        ) : (
                                            <div className="col-span-3 text-center py-8 text-xs text-gray-500">No origins configured</div>
                                        )
                                    )}
                                </div>
                            </div>
                            
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Target Cloud (Destination)</label>
                                    <span className="text-[9px] text-gray-600 uppercase tracking-wider">Output Technology</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    {loadingOpts ? (
                                        <div className="col-span-3 text-center py-8 text-xs text-gray-500">Loading targets...</div>
                                    ) : (
                                        destinationsInfo.length > 0 ? (
                                            destinationsInfo.filter(d => d.enabled).map(opt => {
                                                const isActive = formData.destination === opt.name;
                                                const techStyle = getTechIcon(opt.name, 22);
                                                return (
                                                    <button
                                                        key={opt.id}
                                                        onClick={() => setFormData({ ...formData, destination: opt.name })}
                                                        className={`flex flex-col p-4 rounded-2xl border-2 text-left transition-all ${
                                                            isActive
                                                                ? `${techStyle.bg} ${techStyle.border} shadow-lg`
                                                                : 'bg-white/5 border-white/10 hover:border-white/20'
                                                        }`}
                                                        title={opt.desc}
                                                    >
                                                        <div className="flex items-center justify-between mb-3">
                                                            <div className={`p-2 rounded-lg ${isActive ? 'bg-white/10' : 'bg-black/20'}`}>
                                                                <span className={isActive ? techStyle.color : 'text-gray-500'}>
                                                                    {techStyle.icon}
                                                                </span>
                                                            </div>
                                                            {isActive && <CheckCircle2 size={16} className={techStyle.color} />}
                                                        </div>
                                                        <span className={`font-bold text-xs ${isActive ? 'text-white' : 'text-gray-400'}`}>
                                                            {opt.name}
                                                        </span>
                                                        {opt.desc && (
                                                            <span className="text-[9px] text-gray-500 mt-1 leading-tight line-clamp-2">
                                                                {opt.desc}
                                                            </span>
                                                        )}
                                                    </button>
                                                );
                                            })
                                        ) : (
                                            <div className="col-span-3 text-center py-8 text-xs text-gray-500">No destinations configured</div>
                                        )
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="bg-white/5 rounded-3xl p-6 border border-white/5 space-y-4">
                                <SummaryRow label="Project" value={formData.name} icon={<Box size={14} />} />
                                <SummaryRow label="Extraction" value={formData.sourceType === 'github' ? 'GitHub Sync' : 'Static Archive'} icon={<Github size={14} />} />
                                <SummaryRow label="Modernization" value={`${formData.origin} ➔ ${formData.destination}`} icon={<Zap size={14} />} />
                            </div>
                            <div className="flex items-center gap-3 p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20">
                                <Shield className="text-emerald-500 shrink-0" size={20} />
                                <p className="text-[10px] font-bold text-emerald-800 dark:text-emerald-400 uppercase tracking-widest leading-relaxed">
                                    Validation complete. Ready to initialize legacy discovery pipeline.
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                <div className="p-8 bg-black/40 border-t border-white/5 flex justify-between items-center bg-black/20">
                    <button
                        onClick={step === 1 ? onClose : prevStep}
                        className="px-6 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors"
                    >
                        {step === 1 ? "Cancel" : "Back"}
                    </button>
                    {step < 4 ? (
                        <button
                            onClick={nextStep}
                            disabled={step === 1 && !formData.name}
                            className="px-10 py-3 bg-white text-black rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-cyan-400 transition-all flex items-center gap-2 active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
                        >
                            Continue <ArrowRight size={14} />
                        </button>
                    ) : (
                        <button
                            onClick={handleSubmit}
                            disabled={isCreating}
                            className="px-10 py-3 bg-cyan-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 flex items-center gap-2 active:scale-95"
                        >
                            {isCreating ? "Initializing..." : "Create Solution"}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

function SelectionCard({ active, onClick, icon, title, description }: any) {
    return (
        <button
            onClick={onClick}
            className={`p-6 rounded-3xl border text-left transition-all ${active ? 'bg-cyan-600/10 border-cyan-500 shadow-xl shadow-cyan-600/10' : 'bg-white/5 border-white/5 hover:border-white/10'}`}
        >
            <div className={`p-3 rounded-2xl w-fit mb-4 ${active ? 'bg-cyan-500 text-white' : 'bg-black/20 text-gray-500'}`}>
                {icon}
            </div>
            <h4 className={`text-sm font-black uppercase tracking-wider mb-1 ${active ? 'text-white' : 'text-gray-400'}`}>{title}</h4>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest leading-relaxed">{description}</p>
        </button>
    );
}

function SummaryRow({ label, value, icon }: any) {
    return (
        <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
            <div className="flex items-center gap-3 text-gray-500">
                {icon}
                <span className="text-[10px] font-bold uppercase tracking-widest">{label}</span>
            </div>
            <span className="text-[10px] font-black text-white uppercase tracking-widest">{value}</span>
        </div>
    );
}
