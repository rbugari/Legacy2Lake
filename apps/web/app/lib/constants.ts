
export const AGENT_METADATA: Record<string, { label: string; description: string }> = {
    "agent-s": { label: "Agent S", description: "[Phase 1] Scout & Triage" },
    "agent-a": { label: "Agent A", description: "[Phase 1] Discovery Detective" },
    "agent-c": { label: "Agent C", description: "[Phase 2] Migration Architect" },
    "agent-f": { label: "Agent F", description: "[Phase 2] Compliance Critic" },
    "agent-g": { label: "Agent G", description: "[Global] Governance & Security" },
    "agent-b": { label: "Agent B", description: "[Phase 3] Base Refinement" },
    "agent-p": { label: "Agent P", description: "[Phase 4] Pattern Profiler" },
    "agent-r": { label: "Agent R", description: "[Phase 4] Spark Refactoring" },
    "agent-o": { label: "Agent O", description: "[Phase 4] DevOps Auditor" }
};

export const getAgentDisplayName = (id: string) => {
    const meta = AGENT_METADATA[id.toLowerCase()];
    if (meta) {
        return `${meta.label} (${meta.description})`;
    }
    return id;
};

export const getAgentDescription = (id: string) => {
    return AGENT_METADATA[id.toLowerCase()]?.description || "";
};
