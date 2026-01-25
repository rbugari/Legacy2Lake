"use client";

import React from "react";
import { ArrowRight, RefreshCw, CheckCircle, Info } from "lucide-react";

interface StageHeaderProps {
    title: string;
    subtitle: string;
    icon: React.ReactNode;
    helpText?: string; // [NEW] Contextual Help
    isReadOnly?: boolean;
    onApprove?: () => void;
    onRestart?: () => void;
    approveLabel?: string;
    isApproveDisabled?: boolean;
    isExecuting?: boolean;
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
    children
}) => {
    return (
        <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 shadow-sm shrink-0 transition-all">
            <div className="flex items-center gap-4">
                <div className="p-2.5 bg-cyan-500/10 rounded-2xl text-cyan-500 shadow-sm border border-cyan-500/20">
                    {icon}
                </div>
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h2 className="text-lg font-bold tracking-tight text-gray-900 dark:text-white leading-none">{title}</h2>
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
                        <RefreshCw size={14} /> Editar y Reiniciar
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
    );
};

export default StageHeader;
