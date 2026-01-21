"use client";
import React, { useEffect, useState } from 'react';
import {
    CheckCircle,
    ShieldCheck,
    FileText,
    Download,
    ArrowRight,
    Github,
    Server,
    Database,
    AlertCircle,
    TrendingUp,
    ScrollText,
    ExternalLink,
    Code,
    Settings, // Added for v1.5
    Maximize2,
    Minimize2,
    RotateCcw,
    ArrowLeft
} from 'lucide-react';
import { API_BASE_URL } from '../../lib/config';
import DesignRegistryPanel from './DesignRegistryPanel'; // Added for v1.5

interface GovernanceViewProps {
    projectId: string;
}

export default function GovernanceView({ projectId }: GovernanceViewProps) {
    const [report, setReport] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"report" | "registry">("report");
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        fetch(`${API_BASE_URL}/projects/${projectId}/governance`)
            .then(res => res.json())
            .then(data => {
                setReport(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch governance report:", err);
                setLoading(false);
            });
    }, [projectId]);

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50/50 dark:bg-gray-950 text-gray-500">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="font-bold animate-pulse">Generating Certification Report...</p>
                </div>
            </div>
        );
    }

    const auditScore = report?.score ?? 0;
    const stats = report?.stats ?? {
        bronze_count: 0,
        silver_count: 0,
        gold_count: 0,
        total_files: 0,
        total_lines: 0
    };



    return (
        <div className={`h-full bg-gray-50/50 dark:bg-gray-950 overflow-y-auto custom-scrollbar transition-all duration-300 ${isFullscreen ? 'fixed inset-0 z-50 bg-white dark:bg-gray-950' : ''}`}>
            {/* Standard Operational Bar */}
            <div className="sticky top-0 z-20 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between shadow-sm">

                {/* Left: Functional Tabs */}
                <div className="flex gap-1 bg-gray-100/50 dark:bg-gray-900/50 p-1 rounded-xl border border-gray-200/50 dark:border-gray-800">
                    <button
                        onClick={() => setActiveTab("report")}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === "report" ? "bg-white dark:bg-gray-800 shadow-sm text-blue-600 border border-gray-200 dark:border-gray-700" : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"}`}
                    >
                        <ShieldCheck size={14} className="mb-0.5" /> Certification
                    </button>
                    <button
                        onClick={() => setActiveTab("registry")}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${activeTab === "registry" ? "bg-white dark:bg-gray-800 shadow-sm text-blue-600 border border-gray-200 dark:border-gray-700" : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"}`}
                    >
                        <Settings size={14} className="mb-0.5" /> Design Standards
                    </button>
                </div>

                {/* Right: Operational Controls */}
                <div className="flex items-center gap-3">
                    {/* View Controls */}
                    <div className="flex items-center gap-1 bg-gray-50 dark:bg-gray-900 p-1 rounded-lg border border-gray-100 dark:border-gray-800">
                        <button
                            onClick={() => setIsFullscreen(!isFullscreen)}
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-white dark:hover:bg-gray-800 rounded-md transition-all"
                            title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
                        >
                            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                        </button>
                        <button
                            onClick={() => window.location.reload()}
                            className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-white dark:hover:bg-gray-800 rounded-md transition-all"
                            title="Reset Process"
                        >
                            <RotateCcw size={16} />
                        </button>
                    </div>

                    <div className="h-6 w-px bg-gray-200 dark:bg-gray-800" />

                    {/* Navigation */}
                    <button
                        // In a real app, this would use router.back() or similar. 
                        // For now, we simulate "Step Back" visually.
                        onClick={() => window.history.back()}
                        className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm text-xs font-bold text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
                    >
                        <ArrowLeft size={14} /> Back to Refinement
                    </button>
                </div>
            </div>

            <div className="p-8 max-w-5xl mx-auto space-y-8">
                {activeTab === "registry" ? (
                    <DesignRegistryPanel projectId={projectId} />
                ) : (
                    <>
                        {/* Hero Success Section */}
                        <div className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-blue-600 to-indigo-700 rounded-3xl p-10 text-white shadow-2xl">
                            <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-8">
                                <div className="space-y-4">
                                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-[10px] font-bold uppercase tracking-widest">
                                        <ShieldCheck size={12} /> Compliance Passed
                                    </div>
                                    <h1 className="text-4xl font-extrabold tracking-tight">Migration Certified.</h1>
                                    <p className="text-blue-100 max-w-md text-lg leading-relaxed">
                                        Your legacy SSIS logic has been successfully architecturalized into modern, idempotent Delta Lake logic.
                                    </p>
                                    <div className="flex items-center gap-4 pt-4">
                                        <a
                                            href={`${API_BASE_URL}/projects/${projectId}/export`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-6 py-3 bg-white text-blue-700 rounded-xl font-bold shadow-lg hover:bg-blue-50 transition-all flex items-center gap-2"
                                        >
                                            <Download size={18} /> Download Final Bundle
                                        </a>
                                        <button className="px-6 py-3 bg-blue-500/30 border border-white/20 backdrop-blur-md rounded-xl font-bold hover:bg-white/10 transition-all flex items-center gap-2">
                                            <Github size={18} /> Push to Repository
                                        </button>
                                    </div>
                                </div>

                                {/* Large Score Circle */}
                                <div className="relative w-48 h-48 flex items-center justify-center">
                                    <svg className="w-full h-full transform -rotate-90">
                                        <circle
                                            cx="96"
                                            cy="96"
                                            r="88"
                                            stroke="currentColor"
                                            strokeWidth="12"
                                            fill="transparent"
                                            className="text-white/10"
                                        />
                                        <circle
                                            cx="96"
                                            cy="96"
                                            r="88"
                                            stroke="currentColor"
                                            strokeWidth="12"
                                            fill="transparent"
                                            strokeDasharray={552}
                                            strokeDashoffset={552 - (552 * auditScore) / 100}
                                            className="text-white transition-all duration-1000 ease-out"
                                        />
                                    </svg>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <span className="text-5xl font-black">{auditScore}</span>
                                        <span className="text-[10px] font-bold uppercase opacity-60">Architect Score</span>
                                    </div>
                                </div>
                            </div>

                            {/* Background Decorative Elements */}
                            <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-white/10 rounded-full blur-3xl opacity-50" />
                            <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-64 h-64 bg-black/10 rounded-full blur-3xl opacity-50" />
                        </div>

                        {/* Grid Layout for details */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                            {/* Column 1 & 2: Main Details */}
                            <div className="lg:col-span-2 space-y-8">

                                {/* Summary Metrics */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <StatCard label="Total Refined" value={stats.total_files} icon={<ScrollText className="text-blue-500" />} />
                                    <StatCard label="Pyspark Lines" value={stats.total_lines} icon={<Code className="text-purple-500" />} />
                                    <StatCard label="Medallion Layers" value="3/3" icon={<Database className="text-green-500" />} />
                                    <StatCard label="Idempotency" value="100%" icon={<ShieldCheck className="text-indigo-500" />} />
                                </div>

                                {/* Recent Governance Logs */}
                                <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm">
                                    <h3 className="text-lg font-bold mb-6 flex items-center gap-2">
                                        <CheckCircle className="text-green-500" /> Compliance Audit Trail
                                    </h3>
                                    <div className="space-y-4">
                                        {report?.compliance_logs?.length > 0 ? (
                                            report.compliance_logs.map((log: any, idx: number) => (
                                                <LogItem
                                                    key={idx}
                                                    status={log.status}
                                                    message={log.message}
                                                    time={log.time}
                                                />
                                            ))
                                        ) : (
                                            <div className="text-center py-4 text-gray-400 text-sm italic">
                                                No certification logs found.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Column 3: Sidebar Details */}
                            <div className="space-y-8">
                                {/* Output Artifacts */}
                                <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm h-full">
                                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                        <FileText size={20} className="text-gray-400" /> Deliverables
                                    </h3>
                                    <div className="space-y-3">
                                        <ArtifactLink label="Bronze Layer Scripts" size={`${stats.bronze_count} files`} />
                                        <ArtifactLink label="Silver Layer Scripts" size={`${stats.silver_count} files`} />
                                        <ArtifactLink label="Gold Layer Scripts" size={`${stats.gold_count} files`} />
                                        <ArtifactLink label="IaC & DevOp Manifests" size="2 files" />
                                    </div>

                                    <hr className="my-6 border-gray-100 dark:border-gray-800" />

                                    <div className="p-4 bg-blue-50 dark:bg-blue-900/10 rounded-2xl">
                                        <div className="flex items-center gap-3 mb-2">
                                            <Database className="text-blue-500" size={18} />
                                            <span className="text-sm font-bold text-blue-900 dark:text-blue-200">Catalog Target</span>
                                        </div>
                                        <p className="text-[11px] text-blue-700 dark:text-blue-400 font-mono">
                                            shiftt_silver_db.orders_migrated
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Visual Lineage Section */}
                        <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-sm">
                            <h3 className="text-xl font-bold mb-8 flex items-center gap-2">
                                <TrendingUp size={20} className="text-indigo-500" /> Medallion Lineage Mapping
                            </h3>
                            <div className="space-y-12 max-h-[600px] overflow-y-auto pr-4 custom-scrollbar">
                                {report?.lineage?.map((item: any, idx: number) => (
                                    <LineageRow key={idx} item={item} />
                                ))}
                            </div>
                        </div>

                        {/* Final Footer CTA */}
                        <div className="flex flex-col items-center justify-center py-10 text-center space-y-4 border-t border-gray-100 dark:border-gray-800">
                            <div className="w-16 h-1 w-16 bg-gray-200 dark:bg-gray-800 rounded-full mb-4" />
                            <h3 className="text-xl font-bold">Ready to take the next step?</h3>
                            <p className="text-gray-500 max-w-md text-sm">
                                You can deploy these artifacts directly to your Databricks Workspace or export them for external CI/CD pipelines.
                            </p>
                            <div className="flex gap-4 pt-2">
                                <button className="text-sm font-bold text-primary hover:underline">Support Hub</button>
                                <span className="text-gray-300">|</span>
                                <button className="text-sm font-bold text-primary hover:underline">Open in Databricks</button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

function StatCard({ label, value, icon }: any) {
    return (
        <div className="bg-white dark:bg-gray-900 p-5 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col items-center text-center">
            <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded-2xl mb-3">
                {icon}
            </div>
            <span className="text-xl font-black text-gray-900 dark:text-white leading-none mb-1">{value}</span>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">{label}</span>
        </div>
    );
}

function LogItem({ status, message, time }: any) {
    return (
        <div className="flex items-start gap-4 p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-2xl transition-all cursor-default group">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full mt-1 ${status === 'PASSED' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                }`}>
                {status}
            </span>
            <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-snug">{message}</p>
                <span className="text-[10px] text-gray-400">{time}</span>
            </div>
        </div>
    );
}

function ArtifactLink({ label, size }: any) {
    return (
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-2xl group cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-all border border-transparent hover:border-blue-200 dark:hover:border-blue-900">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white dark:bg-gray-950 flex items-center justify-center shadow-sm">
                    <Download size={14} className="text-gray-400 group-hover:text-blue-500 transition-colors" />
                </div>
                <div className="flex flex-col">
                    <span className="text-xs font-bold text-gray-700 dark:text-gray-200">{label}</span>
                    <span className="text-[9px] text-gray-400 uppercase">{size}</span>
                </div>
            </div>
            <ArrowRight size={14} className="text-gray-300 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
        </div>
    );
}
function LineageRow({ item }: any) {
    return (
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-gray-50 dark:bg-gray-800/30 border border-gray-100 dark:border-gray-800">
            <LineageNode label="Source File" name={item.source} icon={<FileText size={14} />} color="gray" />
            <LineageConnector />
            <LineageNode label="Bronze Delta" name={item.targets.bronze} icon={<Database size={14} />} color="blue" />
            <LineageConnector />
            <LineageNode label="Silver Clean" name={item.targets.silver} icon={<ShieldCheck size={14} />} color="indigo" />
            <LineageConnector />
            <LineageNode label="Gold Semantic" name={item.targets.gold} icon={<TrendingUp size={14} />} color="green" />
        </div>
    );
}

function LineageNode({ label, name, icon, color }: any) {
    const colors: any = {
        gray: "bg-gray-500",
        blue: "bg-blue-500",
        indigo: "bg-indigo-500",
        green: "bg-green-500"
    };

    return (
        <div className="flex flex-col items-center gap-2 min-w-[140px]">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">{label}</span>
            <div className={`p-3 rounded-2xl ${colors[color]} text-white shadow-lg flex items-center gap-2 w-full justify-center`}>
                {icon}
                <span className="text-[11px] font-bold truncate max-w-[120px]">{name.split('.').pop()}</span>
            </div>
            <span className="text-[9px] text-gray-500 font-mono truncate max-w-[140px] opacity-60">{name}</span>
        </div>
    );
}

function LineageConnector() {
    return (
        <div className="hidden md:flex flex-1 items-center justify-center">
            <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-700 to-transparent relative">
                <ArrowRight size={12} className="absolute right-0 -top-[5px] text-gray-300 dark:text-gray-700" />
            </div>
        </div>
    );
}
