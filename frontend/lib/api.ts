const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export type EmailStatus = 'pending' | 'processing' | 'awaiting_approval' | 'processed';

export type RunStatus = 'running' | 'paused' | 'done' | 'failed';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type Responsibility = 'landlord' | 'tenant' | 'shared' | 'unclear';

export type EmailCategory = 'maintenance' | 'lease_question' | 'not_our_problem' | 'emergency';

export type PlanAction = 'send_reply' | 'create_work_order' | 'call_tenant';

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

export interface QaResult {
  question: string;
  answer: string;
  citations: string[];
  reasoning: string;
}

export interface ClassifyOutput {
  category: EmailCategory;
}

export interface ExtractOutput {
  tenant_name: string | null;
  unit: string | null;
  address: string | null;
  issue_summary: string | null;
  severity: Severity | null;
  appliance_or_system: string | null;
}

export interface LeaseCheckOutput {
  lease_addresses_issue: boolean;
  responsibility: Responsibility;
  qa_results: QaResult[];
}

export interface PlanOutput {
  actions: PlanAction[];
}

export interface DraftOutput {
  draft: string;
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
  citation: string | null;
  original_email: string;
  draft: string | null;
  actions: PlanAction[];
}

export interface ExecuteOutput {
  actions_taken: PlanAction[];
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
  | (StepBase & { node_name: 'classify'; output: ClassifyOutput | null })
  | (StepBase & { node_name: 'extract'; output: ExtractOutput | null })
  | (StepBase & { node_name: 'lease_check'; output: LeaseCheckOutput | null })
  | (StepBase & { node_name: 'plan'; output: PlanOutput | null })
  | (StepBase & { node_name: 'draft'; output: DraftOutput | null })
  | (StepBase & { node_name: 'approval'; output: ApprovalCard | null })
  | (StepBase & { node_name: 'execute'; output: ExecuteOutput | null });

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    cache: 'no-store',
    headers: { 'content-type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${response.status} ${detail}`);
  }
  return (await response.json()) as T;
}

export function listEmails(): Promise<EmailListResponse> {
  return request<EmailListResponse>('/inbox');
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

export async function* streamRun(
  emailId: string,
  signal: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${BASE_URL}/runs/stream`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email_id: emailId }),
    cache: 'no-store',
    signal,
  });
  if (!response.ok || response.body === null) {
    throw new Error(`POST /runs/stream failed: ${response.status}`);
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
