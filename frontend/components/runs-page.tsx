'use client';

import { RunTimeline } from './run-timeline';
import { useRunStream } from '@/hooks/use-run-stream';
import { type RunDetailResponse, senderDisplayName } from '@/lib/api';
import { fmtClock, fmtCost, fmtElapsed, fmtTokens, initials } from '@/lib/format';
import { fromRunDetail, runLabel, toDisplaySteps } from '@/lib/run-state';
import { useEffect, useMemo, useRef } from 'react';

export function RunsPage({ data }: { data: RunDetailResponse }) {
  const initial = useMemo(() => fromRunDetail(data), [data]);
  const { state, start, rerun } = useRunStream(data.email.id, initial);

  useEffect(() => {
    if (data.steps.length === 0 && data.email.status === 'pending') {
      start();
    }
  }, [data.email.id, data.steps.length, data.email.status, start]);

  const steps = toDisplaySteps(state);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Follow the tail while events are arriving.
  useEffect(() => {
    if (state.live && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.live, state.steps]);

  const email = data.email;
  const senderName = senderDisplayName(email.sender);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex min-h-0 flex-1">
        <div className="border-hairline bg-page w-[420px] min-w-[280px] shrink basis-[420px] overflow-y-auto border-r p-6">
          <div className="text-ink-40 mb-2.5 text-[12.5px]">Original message</div>
          <div className="border-hairline bg-surface rounded-xl border p-5">
            <div className="mb-3.5 flex items-center gap-2">
              <div className="bg-blue-bg text-blue flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full text-[13px] font-bold">
                {initials(senderName)}
              </div>
              <div className="min-w-0">
                <div className="text-[13.5px] font-semibold">{senderName}</div>
                <div className="text-ink-50 text-[11.5px]">{email.sender}</div>
              </div>
            </div>
            <div className="mb-1 text-[14.5px] font-bold">{email.subject}</div>
            <div className="text-ink-40 mb-3.5 text-[12.5px]">
              Received {fmtClock(email.received_at)}
            </div>
            <div className="text-ink-82 text-[13px] leading-[1.7] whitespace-pre-line">
              {email.body}
            </div>
          </div>
        </div>

        <div
          ref={scrollRef}
          className="min-w-[380px] flex-1 basis-[480px] overflow-y-auto px-7 py-6"
        >
          <div className="mb-1 flex items-start justify-between gap-4">
            <h1 className="m-0 text-lg font-bold tracking-[-0.01em]">Agent run trace</h1>
            <button
              type="button"
              onClick={() => (state.steps.length > 0 ? rerun() : start())}
              disabled={state.live}
              className="bg-surface text-ink-60 hover:bg-raised hover:text-ink disabled:hover:bg-surface disabled:hover:text-ink-60 flex shrink-0 cursor-pointer items-center gap-1.5 rounded-full border border-black/10 px-3 py-[5px] text-[12.5px] font-medium select-none disabled:cursor-default disabled:opacity-50"
            >
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                <path
                  d="M20 12a8 8 0 1 1-2.34-5.66M20 4v4h-4"
                  stroke="currentColor"
                  strokeWidth="2.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {state.live ? 'Running…' : state.steps.length > 0 ? 'Re-run' : 'Run agent'}
            </button>
          </div>

          <div className="text-ink-40 mb-[22px] text-[12.5px]">
            {state.runId ? `run_${state.runId.slice(0, 8)}` : 'no run yet'} ·{' '}
            {runLabel(state, email.status)}
          </div>

          {state.error && (
            <div className="border-red-border bg-red-bg text-red mb-4 rounded-lg border px-3.5 py-3 text-[13px]">
              {state.error}
            </div>
          )}

          <RunTimeline steps={steps} />
        </div>
      </div>

      <div className="border-hairline bg-page text-ink-55 flex shrink-0 items-center gap-7 border-t px-7 py-3 font-mono text-xs">
        <div>
          <span className="text-ink-40">tokens</span>&nbsp;&nbsp;
          {fmtTokens(state.stats.tokens)}
        </div>
        <div>
          <span className="text-ink-40">cost</span>&nbsp;&nbsp;
          {fmtCost(state.stats.cost)}
        </div>
        <div>
          <span className="text-ink-40">elapsed</span>&nbsp;&nbsp;
          {fmtElapsed(state.stats.elapsed)}
        </div>
        <div>
          <span className="text-ink-40">steps</span>&nbsp;&nbsp;
          {state.stats.step_count}
        </div>
      </div>
    </div>
  );
}
