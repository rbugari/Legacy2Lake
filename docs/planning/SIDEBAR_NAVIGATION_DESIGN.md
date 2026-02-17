# Sidebar Navigation Design - Fase Visual v4.0

**Fecha:** Febrero 16, 2026  
**Estado:** 🟢 SPECIFICATION READY  
**Objetivo:** Convertir tabs horizontales en sidebar vertical inteligente aprovechando datos de v4.0

---

## 🎯 Problema Actual

### TriageView tiene 13 tabs en 3 grupos:
```
Views (4):      Graph | Grid | Schema | Mapping
Analysis (6):   Origin | Transform | Queries | Quality | PII | Partitions
Config (3):     Manual Input | Execution | File Explorer
```

**Issues:**
- Demasiados tabs horizontales (no escala)
- No muestra métricas rápidas (hay que entrar para ver)
- No aprovecha la data enriquecida de v4.0 Backend
- **Cada fase debería mostrar solo lo relevante**

---

## 💡 Concept: Sidebar Adaptativa por Stage

**Idea:** La sidebar cambia su contenido según el stage actual del proyecto.

```
Stage 0: Discovery  → Quick Assessment + File Upload
Stage 1: Triage     → Full analysis (13 sections)
Stage 2: Drafting   → Code generation monitoring
Stage 3: Refinement → Code review + optimization
Stage 4: Governance → Documentation + handover
```

---

## 🎨 Solución: Sidebar Vertical Inteligente

**Concepto:** Sidebar adaptativa que muestra secciones relevantes según el stage actual.

---

## 📋 Sidebar por Stage (Adaptativa)

### Stage 0: Discovery (Pre-Triage)
```tsx
┌─────────────────────────┐
│ 🏠 OVERVIEW             │
├─────────────────────────┤
│ 🚦 Quick Assessment     │
│   Score: -- / Pending   │
│                         │
│ 📊 UPLOAD               │
│   📁 File Upload        │
│   🔍 File Browser       │
│                         │
│ 📋 PROJECT INFO         │
│   ⚙️ Settings           │
│   📄 Description        │
└─────────────────────────┘
```

**Sections:**
- Quick Assessment panel (run assessment button)
- File upload area
- File browser (R2 Triage folder)
- Project settings/metadata
- Start Triage button (when files ready)

---

### Stage 1: Triage (Full Analysis)
```tsx
┌─────────────────────────┐
│ 🚦 QUICK INFO           │
│   Score: 85 🟢         │
│   Assets: 12           │
│   Tables: 8            │
├─────────────────────────┤
│ 📊 VIEWS ▼             │
│   📈 Graph [12]        │
│   📋 Grid [12]         │
│   🗄️ Schema [8]        │
│   🔗 Mapping [45]      │
├─────────────────────────┤
│ 🔍 ANALYSIS ▼          │
│   🌐 Origin [5]        │
│   ⚡ Transforms [23]   │
│   📝 Queries [18]      │
│   🛡️ Quality [78%]    │
│   🔒 PII [4]           │
│   📂 Partitions [3]    │
├─────────────────────────┤
│ 📊 TABLES (NEW) ▼      │
│   dbo.Customers [2R/1W]│
│   dbo.Products [1R/1W] │
│   dbo.Sales [0R/1W]    │
├─────────────────────────┤
│ ⚙️ CONFIG ▼            │
│   💬 Context [2]       │
│   📜 Logs              │
│   📁 Files [45]        │
└─────────────────────────┘
```

**Sections:** (13 total - all analysis available)
- Quick Info panel (collapsible)
- Views: Graph, Grid, Schema, Mapping
- Analysis: Origin, Transforms, Queries, Quality, PII, Partitions
- Tables: NEW - Table registry with impacts
- Config: Business context, Logs, Files

---

