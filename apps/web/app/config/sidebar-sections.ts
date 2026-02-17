import { 
    Home, Upload, FolderOpen, Settings, Info, Layout, List, Database, 
    Server, Zap, FileCode, Shield, Lock, Layers, ArrowRight, MessageSquare, 
    Terminal, Activity, FileText, Code, RefreshCw, Shuffle, FolderTree,
    Eye, AlertCircle, CheckCircle, Book, BookOpen, GitBranch, PlayCircle,
    Package, Archive, Download, Search
} from 'lucide-react';

export interface SidebarSection {
    id: string;
    label: string;
    icon: any;
    component?: string;
    collapsible?: boolean;
    children?: SidebarItem[];
    badge?: string;
    status?: boolean;
}

export interface SidebarItem {
    id: string;
    label: string;
    icon: any;
    badge?: string;
    status?: boolean;
    component?: string;
}

/**
 * Sidebar configuration by stage
 * Each stage shows only relevant sections
 */
export const SIDEBAR_SECTIONS: Record<number, SidebarSection[]> = {
    // Stage 0: Discovery (Pre-Triage)
    0: [
        {
            id: 'overview',
            label: 'Overview',
            icon: Home,
            component: 'QuickAssessmentPanel'
        },
        {
            id: 'upload',
            label: 'Upload Files',
            icon: Upload,
            component: 'FileUploadPanel'
        },
        {
            id: 'files',
            label: 'File Browser',
            icon: FolderOpen,
            component: 'FileBrowserPanel',
            badge: 'fileCount'
        },
        {
            id: 'settings',
            label: 'Project Settings',
            icon: Settings,
            component: 'ProjectSettingsPanel'
        }
    ],

    // Stage 1: Triage (Full Analysis)
    1: [
        {
            id: 'quick-info',
            label: 'Quick Info',
            icon: Info,
            component: 'QuickInfoPanel',
            collapsible: true
        },
        {
            id: 'views',
            label: 'Views',
            icon: Layout,
            collapsible: true,
            children: [
                { id: 'graph', label: 'Graph', icon: GitBranch, badge: 'nodeCount' },
                { id: 'grid', label: 'Grid', icon: List, badge: 'assetCount' },
                { id: 'schema', label: 'Schema', icon: Database, badge: 'tableCount' },
                { id: 'mapping', label: 'Mapping', icon: ArrowRight, badge: 'mappingCount' }
            ]
        },
        {
            id: 'analysis',
            label: 'Analysis',
            icon: Search,
            collapsible: true,
            children: [
                { id: 'origin', label: 'Origin', icon: Server, badge: 'sourceSystemCount' },
                { id: 'transform', label: 'Transformations', icon: Zap, badge: 'transformCount' },
                { id: 'queries', label: 'Source Queries', icon: FileCode, badge: 'queryCount' },
                { id: 'quality', label: 'Quality', icon: Shield, badge: 'avgQuality' },
                { id: 'pii', label: 'PII Detection', icon: Lock, badge: 'piiCount' },
                { id: 'partitions', label: 'Partitions', icon: Layers, badge: 'partitionRecs' }
            ]
        },
        {
            id: 'tables',
            label: 'Table Registry',
            icon: Database,
            component: 'TableImpactList',
            collapsible: true,
            badge: 'tableCount'
        },
        {
            id: 'config',
            label: 'Configuration',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'context', label: 'Business Context', icon: MessageSquare, badge: 'contextCount' },
                { id: 'logs', label: 'Execution Logs', icon: Terminal, status: true },
                { id: 'files', label: 'File Explorer', icon: FolderOpen, badge: 'fileCount' }
            ]
        }
    ],

    // Stage 2: Drafting (Code Generation)
    2: [
        {
            id: 'progress',
            label: 'Generation Progress',
            icon: Activity,
            component: 'ProcessProgress'
        },
        {
            id: 'output',
            label: 'Output',
            icon: FileText,
            collapsible: true,
            children: [
                { id: 'logs', label: 'Logs', icon: Terminal, status: true },
                { id: 'code', label: 'Generated Code', icon: Code, badge: 'filesGenerated' },
                { id: 'schema', label: 'Schema Versions', icon: Database, badge: 'versionCount' },
                { id: 'performance', label: 'Performance', icon: Zap },
                { id: 'quality', label: 'Quality Score', icon: Shield, badge: 'qualityScore' }
            ]
        },
        {
            id: 'configuration',
            label: 'Configuration',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'registry', label: 'Design Registry', icon: Database },
                { id: 'mixer', label: 'Tech Mixer', icon: Shuffle },
                { id: 'settings', label: 'Settings', icon: Settings },
                { id: 'prompts', label: 'Prompts', icon: FileText }
            ]
        },
        {
            id: 'files',
            label: 'Output Files',
            icon: FolderTree,
            component: 'MedallionFileTree',
            collapsible: true
        }
    ],

    // Stage 3: Refinement (Optimization)
    3: [
        {
            id: 'status',
            label: 'Refinement Status',
            icon: RefreshCw,
            component: 'RefinementStatus'
        },
        {
            id: 'review',
            label: 'Code Review',
            icon: Eye,
            collapsible: true,
            children: [
                { id: 'logs', label: 'Orchestrator Logs', icon: Terminal, status: true },
                { id: 'comparison', label: 'Code Review', icon: Code },
                { id: 'schema', label: 'Schema Validation', icon: Database },
                { id: 'issues', label: 'Issues', icon: AlertCircle, badge: 'issueCount' }
            ]
        },
        {
            id: 'optimization',
            label: 'Optimization',
            icon: Zap,
            collapsible: true,
            children: [
                { id: 'quality', label: 'Quality', icon: Shield, badge: 'qualityDelta' },
                { id: 'performance', label: 'Performance', icon: Activity },
                { id: 'security', label: 'Security', icon: Lock },
                { id: 'practices', label: 'Best Practices', icon: CheckCircle }
            ]
        },
        {
            id: 'actions',
            label: 'Actions',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'mixer', label: 'Tech Mixer', icon: Shuffle },
                { id: 'settings', label: 'Settings', icon: Settings },
                { id: 'prompts', label: 'Prompts', icon: FileText }
            ]
        }
    ],

    // Stage 4: Governance (Documentation)
    4: [
        {
            id: 'completion',
            label: 'Completion Status',
            icon: CheckCircle,
            component: 'CompletionStatus'
        },
        {
            id: 'documentation',
            label: 'Documentation',
            icon: Book,
            collapsible: true,
            children: [
                { id: 'technical', label: 'Technical Docs', icon: FileText },
                { id: 'dictionary', label: 'Data Dictionary', icon: BookOpen },
                { id: 'lineage', label: 'Lineage Map', icon: GitBranch },
                { id: 'runbook', label: 'Runbook', icon: PlayCircle }
            ]
        },
        {
            id: 'handover',
            label: 'Handover',
            icon: Package,
            collapsible: true,
            children: [
                { id: 'bundle', label: 'COP Bundle', icon: Archive },
                { id: 'download', label: 'Download', icon: Download },
                { id: 'deploy', label: 'Deploy', icon: Upload }
            ]
        }
    ]
};

/**
 * Get sections for a specific stage
 */
export function getSectionsForStage(stage: number): SidebarSection[] {
    return SIDEBAR_SECTIONS[stage] || [];
}

/**
 * Get all section IDs (including children) for a stage
 */
export function getAllSectionIds(stage: number): string[] {
    const sections = getSectionsForStage(stage);
    const ids: string[] = [];
    
    sections.forEach(section => {
        ids.push(section.id);
        if (section.children) {
            section.children.forEach(child => ids.push(child.id));
        }
    });
    
    return ids;
}

/**
 * Find section by ID in a specific stage
 */
export function findSectionById(stage: number, sectionId: string): SidebarSection | SidebarItem | null {
    const sections = getSectionsForStage(stage);
    
    for (const section of sections) {
        if (section.id === sectionId) return section;
        
        if (section.children) {
            const child = section.children.find(c => c.id === sectionId);
            if (child) return child;
        }
    }
    
    return null;
}
