"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { StatusPill, StatusPillProps } from "@/components/status-pill";
import { getCase, sendReminder, retryDuplicateSend, escalate, reply } from "@/lib/api";
import { CaseLogEntry, CollectionCase, CollectionOutcome } from "@/lib/types";
import FsmStageTrack from "./FsmStageTrack";
import BlockedBanner from "./BlockedBanner";
import { cn } from "@/lib/utils";

function agingVariant(bucket: string): StatusPillProps["variant"] {
  switch (bucket) {
    case "CURRENT":
    case "1-30":
      return "gray";
    case "31-60":
    case "61-90":
      return "amber";
    case "90+":
      return "red";
    default:
      return "gray";
  }
}

function formatMoney(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

type CaseWithLog = CollectionCase & { log: CaseLogEntry[] };

export default function CaseDrawer({
  caseId,
  onClose,
}: {
  caseId: string | null;
  onClose: () => void;
}) {
  const [data, setData] = useState<CaseWithLog | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<"en" | "es">("en");
  const [replyText, setReplyText] = useState("");
  const [actionPending, setActionPending] = useState(false);

  useEffect(() => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    getCase(caseId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load case"))
      .finally(() => setLoading(false));
  }, [caseId]);

  async function refetch() {
    if (!caseId) return;
    try {
      const fresh = await getCase(caseId);
      setData(fresh);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to refresh case");
    }
  }

  async function runAction<T>(fn: () => Promise<T>) {
    setActionPending(true);
    try {
      await fn();
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionPending(false);
    }
  }

  const open = caseId !== null;

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent side="right" className="w-[520px] sm:max-w-[520px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="font-mono text-[13px]">{caseId}</SheetTitle>
        </SheetHeader>

        <div className="flex-1 flex flex-col gap-4 px-4 pb-4">
          {loading && <div className="text-[13px] text-muted-foreground">Loading...</div>}
          {error && <div className="text-[13px] text-status-red-fg">{error}</div>}

          {data && (
            <>
              {/* Header zone */}
              <div className="border border-border-hairline rounded-[4px] p-3 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-[14px] font-medium text-foreground">
                    {data.debtor_name}
                  </span>
                  <StatusPill variant={agingVariant(data.aging_bucket)}>
                    {data.aging_bucket}
                  </StatusPill>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[12px]">
                  <div>
                    <div className="text-muted-foreground">Open Amount</div>
                    <div className="font-mono tabular-nums">{formatMoney(data.open_amount)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Dilution Reserve</div>
                    <div className="font-mono tabular-nums">
                      {formatMoney(data.dilution_reserve)}
                    </div>
                  </div>
                </div>
              </div>

              {/* FSM stage track */}
              <div className="border border-border-hairline rounded-[4px] p-3">
                <div className="text-[10px] font-mono uppercase tracking-wide text-muted-foreground mb-1">
                  FSM Stage
                </div>
                <FsmStageTrack stage={data.stage} />
              </div>

              {/* Action panel */}
              <div className="border border-border-hairline rounded-[4px] p-3 flex flex-col gap-2">
                <div className="text-[10px] font-mono uppercase tracking-wide text-muted-foreground">
                  Actions
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <Button
                    size="sm"
                    disabled={actionPending}
                    onClick={() => runAction(() => sendReminder(data.case_id, language))}
                  >
                    Send reminder
                  </Button>
                  <div className="flex items-center border border-border-hairline rounded-[4px] overflow-hidden">
                    {(["en", "es"] as const).map((lang) => (
                      <button
                        key={lang}
                        type="button"
                        onClick={() => setLanguage(lang)}
                        className={cn(
                          "px-2 py-1 text-[11px] font-mono uppercase transition-colors duration-150",
                          language === lang
                            ? "bg-accent text-accent-foreground"
                            : "bg-background text-muted-foreground hover:text-foreground"
                        )}
                      >
                        {lang}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={actionPending}
                    onClick={() => runAction(() => retryDuplicateSend(data.case_id))}
                  >
                    Retry identical send
                  </Button>
                  <span className="ml-2 text-[11px] text-muted-foreground align-middle">
                    demo: resends the last message verbatim to trigger the duplicate guard
                  </span>
                </div>
                <div>
                  <Button
                    size="sm"
                    variant="destructive"
                    disabled={actionPending}
                    onClick={() => runAction(() => escalate(data.case_id))}
                  >
                    Escalate
                  </Button>
                </div>
                <div className="flex flex-col gap-1.5 pt-1 border-t border-border-hairline">
                  <label className="text-[11px] text-muted-foreground">Debtor reply</label>
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    rows={2}
                    className="w-full border border-border-hairline rounded-[4px] px-2 py-1.5 text-[13px] bg-background resize-none focus:outline-none focus:border-accent transition-colors duration-150"
                    placeholder="Simulate an incoming debtor message..."
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={actionPending || !replyText.trim()}
                    onClick={() =>
                      runAction(async () => {
                        await reply(data.case_id, replyText);
                        setReplyText("");
                      })
                    }
                    className="self-start"
                  >
                    Submit
                  </Button>
                </div>
              </div>

              {/* Message log */}
              <div className="border border-border-hairline rounded-[4px] p-3 flex flex-col gap-2">
                <div className="text-[10px] font-mono uppercase tracking-wide text-muted-foreground">
                  Message Log
                </div>
                <div className="flex flex-col gap-2">
                  {data.log && data.log.length > 0 ? (
                    data.log.map((entry, i) => {
                      if (entry.role === "blocked") {
                        return (
                          <BlockedBanner
                            key={i}
                            outcome={entry.message as CollectionOutcome}
                          />
                        );
                      }
                      const isAgent = entry.role === "agent";
                      return (
                        <div
                          key={i}
                          className={cn(
                            "flex flex-col gap-0.5 max-w-[85%]",
                            isAgent ? "self-end items-end" : "self-start items-start"
                          )}
                        >
                          {entry.channel && (
                            <span className="text-[9px] font-mono uppercase text-muted-foreground">
                              {entry.channel}
                            </span>
                          )}
                          <div
                            className={cn(
                              "rounded-[4px] px-2.5 py-1.5 text-[12px]",
                              isAgent
                                ? "bg-status-blue-bg text-foreground"
                                : "bg-status-gray-bg text-foreground"
                            )}
                          >
                            {entry.message}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-[12px] text-muted-foreground">No messages yet.</div>
                  )}
                </div>
              </div>

              {/* Transition history */}
              <div className="border border-border-hairline rounded-[4px] p-3">
                <div className="text-[10px] font-mono uppercase tracking-wide text-muted-foreground mb-1.5">
                  Transition History
                </div>
                <div className="flex flex-col gap-1">
                  {data.history && data.history.length > 0 ? (
                    data.history.map((line, i) => (
                      <div
                        key={i}
                        className={cn(
                          "font-mono text-[11px]",
                          line.includes("BLOCKED") ? "text-status-red-fg" : "text-muted-foreground"
                        )}
                      >
                        {line}
                      </div>
                    ))
                  ) : (
                    <div className="text-[12px] text-muted-foreground">No history yet.</div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