### Stage 2: Drafting (Code Generation)
```tsx
┌─────────────────────────┐
│ ⚙️ GENERATION           │
├─────────────────────────┤
│ 📊 PROGRESS             │
│   ██████░░ 60%         │
│   Agent C: Working...   │
│   12/20 files done      │
├─────────────────────────┤
│ 📂 OUTPUT ▼            │
│   📝 Logs [Live]       │
│   💻 Generated Code    │
│   🗄️ Schema Versions   │
│   📊 Performance       │
│   ✅ Quality Score     │
├─────────────────────────┤
│ 🔧 CONFIGURATION ▼     │
│   🎛️ Registry          │
│   🔀 Tech Mixer        │
│   ⚙️ Settings          │
│   🔒 Prompts           │
├─────────────────────────┤
│ 📁 FILES ▼             │
│   🌳 Bronze/ [8]       │
│   🥈 Silver/ [4]       │
│   🥇 Gold/ [2]         │
└─────────────────────────┘
```

**Sections:** (Focus on generation)
- Progress panel (real-time with ProcessProgress)
- Output: Logs (live), Code viewer, Schema history
- Performance metrics
- Quality dashboard
- Configuration: Registry, Tech Mixer, Settings, Prompts
- File explorer (medallion structure)

---

### Stage 3: Refinement (Optimization)
```tsx
┌─────────────────────────┐
│ 🔄 REFINEMENT           │
├─────────────────────────┤
│ 📊 STATUS               │
│   Profile: Analyzing... │
│   Agent F: Reviewing    │
├─────────────────────────┤
│ 🔍 REVIEW ▼            │
│   📜 Orchestrator Logs │
│   💻 Code Review       │
│   🗄️ Schema Validation │
│   ⚠️ Issues [12]       │
├─────────────────────────┤
│ 🎯 OPTIMIZATION ▼      │
│   🛡️ Quality [+15%]   │
│   ⚡ Performance       │
│   🔒 Security          │
│   📊 Best Practices    │
├─────────────────────────┤
│ 🔧 ACTIONS ▼           │
│   🎛️ Mixer             │
│   ⚙️ Settings          │
│   🔒 Prompts           │
└─────────────────────────┘
```

**Sections:** (Focus on quality)
- Status panel (refinement progress)
- Review: Logs, Code comparison, Schema validation, Issues
- Optimization: Quality improvements, Performance, Security
- Actions: Tech Mixer, Settings, Prompts

---

### Stage 4: Governance (Documentation)
```tsx
┌─────────────────────────┐
│ 📚 GOVERNANCE           │
├─────────────────────────┤
│ 📊 COMPLETION           │
│   ✅ Code Ready         │
│   ✅ Tests Pass         │
│   ⏳ Docs Generating    │
├─────────────────────────┤
│ 📝 DOCUMENTATION ▼     │
│   📖 Technical Docs    │
│   📊 Data Dictionary   │
│   🔍 Lineage Map       │
│   📋 Runbook           │
├─────────────────────────┤
│ 📦 HANDOVER ▼          │
│   🎁 COP Bundle        │
│   💾 Download          │
│   📤 Deploy            │
└─────────────────────────┘
```

**Sections:** (Focus on delivery)
- Completion status
- Documentation: Technical docs, Data dictionary, Lineage, Runbook
- Handover: COP bundle, Download options, Deployment

---

## 🎨 Sidebar Component - Adaptive Logic

### Layout Propuesto

```
┌─────────────────────────────────────────────────────────┐
│ StageHeader (top bar)                                   │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ SIDEBAR  │  MAIN CONTENT AREA                          │
│ (250px)  │  (Dynamic based on active section)          │
│          │                                              │
│ 🏠 Quick │  [Graph View / Grid / Logs / etc.]          │
│ 📊 Views │                                              │
│ 🔍 Analysis                                             │
│ ⚙️ Config│                                              │
│          │                                              │
│ [Badges] │                                              │
│ [Counters]                                              │
└──────────┴──────────────────────────────────────────────┘
```

---

## 🎨 Sidebar Component - Adaptive Logic

### Component Structure

