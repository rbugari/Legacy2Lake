
export const AGENT_METADATA: Record<string, { label: string; description: string; status?: 'active' | 'planned' }> = {
    // ✅ ACTIVE AGENTS (v3.9 GA)
    "agent-s": { label: "Agent S (Scout)", description: "Forensic analysis of file inventories to detect source platform", status: 'active' },
    "agent-a": { label: "Agent A (Architect)", description: "Analyzes legacy code manifests and builds knowledge base", status: 'active' },
    "agent-c": { label: "Agent C (Coder)", description: "Transpiles legacy logic into modern target patterns", status: 'active' },
    "agent-f": { label: "Agent F (Critic)", description: "Reviews code for optimization and compliance violations", status: 'active' },
    "agent-g": { label: "Agent G (Governance)", description: "Enforces security policies and naming conventions", status: 'active' },
    "agent-d": { label: "Agent D (Deliverer)", description: "Reviews modernized code and certifies cloud architecture compliance", status: 'active' },
    
    // 📅 PLANNED AGENTS (Future releases)
    "agent-b": { label: "Agent B (Cartographer) [PLANNED]", description: "Translates legacy control flow into modern lineage mesh", status: 'planned' },
    "agent-p": { label: "Agent P (Profiler) [PLANNED]", description: "Analyzes codebase patterns and data dependencies", status: 'planned' },
    "agent-r": { label: "Agent R (Refactoring) [PLANNED]", description: "Optimizes Spark code for performance and scalability", status: 'planned' },
    "agent-o": { label: "Agent O (OpsAuditor) [PLANNED]", description: "Validates operational readiness and generates DevOps manifests", status: 'planned' }
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
