"use client";

import React from 'react';
import { Loader2 } from 'lucide-react';
import { SidebarItem as SidebarItemType } from '@/app/config/sidebar-sections';
import { SidebarMetrics, formatBadgeValue } from '@/app/hooks/useSidebarMetrics';

const RUNNING_STATUSES = ['PROCESSING', 'ORCHESTRATING', 'REFINING', 'GENERATING', 'GOVERNANCE', 'DOCUMENTING', 'CERTIFYING'];

interface SidebarItemProps {
    item: SidebarItemType;
    isActive: boolean;
    onClick: () => void;
    metrics: SidebarMetrics;
    level?: number;
}

export default function SidebarItem({
    item,
    isActive,
    onClick,
    metrics,
    level = 0
}: SidebarItemProps) {
    const Icon = item.icon;
    const badgeValue = item.badge ? formatBadgeValue(metrics, item.badge) : null;
    const isRunning = item.status && metrics.executionStatus &&
        RUNNING_STATUSES.includes(metrics.executionStatus);

    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-all ${isActive
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-l-4 border-blue-500 font-medium'
                    : item.variant === 'action'
                        ? 'text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 border-l-4 border-amber-500/50'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 border-l-4 border-transparent'
                }`}
            style={{ paddingLeft: `${0.75 + level * 0.5}rem` }}
        >
            {isRunning ? (
                <Loader2 size={14} className="shrink-0 animate-spin text-blue-500" />
            ) : (
                <Icon size={14} className={`shrink-0 ${item.variant === 'action' && !isActive ? 'text-amber-500' : ''}`} />
            )}
            <span className="flex-1 text-left truncate">{item.label}</span>
            {item.variant === 'action' && !isActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500/50" title="Actionable Item" />
            )}
            {badgeValue !== null && (
                <span className={`px-2 py-0.5 text-xs font-mono rounded-full shrink-0 ${isActive
                        ? 'bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                    }`}>
                    {badgeValue}
                </span>
            )}
        </button>
    );
}
