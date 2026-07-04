"use client";

import {
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  forwardRef,
} from "react";
import {
  DataTable,
  DataTableHeader,
  DataTableBody,
  DataTableRow,
  DataTableHead,
  DataTableCell,
} from "@/components/data-table";
import { StatusPill } from "@/components/status-pill";
import { Input } from "@/components/ui/input";
import { AuditEntry } from "@/lib/types";
import { getAuditTrail } from "@/lib/api";

export interface AuditTrailHandle {
  refresh: () => void;
}

const AuditTrail = forwardRef<AuditTrailHandle>(function AuditTrail(_props, ref) {
  const [query, setQuery] = useState("");
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flashKey, setFlashKey] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (q: string, flash = false) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAuditTrail(q || undefined);
      const sorted = [...data].sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      setEntries(sorted);
      if (flash && sorted.length > 0) {
        const key = `${sorted[0].timestamp}-${sorted[0].payment_id}`;
        setFlashKey(key);
        setTimeout(() => setFlashKey(null), 1000);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load audit trail");
    } finally {
      setLoading(false);
    }
  }, []);

  useImperativeHandle(ref, () => ({
    refresh: () => load(query, true),
  }));

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      load(query);
    }, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h2 className="text-[13px] font-medium text-foreground">Audit Trail</h2>
        <Input
          placeholder="Search audit trail..."
          className="max-w-xs"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {loading && <div className="text-[13px] text-muted-foreground">Loading...</div>}
      {error && <div className="text-[13px] text-status-red-fg">{error}</div>}
      <DataTable>
        <DataTableHeader>
          <DataTableRow>
            <DataTableHead numeric>Timestamp</DataTableHead>
            <DataTableHead>Actor</DataTableHead>
            <DataTableHead numeric>Payment</DataTableHead>
            <DataTableHead numeric>Invoices</DataTableHead>
            <DataTableHead>Tier</DataTableHead>
            <DataTableHead numeric>Conf.</DataTableHead>
            <DataTableHead>Reason</DataTableHead>
          </DataTableRow>
        </DataTableHeader>
        <DataTableBody>
          {entries.map((e) => {
            const key = `${e.timestamp}-${e.payment_id}`;
            return (
              <DataTableRow
                key={key}
                className={key === flashKey ? "transition-colors duration-1000 bg-status-amber-bg" : ""}
              >
                <DataTableCell numeric>{e.timestamp}</DataTableCell>
                <DataTableCell>
                  <StatusPill variant={e.actor === "human" ? "blue" : "gray"}>
                    {e.actor}
                  </StatusPill>
                </DataTableCell>
                <DataTableCell numeric>{e.payment_id}</DataTableCell>
                <DataTableCell numeric>{e.invoice_ids.join(", ") || "—"}</DataTableCell>
                <DataTableCell>{e.tier}</DataTableCell>
                <DataTableCell numeric>{e.confidence != null ? `${e.confidence}%` : "—"}</DataTableCell>
                <DataTableCell>{e.reason ?? "—"}</DataTableCell>
              </DataTableRow>
            );
          })}
        </DataTableBody>
      </DataTable>
    </div>
  );
});

export default AuditTrail;
