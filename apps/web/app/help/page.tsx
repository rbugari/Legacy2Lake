"use client";

import { HelpCircle, Book, Terminal, Shield, Workflow, MessageSquare, ChevronRight, Cpu, Brain, Zap, Target, ArrowLeft, FileText, GitBranch, Database, Lock, CheckCircle, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

type Section =
    | "home"
    | "introduction"
    | "installation"
    | "compiler-flow"
    | "discovery"
    | "triage"
    | "cartridge-manual"
    | "knowledge-injection"
    | "auth-rls"
    | "certification";

export default function HelpPage() {
    const [activeSection, setActiveSection] = useState<Section>("home");

    const modelRecommendations = [
        {
            tier: "High Reasoning & Context",
            icon: <Brain className="w-5 h-5" />,
            color: "purple",
            description: "Complex reasoning, multi-step analysis, and deep context understanding required.",
            agents: [
                { name: "Discovery Agent (Triage)", reason: "Analyzes entire codebase, detects patterns, makes strategic decisions" },
                { name: "Agent D (Drafting)", reason: "Generates production-ready code with complex transformations" },
                { name: "Agent E (Refinement)", reason: "Deep code review, optimization, and quality assurance" },
            ],
            models: ["Claude 4.6", "GPT-5.3", "Gemini 3.1"]
        },
        {
            tier: "Medium Reasoning & Context",
            icon: <Target className="w-5 h-5" />,
            color: "cyan",
            description: "Moderate complexity tasks requiring good understanding but less intensive reasoning.",
            agents: [
                { name: "Agent B (Cartridge)", reason: "Applies technology-specific patterns and rules" },
                { name: "Code Generator (Compliance)", reason: "Validates against certification rules and standards" },
            ],
            models: ["Claude 4.0 Haiku", "GPT-4.5 Mini", "Gemini 2.0 Flash"]
        },
        {
            tier: "Low Reasoning & Context",
            icon: <Zap className="w-5 h-5" />,
            color: "emerald",
            description: "Simple, focused tasks with minimal context requirements.",
            agents: [
                { name: "Compliance Auditor (Logging)", reason: "Structured log generation and formatting" },
                { name: "Helper Agent", reason: "Quick responses and simple assistance tasks" },
            ],
            models: ["Claude 3.5 Haiku", "GPT-4.0 Turbo", "Gemini Flash 8B"]
        }
    ];

    const getTierColors = (color: string) => {
        const colors: Record<string, { bg: string; border: string; text: string; iconBg: string }> = {
            purple: { bg: "bg-purple-500/5", border: "border-purple-500/20", text: "text-purple-400", iconBg: "bg-purple-500/10" },
            cyan: { bg: "bg-cyan-500/5", border: "border-cyan-500/20", text: "text-cyan-400", iconBg: "bg-cyan-500/10" },
            emerald: { bg: "bg-emerald-500/5", border: "border-emerald-500/20", text: "text-emerald-400", iconBg: "bg-emerald-500/10" }
        };
        return colors[color];
    };

    const renderContent = () => {
        switch (activeSection) {
            case "introduction":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Introduction to Legacy2Lake</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            Legacy2Lake is an AI-powered data modernization factory that automates the migration of legacy ETL/ELT workloads
                            to modern cloud-native platforms like Snowflake, Databricks, and Microsoft Fabric.
                        </p>

                        <div className="p-6 bg-cyan-500/5 border border-cyan-500/20 rounded-xl">
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <CheckCircle className="w-5 h-5 text-cyan-500" />
                                Key Features
                            </h3>
                            <ul className="space-y-2 text-[var(--text-secondary)]">
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-cyan-500 mt-1 flex-shrink-0" />
                                    <span><strong>6-Stage Compiler Flow:</strong> Discovery, Triage, Drafting, Refinement, Certification, and Deployment</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-cyan-500 mt-1 flex-shrink-0" />
                                    <span><strong>Multi-Agent Architecture:</strong> Specialized AI agents for each stage of migration</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-cyan-500 mt-1 flex-shrink-0" />
                                    <span><strong>Technology Cartridges:</strong> Platform-specific knowledge injection for optimal code generation</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-cyan-500 mt-1 flex-shrink-0" />
                                    <span><strong>Zero-Trust Multi-Tenancy:</strong> Enterprise-grade security with RLS and tenant isolation</span>
                                </li>
                            </ul>
                        </div>

                        <h3 className="text-2xl font-bold mt-8">Supported Technologies</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                                <h4 className="font-bold text-cyan-500 mb-2">Source Platforms</h4>
                                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                    <li>• SSIS (SQL Server Integration Services)</li>
                                    <li>• Informatica PowerCenter</li>
                                    <li>• IBM DataStage</li>
                                    <li>• Oracle PL/SQL</li>
                                    <li>• T-SQL Stored Procedures</li>
                                </ul>
                            </div>
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                                <h4 className="font-bold text-emerald-500 mb-2">Target Platforms</h4>
                                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                    <li>• Snowflake (SQL + Snowpark Python)</li>
                                    <li>• Databricks (PySpark)</li>
                                    <li>• Microsoft Fabric</li>
                                    <li>• Google BigQuery</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                );

            case "installation":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Installation Guide</h2>

                        <div className="p-6 bg-amber-500/5 border border-amber-500/20 rounded-xl">
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <AlertTriangle className="w-5 h-5 text-amber-500" />
                                Prerequisites
                            </h3>
                            <ul className="space-y-2 text-[var(--text-secondary)]">
                                <li>• Node.js 18+ and npm/yarn</li>
                                <li>• PostgreSQL 14+ (Supabase recommended)</li>
                                <li>• Python 3.9+ (for backend services)</li>
                                <li>• API keys for at least one LLM provider (OpenAI, Anthropic, or Google)</li>
                            </ul>
                        </div>

                        <h3 className="text-2xl font-bold">Step 1: Clone Repository</h3>
                        <div className="p-4 bg-black/40 rounded-xl border border-white/10 font-mono text-sm">
                            <code className="text-cyan-400">git clone https://github.com/rbugari/iflow.git</code><br />
                            <code className="text-cyan-400">cd iflow</code>
                        </div>

                        <h3 className="text-2xl font-bold">Step 2: Install Dependencies</h3>
                        <div className="p-4 bg-black/40 rounded-xl border border-white/10 font-mono text-sm">
                            <code className="text-emerald-400"># Frontend</code><br />
                            <code className="text-cyan-400">cd apps/web && npm install</code><br /><br />
                            <code className="text-emerald-400"># Backend</code><br />
                            <code className="text-cyan-400">cd ../../backend && pip install -r requirements.txt</code>
                        </div>

                        <h3 className="text-2xl font-bold">Step 3: Configure Environment</h3>
                        <p className="text-[var(--text-secondary)]">Create a <code className="bg-white/10 px-2 py-1 rounded text-cyan-400">.env</code> file with your credentials:</p>
                        <div className="p-4 bg-black/40 rounded-xl border border-white/10 font-mono text-sm">
                            <code className="text-gray-400"># Supabase</code><br />
                            <code className="text-cyan-400">NEXT_PUBLIC_SUPABASE_URL=your_supabase_url</code><br />
                            <code className="text-cyan-400">NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key</code><br /><br />
                            <code className="text-gray-400"># LLM Providers</code><br />
                            <code className="text-cyan-400">OPENAI_API_KEY=your_openai_key</code><br />
                            <code className="text-cyan-400">ANTHROPIC_API_KEY=your_anthropic_key</code>
                        </div>

                        <h3 className="text-2xl font-bold">Step 4: Run Database Migrations</h3>
                        <div className="p-4 bg-black/40 rounded-xl border border-white/10 font-mono text-sm">
                            <code className="text-cyan-400">npm run db:migrate</code>
                        </div>

                        <h3 className="text-2xl font-bold">Step 5: Start Services</h3>
                        <div className="p-4 bg-black/40 rounded-xl border border-white/10 font-mono text-sm">
                            <code className="text-emerald-400"># Frontend (port 3000)</code><br />
                            <code className="text-cyan-400">npm run dev</code><br /><br />
                            <code className="text-emerald-400"># Backend (port 8000)</code><br />
                            <code className="text-cyan-400">cd backend && python main.py</code>
                        </div>

                        <div className="p-6 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <CheckCircle className="w-5 h-5 text-emerald-500" />
                                You're Ready!
                            </h3>
                            <p className="text-[var(--text-secondary)]">
                                Access the application at <code className="bg-white/10 px-2 py-1 rounded text-cyan-400">http://localhost:3000</code>
                            </p>
                        </div>
                    </div>
                );

            case "compiler-flow":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">6-Stage Compiler Flow</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            Legacy2Lake uses a sophisticated multi-stage pipeline to transform legacy code into modern, cloud-native solutions.
                        </p>

                        <div className="space-y-4">
                            {[
                                {
                                    stage: "1. Discovery",
                                    icon: <Database className="w-5 h-5" />,
                                    color: "cyan",
                                    description: "Scans and catalogs all source code files, extracting metadata and dependencies.",
                                    tasks: ["File system traversal", "Metadata extraction", "Dependency mapping"]
                                },
                                {
                                    stage: "2. Triage (Discovery Agent)",
                                    icon: <GitBranch className="w-5 h-5" />,
                                    color: "purple",
                                    description: "AI analyzes code complexity, identifies patterns, and creates migration strategy.",
                                    tasks: ["Complexity analysis", "Pattern detection", "Migration planning"]
                                },
                                {
                                    stage: "3. Drafting (Agent D)",
                                    icon: <FileText className="w-5 h-5" />,
                                    color: "emerald",
                                    description: "Generates initial target platform code with cartridge-specific optimizations.",
                                    tasks: ["Code generation", "Cartridge injection", "Syntax transformation"]
                                },
                                {
                                    stage: "4. Refinement (Agent E)",
                                    icon: <Brain className="w-5 h-5" />,
                                    color: "amber",
                                    description: "Reviews and optimizes generated code for performance and best practices.",
                                    tasks: ["Code review", "Performance optimization", "Best practices validation"]
                                },
                                {
                                    stage: "5. Certification (Compliance Auditor)",
                                    icon: <Shield className="w-5 h-5" />,
                                    color: "blue",
                                    description: "Validates code against compliance rules and certification standards.",
                                    tasks: ["Compliance validation", "Security checks", "Quality scoring"]
                                },
                                {
                                    stage: "6. Deployment",
                                    icon: <CheckCircle className="w-5 h-5" />,
                                    color: "green",
                                    description: "Packages and prepares code for deployment to target platform.",
                                    tasks: ["Artifact packaging", "Deployment scripts", "Documentation generation"]
                                }
                            ].map((stage, idx) => (
                                <div key={idx} className={`p-5 bg-${stage.color}-500/5 border border-${stage.color}-500/20 rounded-xl`}>
                                    <div className="flex items-start gap-4">
                                        <div className={`p-3 bg-${stage.color}-500/10 rounded-xl text-${stage.color}-500 flex-shrink-0`}>
                                            {stage.icon}
                                        </div>
                                        <div className="flex-1">
                                            <h3 className={`text-lg font-bold text-${stage.color}-400 mb-2`}>{stage.stage}</h3>
                                            <p className="text-[var(--text-secondary)] text-sm mb-3">{stage.description}</p>
                                            <div className="flex flex-wrap gap-2">
                                                {stage.tasks.map((task, tIdx) => (
                                                    <span key={tIdx} className="px-3 py-1 bg-[var(--surface)] border border-[var(--border)] rounded-full text-xs">
                                                        {task}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                );

            case "discovery":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Discovery Stage</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            The Discovery stage is the foundation of the migration process. It automatically scans your source code repository
                            and builds a comprehensive inventory of all assets.
                        </p>

                        <h3 className="text-2xl font-bold">What Gets Discovered?</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                                <h4 className="font-bold text-cyan-500 mb-3">File Types</h4>
                                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                    <li>• SQL scripts (.sql)</li>
                                    <li>• SSIS packages (.dtsx)</li>
                                    <li>• Stored procedures</li>
                                    <li>• ETL workflows</li>
                                    <li>• Configuration files</li>
                                </ul>
                            </div>
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                                <h4 className="font-bold text-emerald-500 mb-3">Metadata Extracted</h4>
                                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                    <li>• File size and line count</li>
                                    <li>• Dependencies and references</li>
                                    <li>• Database connections</li>
                                    <li>• Table and column usage</li>
                                    <li>• Complexity metrics</li>
                                </ul>
                            </div>
                        </div>

                        <h3 className="text-2xl font-bold">How to Run Discovery</h3>
                        <ol className="space-y-3 text-[var(--text-secondary)]">
                            <li className="flex items-start gap-3">
                                <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">1</span>
                                <span>Navigate to <strong>Dashboard</strong> and click <strong>New Solution</strong></span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">2</span>
                                <span>Upload your source code files or connect to a repository</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">3</span>
                                <span>Configure source and target technologies</span>
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">4</span>
                                <span>Click <strong>Start Discovery</strong> and monitor progress in real-time</span>
                            </li>
                        </ol>
                    </div>
                );

            case "triage":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Triage Process (Discovery Agent)</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            Discovery Agent performs intelligent analysis of your codebase to determine migration complexity and create an optimal strategy.
                        </p>

                        <div className="p-6 bg-purple-500/5 border border-purple-500/20 rounded-xl">
                            <h3 className="text-xl font-bold mb-3 text-purple-400">Discovery Agent Capabilities</h3>
                            <ul className="space-y-2 text-[var(--text-secondary)]">
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>Pattern Recognition:</strong> Identifies common ETL patterns and anti-patterns</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>Complexity Scoring:</strong> Assigns difficulty ratings (Low/Medium/High)</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>Dependency Analysis:</strong> Maps relationships between components</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>Migration Strategy:</strong> Recommends optimal conversion approach</span>
                                </li>
                            </ul>
                        </div>

                        <h3 className="text-2xl font-bold">Triage Output</h3>
                        <p className="text-[var(--text-secondary)]">
                            After triage completes, you'll receive a detailed manifest for each asset including:
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl text-center">
                                <div className="text-3xl font-bold text-cyan-500 mb-2">Complexity</div>
                                <p className="text-xs text-[var(--text-secondary)]">Low / Medium / High</p>
                            </div>
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl text-center">
                                <div className="text-3xl font-bold text-emerald-500 mb-2">Strategy</div>
                                <p className="text-xs text-[var(--text-secondary)]">Recommended approach</p>
                            </div>
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl text-center">
                                <div className="text-3xl font-bold text-amber-500 mb-2">Risks</div>
                                <p className="text-xs text-[var(--text-secondary)]">Potential issues identified</p>
                            </div>
                        </div>
                    </div>
                );

            case "cartridge-manual":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Technology Cartridges</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            Cartridges are platform-specific knowledge modules that inject best practices, patterns, and optimizations
                            into the code generation process.
                        </p>

                        <h3 className="text-2xl font-bold">Available Cartridges</h3>
                        <div className="space-y-4">
                            {[
                                {
                                    name: "Snowflake Cartridge",
                                    icon: "❄️",
                                    description: "Optimizes for Snowflake's unique architecture including clustering, materialized views, and Snowpark patterns.",
                                    features: ["Warehouse sizing", "Clustering keys", "Snowpark Python", "Time Travel optimization"]
                                },
                                {
                                    name: "Databricks Cartridge",
                                    icon: "🧱",
                                    description: "Leverages Delta Lake, Unity Catalog, and PySpark best practices for optimal performance.",
                                    features: ["Delta Lake patterns", "Unity Catalog", "Auto Loader", "Photon optimization"]
                                },
                                {
                                    name: "Fabric Cartridge",
                                    icon: "🏭",
                                    description: "Integrates with Microsoft Fabric ecosystem including OneLake, Lakehouses, and Power BI.",
                                    features: ["OneLake integration", "Lakehouse patterns", "Dataflow Gen2", "Direct Lake mode"]
                                }
                            ].map((cartridge, idx) => (
                                <div key={idx} className="p-5 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                                    <div className="flex items-start gap-4">
                                        <div className="text-4xl">{cartridge.icon}</div>
                                        <div className="flex-1">
                                            <h4 className="text-lg font-bold text-cyan-400 mb-2">{cartridge.name}</h4>
                                            <p className="text-[var(--text-secondary)] text-sm mb-3">{cartridge.description}</p>
                                            <div className="flex flex-wrap gap-2">
                                                {cartridge.features.map((feature, fIdx) => (
                                                    <span key={fIdx} className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-xs text-cyan-400">
                                                        {feature}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                );

            case "knowledge-injection":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Knowledge Injection</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            Knowledge injection is the process of enriching AI agent prompts with platform-specific expertise,
                            ensuring generated code follows best practices and leverages target platform capabilities.
                        </p>

                        <div className="p-6 bg-cyan-500/5 border border-cyan-500/20 rounded-xl">
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <Brain className="w-5 h-5 text-cyan-500" />
                                How It Works
                            </h3>
                            <ol className="space-y-3 text-[var(--text-secondary)]">
                                <li className="flex items-start gap-3">
                                    <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">1</span>
                                    <span><strong>Selection:</strong> System identifies source and target technologies</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">2</span>
                                    <span><strong>Retrieval:</strong> Fetches relevant knowledge rules from database</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">3</span>
                                    <span><strong>Injection:</strong> Merges knowledge into agent system prompts</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">4</span>
                                    <span><strong>Execution:</strong> Agent generates code with enriched context</span>
                                </li>
                            </ol>
                        </div>

                        <h3 className="text-2xl font-bold">Managing Knowledge Rules</h3>
                        <p className="text-[var(--text-secondary)]">
                            Administrators can view and manage knowledge rules in the <Link href="/settings" className="text-cyan-400 hover:underline font-semibold">Strategic Intelligence Hub</Link>.
                        </p>
                    </div>
                );

            case "auth-rls":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Authentication & Row-Level Security</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            Legacy2Lake implements enterprise-grade security with zero-trust multi-tenancy powered by Supabase RLS.
                        </p>

                        <div className="p-6 bg-purple-500/5 border border-purple-500/20 rounded-xl">
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <Lock className="w-5 h-5 text-purple-500" />
                                Security Architecture
                            </h3>
                            <ul className="space-y-2 text-[var(--text-secondary)]">
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>JWT-Based Auth:</strong> Secure token-based authentication via Supabase</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>Row-Level Security:</strong> Database-level isolation ensures users only see their data</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>Role-Based Access:</strong> ADMIN and CLIENT roles with different permissions</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <ChevronRight className="w-4 h-4 text-purple-500 mt-1 flex-shrink-0" />
                                    <span><strong>Tenant Isolation:</strong> Complete data separation between organizations</span>
                                </li>
                            </ul>
                        </div>

                        <h3 className="text-2xl font-bold">User Roles</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                                <h4 className="font-bold text-cyan-500 mb-3 flex items-center gap-2">
                                    <Shield className="w-4 h-4" />
                                    ADMIN
                                </h4>
                                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                    <li>• Platform administration</li>
                                    <li>• User management</li>
                                    <li>• Model configuration</li>
                                    <li>• Knowledge rule editing</li>
                                    <li>• System monitoring</li>
                                </ul>
                            </div>
                            <div className="p-4 bg-[var(--surface-light)] border border-[var(--border)] rounded-xl">
                                <h4 className="font-bold text-emerald-500 mb-3">CLIENT</h4>
                                <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                    <li>• Create solutions</li>
                                    <li>• Run migrations</li>
                                    <li>• View own projects</li>
                                    <li>• Download artifacts</li>
                                    <li>• Profile management</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                );

            case "certification":
                return (
                    <div className="space-y-6">
                        <h2 className="text-3xl font-bold">Certification & Compliance</h2>
                        <p className="text-[var(--text-secondary)] leading-relaxed">
                            Compliance Auditor validates all generated code against a comprehensive set of certification rules to ensure
                            quality, security, and compliance with industry standards.
                        </p>

                        <div className="p-6 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                            <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
                                <CheckCircle className="w-5 h-5 text-emerald-500" />
                                Certification Categories
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                <div>
                                    <h4 className="font-bold text-cyan-400 mb-2">Code Quality</h4>
                                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                        <li>• Syntax validation</li>
                                        <li>• Best practices adherence</li>
                                        <li>• Code complexity limits</li>
                                        <li>• Documentation completeness</li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="font-bold text-purple-400 mb-2">Security</h4>
                                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                        <li>• SQL injection prevention</li>
                                        <li>• Credential management</li>
                                        <li>• Access control validation</li>
                                        <li>• Data encryption checks</li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="font-bold text-amber-400 mb-2">Performance</h4>
                                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                        <li>• Query optimization</li>
                                        <li>• Resource usage limits</li>
                                        <li>• Indexing strategies</li>
                                        <li>• Caching patterns</li>
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="font-bold text-emerald-400 mb-2">Compliance</h4>
                                    <ul className="text-sm text-[var(--text-secondary)] space-y-1">
                                        <li>• GDPR requirements</li>
                                        <li>• Data retention policies</li>
                                        <li>• Audit trail generation</li>
                                        <li>• Regulatory standards</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <h3 className="text-2xl font-bold">Certification Scores</h3>
                        <p className="text-[var(--text-secondary)]">
                            Each migrated asset receives a certification score (0-100) based on rule compliance:
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-center">
                                <div className="text-3xl font-bold text-emerald-500 mb-2">90-100</div>
                                <p className="text-xs text-emerald-400 font-bold">EXCELLENT</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-1">Production ready</p>
                            </div>
                            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-center">
                                <div className="text-3xl font-bold text-amber-500 mb-2">70-89</div>
                                <p className="text-xs text-amber-400 font-bold">GOOD</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-1">Minor improvements needed</p>
                            </div>
                            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-center">
                                <div className="text-3xl font-bold text-red-500 mb-2">&lt;70</div>
                                <p className="text-xs text-red-400 font-bold">NEEDS WORK</p>
                                <p className="text-xs text-[var(--text-secondary)] mt-1">Requires refinement</p>
                            </div>
                        </div>
                    </div>
                );

            default:
                return (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {[
                                {
                                    title: "Getting Started",
                                    icon: <Book className="w-6 h-6 text-cyan-500" />,
                                    description: "Learn the basics of Legacy2Lake and how to set up your first project.",
                                    links: [
                                        { label: "Introduction", section: "introduction" as Section },
                                        { label: "Installation Guide", section: "installation" as Section },
                                    ]
                                },
                                {
                                    title: "Core Concepts",
                                    icon: <Workflow className="w-6 h-6 text-emerald-500" />,
                                    description: "Understanding the 6-stage compiler flow and agent architecture.",
                                    links: [
                                        { label: "Compiler Flow", section: "compiler-flow" as Section },
                                        { label: "Discovery Stage", section: "discovery" as Section },
                                        { label: "Triage Process", section: "triage" as Section },
                                    ]
                                },
                                {
                                    title: "Technology Cartridges",
                                    icon: <Terminal className="w-6 h-6 text-amber-500" />,
                                    description: "Detailed documentation for Snowflake, Databricks, and Fabric cartridges.",
                                    links: [
                                        { label: "Cartridge Manual", section: "cartridge-manual" as Section },
                                        { label: "Knowledge Injection", section: "knowledge-injection" as Section },
                                    ]
                                },
                                {
                                    title: "Security & Compliance",
                                    icon: <Shield className="w-6 h-6 text-purple-500" />,
                                    description: "How we ensure zero-trust multi-tenancy and compliance scoring.",
                                    links: [
                                        { label: "Auth & RLS", section: "auth-rls" as Section },
                                        { label: "Certification Rules", section: "certification" as Section },
                                    ]
                                }
                            ].map((section, idx) => (
                                <div
                                    key={idx}
                                    className="p-6 bg-[var(--surface-light)] border border-[var(--border)] rounded-2xl hover:border-cyan-500/50 transition-all group"
                                >
                                    <div className="flex items-center gap-4 mb-4">
                                        <div className="p-2 bg-[var(--surface)] rounded-xl border border-[var(--border)] group-hover:scale-110 transition-transform">
                                            {section.icon}
                                        </div>
                                        <h2 className="text-xl font-semibold">{section.title}</h2>
                                    </div>
                                    <p className="text-[var(--text-secondary)] mb-6 text-sm leading-relaxed">
                                        {section.description}
                                    </p>
                                    <div className="space-y-2">
                                        {section.links.map((link, lIdx) => (
                                            <button
                                                key={lIdx}
                                                onClick={() => setActiveSection(link.section)}
                                                className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-[var(--text-primary)]/5 text-sm transition-colors text-left"
                                            >
                                                <span className="text-[var(--text-primary)] transition-colors">{link.label}</span>
                                                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-50 group-hover:translate-x-1 transition-all" />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Model Assignment Recommendations */}
                        <div className="space-y-6 mt-12">
                            <div className="flex items-center gap-3">
                                <div className="p-3 bg-amber-500/10 rounded-2xl">
                                    <Cpu className="w-7 h-7 text-amber-500" />
                                </div>
                                <div>
                                    <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">Model Assignment Guide</h2>
                                    <p className="text-sm text-[var(--text-secondary)] mt-1">Optimize performance by matching model capabilities to agent requirements</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {modelRecommendations.map((tier, idx) => {
                                    const colors = getTierColors(tier.color);
                                    return (
                                        <div
                                            key={idx}
                                            className={`p-6 ${colors.bg} border ${colors.border} rounded-2xl transition-all hover:shadow-lg`}
                                        >
                                            <div className="flex items-start gap-4 mb-4">
                                                <div className={`p-2 ${colors.iconBg} rounded-xl ${colors.text}`}>
                                                    {tier.icon}
                                                </div>
                                                <div className="flex-1">
                                                    <h3 className={`text-lg font-bold ${colors.text} mb-1`}>{tier.tier}</h3>
                                                    <p className="text-sm text-[var(--text-secondary)]">{tier.description}</p>
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                                                <div className="space-y-2">
                                                    <h4 className="text-xs font-black uppercase tracking-widest text-[var(--text-secondary)] opacity-60">Recommended Agents</h4>
                                                    {tier.agents.map((agent, aIdx) => (
                                                        <div key={aIdx} className="p-3 bg-[var(--surface)] rounded-xl border border-[var(--border)]">
                                                            <div className="flex items-start gap-2">
                                                                <div className={`w-1.5 h-1.5 rounded-full ${colors.text.replace('text-', 'bg-')} mt-1.5 flex-shrink-0`}></div>
                                                                <div>
                                                                    <p className="text-sm font-bold text-[var(--text-primary)]">{agent.name}</p>
                                                                    <p className="text-xs text-[var(--text-secondary)] mt-0.5">{agent.reason}</p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>

                                                <div className="space-y-2">
                                                    <h4 className="text-xs font-black uppercase tracking-widest text-[var(--text-secondary)] opacity-60">Suggested Models</h4>
                                                    <div className="p-4 bg-[var(--surface)] rounded-xl border border-[var(--border)]">
                                                        <div className="space-y-2">
                                                            {tier.models.map((model, mIdx) => (
                                                                <div key={mIdx} className="flex items-center gap-2">
                                                                    <ChevronRight className={`w-3 h-3 ${colors.text}`} />
                                                                    <span className="text-sm font-medium text-[var(--text-primary)]">{model}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className={`p-3 ${colors.iconBg} rounded-xl border ${colors.border}`}>
                                                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                                                    <span className="font-bold text-[var(--text-primary)]">💡 Pro Tip:</span> You can configure model assignments in the{" "}
                                                    <Link href="/settings" className={`${colors.text} hover:underline font-semibold`}>
                                                        Strategic Intelligence Hub
                                                    </Link>
                                                    {" "}under Settings.
                                                </p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </>
                );
        }
    };

    return (
        <div className="max-w-6xl mx-auto p-8 space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="space-y-4">
                <div className="flex items-center gap-3">
                    {activeSection !== "home" && (
                        <button
                            onClick={() => setActiveSection("home")}
                            className="p-2 hover:bg-[var(--text-primary)]/5 rounded-xl transition-colors"
                        >
                            <ArrowLeft className="w-6 h-6 text-cyan-500" />
                        </button>
                    )}
                    <div className="p-3 bg-cyan-500/10 rounded-2xl">
                        <HelpCircle className="w-8 h-8 text-cyan-500" />
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight text-[var(--text-primary)]">Help Center</h1>
                </div>
                <p className="text-xl text-[var(--text-secondary)] max-w-2xl">
                    Complete guide to the Legacy2Lake Data Modernization Factory. Find documentation, tutorials, and technical specifications.
                </p>
            </div>

            {renderContent()}

            {activeSection === "home" && (
                <div className="p-8 bg-cyan-500/5 rounded-3xl border border-cyan-500/10 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-cyan-500 rounded-full flex items-center justify-center">
                            <MessageSquare className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold">Need more assistance?</h3>
                            <p className="text-sm text-[var(--text-secondary)]">Our support team is ready to help you with your migration.</p>
                        </div>
                    </div>
                    <button className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold rounded-xl transition-all hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]">
                        Contact Support
                    </button>
                </div>
            )}
        </div>
    );
}
