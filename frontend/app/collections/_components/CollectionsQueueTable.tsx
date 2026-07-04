"use client";

import { useState } from "react";
import { toast } from "sonner";
import { buildQueue } from "@/lib/api";
import { CollectionCase } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { StatusPill, StatusPillProps } from "@/components/status-pill";
import {
  DataTable,
  DataTableHeader,
  DataTableBody,
  DataTableRow,
  DataTableHead,
  DataTableCell,
} from "@/components/data-table";

function agingVariant(bucket: string): StatusPillProps["variant"] {
  switch (bucket) {
    case "CURRENT":
    case "1-30":
      return "gray";
    case "31-60":
    case "61-90":
      return "amber";
    case "90+":
      return "red";
    default:
      return "gray";
  }
}

function stageVariant(stage: CollectionCase["stage"]): StatusPillProps["variant"] {
  switch (stage) {
    case "RESOLVED":
      return "green";
    case "WRITTEN_OFF":
      return "gray";
    case "ESCALATE":
    case "DISPUTE_INTAKE":
      return "red";
    case "PROMISE_TO_PAY":
      return "blue";
    case "AWAIT_RESPONSE":
    case "OUTREACH":
      return "amber";
    default:
      return "gray";
  }
}

function formatMoney(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export default function CollectionsQueueTable({
  onSelectCase,
}: {
  onSelectCase: (id: string) => void;
}) {
  const [cases, setCases] = useState<CollectionCase[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleBuildQueue() {
    setLoading(true);
    setError(null);
    try {
      const result = await buildQueue();
      setCases(result);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to build queue";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  const sorted = cases
    ? [...cases].sort((a, b) => b.priority_score - a.priority_score)
    : null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[15px] font-semibold text-foreground">Collections Queue</h1>
          <p className="text-[12px] text-muted-foreground">
            FSM-governed outreach and escalation on factored invoices.
          </p>
        </div>
        <Button size="sm" onClick={handleBuildQueue} disabled={loading}>
          {loading ? "Building..." : "Build Collections Queue"}
        </Button>
      </div>

      {error && <div className="text-[12px] text-status-red-fg">{error}</div>}

      {sorted && (
        <DataTable>
          <DataTableHeader>
            <DataTableRow>
              <DataTableHead>Case</DataTableHead>
              <DataTableHead>Debtor</DataTableHead>
              <DataTableHead numeric>Open Amount</DataTableHead>
              <DataTableHead>Aging</DataTableHead>
              <DataTableHead numeric>Priority</DataTableHead>
              <DataTableHead>Stage</DataTableHead>
              <DataTableHead numeric>Outreach</DataTableHead>
            </DataTableRow>
          </DataTableHeader>
          <DataTableBody>
            {sorted.map((c) => (
              <DataTableRow
                key={c.case_id}
                className="cursor-pointer"
                onClick={() => onSelectCase(c.case_id)}
              >
                <DataTableCell numeric>{c.case_id}</DataTableCell>
                <DataTableCell>{c.debtor_name}</DataTableCell>
                <DataTableCell numeric>{formatMoney(c.open_amount)}</DataTableCell>
                <DataTableCell>
                  <StatusPill variant={agingVariant(c.aging_bucket)}>
                    {c.aging_bucket}
                  </StatusPill>
                </DataTableCell>
                <DataTableCell numeric>{c.priority_score}</DataTableCell>
                <DataTableCell>
                  <StatusPill variant={stageVariant(c.stage)}>{c.stage}</StatusPill>
                </DataTableCell>
                <DataTableCell numeric>{c.outreach_count}</DataTableCell>
              </DataTableRow>
            ))}
          </DataTableBody>
        </DataTable>
      )}

      {!sorted && !loading && (
        <div className="text-[13px] text-muted-foreground border border-border-hairline rounded-[4px] p-6 text-center">
          No queue built yet. Click &quot;Build Collections Queue&quot; to prioritize open cases.
        </div>
      )}
    </div>
  );
}
