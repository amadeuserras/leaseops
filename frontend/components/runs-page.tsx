"use client";

import { useEffect, useMemo, useRef } from "react";

import { useRunStream } from "@/hooks/use-run-stream";
import { type RunDetailResponse, senderDisplayName } from "@/lib/api";
import { fmtClock, fmtCost, fmtElapsed, fmtTokens, initials } from "@/lib/format";
import { fromRunDetail, runLabel, toDisplaySteps } from "@/lib/run-state";

import { RunTimeline } from "./run-timeline";

export function RunsPage({ data }: { data: RunDetailResponse }) {
  const initial = useMemo(() => fromRunDetail(data), [data]);
  const { state, start } = useRunStream(data.email.id, initial);
  const autoStarted = useRef(false);

  // Opening an email the agent has not touched yet is what starts the run. It
  // is an explicit call from this flow, fired once, never on later re-renders.
  useEffect(() => {
    if (autoStarted.current) return;
    if (data.steps.length === 0 && data.email.status === "pending") {
      autoStarted.current = true;
      start();
    }
  }, [data.steps.length, data.email.status, start]);

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
        <div className="w-[420px] min-w-[280px] shrink basis-[420px] overflow-y-auto border-r border-hairline bg-page p-6">
          <div className="mb-2.5 text-[12.5px] text-ink-40">Original message</div>
          <div className="rounded-xl border border-hairline bg-surface p-5">
            <div className="mb-3.5 flex items-center gap-2">
              <div className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full bg-blue-bg text-[13px] font-bold text-blue">
                {initials(senderName)}
              </div>
              <div className="min-w-0">
                <div className="text-[13.5px] font-semibold">{senderName}</div>
                <div className="text-[11.5px] text-ink-50">{email.sender}</div>
              </div>
            </div>
            <div className="mb-1 text-[14.5px] font-bold">{email.subject}</div>
            <div className="mb-3.5 text-[12.5px] text-ink-40">
              Received {fmtClock(email.received_at)}
            </div>
            <div className="text-[13px] leading-[1.7] whitespace-pre-line text-ink-82">
              {email.body}
            </div>
          </div>
        </div>

        <div
          ref={scrollRef}
          className="min-w-[380px] flex-1 basis-[480px] overflow-y-auto px-7 py-6"
        >
          <div className="mb-1 flex items-start justify-between gap-4">
            <h1 className="m-0 text-lg font-bold tracking-[-0.01em]">
              Agent run trace
            </h1>
            <button
              type="button"
              onClick={start}
              disabled={state.live}
              className="flex shrink-0 cursor-pointer items-center gap-1.5 rounded-full border border-black/10 bg-surface px-3 py-[5px] text-[12.5px] font-medium text-ink-60 select-none hover:bg-raised hover:text-ink disabled:cursor-default disabled:opacity-50 disabled:hover:bg-surface disabled:hover:text-ink-60"
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
              {state.live ? "Running…" : state.steps.length > 0 ? "Re-run" : "Run agent"}
            </button>
          </div>

          <div className="mb-[22px] text-[12.5px] text-ink-40">
            {state.runId ? `run_${state.runId.slice(0, 8)}` : "no run yet"} ·{" "}
            {runLabel(state, email.status)}
          </div>

          {state.error && (
            <div className="mb-4 rounded-lg border border-red-border bg-red-bg px-3.5 py-3 text-[13px] text-red">
              {state.error}
            </div>
          )}

          {steps.length === 0 && !state.live ? (
            <div className="rounded-xl border border-dashed border-black/12 px-4 py-9 text-center text-[12.5px] text-ink-35">
              The agent has not processed this email yet.
            </div>
          ) : (
            <RunTimeline steps={steps} />
          )}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-7 border-t border-hairline bg-page px-7 py-3 font-mono text-xs text-ink-55">
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
