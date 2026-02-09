
export const AGENT_METADATA: Record<string, { label: string; description: string }> = {
    "agent-s": { label: "Agent S (Scout)", description: "Forensic analysis of file inventories to detect source platform" },
    "agent-a": { label: "Agent A (Detective)", description: "Analyzes legacy code manifests and builds knowledge base" },
    "agent-b": { label: "Agent B (Cartographer)", description: "Translates legacy control flow into modern lineage mesh" },
    "agent-c": { label: "Agent C (Interpreter)", description: "Transpiles legacy logic into modern target patterns" },
    "agent-d": { label: "Agent D (Auditor)", description: "Reviews modernized code and certifies cloud architecture compliance" },
    "agent-f": { label: "Agent F (Critic)", description: "Reviews code for optimization and compliance violations" },
    "agent-g": { label: "Agent G (Governor)", description: "Enforces security policies and naming conventions" },
    "agent-p": { label: "Agent P (Profiler)", description: "Analyzes codebase patterns and data dependencies" },
    "agent-r": { label: "Agent R (Refactoring)", description: "Optimizes Spark code for performance and scalability" },
    "agent-o": { label: "Agent O (OpsAuditor)", description: "Validates operational readiness and generates DevOps manifests" }
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
