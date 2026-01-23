"use client";
import { useState, useEffect } from "react";
import { Terminal } from "lucide-react";
import { API_BASE_URL } from "../lib/config";

interface PromptsExplorerProps {
    className?: string;
}

export default function PromptsExplorer({ className }: PromptsExplorerProps) {
    const [prompts, setPrompts] = useState<{ [key: string]: string }>({});
    const [loading, setLoading] = useState(true);
    const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

    useEffect(() => {
        const fetchPrompts = async () => {
            try {
                const [a, c, f, g] = await Promise.all([
                    fetch(`${API_BASE_URL}/prompts/agent-a`).then(r => r.json()),
                    fetch(`${API_BASE_URL}/prompts/agent-c`).then(r => r.json()),
                    fetch(`${API_BASE_URL}/prompts/agent-f`).then(r => r.json()),
                    fetch(`${API_BASE_URL}/prompts/agent-g`).then(r => r.json())
                ]);
                const loadedPrompts = {
                    "Agent A (Detective)": a.prompt,
                    "Agent C (Developer)": c.prompt,
                    "Agent F (Compliance)": f.prompt,
                    "Agent G (Governance)": g.prompt
                };
                setPrompts(loadedPrompts);
                // Default to first agent
                setSelectedAgent(Object.keys(loadedPrompts)[0]);
            } catch (e) {
                console.error("Failed to load prompts", e);
            } finally {
                setLoading(false);
            }
        };
        fetchPrompts();
    }, []);

    if (loading) return <div className="text-center p-10 text-gray-500">Loading Intelligence Hub...</div>;

    const [testInput, setTestInput] = useState("");
    const [testOutput, setTestOutput] = useState("");
    const [isRunning, setIsRunning] = useState(false);

    const handleRunTest = async () => {
        if (!selectedAgent) return;
        setIsRunning(true);
        setTestOutput("Running validation...");

        try {
            // Map display name to ID
            let agentId = "agent-a";
            if (selectedAgent.includes("Agent C")) agentId = "agent-c";
            if (selectedAgent.includes("Agent F")) agentId = "agent-f";
            if (selectedAgent.includes("Agent G")) agentId = "agent-g";

            const res = await fetch(`${API_BASE_URL}/system/validate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    agent_id: agentId,
                    user_input: testInput || "Hello, verify your system prompt."
                })
            });
            const data = await res.json();
            if (data.success) {
                setTestOutput(data.response);
            } else {
                setTestOutput(`Error: ${data.error}`);
            }
        } catch (e) {
            setTestOutput(`Network Error: ${e}`);
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <div className={`h-full grid grid-cols-1 md:grid-cols-4 gap-4 ${className}`}>
            <div className="col-span-1 space-y-2 border-r border-gray-200 dark:border-gray-800 pr-4">
                {Object.keys(prompts).map(key => (
                    <div
                        key={key}
                        onClick={() => setSelectedAgent(key)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedAgent === key
                            ? "bg-blue-50 dark:bg-blue-900/20 border-primary shadow-sm"
                            : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600"
                            }`}
                    >
                        <h3 className={`font-bold text-sm ${selectedAgent === key ? "text-primary" : ""}`}>{key}</h3>
                        <p className="text-xs text-gray-500">System Prompt</p>
                    </div>
                ))}
            </div>
            <div className="col-span-3 flex flex-col gap-4">
                <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-4 overflow-y-auto font-mono text-xs text-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700 relative min-h-[300px]">
                    {selectedAgent ? (
                        <>
                            <div className="absolute top-2 right-2 text-xs text-gray-400 font-bold bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
                                {selectedAgent}
                            </div>
                            <pre className="whitespace-pre-wrap">{prompts[selectedAgent]}</pre>
                        </>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-400">Select an agent to view its prompt</div>
                    )}
                </div>

                {/* Validation Playground */}
                {selectedAgent && (
                    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-4 shadow-sm">
                        <h4 className="font-bold text-sm mb-2 flex items-center gap-2">
                            <Terminal size={14} className="text-purple-500" />
                            Validation Playground
                        </h4>
                        <div className="flex gap-2 mb-2">
                            <input
                                className="flex-1 p-2 text-sm border border-gray-300 dark:border-gray-700 rounded bg-transparent"
                                placeholder="Enter test message (e.g. 'Analyze this table struct...')"
                                value={testInput}
                                onChange={e => setTestInput(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleRunTest()}
                            />
                            <button
                                onClick={handleRunTest}
                                disabled={isRunning}
                                className="px-4 py-2 bg-purple-600 text-white text-xs font-bold rounded hover:bg-purple-700 disabled:opacity-50"
                            >
                                {isRunning ? "Testing..." : "Run Test"}
                            </button>
                        </div>
                        {testOutput && (
                            <div className="p-3 bg-gray-50 dark:bg-gray-950 rounded border border-gray-200 dark:border-gray-800 text-xs font-mono max-h-32 overflow-y-auto whitespace-pre-wrap">
                                {testOutput}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
