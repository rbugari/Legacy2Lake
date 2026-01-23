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
        switch (type) {
            case 'package': return <Package size={16} className="text-blue-500" />;
            case 'script': return <FileCode size={16} className="text-yellow-500" />;
            case 'config': return <Database size={16} className="text-purple-500" />;
            case 'documentation': return <FileText size={16} className="text-gray-500" />;
            case 'obsolete': return <Trash2 size={16} className="text-red-500" />;
            default: return <AlertCircle size={16} className="text-gray-400" />;
        }
    };

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800">
            {/* Tabs Header */}
            <div className="flex border-b border-gray-100 dark:border-gray-800">
                <button
                    onClick={() => setActiveTab('packages')}
                    className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider ${activeTab === 'packages' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    Paquetes
                </button>
                <button
                    onClick={() => setActiveTab('support')}
                    className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider ${activeTab === 'support' ? 'text-purple-600 border-b-2 border-purple-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    Apoyo
                </button>
                <button
                    onClick={() => setActiveTab('trash')}
                    className={`px-4 py-3 text-xs font-bold uppercase tracking-wider ${activeTab === 'trash' ? 'text-red-600 border-b-2 border-red-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    <Trash2 size={14} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto">
                {isLoading ? (
                    <div className="p-8 text-center text-gray-400 text-sm">
                        <span className="animate-pulse">Escaneando repositorio...</span>
                    </div>
                ) : (
                    <table className="w-full text-sm text-left">
                        <tbody>
                            {activeTab === 'packages' && filteredAssets.length === 0 && (
                                <tr><td className="p-4 text-center text-gray-400 text-xs">No se encontraron paquetes .dtsx</td></tr>
                            )}

                            {filteredAssets.map((asset) => (
                                <tr
                                    key={asset.id}
                                    draggable
                                    onDragStart={(e) => onDragStart(e, asset)}
                                    className="border-b border-gray-50 dark:border-gray-800/50 hover:bg-blue-50 dark:hover:bg-blue-900/20 cursor-grab active:cursor-grabbing group transition-colors"
                                >
                                    <td className="px-4 py-3 font-medium flex items-center gap-3">
                                        <GripVertical size={14} className="text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        {getIcon(asset.type)}
                                        <div className="flex flex-col">
                                            <span className="truncate max-w-[180px]" title={asset.name}>{asset.name}</span>
                                            <span className="text-[10px] text-gray-400 font-normal truncate max-w-[180px]">{asset.path}</span>
                                        </div>
                                    </td>
                                    <td className="px-2 py-3 text-right">
                                        {asset.status === 'connected' && <div className="w-2 h-2 rounded-full bg-green-500 ml-auto" title="Conectado"></div>}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
            <div className="p-2 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-950">
                <p className="text-[10px] text-center text-gray-400">
                    Arrastra <GripVertical size={10} className="inline" /> para orquestar
                </p>
            </div>
        </div>
    );
}
