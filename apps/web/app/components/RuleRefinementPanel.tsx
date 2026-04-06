/**
 * RuleRefinementPanel.tsx
 * UI for reviewing, refining, and creating knowledge package snapshots.
 * Shows rule candidates scored by reusability, complexity, confidence.
 */

import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../lib/auth-client';

interface RefinedRule {
  id: string;
  type: string;
  composite_score: number;
  reusability_score: number;
  complexity_score: number;
  confidence_score: number;
  applicability: 'LOCAL' | 'GLOBAL';
  recommendation: {
    action: string;
    priority: string;
    effort_estimate: string;
    blockers: string[];
    evidence_summary: string;
  };
}

interface SnapshotInfo {
  snapshot_id: string;
  created_at: string;
  understanding_artifacts: number;
  refined_rules_count: number;
  package_hash: string;
}

interface RuleRefinementPanelProps {
  projectId: string;
}

export const RuleRefinementPanel: React.FC<RuleRefinementPanelProps> = ({
  projectId,
}) => {
  const [snapshot, setSnapshot] = useState<SnapshotInfo | null>(null);
  const [refinedRules, setRefinedRules] = useState<RefinedRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [refining, setRefining] = useState(false);
  const [filter, setFilter] = useState<'ALL' | 'LOCAL' | 'GLOBAL'>('ALL');
  const [expandedRule, setExpandedRule] = useState<string | null>(null);

  // Load current snapshot on mount
  useEffect(() => {
    fetchSnapshot();
  }, [projectId]);

  const fetchSnapshot = async () => {
    try {
      const response = await fetchWithAuth(
        `/projects/${projectId}/snapshot`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
      const data = await response.json();

      if (!data.error) {
        setSnapshot(data);
        // Load refined rules
        await fetchRefinedRules();
      }
    } catch (err) {
      console.error('Failed to fetch snapshot:', err);
    }
  };

  const fetchRefinedRules = async () => {
    try {
      const response = await fetchWithAuth(
        `/projects/${projectId}/refined-rules?top_n=20`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
      const data = await response.json();

      if (!data.error && data.rules) {
        setRefinedRules(data.rules);
      }
    } catch (err) {
      console.error('Failed to fetch refined rules:', err);
    }
  };

  const handleRefine = async () => {
    setRefining(true);
    try {
      const response = await fetchWithAuth(
        `/projects/${projectId}/refine`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        }
      );
      const data = await response.json();

      if (!data.error) {
        // Refresh snapshot and rules
        await fetchSnapshot();
        await fetchRefinedRules();
      }
    } catch (err) {
      console.error('Refinement failed:', err);
    } finally {
      setRefining(false);
    }
  };

  const filteredRules = refinedRules.filter((rule) => {
    if (filter === 'ALL') return true;
    return rule.applicability === filter;
  });

  const priorityColor = (priority: string): string => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800';
      case 'LOW':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const scoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6 bg-white">
      <h2 className="text-2xl font-bold mb-4">Rule Refinement & Knowledge Snapshots</h2>

      {/* Snapshot Status */}
      <div className="mb-6 p-4 bg-gray-50 rounded border border-gray-300">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Current Snapshot</h3>
          <button
            onClick={handleRefine}
            disabled={refining || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {refining ? 'Refining...' : 'Create/Update Snapshot'}
          </button>
        </div>

        {snapshot ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Snapshot ID</p>
              <p className="font-mono text-xs">{snapshot.snapshot_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Created</p>
              <p>{new Date(snapshot.created_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Understanding Artifacts</p>
              <p className="text-lg font-bold">{snapshot.understanding_artifacts}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Refined Rules</p>
              <p className="text-lg font-bold">{snapshot.refined_rules_count}</p>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">No snapshot yet. Click "Create/Update Snapshot" to generate.</p>
        )}
      </div>

      {/* Filter */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setFilter('ALL')}
          className={`px-3 py-1 rounded ${
            filter === 'ALL'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800'
          }`}
        >
          All ({refinedRules.length})
        </button>
        <button
          onClick={() => setFilter('GLOBAL')}
          className={`px-3 py-1 rounded ${
            filter === 'GLOBAL'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800'
          }`}
        >
          Global ({refinedRules.filter((r) => r.applicability === 'GLOBAL').length})
        </button>
        <button
          onClick={() => setFilter('LOCAL')}
          className={`px-3 py-1 rounded ${
            filter === 'LOCAL'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800'
          }`}
        >
          Local ({refinedRules.filter((r) => r.applicability === 'LOCAL').length})
        </button>
      </div>

      {/* Rules List */}
      <div className="space-y-3">
        {filteredRules.map((rule) => (
          <div
            key={rule.id}
            className="border border-gray-200 rounded p-4 cursor-pointer hover:bg-gray-50"
            onClick={() =>
              setExpandedRule(expandedRule === rule.id ? null : rule.id)
            }
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <h4 className="font-semibold">{rule.id}</h4>
                <p className="text-sm text-gray-600">Type: {rule.type}</p>
              </div>
              <div className="flex gap-2">
                <span
                  className={`px-2 py-1 rounded text-xs font-semibold ${priorityColor(
                    rule.recommendation.priority
                  )}`}
                >
                  {rule.recommendation.priority}
                </span>
                <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                  {rule.applicability}
                </span>
              </div>
            </div>

            {/* Score Bars */}
            <div className="grid grid-cols-3 gap-3 mb-3 text-xs">
              <div>
                <p className="text-gray-600">Composite</p>
                <div className="bg-gray-200 rounded h-4 overflow-hidden">
                  <div
                    className={`h-full ${scoreColor(
                      rule.composite_score
                    )}`}
                    style={{ width: `${rule.composite_score * 100}%` }}
                  />
                </div>
                <p className={`mt-1 font-semibold ${scoreColor(rule.composite_score)}`}>
                  {(rule.composite_score * 100).toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-gray-600">Reusability</p>
                <div className="bg-gray-200 rounded h-4 overflow-hidden">
                  <div
                    className="h-full bg-blue-500"
                    style={{ width: `${rule.reusability_score * 100}%` }}
                  />
                </div>
                <p className="mt-1 font-semibold text-blue-600">
                  {(rule.reusability_score * 100).toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-gray-600">Confidence</p>
                <div className="bg-gray-200 rounded h-4 overflow-hidden">
                  <div
                    className="h-full bg-green-500"
                    style={{ width: `${rule.confidence_score * 100}%` }}
                  />
                </div>
                <p className="mt-1 font-semibold text-green-600">
                  {(rule.confidence_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {/* Action & Effort */}
            <div className="flex justify-between items-center text-sm mb-3">
              <span>{rule.recommendation.action}</span>
              <span className="px-2 py-1 bg-blue-50 text-blue-800 rounded text-xs">
                Effort: {rule.recommendation.effort_estimate}
              </span>
            </div>

            {/* Evidence */}
            <p className="text-xs text-gray-600 italic">
              {rule.recommendation.evidence_summary}
            </p>

            {/* Expanded Details */}
            {expandedRule === rule.id && (
              <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-sm">
                <div>
                  <p className="font-semibold text-gray-700">Blockers:</p>
                  {rule.recommendation.blockers.length > 0 ? (
                    <ul className="list-disc list-inside ml-2">
                      {rule.recommendation.blockers.map((blocker, idx) => (
                        <li key={idx} className="text-red-600">
                          {blocker}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-green-600">None</p>
                  )}
                </div>
                <div>
                  <p className="font-semibold text-gray-700">Scores:</p>
                  <p>Complexity: {(rule.complexity_score * 100).toFixed(0)}%</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredRules.length === 0 && (
        <p className="text-center text-gray-500 py-8">
          No rules match the selected filter.
        </p>
      )}
    </div>
  );
};

export default RuleRefinementPanel;
