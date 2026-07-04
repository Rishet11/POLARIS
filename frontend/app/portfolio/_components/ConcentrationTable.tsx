import {
  DataTable,
  DataTableHeader,
  DataTableBody,
  DataTableRow,
  DataTableHead,
  DataTableCell,
} from "@/components/data-table";
import { StatusPill } from "@/components/status-pill";
import { ConcentrationRow } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function ConcentrationTable({ rows }: { rows: ConcentrationRow[] }) {
  const sorted = [...rows].sort((a, b) => b.open_amount - a.open_amount);

  return (
    <DataTable>
      <DataTableHeader>
        <DataTableRow>
          <DataTableHead>Debtor</DataTableHead>
          <DataTableHead numeric>Open Amount</DataTableHead>
          <DataTableHead numeric>% of Open AR</DataTableHead>
          <DataTableHead>Status</DataTableHead>
        </DataTableRow>
      </DataTableHeader>
      <DataTableBody>
        {sorted.map((r) => (
          <DataTableRow
            key={r.debtor_id}
            className={cn(r.status === "WARNING" && "border-l-2 border-l-status-amber-fg")}
          >
            <DataTableCell>{r.debtor_name}</DataTableCell>
            <DataTableCell numeric>
              {r.open_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </DataTableCell>
            <DataTableCell numeric>{r.pct_of_open_ar}%</DataTableCell>
            <DataTableCell>
              <StatusPill variant={r.status === "COMPLIANT" ? "green" : "amber"}>
                {r.status}
              </StatusPill>
            </DataTableCell>
          </DataTableRow>
        ))}
      </DataTableBody>
    </DataTable>
  );
}
