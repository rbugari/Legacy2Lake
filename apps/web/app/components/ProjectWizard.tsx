"use client";

import React, { useState } from 'react';
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
    Box
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

    if (!isOpen) return null;

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
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Legacy Source (Origin)</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {['SQL Server', 'Oracle', 'AS400'].map(opt => (
                                        <button key={opt} onClick={() => setFormData({ ...formData, origin: opt })} className={`p-4 rounded-2xl border text-[10px] font-black uppercase tracking-widest transition-all ${formData.origin === opt ? 'bg-cyan-600 border-cyan-500 text-white shadow-lg shadow-cyan-600/20' : 'bg-white/5 border-white/5 text-gray-500 hover:bg-white/10'}`}>{opt}</button>
                                    ))}
                                </div>
                            </div>
                            <div className="space-y-4">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Target Cloud (Destination)</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {['Databricks', 'Snowflake', 'Fabric'].map(opt => (
                                        <button key={opt} onClick={() => setFormData({ ...formData, destination: opt })} className={`p-4 rounded-2xl border text-[10px] font-black uppercase tracking-widest transition-all ${formData.destination === opt ? 'bg-emerald-600 border-emerald-500 text-white shadow-lg shadow-emerald-600/20' : 'bg-white/5 border-white/5 text-gray-500 hover:bg-white/10'}`}>{opt}</button>
                                    ))}
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
