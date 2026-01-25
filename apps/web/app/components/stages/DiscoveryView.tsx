"use client";

import React, { useState, useEffect, useRef } from 'react';
import {
    Search,
    Cpu,
    ShieldAlert,
    FileUp,
    CheckCircle2,
    Terminal,
    Zap,
    AlertCircle,
    ArrowRight,
    SearchCode,
    Activity,
    Database,
    Binary,
    RefreshCw,
    ShieldCheck
} from 'lucide-react';
import StageHeader from '../StageHeader';
import { fetchWithAuth } from '../../lib/auth-client';

interface DiscoveryViewProps {
    projectId: string;
    onStageChange: (stage: number) => void;
}

export default function DiscoveryView({ projectId, onStageChange }: DiscoveryViewProps) {
    const [isScanning, setIsScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [scanLogs, setScanLogs] = useState<string[]>([]);
    const [showConflict, setShowConflict] = useState(false);
    const [hasContext, setHasContext] = useState(false);
    const [isApproved, setIsApproved] = useState(false);

    // Agent S Assessment Results
    const [assessment, setAssessment] = useState<{
        summary: string;
        score: number;
        gaps: any[];
    }>({ summary: "", score: 0, gaps: [] });

    const logEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [scanLogs]);

    const runScan = async () => {
        setIsScanning(true);
        setScanLogs(["Initializing Agent S (The Scout)...", "Establishing connection to repository..."]);
        setScanProgress(10);

        try {
            // Simulated file list for assessment (In Phase 5 this will come from real list_dir)
            const file_list = ["main.ssis", "dtsx_loader.sql", "config.xml", "db_utils.plsql"];

            setScanLogs(prev => [...prev, "Scanning directory structure...", "Analyzing file headers (Dialect Detection)..."]);
            setScanProgress(40);

            const res = await fetchWithAuth("system/scout/assess", {
                method: "POST",
                body: JSON.stringify({ file_list })
            });
            const data = await res.json();

            setScanProgress(70);
            setScanLogs(prev => [...prev, "Forensic assessment in progress...", "Mapping procedural logic complexity..."]);

            if (data.error) {
                setScanLogs(prev => [...prev, `ERROR: ${data.error}`]);
            } else {
                setAssessment({
                    summary: data.assessment_summary,
                    score: data.completeness_score,
                    gaps: data.detected_gaps || []
                });
                setScanLogs(prev => [...prev, "Generating forensic modernization report...", "Discovery Audit Complete."]);

                // Trigger conflict if low score (simulated logic)
                if (data.completeness_score < 50) {
                    setShowConflict(true);
                }
            }
        } catch (e) {
            setScanLogs(prev => [...prev, `Connection failed: ${e}`]);
        } finally {
            setIsScanning(false);
            setScanProgress(100);
        }
    };

    const handleScan = () => {
        runScan();
    };

    return (
        <div className="flex flex-col h-full bg-[#050505]">
            <StageHeader
                title="Stage 0.5: Technical Discovery"
                subtitle="Agent S: Forensic repository audit and gap detection"
                icon={<Activity className="text-cyan-500" />}
                helpText="Initial analysis to ensure technical consistency and fill tribal knowledge gaps before triage."
                onApprove={() => onStageChange(1)}
                approveLabel="Start Triage"
                isApproveDisabled={scanProgress < 100 || showConflict}
            >
                <div className="flex gap-2">
                    <button
                        onClick={handleScan}
                        disabled={isScanning}
                        className="px-6 py-2.5 bg-cyan-600 text-white rounded-xl text-xs font-bold flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 disabled:opacity-50"
                    >
                        {isScanning ? <RefreshCw size={14} className="animate-spin" /> : <Activity size={14} />}
                        {isScanning ? "Scanning..." : "Start Forensic Scan"}
                    </button>
                </div>
            </StageHeader>

            <div className="flex-1 overflow-y-auto p-8 grid grid-cols-12 gap-8 custom-scrollbar">

                {/* Left Side: Agent S Console */}
                <div className="col-span-12 lg:col-span-7 space-y-6">
                    <div className="bg-black/40 border border-white/5 rounded-3xl overflow-hidden flex flex-col h-[500px] shadow-2xl">
                        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-white/5">
                            <div className="flex items-center gap-3">
                                <Terminal size={14} className="text-cyan-500" />
                                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white">Agent S: Forensic Audit</span>
                            </div>
                            {isScanning && (
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 bg-cyan-500 rounded-full animate-ping" />
                                    <span className="text-[9px] font-bold text-cyan-500 uppercase">Scanning...</span>
                                </div>
                            )}
                        </div>
                        <div className="flex-1 p-6 font-mono text-[11px] space-y-2 overflow-y-auto custom-scrollbar-slim bg-[#080808]">
                            {scanLogs.map((log, idx) => (
                                <div key={idx} className={`flex gap-3 ${log.includes('ALERT') ? 'text-amber-500' : 'text-gray-400'}`}>
                                    <span className="text-gray-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                                    <span className={log.includes('Complete') ? 'text-emerald-500 font-bold' : ''}>{log}</span>
                                </div>
                            ))}
                            {scanLogs.length === 0 && !isScanning && (
                                <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
                                    <SearchCode size={48} className="mb-4" />
                                    <p className="text-xs font-bold uppercase tracking-widest">Awaiting execution command...</p>
                                </div>
                            )}
                            <div ref={logEndRef} />
                        </div>
                        {isScanning && (
                            <div className="h-1 bg-white/5 w-full overflow-hidden">
                                <div
                                    className="h-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)] transition-all duration-300"
                                    style={{ width: `${scanProgress}%` }}
                                />
                            </div>
                        )}
                    </div>

                    {/* GAP DETECTION REPORT */}
                    {assessment.summary && (
                        <div className="bg-white/5 border border-white/5 rounded-3xl p-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <ShieldCheck size={18} className="text-emerald-500" />
                                    <h3 className="text-xs font-black uppercase tracking-widest text-white">Forensic Assessment</h3>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Completeness</span>
                                    <div className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-black text-cyan-500">
                                        {assessment.score}%
                                    </div>
                                </div>
                            </div>

                            <p className="text-xs text-gray-400 leading-relaxed mb-6 font-medium">
                                {assessment.summary}
                            </p>

                            <div className="space-y-3">
                                {assessment.gaps.map((gap, idx) => (
                                    <div key={idx} className="p-4 bg-black/40 border border-white/5 rounded-2xl flex items-start gap-4 hover:border-cyan-500/30 transition-colors">
                                        <div className={`p-2 rounded-xl border ${gap.impact === 'HIGH' ? 'bg-red-500/10 border-red-500/30 text-red-500' : 'bg-amber-500/10 border-amber-500/30 text-amber-500'}`}>
                                            <ShieldAlert size={16} />
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-[9px] font-black uppercase tracking-widest text-white">{gap.category}</span>
                                                <span className={`text-[8px] font-black uppercase px-2 py-0.5 rounded-full ${gap.impact === 'HIGH' ? 'bg-red-500/20 text-red-500' : 'bg-amber-500/20 text-amber-500'}`}>
                                                    {gap.impact} IMPACT
                                                </span>
                                            </div>
                                            <p className="text-[11px] text-gray-400 mb-2">{gap.gap_description}</p>
                                            <div className="flex items-center gap-2">
                                                <span className="text-[8px] font-black text-gray-600 uppercase tracking-widest">Recommendation:</span>
                                                <span className="text-[9px] font-bold text-cyan-500 lowercase opacity-80 italic">Upload "{gap.suggested_file}"</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Side: Quality Gates */}
                <div className="col-span-12 lg:col-span-5 space-y-6">

                    {/* Gate 1: Technology Validation */}
                    <div className={`p-6 rounded-3xl border transition-all ${showConflict ? 'bg-amber-500/5 border-amber-500/20' : 'bg-white/5 border-white/5'}`}>
                        <div className="flex items-center gap-3 mb-6">
                            <div className={`p-2 rounded-xl border ${showConflict ? 'bg-amber-500/20 text-amber-500 border-amber-500/30' : 'bg-cyan-500/20 text-cyan-500 border-cyan-500/30'}`}>
                                <Cpu size={18} />
                            </div>
                            <div>
                                <h3 className="text-xs font-black uppercase tracking-widest text-white">Technology Validation</h3>
                                <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-1">Cross-check Audit</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-black/40 border border-white/5 rounded-2xl">
                                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block mb-2">User Input</span>
                                <div className="flex items-center gap-2">
                                    <Database size={14} className="text-gray-400" />
                                    <span className="text-xs font-black text-white">ORACLE</span>
                                </div>
                            </div>
                            <div className={`p-4 border rounded-2xl transition-all ${showConflict ? 'bg-amber-500/10 border-amber-500/30' : 'bg-black/40 border-white/5'}`}>
                                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block mb-2">Detected</span>
                                <div className="flex items-center gap-2">
                                    <Binary size={14} className={showConflict ? 'text-amber-500' : 'text-gray-400'} />
                                    <span className={`text-xs font-black ${showConflict ? 'text-amber-500' : 'text-white'}`}>
                                        {showConflict ? "SQL SERVER" : "PENDING"}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {showConflict && (
                            <div className="mt-6 space-y-4 animate-in fade-in slide-in-from-top-2">
                                <div className="flex items-start gap-3 p-4 bg-amber-500/10 rounded-2xl border border-amber-500/20">
                                    <ShieldAlert className="text-amber-500 shrink-0" size={16} />
                                    <p className="text-[10px] text-amber-200/80 font-bold uppercase tracking-wide leading-relaxed">
                                        Agent S detected SQL Server dialect instead of Oracle. Resolve this conflict to proceed.
                                    </p>
                                </div>
                                <button
                                    onClick={() => setShowConflict(false)}
                                    className="w-full py-3 bg-amber-500 text-black text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-amber-400 transition-all active:scale-95"
                                >
                                    Override: Detected is correct
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Gate 2: Tribal Knowledge Ingestion */}
                    <div className={`p-6 rounded-3xl border transition-all ${hasContext ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-white/5 border-white/5'}`}>
                        <div className="flex items-center gap-3 mb-6">
                            <div className={`p-2 rounded-xl border ${hasContext ? 'bg-emerald-500/20 text-emerald-500 border-emerald-500/30' : 'bg-cyan-500/20 text-cyan-500 border-cyan-500/30'}`}>
                                <FileUp size={18} />
                            </div>
                            <div>
                                <h3 className="text-xs font-black uppercase tracking-widest text-white">Tribal Knowledge Ingest</h3>
                                <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-1">Extra AI Context</p>
                            </div>
                        </div>

                        {!hasContext ? (
                            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/5 rounded-2xl cursor-pointer hover:bg-white/5 hover:border-cyan-500/50 transition-all group">
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <FileUp className="w-8 h-8 mb-3 text-gray-600 group-hover:text-cyan-500 transition-colors" />
                                    <p className="text-[9px] text-gray-400 font-black uppercase tracking-widest">Upload Business Rules / Docs</p>
                                </div>
                                <input type="file" className="hidden" onChange={() => setHasContext(true)} />
                            </label>
                        ) : (
                            <div className="flex items-center justify-between p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 animate-in zoom-in-95">
                                <div className="flex items-center gap-3">
                                    <CheckCircle2 size={16} className="text-emerald-500" />
                                    <span className="text-[10px] font-black text-white uppercase tracking-widest">biz-logic-rules.pdf</span>
                                </div>
                                <button onClick={() => setHasContext(false)} className="text-[9px] font-bold text-emerald-500 uppercase hover:underline">Remove</button>
                            </div>
                        )}
                        <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest mt-4 leading-relaxed">
                            These documents will be used by Agent R and Agent F to respect legacy business rules.
                        </p>
                    </div>

                </div>
            </div>
        </div>
    );
}
