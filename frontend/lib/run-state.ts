/** Turns live stream events and saved run data into the timeline the UI draws. */
import {
  type ApprovalCard,
  type ClassifyOutput,
  type DraftOutput,
  type EmailStatus,
  type ExecuteOutput,
  type ExtractOutput,
  type LeaseCheckOutput,
  type NodeName,
  type PlanOutput,
  type RunDetailResponse,
  type RunStats,
  type StepResponse,
  type StreamEvent,
} from './api';
import { fmtCost, hum, humArgs, humVal } from './format';

export type TimelineStatus = 'pending' | 'running' | 'completed' | 'paused';

export type RunPhase = 'idle' | 'running' | 'paused' | 'done' | 'failed';

export interface ToolCall {
  tool: string;
  reasoning: string | null;
  question: string | null;
  argsText: string | null;
  answer: string | null;
  citations: string[];
  done: boolean;
  isError: boolean;
}

export interface Usage {
  model: string;
  inputTokens: number;
  outputTokens: number;
  cost: number;
}

export interface TimelineStep {
  key: string;
  node: NodeName;
  status: TimelineStatus;
  usage: Usage | null;
  at: number | null;
  output: unknown;
  calls: ToolCall[];
  note: string | null;
}

export interface RunState {
  runId: string | null;
  phase: RunPhase;
  live: boolean;
  steps: TimelineStep[];
  stats: RunStats;
  approval: ApprovalCard | null;
  error: string | null;
}

const EMPTY_STATS: RunStats = { tokens: 0, cost: 0, elapsed: 0, step_count: 0 };

export function emptyRunState(): RunState {
  return {
    runId: null,
    phase: 'idle',
    live: false,
    steps: [],
    stats: EMPTY_STATS,
    approval: null,
    error: null,
  };
}

const CITATION_RE = /\s*\[([a-z0-9-]+) (§[^\]]+|p\d+(?:\(\d+\))?)\]/g;

function splitCitations(text: string): { text: string; citations: string[] } {
  const citations: string[] = [];
  const stripped = text.replace(CITATION_RE, (_match, doc: string, ref: string) => {
    const id = `${doc} ${ref}`;
    if (!citations.includes(id)) citations.push(id);
    return '';
  });
  return { text: stripped.trim(), citations };
}

function unbracket(citation: string): string {
  return citation.replace(/^\[|\]$/g, '');
}

function verdictCall(output: LeaseCheckOutput): ToolCall {
  return {
    tool: 'submit_verdict',
    reasoning: output.reasoning || null,
    question: null,
    argsText: `lease_addresses_issue: ${output.lease_addresses_issue}, responsibility: "${output.responsibility}"`,
    answer: null,
    citations: [],
    done: true,
    isError: false,
  };
}

function qaCalls(output: LeaseCheckOutput): ToolCall[] {
  return output.qa_results.map((qa) => {
    const { text } = splitCitations(qa.answer);
    return {
      tool: 'lease_qa',
      reasoning: qa.reasoning || null,
      question: qa.question,
      argsText: null,
      answer: text,
      citations: qa.citations.map(unbracket),
      done: true,
      isError: false,
    };
  });
}

export function fromRunDetail(data: RunDetailResponse): RunState {
  const awaiting = data.email.status === 'awaiting_approval';
  const executed = data.steps.some((step) => step.node_name === 'execute');

  const steps = data.steps.map<TimelineStep>((step) => ({
    key: step.id,
    node: step.node_name,
    status: step.node_name === 'approval' && awaiting ? 'paused' : 'completed',
    usage:
      step.model === null
        ? null
        : {
            model: step.model,
            inputTokens: step.input_tokens ?? 0,
            outputTokens: step.output_tokens ?? 0,
            cost: step.cost_usd ?? 0,
          },
    at: null,
    output: step.output,
    calls: leaseCallsFor(step),
    note: step.node_name === 'approval' ? gateNote(awaiting, executed) : null,
  }));

  const approvalStep = data.steps.find((step) => step.node_name === 'approval');

  return {
    runId: data.steps[0]?.run_id ?? null,
    phase: awaiting ? 'paused' : steps.length > 0 ? 'done' : 'idle',
    live: false,
    steps,
    stats: data.stats,
    approval: (approvalStep?.output as ApprovalCard | null) ?? null,
    error: null,
  };
}

