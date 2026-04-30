"use client";

import React, { useMemo } from 'react';
import { Home, Search, Code, RefreshCw, Package, ShieldCheck } from 'lucide-react';
import { SidebarMetrics } from '@/app/hooks/useSidebarMetrics';

const RUNNING_STATUSES = ['PROCESSING', 'ORCHESTRATING', 'REFINING', 'GENERATING', 'GOVERNANCE', 'DOCUMENTING', 'CERTIFYING'];

interface SidebarHeaderProps {
    stage: number;
    metrics: SidebarMetrics;
}

const STAGE_INFO = {
    0: { name: 'Discovery', icon: Home, color: 'text-gray-600 dark:text-gray-400' },
    1: { name: 'Triage', icon: Search, color: 'text-blue-600 dark:text-blue-400' },
    2: { name: 'Drafting', icon: Code, color: 'text-green-600 dark:text-green-400' },
    3: { name: 'Refinement', icon: RefreshCw, color: 'text-orange-600 dark:text-orange-400' },
    4: { name: 'Governance', icon: ShieldCheck, color: 'text-purple-600 dark:text-purple-400' },
    5: { name: 'Handover', icon: Package, color: 'text-emerald-600 dark:text-emerald-400' }
};

export default function SidebarHeader({ stage, metrics }: SidebarHeaderProps) {
    const stageInfo = STAGE_INFO[stage as keyof typeof STAGE_INFO] || STAGE_INFO[0];
    const StageIcon = stageInfo.icon;

    // Determine if stage has been executed (has data)
    const hasData = useMemo(() => {
        let result = false;
        if (stage === 0) result = (metrics.fileCount || 0) > 0;
        if (stage === 1) result = (metrics.assetCount || 0) > 0 || metrics.quickAssessment !== undefined;
        if (stage === 2) result = (metrics.filesGenerated || 0) > 0;
        if (stage === 3) result = metrics.issueCount !== undefined || metrics.qualityDelta !== undefined;
        if (stage === 4) result = !!(metrics.docsGenerated || metrics.bundleReady);
        if (stage === 5) result = !!(metrics.bundleReady || metrics.docsGenerated);

        return result;
    }, [stage, metrics]);

    const emptyStateMessage = useMemo(() => {
        if (stage === 4) return 'No governance artifacts yet - Run governance first';
        if (stage === 5) return 'No handover bundle yet - Finish governance or export a bundle';
        return 'No data yet - Run pipeline first';
    }, [stage]);

    const isRunning = metrics.executionStatus &&
        RUNNING_STATUSES.includes(metrics.executionStatus);

    return (
        <div className="p-4 border-b border-gray-200 dark:border-gray-800">
            {/* Stage Name */}
            <div className="flex items-center gap-2 mb-3">
                <StageIcon size={20} className={stageInfo.color} />
                <h2 className="font-bold text-lg text-gray-900 dark:text-gray-100">
                    {stageInfo.name}
                </h2>
            </div>

            {/* Execution Status Banner */}
            {!hasData && !isRunning && (
                <div className="mb-3 p-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-amber-700 dark:text-amber-400">
                            ⚠️ {emptyStateMessage}
                        </span>
                    </div>
                </div>
            )}

            {isRunning && (
                <div className="mb-3 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <div className="flex items-center gap-2">
                        <RefreshCw size={12} className="animate-spin text-blue-600 dark:text-blue-400" />
                        <span className="text-xs font-bold text-blue-700 dark:text-blue-400">
                            {metrics.executionStatus}...
                        </span>
                    </div>
                </div>
            )}

            {/* Quick Metrics for Triage */}
            {stage === 1 && metrics.quickAssessment && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600 dark:text-gray-400">Score</span>
                        <span className={`text-lg font-bold ${metrics.quickAssessment.score >= 80 ? 'text-green-600 dark:text-green-400' :
                            metrics.quickAssessment.score >= 50 ? 'text-yellow-600 dark:text-yellow-400' :
                                'text-red-600 dark:text-red-400'
                            }`}>
                            {metrics.quickAssessment.score}
                        </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400">Assets</span>
                        <span className="font-mono font-bold text-gray-900 dark:text-gray-100">
                            {metrics.assetCount || 0}
                        </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400">Tables</span>
                        <span className="font-mono font-bold text-gray-900 dark:text-gray-100">
                            {metrics.tableCount || 0}
                        </span>
                    </div>
                </div>
            )}

            {/* Progress for Drafting */}
            {stage === 2 && metrics.generationProgress !== undefined && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-600 dark:text-gray-400">Progress</span>
                        <span className="text-sm font-bold text-gray-900 dark:text-gray-100">
                            {metrics.generationProgress}%
                        </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${metrics.generationProgress}%` }}
                        />
                    </div>
                    {metrics.currentAgent && (
                        <div className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                            {metrics.currentAgent} working...
                        </div>
                    )}
                </div>
            )}

            {/* Quality Delta for Refinement */}
            {stage === 3 && metrics.qualityDelta !== undefined && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600 dark:text-gray-400">Quality</span>
                        <span className={`text-lg font-bold ${metrics.qualityDelta > 0 ? 'text-green-600 dark:text-green-400' : 'text-gray-600'
                            }`}>
                            {metrics.qualityDelta > 0 ? '+' : ''}{metrics.qualityDelta}%
                        </span>
                    </div>
                    {metrics.issueCount !== undefined && (
                        <div className="flex items-center justify-between text-xs mt-2">
                            <span className="text-gray-600 dark:text-gray-400">Issues</span>
                            <span className="font-mono font-bold text-red-600 dark:text-red-400">
                                {metrics.issueCount}
                            </span>
                        </div>
                    )}
                </div>
            )}

            {/* Completion for Governance */}
            {stage === 4 && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400">Documentation</span>
                        <span className={`font-bold ${metrics.docsGenerated ? 'text-green-600' : 'text-gray-400'}`}>
                            {metrics.docsGenerated ? '✓ Ready' : '⏳ Pending'}
                        </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400">COP Bundle</span>
                        <span className={`font-bold ${metrics.bundleReady ? 'text-green-600' : 'text-gray-400'}`}>
                            {metrics.bundleReady ? '✓ Ready' : '⏳ Pending'}
                        </span>
                    </div>
                </div>
            )}

            {stage === 5 && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400">Delivery Bundle</span>
                        <span className={`font-bold ${metrics.bundleReady ? 'text-green-600' : 'text-gray-400'}`}>
                            {metrics.bundleReady ? '✓ Export Ready' : '⏳ Pending'}
                        </span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 dark:text-gray-400">Governance Docs</span>
                        <span className={`font-bold ${metrics.docsGenerated ? 'text-green-600' : 'text-gray-400'}`}>
                            {metrics.docsGenerated ? '✓ Available' : '⏳ Pending'}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
