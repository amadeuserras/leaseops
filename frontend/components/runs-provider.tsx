'use client';

import { ApiError, streamRun } from '@/lib/api';
import type { ApprovalRequest, StreamEvent } from '@/lib/api';
import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';

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
  steps: TraceStep[];
  pausedRequest: ApprovalRequest | null;
  error: string | null;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  startedAt: number;
  endedAt: number | null;
};

const newRun = (emailId: string): RunState => ({
  emailId,
  runId: null,
  status: 'streaming',
  steps: [],
  pausedRequest: null,
  error: null,
  inputTokens: 0,
  outputTokens: 0,
  costUsd: 0,
  startedAt: Date.now(),
  endedAt: null,
});

const patchStep = (
  run: RunState,
  node: string,
  update: (step: TraceStep) => TraceStep,
): TraceStep[] => {
  const index = run.steps.findLastIndex((step) => step.node === node);
  if (index === -1) return run.steps;
  return run.steps.map((step, i) => (i === index ? update(step) : step));
};

const applyEvent = (run: RunState, event: StreamEvent): RunState => {
  switch (event.type) {
    case 'run_started':
      return { ...run, runId: event.run_id };

    case 'node_started':
      return {
        ...run,
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
        inputTokens: run.inputTokens + event.input_tokens,
        outputTokens: run.outputTokens + event.output_tokens,
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

type RunsContextValue = {
  runs: Record<string, RunState>;
  activeEmailId: string | null;
  setActiveEmailId: (emailId: string) => void;
  startRun: (emailId: string, options?: { force?: boolean }) => void;
};

const RunsContext = createContext<RunsContextValue | null>(null);

type RunsProviderProps = { children: ReactNode };

export function RunsProvider({ children }: RunsProviderProps) {
  const [runs, setRuns] = useState<Record<string, RunState>>({});
  const [activeEmailId, setActiveEmailId] = useState<string | null>(null);
  const controllers = useRef(new Map<string, AbortController>());

  const startRun = useCallback((emailId: string, options?: { force?: boolean }) => {
    let started = false;

    setRuns((previous) => {
      if (previous[emailId] !== undefined && options?.force !== true) return previous;
      started = true;
      return { ...previous, [emailId]: newRun(emailId) };
    });

    if (!started) return;

    controllers.current.get(emailId)?.abort();
    const controller = new AbortController();
    controllers.current.set(emailId, controller);

    const onEvent = (event: StreamEvent) =>
      setRuns((previous) => {
        const current = previous[emailId];
        if (current === undefined) return previous;
        return { ...previous, [emailId]: applyEvent(current, event) };
      });

    void streamRun({ emailId, onEvent, signal: controller.signal })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          cause instanceof ApiError || cause instanceof Error
            ? cause.message
            : 'the trace stream failed';
        setRuns((previous) => {
          const current = previous[emailId];
          if (current === undefined) return previous;
          return {
            ...previous,
            [emailId]: { ...current, status: 'failed', error: message, endedAt: Date.now() },
          };
        });
      })
      .finally(() => {
        setRuns((previous) => {
          const current = previous[emailId];
          if (current === undefined || current.status !== 'streaming') return previous;
          return {
            ...previous,
            [emailId]: {
              ...current,
              status: current.pausedRequest !== null ? 'paused' : 'done',
              endedAt: Date.now(),
            },
          };
        });
      });
  }, []);

  const value = useMemo<RunsContextValue>(
    () => ({ runs, activeEmailId, setActiveEmailId, startRun }),
    [runs, activeEmailId, startRun],
  );

  return <RunsContext.Provider value={value}>{children}</RunsContext.Provider>;
}

export const useRuns = (): RunsContextValue => {
  const context = useContext(RunsContext);
  if (context === null) throw new Error('useRuns must be used inside <RunsProvider>');
  return context;
};
