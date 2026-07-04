import { CollectionOutcome } from "@/lib/types";

const EXPLANATIONS: Partial<Record<CollectionOutcome, string>> = {
  BLOCKED_DUPLICATE_MESSAGE:
    "Identical message to same debtor - refused by FSM guard.",
  BLOCKED_ESCALATION_GATE:
    "Escalation requires a minimum number of unanswered outreaches - threshold not met.",
  BLOCKED_ILLEGAL_TRANSITION:
    "Requested transition is not in the allowed transition table - refused.",
  BLOCKED_MAX_ACTIONS:
    "Case has hit its action cap - refused to prevent runaway loops.",
  BLOCKED_TERMINAL:
    "Case is in a terminal stage - no further transitions are possible.",
};

export default function BlockedBanner({
  outcome,
  message,
}: {
  outcome: CollectionOutcome;
  message?: string;
}) {
  const explanation = message ?? EXPLANATIONS[outcome] ?? "Action refused by FSM guard.";
  return (
    <div className="w-full border border-status-red-fg/30 bg-status-red-bg px-3 py-2 rounded-[4px]">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-wide text-status-red-fg">
          {outcome}
        </span>
      </div>
      <div className="text-[12px] text-status-red-fg mt-0.5">{explanation}</div>
    </div>
  );
}
