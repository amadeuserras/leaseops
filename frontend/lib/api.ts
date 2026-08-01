const BASE_PATH = process.env.NEXT_PUBLIC_LEASEOPS_API_URL;

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export type EmailStatus = 'pending' | 'processed' | 'escalated';

export type Email = {
  id: string;
  sender: string;
  subject: string;
  body: string;
  received_at: string;
  status: EmailStatus;
};

export type RunStatus = 'running' | 'paused' | 'done' | 'failed';

export type Run = {
  id: string;
  email_id: string;
  status: RunStatus;
  started_at: string;
  ended_at: string | null;
};

export type PlanAction = 'create_work_order' | 'send_reply' | 'call_tenant';

export type ApprovalRequest = {
  email_id: string;
  actions: PlanAction[];
  draft: string | null;
  tenant_name: string | null;
  unit: string | null;
  issue_summary: string | null;
};

export type PendingApproval = ApprovalRequest & { run_id: string };

export type StreamEvent =
  | { type: 'run_started'; run_id: string }
  | { type: 'node_started'; node: string }
  | { type: 'node_finished'; node: string; output: Record<string, unknown> | null }
  | {
      type: 'tool_call';
      node: string;
      tool: string;
      arguments: Record<string, unknown>;
      /**
       * Why the agent reached for this tool, shown above the call in the trace.
       * MOCK — `ToolCallEvent` does not carry this yet, so it is backfilled in
       * `parseEvent`. Delete `mockedReasoning` once the backend emits it.
       */
      reasoning: string;
    }
  | { type: 'tool_result'; node: string; tool: string; result: unknown; is_error: boolean }
  | {
      type: 'cost';
      node: string;
      model: string;
      input_tokens: number;
      output_tokens: number;
      cost_usd: number;
    }
  | { type: 'paused'; request: ApprovalRequest }
  | { type: 'run_finished'; status: RunStatus }
  | { type: 'error'; message: string };

const errorMessage = async (response: Response): Promise<string> => {
  try {
    const body: unknown = await response.json();
    if (body !== null && typeof body === 'object' && 'detail' in body) {
      return String((body as { detail: unknown }).detail);
    }
  } catch {}
  return `${response.status} ${response.statusText}`;
};

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${BASE_PATH}${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...init?.headers },
  });
  if (!response.ok) throw new ApiError(response.status, await errorMessage(response));
  return (await response.json()) as T;
};

const postJson = async <T>(path: string, payload: unknown): Promise<T> =>
  request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

export const listEmails = async (status?: EmailStatus): Promise<Email[]> => {
  const query = status ? `?status=${status}` : '';
  const data = await request<{ items: Email[] }>(`/inbox${query}`);
  return data.items;
};

export const getEmail = async (emailId: string): Promise<Email> =>
  request<Email>(`/inbox/${emailId}`);

type StreamRunOptions = {
  emailId: string;
  onEvent: (event: StreamEvent) => void;
  signal?: AbortSignal;
};

const parseEvent = (payload: string): StreamEvent => {
  const raw = JSON.parse(payload) as Record<string, unknown>;
  if (raw.type === 'tool_call' && typeof raw.reasoning !== 'string') {
    return { ...raw, reasoning: mockedReasoning(String(raw.tool)) } as unknown as StreamEvent;
  }
  return raw as unknown as StreamEvent;
};

