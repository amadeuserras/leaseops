import { SESSION_COOKIE, SESSION_HEADER } from '@/lib/session';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

const readSessionId = async (): Promise<string> => {
  if (typeof window === 'undefined') {
    const { cookies, headers } = await import('next/headers');
    const value =
      (await cookies()).get(SESSION_COOKIE)?.value ?? (await headers()).get(SESSION_HEADER);
    if (!value) {
      throw new Error('missing leaseops_session cookie');
    }
    return value;
  }
  const match = document.cookie.match(new RegExp(`(?:^|; )${SESSION_COOKIE}=([^;]*)`));
  const value = match?.[1];
  if (!value) {
    throw new Error('missing leaseops_session cookie');
  }
  return decodeURIComponent(value);
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const sessionId = await readSessionId();
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    cache: 'no-store',
    headers: {
      'content-type': 'application/json',
      'X-Session-Id': sessionId,
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${response.status} ${detail}`);
  }
  return (await response.json()) as T;
}

export type EmailStatus = 'pending' | 'processing' | 'awaiting_approval' | 'processed';

export type RunStatus = 'running' | 'paused' | 'done' | 'failed';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type Responsibility = 'landlord' | 'tenant' | 'shared' | 'unclear';

export type EmailCategory = 'maintenance' | 'lease_question' | 'not_our_problem' | 'emergency';

export type PlanAction = 'send_reply' | 'create_work_order';

export interface EmailResponse {
  id: string;
  sender: string;
  subject: string;
  body: string;
  received_at: string;
  status: EmailStatus;
  unit: string | null;
  severity: Severity | null;
  actions_taken: string[];
}

export interface EmailListResponse {
  items: EmailResponse[];
  agent_last_ran_at: string | null;
}

export interface LeaseQaTool {
  name: 'lease_qa';
  question: string;
  answer: string;
  citations: string[];
}

export interface SubmitVerdictTool {
  name: 'submit_verdict';
  lease_addresses_issue: boolean;
  responsibility: Responsibility;
}

export type LeaseCheckTool = LeaseQaTool | SubmitVerdictTool;

export interface LeaseCheckStep {
  reasoning: string;
  tool: LeaseCheckTool;
}

export interface ClassifyOutput {
  category: EmailCategory;
}

export interface ExtractOutput {
  tenant_name: string | null;
  unit: string | null;
  address: string | null;
  document_id: string | null;
  issue_summary: string | null;
  severity: Severity | null;
  appliance_or_system: string | null;
}

export interface LeaseCheckOutput {
  lease_addresses_issue: boolean;
  responsibility: Responsibility;
  lease_check_steps: LeaseCheckStep[];
}

export interface PlanOutput {
  actions: PlanAction[];
}

export interface DraftOutput {
  draft: string;
}

export interface LeaseEvidence {
  citation: string;
  question: string;
  document_id: string;
}

export interface ApprovalCard {
  email_id: string;
  category: string;
  severity: Severity | null;
  received_at: string;
  tenant_name: string | null;
  unit: string | null;
  address: string | null;
  issue_summary: string | null;
  appliance_or_system: string | null;
  responsibility: Responsibility | null;
  lease_evidence: LeaseEvidence | null;
  original_email: string;
  draft: string | null;
  actions: PlanAction[];
}

export interface ExecuteOutput {
  succeeded: boolean;
}

interface StepBase {
  id: string;
  run_id: string;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number | null;
  created_at: string;
}

export type StepResponse =
  | (StepBase & { node_name: 'classify'; output: ClassifyOutput })
  | (StepBase & { node_name: 'extract'; output: ExtractOutput })
  | (StepBase & { node_name: 'lease_check'; output: LeaseCheckOutput })
  | (StepBase & { node_name: 'plan'; output: PlanOutput })
  | (StepBase & { node_name: 'draft'; output: DraftOutput })
  | (StepBase & { node_name: 'approval'; output: ApprovalCard })
  | (StepBase & { node_name: 'execute'; output: ExecuteOutput });

export type NodeName = StepResponse['node_name'];

export interface RunStats {
  tokens: number;
  cost: number;
  elapsed: number;
  step_count: number;
}

export interface RunDetailResponse {
  email: EmailResponse;
  steps: StepResponse[];
  stats: RunStats;
}

export interface RunResponse {
  id: string;
  email_id: string;
  status: RunStatus;
  started_at: string;
  ended_at: string | null;
}

export interface LatestRunResponse {
  email_id: string | null;
}

export interface ApprovalRequestResponse extends ApprovalCard {
  run_id: string;
}

export interface ApprovalListResponse {
  items: ApprovalRequestResponse[];
}

export type StreamEvent =
  | { type: 'run_started'; run_id: string }
  | { type: 'node_started'; node: NodeName }
  | { type: 'node_finished'; node: NodeName; output: unknown }
  | { type: 'paused'; request: ApprovalCard }
  | { type: 'error'; message: string }
  | { type: 'run_finished'; status: RunStatus }
  | {
      type: 'tool_call';
      node: NodeName;
      tool: string;
      arguments: Record<string, unknown>;
      reasoning: string;
    }
  | {
      type: 'tool_result';
      node: NodeName;
      tool: string;
      result: unknown;
      is_error: boolean;
    }
  | {
      type: 'cost';
      node: NodeName;
      model: string;
      input_tokens: number;
      output_tokens: number;
      cost_usd: number;
    };

export type SessionLookup = 'ok' | 'missing' | 'error';

export async function lookupSession(sessionId: string): Promise<SessionLookup> {
  const response = await fetch(`${BASE_URL}/sessions/${encodeURIComponent(sessionId)}`, {
    cache: 'no-store',
  });
  if (response.ok) {
    return 'ok';
  }
  if (response.status === 404 || response.status === 422) {
    return 'missing';
  }
  return 'error';
}

export async function createSession(): Promise<string | null> {
  const created = await fetch(`${BASE_URL}/sessions`, {
    method: 'POST',
    cache: 'no-store',
  });
  if (!created.ok) {
    return null;
  }
  const body = (await created.json()) as { id: string };
  return body.id;
}

export function listEmails(): Promise<EmailListResponse> {
  return request<EmailListResponse>('/inbox');
}

export function getLatestRun(): Promise<LatestRunResponse> {
  return request<LatestRunResponse>('/runs/latest');
}

export function getRun(emailId: string): Promise<RunDetailResponse> {
  return request<RunDetailResponse>(`/runs/${emailId}`);
}

export function startRun(emailId: string): Promise<RunResponse> {
  return request<RunResponse>('/runs', {
    method: 'POST',
    body: JSON.stringify({ email_id: emailId }),
  });
}

async function* readRunStream(response: Response): AsyncGenerator<StreamEvent> {
  if (response.body === null) {
    throw new Error('stream response had no body');
  }
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;

      let boundary = buffer.indexOf('\n\n');
      while (boundary !== -1) {
        const record = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const payload = record
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trim())
          .join('');
        if (payload) yield JSON.parse(payload) as StreamEvent;
        boundary = buffer.indexOf('\n\n');
      }
    }
  } finally {
    reader.cancel().catch(() => {});
  }
}

export async function* streamRun(
  emailId: string,
  signal: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const sessionId = await readSessionId();
  const response = await fetch(`${BASE_URL}/runs/stream`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'X-Session-Id': sessionId,
    },
    body: JSON.stringify({ email_id: emailId }),
    cache: 'no-store',
    signal,
  });
  if (!response.ok) {
    throw new Error(`POST /runs/stream failed: ${response.status}`);
  }
  yield* readRunStream(response);
}

export async function* streamRerun(
  emailId: string,
  signal: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const sessionId = await readSessionId();
  const response = await fetch(`${BASE_URL}/runs/rerun/stream`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'X-Session-Id': sessionId,
    },
    body: JSON.stringify({ email_id: emailId }),
    cache: 'no-store',
    signal,
  });
  if (!response.ok) {
    throw new Error(`POST /runs/rerun/stream failed: ${response.status}`);
  }
  yield* readRunStream(response);
}

export function listApprovals(): Promise<ApprovalListResponse> {
  return request<ApprovalListResponse>('/approvals');
}

export function approveRun(runId: string): Promise<RunResponse> {
  return request<RunResponse>(`/approvals/${runId}/approve`, {
    method: 'POST',
  });
}

export function rejectRun(runId: string): Promise<RunResponse> {
  return request<RunResponse>(`/approvals/${runId}/reject`, { method: 'POST' });
}

// Mocks — everything below has no backend endpoint yet

export interface BuildInfo {
  evalsPassing: number;
  evalsTotal: number;
  version: string;
  build: string;
}

export function getBuildInfo(): BuildInfo {
  return {
    evalsPassing: 42,
    evalsTotal: 42,
    version: 'v0.4.2-beta',
    build: '8f21a0c',
  };
}

export function senderDisplayName(sender: string): string {
  const local = sender.split('@')[0] ?? sender;
  return (
    local
      .split(/[._-]+/)
      .filter(Boolean)
      .map((part) =>
        part.length <= 2 ? part.toUpperCase() : part.charAt(0).toUpperCase() + part.slice(1),
      )
      .join(' ') || sender
  );
}
