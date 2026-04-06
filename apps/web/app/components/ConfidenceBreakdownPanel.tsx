"use client";

import React from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

export interface ConfidenceAdjustment {
    label: string;
    delta: number;
    reason: string;
}

export interface ConfidenceBreakdown {
    baseline_score: number;
    adjustments: ConfidenceAdjustment[];
    final_score: number;
}

interface Props {
    breakdown: ConfidenceBreakdown;
    className?: string;
}

function getDeltaStyles(delta: number) {
    if (delta > 0) {
        return {
            icon: <ArrowUpRight size={12} className="text-emerald-400" />,
            text: "text-emerald-300",
            chip: "bg-emerald-500/10 border-emerald-500/20",
        };
    }

    if (delta < 0) {
        return {
            icon: <ArrowDownRight size={12} className="text-red-400" />,
            text: "text-red-300",
            chip: "bg-red-500/10 border-red-500/20",
        };
    }

    return {
        icon: <Minus size={12} className="text-white/40" />,
        text: "text-white/60",
        chip: "bg-white/5 border-white/10",
    };
}

export default function ConfidenceBreakdownPanel({ breakdown, className = "" }: Props) {
    const totalDelta = breakdown.final_score - breakdown.baseline_score;

    return (
        <div className={`rounded-2xl border border-white/10 bg-black/20 p-3 space-y-3 ${className}`}>
            <div className="flex items-center justify-between gap-3">
                <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.24em] text-white/40">
                        Confidence breakdown
                    </p>
                    <p className="text-xs text-white/60 mt-1">
                        Baseline {breakdown.baseline_score}% with signal-based adjustments.
                    </p>
                </div>
                <div className="text-right">
                    <p className="text-lg font-black text-white">{breakdown.final_score}%</p>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40">
                        {totalDelta >= 0 ? "+" : ""}{totalDelta} net
                    </p>
                </div>
            </div>

            <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] text-white/50">
                    <span>Baseline</span>
                    <span className="font-mono">{breakdown.baseline_score}%</span>
                </div>

                {breakdown.adjustments.length > 0 ? (
                    breakdown.adjustments.map((adjustment, index) => {
                        const styles = getDeltaStyles(adjustment.delta);
                        return (
                            <div
                                key={`${adjustment.label}-${index}`}
                                className={`rounded-xl border px-3 py-2 ${styles.chip}`}
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-start gap-2 min-w-0">
                                        <span className="mt-0.5 flex-shrink-0">{styles.icon}</span>
                                        <div className="min-w-0">
                                            <p className="text-[11px] font-semibold text-white/90">
                                                {adjustment.label}
                                            </p>
                                            <p className="text-[11px] text-white/55 leading-relaxed">
                                                {adjustment.reason}
                                            </p>
                                        </div>
                                    </div>
                                    <span className={`text-[11px] font-mono font-semibold ${styles.text}`}>
                                        {adjustment.delta >= 0 ? "+" : ""}{adjustment.delta}
                                    </span>
                                </div>
                            </div>
                        );
                    })
                ) : (
                    <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-[11px] text-white/50">
                        No signal adjustments were applied.
                    </div>
                )}
            </div>

            <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px] uppercase tracking-[0.24em] text-white/40">
                <span>Final score</span>
                <span className="font-mono text-white/70">{breakdown.final_score}%</span>
            </div>
        </div>
    );
}
