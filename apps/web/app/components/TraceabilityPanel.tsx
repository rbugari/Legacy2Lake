"use client";
import React, { useEffect, useState } from "react";
import { fetchWithAuth } from "../lib/auth-client";
import { GitCompare, Loader2, AlertCircle, CheckCircle, Info, RefreshCw, ChevronDown, ChevronRight } from "lucide-react";

interface AssetSummary {
  asset_id: string;
  asset_name: string;
  overall_status: string;
  summary: { preserved: number; inferred: number; changed: number; unresolved: number; total: number };
  computed_at?: string;
}

interface ColumnEntry {
  source_name: string;
  source_type: string;
  target_name?: string;
  status: string;
  note?: string;
  is_pii?: boolean;
}

interface TableEntry {
  source_name: string;
  operation: string;
  status: string;
  note?: string;
}

interface AssetDetail {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  target_code_available: boolean;
  overall_status: string;
  summary: { preserved: number; inferred: number; changed: number; unresolved: number; total: number };
  column_entries: ColumnEntry[];
  table_entries: TableEntry[];
  computed_at: string;
}

const STATUS_STYLE: Record<string, string> = {
  PRESERVED:  "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  INFERRED:   "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
  CHANGED:    "bg-blue-500/15 text-blue-300 border-blue-500/30",
  UNRESOLVED: "bg-red-500/15 text-red-400 border-red-500/30",
};

