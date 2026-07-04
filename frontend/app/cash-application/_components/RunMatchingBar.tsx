"use client";

import { Button } from "@/components/ui/button";
import { KPIs } from "@/lib/types";

function KpiTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex-1 border border-border-hairline rounded-[4px] px-4 py-3">
      <div className="font-mono tabular-nums text-2xl text-foreground">{value}</div>
      <div className="mt-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
    </div>
  );
}

export default function RunMatchingBar({
  kpis,
  loading,
  error,
  onRun,
}: {
  kpis: KPIs | null;
  loading: boolean;
  error: string | null;
  onRun: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <Button onClick={onRun} disabled={loading}>
          {loading ? "Running..." : "Run Payment Matching"}
        </Button>
        {loading && <span className="text-[13px] text-muted-foreground">Loading...</span>}
        {error && <span className="text-[13px] text-status-red-fg">{error}</span>}
      </div>
      {kpis && (
        <div className="flex gap-3">
          <KpiTile label="Auto-Match Rate" value={`${kpis.auto_match_rate.toFixed(1)}%`} />
          <KpiTile label="Auto-Applied" value={String(kpis.auto_applied)} />
          <KpiTile label="Needs Review" value={String(kpis.needs_review)} />
          <KpiTile label="Exceptions" value={String(kpis.exceptions)} />
        </div>
      )}
    </div>
  );
}
