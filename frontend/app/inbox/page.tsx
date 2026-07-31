'use client';

import { useApprovals } from '@/components/approvals-provider';
import { Pill } from '@/components/pill';
import { useRuns } from '@/components/runs-provider';
import type { RunState } from '@/components/runs-provider';
import { useTenants } from '@/components/tenants-provider';
import { listEmails } from '@/lib/api';
import type { Email } from '@/lib/api';
import { formatReceived, previewOf } from '@/lib/format';
import { INBOX_STATUSES, inboxStatusPill, isUrgency, urgencyDot, urgencyText } from '@/lib/status';
import type { InboxStatus, Urgency } from '@/lib/status';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

const GRID = 'grid grid-cols-[180px_1fr_110px_90px_150px] gap-4 min-w-[780px]';

const deriveStatus = (
  email: Email,
  run: RunState | undefined,
  awaitingApproval: boolean,
): InboxStatus => {
  if (run?.status === 'streaming') return 'Running';
  if (awaitingApproval) return 'Awaiting approval';
  if (run?.status === 'failed') return 'Failed';
  if (run?.status === 'done' || run?.status === 'paused') return 'Completed';
  if (email.status === 'escalated') return 'Escalated';
  if (email.status === 'processed') return 'Completed';
  return 'Unprocessed';
};

const deriveUrgency = (run: RunState | undefined): Urgency | null => {
  const extract = run?.steps.find((step) => step.node === 'extract');
  const urgency = extract?.output?.urgency;
  return isUrgency(urgency) ? urgency : null;
};

type FilterValue = InboxStatus | 'all';

const FILTERS: FilterValue[] = ['all', ...INBOX_STATUSES];

type FilterChipProps = {
  label: string;
  active: boolean;
  onSelect: () => void;
};

function FilterChip({ label, active, onSelect }: FilterChipProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`cursor-pointer rounded-full border px-3 py-1.5 text-[12.5px] font-medium whitespace-nowrap transition-colors ${
        active
          ? 'border-ink bg-ink text-white'
          : 'bg-surface text-ink/60 hover:bg-muted border-black/10'
      }`}
    >
      {label}
    </button>
  );
}

export default function InboxPage() {
  const router = useRouter();
  const { runs, setActiveEmailId } = useRuns();
  const { items: approvals, decisions } = useApprovals();
  const { profileOf } = useTenants();

  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterValue>('all');

  useEffect(() => {
    listEmails()
      .then(setEmails)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : 'could not load the inbox'),
      )
      .finally(() => setLoading(false));
  }, []);

  const awaitingApprovalIds = useMemo(
    () =>
      new Set(
        approvals
          .filter((item) => decisions[item.run_id] === undefined)
          .map((item) => item.email_id),
      ),
    [approvals, decisions],
  );

  const rows = useMemo(
    () =>
      emails.map((email) => {
        const run = runs[email.id];
        const profile = profileOf(email.sender);
        return {
          email,
          profile,
          run,
          status: deriveStatus(email, run, awaitingApprovalIds.has(email.id)),
          urgency: deriveUrgency(run),
        };
      }),
    [emails, runs, profileOf, awaitingApprovalIds],
  );

  const visibleRows = filter === 'all' ? rows : rows.filter((row) => row.status === filter);

  const openRun = (emailId: string) => {
    setActiveEmailId(emailId);
    router.push(`/runs/${emailId}`);
  };

  return (
    <div className="custom-scrollbar h-full overflow-y-auto px-9 pt-7 pb-10">
      <div className="mb-[18px] flex flex-wrap items-center justify-between gap-y-2">
        <h1 className="m-0 text-xl font-bold tracking-[-0.01em]">Inbox</h1>
        <div className="flex items-center gap-3.5">
          <span className="text-ink/40 font-mono text-[11.5px] whitespace-nowrap">
            {emails.length} messages
          </span>
          <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[#3C4450] text-[12.5px] font-semibold text-white">
            D
          </span>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-end justify-between gap-y-2.5">
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((value) => (
            <FilterChip
              key={value}
              label={value === 'all' ? 'All' : value}
              active={filter === value}
              onSelect={() => setFilter(value)}
            />
          ))}
        </div>
        <span className="text-ink/45 flex items-center gap-1.5 text-[11.5px] whitespace-nowrap">
          <span className="bg-success-dot size-[5px] rounded-full" aria-hidden />
          Click a message to run the agent
        </span>
      </div>

      {error !== null && (
        <div className="border-danger-line bg-danger-bg text-danger rounded-[10px] border px-4 py-3 text-[13px]">
          {error}
        </div>
      )}

      <div className="custom-scrollbar bg-surface overflow-x-auto rounded-[10px] border border-black/8">
        <div
          className={`${GRID} bg-canvas text-ink/45 border-b border-black/8 px-[18px] py-2.5 text-[11px] font-semibold tracking-[0.03em] uppercase`}
        >
          <div>Sender</div>
          <div>Subject</div>
          <div>Received</div>
          <div>Urgency</div>
          <div>Status</div>
        </div>

        {loading && <div className="text-ink/45 px-[18px] py-6 text-[13px]">Loading messages…</div>}

        {!loading && visibleRows.length === 0 && (
          <div className="text-ink/45 px-[18px] py-6 text-[13px]">
            No messages match this filter.
          </div>
        )}

        {visibleRows.map(({ email, profile, status, urgency }) => (
          <button
            key={email.id}
            type="button"
            onClick={() => openRun(email.id)}
            className={`${GRID} w-full cursor-pointer items-center border-b border-black/6 px-[18px] py-3.5 text-left transition-colors hover:bg-[#FAFAFB]`}
          >
            <div className="min-w-0">
              <div className="truncate text-[13px] font-semibold">{profile.name}</div>
              <div className="text-ink/50 truncate text-[11.5px]">
                {profile.unit === null ? email.sender : `Unit ${profile.unit}`}
              </div>
            </div>
            <div className="min-w-0">
              <div className="truncate text-[13px] font-medium">{email.subject}</div>
              <div className="text-ink/50 truncate text-[12px]">{previewOf(email.body)}</div>
            </div>
            <div className="text-ink/55 font-mono text-[12px]">
              {formatReceived(email.received_at)}
            </div>
            <div
              className={`flex items-center gap-1.5 text-[12px] font-medium ${
                urgency === null ? 'text-ink/30' : urgencyText[urgency]
              }`}
            >
              {urgency !== null && (
                <span
                  className={`size-1.5 shrink-0 rounded-full ${urgencyDot[urgency]}`}
                  aria-hidden
                />
              )}
              {urgency === null ? '—' : urgency[0].toUpperCase() + urgency.slice(1)}
            </div>
            <div>
              <Pill className={inboxStatusPill[status]}>{status}</Pill>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
