/**
 * Dense fintech ledger table primitives.
 *
 * Conventions (baked into these components, mirrored in globals.css):
 * - Sticky header, background matches page so content doesn't show through on scroll.
 * - Column labels: 11px uppercase, letter-spaced, muted-foreground, medium weight.
 * - Row height: 36px.
 * - Cell padding: 8px vertical / 12px horizontal.
 * - Row separators: 1px hairline border, bottom only, no border on last row.
 * - Row hover: bg-row-hover (#f7f6f2).
 * - Numeric columns: pass `numeric` to DataTableCell, or apply `.num` directly
 *   (font-mono, tabular-nums, text-right). Use for amounts, ids, dates, counts.
 *
 * Usage:
 *   <DataTable>
 *     <DataTableHeader>
 *       <DataTableRow>
 *         <DataTableHead>Debtor</DataTableHead>
 *         <DataTableHead numeric>Amount</DataTableHead>
 *       </DataTableRow>
 *     </DataTableHeader>
 *     <DataTableBody>
 *       <DataTableRow>
 *         <DataTableCell>Acme Corp</DataTableCell>
 *         <DataTableCell numeric>$12,450.00</DataTableCell>
 *       </DataTableRow>
 *     </DataTableBody>
 *   </DataTable>
 */
import * as React from "react"

import { cn } from "@/lib/utils"

function DataTable({ className, ...props }: React.ComponentProps<"table">) {
  return (
    <div className="relative w-full overflow-x-auto border border-border-hairline">
      <table className={cn("w-full border-collapse text-[13px]", className)} {...props} />
    </div>
  )
}

function DataTableHeader({ className, ...props }: React.ComponentProps<"thead">) {
  return (
    <thead
      className={cn("sticky top-0 z-10 bg-background", className)}
      {...props}
    />
  )
}

function DataTableBody({ className, ...props }: React.ComponentProps<"tbody">) {
  return <tbody className={cn(className)} {...props} />
}

function DataTableRow({ className, ...props }: React.ComponentProps<"tr">) {
  return (
    <tr
      className={cn(
        "h-9 border-b border-border-hairline last:border-b-0 hover:bg-row-hover",
        className
      )}
      {...props}
    />
  )
}

function DataTableHead({
  className,
  numeric,
  ...props
}: React.ComponentProps<"th"> & { numeric?: boolean }) {
  return (
    <th
      className={cn(
        "px-3 py-2 text-left align-middle text-[11px] font-medium uppercase tracking-wide text-muted-foreground whitespace-nowrap",
        numeric && "num",
        className
      )}
      {...props}
    />
  )
}

function DataTableCell({
  className,
  numeric,
  ...props
}: React.ComponentProps<"td"> & { numeric?: boolean }) {
  return (
    <td
      className={cn(
        "px-3 py-2 align-middle whitespace-nowrap",
        numeric && "num",
        className
      )}
      {...props}
    />
  )
}

export {
  DataTable,
  DataTableHeader,
  DataTableBody,
  DataTableRow,
  DataTableHead,
  DataTableCell,
}
