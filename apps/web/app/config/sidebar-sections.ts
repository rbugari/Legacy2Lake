import {
    Home, Upload, FolderOpen, Settings, Info, Layout, List, Database,
    Server, Zap, FileCode, Shield, Lock, Layers, ArrowRight, MessageSquare,
    Terminal, Activity, FileText, Code, RefreshCw, FolderTree,
    Eye, AlertCircle, CheckCircle, Book, BookOpen, GitBranch, PlayCircle,
    Package, Archive, Download, Search, BarChart3, ShieldCheck, ShieldAlert, Cpu
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
    variant?: 'view' | 'action';
}

export interface SidebarItem {
    id: string;
    label: string;
    icon: any;
    badge?: string;
    status?: boolean;
    component?: string;
    variant?: 'view' | 'action'; // Added for visual distinction
}

/**
 * Sidebar configuration by stage
 * Each stage shows only relevant sections
 */
export const SIDEBAR_SECTIONS: Record<number, SidebarSection[]> = {
    // Stage 0: Discovery
    0: [
        {
            id: 'quick-info',
            label: 'Quick Info',
            icon: Info
        },
        {
            id: 'overview',
            label: 'Overview',
            icon: Home,
            variant: 'view'
        },
        {
            id: 'analysis',
            label: 'Analysis Reports',
            icon: Search,
            collapsible: true,
            children: [
                { id: 'assessment', label: 'Forensic Assessment', icon: ShieldCheck, variant: 'view' },
                { id: 'validation', label: 'Tech Validation', icon: Cpu, variant: 'view' }
            ]
        },
        {
            id: 'config',
            label: 'Project Data',
            icon: Database,
            collapsible: true,
            children: [
                { id: 'upload', label: 'Tribal Knowledge', icon: Upload, variant: 'action' },
                { id: 'files', label: 'File Pre-Classification', icon: FolderOpen, badge: 'fileCount', variant: 'view' }
            ]
        },
        {
            id: 'execution',
            label: 'Execution',
            icon: PlayCircle,
            collapsible: true,
            children: [
                { id: 'logs', label: 'Execution Logs', icon: Terminal, status: true, variant: 'view' },
                { id: 'run-scan', label: 'Run Forensic Scan', icon: PlayCircle, variant: 'action' }
            ]
        }
    ],

    // Stage 1: Triage (Full Analysis)
    1: [
        {
            id: 'quick-info',
            label: 'Quick Info',
            icon: Info
        },
        {
            id: 'overview',
            label: 'Overview',
            icon: Home,
            variant: 'view'
        },
        {
            id: 'views',
            label: 'Views',
            icon: Layout,
            collapsible: true,
            children: [
                { id: 'graph', label: 'Graph', icon: GitBranch, badge: 'nodeCount', variant: 'view' },
                { id: 'grid', label: 'Grid', icon: List, badge: 'assetCount', variant: 'view' },
                { id: 'schema', label: 'Schema', icon: Database, badge: 'tableCount', variant: 'view' },
                { id: 'mapping', label: 'Mapping', icon: ArrowRight, badge: 'mappingCount', variant: 'view' }
            ]
        },
        {
            id: 'analysis',
            label: 'Analysis',
            icon: Search,
            collapsible: true,
            children: [
                { id: 'origin', label: 'Origin', icon: Server, badge: 'sourceSystemCount', variant: 'view' },
                { id: 'transform', label: 'Transformations', icon: Zap, badge: 'transformCount', variant: 'view' },
                { id: 'queries', label: 'Source Queries', icon: FileCode, badge: 'queryCount', variant: 'view' },
                { id: 'quality', label: 'Code Quality', icon: Shield, badge: 'avgQuality', variant: 'view' },
                { id: 'pii', label: 'PII Detection', icon: Lock, badge: 'piiCount', variant: 'view' },
                { id: 'tables', label: 'Table Registry', icon: Database, badge: 'tableCount', variant: 'view' }
            ]
        },
        {
            id: 'config',
            label: 'Configuration',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'context', label: 'Business Context', icon: MessageSquare, badge: 'contextCount', variant: 'action' },
                { id: 'logs', label: 'Execution Logs', icon: Terminal, status: true, variant: 'view' },
                { id: 'files', label: 'File Explorer', icon: FolderOpen, badge: 'fileCount', variant: 'view' }
            ]
        },
        {
            id: 'actions',
            label: 'Actions',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'run-triage', label: 'Run Analysis', icon: PlayCircle, variant: 'action' }
            ]
        }
    ],

    // Stage 2: Drafting (1:1 Code Generation - "Make it Work")
    // Philosophy: Direct migration, minimal structure changes, focus on OUTPUT
    2: [
        {
            id: 'quick-info',
            label: 'Quick Info',
            icon: Info
        },
        {
            id: 'overview',
            label: 'Overview',
            icon: Home,
            variant: 'view'
        },
        {
            id: 'execution',
            label: 'Execution',
            icon: PlayCircle,
            collapsible: true,
            children: [
                { id: 'progress', label: 'Pipeline Status', icon: Activity, status: true, variant: 'view' },
                { id: 'logs', label: 'Execution Logs', icon: Terminal, status: true, variant: 'view' }
            ]
        },
        {
            id: 'output',
            label: 'Generated Output',
            icon: FileText,
            collapsible: true,
            children: [
                { id: 'code', label: 'Generation Summary', icon: BarChart3, badge: 'filesGenerated', variant: 'view' },
                { id: 'files', label: 'Output Files', icon: FolderTree, badge: 'fileCount', variant: 'view' },
                { id: 'stats', label: 'Generation Stats', icon: Activity, variant: 'view' }
            ]
        },
        {
            id: 'target',
            label: 'Target Configuration',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'cartridge', label: 'Cartridge Settings', icon: Package, variant: 'action' },
                { id: 'prompts', label: 'Cartridge Prompt', icon: FileCode, variant: 'action' },
                { id: 'schema', label: 'Target Schema', icon: Database, variant: 'view' }
            ]
        },
        {
            id: 'actions',
            label: 'Actions',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'run-translation', label: 'Run Pipeline', icon: PlayCircle, variant: 'action' }
            ]
        }
    ],

    // Stage 3: Refinement (Optimization)
    3: [
        {
            id: 'quick-info',
            label: 'Quick Info',
            icon: Info
        },
        {
            id: 'overview',
            label: 'Overview',
            icon: Home,
            variant: 'view'
        },
        {
            id: 'status',
            label: 'Status Dashboard',
            icon: Activity,
            component: 'RefinementStatus',
            variant: 'view'
        },
        {
            id: 'summary',
            label: 'Refinement Summary',
            icon: BarChart3,
            component: 'RefinementSummary',
            variant: 'view'
        },
        {
            id: 'explorer',
            label: 'Generated Files',
            icon: FolderTree,
            collapsible: true,
            children: [
                { id: 'comparison', label: '📂 File Explorer', icon: FolderOpen, badge: 'fileCount', variant: 'view' },
                { id: 'logs', label: '📋 Execution Logs', icon: Terminal, status: true, variant: 'view' }
            ]
        },
        {
            id: 'quality',
            label: 'Quality Metrics',
            icon: Shield,
            collapsible: true,
            children: [
                { id: 'quality', label: 'Quality Score', icon: BarChart3, badge: 'qualityDelta', variant: 'view' },
                { id: 'schema', label: 'Schema Validation', icon: Database, variant: 'view' }
            ]
        },
        {
            id: 'actions',
            label: 'Configuration',
            icon: Settings,
            collapsible: true,
            children: [
                { id: 'run-refinement', label: 'Run Refinement', icon: PlayCircle, variant: 'action' },
                { id: 'settings', label: 'Design Settings', icon: Settings, variant: 'action' },
                { id: 'prompts', label: 'Cartridge Prompts', icon: FileCode, variant: 'action' }
            ]
        }
    ],

    // Stage 4: Governance & Certification
    4: [
        {
            id: 'quick-info',
            label: 'Quick Info',
            icon: Info
        },
        {
            id: 'overview',
            label: 'Overview',
            icon: Home,
            variant: 'view'
        },
        {
            id: 'report',
            label: 'Certification Report',
            icon: ShieldCheck,
            variant: 'view',
            status: true
        },
        {
            id: 'logs',
            label: 'Execution Logs',
            icon: Terminal,
            variant: 'view',
            status: true
        },
        {
            id: 'audit',
            label: 'Audit Checks',
            icon: ShieldAlert,
            variant: 'view'
        },
        {
            id: 'gaps',
            label: 'Gap Workspace',
            icon: AlertCircle,
            variant: 'view',
            badge: 'gapCount'
        },
        {
            id: 'quality',
            label: 'Quality Metrics',
            icon: BarChart3,
            variant: 'view'
        },
        {
            id: 'documentation',
            label: 'Lineage & Runbook',
            icon: GitBranch,
            variant: 'view'
        }
    ],

    // Stage 5: Handover
    5: [
        {
            id: 'quick-info',
            label: 'Quick Info',
            icon: Info
        },
        {
            id: 'overview',
            label: 'Overview',
            icon: Home,
            variant: 'view'
        },
        {
            id: 'handover-pkg',
            label: 'Handover Package',
            icon: Package,
            variant: 'view',
            status: true
        },
        {
            id: 'actions',
            label: 'Actions',
            icon: Settings,
            collapsible: true,
            children: [
                {
                    id: 'export-delivery',
                    label: 'Download Deployable Code',
                    icon: Download,
                    component: 'ExportOptions',
                    variant: 'action'
                },
                {
                    id: 'export-full',
                    label: 'Download Complete Bundle',
                    icon: Archive,
                    component: 'ExportOptions',
                    variant: 'action'
                }
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