export const streamRun = async ({ emailId, onEvent, signal }: StreamRunOptions): Promise<void> => {
  const response = await fetch(`${BASE_PATH}/runs/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ email_id: emailId }),
    signal,
  });

  if (!response.ok) throw new ApiError(response.status, await errorMessage(response));
  if (response.body === null) throw new ApiError(response.status, 'trace stream had no body');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const emit = (frame: string) => {
    const line = frame.split('\n').find((candidate) => candidate.startsWith('data:'));
    if (line === undefined) return;
    onEvent(parseEvent(line.slice(5).trim()));
  };

  let chunk = await reader.read();
  while (!chunk.done) {
    buffer += decoder.decode(chunk.value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';
    frames.forEach(emit);
    chunk = await reader.read();
  }
  if (buffer.trim() !== '') emit(buffer);
};

export type StepRecord = {
  id: string;
  run_id: string;
  node_name: string;
  output: Record<string, unknown> | null;
  tokens: number | null;
  cost_usd: number | null;
  created_at: string;
};

export const listEmailSteps = async (emailId: string): Promise<StepRecord[]> => {
  const data = await request<{ items: StepRecord[] }>(`/runs/${emailId}/steps`);
  return data.items;
};

export const listApprovals = async (): Promise<PendingApproval[]> => {
  const data = await request<{ items: PendingApproval[] }>('/approvals');
  return data.items;
};

export const approveRun = async (runId: string): Promise<Run> =>
  postJson<Run>(`/approvals/${runId}/approve`, {});

export const rejectRun = async (runId: string, rejectionReason: string): Promise<Run> =>
  postJson<Run>(`/approvals/${runId}/reject`, { rejection_reason: rejectionReason });

/* ========================================================================== */
/* MOCKED DATA — no API endpoint exists for any of the below                   */
/* ========================================================================== */

/**
 * MOCK — hardcoded stand-in for the `reasoning` field on `tool_call` events.
 *
 * The trace shows a sentence above each tool call explaining why the agent
 * reached for it. `leaseops.agent.events.ToolCallEvent` has no such field, so
 * every call gets this canned line per tool. Once the backend emits a real
 * `reasoning`, `parseEvent` passes it straight through and this can go.
 */
const mockedReasoning = (tool: string): string => {
  const byTool: Record<string, string> = {
    lease_qa: 'Checking what the lease says about this before responding.',
    tenant_lookup: 'Resolving the sender to a tenant record before writing anything.',
    work_order_create: 'Responsibility is established — opening the work order.',
    send_reply: 'Reply approved — queueing it in the outbox.',
  };
  return byTool[tool] ?? `Calling ${tool}.`;
};

export type Tenant = {
  email: string;
  name: string;
  address: string;
  unit: string | null;
};

/**
 * MOCK — the API exposes no `/tenants` endpoint, so the inbox has no way to
 * turn a sender address into a display name and unit. Mirrors
 * `backend/seed_data/tenants.json`; replace with a real fetch once the
 * endpoint lands.
 */
export const listTenants = async (): Promise<Tenant[]> =>
  Promise.resolve([
    {
      email: 'deshawn.johnson@example.com',
      name: 'DeShawn Johnson',
      address: '1142 Sunset Ridge Drive, Los Angeles, CA 90026',
      unit: '5',
    },
    {
      email: 'yuna.kim@example.com',
      name: 'Yuna Kim',
      address: '1142 Sunset Ridge Drive, Los Angeles, CA 90026',
      unit: '5',
    },
    {
      email: 'maria.vega@example.com',
      name: 'Maria Elena Vega',
      address: '884 Pelican Court, Oxnard, CA 93035',
      unit: null,
    },
    {
      email: 'james.whitfield@example.com',
      name: 'James Whitfield',
      address: '884 Pelican Court, Oxnard, CA 93035',
      unit: null,
    },
    {
      email: 'priya.nadkarni@example.com',
      name: 'Priya Nadkarni',
      address: '77 Larkspur Lane, Port Marlow, CA 94066',
      unit: '3C',
    },
    {
      email: 'daniel.osei@example.com',
      name: 'Daniel Osei',
      address: '77 Larkspur Lane, Port Marlow, CA 94066',
      unit: '3C',
    },
    {
      email: 'soojin.park@example.com',
      name: 'Soo-Jin Park',
      address: '302 Fern Valley Road, Ashford Heights, OR 97201',
      unit: '8B',
    },
    {
      email: 'kevin.chen@example.com',
      name: 'Kevin Chen',
      address: '302 Fern Valley Road, Ashford Heights, OR 97201',
      unit: '8B',
    },
    {
      email: 'astrid.lindqvist@example.com',
      name: 'Astrid Lindqvist',
      address: '3712 Lake Harriet Pkwy, Minneapolis, Minnesota',
      unit: '2B',
    },
    {
      email: 'ravi.patel@example.com',
      name: 'Ravi Patel',
      address: '3712 Lake Harriet Pkwy, Minneapolis, Minnesota',
      unit: '2B',
    },
    {
      email: 'chukwuemeka.okonkwo@example.com',
      name: 'Chukwuemeka Okonkwo',
      address: '1845 Selby Avenue, Saint Paul, MN 55104',
      unit: null,
    },
    {
      email: 'sara.berg@example.com',
      name: 'Sara Berg',
      address: '1845 Selby Avenue, Saint Paul, MN 55104',
      unit: null,
    },
    {
      email: 'carlos.morales@example.com',
      name: 'Carlos Morales',
      address: '2214 Brentwood Street, Austin, TX 78757',
      unit: null,
    },
    {
      email: 'isabel.reyes@example.com',
      name: 'Isabel Reyes',
      address: '2214 Brentwood Street, Austin, TX 78757',
      unit: null,
    },
    {
      email: 'darnell.washington@example.com',
      name: 'Darnell Washington',
      address: '5522 Westheimer Road, Houston, TX 77056',
      unit: '14C',
    },
    {
      email: 'keisha.price@example.com',
      name: 'Keisha Price',
      address: '5522 Westheimer Road, Houston, TX 77056',
      unit: '14C',
    },
  ]);

export type ApprovalCategory = 'emergency' | 'maintenance' | 'lease_question';
export type ApprovalSeverity = 'critical' | 'high' | 'medium' | 'low';
export type ApprovalResponsibility = 'landlord' | 'tenant';
export type ApprovalAction = 'call_tenant' | 'send_reply' | 'create_work_order' | 'mark_complete';

export type ApprovalQueueItem = {
  run_id: string;
  email_id: string;
  category: ApprovalCategory;
  severity: ApprovalSeverity;
  received_at: string;
  tenant_name: string;
  unit: string | null;
  address: string;
  issue_summary: string;
  issue_category: string;
  responsibility: ApprovalResponsibility | null;
  lease_citation: string | null;
  original_email: string;
  draft: string;
  actions: ApprovalAction[];
};

export type ApprovalQueueResponse = {
  items: ApprovalQueueItem[];
  cleared_today: number;
};

/**
 * MOCK — no endpoint exposes the triage queue the Approvals page needs
 * (category/severity/responsibility, the original email, and which actions
 * apply to each item). Replace with a real `GET /approvals/queue` once it
 * exists; the shape above (`ApprovalQueueResponse`) is the intended contract.
 */
export const listApprovalQueue = async (): Promise<ApprovalQueueResponse> =>
  Promise.resolve({
    cleared_today: 9,
    items: [
      {
        run_id: 'a1b2c3d4-0001-4a00-9c00-000000000001',
        email_id: 'e1b2c3d4-0001-4a00-9c00-000000000001',
        category: 'emergency',
        severity: 'critical',
        received_at: new Date(Date.now() - 4 * 60_000).toISOString(),
        tenant_name: 'DeShawn Johnson',
        unit: '5',
        address: '1142 Sunset Ridge Drive, Los Angeles, CA 90026',
        issue_summary: 'Gas smell in the kitchen, worsening since this morning',
        issue_category: 'Gas / utilities',
        responsibility: null,
        lease_citation: null,
        original_email:
          "There's a strong smell of gas in the kitchen — it was faint when I woke up and it's much worse now. I've opened the windows but it isn't clearing. What should I do?",
        draft:
          "DeShawn — please leave the building immediately and do not switch anything electrical on or off on your way out. Once you're outside, call the gas emergency line on 0800 111 999.\n\nI'm contacting our on-call engineer now and will call you within the next few minutes.",
        actions: ['call_tenant', 'send_reply'],
      },
      {
        run_id: 'a1b2c3d4-0002-4a00-9c00-000000000002',
        email_id: 'e1b2c3d4-0002-4a00-9c00-000000000002',
        category: 'maintenance',
        severity: 'medium',
        received_at: new Date(Date.now() - 22 * 60_000).toISOString(),
        tenant_name: 'Astrid Lindqvist',
        unit: '2B',
        address: '3712 Lake Harriet Pkwy, Minneapolis, Minnesota',
        issue_summary: 'Blocked kitchen sink after tenant used drain cleaner',
        issue_category: 'Plumbing',
        responsibility: 'landlord',
        lease_citation: 'lake-harriet-lindqvist §7.2',
        original_email:
          "The kitchen sink has been draining slowly for a few days and now it's completely blocked. I tried a bottle of drain cleaner last night and it didn't help. Can someone come look at it?",
        draft:
          "Hi Astrid, thanks for flagging this. Clearing a blocked drain falls to us as landlord under §7.2 of your lease, so we'll cover the callout. One note for next time — pouring drain cleaner can damage the trap, so please hold off on that and let us handle it.\n\nI can get a plumber out tomorrow between 10am and 2pm. Does that window work for you?",
        actions: ['send_reply', 'create_work_order', 'mark_complete'],
      },
      {
        run_id: 'a1b2c3d4-0003-4a00-9c00-000000000003',
        email_id: 'e1b2c3d4-0003-4a00-9c00-000000000003',
        category: 'maintenance',
        severity: 'high',
        received_at: new Date(Date.now() - 60 * 60_000).toISOString(),
        tenant_name: 'Darnell Washington',
        unit: '14C',
        address: '5522 Westheimer Road, Houston, TX 77056',
        issue_summary: 'Water through bedroom ceiling when the flat above runs a bath',
        issue_category: 'Plumbing / structural',
        responsibility: 'landlord',
        lease_citation: 'westheimer-washington §7.1',
        original_email:
          "Every time the flat above runs a bath, water comes through my bedroom ceiling. There's a brown stain spreading and it dripped onto the bed last night.",
        draft:
          "Hi Darnell, this is a structural plumbing issue and sits with us under §7.1. I've flagged it as urgent and we'll have someone inspect both units today — we may need brief access to the flat above as well.\n\nPlease move anything valuable out from under the affected area in the meantime.",
        actions: ['send_reply', 'create_work_order', 'mark_complete'],
      },
      {
        run_id: 'a1b2c3d4-0004-4a00-9c00-000000000004',
        email_id: 'e1b2c3d4-0004-4a00-9c00-000000000004',
        category: 'maintenance',
        severity: 'low',
        received_at: new Date(Date.now() - 2 * 60 * 60_000).toISOString(),
        tenant_name: 'Soo-Jin Park',
        unit: '8B',
        address: '302 Fern Valley Road, Ashford Heights, OR 97201',
        issue_summary: 'Cracked toilet seat, believes it broke from normal use',
        issue_category: 'Fixtures',
        responsibility: 'tenant',
        lease_citation: 'fern-valley-park §7.4',
        original_email:
          'The toilet seat in the main bathroom has cracked right along the hinge. Nothing unusual happened, it just went. Is that something you replace?',
        draft:
          "Hi Soo-Jin, this one falls to you under the lease (§7.4 covers tenant fixtures), but we can arrange it through our handyman and bill it at cost — around $60 including fitting — if that's easier than sourcing it yourself. Just let me know which you'd prefer.",
        actions: ['send_reply', 'mark_complete'],
      },
      {
        run_id: 'a1b2c3d4-0005-4a00-9c00-000000000005',
        email_id: 'e1b2c3d4-0005-4a00-9c00-000000000005',
        category: 'lease_question',
        severity: 'low',
        received_at: new Date(Date.now() - 3 * 60 * 60_000).toISOString(),
        tenant_name: 'Priya Nadkarni',
        unit: '3C',
        address: '77 Larkspur Lane, Port Marlow, CA 94066',
        issue_summary: 'Asking whether she can repaint the living room light blue',
        issue_category: 'Alterations',
        responsibility: 'tenant',
        lease_citation: 'larkspur-nadkarni §6.1',
        original_email:
          "Quick question — am I allowed to repaint the living room? I was thinking a light blue. Happy to paint it back before I move out if that's needed.",
        draft:
          "Hi Priya, the lease requires the landlord's prior written consent before painting (§6.1), so we'd need to approve the colour before you start. Happy to put that request in for you — just confirm the exact shade and whether you'll restore the original on move-out.",
        actions: ['send_reply', 'mark_complete'],
      },
      {
        run_id: 'a1b2c3d4-0006-4a00-9c00-000000000006',
        email_id: 'e1b2c3d4-0006-4a00-9c00-000000000006',
        category: 'maintenance',
        severity: 'low',
        received_at: new Date(Date.now() - 5 * 60 * 60_000).toISOString(),
        tenant_name: 'Maria Elena Vega',
        unit: null,
        address: '884 Pelican Court, Oxnard, CA 93035',
        issue_summary: 'Porch light has been flickering for a week',
        issue_category: 'Electrical',
        responsibility: 'landlord',
        lease_citation: 'pelican-vega §7.2',
        original_email:
          "The porch light outside my door has been flickering on and off for about a week. It's not urgent but it's getting annoying — could someone take a look?",
        draft:
          "Hi Maria, thanks for the heads up — exterior lighting is on us under §7.2, so I'll get an electrician scheduled. It's not urgent so I've queued it for our next routine visit, but let me know if it starts acting up more and I'll move it up.",
        actions: ['send_reply', 'create_work_order', 'mark_complete'],
      },
    ],
  });

export type BuildInfo = {
  evalsPassing: number;
  evalsTotal: number;
  version: string;
  commit: string;
};

/**
 * MOCK — the sidebar footer in the design shows eval health and a build stamp.
 * `/evals` is postponed (SPEC Ch. 8) and no build endpoint exists.
 */
export const getBuildInfo = async (): Promise<BuildInfo> =>
  Promise.resolve({
    evalsPassing: 42,
    evalsTotal: 42,
    version: 'v0.4.2-beta',
    commit: '8f21a0c',
  });
