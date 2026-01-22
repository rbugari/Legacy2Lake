"use client";

import React from "react";
import { ArrowRight, RefreshCw, CheckCircle, Lock } from "lucide-react";

interface StageHeaderProps {
    title: string;
    subtitle: string;
    icon: React.ReactNode;
    isReadOnly?: boolean;
    onApprove?: () => void;
    onRestart?: () => void;
    approveLabel?: string;
    isApproveDisabled?: boolean;
    isExecuting?: boolean;
    children?: React.ReactNode; // For stage-specific controls (e.g. Run Pipeline)
}

const StageHeader: React.FC<StageHeaderProps> = ({
    title,
    subtitle,
    icon,
    isReadOnly,
    onApprove,
    onRestart,
    approveLabel = "Aprobar y Continuar",
    isApproveDisabled,
    isExecuting,
    children
}) => {
    return (
        <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 shadow-sm shrink-0 transition-all">
            <div className="flex items-center gap-4">
                <div className="p-2.5 bg-primary/5 rounded-2xl text-primary">
                    {icon}
                </div>
                <div>
                    <h2 className="text-lg font-bold tracking-tight text-gray-900 dark:text-white leading-none mb-1">{title}</h2>
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
                        className="flex items-center gap-2 px-4 py-2 border border-orange-200 dark:border-orange-900/50 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400 rounded-xl text-xs font-bold hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-all"
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
                                    : "bg-green-600 hover:bg-green-700 text-white shadow-green-200 dark:shadow-none"
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
