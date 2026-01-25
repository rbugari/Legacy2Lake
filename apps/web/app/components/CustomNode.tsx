"use client";

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Trash2, ShieldAlert, Clock, Zap } from 'lucide-react';

const CustomNode = ({ data }: any) => {
    const isCore = data.category === 'CORE';
    const isSupport = data.category === 'SUPPORT';
    const isIgnored = data.category === 'IGNORE' || data.category === 'IGNORED';
    const isVirtual = data.id?.startsWith('virtual_');

    // Architect v2.0 Metadata Support
    const metadata = data.metadata || {};
    const isPII = metadata.is_pii ?? data.is_pii;
    const criticality = metadata.criticality ?? (data.criticality || 'P3');
    const volume = metadata.volume ?? (data.volume || 'LOW');
    const latency = metadata.latency ?? (data.frequency || 'BATCH');
    const lineageGroup = metadata.lineage_group;

    const heatmapMode = data.heatmapMode || 'none';

    const onDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (data.onDelete) data.onDelete(data.id || '');
    };

    // Heatmap Visual Overrides
    let borderClass = '';
    let glowClass = '';
    let bgPulse = '';

    if (heatmapMode === 'pii' && isPII) {
        borderClass = 'border-red-500 border-2';
        glowClass = 'shadow-[0_0_20px_rgba(239,68,68,0.4)]';
        bgPulse = 'animate-pulse bg-red-500/5';
    } else if (heatmapMode === 'criticality') {
        if (criticality === 'P1') borderClass = 'border-red-500 border-2';
        else if (criticality === 'P2') borderClass = 'border-amber-500 border-2';
        else borderClass = 'border-emerald-500/30';
    } else if (heatmapMode === 'volume' && volume === 'HIGH') {
        glowClass = 'shadow-[0_0_30px_rgba(6,182,212,0.5)]';
        borderClass = 'border-cyan-500 border-2';
    }

    const config = isCore
        ? { color: 'from-emerald-500 to-green-600', icon: '🎯', border: borderClass || 'border-emerald-500/50', glow: glowClass || 'shadow-emerald-500/20' }
        : isSupport
            ? { color: 'from-cyan-500 to-blue-600', icon: '🔧', border: borderClass || 'border-cyan-500/50', glow: glowClass || 'shadow-cyan-500/20' }
            : isIgnored
                ? { color: 'from-gray-500 to-gray-600', icon: '⏸️', border: borderClass || 'border-gray-500/50', glow: glowClass || 'shadow-gray-500/10' }
                : { color: 'from-slate-500 to-slate-600', icon: '📄', border: borderClass || 'border-slate-500/50', glow: glowClass || 'shadow-slate-500/10' };

    return (
        <div className={`group relative transition-all duration-300 hover:scale-[1.02]`}>
            {/* Outer Glow */}
            <div className={`absolute -inset-0.5 bg-gradient-to-r ${config.color} rounded-xl blur opacity-0 group-hover:opacity-40 transition duration-300 ${config.glow}`} />

            <div className={`relative px-4 py-3 rounded-xl shadow-2xl border ${config.border} min-w-[200px] bg-white dark:bg-[#121212]/90 backdrop-blur-md overflow-hidden ${bgPulse}`}>
                <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-white dark:!border-[#121212]" />

                <div className="flex flex-col gap-2">
                    <div className="flex justify-between items-center">
                        <div className="flex gap-1.5 items-center">
                            <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase text-white bg-gradient-to-r ${config.color}`}>
                                {isVirtual ? 'VIRTUAL' : (data.category || 'ASSET')}
                            </span>
                            {isPII && (
                                <span className="flex items-center gap-0.5 text-[8px] font-bold text-red-500 bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/30">
                                    <ShieldAlert size={8} /> PII
                                </span>
                            )}
                            {lineageGroup && (
                                <span className="text-[8px] font-bold text-cyan-500 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/30">
                                    {lineageGroup}
                                </span>
                            )}
                        </div>
                        <div className="flex items-center gap-1.5">
                            {!data.isReadOnly && (
                                <button
                                    onClick={onDelete}
                                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                    title="Eliminar"
                                >
                                    <Trash2 size={12} />
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="flex items-start gap-2">
                        <span className="text-lg mt-0.5">{config.icon}</span>
                        <div className="flex flex-col min-w-0">
                            <div className="text-sm font-bold text-[var(--text-primary)] truncate">
                                {data.label || 'Unnamed Node'}
                            </div>
                            <div className="text-[10px] text-[var(--text-tertiary)] font-medium truncate">
                                {data.type || 'Object'}
                            </div>
                        </div>
                    </div>

                    {/* Metadata summary for CORE nodes */}
                    {isCore && (
                        <div className="mt-2 pt-2 border-t border-gray-100 dark:border-white/5 flex flex-col gap-1.5">
                            <div className="flex justify-between items-center text-[8px] font-black uppercase tracking-widest text-gray-500">
                                <span>Latency</span>
                                <span className="text-cyan-500">{latency}</span>
                            </div>
                            <div className="flex justify-between items-center text-[8px] font-black uppercase tracking-widest text-gray-500">
                                <span>Volume</span>
                                <span className="text-emerald-500">{volume}</span>
                            </div>
                        </div>
                    )}
                </div>

                <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-emerald-500 !border-2 !border-white dark:!border-[#121212]" />
            </div>
        </div>
    );
};

export default CustomNode;
