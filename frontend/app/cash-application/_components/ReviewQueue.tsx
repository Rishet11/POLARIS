"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Payment } from "@/lib/types";
import { approvePayment, rejectPayment } from "@/lib/api";

export default function ReviewQueue({
  payments,
  onResolved,
}: {
  payments: Payment[];
  onResolved: (paymentId: string) => void;
}) {
  const items = payments.filter((p) => p.match_tier === "REVIEW" && !p.applied);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleApprove(id: string) {
    setBusy(id);
    setError(null);
    try {
      await approvePayment(id);
      onResolved(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approve failed");
    } finally {
      setBusy(null);
    }
  }

  async function handleReject(id: string) {
    setBusy(id);
    setError(null);
    try {
      await rejectPayment(id, reasons[id] ?? "");
      onResolved(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reject failed");
    } finally {
      setBusy(null);
    }
  }

  if (items.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-[13px] font-medium text-foreground">Review Queue</h2>
      {error && <div className="text-[13px] text-status-red-fg">{error}</div>}
      <div className="flex flex-col gap-2">
        {items.map((p) => (
          <Card key={p.id} className="rounded-[4px]">
            <CardContent className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="font-mono text-[13px]">{p.id}</div>
                <div className="font-mono tabular-nums text-[13px]">
                  {p.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div className="text-[13px] text-muted-foreground">{p.payer} — {p.memo}</div>
              <div className="text-[13px]">
                Candidates:{" "}
                <span className="font-mono">
                  {p.matched_invoice_candidates.length
                    ? p.matched_invoice_candidates
                        .map((c) => `${c.invoice_id} (${c.open_amount.toFixed(2)})`)
                        .join(", ")
                    : "none"}
                </span>
              </div>
              <div className="text-[13px] text-muted-foreground">
                Confidence: {p.confidence != null ? `${p.confidence}%` : "—"} — {p.match_reason ?? "—"}
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={() => handleApprove(p.id)} disabled={busy === p.id}>
                  Approve
                </Button>
                <Input
                  placeholder="Reason for rejection"
                  className="max-w-xs"
                  value={reasons[p.id] ?? ""}
                  onChange={(e) =>
                    setReasons((r) => ({ ...r, [p.id]: e.target.value }))
                  }
                />
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleReject(p.id)}
                  disabled={busy === p.id}
                >
                  Reject
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
