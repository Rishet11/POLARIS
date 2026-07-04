import { StatusPill } from "@/components/status-pill";
import { CovenantRow } from "@/lib/types";

function statusVariant(status: CovenantRow["status"]): "green" | "amber" | "red" {
  if (status === "COMPLIANT") return "green";
  return "amber";
}

export default function CovenantPills({ covenants }: { covenants: CovenantRow[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {covenants.map((c) => (
        <div
          key={c.metric}
          className="relative border border-border-hairline rounded-[4px] bg-card px-4 py-3 flex flex-col gap-2"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              {c.metric}
            </div>
            <StatusPill variant={statusVariant(c.status)}>{c.status}</StatusPill>
          </div>
          <div className="font-mono tabular-nums text-2xl text-foreground">{c.current}</div>
          <div className="text-[11px] text-muted-foreground">Limit: {c.threshold}</div>
        </div>
      ))}
    </div>
  );
}