```tsx
// apps/web/app/components/navigation/StageSidebar.tsx

interface StageSidebarProps {
  stage: number; // 0-4
  projectId: string;
  tenantId: string;
  onSectionChange: (section: string) => void;
  activeSection: string;
}

export default function StageSidebar({ 
  stage, 
  projectId, 
  tenantId,
  onSectionChange,
  activeSection 
}: StageSidebarProps) {
  // Fetch metrics based on stage
  const metrics = useSidebarMetrics(projectId, stage);
  
  // Render sections based on stage
  const sections = getSectionsForStage(stage);
  
  return (
    <aside className="w-64 bg-gray-50 dark:bg-gray-900 border-r h-full overflow-y-auto">
      {/* Stage-specific header */}
      <SidebarHeader stage={stage} metrics={metrics} />
      
      {/* Dynamic sections */}
      {sections.map(section => (
        <SidebarSection
          key={section.id}
          section={section}
          isActive={activeSection === section.id}
          onClick={() => onSectionChange(section.id)}
          metrics={metrics}
        />
      ))}
    </aside>
  );
}
```

### Section Configuration by Stage

```tsx
// apps/web/app/config/sidebar-sections.ts

export const SIDEBAR_SECTIONS = {
  // Stage 0: Discovery
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
      component: 'FileBrowserPanel'
    },
    {
      id: 'settings',
      label: 'Project Settings',
      icon: Settings,
      component: 'ProjectSettingsPanel'
    }
  ],
  
  // Stage 1: Triage (Full analysis)
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
        { id: 'transforms', label: 'Transformations', icon: Zap, badge: 'transformCount' },
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
  
  // Stage 2: Drafting
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
        { id: 'code', label: 'Generated Code', icon: Code, badge: 'fileCount' },
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
  
  // Stage 3: Refinement
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
  
  // Stage 4: Governance
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

export function getSectionsForStage(stage: number) {
  return SIDEBAR_SECTIONS[stage] || [];
}
```

---

## 📊 Metrics Hook by Stage

## 📊 Metrics Hook by Stage

```tsx
// apps/web/app/hooks/useSidebarMetrics.ts

export function useSidebarMetrics(projectId: string, stage: number) {
  const [metrics, setMetrics] = useState<SidebarMetrics>({});
  
  useEffect(() => {
    async function fetchMetrics() {
      // Fetch only metrics relevant to current stage
      const endpoint = `/api/v1/projects/${projectId}/sidebar-metrics?stage=${stage}`;
      const response = await fetchWithAuth(endpoint);
      setMetrics(response);
    }
    
    fetchMetrics();
    
    // Auto-refresh if process is running
    const interval = setInterval(fetchMetrics, 3000);
    return () => clearInterval(interval);
  }, [projectId, stage]);
  
  return metrics;
}

interface SidebarMetrics {
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
```

---

## 🔌 Backend API - Stage-Aware Metrics

