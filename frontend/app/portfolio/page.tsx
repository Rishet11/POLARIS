"use client";

import { useEffect, useState } from "react";
import { getAging, getConcentration, getCovenants, getSummary } from "@/lib/api";
import { AgingDistribution, ConcentrationRow, CovenantRow, PortfolioSummary } from "@/lib/types";
import CovenantPills from "./_components/CovenantPills";
import AgingChart from "./_components/AgingChart";
import ConcentrationTable from "./_components/ConcentrationTable";
import ExportCsvButton from "./_components/ExportCsvButton";

export default function PortfolioPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [covenants, setCovenants] = useState<CovenantRow[] | null>(null);
  const [concentration, setConcentration] = useState<ConcentrationRow[] | null>(null);
  const [aging, setAging] = useState<AgingDistribution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getSummary(), getCovenants(), getConcentration(), getAging()])
      .then(([s, c, conc, a]) => {
        setSummary(s);
        setCovenants(c);
        setConcentration(conc);
        setAging(a);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Portfolio Monitor</h1>
        <ExportCsvButton />
      </div>

      {loading && <div className="text-[13px] text-muted-foreground">Loading...</div>}
      {error && <div className="text-[13px] text-status-red-fg">{error}</div>}

      {summary && (
        <div className="flex gap-6">
          <div className="border border-border-hairline rounded-[4px] bg-card px-4 py-3 flex-1">
            <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Open AR Total
            </div>
            <div className="font-mono tabular-nums text-3xl text-foreground mt-1">
              $
              {summary.open_ar_total.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </div>
          </div>
          <div className="border border-border-hairline rounded-[4px] bg-card px-4 py-3 flex-1">
            <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Funds Employed
            </div>
            <div className="font-mono tabular-nums text-3xl text-foreground mt-1">
              $
              {summary.funds_employed.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
            </div>
          </div>
        </div>
      )}

      {covenants && <CovenantPills covenants={covenants} />}

      {aging && <AgingChart aging={aging} />}

      {concentration && <ConcentrationTable rows={concentration} />}
    </div>
  );
}
