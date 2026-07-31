'use client';

import type { ApprovalDecision } from '@/components/approvals-provider';
import { Avatar, Pill } from '@/components/pill';
import type { PendingApproval } from '@/lib/api';
import { initialsOf, shortId } from '@/lib/format';
import { actionPill } from '@/lib/status';
import Link from 'next/link';
import { useState } from 'react';

type SectionProps = { label: string; children: string };

function Section({ label, children }: SectionProps) {
  return (
    <div className="bg-canvas rounded-[7px] border border-black/6 px-3 py-2.5">
      <div className="text-ink/40 mb-1.5 font-mono text-[10.5px]">{label}</div>
      <p className="text-ink-soft text-[12.5px] leading-normal">{children}</p>
    </div>
  );
}

type ApprovalCardProps = {
  item: PendingApproval;
  decision: ApprovalDecision | null;
  onApprove: () => Promise<void>;
  onReject: (reason: string) => Promise<void>;
};

export function ApprovalCard({ item, decision, onApprove, onReject }: ApprovalCardProps) {
  const [rejectOpen, setRejectOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : 'the decision could not be recorded');
    } finally {
      setBusy(false);
    }
  };

  const decided = decision !== null;

  return (
    <div
      className={`bg-surface flex flex-col gap-3 rounded-[10px] border border-black/8 p-[18px] ${
        decided ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-2.5">
        <div className="flex min-w-0 items-center gap-2.5">
          <Avatar initials={initialsOf(item.tenant_name ?? 'Unknown tenant')} size="sm" />
          <div className="min-w-0">
            <div className="truncate text-[13.5px] font-semibold">
              {item.tenant_name ?? 'Unidentified tenant'}
            </div>
            <Link
              href={`/runs/${item.email_id}`}
              className="text-ink/45 hover:text-ink/70 font-mono text-[11px]"
            >
              unit {item.unit ?? '—'} · run_{shortId(item.run_id)}
            </Link>
          </div>
        </div>
        <Pill className={`${actionPill[item.action_type]} px-2 py-px text-[10.5px]`}>
          {item.action_type}
        </Pill>
      </div>

      {item.issue_summary !== null && <Section label="issue summary">{item.issue_summary}</Section>}
      {item.summary !== null && <Section label="decision summary">{item.summary}</Section>}

      {item.draft !== null && (
        <div>
          <div className="text-ink/40 mb-1.5 font-mono text-[10.5px]">draft reply</div>
          <p className="text-ink-soft border-l-2 border-black/12 pl-3 text-[12.5px] leading-normal whitespace-pre-line">
            {item.draft}
          </p>
        </div>
      )}

      {error !== null && <p className="text-danger text-[12px]">{error}</p>}

      {!decided &&
        (rejectOpen ? (
          <div className="flex flex-col gap-2">
            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Reason for rejecting…"
              className="bg-surface text-ink min-h-[60px] w-full resize-y rounded-md border border-black/12 px-2.5 py-2 text-[12.5px] outline-none focus:border-black/25"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setRejectOpen(false)}
                className="bg-surface text-ink hover:bg-muted cursor-pointer rounded-md border border-black/12 px-3.5 py-[7px] text-[12.5px] font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={reason.trim() === '' || busy}
                onClick={() => void run(() => onReject(reason.trim()))}
                className="bg-danger-solid cursor-pointer rounded-md px-3.5 py-[7px] text-[12.5px] font-semibold text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-50"
              >
                Confirm rejection
              </button>
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => void run(onApprove)}
              className="bg-accent cursor-pointer rounded-md px-4 py-2 text-[13px] font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => setRejectOpen(true)}
              className="bg-surface text-ink hover:bg-muted cursor-pointer rounded-md border border-black/12 px-4 py-2 text-[13px] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        ))}

      {decision !== null && (
        <div
          className={`flex items-center gap-2 rounded-md border px-3 py-2.5 ${
            decision.outcome === 'approved'
              ? 'border-success-dot/25 bg-success-bg'
              : 'border-danger/25 bg-danger-bg'
          }`}
        >
          <span
            className={`size-[7px] shrink-0 rounded-full ${
              decision.outcome === 'approved' ? 'bg-success-dot' : 'bg-danger'
            }`}
            aria-hidden
          />
          <span
            className={`text-[12.5px] font-semibold ${
              decision.outcome === 'approved' ? 'text-success' : 'text-danger'
            }`}
          >
            {decision.outcome === 'approved'
              ? 'Approved'
              : `Rejected${decision.reason === null ? '' : `: ${decision.reason}`}`}
          </span>
        </div>
      )}
    </div>
  );
}