```python
# apps/api/routers/projects.py

@router.get("/{project_id}/sidebar-metrics")
async def get_sidebar_metrics(
    project_id: str,
    stage: int = Query(..., ge=0, le=4),
    db: SupabasePersistence = Depends(get_db)
):
    """
    Returns metrics relevant to current stage.
    Optimized to fetch only what's needed.
    """
    
    metrics = {}
    
    if stage == 0:  # Discovery
        # Count files in Triage folder
        files = await db.get_file_inventory(project_id)
        metrics["fileCount"] = len(files)
        metrics["uploadStatus"] = "ready" if len(files) > 0 else "pending"
    
    elif stage == 1:  # Triage
        # Full metrics - all analysis available
        project = await db.get_project(project_id)
        metrics["quickAssessment"] = project.get("quick_assessment")
        
        # Asset counts
        assets = await db.get_objects(project_id)
        metrics["assetCount"] = len(assets)
        
        # Table impacts (Fase C)
        table_impacts = await db.get_table_impacts(project_id)
        metrics["tableCount"] = len(set(t["table_name"] for t in table_impacts))
        
        # Column mappings
        mappings = await db.get_column_mappings(project_id)
        metrics["mappingCount"] = len(mappings)
        
        # Sprint 8.5 metrics
        source_systems = set()
        transform_count = 0
        query_count = 0
        
        for asset in assets:
            meta = asset.get("metadata", {})
            if meta.get("source_systems"):
                source_systems.update(meta["source_systems"])
            if meta.get("transformations"):
                transform_count += len(meta["transformations"])
            if asset.get("source_query"):
                query_count += 1
        
        metrics["sourceSystemCount"] = len(source_systems)
        metrics["transformCount"] = transform_count
        metrics["queryCount"] = query_count
        
        # Quality metrics (Sprint 7 + 11)
        columns = await db.get_asset_columns(project_id)
        if columns:
            quality_scores = [c["quality_score"] for c in columns if c.get("quality_score")]
            metrics["avgQuality"] = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            metrics["piiCount"] = sum(1 for c in columns if c.get("has_pii"))
            metrics["partitionRecs"] = sum(1 for c in columns if c.get("partition_recommendation"))
        
        # Business context
        contexts = await db.get_solution_contexts(project_id)
        metrics["contextCount"] = sum(1 for c in contexts if c.get("notes"))
    
    elif stage == 2:  # Drafting
        # Generation progress
        registry = await db.get_design_registry(project_id)
        total = len(registry)
        generated = sum(1 for r in registry if r.get("generated_code"))
        metrics["generationProgress"] = int((generated / total * 100)) if total > 0 else 0
        metrics["filesGenerated"] = generated
        
        # Current agent from logs
        logs = await db.get_execution_logs(project_id, log_type="migration", limit=1)
        if logs:
            last_log = logs[0]["message"]
            if "Agent C" in last_log:
                metrics["currentAgent"] = "Agent C"
            elif "Agent F" in last_log:
                metrics["currentAgent"] = "Agent F"
            elif "Agent G" in last_log:
                metrics["currentAgent"] = "Agent G"
        
        # Schema versions
        versions = await db.get_schema_versions(project_id)
        metrics["versionCount"] = len(versions)
        
        # Quality score
        validations = await db.get_code_validations(project_id)
        if validations:
            metrics["qualityScore"] = validations[-1].get("quality_score", 0)
    
    elif stage == 3:  # Refinement
        # Refinement status
        project = await db.get_project(project_id)
        metrics["refinementStatus"] = project.get("status", "REFINED")
        
        # Issue count from validations
        validations = await db.get_code_validations(project_id)
        metrics["issueCount"] = sum(
            len(v.get("issues", [])) for v in validations
        )
        
        # Quality improvement
        if len(validations) >= 2:
            old_score = validations[0].get("quality_score", 0)
            new_score = validations[-1].get("quality_score", 0)
            metrics["qualityDelta"] = new_score - old_score
    
    elif stage == 4:  # Governance
        # Documentation status
        project = await db.get_project(project_id)
        settings = project.get("settings", {})
        metrics["docsGenerated"] = settings.get("documentation_complete", False)
        metrics["bundleReady"] = settings.get("cop_bundle_ready", False)
    
    # Common metrics (all stages)
    project = await db.get_project(project_id)
    metrics["executionStatus"] = project.get("status")
    
    # Last activity from logs
    logs = await db.get_execution_logs(project_id, limit=1)
    if logs:
        metrics["lastActivity"] = logs[0]["created_at"]
    
    return metrics
```

---

## 📋 Original Detailed Sections (for reference)
```tsx
┌─────────────────────────┐
│ 🚦 Quick Assessment     │
│ ────────────────────    │
│ Score: 85/100 🟢        │
│ Status: VIABLE          │
│                         │
│ 📦 Assets: 12          │
│ 📊 Tables: 8           │
│ ⚠️ Issues: 3           │
└─────────────────────────┘
```

**Data Source:** `utm_projects.quick_assessment` (Fase A)

**Fields to show:**
- `final_score` → Badge color-coded
- `classification` → VIABLE/NEEDS_REVIEW/NOT_VIABLE
- Asset counts from `utm_objects`
- Table counts from `utm_table_impacts` (Fase C)
- Issue counts from validation

---

### 2. **Views Section** (Always Visible)
```tsx
GROUP: VIEWS
├─ 📈 Graph              [12 nodes]
├─ 📋 Grid               [12 assets]
├─ 🗄️ Schema             [8 tables]
└─ 🔗 Mapping            [45 columns]
```

