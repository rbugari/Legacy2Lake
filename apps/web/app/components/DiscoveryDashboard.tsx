"use client";
import React from 'react';
import { BarChart3, Database, AlertCircle, Cpu, Shield } from 'lucide-react';

interface DiscoveryDashboardProps {
    assets: any[];
    nodes: any[];
}

export default function DiscoveryDashboard({ assets, nodes }: DiscoveryDashboardProps) {
    const total = assets.length;
    const coreCount = assets.filter(a => a.type === 'CORE' || a.category === 'CORE').length;
    const highComplexity = assets.filter(a => a.complexity === 'HIGH').length;

    // Architect v2.0 PII detection
    const piiCount = assets.filter(a => (a.metadata?.is_pii || a.is_pii)).length;

    // Tech Stack 
    const ssissCount = assets.filter(a => a.name?.toLowerCase().endsWith('.dtsx')).length;
    const sqlCount = assets.filter(a => a.name?.toLowerCase().endsWith('.sql')).length;

    return (
        <div className="space-y-6 p-6 bg-[var(--surface)] backdrop-blur-md rounded-2xl border border-[var(--border)] shadow-sm">
            <h3 className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-[0.2em] flex items-center gap-2">
                <BarChart3 size={14} className="text-cyan-500" /> Discovery Metrics
            </h3>

            <div className="grid grid-cols-2 gap-4">
                <MetricCard
                    label="Total Assets"
                    value={total}
                    icon={<Database size={16} className="text-cyan-500" />}
                    color="cyan"
                />
                <MetricCard
                    label="Core Logic"
                    value={coreCount}
                    icon={<Cpu size={16} className="text-emerald-500" />}
                    color="emerald"
                />
            </div>

            <div className="space-y-3 pt-2">
                <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-tight">
                    <span className="text-[var(--text-tertiary)] flex items-center gap-1.5">
                        <AlertCircle size={12} className="text-orange-500" /> High Complexity
                    </span>
                    <span className="text-orange-500">{highComplexity}</span>
                </div>
                <div className="w-full bg-[var(--background-secondary)] h-2 rounded-full overflow-hidden">
                    <div
                        className="bg-gradient-to-r from-orange-400 to-orange-600 h-full transition-all duration-1000 relative"
                        style={{ width: `${total > 0 ? (highComplexity / total) * 100 : 0}%` }}
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" style={{ backgroundSize: '200% 100%' }} />
                    </div>
                </div>
            </div>

            <div className="pt-4 border-t border-[var(--border)] space-y-2">
                <StackItem label="Source Packages" count={ssissCount} color="bg-cyan-500" />
                <StackItem label="SQL Scripts" count={sqlCount} color="bg-orange-500" />
                <div className="pt-2">
                    <StackItem label="PII Exposure" count={piiCount} color={piiCount > 0 ? "bg-red-500" : "bg-emerald-500"} />
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

function MetricCard({ label, value, icon, color }: any) {
    const colorClasses = color === 'cyan' ? 'border-cyan-500/20' : 'border-emerald-500/20';
    return (
        <div className={`bg-[var(--background-secondary)] p-4 rounded-xl border ${colorClasses} transition-all hover:scale-[1.02]`}>
            <div className="flex items-center justify-between mb-2">
                {icon}
                <span className="text-2xl font-black text-[var(--text-primary)] leading-none">{value}</span>
            </div>
            <p className="text-[9px] text-[var(--text-tertiary)] font-bold uppercase tracking-wider">{label}</p>
        </div>
    );
}

function StackItem({ label, count, color }: any) {
    return (
        <div className="flex justify-between items-center text-[10px]">
            <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${color}`} />
                <span className="text-gray-600 dark:text-gray-400">{label}</span>
            </div>
            <span className="font-mono text-gray-400">{count}</span>
        </div>
    );
}
