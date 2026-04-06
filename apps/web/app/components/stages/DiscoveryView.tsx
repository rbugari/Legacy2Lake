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
import ReadinessBadge from '../ReadinessBadge';

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

interface DiscoveryIntake {
    business_domain: string;
    migration_goals: string;
    critical_processes: string;
    operational_constraints: string;
    data_sensitivity: string;
    notes: string;
}

const emptyIntake: DiscoveryIntake = {
    business_domain: '',
    migration_goals: '',
    critical_processes: '',
    operational_constraints: '',
    data_sensitivity: '',
    notes: ''
};

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
    const SUPPORTED_SOURCE_TECHS = new Set([
        "MYSQL",
        "SQL_SERVER",
        "ORACLE",
        "SSIS",
        "INFORMATICA",
        "DATASTAGE",
        "PENTAHO",
    ]);

    const { confirm, ConfirmDialog } = useConfirm();
    const [isScanning, setIsScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const [scanLogs, setScanLogs] = useState<string[]>([]);
    const [showConflict, setShowConflict] = useState(false);
    const [hasContext, setHasContext] = useState(false);
    const [isApproved, setIsApproved] = useState(false);
    const [isApproving, setIsApproving] = useState(false);
    const [projectSettings, setProjectSettings] = useState<Record<string, any>>({});
    const [projectIntake, setProjectIntake] = useState<DiscoveryIntake>(emptyIntake);
    const [savingIntake, setSavingIntake] = useState(false);
    const [evidenceItems, setEvidenceItems] = useState<any[]>([]);
    const [savingEvidenceKey, setSavingEvidenceKey] = useState<string | null>(null);

    // Readiness badge refresh trigger (incremented after a scan completes)
    const [readinessKey, setReadinessKey] = useState(0);

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
    const sourceTechRef = useRef(sourceTech);

    useEffect(() => {
        sourceTechRef.current = sourceTech;
    }, [sourceTech]);

    const normalizeTech = (tech: string) => {
        const t = tech.toUpperCase();
        if (t.includes("MYSQL") || t.includes("MARIADB")) return "MYSQL";
        if (t.includes("SSIS") || t.includes("SQL SERVER") || t.includes("T-SQL") || t.includes("TSQL")) return "SQL_SERVER";
        if (t.includes("ORACLE") || t.includes("PLSQL") || t.includes("PL/SQL")) return "ORACLE";
        if (t.includes("PYTHON") || t.includes("PY")) return "PYTHON";
        if (t.includes("SPARK") || t.includes("DATABRICKS") || t.includes("PYSPARK")) return "DATABRICKS";
        if (t.includes("SNOWFLAKE") || t.includes("SNOWPARK")) return "SNOWFLAKE";
        if (t.includes("FABRIC")) return "FABRIC";
        return t;
    };

    const isCompatibleTech = (source: string, detected: string) => {
        const s = normalizeTech(source || "");
        const d = normalizeTech(detected || "");

        if (!s || !d || s === "UNKNOWN" || d === "UNKNOWN") return false;
        if (s === d) return true;

        // Generic SQL detection is acceptable for MySQL/MariaDB source projects.
        if (s === "MYSQL" && d === "SQL") return true;

        return false;
    };

    const isSupportedSourceTech = (tech: string) => {
        const n = normalizeTech(tech || "");
        return SUPPORTED_SOURCE_TECHS.has(n);
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
                const currentSourceTech = sourceTechRef.current;
                const detectedNormalized = normalizeTech(data.detected_techs?.[0] || "");
                const sourceNormalized = normalizeTech(currentSourceTech);

                const mismatch = data.detected_techs?.[0] &&
                    currentSourceTech !== "UNKNOWN" &&
                    !isCompatibleTech(currentSourceTech, data.detected_techs?.[0]);

                // Only show conflict if there is a real mismatch and we have a decent score
                // or if it's unknown but we detected something.
                if (mismatch || (currentSourceTech === "UNKNOWN" && data.detected_techs?.[0])) {
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

                try {
                    const evidenceRes = await fetchWithAuth(`projects/${projectId}/evidence`);
                    const evidenceData = await evidenceRes.json();

                    if (evidenceData.success && Array.isArray(evidenceData.items)) {
                        setEvidenceItems(evidenceData.items);
                        setScanLogs(prev => [...prev, `✓ Loaded ${evidenceData.count || evidenceData.items.length} evidence items`]);
                    }
                } catch (err) {
                    console.error("Failed to load evidence items:", err);
                }

                // Trigger readiness recompute after successful scan
                setReadinessKey(k => k + 1);
            }
        } catch (e) {
            setScanLogs(prev => [...prev, `❌ Connection failed: ${e}`]);
        } finally {
            setIsScanning(false);
            setScanProgress(100);
        }
    };

    useEffect(() => {
        // Fetch project settings to get Source Tech + structured intake
        fetchWithAuth(`projects/${projectId}`)
            .then(res => res.json())
            .then(data => {
                if (data?.settings) {
                    setProjectSettings(data.settings);
                    if (data.settings.source_tech) {
                        setSourceTech(data.settings.source_tech);
                    }
                    if (data.settings.discovery_intake && typeof data.settings.discovery_intake === 'object') {
                        setProjectIntake(prev => ({
                            ...prev,
                            ...data.settings.discovery_intake
                        }));
                    }
                }
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
        if (!isSupportedSourceTech(assessment.detectedTech)) {
            setScanLogs(prev => [
                ...prev,
                `⚠️ Detected origin '${assessment.detectedTech}' is not supported. Report this origin to admin.`
            ]);
            return;
        }

        try {
            const res = await fetchWithAuth(`projects/${projectId}/settings`, {
                method: "PATCH",
                body: JSON.stringify({
                    ...projectSettings,
                    source_tech: assessment.detectedTech,
                })
            });

            if (res.ok) {
                setSourceTech(assessment.detectedTech);
                setProjectSettings(prev => ({
                    ...prev,
                    source_tech: assessment.detectedTech
                }));
                setShowConflict(false);
                setScanLogs(prev => [...prev, `✓ Updated project source technology to ${assessment.detectedTech}`]);
                setReadinessKey(k => k + 1);
            }
        } catch (err) {
            console.error("Failed to update project settings", err);
        }
    };

    const handleSaveIntake = async () => {
        setSavingIntake(true);

        try {
            const nextSettings = {
                ...projectSettings,
                discovery_intake: {
                    ...projectIntake,
                    updated_at: new Date().toISOString()
                }
            };

            const res = await fetchWithAuth(`projects/${projectId}/settings`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(nextSettings)
            });

            if (res.ok) {
                setProjectSettings(nextSettings);
                setReadinessKey(k => k + 1);
                setScanLogs(prev => [...prev, "✓ Project intake saved and readiness refreshed"]);
            } else {
                alert("Failed to save project intake");
            }
        } catch (err) {
            console.error("Failed to save project intake", err);
            alert("Connection error while saving project intake");
        } finally {
            setSavingIntake(false);
        }
    };

    const handleEvidenceReview = async (reviewKey: string, state: 'detected' | 'reviewed' | 'pinned' | 'dismissed', note?: string) => {
        setSavingEvidenceKey(reviewKey);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/evidence/review`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ review_key: reviewKey, state, note })
            });

            if (res.ok) {
                setEvidenceItems(prev => prev.map(item => (
                    item.review_key === reviewKey
                        ? { ...item, review_status: state, review_note: note || item.review_note, review_updated_at: new Date().toISOString() }
                        : item
                )));
                setScanLogs(prev => [...prev, `✓ Evidence ${state}: ${reviewKey.slice(0, 8)}...`]);
            }
        } catch (err) {
            console.error("Failed to update evidence review", err);
        } finally {
            setSavingEvidenceKey(null);
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
        // Auto-classify: migratable → CORE, support → SUPPORT, docs/unknown → IGNORED
        setFileInventory(prev => prev.map(file => {
            if (file.category === 'migratable') return { ...file, classification: 'CORE', include: true };
            if (file.category === 'support') return { ...file, classification: 'SUPPORT', include: true };
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
                subtitle="Inspect what was ingested, validate the detected stack, and prepare the project for Triage"
                icon={<Activity className="text-cyan-500" />}
                helpText="Discovery is the intake checkpoint: review repository contents, confirm technology, add supporting context, and promote only the files that should enter Triage."
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
                        {isScanning ? "Scanning..." : "Run Discovery Audit"}
                    </button>
                </div>
            </StageHeader>

            <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">

                {activeSection === 'overview' && (
                    <div className="max-w-6xl mx-auto space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <p className="text-[11px] font-black uppercase tracking-widest text-cyan-400">Discovery Status</p>
                                <p className="mt-3 text-2xl font-black text-white">{isScanning ? 'Scanning' : scanProgress >= 100 ? 'Ready for Triage' : 'Pending Scan'}</p>
                                <p className="mt-2 text-sm text-gray-400">Progress: {scanProgress}%</p>
                            </div>
                            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <p className="text-[11px] font-black uppercase tracking-widest text-cyan-400">Files Classified</p>
                                <p className="mt-3 text-2xl font-black text-white">{fileInventory.length}</p>
                                <p className="mt-2 text-sm text-gray-400">Visible inventory before Triage promotion.</p>
                            </div>
                            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
                                <p className="text-[11px] font-black uppercase tracking-widest text-cyan-400">Assessment</p>
                                <p className="mt-3 text-2xl font-black text-white">{assessment.score || 0}%</p>
                                <p className="mt-2 text-sm text-gray-400">Gap detection and technical completeness.</p>
                            </div>
                        </div>

                        <div className="rounded-3xl border border-white/10 bg-black/20 p-8">
                            <h2 className="text-xl font-black text-white">Stage Home</h2>
                            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-gray-400">
                                Use Discovery to inspect the source repository, confirm the detected technology, record project context, and decide which files should move into Triage.
                            </p>
                            <div className="mt-6 flex flex-wrap gap-3">
                                <button
                                    onClick={() => onSectionChange?.('run-scan')}
                                    disabled={isScanning}
                                    className="px-5 py-2.5 bg-cyan-600 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-cyan-500 disabled:opacity-50"
                                >
                                    {isScanning ? 'Scanning...' : 'Run Discovery Audit'}
                                </button>
                                <button
                                    onClick={() => onSectionChange?.('assessment')}
                                    className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                >
                                    View Assessment
                                </button>
                                <button
                                    onClick={() => onSectionChange?.('files')}
                                    className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                >
                                    Review Files
                                </button>
                                <button
                                    onClick={() => onSectionChange?.('upload')}
                                    className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                >
                                    Add Supporting Context
                                </button>
                                <button
                                    onClick={() => onSectionChange?.('intake')}
                                    className="px-5 py-2.5 bg-white/5 border border-white/10 text-white rounded-xl text-xs font-black uppercase tracking-wider hover:bg-white/10"
                                >
                                    Project Intake Notes
                                </button>
                            </div>
                        </div>
                    </div>
                )}

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

                        {/* Sprint 1: Readiness + Confidence Model */}
                        <ReadinessBadge
                            projectId={projectId}
                            variant="card"
                            refreshKey={readinessKey}
                        />

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

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
                                    <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                                        <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Detected Stack</p>
                                        <p className="mt-2 text-sm font-bold text-white">{assessment.detectedTech || 'Unknown'}</p>
                                    </div>
                                    <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                                        <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Files Ready</p>
                                        <p className="mt-2 text-sm font-bold text-white">{fileInventory.filter(file => file.include !== false).length} selected</p>
                                    </div>
                                    <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                                        <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Next Step</p>
                                        <p className="mt-2 text-sm font-bold text-white">Review gaps, then promote the right files to Triage</p>
                                    </div>
                                </div>

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
                                            You selected <span className="text-white bg-black/30 px-2 py-0.5 rounded">{sourceTech}</span>. The forensic scan suggests <span className="text-white bg-black/30 px-2 py-0.5 rounded">{assessment.detectedTech}</span> as an alternative. You can keep your manual selection or update the project configuration.
                                        </p>
                                    </div>
                                    {!isSupportedSourceTech(assessment.detectedTech || "") && (
                                        <div className="flex items-start gap-4 p-5 bg-red-500/10 rounded-2xl border border-red-500/20">
                                            <AlertCircle className="text-red-400 shrink-0" size={20} />
                                            <p className="text-xs text-red-200/90 font-bold leading-relaxed">
                                                The suggested origin <span className="text-white bg-black/30 px-2 py-0.5 rounded">{assessment.detectedTech}</span> is not supported by the configured source cartridges. Your current selection can still be used.
                                            </p>
                                        </div>
                                    )}
                                    <div className="flex gap-4">
                                        {isSupportedSourceTech(assessment.detectedTech || "") && (
                                            <button
                                                onClick={handleUpdateTech}
                                                className="px-6 py-3 bg-cyan-600 text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-cyan-500 transition-all shadow-lg active:scale-95"
                                            >
                                                Update Configuration
                                            </button>
                                        )}
                                        <button
                                            onClick={() => setShowConflict(false)}
                                            className="px-6 py-3 bg-white/5 border border-white/10 text-gray-400 text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white/10 hover:text-white transition-all"
                                        >
                                            Keep My Selection
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
                {activeSection === 'intake' && (
                    <div className="max-w-5xl mx-auto space-y-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Database size={24} className="text-cyan-500" />
                                Project Intake
                            </h2>
                            <div className="text-xs font-black uppercase tracking-widest text-cyan-400 bg-cyan-500/10 px-4 py-2 rounded-full border border-cyan-500/20">
                                Baseline Context
                            </div>
                        </div>

                        <div className="p-8 rounded-3xl border bg-white/5 border-white/5 space-y-6">
                            <p className="text-sm text-gray-400 leading-relaxed max-w-4xl">
                                Capture the business and operational context that should travel with Discovery into Triage. This intake is stored with the project and reused by the manifest and readiness model.
                            </p>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <label className="space-y-2">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Business Domain</span>
                                    <input
                                        value={projectIntake.business_domain}
                                        onChange={(e) => setProjectIntake(prev => ({ ...prev, business_domain: e.target.value }))}
                                        placeholder="Insurance, retail, finance, healthcare..."
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-cyan-500/40"
                                    />
                                </label>
                                <label className="space-y-2">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Migration Goals</span>
                                    <input
                                        value={projectIntake.migration_goals}
                                        onChange={(e) => setProjectIntake(prev => ({ ...prev, migration_goals: e.target.value }))}
                                        placeholder="Lift-and-shift, refactor, modernization, decommission..."
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-cyan-500/40"
                                    />
                                </label>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <label className="space-y-2">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Critical Processes</span>
                                    <textarea
                                        value={projectIntake.critical_processes}
                                        onChange={(e) => setProjectIntake(prev => ({ ...prev, critical_processes: e.target.value }))}
                                        placeholder="Orders, billing, claims, ETL windows, daily feeds..."
                                        rows={4}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-cyan-500/40 resize-none"
                                    />
                                </label>
                                <label className="space-y-2">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Operational Constraints</span>
                                    <textarea
                                        value={projectIntake.operational_constraints}
                                        onChange={(e) => setProjectIntake(prev => ({ ...prev, operational_constraints: e.target.value }))}
                                        placeholder="Batch windows, dependencies, outages, release freeze, SLAs..."
                                        rows={4}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-cyan-500/40 resize-none"
                                    />
                                </label>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <label className="space-y-2">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Data Sensitivity</span>
                                    <textarea
                                        value={projectIntake.data_sensitivity}
                                        onChange={(e) => setProjectIntake(prev => ({ ...prev, data_sensitivity: e.target.value }))}
                                        placeholder="PII, PCI, PHI, regulated data, retention rules..."
                                        rows={4}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-cyan-500/40 resize-none"
                                    />
                                </label>
                                <label className="space-y-2">
                                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Notes</span>
                                    <textarea
                                        value={projectIntake.notes}
                                        onChange={(e) => setProjectIntake(prev => ({ ...prev, notes: e.target.value }))}
                                        placeholder="Any extra context useful for triage or assessment..."
                                        rows={4}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white outline-none focus:border-cyan-500/40 resize-none"
                                    />
                                </label>
                            </div>

                            <div className="flex items-center justify-between gap-4 pt-2">
                                <div className="text-xs text-gray-500">
                                    Saved intake updates the manifest context and refreshes readiness automatically.
                                </div>
                                <button
                                    onClick={handleSaveIntake}
                                    disabled={savingIntake}
                                    className="px-6 py-3 bg-cyan-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-cyan-500 disabled:opacity-50 transition-all shadow-lg shadow-cyan-600/20"
                                >
                                    {savingIntake ? 'Saving...' : 'Save Intake'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* TRIBAL KNOWLEDGE */}
                {activeSection === 'upload' && (
                    <div className="max-w-4xl mx-auto space-y-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Upload size={24} className="text-purple-500" />
                                Supporting Context Upload
                            </h2>
                        </div>

                        <div className="p-8 rounded-3xl border bg-white/5 border-white/5">
                            <p className="text-sm text-gray-400 mb-8 leading-relaxed">
                                Upload business rules, data dictionaries, mapping documents, or other supporting material that helps Discovery and Triage understand the legacy system context.
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
                                    Classify files before Triage so the promoted set stays focused: <strong className="text-cyan-400">CORE</strong> for migration work, <strong className="text-purple-400">SUPPORT</strong> for read-only context, <strong className="text-gray-500">IGNORED</strong> to skip.
                                </p>
                            </div>
                            {fileInventory.length > 0 && (
                                <div className="text-sm border border-white/10 bg-black/40 px-5 py-2.5 rounded-xl flex gap-4">
                                    <div><span className="text-gray-400">Total:</span> <span className="font-bold">{fileInventory.length}</span></div>
                                    <div><span className="text-gray-400">Selected:</span> <span className="font-bold text-cyan-500">{fileInventory.filter(f => f.include).length}</span></div>
                                </div>
                            )}
                        </div>

                            {evidenceItems.length > 0 && (
                                <div className="rounded-2xl border border-white/5 bg-black/40 p-5 space-y-4">
                                    <div className="flex items-center justify-between gap-4">
                                        <div>
                                            <h3 className="text-sm font-black uppercase tracking-widest text-white">Evidence Review</h3>
                                                <p className="text-xs text-gray-500 mt-1">Review the strongest detected signals and mark which ones should influence Triage.</p>
                                        </div>
                                        <div className="text-[10px] font-black uppercase tracking-widest text-cyan-400 bg-cyan-500/10 px-3 py-1.5 rounded-full border border-cyan-500/20">
                                            {evidenceItems.filter(item => item.review_status === 'pinned').length} Pinned
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 max-h-[320px] overflow-auto custom-scrollbar pr-1">
                                        {evidenceItems.slice(0, 9).map((item) => (
                                            <div key={item.review_key} className={`rounded-xl border p-4 bg-white/5 ${item.review_status === 'pinned' ? 'border-cyan-500/30' : item.review_status === 'dismissed' ? 'border-white/5 opacity-50' : 'border-white/10'}`}>
                                                <div className="flex items-start justify-between gap-3 mb-3">
                                                    <div className="min-w-0">
                                                        <p className="text-[10px] font-black uppercase tracking-widest text-cyan-400">{item.parser_name || 'Evidence'}</p>
                                                        <p className="text-xs text-gray-300 truncate mt-1" title={item.source_path}>{item.source_path}</p>
                                                    </div>
                                                    <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-full border border-white/10 text-gray-400">
                                                        {item.review_status}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-gray-400 leading-relaxed line-clamp-4 whitespace-pre-wrap">{item.snippet || 'No snippet available.'}</p>
                                                <div className="mt-4 flex flex-wrap gap-2">
                                                    <button
                                                        onClick={() => handleEvidenceReview(item.review_key, 'pinned')}
                                                        disabled={savingEvidenceKey === item.review_key}
                                                        className="px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-cyan-600/20 text-cyan-300 border border-cyan-500/20 disabled:opacity-50"
                                                    >
                                                        Pin
                                                    </button>
                                                    <button
                                                        onClick={() => handleEvidenceReview(item.review_key, 'reviewed')}
                                                        disabled={savingEvidenceKey === item.review_key}
                                                        className="px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-emerald-600/20 text-emerald-300 border border-emerald-500/20 disabled:opacity-50"
                                                    >
                                                        Reviewed
                                                    </button>
                                                    <button
                                                        onClick={() => handleEvidenceReview(item.review_key, 'dismissed')}
                                                        disabled={savingEvidenceKey === item.review_key}
                                                        className="px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-white/5 text-gray-400 border border-white/10 disabled:opacity-50"
                                                    >
                                                        Dismiss
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

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
                                                        <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${file.category === 'migratable' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/20' :
                                                            file.category === 'support' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/20' :
                                                                file.category === 'documentation' ? 'bg-gray-500/20 text-gray-400 border border-gray-500/20' :
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
                                                        {file.has_override && (
                                                            <div className="mt-2 text-[10px] font-black uppercase tracking-widest text-cyan-400">
                                                                Manual Override
                                                            </div>
                                                        )}
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
                                <p className="text-sm font-bold text-gray-400 max-w-md">No file inventory available yet. Run the Discovery Audit first to analyze the repository contents.</p>
                                <button
                                    onClick={() => onSectionChange?.('run-scan')}
                                    className="mt-6 px-6 py-2 bg-white/5 rounded-xl text-xs font-bold hover:bg-white/10 transition-colors uppercase tracking-widest text-white"
                                >
                                    Go to Discovery Audit
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
