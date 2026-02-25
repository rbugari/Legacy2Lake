"use client";

import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { SidebarSection as SidebarSectionType, SidebarItem as SidebarItemTypeImport } from '@/app/config/sidebar-sections';
import { SidebarMetrics, formatBadgeValue } from '@/app/hooks/useSidebarMetrics';
import SidebarItem from './SidebarItem';

interface SidebarSectionProps {
    section: SidebarSectionType;
    activeSection: string;
    onSectionChange: (sectionId: string) => void;
    metrics: SidebarMetrics;
    level?: number;
}

/**
 * Determine status indicator color based on section and metrics
 * Green = has data, Yellow = no data yet, None = not applicable
 */
function getSectionStatus(section: SidebarSectionType, metrics: SidebarMetrics): 'green' | 'yellow' | null {
    // Execution sections (Drafting, Refinement, Triage)
    if (section.id === 'execution') {
        // Check if any files have been generated (Drafting)
        if (metrics.filesGenerated && metrics.filesGenerated > 0) return 'green';
        // Check if execution is in progress
        if (metrics.executionStatus && ['PROCESSING', 'ORCHESTRATING', 'GENERATING'].includes(metrics.executionStatus)) return 'yellow';
        return 'yellow';
    }
    
    // Output sections (Generated Output)
    if (section.id === 'output') {
        if (metrics.filesGenerated && metrics.filesGenerated > 0) return 'green';
        return 'yellow';
    }
    
    // Analysis sections (Triage)
    if (section.id === 'analysis') {
        if (metrics.assetCount && metrics.assetCount > 0) return 'green';
        return 'yellow';
    }
    
    // Views sections (Triage)
    if (section.id === 'views') {
        if (metrics.nodeCount && metrics.nodeCount > 0) return 'green';
        if (metrics.assetCount && metrics.assetCount > 0) return 'green';
        return 'yellow';
    }
    
    // Review sections (Refinement)
    if (section.id === 'review') {
        if (metrics.refinementStatus && metrics.refinementStatus !== 'NOT_STARTED') return 'green';
        return 'yellow';
    }
    
    // Quick info
    if (section.id === 'quick-info') {
        if (metrics.quickAssessment) return 'green';
        return 'yellow';
    }
    
    // Configuration sections are neutral (no status indicator)
    if (section.id === 'config' || section.id === 'target' || section.id === 'actions' || section.id === 'completion') {
        return null;
    }
    
    // Default: no indicator
    return null;
}

export default function SidebarSection({
    section,
    activeSection,
    onSectionChange,
    metrics,
    level = 0
}: SidebarSectionProps) {
    const [isExpanded, setIsExpanded] = useState(true);
    const Icon = section.icon;
    
    // Check if this section or any child is active
    const isActive = activeSection === section.id;
    const hasActiveChild = section.children?.some((child: SidebarItemTypeImport) => child.id === activeSection);
    
    // Get status indicator
    const statusColor = getSectionStatus(section, metrics);

    // Auto-expand if has active child
    useEffect(() => {
        if (hasActiveChild) {
            setIsExpanded(true);
        }
    }, [hasActiveChild]);

    // If section has no children and no component, just render as item
    if (!section.children && !section.component) {
        return (
            <SidebarItem
                item={{
                    id: section.id,
                    label: section.label,
                    icon: section.icon,
                    badge: section.badge,
                    status: section.status
                }}
                isActive={isActive}
                onClick={() => onSectionChange(section.id)}
                metrics={metrics}
                level={level}
            />
        );
    }

    const badgeValue = section.badge ? formatBadgeValue(metrics, section.badge) : null;

    return (
        <div className="mb-1">
            {/* Section Header */}
            {section.collapsible ? (
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        isActive || hasActiveChild
                            ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                >
                    {/* Status Indicator */}
                    {statusColor && (
                        <div 
                            className={`w-2 h-2 rounded-full shrink-0 ${
                                statusColor === 'green' 
                                    ? 'bg-green-500 ring-2 ring-green-500/20' 
                                    : 'bg-yellow-500 ring-2 ring-yellow-500/20 animate-pulse'
                            }`}
                            title={statusColor === 'green' ? 'Has data' : 'No data yet'}
                        />
                    )}
                    {isExpanded ? (
                        <ChevronDown size={14} className="shrink-0" />
                    ) : (
                        <ChevronRight size={14} className="shrink-0" />
                    )}
                    <Icon size={16} className="shrink-0" />
                    <span className="flex-1 text-left truncate">{section.label}</span>
                    {badgeValue !== null && (
                        <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-mono rounded-full shrink-0">
                            {badgeValue}
                        </span>
                    )}
                </button>
            ) : (
                <div className="flex items-center gap-2 px-3 py-2 text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    {/* Status Indicator */}
                    {statusColor && (
                        <div 
                            className={`w-2 h-2 rounded-full shrink-0 ${
                                statusColor === 'green' 
                                    ? 'bg-green-500 ring-2 ring-green-500/20' 
                                    : 'bg-yellow-500 ring-2 ring-yellow-500/20 animate-pulse'
                            }`}
                            title={statusColor === 'green' ? 'Has data' : 'No data yet'}
                        />
                    )}
                    <Icon size={14} className="shrink-0" />
                    <span className="flex-1 truncate">{section.label}</span>
                    {badgeValue !== null && (
                        <span className="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs font-mono rounded-full shrink-0">
                            {badgeValue}
                        </span>
                    )}
                </div>
            )}

            {/* Children */}
            {section.children && isExpanded && (
                <div className="mt-1 ml-4 space-y-1">
                    {section.children.map((child: SidebarItemTypeImport) => (
                        <SidebarItem
                            key={child.id}
                            item={child}
                            isActive={activeSection === child.id}
                            onClick={() => onSectionChange(child.id)}
                            metrics={metrics}
                            level={level + 1}
                        />
                    ))}
                </div>
            )}

            {/* Component placeholder (rendered in main content area) */}
            {section.component && isActive && (
                <div className="text-xs text-gray-400 px-3 py-1">
                    → {section.component}
                </div>
            )}
        </div>
    );
}