const OVERALL_STYLE: Record<string, string> = {
  FULLY_MAPPED:         "text-emerald-400",
  MAPPED_WITH_CHANGES:  "text-blue-400",
  MOSTLY_MAPPED:        "text-yellow-400",
  REQUIRES_REVIEW:      "text-red-400",
  NO_TARGET_OUTPUT:     "text-gray-500",
  UNKNOWN:              "text-gray-500",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${STATUS_STYLE[status] ?? "bg-gray-700 text-gray-400 border-gray-600"}`}>
      {status}
    </span>
  );
}

function ProgressBar({ summary }: { summary: AssetDetail["summary"] }) {
  const total = summary.total || 1;
  return (
    <div className="flex h-1.5 rounded overflow-hidden w-full">
      <div style={{ width: `${(summary.preserved / total) * 100}%` }} className="bg-emerald-500" />
      <div style={{ width: `${(summary.inferred / total) * 100}%` }} className="bg-yellow-500" />
      <div style={{ width: `${(summary.changed / total) * 100}%` }} className="bg-blue-500" />
      <div style={{ width: `${(summary.unresolved / total) * 100}%` }} className="bg-red-500" />
    </div>
  );
}

function AssetDetailPanel({ projectId, asset, onClose }: { projectId: string; asset: AssetSummary; onClose: () => void }) {
  const [detail, setDetail] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCols, setShowCols] = useState(true);
  const [showTables, setShowTables] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchWithAuth(`projects/${projectId}/traceability/${asset.asset_id}`)
      .then((r) => (r.ok ? r.json() : r.json().then((e: any) => Promise.reject(e.detail || "Error"))))
      .then(setDetail)
      .catch((e) => setError(typeof e === "string" ? e : "Could not load traceability"))
      .finally(() => setLoading(false));
  }, [projectId, asset.asset_id]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-[#0d1117] border border-gray-700 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <GitCompare size={16} className="text-indigo-400" />
            <span className="text-sm font-semibold text-white truncate">{asset.asset_name}</span>
            {detail && (
              <span className={`text-xs font-medium ${OVERALL_STYLE[detail.overall_status] ?? "text-gray-400"}`}>
                — {detail.overall_status.replace(/_/g, " ")}
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 transition-colors text-xs px-2 py-1 rounded border border-gray-700">
            Close
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {loading && (
            <div className="flex items-center gap-2 text-gray-400 text-sm">
              <Loader2 size={14} className="animate-spin" /> Building traceability map…
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
              <AlertCircle size={14} /> {error}
            </div>
          )}
          {detail && !loading && (
            <>
              {/* Summary pills */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="text-gray-400">{detail.summary.total} items —</span>
                <span className="text-emerald-400">{detail.summary.preserved} preserved</span>
                <span className="text-yellow-400">{detail.summary.inferred} inferred</span>
                <span className="text-blue-400">{detail.summary.changed} changed</span>
                <span className="text-red-400">{detail.summary.unresolved} unresolved</span>
                {!detail.target_code_available && (
                  <span className="text-gray-500 ml-2 flex items-center gap-1">
                    <Info size={11} /> No generated output available yet
                  </span>
                )}
              </div>
              <ProgressBar summary={detail.summary} />

              {/* Column entries */}
              {detail.column_entries.length > 0 && (
                <div>
                  <button
                    onClick={() => setShowCols((v) => !v)}
                    className="flex items-center gap-1 text-xs text-gray-400 font-semibold uppercase tracking-wide mb-2"
                  >
                    {showCols ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    Columns ({detail.column_entries.length})
                  </button>
                  {showCols && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="text-gray-500 border-b border-gray-800">
                            <th className="py-1.5 pr-3 font-medium">Source</th>
                            <th className="py-1.5 pr-3 font-medium">Type</th>
                            <th className="py-1.5 pr-3 font-medium">Target</th>
                            <th className="py-1.5 pr-3 font-medium">Status</th>
                            <th className="py-1.5 font-medium">Note</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.column_entries.map((col, i) => (
                            <tr key={i} className="border-b border-gray-800/50 hover:bg-white/[0.02]">
                              <td className="py-1.5 pr-3 font-mono text-gray-300">
                                {col.source_name}
                                {col.is_pii && <span className="ml-1 text-[9px] text-rose-400 bg-rose-500/10 px-1 rounded">PII</span>}
                              </td>
                              <td className="py-1.5 pr-3 text-gray-500 font-mono">{col.source_type}</td>
                              <td className="py-1.5 pr-3 font-mono text-gray-300">{col.target_name ?? <span className="text-gray-600">—</span>}</td>
                              <td className="py-1.5 pr-3"><StatusBadge status={col.status} /></td>
                              <td className="py-1.5 text-gray-500 max-w-[200px] truncate" title={col.note ?? ""}>{col.note ?? ""}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Table entries */}
              {detail.table_entries.length > 0 && (
                <div>
                  <button
                    onClick={() => setShowTables((v) => !v)}
                    className="flex items-center gap-1 text-xs text-gray-400 font-semibold uppercase tracking-wide mb-2"
                  >
                    {showTables ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    Table References ({detail.table_entries.length})
                  </button>
                  {showTables && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead>
                          <tr className="text-gray-500 border-b border-gray-800">
                            <th className="py-1.5 pr-3 font-medium">Source Table</th>
                            <th className="py-1.5 pr-3 font-medium">Operation</th>
                            <th className="py-1.5 pr-3 font-medium">Status</th>
                            <th className="py-1.5 font-medium">Note</th>
                          </tr>
                        </thead>
                        <tbody>
                          {detail.table_entries.map((tbl, i) => (
                            <tr key={i} className="border-b border-gray-800/50 hover:bg-white/[0.02]">
                              <td className="py-1.5 pr-3 font-mono text-gray-300">{tbl.source_name}</td>
                              <td className="py-1.5 pr-3 text-gray-500">{tbl.operation}</td>
                              <td className="py-1.5 pr-3"><StatusBadge status={tbl.status} /></td>
                              <td className="py-1.5 text-gray-500 max-w-[200px] truncate" title={tbl.note ?? ""}>{tbl.note ?? ""}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {detail.column_entries.length === 0 && detail.table_entries.length === 0 && (
                <p className="text-gray-500 text-xs">
                  No column or table data found for this asset. Run Triage to collect source metadata.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

interface Props {
  projectId: string;
}

export default function TraceabilityPanel({ projectId }: Props) {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AssetSummary | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    fetchWithAuth(`projects/${projectId}/traceability`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setAssets)
      .catch(() => setError("Could not load traceability list"))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [projectId]);

  return (
    <div className="space-y-4">
      {/* Panel header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitCompare size={16} className="text-indigo-400" />
          <h3 className="text-base font-semibold text-white">Traceability Review</h3>
        </div>
        <button onClick={load} disabled={loading} className="text-gray-500 hover:text-gray-300 disabled:opacity-40 transition-colors">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <p className="text-xs text-gray-500 leading-relaxed">
        Column and table-level traceability from legacy source to generated target output.
        Status badges: <span className="text-emerald-400">PRESERVED</span> · <span className="text-yellow-400">INFERRED</span> · <span className="text-blue-400">CHANGED</span> · <span className="text-red-400">UNRESOLVED</span>.
        Click an asset to compute its map.
      </p>

      {loading && (
        <div className="flex items-center gap-2 text-gray-400 text-sm">
          <Loader2 size={14} className="animate-spin" /> Loading…
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {!loading && !error && assets.length === 0 && (
        <div className="bg-white/[0.02] border border-white/8 rounded-xl px-4 py-6 text-center text-gray-500 text-sm">
          <GitCompare size={28} className="mx-auto mb-2 opacity-30" />
          No traceability data yet. Open any asset below to compute its map.
          <br />
          <span className="text-xs">Traceability is available for assets that have generated output (Drafting stage).</span>
        </div>
      )}

      {assets.length > 0 && (
        <div className="space-y-2">
          {assets.map((asset) => {
            const hasIssues = (asset.summary?.unresolved ?? 0) > 0;
            return (
              <button
                key={asset.asset_id}
                onClick={() => setSelected(asset)}
                className="w-full text-left bg-white/[0.02] hover:bg-white/[0.04] border border-white/8 rounded-xl px-4 py-3 transition-colors group"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-200 font-medium truncate pr-2">{asset.asset_name}</span>
                  <span className={`text-xs ${OVERALL_STYLE[asset.overall_status] ?? "text-gray-500"}`}>
                    {asset.overall_status.replace(/_/g, " ")}
                  </span>
                </div>
                {asset.summary?.total > 0 && (
                  <>
                    <ProgressBar summary={asset.summary} />
                    <div className="flex gap-3 mt-1.5 text-[10px] text-gray-500">
                      <span className="text-emerald-400">{asset.summary.preserved}✓</span>
                      <span className="text-yellow-400">{asset.summary.inferred}~</span>
                      <span className="text-blue-400">{asset.summary.changed}Δ</span>
                      {hasIssues && <span className="text-red-400">{asset.summary.unresolved} unresolved</span>}
                    </div>
                  </>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Click-to-compute prompt for assets without cached data */}
      {!loading && (
        <p className="text-xs text-gray-600 text-center pt-2">
          Click any asset to compute or refresh its traceability map from current source + generated data.
        </p>
      )}

      {selected && (
        <AssetDetailPanel
          projectId={projectId}
          asset={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
