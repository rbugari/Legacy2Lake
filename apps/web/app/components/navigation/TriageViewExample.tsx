"use client";

/**
 * EXAMPLE: TriageView with Stage Sidebar Integration
 * This is a simplified example showing how to integrate the StageSidebar
 * into an existing view component. Use this as a template for other stages.
 * 
 * To use this:
 * 1. Copy the pattern to your actual TriageView.tsx
 * 2. Map old tab IDs to new section IDs
 * 3. Remove old horizontal tab navigation
 * 4. Test all sections render correctly
 */

import React, { useState, useEffect } from 'react';
import StageSidebar from '@/app/components/navigation/StageSidebar';
import ProcessProgress from '@/app/components/ProcessProgress';

// Import your existing view components
// import QuickAssessmentPanel from './QuickAssessmentPanel';
// import GraphView from './GraphView';
// import FileExplorer from './FileExplorer';
// ... etc

interface TriageViewExampleProps {
    projectId: string;
    projectName: string;
}

export default function TriageViewExample({ projectId, projectName }: TriageViewExampleProps) {
    // State for active section (replaces old activeTab)
    const [activeSection, setActiveSection] = useState('quick-info');
    
    // Process running state (for ProcessProgress component)
    const [isTriageRunning, setIsTriageRunning] = useState(false);

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
            {/* Stage Sidebar - Replaces horizontal tabs */}
            <StageSidebar
                stage={1}  // 1 = Triage stage
                projectId={projectId}
                activeSection={activeSection}
                onSectionChange={setActiveSection}
            />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Header */}
                <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                        {projectName}
                    </h1>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Triage Phase - Full Analysis
                    </p>
                </div>

                {/* Content Container */}
                <div className="flex-1 overflow-auto p-6">
                    {/* Quick Info - Default view */}
                    {activeSection === 'quick-info' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Quick Assessment</h2>
                            {/* <QuickAssessmentPanel projectId={projectId} /> */}
                            <p className="text-gray-600">Quick assessment content goes here...</p>
                        </div>
                    )}

                    {/* Views Group */}
                    {activeSection === 'graph' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Architecture Graph</h2>
                            {/* <GraphView projectId={projectId} /> */}
                            <p className="text-gray-600">Graph view content goes here...</p>
                        </div>
                    )}

                    {activeSection === 'files' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Files</h2>
                            {/* <FileExplorer projectId={projectId} /> */}
                            <p className="text-gray-600">File explorer content goes here...</p>
                        </div>
                    )}

                    {activeSection === 'assets' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Assets</h2>
                            {/* <AssetInventory projectId={projectId} /> */}
                            <p className="text-gray-600">Asset inventory content goes here...</p>
                        </div>
                    )}

                    {activeSection === 'tables' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Table Impacts</h2>
                            {/* <TableImpacts projectId={projectId} /> */}
                            <p className="text-gray-600">Table impacts content goes here...</p>
                        </div>
                    )}

                    {/* Analysis Group */}
                    {activeSection === 'transformations' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Transformations</h2>
                            {/* <TransformationsView projectId={projectId} /> */}
                            <p className="text-gray-600">Transformations analysis goes here...</p>
                        </div>
                    )}

                    {activeSection === 'queries' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">SQL Queries</h2>
                            {/* <QueriesView projectId={projectId} /> */}
                            <p className="text-gray-600">Queries analysis goes here...</p>
                        </div>
                    )}

                    {activeSection === 'lineage' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Data Lineage</h2>
                            {/* <DataLineage projectId={projectId} /> */}
                            <p className="text-gray-600">Data lineage visualization goes here...</p>
                        </div>
                    )}

                    {activeSection === 'dependencies' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Dependency DAG</h2>
                            {/* <DependencyDAG projectId={projectId} /> */}
                            <p className="text-gray-600">Dependency graph goes here...</p>
                        </div>
                    )}

                    {activeSection === 'quality' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Quality Metrics</h2>
                            {/* <QualityMetrics projectId={projectId} /> */}
                            <p className="text-gray-600">Quality metrics content goes here...</p>
                        </div>
                    )}

                    {activeSection === 'pii' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">PII Analysis</h2>
                            {/* <PIIAnalysis projectId={projectId} /> */}
                            <p className="text-gray-600">PII detection results go here...</p>
                        </div>
                    )}

                    {/* Config Group */}
                    {activeSection === 'settings' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Project Settings</h2>
                            {/* <ProjectSettings projectId={projectId} /> */}
                            <p className="text-gray-600">Settings form goes here...</p>
                        </div>
                    )}

                    {activeSection === 'prompts' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Prompts</h2>
                            {/* <PromptManager projectId={projectId} /> */}
                            <p className="text-gray-600">Prompt management goes here...</p>
                        </div>
                    )}

                    {activeSection === 'models' && (
                        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                            <h2 className="text-xl font-bold mb-4">Agent Matrix</h2>
                            {/* <AgentMatrix projectId={projectId} /> */}
                            <p className="text-gray-600">Agent-model configuration goes here...</p>
                        </div>
                    )}

                    {/* Process Progress (if triage is running) */}
                    {activeSection === 'logs' && (
                        <ProcessProgress
                            isRunning={isTriageRunning}
                            logs={[]}  // Fetch logs from API or pass from parent
                            processName="Triage Analysis"
                            onCancel={() => setIsTriageRunning(false)}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

/**
 * MIGRATION NOTES:
 * 
 * 1. Section ID Mapping (old tab → new section):
 *    - 'overview' → 'quick-info'
 *    - 'graph' → 'graph' (same)
 *    - 'files' → 'files' (same)
 *    - 'assets' → 'assets' (same)
 *    - 'tables' → 'tables' (same)
 *    - 'transformations' → 'transformations' (same)
 *    - 'queries' → 'queries' (same)
 *    - 'lineage' → 'lineage' (same)
 *    - 'dependencies' → 'dependencies' (same)
 *    - 'quality' → 'quality' (same)
 *    - 'pii' → 'pii' (same)
 *    - 'settings' → 'settings' (same)
 *    - 'prompts' → 'prompts' (same)
 *    - 'models' → 'models' (same)
 * 
 * 2. Remove old code:
 *    - Delete TABS array definition
 *    - Remove horizontal tab rendering logic
 *    - Remove old tab styling
 * 
 * 3. Benefits:
 *    - Cleaner code (no massive switch/if-else for tabs)
 *    - Auto-updating badges (asset count, table count, etc.)
 *    - Collapsible groups (Views, Analysis, Config)
 *    - Keyboard shortcut (Cmd+B)
 *    - Better scalability (easy to add new sections)
 * 
 * 4. Testing:
 *    - Click through all sections
 *    - Verify content renders correctly
 *    - Test collapse/expand groups
 *    - Check badge counts
 *    - Test keyboard shortcut
 */
