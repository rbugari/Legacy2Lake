import { useState, useEffect } from 'react';
import { fetchWithAuth } from '../lib/auth-client';

const RUNNING_STATUSES = ['PROCESSING', 'ORCHESTRATING', 'REFINING', 'GENERATING', 'GOVERNANCE', 'DOCUMENTING', 'CERTIFYING'];

export interface SidebarMetrics {
    // Stage 0 (Discovery)
    fileCount?: number;
    uploadStatus?: string;
    
    // Stage 1 (Triage)
    quickAssessment?: {
        score: number;
        classification: string;
    };
    assetCount?: number;
    tableCount?: number;
    nodeCount?: number;
    mappingCount?: number;
    sourceSystemCount?: number;
    transformCount?: number;
    queryCount?: number;
    avgQuality?: number;
    piiCount?: number;
    partitionRecs?: number;
    contextCount?: number;
    
    // Stage 2 (Drafting)
    generationProgress?: number;
    filesGenerated?: number;
    currentAgent?: string;
    versionCount?: number;
    qualityScore?: number;
    
    // Stage 3 (Refinement)
    refinementStatus?: string;
    issueCount?: number;
    qualityDelta?: number;
    suggestionsCount?: number;
    
    // Stage 4 (Governance)
    docsGenerated?: boolean;
    bundleReady?: boolean;
    
    // Common
    executionStatus?: string;
    lastActivity?: string;
}

/**
 * Hook to fetch sidebar metrics for current stage
 * Auto-refreshes every 3 seconds if process is running
 */
export function useSidebarMetrics(projectId: string, stage: number, enabled: boolean = true) {
    const [metrics, setMetrics] = useState<SidebarMetrics>({});
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!enabled || !projectId) {
            setIsLoading(false);
            return;
        }

        let isMounted = true;
        let interval: NodeJS.Timeout | null = null;

        async function fetchMetrics() {
            try {
                const response = await fetchWithAuth(
                    `/projects/${projectId}/sidebar-metrics?stage=${stage}`
                );

                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }

                const data = await response.json();

                if (isMounted) {
                    setMetrics(data);
                    setError(null);
                    setIsLoading(false);
                }

                // Auto-refresh if process is running
                if (data.executionStatus && 
                    RUNNING_STATUSES.includes(data.executionStatus)) {
                    if (!interval && isMounted) {
                        interval = setInterval(fetchMetrics, 10000); // 10 seconds
                    }
                } else {
                    // Stop polling if not running
                    if (interval) {
                        clearInterval(interval);
                        interval = null;
                    }
                }
            } catch (err) {
                if (isMounted) {
                    setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
                    setIsLoading(false);
                }
            }
        }

        fetchMetrics();

        return () => {
            isMounted = false;
            if (interval) clearInterval(interval);
        };
    }, [projectId, stage, enabled]);

    return { metrics, isLoading, error };
}

/**
 * Format badge value for display
 */
export function formatBadgeValue(metrics: SidebarMetrics, badgeKey: string): string | number | null {
    const value = metrics[badgeKey as keyof SidebarMetrics];
    
    if (value === undefined || value === null) return null;
    
    // Handle boolean values
    if (typeof value === 'boolean') {
        return value ? '✓' : '✗';
    }
    
    // Handle objects (like quickAssessment)
    if (typeof value === 'object' && value !== null) {
        if ('score' in value) return value.score;
        return null;
    }
    
    // Special formatting for specific metrics
    if (badgeKey === 'avgQuality' && typeof value === 'number') {
        return `${Math.round(value)}%`;
    }
    
    if (badgeKey === 'qualityScore' && typeof value === 'number') {
        return Math.round(value);
    }
    
    if (badgeKey === 'qualityDelta' && typeof value === 'number') {
        return value > 0 ? `+${value}%` : `${value}%`;
    }
    
    if (badgeKey === 'generationProgress' && typeof value === 'number') {
        return `${value}%`;
    }
    
    // Return primitive values (string or number)
    if (typeof value === 'string' || typeof value === 'number') {
        return value;
    }
    
    return null;
}
