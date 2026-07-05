import {
  AuditEntry,
  CaseActionResult,
  CaseLogEntry,
  CollectionCase,
  CovenantRow,
  ConcentrationRow,
  AgingDistribution,
  KPIs,
  MatchTier,
  Payment,
  PortfolioSummary,
  ResetResult,
  RunResult,
  SystemConfig,
} from "./types";

export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8600";

// Helper: fetch with type safety and error handling
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API}${path}`;
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new Error(`Can't reach the POLARIS engine at ${API}. Is the API running?`);
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status}: ${text}`);
  }
  return response.json();
}

// System endpoints

export async function health(): Promise<void> {
  return req("/health");
}

export async function getConfig(): Promise<SystemConfig> {
  return req("/api/config");
}

export async function reset(): Promise<ResetResult> {
  return req("/api/reset", { method: "POST" });
}

// Reconciliation endpoints

export async function runMatching(): Promise<RunResult> {
  return req("/api/reconciliation/run", { method: "POST" });
}

export async function getPayments(tier?: MatchTier): Promise<Payment[]> {
  const params = tier ? `?tier=${tier}` : "";
  return req(`/api/reconciliation/payments${params}`);
}

export async function approvePayment(id: string): Promise<AuditEntry> {
  return req(`/api/reconciliation/payments/${id}/approve`, { method: "POST" });
}

export async function rejectPayment(id: string, reason: string): Promise<AuditEntry> {
  return req(`/api/reconciliation/payments/${id}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
}

export async function approveFirstCandidate(id: string): Promise<AuditEntry> {
  return req(`/api/reconciliation/payments/${id}/approve-first-candidate`, {
    method: "POST",
  });
}

export async function getAuditTrail(q?: string): Promise<AuditEntry[]> {
  const params = q ? `?q=${encodeURIComponent(q)}` : "";
  return req(`/api/reconciliation/audit-trail${params}`);
}

// Collections endpoints

export async function buildQueue(): Promise<CollectionCase[]> {
  return req("/api/collections/build-queue", { method: "POST" });
}

export async function getCases(): Promise<CollectionCase[]> {
  return req("/api/collections/cases");
}

export async function getCase(id: string): Promise<CollectionCase & { log: CaseLogEntry[] }> {
  return req(`/api/collections/cases/${id}`);
}

export async function sendReminder(
  id: string,
  language: string = "en"
): Promise<CaseActionResult> {
  return req(`/api/collections/cases/${id}/send-reminder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ language }),
  });
}

export async function retryDuplicateSend(id: string): Promise<CaseActionResult> {
  return req(`/api/collections/cases/${id}/retry-duplicate-send`, {
    method: "POST",
  });
}

export async function escalate(id: string): Promise<CaseActionResult> {
  return req(`/api/collections/cases/${id}/escalate`, {
    method: "POST",
  });
}

export async function reply(
  id: string,
  text: string,
  promiseDate?: string
): Promise<CaseActionResult> {
  const body: { text: string; promise_date?: string } = { text };
  if (promiseDate) {
    body.promise_date = promiseDate;
  }
  return req(`/api/collections/cases/${id}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// Portfolio endpoints

export async function getSummary(): Promise<PortfolioSummary> {
  return req("/api/portfolio/summary");
}

export async function getCovenants(): Promise<CovenantRow[]> {
  return req("/api/portfolio/covenants");
}

export async function getConcentration(): Promise<ConcentrationRow[]> {
  return req("/api/portfolio/concentration");
}

export async function getAging(): Promise<AgingDistribution> {
  return req("/api/portfolio/aging");
}

export function dataTapeCsvUrl(): string {
  return `${API}/api/portfolio/data-tape.csv`;
}
