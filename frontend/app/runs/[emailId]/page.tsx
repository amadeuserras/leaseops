'use client';

import { useApprovals } from '@/components/approvals-provider';
import { EmailCard } from '@/components/email-card';
import { Pill } from '@/components/pill';
import { RunStats } from '@/components/run-stats';
import { useRuns } from '@/components/runs-provider';
import type { RunState } from '@/components/runs-provider';
import { useTenants } from '@/components/tenants-provider';
import { TraceStep } from '@/components/trace-step';
import { getEmail } from '@/lib/api';
import type { Email } from '@/lib/api';
import { shortId } from '@/lib/format';
import { runStatusPill } from '@/lib/status';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

const runPill = (run: RunState | undefined): { label: string; className: string } => {
  switch (run?.status) {
    case 'streaming':
      return { label: 'running', className: runStatusPill.streaming };
    case 'paused':
      return { label: 'awaiting approval', className: runStatusPill.paused };
    case 'done':
      return { label: 'completed', className: runStatusPill.done };
    case 'failed':
      return { label: 'failed', className: runStatusPill.failed };
    default:
      return { label: 'not started', className: runStatusPill.idle };
  }
};

const streamLabel = (run: RunState | undefined): string => {
  if (run === undefined) return 'no run in this session';
  const nodes = `${run.steps.length} nodes`;
  if (run.status === 'streaming') return `streaming · ${nodes}`;
  return `stream closed · ${nodes}`;
};

export default function RunTracePage() {
  const params = useParams<{ emailId: string }>();
  const emailId = params.emailId;

  const { runs, startRun, setActiveEmailId } = useRuns();
  const { items: approvals, decisions, refresh } = useApprovals();
  const { profileOf } = useTenants();

  const [email, setEmail] = useState<Email | null>(null);
  const [error, setError] = useState<string | null>(null);
  const autoStarted = useRef<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const run = runs[emailId];
  const pending = approvals.find((item) => item.email_id === emailId);
  const decision = pending === undefined ? null : (decisions[pending.run_id] ?? null);

  useEffect(() => {
    setActiveEmailId(emailId);
    getEmail(emailId)
      .then(setEmail)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : 'could not load the message'),
      );
  }, [emailId, setActiveEmailId]);

  useEffect(() => {
    if (email === null || autoStarted.current === emailId) return;
    autoStarted.current = emailId;
    if (email.status === 'pending' && runs[emailId] === undefined) startRun(emailId);
  }, [email, emailId, runs, startRun]);

  useEffect(() => {
    if (run?.status === 'paused') void refresh();
  }, [run?.status, refresh]);

  useEffect(() => {
    if (run?.status !== 'streaming' || scrollRef.current === null) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [run?.status, run?.steps]);

  const status = runPill(run);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex min-h-0 flex-1">
        <div className="custom-scrollbar bg-canvas w-[420px] shrink-0 overflow-y-auto border-r border-black/8 p-6">
          <div className="text-ink/40 mb-2.5 text-[11px] font-semibold tracking-[0.03em] uppercase">
            Original message
          </div>
          {error !== null && (
            <div className="border-danger-line bg-danger-bg text-danger rounded-[10px] border px-4 py-3 text-[13px]">
              {error}
            </div>
          )}
          {email !== null && <EmailCard email={email} profile={profileOf(email.sender)} />}
        </div>

        <div ref={scrollRef} className="custom-scrollbar min-w-0 flex-1 overflow-y-auto px-7 py-6">
          <div className="mb-1 flex items-start justify-between gap-4">
            <h1 className="m-0 text-[18px] font-bold tracking-[-0.01em]">Agent run trace</h1>
            <div className="flex shrink-0 items-center gap-2.5">
              {email !== null && run?.status !== 'streaming' && (
                <button
                  type="button"
                  onClick={() => startRun(emailId, { force: true })}
                  className="bg-surface text-ink-soft hover:bg-muted flex cursor-pointer items-center gap-1.5 rounded-md border border-black/12 px-2.5 py-1 text-[11.5px] font-semibold transition-colors select-none"
                >
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" aria-hidden>
                    <path
                      d="M20 12a8 8 0 1 1-2.34-5.66M20 4v4h-4"
                      stroke="#2A2C31"
                      strokeWidth="2.4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  {run === undefined ? 'Run agent' : 'Replay'}
                </button>
              )}
              <Pill className={status.className}>{status.label}</Pill>
            </div>
          </div>
          <div className="text-ink/40 mb-[22px] font-mono text-[11.5px]">
            {run?.runId == null ? 'run_—' : `run_${shortId(run.runId)}`} · {streamLabel(run)}
          </div>

          {run === undefined && (
            <div className="bg-surface text-ink/60 rounded-[10px] border border-black/8 p-5 text-[13px] leading-relaxed">
              No live trace for this message in this session.
              <br />
              The API exposes no endpoint for reading a past run&apos;s trace, so history cannot be
              replayed — use <span className="font-semibold">Run agent</span> to stream a new one.
            </div>
          )}

          {run?.error != null && (
            <div className="border-danger-line bg-danger-bg text-danger mb-4 rounded-[10px] border px-4 py-3 text-[13px]">
              {run.error}
            </div>
          )}

          <div className="relative">
            {run?.steps.map((step, index) => (
              <TraceStep
                key={`${step.node}-${index}`}
                step={step}
                isLast={index === run.steps.length - 1}
                pausedRequest={run.pausedRequest}
                decision={step.node === 'approval_gate' ? decision : null}
              />
            ))}
          </div>

          {run?.status === 'paused' && decision === null && (
            <Link
              href="/approvals"
              className="border-warn-line bg-warn-bg text-warn inline-flex items-center gap-1.5 rounded-md border px-3 py-2 text-[12.5px] font-semibold transition-opacity hover:opacity-80"
            >
              Review in approvals →
            </Link>
          )}
        </div>
      </div>

      <RunStats run={run} />
    </div>
  );
}
