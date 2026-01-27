import React from 'react';
import { Maximize2, Minimize2, RotateCcw } from 'lucide-react';

interface StageControlsProps {
    isMaximized: boolean;
    onToggleMaximize: () => void;
    onReload: () => void;
}

export default function StageControls({ isMaximized, onToggleMaximize, onReload }: StageControlsProps) {
    return (
        <div className="flex items-center gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-1 shadow-sm">
            <button
                onClick={onToggleMaximize}
                className="p-1.5 text-gray-500 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                title={isMaximized ? "Collapse View" : "Expand View"}
            >
                {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            <div className="w-px h-4 bg-gray-200 dark:bg-gray-700" />
            <button
                onClick={onReload}
                className="p-1.5 text-gray-500 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition-colors"
                title="Reload Stage Data"
            >
                <RotateCcw size={16} />
            </button>
        </div>
    );
}
