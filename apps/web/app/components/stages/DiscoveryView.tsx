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
    ShieldCheck,
    Upload,
    X,
    FolderOpen
} from 'lucide-react';
import StageHeader from '../StageHeader';
import { fetchWithAuth } from '../../lib/auth-client';
import UnifiedLogViewer from '../UnifiedLogViewer';
import { useConfirm } from '../../hooks/useConfirm';

interface DiscoveryViewProps {
    projectId: string;
    onStageChange: (stage: number) => void;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void;
    activeSection?: string;
    onSectionChange?: (section: string) => void;
}

export default function DiscoveryView({
    projectId,
    onStageChange,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent,
    activeSection = 'assessment',
    onSectionChange
}: DiscoveryViewProps) {
    const { confirm, ConfirmDialog } = useConfirm();
    const [isScanning, setIsScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [scanLogs, setScanLogs] = useState<string[]>([]);
    const [showConflict, setShowConflict] = useState(false);
    const [hasContext, setHasContext] = useState(false);
    const [isApproved, setIsApproved] = useState(false);
    const [isApproving, setIsApproving] = useState(false);

    // File Inventory & Pre-Classification (NEW)
    const [fileInventory, setFileInventory] = useState<any[]>([]);
    const [showClassification, setShowClassification] = useState(false);

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

            const filesRes = await fetchWithAuth(`projects/${projectId}/source/files`);
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

            // Show file statistics
            const fileTypesSummary = Object.entries(filesData.file_types || {})
                .map(([ext, count]) => `${ext}: ${count}`)
                .join(', ');

            setScanLogs(prev => [...prev,
            `✓ Found ${filesData.file_count} files in Triage folder`,
            `  Tech detected: ${fileTypesSummary}`,
                "Running Quick Assessment (v4.0 Zero-Hardcode)..."
            ]);
            setScanProgress(40);

            // ✅ STEP 2: Call Quick Assessment (replaces Agent S in v4.0)
            const res = await fetchWithAuth(`projects/${projectId}/quick-assessment`, {
                method: "POST"
            });
            const data = await res.json();

            setScanProgress(70);
            setScanLogs(prev => [...prev,
                "Analyzing viability and detecting blockers...",
                "Mapping dependencies and gaps..."
            ]);

            if (data.error) {
                setScanLogs(prev => [...prev, `❌ ERROR: ${data.error}`]);
            } else {
                setAssessment({
                    summary: data.llm_opinion || `Viability: ${data.semaforo?.toUpperCase() || 'UNKNOWN'}`,
                    score: data.score || 0,
                    gaps: data.blockers || [],
                    detectedTech: data.detected_techs?.[0] || "UNKNOWN"
                });

                setScanLogs(prev => [...prev,
                `✓ Viability Score: ${data.score}% (${data.semaforo || 'unknown'})`,
                `✓ Detected ${data.blockers?.length || 0} blockers`,
                `✓ Detected tech: ${data.detected_techs?.[0] || "UNKNOWN"}`,
                    "Discovery Audit Complete."
                ]);

                // Trigger conflict if low score OR tech mismatch
                const detectedNormalized = normalizeTech(data.detected_techs?.[0] || "");
                const sourceNormalized = normalizeTech(sourceTech);

                const mismatch = data.detected_techs?.[0] &&
                    sourceTech !== "UNKNOWN" &&
                    detectedNormalized !== sourceNormalized;

                // Only show conflict if there is a real mismatch and we have a decent score
                // or if it's unknown but we detected something.
                if (mismatch || (sourceTech === "UNKNOWN" && data.detected_techs?.[0])) {
                    setShowConflict(true);
                } else {
                    setShowConflict(false);
                }

                // ✅ NEW: Fetch file inventory for pre-classification
                setScanLogs(prev => [...prev, "Loading file classification suggestions..."]);
                try {
                    const invRes = await fetchWithAuth(`projects/${projectId}/file-inventory`);
                    const invData = await invRes.json();

                    if (invData.success && invData.files) {
                        setFileInventory(invData.files);
                        setShowClassification(true);
                        setScanLogs(prev => [...prev, `✓ Ready for classification: ${invData.file_count} files`]);
                    }
                } catch (err) {
                    console.error("Failed to load file inventory:", err);
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

    const handleScan = async () => {
        const runOk = await confirm({
            title: 'Run Forensic Scan',
            description: 'This will analyze the repository to detect technical stack and viabilities. Are you sure you want to proceed?',
            confirmLabel: 'Run Scan',
            variant: 'execute'
        });

        if (runOk) {
            runScan();
            onSectionChange?.('logs');
        } else if (activeSection === 'run-scan') {
            onSectionChange?.('assessment');
        }
    };

    useEffect(() => {
        if (activeSection === 'run-scan' && !isScanning) {
            handleScan();
        }
    }, [activeSection, isScanning]);

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
            const res = await fetchWithAuth(`projects/${projectId}/source/upload`, {
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

    // Pre-Classification Handlers
    const handleFileClassification = (index: number, classification: string) => {
        setFileInventory(prev => prev.map((file, idx) =>
            idx === index ? { ...file, classification } : file
        ));
    };

    const handleFileInclude = (index: number, include: boolean) => {
        setFileInventory(prev => prev.map((file, idx) =>
            idx === index ? { ...file, include } : file
        ));
    };

    const bulkClassify = (classification: string) => {
        setFileInventory(prev => prev.map(file => ({ ...file, classification })));
    };

    const bulkInclude = (include: boolean) => {
        setFileInventory(prev => prev.map(file => ({ ...file, include })));
    };

    const bulkClassifyByCategory = () => {
        // Auto-classify: migrable → CORE, soporte → SUPPORT, docs/unknown → IGNORED
        setFileInventory(prev => prev.map(file => {
            if (file.category === 'migrable') return { ...file, classification: 'CORE', include: true };
            if (file.category === 'soporte') return { ...file, classification: 'SUPPORT', include: true };
            return { ...file, classification: 'IGNORED', include: false };
        }));
    };

    const handleStartTriage = async () => {
        setIsApproving(true);

        // Save pre-classification if user made any adjustments
        if (showClassification && fileInventory.length > 0) {
            try {
                const classification: Record<string, any> = {};
                fileInventory.forEach(file => {
                    classification[file.path] = {
                        classification: file.classification,
                        include: file.include
                    };
                });

                await fetchWithAuth(`projects/${projectId}/pre-classification`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ classification })
                });

                setScanLogs(prev => [...prev, `✓ Saved classification for ${Object.keys(classification).length} files`]);

                // Call promotion endpoint to copy files to Triage
                setScanLogs(prev => [...prev, `Promoting ${Object.values(classification).filter((c: any) => c.include).length} selected files to Triage...`]);
                const promoteRes = await fetchWithAuth(`projects/${projectId}/source/promote`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ classification })
                });

                if (promoteRes.ok) {
                    const promoteData = await promoteRes.json();
                    if (promoteData.success) {
                        setScanLogs(prev => [...prev, `✓ Promoted ${promoteData.promoted_count} files to Triage.`]);
                    } else {
                        setScanLogs(prev => [...prev, `⚠️ Error promoting files: ${promoteData.errors?.join(", ")}`]);
                    }
                } else {
                    setScanLogs(prev => [...prev, `❌ Failed to promote files to Triage.`]);
                }
            } catch (err) {
                console.error("Failed to save pre-classification:", err);
                alert("Warning: Failed to save classification settings");
            }
        }

        onStageChange(1);
    };

    return (
        <div className="flex flex-col h-full bg-[#050505]">
            <StageHeader
                title="Stage 0: Technical Discovery"
                subtitle="The Scout: Forensic repository audit and gap detection"
                icon={<Activity className="text-cyan-500" />}
                helpText="Initial analysis to ensure technical consistency and fill tribal knowledge gaps before triage."
                onApprove={handleStartTriage}
                approveLabel={showClassification ? `Start Triage (${fileInventory.filter(f => f.include).length} files)` : "Start Triage"}
                isApproveDisabled={scanProgress < 100 || showConflict || (showClassification && fileInventory.filter(f => f.include).length === 0)}
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

            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">

                {/* LOGS VIEW */}
                {activeSection === 'logs' && (
                    <div className="h-full flex flex-col">
                        <div className="flex-1 min-h-[500px]">
                            <UnifiedLogViewer
                                mode="realtime"
                                projectId={projectId}
                                logs={scanLogs}
                                isRunning={isScanning}
                                processName="Forensic Discovery Analysis"
                                variant="embedded"
                            />
                        </div>
                    </div>
                )}

                {/* FORENSIC ASSESSMENT */}
                {activeSection === 'assessment' && (
                    <div className="max-w-4xl mx-auto space-y-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <ShieldCheck size={24} className="text-emerald-500" />
                                Forensic Assessment
                            </h2>
                        </div>
                        {assessment.summary ? (
                            <div className="bg-white/5 border border-white/5 rounded-3xl p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-sm font-black uppercase tracking-widest text-white">Gap Detection Summary</h3>
                                    <div className="flex items-center gap-2">
                                        <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Completeness</span>
                                        <div className="px-4 py-1.5 bg-white/5 rounded-full text-xs font-black text-cyan-500">
                                            {assessment.score}%
                                        </div>
                                    </div>
                                </div>

                                <p className="text-sm text-gray-300 leading-relaxed mb-8 font-medium bg-black/20 p-6 rounded-2xl border border-white/5">
                                    {assessment.summary}
                                </p>

                                <div className="space-y-4">
                                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Identified Gaps</h4>
                                    {assessment.gaps.map((gap, idx) => (
                                        <div key={idx} className="p-5 bg-black/40 border border-white/5 rounded-2xl flex items-start gap-5 hover:border-cyan-500/30 transition-colors">
                                            <div className={`p-3 rounded-xl border ${gap.impact === 'HIGH' ? 'bg-red-500/10 border-red-500/30 text-red-500' : 'bg-amber-500/10 border-amber-500/30 text-amber-500'}`}>
                                                <ShieldAlert size={20} />
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-xs font-black uppercase tracking-widest text-white">{gap.category}</span>
                                                    <span className={`text-[10px] font-black uppercase px-3 py-1 rounded-full ${gap.impact === 'HIGH' ? 'bg-red-500/20 text-red-500' : 'bg-amber-500/20 text-amber-500'}`}>
                                                        {gap.impact} IMPACT
                                                    </span>
                                                </div>
                                                <p className="text-sm text-gray-400 mb-3 leading-relaxed">{gap.gap_description}</p>
                                                <div className="flex items-center gap-2 bg-white/5 p-3 rounded-xl border border-white/5">
                                                    <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Recommendation:</span>
                                                    <span className="text-[11px] font-bold text-cyan-500 opacity-90 italic">Upload "{gap.suggested_file}"</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    {assessment.gaps.length === 0 && (
                                        <div className="text-center p-8 text-gray-500 text-sm">No critical gaps identified.</div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="h-[400px] flex flex-col items-center justify-center text-center opacity-50 border border-dashed border-white/10 rounded-3xl">
                                <SearchCode size={48} className="mb-4 text-cyan-500" />
                                <p className="text-sm font-bold uppercase tracking-widest">Run the Forensic Scan to view assessment.</p>
                                <button
                                    onClick={() => onSectionChange?.('run-scan')}
                                    className="mt-6 px-6 py-2 bg-white/5 rounded-xl text-xs font-bold hover:bg-white/10 transition-colors uppercase tracking-widest"
                                >
                                    Go to Scan
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* TECH VALIDATION */}
                {activeSection === 'validation' && (
                    <div className="max-w-4xl mx-auto space-y-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Cpu size={24} className="text-cyan-500" />
                                Tech Validation
                            </h2>
                        </div>

                        <div className={`p-8 rounded-3xl border transition-all ${showConflict ? 'bg-amber-500/5 border-amber-500/20' : 'bg-white/5 border-white/5'}`}>
                            <div className="flex items-center gap-4 mb-8">
                                <div className={`p-3 rounded-xl border ${showConflict ? 'bg-amber-500/20 text-amber-500 border-amber-500/30' : 'bg-cyan-500/20 text-cyan-500 border-cyan-500/30'}`}>
                                    <Cpu size={24} />
                                </div>
                                <div>
                                    <h3 className="text-sm font-black uppercase tracking-widest text-white">Cross-check Audit</h3>
                                    <p className="text-xs text-gray-500 font-bold mt-1">Comparing repository contents against project settings.</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div className="p-6 bg-black/40 border border-white/5 rounded-2xl">
                                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block mb-3">User Input</span>
                                    <div className="flex items-center gap-3">
                                        <Database size={20} className="text-gray-400" />
                                        <span className="text-lg font-black text-white uppercase">{sourceTech}</span>
                                    </div>
                                </div>
                                <div className={`p-6 border rounded-2xl transition-all ${showConflict ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-black/40 border-white/5'}`}>
                                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block mb-3">Agent Detected</span>
                                    <div className="flex items-center gap-3">
                                        <Binary size={20} className={showConflict ? 'text-cyan-500' : 'text-gray-400'} />
                                        <span className={`text-lg font-black ${showConflict ? 'text-cyan-500' : 'text-white'}`}>
                                            {assessment.detectedTech || "PENDING SCAN"}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {showConflict && (
                                <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-top-2">
                                    <div className="flex items-start gap-4 p-5 bg-cyan-500/10 rounded-2xl border border-cyan-500/20">
                                        <ShieldCheck className="text-cyan-500 shrink-0" size={20} />
                                        <p className="text-xs text-cyan-200/90 font-bold leading-relaxed">
                                            You selected <span className="text-white bg-black/30 px-2 py-0.5 rounded">{sourceTech}</span>, but the forensic analysis concludes that <span className="text-white bg-black/30 px-2 py-0.5 rounded">{assessment.detectedTech}</span> is a better match. Do you want to update the project configuration?
                                        </p>
                                    </div>
                                    <div className="flex gap-4">
                                        <button
                                            onClick={handleUpdateTech}
                                            className="px-6 py-3 bg-cyan-600 text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-cyan-500 transition-all shadow-lg active:scale-95"
                                        >
                                            Update Configuration
                                        </button>
                                        <button
                                            onClick={() => setShowConflict(false)}
                                            className="px-6 py-3 bg-white/5 border border-white/10 text-gray-400 text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white/10 hover:text-white transition-all"
                                        >
                                            Keep {sourceTech}
                                        </button>
                                    </div>
                                </div>
                            )}

                            {!showConflict && assessment.detectedTech && (
                                <div className="mt-8 flex items-center gap-3 p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20">
                                    <CheckCircle2 className="text-emerald-500" size={20} />
                                    <p className="text-sm text-emerald-400 font-medium">Technology configuration matches repository contents.</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* TRIBAL KNOWLEDGE */}
                {activeSection === 'upload' && (
                    <div className="max-w-4xl mx-auto space-y-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Upload size={24} className="text-purple-500" />
                                Tribal Knowledge Ingest
                            </h2>
                        </div>

                        <div className="p-8 rounded-3xl border bg-white/5 border-white/5">
                            <p className="text-sm text-gray-400 mb-8 leading-relaxed">
                                Upload business rules, data dictionaries, mapping documents, or any other tribal knowledge that can help the AI agents understand the legacy system context better.
                            </p>

                            <label className={`flex flex-col items-center justify-center w-full border-2 border-dashed border-white/10 rounded-3xl cursor-pointer hover:bg-white/5 hover:border-purple-500/50 transition-all group relative h-48 mb-8`}>
                                {isUploading ? (
                                    <div className="flex flex-col items-center gap-4">
                                        <RefreshCw size={24} className="text-purple-500 animate-spin" />
                                        <p className="text-xs text-gray-300 font-black uppercase tracking-widest">Uploading securely...</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center">
                                        <div className="p-4 bg-purple-500/10 rounded-full mb-4 group-hover:scale-110 transition-transform">
                                            <FileUp size={32} className="text-purple-500" />
                                        </div>
                                        <p className="text-sm text-white font-bold mb-2">
                                            Click to browse or drag and drop
                                        </p>
                                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                                            PDF, DOCX, TXT, CSV, XLSX
                                        </p>
                                    </div>
                                )}
                                <input type="file" multiple className="hidden" onChange={handleFileUpload} disabled={isUploading} />
                            </label>

                            {uploadedFiles.length > 0 && (
                                <div className="space-y-4">
                                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Ingested Documents</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {uploadedFiles.map((file, idx) => (
                                            <div key={idx} className="flex items-center justify-between p-4 bg-purple-500/10 rounded-2xl border border-purple-500/20 group animate-in zoom-in-95">
                                                <div className="flex items-center gap-3 overflow-hidden">
                                                    <CheckCircle2 size={18} className="text-purple-500 shrink-0" />
                                                    <span className="text-xs font-bold text-white truncate">
                                                        {file}
                                                    </span>
                                                </div>
                                                <button
                                                    onClick={() => {
                                                        const newFiles = uploadedFiles.filter((_, i) => i !== idx);
                                                        setUploadedFiles(newFiles);
                                                        if (newFiles.length === 0) setHasContext(false);
                                                    }}
                                                    className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded-xl transition-colors ml-2 shrink-0"
                                                    title="Remove document"
                                                >
                                                    <X size={16} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* PRE-CLASSIFICATION GRID (NEW) */}
                {activeSection === 'files' && (
                    <div className="space-y-6">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                    <FolderOpen size={24} className="text-blue-500" />
                                    File Pre-Classification
                                </h2>
                                <p className="text-sm text-gray-400 mt-1">
                                    Classify files BEFORE Triage to optimize analysis: <strong className="text-cyan-400">CORE</strong> = deep migration, <strong className="text-purple-400">SUPPORT</strong> = read-only context, <strong className="text-gray-500">IGNORED</strong> = skip.
                                </p>
                            </div>
                            {fileInventory.length > 0 && (
                                <div className="text-sm border border-white/10 bg-black/40 px-5 py-2.5 rounded-xl flex gap-4">
                                    <div><span className="text-gray-400">Total:</span> <span className="font-bold">{fileInventory.length}</span></div>
                                    <div><span className="text-gray-400">Selected:</span> <span className="font-bold text-cyan-500">{fileInventory.filter(f => f.include).length}</span></div>
                                </div>
                            )}
                        </div>

                        {showClassification && fileInventory.length > 0 ? (
                            <div className="bg-black/40 border border-white/5 rounded-2xl overflow-hidden flex flex-col h-[600px]">
                                {/* Bulk Actions */}
                                <div className="p-4 border-b border-white/5 bg-white/5 flex gap-3 flex-wrap items-center">
                                    <button
                                        onClick={bulkClassifyByCategory}
                                        className="px-4 py-2 bg-blue-600/20 border border-blue-500/30 text-blue-400 rounded-lg text-xs font-bold hover:bg-blue-600/30 transition-all flex items-center gap-2"
                                    >
                                        <Zap size={14} /> Auto-Classify
                                    </button>
                                    <div className="w-px h-6 bg-white/10 mx-2"></div>
                                    <button
                                        onClick={() => bulkClassify('CORE')}
                                        className="px-3 py-1.5 bg-cyan-600/10 text-cyan-500 hover:bg-cyan-600/20 rounded text-xs font-medium transition-colors"
                                    >
                                        All CORE
                                    </button>
                                    <button
                                        onClick={() => bulkClassify('SUPPORT')}
                                        className="px-3 py-1.5 bg-purple-600/10 text-purple-400 hover:bg-purple-600/20 rounded text-xs font-medium transition-colors"
                                    >
                                        All SUPPORT
                                    </button>
                                    <button
                                        onClick={() => bulkClassify('IGNORED')}
                                        className="px-3 py-1.5 bg-gray-600/10 text-gray-400 hover:bg-gray-600/20 rounded text-xs font-medium transition-colors"
                                    >
                                        All IGNORED
                                    </button>
                                    <div className="w-px h-6 bg-white/10 mx-2"></div>
                                    <button
                                        onClick={() => bulkInclude(true)}
                                        className="px-3 py-1.5 bg-emerald-600/10 text-emerald-500 hover:bg-emerald-600/20 rounded text-xs font-medium transition-colors"
                                    >
                                        Select All
                                    </button>
                                    <button
                                        onClick={() => bulkInclude(false)}
                                        className="px-3 py-1.5 bg-white/5 text-gray-400 hover:bg-white/10 rounded text-xs font-medium transition-colors"
                                    >
                                        Deselect All
                                    </button>
                                </div>

                                <div className="flex-1 overflow-auto custom-scrollbar">
                                    <table className="w-full text-sm">
                                        <thead className="bg-white/5 text-gray-400 uppercase text-[10px] font-black tracking-widest sticky top-0 backdrop-blur-md">
                                            <tr>
                                                <th className="px-6 py-4 text-left">File Path</th>
                                                <th className="px-6 py-4 text-left w-48">Detected Type</th>
                                                <th className="px-6 py-4 text-right w-32">Size</th>
                                                <th className="px-6 py-4 text-left w-48">Classification</th>
                                                <th className="px-6 py-4 text-center w-24">Include</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-white/5">
                                            {fileInventory.map((file, idx) => (
                                                <tr key={idx} className={`hover:bg-white/5 transition-colors ${file.include === false ? 'opacity-50 grayscale' : ''}`}>
                                                    <td className="px-6 py-3 font-mono text-xs text-white max-w-sm truncate" title={file.name}>
                                                        {file.name}
                                                    </td>
                                                    <td className="px-6 py-3">
                                                        <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${file.category === 'migrable' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/20' :
                                                            file.category === 'soporte' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/20' :
                                                                file.category === 'documentacion' ? 'bg-gray-500/20 text-gray-400 border border-gray-500/20' :
                                                                    'bg-red-500/20 text-red-400 border border-red-500/20'
                                                            }`}>
                                                            {file.category || 'unknown'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-3 text-gray-400 text-xs text-right font-mono">
                                                        {(file.size / 1024).toFixed(1)} KB
                                                    </td>
                                                    <td className="px-6 py-3">
                                                        <select
                                                            value={file.classification || 'CORE'}
                                                            onChange={(e) => handleFileClassification(idx, e.target.value)}
                                                            className={`w-full bg-black/60 border rounded-lg px-3 py-2 text-xs font-bold transition-colors outline-none focus:ring-1 ${file.classification === 'CORE' ? 'border-cyan-500/30 text-cyan-400 focus:ring-cyan-500' :
                                                                file.classification === 'SUPPORT' ? 'border-purple-500/30 text-purple-400 focus:ring-purple-500' :
                                                                    'border-gray-600 text-gray-400 focus:ring-gray-500'
                                                                }`}
                                                        >
                                                            <option value="CORE">CORE</option>
                                                            <option value="SUPPORT">SUPPORT</option>
                                                            <option value="IGNORED">IGNORED</option>
                                                        </select>
                                                    </td>
                                                    <td className="px-6 py-3 text-center">
                                                        <input
                                                            type="checkbox"
                                                            checked={file.include !== false}
                                                            onChange={(e) => handleFileInclude(idx, e.target.checked)}
                                                            className="w-5 h-5 rounded bg-black/40 border-white/20 text-blue-500 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer transition-all"
                                                        />
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ) : (
                            <div className="h-[400px] flex flex-col items-center justify-center text-center opacity-50 border border-dashed border-white/10 rounded-3xl">
                                <SearchCode size={48} className="mb-4 text-gray-500" />
                                <p className="text-sm font-bold text-gray-400 max-w-md">No file inventory available. Run the Forensic Scan first to analyze the repository contents.</p>
                                <button
                                    onClick={() => onSectionChange?.('run-scan')}
                                    className="mt-6 px-6 py-2 bg-white/5 rounded-xl text-xs font-bold hover:bg-white/10 transition-colors uppercase tracking-widest text-white"
                                >
                                    Go to Scan
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
            {ConfirmDialog}
        </div>
    );
}
