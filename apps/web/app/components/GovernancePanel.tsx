/**
 * GovernancePanel.tsx
 * UI for governance readiness validation and snapshot versioning.
 */

import React, { useState, useEffect } from 'react';
import { Check, AlertCircle, X, ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { fetchWithAuth } from '../lib/auth-client';

export const GovernancePanel: React.FC<{ projectId: string }> = ({ projectId }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'checks' | 'diff' | 'history'>('checks');

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [govRes, diffRes, histRes] = await Promise.all([
        fetchWithAuth(`/projects/${projectId}/governance/checks`),
        fetchWithAuth(`/projects/${projectId}/snapshot/diff`),
        fetchWithAuth(`/projects/${projectId}/snapshot/history`),
      ]);
      
      const gov = govRes.ok ? await govRes.json() : null;
      const dif = diffRes.ok ? await diffRes.json() : null;
      const his = histRes.ok ? await histRes.json() : null;
      
      setData({ gov, dif, his });
    } catch (err) {
      console.error('Failed to load governance data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!data || loading) return <div className="p-8 text-gray-500">Loading governance data...</div>;

  const gov = data.gov;
  const dif = data.dif?.diff;
  const his = data.his;

  return (
    <div className="p-6 bg-white space-y-6">
      <h2 className="text-2xl font-bold">Governance & Versioning</h2>

      {/* Status Card */}
      {gov && (
        <div className="p-4 rounded-lg border border-gray-300 bg-gradient-to-r from-gray-50 to-white">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Readiness Status</h3>
            <span
              className={`px-3 py-1 rounded-full text-sm font-semibold ${
                gov.status === 'pass'
                  ? 'bg-green-100 text-green-800'
                  : gov.status === 'warning'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
              }`}
            >
              {gov.status.toUpperCase()}
            </span>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{gov.passed}</p>
              <p className="text-xs text-gray-600">Passed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">{gov.warnings}</p>
              <p className="text-xs text-gray-600">Warnings</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{gov.failures}</p>
              <p className="text-xs text-gray-600">Failures</p>
            </div>
            <div className="text-center">
              <p className={`text-2xl font-bold ${gov.can_finalize ? 'text-green-600' : 'text-red-600'}`}>
                {gov.can_finalize ? '✓' : '✗'}
              </p>
              <p className="text-xs text-gray-600">Can Finalize</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {['checks', 'diff', 'history'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === tab
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600'
            }`}
          >
            {tab === 'checks' && `Checks (${gov?.checks.length || 0})`}
            {tab === 'diff' && `Changes (${dif?.summary.total_changes || 0})`}
            {tab === 'history' && `History (${his?.total_versions || 0})`}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="space-y-3">
        {activeTab === 'checks' &&
          gov?.checks.map((check: any, idx: number) => (
            <div key={idx} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                {check.status === 'pass' && <Check className="w-5 h-5 text-green-600 mt-0.5" />}
                {check.status === 'warning' && <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />}
                {check.status === 'fail' && <X className="w-5 h-5 text-red-600 mt-0.5" />}
                <div className="flex-1">
                  <p className="font-semibold capitalize">{check.name.replace(/_/g, ' ')}</p>
                  <p className="text-sm text-gray-600">{check.message}</p>
                </div>
              </div>
            </div>
          ))}

        {activeTab === 'diff' && dif && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg grid grid-cols-5 gap-2 text-sm">
              <div>Added: <span className="font-bold text-green-600">{dif.summary.added_count}</span></div>
              <div>Removed: <span className="font-bold text-red-600">{dif.summary.removed_count}</span></div>
              <div>Promoted: <span className="font-bold text-purple-600">{dif.summary.promoted_count}</span></div>
              <div>Demoted: <span className="font-bold text-amber-600">{dif.summary.demoted_count}</span></div>
              <div>{dif.significant ? <span className="font-bold text-orange-600">🔔 Significant</span> : <span className="text-gray-600">Minor</span>}</div>
            </div>
            {dif.changes.slice(0, 15).map((change: any, idx: number) => (
              <div key={idx} className="border border-gray-200 rounded p-2 text-sm">
                <p className="font-semibold capitalize">{change.type.replace(/_/g, ' ')}</p>
                <p className="text-xs text-gray-600">
                  {change.rule_id && `Rule: ${change.rule_id}`}
                  {change.delta && ` (Δ ${change.delta > 0 ? '+' : ''}${change.delta})`}
                </p>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'history' &&
          his?.history.map((snapshot: any, idx: number) => (
            <div key={idx} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between">
                <div>
                  <p className="font-semibold">{snapshot.version}</p>
                  <p className="text-xs text-gray-500">{snapshot.snapshot_id}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">{snapshot.rules_count}</p>
                  <p className="text-xs text-gray-600">rules</p>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};

export default GovernancePanel;
