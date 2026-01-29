"use client";

import React from "react";
import { ArrowRight, RefreshCw, CheckCircle, Info, Maximize2, Minimize2, RotateCcw } from "lucide-react";

interface StageHeaderProps {
    title: string;
    subtitle: string;
    icon: React.ReactNode;
    helpText?: string;
    isReadOnly?: boolean;
    onApprove?: () => void;
    onRestart?: () => void;
    approveLabel?: string;
    isApproveDisabled?: boolean;
    isExecuting?: boolean;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void; // [NEW] Inspection Mode exit
    children?: React.ReactNode;
}

const StageHeader: React.FC<StageHeaderProps> = ({
    title,
    subtitle,
    icon,
    helpText,
    isReadOnly,
    onApprove,
    onRestart,
    approveLabel = "Approve and Continue",
    isApproveDisabled,
    isExecuting,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent,
    children
}) => {
    return (
        <div className="flex items-center justify-between px-6 py-4 bg-[var(--surface)] border-b border-[var(--border)] shadow-sm shrink-0 transition-all">
            <div className="flex items-center gap-4">
                <div className="p-2.5 bg-cyan-500/10 rounded-2xl text-cyan-500 shadow-sm border border-cyan-500/20">
                    {icon}
                </div>
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h2 className="text-lg font-bold tracking-tight text-[var(--text-primary)] leading-none">{title}</h2>
                        {helpText && (
                            <div className="group relative">
                                <Info size={14} className="text-gray-400 hover:text-cyan-500 cursor-help transition-colors" />
                                <div className="absolute left-0 top-full mt-2 w-64 p-3 bg-gray-900 text-white text-[10px] font-bold uppercase tracking-widest rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-[100] border border-white/10 backdrop-blur-xl">
                                    <p className="leading-relaxed">{helpText}</p>
                                </div>
                            </div>
                        )}
                    </div>
                    <p className="text-xs text-gray-500 font-medium">{subtitle}</p>
                </div>
            </div>

            <div className="flex items-center gap-4">
                {/* Stage Navigation / Inspection Mode */}
                {onBackToCurrent && (
                    <button
                        onClick={onBackToCurrent}
                        className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 text-amber-500 border border-amber-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-amber-500 hover:text-white transition-all shadow-sm active:scale-95"
                    >
                        <ArrowRight size={12} className="rotate-180" /> Back to Current Stage
                    </button>
                )}

                {/* View Controls */}
                <div className="flex items-center gap-1 bg-gray-50 dark:bg-gray-900/50 p-1 rounded-xl border border-gray-200 dark:border-white/5">
                    {onToggleFullscreen && (
                        <button
                            onClick={onToggleFullscreen}
                            className="p-1.5 text-gray-400 hover:text-cyan-500 hover:bg-white dark:hover:bg-gray-800 rounded-lg transition-all"
                            title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
                        >
                            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                        </button>
                    )}
                    {onReset && (
                        <button
                            onClick={onReset}
                            className="p-1.5 text-gray-400 hover:text-orange-500 hover:bg-white dark:hover:bg-gray-800 rounded-lg transition-all"
                            title="Reset Step"
                        >
                            <RotateCcw size={16} />
                        </button>
                    )}
                </div>

                <div className="h-6 w-px bg-gray-200 dark:bg-gray-800" />

                <div className="flex items-center gap-3">
                    {/* Stage Specific Actions (e.g. Execute) */}
                    {!isReadOnly && children && (
                        <div className="flex items-center gap-2 mr-2">
                            {children}
                            <div className="h-6 w-px bg-gray-200 dark:bg-gray-800 mx-2" />
                        </div>
                    )}

                    {isReadOnly ? (
                        <button
                            onClick={onRestart}
                            className="flex items-center gap-2 px-5 py-2.5 border border-cyan-200 dark:border-cyan-900/50 bg-cyan-50 dark:bg-cyan-900/20 text-cyan-700 dark:text-cyan-400 rounded-xl text-xs font-bold hover:bg-cyan-100 dark:hover:bg-cyan-900/30 transition-all shadow-sm"
                        >
                            <RefreshCw size={14} /> Edit and Restart
                        </button>
                    ) : (
                        onApprove && (
                            <button
                                onClick={onApprove}
                                disabled={isApproveDisabled || isExecuting}
                                className={`
                                flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm
                                ${isApproveDisabled || isExecuting
                                        ? "bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-600 cursor-not-allowed shadow-none"
                                        : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20 dark:shadow-none"
                                    }
                            `}
                            >
                                <CheckCircle size={14} /> {approveLabel} <ArrowRight size={14} />
                            </button>
                        )
                    )}
                </div>
            </div>
        </div>
    );
};

export default StageHeader;
