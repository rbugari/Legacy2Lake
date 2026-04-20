"use client";

import React from 'react';
import { Library } from 'lucide-react';

interface ReportsAccessPanelProps {
    currentStage: number;
    onOpenCatalog: () => void;
}

export default function ReportsAccessPanel({ currentStage, onOpenCatalog }: ReportsAccessPanelProps) {
    return (
        <div className="bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-950/30 dark:to-blue-950/30 border-b border-cyan-200/50 dark:border-cyan-800/50 px-6 py-3">
            <div className="flex items-center justify-between max-w-7xl mx-auto">
                <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                        <Library className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                            Reports Library Available
                        </h3>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                            Access governance reports, handover documentation, and certification artifacts
                        </p>
                    </div>
                </div>
                <button
                    onClick={onOpenCatalog}
                    className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white text-sm font-medium rounded-lg transition-colors shadow-sm hover:shadow-md"
                >
                    Open Reports Library
                </button>
            </div>
        </div>
    );
}