**With Live Badges:**
- Graph → node count
- Grid → asset count
- Schema → table count
- Mapping → mapped column count

**Data Sources:**
- `nodes` state (Graph)
- `utm_objects` → count
- `schema_reference.json` → table count
- `utm_column_mappings` → count

---

### 3. **Analysis Section** (Collapsible)
```tsx
GROUP: ANALYSIS ▼
├─ 🌐 Origin             [5 source systems]
├─ ⚡ Transformations    [23 transforms]
├─ 📝 Source Queries     [18 queries]
├─ 🛡️ Quality Score     [AVG: 78%]
├─ 🔒 PII Detection     [4 sensitive fields]
└─ 📂 Partitions        [3 recommendations]
```

**With Smart Badges:**
- Origin → unique source systems count
- Transformations → transformation count
- Queries → extracted queries count
- Quality → average quality score
- PII → detected PII fields count
- Partitions → recommendation count

**Data Sources:** (Sprint 8.5 + 11)
- `utm_objects.metadata` → `source_systems`
- `utm_objects.transformations` (JSONB array)
- `utm_objects.source_query`
- `utm_asset_columns.quality_score` → AVG
- `utm_asset_columns.has_pii` → COUNT
- `utm_asset_columns` → partition recommendations

---

### 4. **Config Section** (Collapsible)
```tsx
GROUP: CONFIG ▼
├─ 💬 Business Context   [2 edited]
├─ 📜 Execution Logs     [Running...]
└─ 📁 File Explorer      [45 files]
```

**With Status Indicators:**
- Business Context → edited count badge
- Execution Logs → status indicator (spinning if running)
- File Explorer → file count

**Data Sources:**
- `utm_solution_context` → count where notes IS NOT NULL
- `utm_execution_logs` → latest status
- R2 file inventory

---

### 5. **Table Impact View** (NEW - Fase C)
```tsx
GROUP: TABLES (NEW) ▼
├─ 📊 Table Registry     [8 tables]
│   ├─ dbo.Customers    [2R/1W] ⚠️
│   ├─ dbo.Products     [1R/1W]
│   └─ dbo.Sales        [0R/1W]
└─ 🔍 Conflict Analysis
```

**Interactive List:**
- Click table → show detail panel
- Badge colors:
  - 🟢 Green: No conflicts
  - 🟡 Yellow: Multiple operations (need review)
  - 🔴 Red: Detected conflicts

**Data Source:** `utm_table_impacts` (Fase C)

```sql
SELECT 
  table_name,
  COUNT(*) FILTER (WHERE operation IN ('SELECT')) as read_count,
  COUNT(*) FILTER (WHERE operation IN ('INSERT','UPDATE','DELETE','MERGE')) as write_count,
  ARRAY_AGG(DISTINCT asset_name) as assets
FROM utm_table_impacts
WHERE project_id = ?
GROUP BY table_name
```

---

## 🎨 Visual Specifications

### Colors & Styles
```css
--sidebar-width: 250px;
--sidebar-bg: bg-gray-50 dark:bg-gray-900;
--sidebar-border: border-r border-gray-200 dark:border-gray-800;

--group-header-bg: bg-gray-100 dark:bg-gray-800;
--group-header-text: text-gray-700 dark:text-gray-300;

--item-hover: hover:bg-gray-100 dark:hover:bg-gray-800;
--item-active: bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500;

--badge-bg: bg-blue-100 dark:bg-blue-900;
--badge-text: text-blue-700 dark:text-blue-300;
```

### Typography
```css
Group Header: font-bold text-xs uppercase tracking-wide
Item Label:   font-medium text-sm
Badge:        font-mono text-xs
```

### Spacing
```css
Sidebar padding:      p-4
Group vertical gap:   space-y-6
Items vertical gap:   space-y-1
Item padding:         px-3 py-2
Badge margin:         ml-auto
```

---

## 📊 Component Structure

