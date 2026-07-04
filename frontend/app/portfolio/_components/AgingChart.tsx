"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { StatusPill } from "@/components/status-pill";
import { AgingBucketKey, AgingDistribution } from "@/lib/types";

const BUCKET_ORDER: AgingBucketKey[] = ["CURRENT", "1-30", "31-60", "61-90", "90+"];

const BUCKET_COLOR: Record<AgingBucketKey, string> = {
  CURRENT: "#1a7f4b",
  "1-30": "#1a7f4b",
  "31-60": "#a06b00",
  "61-90": "#a06b00",
  "90+": "#b3392e",
};

interface ChartDatum {
  bucket: AgingBucketKey;
  amount: number;
  count: number;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: ChartDatum }[];
}) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <div className="border border-border-hairline bg-card px-3 py-2 text-[13px] font-mono tabular-nums">
      <div className="font-sans font-medium uppercase tracking-wide text-[11px] text-muted-foreground mb-1">
        {d.bucket}
      </div>
      <div>${d.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
      <div className="text-muted-foreground">{d.count} invoices</div>
    </div>
  );
}

export default function AgingChart({ aging }: { aging: AgingDistribution }) {
  const data: ChartDatum[] = BUCKET_ORDER.map((bucket) => {
    const b = aging[bucket] as { count: number; amount: number; pct_of_open_ar: number };
    return { bucket, amount: b.amount, count: b.count };
  });

  const maxAmount = Math.max(...data.map((d) => d.amount), 0);
  const yMax = Math.ceil((maxAmount * 1.15) / 1000) * 1000;

  return (
    <div className="border border-border-hairline rounded-[4px] bg-card px-4 py-3 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Aging over 60 days
          </div>
          <div className="font-mono tabular-nums text-2xl text-foreground">
            {aging.pct_over_60}%
          </div>
        </div>
        <StatusPill variant={aging.status === "COMPLIANT" ? "green" : "amber"}>
          {aging.status}
        </StatusPill>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="var(--border-hairline)" vertical={false} />
            <XAxis
              dataKey="bucket"
              tick={{ fontFamily: "var(--font-mono)", fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={{ stroke: "var(--border-hairline)" }}
              tickLine={false}
            />
            <YAxis
              domain={[0, yMax]}
              tick={{ fontFamily: "var(--font-mono)", fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={{ stroke: "var(--border-hairline)" }}
              tickLine={false}
              width={56}
              tickFormatter={(v: number) => `$${v.toLocaleString()}`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--row-hover)" }} />
            <Bar dataKey="amount" radius={[2, 2, 0, 0]} isAnimationActive={false}>
              {data.map((d) => (
                <Cell key={d.bucket} fill={BUCKET_COLOR[d.bucket]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
