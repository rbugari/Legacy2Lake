"use client";
import { useState } from "react";
import Link from "next/link";
import { Github, FolderPlus, Settings, Trash2, RefreshCw, AlertCircle, FileText, Package, Archive, Database, FolderArchive } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import BackupsModal from "./BackupsModal";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface ProjectCardProps {
    project: {
        id: string;
        name: string;
        progress: number;
        stage: number | string;
        origin: string;
        assets_count?: number;
        alerts?: number;
        updated_at?: string;
        source_tech?: string;
        target_tech?: string;
        lines_generated?: number;
        complexity_high?: number;
        complexity_medium?: number;
        complexity_low?: number;
    };
    onDelete: (e: React.MouseEvent, id: string) => void;
    onReset: (e: React.MouseEvent, id: string) => void;
}

export default function ProjectCard({ project, onDelete, onReset }: ProjectCardProps) {
    const [showBackupsModal, setShowBackupsModal] = useState(false);
    
    const stageMap: { [key: string]: { label: string; color: string; emoji: string } } = {
        "1": { label: "DISCOVERY", color: "from-slate-500 to-slate-600", emoji: "🔭" },
        "2": { label: "TRIAGE", color: "from-cyan-500 to-teal-500", emoji: "🔍" },
        "3": { label: "DRAFTING", color: "from-blue-500 to-indigo-500", emoji: "📐" },
        "4": { label: "REFINEMENT", color: "from-emerald-500 to-green-500", emoji: "⚡" },
        "5": { label: "GOVERNANCE", color: "from-teal-500 to-emerald-600", emoji: "🛡️" },
        "6": { label: "HANDOVER", color: "from-blue-600 to-cyan-600", emoji: "🚀" }
    };
    const currentStage = stageMap[project.stage.toString()] || { label: "INITIATED", color: "from-slate-500 to-slate-600", emoji: "🏁" };

    const getOriginConfig = (origin: string) => {
        switch (origin.toLowerCase()) {
            case "github":
                return { label: "GitHub Repository", icon: <Github size={14} className="text-cyan-500" /> };
            case "zip":
            case "local_zip":
                return { label: "Local Archive", icon: <Archive size={14} className="text-emerald-500" /> };
            case "manual":
            case "upload":
                return { label: "Manual Upload", icon: <Package size={14} className="text-blue-500" /> };
            default:
                return { label: "Legacy Source", icon: <Database size={14} className="text-gray-500" /> };
        }
    };

    const originConfig = getOriginConfig(project.origin);

    return (
        <div className="group relative">
            {/* Glow effect on hover */}
            <div className={cn(
                "absolute -inset-0.5 bg-gradient-to-r rounded-2xl blur opacity-0 group-hover:opacity-75 transition duration-700",
                currentStage.color
            )} />

            {/* Main Card */}
            <div className="relative bg-[var(--surface)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 flex flex-col h-full hover:border-[var(--accent)]/50 transition-all duration-300 shadow-lg dark:shadow-[0_0_30px_rgba(0,0,0,0.4)] hover:shadow-2xl">

                {/* Header Row */}
                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-2 text-[var(--text-tertiary)] text-[10px] font-bold tracking-widest uppercase">
                        <Database size={14} className="text-cyan-500" />
                        {project.name}
                    </div>

                    <div className={cn(
                        "px-3 py-1 rounded-full text-[10px] font-black tracking-wider uppercase text-white shadow-lg flex items-center gap-1.5 bg-gradient-to-r",
                        currentStage.color
                    )}>
                        <span>{currentStage.emoji}</span>
                        {currentStage.label}
                    </div>
                </div>

                {/* Project Title */}
                <Link href={`/workspace?id=${project.id}`} className="block group/title">
                    <h3 className="text-xl font-bold mb-1 text-[var(--text-primary)] group-hover/title:text-cyan-500 transition-colors line-clamp-1">
                        {project.name}
                    </h3>
                    <p className="text-xs text-[var(--text-tertiary)] mb-4 font-mono">
                        {project.source_tech && project.target_tech ? (
                            <>
                                <span className="text-cyan-500 font-bold">{project.source_tech}</span>
                                <span className="mx-2 opacity-40">→</span>
                                <span className="text-blue-500 font-bold">{project.target_tech}</span>
                            </>
                        ) : (
                            <span className="opacity-40 italic">Tech stack not defined yet</span>
                        )}
                    </p>
                </Link>

                {/* Progress Bar */}
                <div className="mb-6">
                    <div className="flex justify-between items-end mb-2 px-0.5">
                        <span className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-tight">Progress</span>
                        <span className="text-sm font-black text-cyan-500">{project.progress}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-[var(--background-secondary)] rounded-full overflow-hidden shadow-inner">
                        <div
                            className={cn(
                                "h-full rounded-full transition-all duration-1000 ease-out relative bg-gradient-to-r shadow-lg",
                                currentStage.color
                            )}
                            style={{ width: `${project.progress}%` }}
                        >
                            {/* Shimmer effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"
                                style={{ backgroundSize: '200% 100%' }} />
                        </div>
                    </div>
                </div>

                {/* Dashboard Metrics */}
                <div className="grid grid-cols-2 gap-3 mb-6 mt-auto">
                    {/* Assets Count */}
                    <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-3">
                        <div className="flex items-center gap-2 mb-1">
                            <FileText size={12} className="text-cyan-400" />
                            <span className="text-[9px] font-black text-cyan-400 uppercase tracking-wider">Assets</span>
                        </div>
                        <div className="text-2xl font-black text-white">{project.assets_count || 0}</div>
                    </div>

                    {/* Lines Generated */}
                    <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-3">
                        <div className="flex items-center gap-2 mb-1">
                            <Package size={12} className="text-purple-400" />
                            <span className="text-[9px] font-black text-purple-400 uppercase tracking-wider">Lines</span>
                        </div>
                        <div className="text-2xl font-black text-white">{project.lines_generated ? `${(project.lines_generated / 1000).toFixed(1)}k` : '0'}</div>
                    </div>

                    {/* Complexity Breakdown (if available) */}
                    {(project.complexity_high || project.complexity_medium || project.complexity_low) && (
                        <div className="col-span-2 bg-white/5 border border-white/10 rounded-xl p-3">
                            <div className="text-[9px] font-black text-gray-400 uppercase tracking-wider mb-2">Complexity</div>
                            <div className="flex gap-2">
                                {(project.complexity_high ?? 0) > 0 && (
                                    <div className="flex items-center gap-1 text-xs">
                                        <div className="w-2 h-2 rounded-full bg-red-500"></div>
                                        <span className="font-bold text-red-400">{project.complexity_high}</span>
                                    </div>
                                )}
                                {(project.complexity_medium ?? 0) > 0 && (
                                    <div className="flex items-center gap-1 text-xs">
                                        <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                                        <span className="font-bold text-amber-400">{project.complexity_medium}</span>
                                    </div>
                                )}
                                {(project.complexity_low ?? 0) > 0 && (
                                    <div className="flex items-center gap-1 text-xs">
                                        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                                        <span className="font-bold text-emerald-400">{project.complexity_low}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Health Status */}
                    {project.alerts && project.alerts > 0 ? (
                        <div className="col-span-2 bg-orange-500/10 border border-orange-500/20 rounded-xl p-3 flex items-center gap-2">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                            </span>
                            <span className="text-xs font-bold text-orange-400">{project.alerts} Alerts</span>
                        </div>
                    ) : (
                        <div className="col-span-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 flex items-center gap-2">
                            <AlertCircle size={14} className="text-emerald-400" />
                            <span className="text-xs font-bold text-emerald-400">Healthy</span>
                        </div>
                    )}
                </div>

                {/* Footer / Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
                    <Link
                        href={`/workspace?id=${project.id}`}
                        className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-cyan-600/30 active:scale-95 relative overflow-hidden group/btn"
                    >
                        <span className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-700"></span>
                        <span className="relative">Open Project</span>
                    </Link>

                    <div className="flex items-center gap-1">
                        <button
                            onClick={(e) => onReset(e, project.id)}
                            className="p-2 text-[var(--text-tertiary)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-lg transition-all"
                            title="Reset Project"
                        >
                            <RefreshCw size={18} />
                        </button>
                        <button
                            onClick={(e) => { e.preventDefault(); setShowBackupsModal(true); }}
                            className="p-2 text-[var(--text-tertiary)] hover:text-amber-500 hover:bg-amber-500/10 rounded-lg transition-all"
                            title="Manage Backups"
                        >
                            <FolderArchive size={18} />
                        </button>
                        <Link
                            href={`/workspace/settings?id=${project.id}`}
                            className="p-2 text-[var(--text-tertiary)] hover:text-white hover:bg-white/5 rounded-lg transition-all"
                            title="Settings"
                        >
                            <Settings size={18} />
                        </Link>
                        <button
                            onClick={(e) => onDelete(e, project.id)}
                            className="p-2 text-[var(--text-tertiary)] hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                            title="Delete"
                        >
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Backups Modal */}
            <BackupsModal
                isOpen={showBackupsModal}
                onClose={() => setShowBackupsModal(false)}
                projectId={project.id}
                projectName={project.name}
            />

            <style jsx>{`
                @keyframes shimmer {
                    0% { background-position: -200% 0; }
                    100% { background-position: 200% 0; }
                }
                .animate-shimmer {
                    animation: shimmer 3s infinite linear;
                }
            `}</style>
        </div>
    );
}