### Main Component: `<SidebarNavigation>`
```tsx
<SidebarNavigation
  projectId={projectId}
  activeSection={activeSection}
  onSectionChange={setActiveSection}
  quickAssessment={quickAssessment}
  assetCount={assets.length}
  tableImpacts={tableImpacts}
  columnMappings={columnMappings}
  executionStatus={executionStatus}
/>
```

### Sub-components:
1. `<QuickInfoPanel>` - Top collapsible summary
2. `<SidebarGroup>` - Collapsible group wrapper
3. `<SidebarItem>` - Individual nav item with badge
4. `<TableImpactList>` - NEW: Table registry viewer
5. `<StatusBadge>` - Color-coded badge component

---

## 🔄 State Management

### Context or Props?
**Recommendation:** Use Context API for sidebar state

```tsx
// apps/web/app/context/SidebarContext.tsx
interface SidebarContextType {
  activeSection: string;
  setActiveSection: (section: string) => void;
  isCollapsed: boolean;
  toggleCollapsed: () => void;
  metrics: {
    assetCount: number;
    tableCount: number;
    issueCount: number;
    // ... other counts
  };
}
```

### Persistence
- Store `activeSection` in localStorage
- Store `isCollapsed` in localStorage
- Restore on mount

---

## 📱 Responsive Behavior

### Desktop (> 1024px)
- Sidebar fixed at 250px
- Always visible
- Can collapse to icon-only (60px)

### Tablet (768px - 1024px)
- Sidebar overlay on demand
- Hamburger menu to toggle
- Backdrop blur when open

### Mobile (< 768px)
- Full-screen overlay
- Slide in from left
- Close button top-right

---

## 🚀 Implementation Plan

### Phase 1: Core Adaptive Structure (1.5 days)
- [ ] Create `<StageSidebar>` component with stage prop
- [ ] Create `sidebar-sections.ts` config file with all stages
- [ ] Implement `getSectionsForStage()` helper
- [ ] Create `<SidebarSection>` and `<SidebarItem>` components
- [ ] Add basic layout (sidebar + main area)
- [ ] Implement collapse/expand functionality
- [ ] Add stage switching logic

### Phase 2: Data Integration by Stage (1.5 days)
- [ ] Create `useSidebarMetrics()` hook with stage param
- [ ] Implement backend endpoint `/sidebar-metrics?stage=X`
- [ ] Connect metrics to badges for each stage
- [ ] Implement auto-refresh for running processes
- [ ] Add loading states for metrics

### Phase 3: Stage-Specific Components (2 days)
- [ ] **Stage 0:** Quick Assessment + File Upload panels
- [ ] **Stage 1:** Table Impact List component
- [ ] **Stage 2:** Process Progress integration
- [ ] **Stage 3:** Code comparison + Issues panel
- [ ] **Stage 4:** COP Bundle + Download UI

### Phase 4: Polish & Responsive (1 day)
- [ ] Add animations (slide, fade, collapse)
- [ ] Implement responsive behavior (mobile overlay)
- [ ] Add keyboard shortcuts (Cmd+B to toggle)
- [ ] Persist collapsed/expanded state per stage
- [ ] Test on all screen sizes
- [ ] Add accessibility (ARIA labels, keyboard nav)

**Total:** 6 days

---

## 🎯 Integration with Existing Views

### Update View Components

```tsx
// apps/web/app/components/stages/TriageView.tsx

export default function TriageView({ projectId, stage, ... }) {
  const [activeSection, setActiveSection] = useState('graph');
  
  return (
    <div className="flex h-full">
      {/* NEW: Stage-aware sidebar */}
      <StageSidebar
        stage={stage} // 1 for Triage
        projectId={projectId}
        tenantId={activeTenantId}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />
      
      {/* Existing content - now conditional on activeSection */}
      <main className="flex-1 overflow-auto">
        {activeSection === 'graph' && <GraphView />}
        {activeSection === 'grid' && <GridView />}
        {activeSection === 'schema' && <SchemaView />}
        {/* ... etc ... */}
      </main>
    </div>
  );
}
```

### Remove Old Tab Navigation

