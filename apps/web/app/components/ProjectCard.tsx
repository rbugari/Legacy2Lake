"use client";
import Link from "next/link";
import { Github, FolderPlus, Settings, Trash2, RefreshCw, AlertCircle, FileText } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

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
    };
    onDelete: (e: React.MouseEvent, id: string) => void;
    onReset: (e: React.MouseEvent, id: string) => void;
}

export default function ProjectCard({ project, onDelete, onReset }: ProjectCardProps) {
    const stageMap: { [key: string]: { label: string; color: string; emoji: string } } = {
        "1": { label: "TRIAGE", color: "from-cyan-500 to-teal-500", emoji: "🔍" },
        "2": { label: "DRAFTING", color: "from-blue-500 to-indigo-500", emoji: "📐" },
        "3": { label: "REFINEMENT", color: "from-emerald-500 to-green-500", emoji: "⚡" },
        "4": { label: "GOVERNANCE", color: "from-teal-500 to-emerald-600", emoji: "✅" }
    };

    const currentStage = stageMap[project.stage.toString()] || { label: "UNKNOWN", color: "from-gray-500 to-gray-600", emoji: "❓" };
    const displayOrigin = project.origin === "github" ? "GitHub" : project.origin === "zip" ? "Local ZIP" : project.origin;

    return (
        <div className="group relative">
            {/* Glow effect on hover */}
            <div className={cn(
                "absolute -inset-0.5 bg-gradient-to-r rounded-2xl blur opacity-0 group-hover:opacity-60 transition duration-500",
                currentStage.color
            )} />

            {/* Main Card */}
            <div className="relative bg-white dark:bg-[#121212]/80 backdrop-blur-md border border-gray-200 dark:border-white/10 rounded-2xl p-6 flex flex-col h-full hover:border-cyan-500/50 transition-all duration-300 shadow-sm dark:shadow-none">

                {/* Header Row */}
                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-2 text-[var(--text-tertiary)] text-[10px] font-bold tracking-widest uppercase">
                        {project.origin === "github" ? <Github size={14} className="text-cyan-500" /> : <FolderPlus size={14} className="text-emerald-500" />}
                        {displayOrigin}
                    </div>

                    <div className={cn(
                        "px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase text-white shadow-sm flex items-center gap-1 bg-gradient-to-r",
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
                    <p className="text-xs text-[var(--text-tertiary)] mb-4">
                        Project ID: <span className="font-mono">{project.id}</span>
                    </p>
                </Link>

                {/* Progress Bar */}
                <div className="mb-6">
                    <div className="flex justify-between items-end mb-1.5 px-0.5">
                        <span className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-tight">Progreso</span>
                        <span className="text-xs font-bold text-cyan-500">{project.progress}%</span>
                    </div>
                    <div className="h-2 w-full bg-gray-100 dark:bg-white/5 rounded-full overflow-hidden">
                        <div
                            className={cn(
                                "h-full rounded-full transition-all duration-1000 ease-out relative bg-gradient-to-r",
                                currentStage.color
                            )}
                            style={{ width: `${project.progress}%` }}
                        >
                            {/* Shimmer effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"
                                style={{ backgroundSize: '200% 100%' }} />
                        </div>
                    </div>
                </div>

                {/* Metrics Row */}
                <div className="flex items-center gap-4 mb-6 mt-auto">
                    <div className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-secondary)]">
                        <FileText size={14} className="text-cyan-400" />
                        <span>{project.assets_count || 0} assets</span>
                    </div>

                    {project.alerts && project.alerts > 0 ? (
                        <div className="flex items-center gap-1.5 text-xs font-medium text-orange-400">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                            </span>
                            <span>{project.alerts} alertas</span>
                        </div>
                    ) : (
                        <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-400">
                            <AlertCircle size={14} />
                            <span>Healthy</span>
                        </div>
                    )}
                </div>

                {/* Footer / Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-white/5">
                    <Link
                        href={`/workspace?id=${project.id}`}
                        className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-bold transition-all shadow-md shadow-cyan-600/20 active:scale-95"
                    >
                        Abrir Proyecto
                    </Link>

                    <div className="flex items-center gap-1">
                        {parseInt(project.stage.toString()) > 1 && (
                            <button
                                onClick={(e) => onReset(e, project.id)}
                                className="p-2 text-[var(--text-tertiary)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-lg transition-all"
                                title="Resetear a Triage"
                            >
                                <RefreshCw size={18} />
                            </button>
                        )}
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
                            title="Eliminar"
                        >
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>
            </div>

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
