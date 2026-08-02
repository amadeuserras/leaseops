import type { ApprovalRequest, StepRecord, StreamEvent } from '@/lib/api';

export type ToolCallRecord = {
  tool: string;
  arguments: Record<string, unknown>;
  reasoning: string;
  result: unknown;
  isError: boolean;
  done: boolean;
};

export type TraceStep = {
  node: string;
  status: 'running' | 'completed' | 'paused';
  output: Record<string, unknown> | null;
  calls: ToolCallRecord[];
  model: string | null;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  startedAt: number;
  endedAt: number | null;
};

export type RunState = {
  emailId: string;
  runId: string | null;
  status: 'streaming' | 'paused' | 'done' | 'failed';
  source: 'live' | 'db';
  steps: TraceStep[];
  pausedRequest: ApprovalRequest | null;
  error: string | null;
  tokens: number;
  costUsd: number;
  elapsedMs: number | null;
  stepCount: number;
  startedAt: number;
  endedAt: number | null;
};

const patchStep = (
  run: RunState,
  node: string,
  update: (step: TraceStep) => TraceStep,
): TraceStep[] => {
  const index = run.steps.findLastIndex((step) => step.node === node);
  if (index === -1) return run.steps;
  return run.steps.map((step, i) => (i === index ? update(step) : step));
};

export const applyEvent = (run: RunState, event: StreamEvent): RunState => {
  switch (event.type) {
    case 'run_started':
      return { ...run, runId: event.run_id };

    case 'node_started':
      return {
        ...run,
        stepCount: run.steps.length + 1,
        steps: [
          ...run.steps,
          {
            node: event.node,
            status: 'running',
            output: null,
            calls: [],
            model: null,
            inputTokens: 0,
            outputTokens: 0,
            costUsd: 0,
            startedAt: Date.now(),
            endedAt: null,
          },
        ],
      };

    case 'cost':
      return {
        ...run,
        tokens: run.tokens + event.input_tokens + event.output_tokens,
        costUsd: run.costUsd + event.cost_usd,
        steps: patchStep(run, event.node, (step) => ({
          ...step,
          model: event.model,
          inputTokens: step.inputTokens + event.input_tokens,
          outputTokens: step.outputTokens + event.output_tokens,
          costUsd: step.costUsd + event.cost_usd,
        })),
      };

    case 'tool_call':
      return {
        ...run,
        steps: patchStep(run, event.node, (step) => ({
          ...step,
          calls: [
            ...step.calls,
            {
              tool: event.tool,
              arguments: event.arguments,
              reasoning: event.reasoning,
              result: null,
              isError: false,
              done: false,
            },
          ],
        })),
      };

    case 'tool_result':
      return {
        ...run,
        steps: patchStep(run, event.node, (step) => {
          const index = step.calls.findLastIndex((call) => call.tool === event.tool && !call.done);
          if (index === -1) return step;
          return {
            ...step,
            calls: step.calls.map((call, i) =>
              i === index
                ? { ...call, result: event.result, isError: event.is_error, done: true }
                : call,
            ),
          };
        }),
      };

    case 'node_finished':
      return {
        ...run,
        steps: patchStep(run, event.node, (step) => ({
          ...step,
          status: 'completed',
          output: event.output,
          endedAt: Date.now(),
        })),
      };

    case 'paused': {
      const gate = run.steps.at(-1);
      return {
        ...run,
        pausedRequest: event.request,
        steps: gate
          ? patchStep(run, gate.node, (step) => ({
              ...step,
              status: 'paused',
              endedAt: Date.now(),
            }))
          : run.steps,
      };
    }

    case 'run_finished':
      return {
        ...run,
        status: event.status === 'paused' ? 'paused' : 'done',
        endedAt: Date.now(),
      };

    case 'error':
      return { ...run, status: 'failed', error: event.message, endedAt: Date.now() };
  }
};

export const buildRunFromSteps = (
  emailId: string,
  dbSteps: StepRecord[],
  aggregates: { tokens: number; cost: number; elapsed: number; step_count: number },
  awaitingApproval = false,
): RunState => {
  const last = dbSteps[dbSteps.length - 1];
  const pausedRequest =
    awaitingApproval && last?.node_name === 'approval' && last.output !== null
      ? last.output
      : null;

  const startedAt = Date.parse(dbSteps[0].created_at);
  const elapsedMs = aggregates.elapsed * 1000;

  return {
    emailId,
    runId: dbSteps[0].run_id,
    status: pausedRequest !== null ? 'paused' : 'done',
    source: 'db',
    steps: dbSteps.map((s) => ({
      node: s.node_name,
      status:
        pausedRequest !== null && s.node_name === 'approval' && s.id === last.id
          ? ('paused' as const)
          : ('completed' as const),
      output: s.output as Record<string, unknown> | null,
      calls: [],
      model: s.model,
      inputTokens: s.input_tokens ?? 0,
      outputTokens: s.output_tokens ?? 0,
      costUsd: s.cost_usd ?? 0,
      startedAt: Date.parse(s.created_at),
      endedAt: Date.parse(s.created_at),
    })),
    pausedRequest,
    error: null,
    tokens: aggregates.tokens,
    costUsd: aggregates.cost,
    elapsedMs,
    stepCount: aggregates.step_count,
    startedAt,
    endedAt: startedAt + elapsedMs,
  };
};