function leaseCallsFor(step: StepResponse): ToolCall[] {
  if (step.node_name !== 'lease_check' || step.output === null) return [];
  return [...qaCalls(step.output), verdictCall(step.output)];
}

function gateNote(awaiting: boolean, executed: boolean): string {
  if (awaiting) return 'Waiting for human approval';
  return executed ? 'Approved' : 'Rejected';
}

function replaceStep(
  steps: TimelineStep[],
  node: NodeName,
  update: (step: TimelineStep) => TimelineStep,
): TimelineStep[] {
  const index = steps.findLastIndex((step) => step.node === node);
  if (index === -1) return steps;
  return steps.map((step, i) => (i === index ? update(step) : step));
}

export function applyStreamEvent(state: RunState, event: StreamEvent, elapsed: number): RunState {
  switch (event.type) {
    case 'run_started':
      return { ...state, runId: event.run_id, phase: 'running', live: true };

    case 'node_started': {
      const steps = [
        ...state.steps,
        {
          key: `${event.node}-${state.steps.length}`,
          node: event.node,
          status: 'running' as const,
          usage: null,
          at: null,
          output: null,
          calls: [],
          note: null,
        },
      ];
      return {
        ...state,
        steps,
        stats: { ...state.stats, step_count: steps.length },
      };
    }

    case 'cost': {
      const steps = replaceStep(state.steps, event.node, (step) => ({
        ...step,
        usage: {
          model: event.model,
          inputTokens: (step.usage?.inputTokens ?? 0) + event.input_tokens,
          outputTokens: (step.usage?.outputTokens ?? 0) + event.output_tokens,
          cost: (step.usage?.cost ?? 0) + event.cost_usd,
        },
      }));
      return {
        ...state,
        steps,
        stats: {
          ...state.stats,
          tokens: state.stats.tokens + event.input_tokens + event.output_tokens,
          cost: state.stats.cost + event.cost_usd,
        },
      };
    }

    case 'tool_call': {
      const steps = replaceStep(state.steps, event.node, (step) => ({
        ...step,
        calls: [
          ...step.calls,
          {
            tool: event.tool,
            reasoning: event.reasoning || null,
            question: (event.arguments.question as string | undefined) ?? null,
            argsText: null,
            answer: null,
            citations: [],
            done: false,
            isError: false,
          },
        ],
      }));
      return { ...state, steps };
    }

    case 'tool_result': {
      const raw = typeof event.result === 'string' ? event.result : null;
      const parsed = raw === null ? null : splitCitations(raw);
      const steps = replaceStep(state.steps, event.node, (step) => ({
        ...step,
        calls: step.calls.map((call, i) =>
          i === step.calls.length - 1
            ? {
                ...call,
                answer: parsed?.text ?? null,
                citations: parsed?.citations ?? [],
                done: true,
                isError: event.is_error,
              }
            : call,
        ),
      }));
      return { ...state, steps };
    }

    case 'node_finished': {
      const steps = replaceStep(state.steps, event.node, (step) => ({
        ...step,
        status: 'completed' as const,
        output: event.output,
        at: elapsed,
        calls:
          event.node === 'lease_check' && event.output
            ? [...step.calls, verdictCall(event.output as LeaseCheckOutput)]
            : step.calls,
      }));
      return { ...state, steps };
    }

    case 'paused': {
      const steps = state.steps.map((step, i) =>
        i === state.steps.length - 1
          ? {
              ...step,
              status: 'paused' as const,
              output: event.request,
              note: 'Waiting for human approval',
            }
          : step,
      );
      return { ...state, steps, approval: event.request, phase: 'paused' };
    }

    case 'error':
      return { ...state, phase: 'failed', live: false, error: event.message };

    case 'run_finished':
      return {
        ...state,
        live: false,
        phase: event.status === 'paused' ? 'paused' : event.status === 'failed' ? 'failed' : 'done',
        stats: { ...state.stats, elapsed },
      };

    default:
      return state;
  }
}

export interface Field {
  k: string;
  v: string;
  muted: boolean;
}

export interface DisplayCall extends ToolCall {
  key: string;
  isQa: boolean;
  isVerdict: boolean;
  argsLabel: string;
}

export interface DisplayStep {
  key: string;
  node: NodeName;
  name: string;
  status: TimelineStatus;
  dotColor: string;
  headerRight: string;
  hasNext: boolean;
  showSkeleton: boolean;
  category: string | null;
  fieldsLeft: Field[];
  fieldsRight: Field[];
  calls: DisplayCall[];
  verdictFields: Field[];
  actions: string | null;
  draft: string | null;
  note: string | null;
  gate: { bg: string; border: string; text: string; pulse: boolean } | null;
}