```tsx
// REMOVE: Old horizontal tabs
// const TABS = [...];
// <TabBar tabs={TABS} />

// REPLACE WITH: StageSidebar component (handles navigation)
```

---

## 📱 Responsive Behavior (Updated)
- [ ] Create `<SidebarNavigation>` component
- [ ] Create `<SidebarGroup>` and `<SidebarItem>` components
- [ ] Implement basic layout (sidebar + main area)
- [ ] Add collapse/expand functionality

### Phase 2: Data Integration (1 day)
- [ ] Connect to Quick Assessment data
- [ ] Add live badges for all sections
- [ ] Fetch metrics from database
- [ ] Implement auto-refresh for running processes

### Phase 3: Table Impact View (1 day)
- [ ] Create `<TableImpactList>` component
- [ ] Fetch from `utm_table_impacts`
- [ ] Implement conflict detection logic
- [ ] Add detail panel on click

### Phase 4: Polish & Responsive (1 day)
- [ ] Add animations (slide, fade)
- [ ] Implement responsive behavior
- [ ] Add keyboard shortcuts (Cmd+B to toggle)
- [ ] Test on all screen sizes

---

## 🎯 Success Metrics

### User Experience
- ✅ Navigation adapts intelligently to current stage
- ✅ Only relevant sections shown (no clutter)
- ✅ All information accessible in < 2 clicks per stage
- ✅ Key metrics visible without navigation
- ✅ Smooth transitions between stages
- ✅ Reduced time to find information by 60%+
- ✅ Zero horizontal scrolling

### Performance
- ✅ Sidebar renders in < 100ms
- ✅ Stage switching in < 50ms
- ✅ Metrics update in < 500ms
- ✅ Smooth animations (60fps)
- ✅ Optimized API calls (fetch only stage-relevant data)

### Accessibility
- ✅ Keyboard navigation works across all stages
- ✅ Screen reader compatible
- ✅ Focus indicators visible
- ✅ ARIA labels for all interactive elements

---

## 🔌 API Requirements

### New Endpoints Needed

#### 1. Get Sidebar Metrics
```typescript
GET /api/v1/projects/{projectId}/sidebar-metrics

Response:
{
  assetCount: 12,
  tableCount: 8,
  nodeCount: 12,
  mappingCount: 45,
  sourceSystemCount: 5,
  transformationCount: 23,
  queryCount: 18,
  avgQualityScore: 78.5,
  piiFieldCount: 4,
  partitionRecommendations: 3,
  contextEditCount: 2,
  fileCount: 45,
  executionStatus: "PROCESSING"
}
```

#### 2. Get Table Impacts Summary
```typescript
GET /api/v1/projects/{projectId}/table-impacts/summary

Response:
{
  tables: [
    {
      tableName: "dbo.Customers",
      readCount: 2,
      writeCount: 1,
      assets: ["LoadCustomers.dtsx", "UpdateCustomers.dtsx"],
      hasConflicts: true,
      conflictType: "MULTIPLE_WRITERS"
    }
  ]
}
```

---

## 💡 Future Enhancements (v4.1+)

### Smart Recommendations
```tsx
⚡ INSIGHTS
├─ "Table dbo.Customers has 3 writers - review recommended"
├─ "15 columns missing mappings"
└─ "Quality score improved +12% since last run"
```

### Search & Filter
```tsx
🔍 [Search sections and tables...]
```

### Favorites/Pinned
```tsx
⭐ PINNED
├─ dbo.Customers (frequent access)
└─ Quality Dashboard (monitoring)
```

### Activity Feed
```tsx
🕒 RECENT ACTIVITY
├─ 2 min ago - Triage completed
├─ 5 min ago - Schema updated
└─ 10 min ago - Mapping edited
```

---

## 📝 Implementation Notes

### TriageView Refactor
```tsx
// BEFORE (current)
return (
  <div>
    <TabBar tabs={TABS} />
    <MainContent />
  </div>
);

// AFTER (with sidebar)
return (
  <div className="flex h-full">
    <SidebarNavigation />
    <MainContent className="flex-1" />
  </div>
);
```

