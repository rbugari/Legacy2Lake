"use client";

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Trash2, ShieldAlert, Clock, Zap } from 'lucide-react';

const CustomNode = ({ data }: any) => {
    const isCore = data.category === 'CORE';
    const isSupport = data.category === 'SUPPORT';
    const isVirtual = data.id?.startsWith('virtual_');
    const isPII = data.is_pii;

    const onDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (data.onDelete) data.onDelete(data.id || '');
    };

    return (
        <div className={`px-4 py-3 rounded-lg shadow-xl border-2 min-w-[190px] transition-all group bg-white dark:bg-gray-800 ${isVirtual ? 'border-dashed border-primary/50' :
            isCore ? 'border-primary dark:border-secondary' :
                isSupport ? 'border-purple-400 dark:border-purple-500' :
                    'border-gray-300 dark:border-gray-600'
            } ${isPII ? 'ring-2 ring-red-100 dark:ring-red-900/10' : ''}`}>
            <Handle type="target" position={Position.Top} className="w-3 h-3 bg-gray-400 border-none" />

            <div className="flex flex-col gap-1">
                <div className="flex justify-between items-center mb-1">
                    <div className="flex gap-1 items-center">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full uppercase ${isVirtual ? 'bg-indigo-100 text-indigo-700' :
                            isCore ? 'bg-primary/10 text-primary dark:text-secondary' :
                                isSupport ? 'bg-purple-100 text-purple-700' :
                                    'bg-gray-100 text-gray-600'
                            }`}>
                            {isVirtual ? 'VIRTUAL' : (data.category || 'N/A')}
                        </span>
                        {isPII && (
                            <span className="flex items-center gap-0.5 text-[8px] font-bold text-red-600 bg-red-50 px-1 py-0.5 rounded border border-red-100">
                                <ShieldAlert size={8} /> PII
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-1">
                        <span className="text-[10px] text-gray-400 font-mono">
                            {data.complexity || ''}
                        </span>
                        {!data.isReadOnly && (
                            <button
                                onClick={onDelete}
                                className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-all opacity-0 group-hover:opacity-100"
                                title="Eliminar de la malla"
                            >
                                <Trash2 size={10} />
                            </button>
                        )}
                    </div>
                </div>

                <div className="text-sm font-bold text-gray-900 dark:text-white truncate">
                    {data.label || 'Unnamed Node'}
                </div>

                {data.type && (
                    <div className="text-[10px] text-gray-500 italic truncate">
                        {data.type}
                    </div>
                )}

                {(data.load_strategy || data.frequency) && isCore && (
                    <div className="mt-2 pt-2 border-t border-gray-50 dark:border-gray-800 flex items-center justify-between text-[8px] text-gray-400 font-mono">
                        <span className="flex items-center gap-0.5">
                            <Zap size={8} className={data.load_strategy === 'INCREMENTAL' ? 'text-blue-500' : ''} /> {data.load_strategy?.replace('FULL_OVERWRITE', 'FULL') || 'FULL'}
                        </span>
                        <span className="flex items-center gap-0.5">
                            <Clock size={8} /> {data.frequency || 'DAILY'}
                        </span>
                    </div>
                )}
            </div>

            <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-gray-400 border-none" />
        </div>
    );
};

export default CustomNode;
