import { CollectionStage } from "@/lib/types";
import { cn } from "@/lib/utils";

// Real stage graph from factoring/collections_fsm.py ALLOWED_TRANSITIONS.
// Linear spine with a branch at AWAIT_RESPONSE into three possible next
// stages, all converging on the two terminal states.
const SPINE: CollectionStage[] = ["PRIORITIZE", "OUTREACH", "AWAIT_RESPONSE"];
const BRANCH: CollectionStage[] = ["PROMISE_TO_PAY", "DISPUTE_INTAKE", "ESCALATE"];
const TERMINAL: CollectionStage[] = ["RESOLVED", "WRITTEN_OFF"];

const ALL_ORDER: CollectionStage[] = [...SPINE, ...BRANCH, ...TERMINAL];

function stageState(stage: CollectionStage, current: CollectionStage): "past" | "current" | "future" {
  if (stage === current) return "current";
  const stageIdx = ALL_ORDER.indexOf(stage);
  const currentIdx = ALL_ORDER.indexOf(current);
  return stageIdx < currentIdx ? "past" : "future";
}

function StageDot({ state }: { state: "past" | "current" | "future" }) {
  return (
    <span
      className={cn(
        "inline-block size-2 rounded-full shrink-0 border",
        state === "current" && "bg-accent border-accent",
        state === "past" && "bg-muted-foreground border-muted-foreground",
        state === "future" && "bg-transparent border-border-hairline"
      )}
    />
  );
}

function StageLabel({ stage, state }: { stage: CollectionStage; state: "past" | "current" | "future" }) {
  return (
    <span
      className={cn(
        "font-mono text-[11px] uppercase tracking-wide whitespace-nowrap",
        state === "current" && "text-accent font-semibold",
        state === "past" && "text-muted-foreground",
        state === "future" && "text-muted-foreground/40"
      )}
    >
      {stage.replace(/_/g, " ")}
    </span>
  );
}

function Connector({ state }: { state: "past" | "current" | "future" }) {
  return (
    <span
      className={cn(
        "h-px flex-1 min-w-4",
        state === "past" ? "bg-muted-foreground" : "bg-border-hairline"
      )}
    />
  );
}

export default function FsmStageTrack({ stage }: { stage: CollectionStage }) {
  const isBranchOrLater = BRANCH.includes(stage) || TERMINAL.includes(stage);

  return (
    <div className="flex flex-col gap-3 py-3">
      {/* Spine: PRIORITIZE -> OUTREACH -> AWAIT_RESPONSE */}
      <div className="flex items-center">
        {SPINE.map((s, i) => {
          const st = stageState(s, stage);
          return (
            <div key={s} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1">
                <StageDot state={st} />
                <StageLabel stage={s} state={st} />
              </div>
              {i < SPINE.length - 1 && (
                <Connector state={stageState(SPINE[i + 1], stage) === "future" && st === "future" ? "future" : st} />
              )}
            </div>
          );
        })}
        <Connector state={isBranchOrLater ? "past" : "future"} />
      </div>

      {/* Branch: three possible destinations from AWAIT_RESPONSE, stacked
          vertically so labels never wrap/collide at drawer width. */}
      <div className="flex flex-col gap-1.5 pl-3 ml-1 border-l border-border-hairline">
        {BRANCH.map((s) => {
          const st = stageState(s, stage);
          return (
            <div key={s} className="flex items-center gap-2">
              <StageDot state={st} />
              <StageLabel stage={s} state={st} />
            </div>
          );
        })}
      </div>

      {/* Terminal states */}
      <div className="flex items-center justify-center gap-6 pt-1 border-t border-border-hairline">
        {TERMINAL.map((s) => {
          const st = stageState(s, stage);
          return (
            <div key={s} className="flex items-center gap-1.5">
              <StageDot state={st} />
              <StageLabel stage={s} state={st} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
