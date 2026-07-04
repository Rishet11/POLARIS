"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Payment } from "@/lib/types";
import { approveFirstCandidate } from "@/lib/api";

export default function ExceptionQueue({
  payments,
  onResolved,
}: {
  payments: Payment[];
  onResolved: (paymentId: string) => void;
}) {
  const items = payments.filter((p) => p.match_tier === "EXCEPTION" && !p.applied);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleApproveFirst(id: string) {
    setBusy(id);
    setError(null);
    try {
      await approveFirstCandidate(id);
      onResolved(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approve failed");
    } finally {
      setBusy(null);
    }
  }

  if (items.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-[13px] font-medium text-foreground">Exception Queue</h2>
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
                {p.match_reason ?? "—"}
              </div>
              {p.matched_invoice_candidates.length > 0 && (
                <div>
                  <Button
                    size="sm"
                    onClick={() => handleApproveFirst(p.id)}
                    disabled={busy === p.id}
                  >
                    Approve first candidate
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
