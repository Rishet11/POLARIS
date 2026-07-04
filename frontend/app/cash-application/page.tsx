"use client";

import { useCallback, useRef, useState } from "react";
import RunMatchingBar from "./_components/RunMatchingBar";
import MatchResultsTable from "./_components/MatchResultsTable";
import ReviewQueue from "./_components/ReviewQueue";
import ExceptionQueue from "./_components/ExceptionQueue";
import AuditTrail, { AuditTrailHandle } from "./_components/AuditTrail";
import { KPIs, Payment } from "@/lib/types";
import { runMatching } from "@/lib/api";

export default function CashApplicationPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const auditRef = useRef<AuditTrailHandle>(null);

  const handleRun = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runMatching();
      setKpis(result.kpis);
      setPayments(result.payments);
      auditRef.current?.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run matching");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleResolved = useCallback((paymentId: string) => {
    setPayments((prev) => prev.filter((p) => p.id !== paymentId));
    auditRef.current?.refresh();
  }, []);

  return (
    <div className="flex flex-col gap-6 p-6">
      <RunMatchingBar kpis={kpis} loading={loading} error={error} onRun={handleRun} />
      {payments.length > 0 && <MatchResultsTable payments={payments} />}
      <ReviewQueue payments={payments} onResolved={handleResolved} />
      <ExceptionQueue payments={payments} onResolved={handleResolved} />
      <AuditTrail ref={auditRef} />
    </div>
  );
}