### Reusable Across All Stages
**Same component, different configurations:**
- **Stage 0 (DiscoveryView):** Quick Assessment + Upload (4 sections)
- **Stage 1 (TriageView):** Full analysis (13 sections + table registry)
- **Stage 2 (DraftingView):** Generation focus (7 sections)
- **Stage 3 (RefinementView):** Code review focus (8 sections)
- **Stage 4 (GovernanceView):** Documentation + handover (5 sections)

---

## ✅ Next Steps

1. **✅ Review & Approve** this spec (DONE)
2. **Create base components** in `apps/web/app/components/navigation/`:
   - `StageSidebar.tsx` (main component)
   - `SidebarSection.tsx` (collapsible group)
   - `SidebarItem.tsx` (individual nav item)
   - `SidebarHeader.tsx` (stage-specific header)
3. **Create config** in `apps/web/app/config/sidebar-sections.ts`
4. **Implement backend endpoint** `/sidebar-metrics?stage=X`
5. **Test stage by stage**:
   - Stage 0 first (simplest)
   - Stage 1 second (most complex - validate pattern)
   - Stages 2-4 (replicate pattern)
6. **Integrate with existing views** (remove old tabs)

---

## 📊 Summary Table

| Stage | Name | Sections | Complexity | Priority |
|-------|------|----------|------------|----------|
| 0 | Discovery | 4 | 🟢 Simple | High |
| 1 | Triage | 13+ | 🔴 Complex | High |
| 2 | Drafting | 7 | 🟡 Medium | Medium |
| 3 | Refinement | 8 | 🟡 Medium | Medium |
| 4 | Governance | 5 | 🟢 Simple | Low |

**Implementation Order:** 0 → 1 → 2 → 3 → 4

---

**Owner:** Frontend Team  
**Timeline:** 6 days (adaptive design adds complexity)  
**Dependencies:** 
- ✅ v4.0 Backend (Fases A, B, C) complete
- ✅ ProcessProgress component (already done today!)
- 🔄 Backend endpoint `/sidebar-metrics?stage=X` (needs implementation)

---

**Status:** 🟢 SPECIFICATION COMPLETE - READY FOR IMPLEMENTATION  
**Date:** February 16, 2026

---

## 🎬 Visual Example: Stage Transitions

### User Journey Visualization

```
USER CREATES PROJECT
        ↓
┌──────────────────┐
│ STAGE 0          │  🏠 Overview → Upload files
│ Discovery        │  📁 File Browser → See uploads
└──────────────────┘  ⚙️ Settings → Configure
        ↓ [Run Quick Assessment]
        ↓
┌──────────────────┐
│ STAGE 1          │  🚦 Quick Info → See score 85
│ Triage           │  📈 Graph → Drag & drop nodes
│                  │  📊 Tables → dbo.Customers [2R/1W]
│ (Most complex)   │  🔍 Analysis → 6 subsections
└──────────────────┘  💬 Context → Add tribal knowledge
        ↓ [Approve Design]
        ↓
┌──────────────────┐
│ STAGE 2          │  ⚙️ Progress → 60% complete
│ Drafting         │  📝 Logs → Agent C working...
│                  │  💻 Code → View generated
└──────────────────┘  📊 Quality → Score 78
        ↓ [Generation Complete]
        ↓
┌──────────────────┐
│ STAGE 3          │  🔄 Status → Refining...
│ Refinement       │  💻 Review → Side-by-side
│                  │  ⚠️ Issues → 12 to fix
└──────────────────┘  🛡️ Quality → +15% improvement
        ↓ [Refinement Complete]
        ↓
┌──────────────────┐
│ STAGE 4          │  ✅ Completion → All ready
│ Governance       │  📝 Docs → Generated
│                  │  📦 Bundle → Download COP
└──────────────────┘  📤 Deploy → Push to repo
```

**Key Insight:** Each stage shows ONLY what matters at that moment.  
No clutter, no overwhelm, perfect focus. 🎯

---

*"The best interface is the one that adapts to you, not the other way around."*
