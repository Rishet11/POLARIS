import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const statusPillVariants = cva(
  "inline-flex w-fit shrink-0 items-center rounded-[4px] px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide font-mono tabular-nums whitespace-nowrap",
  {
    variants: {
      variant: {
        green: "text-status-green-fg bg-status-green-bg",
        blue: "text-status-blue-fg bg-status-blue-bg",
        amber: "text-status-amber-fg bg-status-amber-bg",
        red: "text-status-red-fg bg-status-red-bg",
        gray: "text-status-gray-fg bg-status-gray-bg",
      },
    },
    defaultVariants: {
      variant: "gray",
    },
  }
)

export interface StatusPillProps
  extends React.ComponentProps<"span">,
    VariantProps<typeof statusPillVariants> {}

function StatusPill({ className, variant, ...props }: StatusPillProps) {
  return (
    <span
      data-slot="status-pill"
      className={cn(statusPillVariants({ variant }), className)}
      {...props}
    />
  )
}

export { StatusPill, statusPillVariants }
