"use client";

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { getSectionsForStage, SidebarSection as SidebarSectionType } from '@/app/config/sidebar-sections';
import { useSidebarMetrics } from '@/app/hooks/useSidebarMetrics';
import SidebarHeader from './SidebarHeader';
import SidebarSection from './SidebarSection';

interface StageSidebarProps {
    stage: number; // 0=Discovery, 1=Triage, 2=Drafting, 3=Refinement, 4=Governance
    projectId: string;
    activeSection: string;
    onSectionChange: (sectionId: string) => void;
    className?: string;
}

export default function StageSidebar({
    stage,
    projectId,
    activeSection,
    onSectionChange,
    className = ''
}: StageSidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const sections = getSectionsForStage(stage);
    
    // DEBUG: Log what stage we're receiving
    console.log('[StageSidebar] Rendering with stage:', stage, 'projectId:', projectId);
    
    // Fetch metrics with auto-refresh
    const { metrics, isLoading, error } = useSidebarMetrics(projectId, stage, true);
    
    // Validate activeSection exists in current stage, auto-correct if not
    useEffect(() => {
        const allSectionIds: string[] = [];
        sections.forEach(section => {
            allSectionIds.push(section.id);
            if (section.children) {
                section.children.forEach(child => {
                    allSectionIds.push(child.id);
                });
            }
        });
        
        // If activeSection is invalid for this stage, select first available
        if (sections.length > 0 && !allSectionIds.includes(activeSection)) {
            const firstSection = sections[0];
            const firstId = firstSection.children && firstSection.children.length > 0 
                ? firstSection.children[0].id 
                : firstSection.id;
            onSectionChange(firstId);
        }
    }, [stage, sections, activeSection, onSectionChange]);

    // Keyboard shortcut (Cmd+B / Ctrl+B to toggle)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
                e.preventDefault();
                setIsCollapsed(prev => !prev);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    // Persist collapsed state
    useEffect(() => {
        const saved = localStorage.getItem('sidebar-collapsed');
        if (saved !== null) {
            setIsCollapsed(JSON.parse(saved));
        }
    }, []);

    useEffect(() => {
        localStorage.setItem('sidebar-collapsed', JSON.stringify(isCollapsed));
    }, [isCollapsed]);

    if (isCollapsed) {
        return (
            <div className={`w-12 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col ${className}`}>
                <button
                    onClick={() => setIsCollapsed(false)}
                    className="p-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    title="Expand Sidebar (Cmd+B)"
                >
                    <ChevronRight size={20} className="text-gray-600 dark:text-gray-400" />
                </button>
                
                {/* Mini section icons */}
                <div className="flex-1 overflow-y-auto py-2 space-y-2">
                    {sections.map((section: SidebarSectionType) => {
                        const Icon = section.icon;
                        const isActive = activeSection === section.id;
                        return (
                            <button
                                key={section.id}
                                onClick={() => onSectionChange(section.id)}
                                className={`w-full p-2 flex items-center justify-center transition-colors ${
                                    isActive
                                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                                        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                                }`}
                                title={section.label}
                            >
                                <Icon size={18} />
                            </button>
                        );
                    })}
                </div>
            </div>
        );
    }

    return (
        <div className={`w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col ${className}`}>
            {/* Header with stage info */}
            <SidebarHeader stage={stage} metrics={metrics} />

            {/* Collapse Button */}
            <button
                onClick={() => setIsCollapsed(true)}
                className="absolute top-4 right-2 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors opacity-0 hover:opacity-100 group-hover:opacity-100"
                title="Collapse Sidebar (Cmd+B)"
            >
                <ChevronLeft size={16} className="text-gray-600 dark:text-gray-400" />
            </button>

            {/* Sections */}
            <div className="flex-1 overflow-y-auto py-2 px-2 space-y-1">
                {isLoading && sections.length === 0 && (
                    <div className="text-center text-sm text-gray-500 py-8">
                        Loading sections...
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs p-3 rounded-lg">
                        Failed to load metrics
                    </div>
                )}

                {sections.map((section: SidebarSectionType) => (
                    <SidebarSection
                        key={section.id}
                        section={section}
                        activeSection={activeSection}
                        onSectionChange={onSectionChange}
                        metrics={metrics}
                    />
                ))}
            </div>

            {/* Footer hint */}
            <div className="p-3 border-t border-gray-200 dark:border-gray-800 text-xs text-gray-500 dark:text-gray-400">
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">Cmd+B</kbd> to toggle
            </div>
        </div>
    );
}
