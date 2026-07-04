"use client";

import {
  DataTable,
  DataTableHeader,
  DataTableBody,
  DataTableRow,
  DataTableHead,
  DataTableCell,
} from "@/components/data-table";
import { StatusPill } from "@/components/status-pill";
import { Payment, MatchTier } from "@/lib/types";

const TIER_LABEL: Record<MatchTier, string> = {
  AUTO_APPLY: "AUTO-APPLY",
  AUTO_APPLY_LOGGED: "AUTO+LOG",
  REVIEW: "REVIEW",
  EXCEPTION: "EXCEPTION",
};

const TIER_VARIANT: Record<MatchTier, "green" | "blue" | "amber" | "red"> = {
  AUTO_APPLY: "green",
  AUTO_APPLY_LOGGED: "blue",
  REVIEW: "amber",
  EXCEPTION: "red",
};

function TierPill({ tier, confidence }: { tier: MatchTier | null; confidence: number | null }) {
  if (!tier) return <StatusPill variant="gray">UNMATCHED</StatusPill>;
  const label =
    tier === "AUTO_APPLY" && confidence != null
      ? `${TIER_LABEL[tier]} ${confidence}`
      : TIER_LABEL[tier];
  return <StatusPill variant={TIER_VARIANT[tier]}>{label}</StatusPill>;
}

export default function MatchResultsTable({ payments }: { payments: Payment[] }) {
  return (
    <DataTable>
      <DataTableHeader>
        <DataTableRow>
          <DataTableHead numeric>Payment</DataTableHead>
          <DataTableHead>Payer</DataTableHead>
          <DataTableHead numeric>Amount</DataTableHead>
          <DataTableHead>Memo</DataTableHead>
          <DataTableHead>Tier</DataTableHead>
          <DataTableHead numeric>Conf.</DataTableHead>
          <DataTableHead numeric>Matched Invoices</DataTableHead>
          <DataTableHead>Match Reason</DataTableHead>
        </DataTableRow>
      </DataTableHeader>
      <DataTableBody>
        {payments.map((p) => (
          <DataTableRow key={p.id}>
            <DataTableCell numeric>{p.id}</DataTableCell>
            <DataTableCell>{p.payer}</DataTableCell>
            <DataTableCell numeric>
              {p.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </DataTableCell>
            <DataTableCell>{p.memo}</DataTableCell>
            <DataTableCell>
              <TierPill tier={p.match_tier} confidence={p.confidence} />
            </DataTableCell>
            <DataTableCell numeric>{p.confidence != null ? `${p.confidence}%` : "—"}</DataTableCell>
            <DataTableCell numeric>
              {p.matched_invoice_ids.length ? p.matched_invoice_ids.join(", ") : "—"}
            </DataTableCell>
            <DataTableCell>{p.match_reason ?? "—"}</DataTableCell>
          </DataTableRow>
        ))}
      </DataTableBody>
    </DataTable>
  );
}
