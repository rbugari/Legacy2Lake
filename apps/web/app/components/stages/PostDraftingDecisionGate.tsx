import { useEffect, useState } from "react";
import { ArrowRight, Zap, BookOpen, Loader } from "lucide-react";
import { fetchWithAuth } from "../../lib/auth-client";

interface PostDraftingDecisionGateProps {
    projectId: string;
    onModeSelected: (mode: string) => void;
    initialSelectedMode?: string | null;
}

export default function PostDraftingDecisionGate({
    projectId,
    onModeSelected,
    initialSelectedMode = null,
}: PostDraftingDecisionGateProps) {
    const [selectedMode, setSelectedMode] = useState<string | null>(initialSelectedMode);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setSelectedMode(initialSelectedMode);
    }, [initialSelectedMode]);

    const modes = [
        {
            id: "drafting_delivery",
            title: "Drafting Delivery",
            icon: "✓",
            riskLevel: "low",
            description: "Assets are ready for certification as-is.",
            details: "Skip Refinement and proceed directly to Governance for audit and certification. No further optimization applied.",
            recommendation: "Best for: Standard SQL → Snowflake migrations with straightforward logic.",
            color: "emerald",
            recommended: false,
        },
        {
            id: "structured_refinement",
            title: "Structured Refinement",
            icon: "⚡",
            riskLevel: "low",
            description: "Apply multi-layer medallion optimization with quality rules.",
            details: "Refinement stage enhances consistency, performance, and governance compliance within bounded medallion patterns (Bronze → Silver → Gold).",
            recommendation: "Best for: Most enterprise migrations seeking modern data architecture.",
            color: "amber",
            recommended: true,
        },
        {
            id: "intelligent_reengineering",
            title: "Intelligent Reengineering",
            icon: "🧠",
            riskLevel: "medium",
            description: "Apply advanced optimizations and architectural improvements.",
            details: "Refinement stage may propose schema redesigns, query optimizations, and structural improvements for better modernization.",
            recommendation: "Best for: Complex legacy systems where architectural redesign is strategic.",
            color: "purple",
            recommended: false,
        },
    ];

    const handleSelectMode = async () => {
        if (!selectedMode) return;

        setIsSubmitting(true);
        setError(null);

        try {
            const response = await fetchWithAuth(`projects/${projectId}/set-post-drafting-mode`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mode: selectedMode }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to set post-drafting mode");
            }

            // Notify parent that mode has been selected
            onModeSelected(selectedMode);
        } catch (err: any) {
            setError(err.message || "An error occurred");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="w-full space-y-4">
            <div className="px-6 py-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-2xl">
                <h3 className="text-lg font-black text-white mb-2">What's Next?</h3>
                <p className="text-sm text-gray-400">
                    {initialSelectedMode
                        ? 'Drafting is complete. Your current post-drafting path is preselected below, and you can keep it or change it before continuing.'
                        : 'Your drafting is complete. Choose how to proceed with these assets.'}
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {modes.map((mode) => {
                    const isSelected = selectedMode === mode.id;
                    const colorClass = {
                        emerald: "border-emerald-500/50 bg-emerald-500/5 hover:bg-emerald-500/10",
                        amber: "border-amber-500/50 bg-amber-500/5 hover:bg-amber-500/10",
                        purple: "border-purple-500/50 bg-purple-500/5 hover:bg-purple-500/10",
                    }[mode.color];
                    
                    const riskBadgeColor = {
                        low: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
                        medium: "bg-amber-500/20 text-amber-300 border-amber-500/30",
                        high: "bg-red-500/20 text-red-300 border-red-500/30",
                    }[mode.riskLevel];

                    return (
                        <div
                            key={mode.id}
                            onClick={() => setSelectedMode(mode.id)}
                            className={`p-5 border-2 rounded-xl cursor-pointer transition-all space-y-3 ${
                                isSelected
                                    ? `${colorClass} border-2 border-${mode.color}-500`
                                    : colorClass
                            } ${isSelected ? "ring-2 ring-offset-2 ring-offset-slate-900" : ""}`}
                        >
                            <div className="flex items-start justify-between">
                                <div className="text-3xl">{mode.icon}</div>
                                <span className={`px-2 py-1 rounded text-xs font-black uppercase tracking-wider border ${riskBadgeColor}`}>
                                    {mode.riskLevel} risk
                                </span>
                            </div>
                            <h4 className="font-black text-white text-sm">{mode.title}</h4>
                            <p className="text-xs text-gray-300 font-medium">{mode.description}</p>
                            <p className="text-xs text-gray-400 leading-relaxed">{mode.details}</p>
                            <p className="text-xs text-gray-500 italic">{mode.recommendation}</p>
                            <div className="pt-2 flex items-center justify-between">
                                {mode.recommended && (
                                    <div className="text-xs font-black text-amber-400 uppercase tracking-wide">
                                        ⭐ Recommended
                                    </div>
                                )}
                                {isSelected && (
                                    <div className={`text-xs font-black text-${mode.color}-400 uppercase tracking-wide ml-auto`}>
                                        ✓ Selected
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {error && (
                <div className="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                    {error}
                </div>
            )}

            <div className="flex items-center gap-3">
                <button
                    onClick={handleSelectMode}
                    disabled={!selectedMode || isSubmitting}
                    className={`flex-1 flex items-center justify-center gap-2 px-6 py-3 font-black uppercase tracking-wider rounded-xl transition-all ${
                        !selectedMode || isSubmitting
                            ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                            : "bg-blue-600 hover:bg-blue-500 text-white active:scale-95"
                    }`}
                >
                    {isSubmitting ? (
                        <>
                            <Loader size={16} className="animate-spin" />
                            Setting...
                        </>
                    ) : (
                        <>
                            <ArrowRight size={16} />
                            {initialSelectedMode ? 'Update Choice' : 'Confirm Choice'}
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}