const DOT: Record<TimelineStatus, string> = {
  completed: '#2E8B4F',
  running: '#2C7BC8',
  paused: '#C68A2E',
  pending: 'rgba(0,0,0,0.12)',
};

const EXTRACT_LEFT: (keyof ExtractOutput)[] = ['tenant_name', 'address', 'unit'];
const EXTRACT_RIGHT: (keyof ExtractOutput)[] = ['appliance_or_system', 'severity', 'issue_summary'];

function extractFields(output: ExtractOutput | null, keys: (keyof ExtractOutput)[]): Field[] {
  if (!output) return [];
  return keys.map((key) => ({
    k: hum(key),
    v: output[key] === null ? 'None' : humVal(output[key]),
    muted: output[key] === null,
  }));
}

function headerRight(step: TimelineStep): string {
  if (step.usage) {
    const { model, inputTokens, outputTokens, cost } = step.usage;
    return `${model} · ${inputTokens} in / ${outputTokens} out tok · ${fmtCost(cost)}`;
  }
  if (step.status === 'running') return 'streaming…';
  return step.at === null ? '' : `${step.at.toFixed(2)}s`;
}

function gateStyle(kind: 'paused' | 'approved' | 'rejected') {
  if (kind === 'paused') {
    return { bg: '#FCF3E3', border: '#EFDDB0', text: '#8A5A16', pulse: true };
  }
  if (kind === 'approved') {
    return { bg: '#E9F5EC', border: '#BFE2C8', text: '#256B3A', pulse: false };
  }
  return { bg: '#FBEAEA', border: 'rgba(178,58,50,0.25)', text: '#8E2A24', pulse: false };
}

export function toDisplaySteps(state: RunState): DisplayStep[] {
  const approved = state.steps.some((step) => step.node === 'execute');

  return state.steps.map((step, index) => {
    const running = step.status === 'running';
    const isLease = step.node === 'lease_check';
    const lease = isLease ? (step.output as LeaseCheckOutput | null) : null;
    const gateKind =
      step.status === 'paused' ? 'paused' : approved ? 'approved' : 'rejected';

    return {
      key: step.key,
      node: step.node,
      name: hum(step.node),
      status: step.status,
      dotColor: DOT[step.status],
      headerRight: headerRight(step),
      hasNext: index < state.steps.length - 1,
      showSkeleton: running && !isLease && step.node !== 'approval' && !step.output,
      category:
        step.node === 'classify' && step.output
          ? humVal((step.output as ClassifyOutput).category)
          : null,
      fieldsLeft:
        step.node === 'extract'
          ? extractFields(step.output as ExtractOutput | null, EXTRACT_LEFT)
          : [],
      fieldsRight:
        step.node === 'extract'
          ? extractFields(step.output as ExtractOutput | null, EXTRACT_RIGHT)
          : [],
      calls: step.calls.map((call, i) => ({
        ...call,
        key: `${step.key}-${i}`,
        isQa: call.tool === 'lease_qa',
        isVerdict: call.tool === 'submit_verdict',
        argsLabel: humArgs(call.argsText),
      })),
      verdictFields: lease
        ? [
            {
              k: hum('lease_addresses_issue'),
              v: humVal(lease.lease_addresses_issue),
              muted: false,
            },
            {
              k: hum('responsibility'),
              v: humVal(lease.responsibility),
              muted: false,
            },
          ]
        : [],
      actions:
        step.node === 'plan' && step.output
          ? (step.output as PlanOutput).actions.map(humVal).join(', ')
          : step.node === 'execute' && step.output
            ? humVal((step.output as ExecuteOutput).succeeded)
            : null,
      draft: step.node === 'draft' && step.output ? (step.output as DraftOutput).draft : null,
      note: step.note,
      gate: step.node === 'approval' ? gateStyle(gateKind) : null,
    };
  });
}

export function runLabel(state: RunState, emailStatus: EmailStatus): string {
  if (state.live) return 'streaming live';
  switch (state.phase) {
    case 'paused':
      return 'paused at approval gate';
    case 'failed':
      return `failed${state.error ? ` · ${state.error}` : ''}`;
    case 'done':
      return 'finished';
    default:
      return emailStatus === 'pending' ? 'not started' : humVal(emailStatus);
  }
}
