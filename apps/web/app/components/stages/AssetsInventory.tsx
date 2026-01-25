"use client";
import { Package, FileText, Trash2, GripVertical, AlertCircle, Database, FileCode } from 'lucide-react';
import { useState } from 'react';

type Asset = {
    id: string;
    name: string;
    type: 'package' | 'script' | 'config' | 'unused' | 'documentation';
    status: 'pending' | 'connected' | 'obsolete';
    tags: string[];
    path?: string;
};

export default function AssetsInventory({ assets, onDragStart, isLoading }: { assets: Asset[], onDragStart: (event: React.DragEvent, asset: Asset) => void, isLoading?: boolean }) {
    const [activeTab, setActiveTab] = useState<'packages' | 'support' | 'trash'>('packages');

    const filteredAssets = assets.filter(asset => {
        if (activeTab === 'packages') return asset.type === 'package';
        if (activeTab === 'support') return ['script', 'config', 'documentation'].includes(asset.type);
        if (activeTab === 'trash') return asset.type === 'unused' || asset.status === 'obsolete';
        return true;
    });

    const getIcon = (type: string) => {
        const iconBase = "w-8 h-8 rounded-lg flex items-center justify-center shadow-sm border";
        switch (type) {
            case 'package': return (
                <div className={`${iconBase} bg-cyan-500/10 border-cyan-500/20 text-cyan-500`}>
                    <Package size={16} />
                </div>
            );
            case 'script': return (
                <div className={`${iconBase} bg-emerald-500/10 border-emerald-500/20 text-emerald-500`}>
                    <FileCode size={16} />
                </div>
            );
            case 'config': return (
                <div className={`${iconBase} bg-blue-500/10 border-blue-500/20 text-blue-500`}>
                    <Database size={16} />
                </div>
            );
            case 'documentation': return (
                <div className={`${iconBase} bg-gray-500/10 border-gray-500/20 text-gray-400`}>
                    <FileText size={16} />
                </div>
            );
            case 'obsolete': return (
                <div className={`${iconBase} bg-red-500/10 border-red-500/20 text-red-500`}>
                    <Trash2 size={16} />
                </div>
            );
            default: return (
                <div className={`${iconBase} bg-slate-500/10 border-slate-500/20 text-slate-400`}>
                    <AlertCircle size={16} />
                </div>
            );
        }
    };

    return (
        <div className="flex flex-col h-full bg-white dark:bg-[#0a0a0a] border-r border-gray-100 dark:border-white/5 transition-colors">
            {/* Tabs Header */}
            <div className="flex border-b border-gray-50 dark:border-white/5 bg-gray-50/50 dark:bg-black/20">
                <button
                    onClick={() => setActiveTab('packages')}
                    className={`flex-1 py-4 text-[10px] font-bold uppercase tracking-[0.2em] transition-all ${activeTab === 'packages' ? 'text-cyan-500 border-b-2 border-cyan-500' : 'text-[var(--text-tertiary)] hover:text-cyan-400'}`}
                >
                    Paquetes
                </button>
                <button
                    onClick={() => setActiveTab('support')}
                    className={`flex-1 py-4 text-[10px] font-bold uppercase tracking-[0.2em] transition-all ${activeTab === 'support' ? 'text-emerald-500 border-b-2 border-emerald-500' : 'text-[var(--text-tertiary)] hover:text-emerald-400'}`}
                >
                    Apoyo
                </button>
                <button
                    onClick={() => setActiveTab('trash')}
                    className={`px-6 py-4 text-[10px] font-bold uppercase tracking-[0.2em] transition-all ${activeTab === 'trash' ? 'text-red-500 border-b-2 border-red-500' : 'text-[var(--text-tertiary)] hover:text-red-400'}`}
                >
                    <Trash2 size={14} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar">
                {isLoading ? (
                    <div className="p-12 text-center flex flex-col items-center gap-3">
                        <div className="w-8 h-8 border-2 border-cyan-500 border-b-transparent rounded-full animate-spin" />
                        <span className="text-[10px] uppercase font-bold tracking-widest text-cyan-500/50 animate-pulse">Escaneando repo...</span>
                    </div>
                ) : (
                    <table className="w-full text-sm text-left border-separate border-spacing-0">
                        <tbody>
                            {activeTab === 'packages' && filteredAssets.length === 0 && (
                                <tr><td className="p-8 text-center text-[var(--text-tertiary)] text-[10px] font-bold uppercase tracking-widest">No se encontraron paquetes .dtsx</td></tr>
                            )}

                            {filteredAssets.map((asset) => (
                                <tr
                                    key={asset.id}
                                    draggable
                                    onDragStart={(e) => onDragStart(e, asset)}
                                    className="group cursor-grab active:cursor-grabbing hover:bg-cyan-500/5 dark:hover:bg-cyan-500/5 transition-all"
                                >
                                    <td className="px-5 py-4 border-b border-gray-50 dark:border-white/5 flex items-center gap-3">
                                        <div className="opacity-0 group-hover:opacity-100 transition-opacity translate-x-[-8px] group-hover:translate-x-0">
                                            <GripVertical size={14} className="text-cyan-500/40" />
                                        </div>

                                        <div className="transition-transform group-hover:scale-110 duration-300">
                                            {getIcon(asset.type)}
                                        </div>

                                        <div className="flex flex-col min-w-0">
                                            <span className="text-sm font-bold text-[var(--text-primary)] truncate group-hover:text-cyan-500 transition-colors" title={asset.name}>
                                                {asset.name}
                                            </span>
                                            <span className="text-[10px] text-[var(--text-tertiary)] font-medium truncate opacity-60 group-hover:opacity-100 transition-opacity" title={asset.path}>
                                                {asset.path}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-5 py-4 border-b border-gray-50 dark:border-white/5 text-right bg-white/0">
                                        {asset.status === 'connected' && (
                                            <div className="flex items-center justify-end gap-1.5">
                                                <span className="text-[9px] font-bold text-emerald-500 uppercase tracking-tighter opacity-0 group-hover:opacity-100 transition-opacity">Mapped</span>
                                                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            <div className="p-4 border-t border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-black/40">
                <div className="flex items-center justify-center gap-2 text-[9px] font-bold uppercase tracking-[0.1em] text-[var(--text-tertiary)]">
                    <span className="text-cyan-500">Arrastra</span>
                    <GripVertical size={12} className="text-cyan-500/40" />
                    <span>para orquestar la resolución</span>
                </div>
            </div>
        </div>
    );
}
