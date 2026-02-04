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
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void;
}

export default function DiscoveryView({ projectId, onStageChange, isFullscreen, onToggleFullscreen, onReset, onBackToCurrent }: DiscoveryViewProps) {
    const [isScanning, setIsScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [scanLogs, setScanLogs] = useState<string[]>([]);
    const [showConflict, setShowConflict] = useState(false);
    const [hasContext, setHasContext] = useState(false);
    const [isApproved, setIsApproved] = useState(false);
    const [isApproving, setIsApproving] = useState(false);

    // Agent S Assessment Results
    const [assessment, setAssessment] = useState<{
        summary: string;
        score: number;
        gaps: any[];
        detectedTech?: string;
    }>({ summary: "", score: 0, gaps: [], detectedTech: "" });

    const logEndRef = useRef<HTMLDivElement>(null);

    const [sourceTech, setSourceTech] = useState("UNKNOWN");

    const normalizeTech = (tech: string) => {
        const t = tech.toUpperCase();
        if (t.includes("SSIS") || t.includes("SQL SERVER") || t.includes("T-SQL") || t.includes("TSQL")) return "SQL_SERVER";
        if (t.includes("ORACLE") || t.includes("PLSQL") || t.includes("PL/SQL")) return "ORACLE";
        if (t.includes("PYTHON") || t.includes("PY")) return "PYTHON";
        if (t.includes("SPARK") || t.includes("DATABRICKS") || t.includes("PYSPARK")) return "DATABRICKS";
        if (t.includes("SNOWFLAKE") || t.includes("SNOWPARK")) return "SNOWFLAKE";
        if (t.includes("FABRIC")) return "FABRIC";
        return t;
    };

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [scanLogs]);

    const runScan = async () => {
        setIsScanning(true);
        setScanLogs(["Initializing Agent S (The Scout)...", "Connecting to repository..."]);
        setScanProgress(10);

        try {
            // ✅ STEP 1: Fetch real file list from Triage folder
            setScanLogs(prev => [...prev, "Scanning Triage folder..."]);

            const filesRes = await fetchWithAuth(`projects/${projectId}/triage/files`);
            const filesData = await filesRes.json();

            if (!filesData || !filesData.success || filesData.file_count === 0) {
                setScanLogs(prev => [...prev,
                    "⚠️ No files found in Triage folder",
                    "Please upload SSIS packages or source files first"
                ]);
                setIsScanning(false);
                setScanProgress(100);
                return;
            }

            // Extract file paths for Agent S
            const file_list = filesData.files.map((f: any) => f.path);

            // Show file statistics
            const fileTypesSummary = Object.entries(filesData.file_types || {})
                .map(([ext, count]) => `${ext}: ${count}`)
                .join(', ');

            setScanLogs(prev => [...prev,
            `✓ Found ${filesData.file_count} files in Triage folder`,
            `  Tech detected: ${fileTypesSummary}`,
                "Analyzing file headers and dependencies..."
            ]);
            setScanProgress(40);

            // ✅ STEP 2: Call Agent S with real file list
            const res = await fetchWithAuth("system/scout/assess", {
                method: "POST",
                body: JSON.stringify({ project_id: projectId, file_list })
            });
            const data = await res.json();

            setScanProgress(70);
            setScanLogs(prev => [...prev,
                "Forensic assessment in progress...",
                "Mapping dependencies and gaps..."
            ]);

            if (data.error) {
                setScanLogs(prev => [...prev, `❌ ERROR: ${data.error}`]);
            } else {
                setAssessment({
                    summary: data.assessment_summary || "Assessment complete",
                    score: data.completeness_score || 0,
                    gaps: data.detected_gaps || [],
                    detectedTech: data.detected_technology || "UNKNOWN"
                });

                setScanLogs(prev => [...prev,
                `✓ Completeness Score: ${data.completeness_score}%`,
                `✓ Detected ${data.detected_gaps?.length || 0} gaps`,
                `✓ Detected tech: ${data.detected_technology || "UNKNOWN"}`,
                    "Discovery Audit Complete."
                ]);

                // Trigger conflict if low score OR tech mismatch
                const detectedNormalized = normalizeTech(data.detected_technology || "");
                const sourceNormalized = normalizeTech(sourceTech);

                const mismatch = data.detected_technology &&
                    sourceTech !== "UNKNOWN" &&
                    detectedNormalized !== sourceNormalized;

                // Only show conflict if there is a real mismatch and we have a decent score
                // or if it's unknown but we detected something.
                if (mismatch || (sourceTech === "UNKNOWN" && data.detected_technology)) {
                    setShowConflict(true);
                } else {
                    setShowConflict(false);
                }
            }
        } catch (e) {
            setScanLogs(prev => [...prev, `❌ Connection failed: ${e}`]);
        } finally {
            setIsScanning(false);
            setScanProgress(100);
        }
    };

    useEffect(() => {
        // Fetch project settings to get Source Tech
        fetchWithAuth(`projects/${projectId}`)
            .then(res => res.json())
            .then(data => {
                if (data.settings?.source_tech) {
                    setSourceTech(data.settings.source_tech);
                }
            })
            .catch(err => console.error("Failed to fetch project settings", err));
    }, [projectId]);

    const handleScan = () => {
        runScan();
    };

    const handleUpdateTech = async () => {
        if (!assessment.detectedTech) return;

        try {
            const res = await fetchWithAuth(`projects/${projectId}/settings`, {
                method: "PATCH",
                body: JSON.stringify({
                    settings: { source_tech: assessment.detectedTech }
                })
            });

            if (res.ok) {
                setSourceTech(assessment.detectedTech);
                setShowConflict(false);
                setScanLogs(prev => [...prev, `✓ Updated project source technology to ${assessment.detectedTech}`]);
            }
        } catch (err) {
            console.error("Failed to update project settings", err);
        }
    };

    const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
    const [isUploading, setIsUploading] = useState(false);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        const formData = new FormData();
        formData.append("files", file);

        try {
            const res = await fetchWithAuth(`projects/${projectId}/triage/upload`, {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                const newFiles = data.files || [];
                setUploadedFiles(prev => [...prev, ...newFiles]);
                setHasContext(true);
                newFiles.forEach((f: string) => {
                    setScanLogs(prev => [...prev, `✓ Uploaded support document: ${f}`]);
                });
            } else {
                alert("Failed to upload file");
            }
        } catch (err) {
            console.error("Upload error:", err);
            alert("Connection error during upload");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#050505]">
            <StageHeader
                title="Stage 1: Technical Discovery"
                subtitle="Agent S: Forensic repository audit and gap detection"
                icon={<Activity className="text-cyan-500" />}
                helpText="Initial analysis to ensure technical consistency and fill tribal knowledge gaps before triage."
                onApprove={async () => {
                    setIsApproving(true);
                    onStageChange(2);
                }}
                approveLabel="Start Triage"
                isApproveDisabled={scanProgress < 100 || showConflict}
                isExecuting={isApproving}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            >
                <div className="flex gap-2">
                    <button
                        onClick={handleScan}
                        disabled={isScanning}
                        className="px-6 py-2.5 bg-cyan-600 text-white rounded-xl text-xs font-bold flex items-center gap-2 hover:bg-cyan-500 transition-all shadow-xl shadow-cyan-600/20 disabled:opacity-50 active:scale-95"
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
                                    <span className="text-xs font-black text-white uppercase">{sourceTech}</span>
                                </div>
                            </div>
                            <div className={`p-4 border rounded-2xl transition-all ${showConflict ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-black/40 border-white/5'}`}>
                                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block mb-2">Detected</span>
                                <div className="flex items-center gap-2">
                                    <Binary size={14} className={showConflict ? 'text-cyan-500' : 'text-gray-400'} />
                                    <span className={`text-xs font-black ${showConflict ? 'text-cyan-500' : 'text-white'}`}>
                                        {assessment.detectedTech || "PENDING"}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {showConflict && (
                            <div className="mt-6 space-y-4 animate-in fade-in slide-in-from-top-2">
                                <div className="flex items-start gap-3 p-4 bg-cyan-500/10 rounded-2xl border border-cyan-500/20">
                                    <ShieldCheck className="text-cyan-500 shrink-0" size={16} />
                                    <p className="text-[10px] text-cyan-200/80 font-bold uppercase tracking-wide leading-relaxed">
                                        You selected {sourceTech}, but my analysis thinks {assessment.detectedTech} is a better match. Do you want to update?
                                    </p>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleUpdateTech}
                                        className="flex-1 py-3 bg-cyan-600 text-white text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-cyan-500 transition-all active:scale-95"
                                    >
                                        Update Selection
                                    </button>
                                    <button
                                        onClick={() => setShowConflict(false)}
                                        className="px-4 py-3 bg-white/5 text-gray-400 text-[10px] font-black uppercase tracking-widest rounded-xl hover:bg-white/10 transition-all"
                                    >
                                        Keep {sourceTech}
                                    </button>
                                </div>
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

                        <div className="space-y-3">
                            {uploadedFiles.map((file, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 animate-in zoom-in-95 group">
                                    <div className="flex items-center gap-3">
                                        <CheckCircle2 size={14} className="text-emerald-500" />
                                        <span className="text-[10px] font-black text-white uppercase tracking-widest truncate max-w-[180px]">
                                            {file}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => {
                                            const newFiles = uploadedFiles.filter((_, i) => i !== idx);
                                            setUploadedFiles(newFiles);
                                            if (newFiles.length === 0) setHasContext(false);
                                        }}
                                        className="text-[9px] font-bold text-gray-500 hover:text-red-500 uppercase transition-colors opacity-0 group-hover:opacity-100"
                                    >
                                        Remove
                                    </button>
                                </div>
                            ))}

                            <label className={`flex flex-col items-center justify-center w-full border-2 border-dashed border-white/5 rounded-2xl cursor-pointer hover:bg-white/5 hover:border-cyan-500/50 transition-all group relative ${uploadedFiles.length > 0 ? 'h-16' : 'h-32'}`}>
                                {isUploading ? (
                                    <div className="flex items-center gap-3">
                                        <RefreshCw size={14} className="text-cyan-500 animate-spin" />
                                        <p className="text-[9px] text-gray-400 font-black uppercase tracking-widest">Uploading...</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center">
                                        <FileUp size={uploadedFiles.length > 0 ? 14 : 20} className="mb-1 text-gray-600 group-hover:text-cyan-500 transition-colors" />
                                        <p className="text-[9px] text-gray-400 font-black uppercase tracking-widest text-center px-4">
                                            {uploadedFiles.length > 0 ? "+ Add More Docs" : "Upload Business Rules / Docs / PDF"}
                                        </p>
                                    </div>
                                )}
                                <input type="file" multiple className="hidden" onChange={handleFileUpload} disabled={isUploading} />
                            </label>
                        </div>
                        <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest mt-4 leading-relaxed">
                            These documents will be used by Agent R and Agent F to respect legacy business rules.
                        </p>
                    </div>

                </div>
            </div>
        </div>
    );
}
