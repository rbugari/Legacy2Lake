# React Stage View Component Pattern

**Category:** Frontend - React Components  
**Use Case:** Creating stage view components for the 6-stage migration flow

## Pattern Template

```typescript
"use client";

/**
 * {Stage Name} View Component
 * =============================
 * 
 * Purpose:
 *     {Description of this stage's responsibility}
 * 
 * Features:
 *     - {Feature 1}
 *     - {Feature 2}
 *     - {Feature 3}
 * 
 * Props:
 *     - projectId: UUID of the project
 *     - tenantId: Optional tenant ID (from context)
 * 
 * Author: Legacy2Lake Engineering
 * Date: {Current Date}
 * Version: v1.0
 */

import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '@/lib/auth-client';

// ================================================================
// TYPES & INTERFACES
// ================================================================

interface {Stage}ViewProps {
    projectId: string;
    tenantId?: string;
}

interface {Stage}Data {
    // Define data structure based on API response
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    results: {Stage}Results;
    metadata: Record<string, any>;
}

interface {Stage}Results {
    // Define results structure
    total_items: number;
    processed_items: number;
    success_rate: number;
    details: Array<{Stage}Item>;
}

interface {Stage}Item {
    // Define individual item structure
    item_id: string;
    name: string;
    status: string;
}

// ================================================================
// MAIN COMPONENT
// ================================================================

export default function {Stage}View({ projectId, tenantId }: {Stage}ViewProps) {
    // State management
    const [data, setData] = useState<{Stage}Data | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    
    // Tab state (if using tabs)
    const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'logs'>('overview');
    
    // Load data on mount and when projectId changes
    useEffect(() => {
        if (projectId) {
            loadData();
        }
    }, [projectId]);
    
    // ================================================================
    // DATA LOADING
    // ================================================================
    
    const loadData = async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await fetchWithAuth(
                `/api/v1/projects/${projectId}/{stage-endpoint}`
            );
            
            if (!response.ok) {
                throw new Error(`Failed to load {stage} data: ${response.status}`);
            }
            
            const result = await response.json();
            setData(result);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error';
            setError(errorMessage);
            console.error('[{Stage}View] Load failed:', err);
        } finally {
            setIsLoading(false);
        }
    };
    
    // ================================================================
    // ACTIONS
    // ================================================================
    
    const handleStart{Stage} = async () => {
        setIsProcessing(true);
        setError(null);
        
        try {
            const response = await fetchWithAuth(
                `/api/v1/projects/${projectId}/{stage-endpoint}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        // Add request payload
                        force_refresh: false
                    })
                }
            );
            
            if (!response.ok) {
                throw new Error(`Failed to start {stage}: ${response.status}`);
            }
            
            const result = await response.json();
            setData(result);
            
            // Show success message
            console.log('[{Stage}View] {Stage} started successfully');
            
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error';
            setError(errorMessage);
            console.error('[{Stage}View] Start failed:', err);
        } finally {
            setIsProcessing(false);
        }
    };
    
    const handleRefresh = async () => {
        await loadData();
    };
    
    // ================================================================
    // RENDER HELPERS
    // ================================================================
    
    const renderStatus = (status: string) => {
        const statusColors = {
            pending: 'bg-gray-100 text-gray-800',
            running: 'bg-blue-100 text-blue-800',
            completed: 'bg-green-100 text-green-800',
            failed: 'bg-red-100 text-red-800'
        };
        
        return (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status as keyof typeof statusColors]}`}>
                {status.toUpperCase()}
            </span>
        );
    };
    
    const renderProgressBar = (current: number, total: number) => {
        const percentage = total > 0 ? (current / total) * 100 : 0;
        
        return (
            <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        );
    };
    
    // ================================================================
    // LOADING & ERROR STATES
    // ================================================================
    
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
                <span className="ml-3 text-gray-600">Loading {stage} data...</span>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                    <svg className="w-5 h-5 text-red-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">Error loading {stage} data</h3>
                        <p className="mt-1 text-sm text-red-700">{error}</p>
                        <button
                            onClick={handleRefresh}
                            className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                        >
                            Try again
                        </button>
                    </div>
                </div>
            </div>
        );
    }
    
    if (!data) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-600 mb-4">No {stage} data available</p>
                <button
                    onClick={handleStart{Stage}}
                    disabled={isProcessing}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isProcessing ? 'Starting...' : 'Start {Stage}'}
                </button>
            </div>
        );
    }
    
    // ================================================================
    // MAIN RENDER
    // ================================================================
    
    return (
        <div className="space-y-6">
            {/* Header Section */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900">{Stage Name}</h2>
                    <p className="text-gray-600 mt-1">{Description of this stage}</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleRefresh}
                        disabled={isLoading}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                    >
                        Refresh
                    </button>
                    <button
                        onClick={handleStart{Stage}}
                        disabled={isProcessing || data.status === 'running'}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isProcessing ? 'Processing...' : 'Run {Stage}'}
                    </button>
                </div>
            </div>
            
            {/* Status Card */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Status</h3>
                    {renderStatus(data.status)}
                </div>
                
                <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                        <p className="text-sm text-gray-600">Total Items</p>
                        <p className="text-2xl font-bold">{data.results.total_items}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-600">Processed</p>
                        <p className="text-2xl font-bold">{data.results.processed_items}</p>
                    </div>
                    <div>
                        <p className="text-sm text-gray-600">Success Rate</p>
                        <p className="text-2xl font-bold">{data.results.success_rate}%</p>
                    </div>
                </div>
                
                {renderProgressBar(data.results.processed_items, data.results.total_items)}
            </div>
            
            {/* Tabs Section */}
            <div className="bg-white border border-gray-200 rounded-lg">
                {/* Tab Headers */}
                <div className="border-b border-gray-200">
                    <nav className="flex space-x-4 px-6">
                        {['overview', 'details', 'logs'].map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab as any)}
                                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                                    activeTab === tab
                                        ? 'border-blue-600 text-blue-600'
                                        : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                                }`}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </nav>
                </div>
                
                {/* Tab Content */}
                <div className="p-6">
                    {activeTab === 'overview' && (
                        <div>
                            <h3 className="text-lg font-semibold mb-4">Overview</h3>
                            {/* Add overview content */}
                            <p className="text-gray-600">Overview content goes here</p>
                        </div>
                    )}
                    
                    {activeTab === 'details' && (
                        <div>
                            <h3 className="text-lg font-semibold mb-4">Details</h3>
                            {/* Add details content */}
                            <div className="space-y-2">
                                {data.results.details.map((item) => (
                                    <div key={item.item_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                                        <span className="font-medium">{item.name}</span>
                                        {renderStatus(item.status)}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {activeTab === 'logs' && (
                        <div>
                            <h3 className="text-lg font-semibold mb-4">Logs</h3>
                            {/* Add logs content */}
                            <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm">
                                <p>Logs content goes here...</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
```

## Usage Example

```typescript
// In a page component
import {Stage}View from '@/components/stages/{Stage}View';

export default function ProjectPage({ params }: { params: { id: string } }) {
    return (
        <div className="container mx-auto p-6">
            <{Stage}View projectId={params.id} />
        </div>
    );
}
```

## Key Features

- ✅ fetchWithAuth for authenticated API calls
- ✅ Loading, error, and empty states
- ✅ Tab-based navigation
- ✅ Real-time progress tracking
- ✅ Status badges with color coding
- ✅ Refresh and action buttons
- ✅ Responsive grid layout
- ✅ TypeScript type safety
- ✅ Consistent error handling

## Customization Guide

1. **Replace placeholders:**
   - `{Stage}` → DiscoveryView, TriageView, DraftingView, etc.
   - `{stage}` → discovery, triage, drafting, etc.
   - `{Stage Name}` → "Stage 1: Discovery", etc.
   - `{stage-endpoint}` → API endpoint path

2. **Add stage-specific features:**
   - Custom visualizations (charts, graphs)
   - Stage-specific actions
   - Additional tabs
   - Real-time updates via WebSocket

3. **Styling:**
   - Uses Tailwind CSS classes
   - Customize colors via `statusColors` object
   - Adjust spacing and sizing as needed
