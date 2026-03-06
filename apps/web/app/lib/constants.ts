
export const AGENT_METADATA: Record<string, { label: string; description: string; status?: 'active' | 'planned' | 'deterministic' }> = {
    // ✅ LLM AGENTS (use model configured by tenant in Agent Matrix)
    "agent-s":  { label: "Agent S (Scout)",       description: "Forensic analysis of file inventories to detect source platform", status: 'active' },
    "agent-qa": { label: "Agent QA (Assessor)",   description: "Fast hybrid evaluation of project viability before Triage", status: 'active' },
    "agent-a":  { label: "Agent A (Detective)",   description: "Analyzes legacy code manifests and builds knowledge base", status: 'active' },
    "agent-c":  { label: "Agent C (Developer)",   description: "Transpiles legacy logic into modern target patterns", status: 'active' },
    "agent-f":  { label: "Agent F (Critic)",      description: "Reviews code for optimization and compliance violations", status: 'active' },
    "agent-g":  { label: "Agent G (Governor)",    description: "Enforces security policies and naming conventions", status: 'active' },
    "agent-d":  { label: "Agent D (Auditor)",     description: "Reviews modernized code and certifies cloud architecture compliance", status: 'active' },

    // ⚙️ DETERMINISTIC AGENTS (no LLM — rule-based engines active in Refinement)
    "agent-p":  { label: "Agent P (Profiler)",    description: "Analyzes codebase patterns and data dependencies", status: 'deterministic' },
    "agent-r":  { label: "Agent R (Refactoring)", description: "Optimizes Spark code for performance and scalability", status: 'deterministic' },
    "agent-o":  { label: "Agent O (OpsAuditor)",  description: "Validates operational readiness and generates DevOps manifests", status: 'deterministic' },
};

export const getAgentDisplayName = (id: string) => {
    const meta = AGENT_METADATA[id.toLowerCase()];
    if (meta) {
        return `${meta.label}`;
    }
    return id;
};

export const getAgentDescription = (id: string) => {
    return AGENT_METADATA[id.toLowerCase()]?.description || "";
};

export const getAgentFullLabel = (id: string) => {
    const meta = AGENT_METADATA[id.toLowerCase()];
    if (meta) {
        return `${meta.label} - ${meta.description}`;
    }
    return id;
};
