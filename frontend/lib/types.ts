// Reconciliation Types

export type MatchTier = "AUTO_APPLY" | "AUTO_APPLY_LOGGED" | "REVIEW" | "EXCEPTION";

export interface MatchCandidate {
  invoice_id: string;
  open_amount: number;
}

export interface Payment {
  id: string;
  payer: string;
  amount: number;
  value_date: string;
  memo: string;
  reference: string;
  match_tier: MatchTier | null;
  confidence: number | null;
  matched_invoice_ids: string[];
  match_reason: string | null;
  applied: boolean;
  matched_invoice_candidates: MatchCandidate[];
}

export interface KPIs {
  auto_match_rate: number;
  auto_applied: number;
  needs_review: number;
  exceptions: number;
}

export interface RunResult {
  kpis: KPIs;
  payments: Payment[];
}

export interface AuditEntry {
  timestamp: string;
  actor: string;
  payment_id: string;
  invoice_ids: string[];
  tier: string;
  confidence: number | null;
  reason: string | null;
}

// Collections Types

export type CollectionStage =
  | "PRIORITIZE"
  | "OUTREACH"
  | "AWAIT_RESPONSE"
  | "PROMISE_TO_PAY"
  | "DISPUTE_INTAKE"
  | "ESCALATE"
  | "RESOLVED"
  | "WRITTEN_OFF";

export type CollectionOutcome =
  | "OK"
  | "BLOCKED_ILLEGAL_TRANSITION"
  | "BLOCKED_DUPLICATE_MESSAGE"
  | "BLOCKED_ESCALATION_GATE"
  | "BLOCKED_MAX_ACTIONS"
  | "BLOCKED_TERMINAL";

export interface CollectionCase {
  case_id: string;
  invoice_id: string;
  debtor_id: string;
  debtor_name: string;
  open_amount: number;
  factored_amount?: number;
  aging_bucket: string;
  priority_score: number;
  stage: CollectionStage;
  outreach_count: number;
  total_actions: number;
  channel_history: string[];
  next_channel: string;
  dilution_reserve: number;
  history?: string[];
}

export interface CaseLogEntry {
  role: "agent" | "debtor" | "blocked";
  message: string;
  channel?: string | null;
  ts: string;
}

export interface CaseActionResult {
  outcome: CollectionOutcome | null;
  message?: string;
  channel?: string | null;
  case: CollectionCase;
}

// Portfolio Types

export type AgingBucketKey = "CURRENT" | "1-30" | "31-60" | "61-90" | "90+";

export interface AgingBucketData {
  count: number;
  amount: number;
  pct_of_open_ar: number;
}

export interface AgingDistribution {
  [key: string]: AgingBucketData | number | string; // also has "pct_over_60" and "status"
  "CURRENT": AgingBucketData;
  "1-30": AgingBucketData;
  "31-60": AgingBucketData;
  "61-90": AgingBucketData;
  "90+": AgingBucketData;
  pct_over_60: number;
  status: "COMPLIANT" | "WARNING";
}

export interface ConcentrationRow {
  debtor_id: string;
  debtor_name: string;
  open_amount: number;
  pct_of_open_ar: number;
  status: "COMPLIANT" | "WARNING";
}

export interface CovenantRow {
  metric: string;
  current: number | string;
  threshold: string;
  status: "COMPLIANT" | "WARNING";
}

export interface PortfolioSummary {
  open_ar_total: number;
  funds_employed: number;
}

// System Types

export interface SystemConfig {
  demo_mode: boolean;
}

export interface ResetResult {
  payments: number;
  invoices_open: number;
}
