'use client';

import {
  type EmailListResponse,
  type EmailResponse,
  type EmailStatus,
  type Severity,
  senderDisplayName,
} from '@/lib/api';
import { fmtClock, fmtRelative, humVal, preview } from '@/lib/format';
import Link from 'next/link';
import { useState } from 'react';

const STATUS_STYLE: Record<
  EmailStatus,
  { label: string; bg: string; text: string; border: string }
> = {
  pending: {
    label: 'Pending',
    bg: '#EDEEF1',
    text: 'rgba(23,24,27,0.6)',
    border: 'rgba(0,0,0,0.09)',
  },
  processing: {
    label: 'Processing',
    bg: '#EAF3FC',
    text: '#2C7BC8',
    border: 'rgba(44,123,200,0.28)',
  },
  awaiting_approval: {
    label: 'Awaiting approval',
    bg: '#FCF3E3',
    text: '#8A5A16',
    border: '#EFDDB0',
  },
  processed: {
    label: 'Processed',
    bg: '#E9F5EC',
    text: '#256B3A',
    border: '#BFE2C8',
  },
};

const SEVERITY_STYLE: Record<Severity, { label: string; color: string }> = {
  critical: { label: 'Critical', color: '#963226' },
  high: { label: 'High', color: '#8A5A16' },
  medium: { label: 'Medium', color: 'rgba(23,24,27,0.6)' },
  low: { label: 'Low', color: 'rgba(23,24,27,0.4)' },
};

const FILTERS: { key: 'all' | EmailStatus; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'processing', label: 'Processing' },
  { key: 'awaiting_approval', label: 'Awaiting approval' },
  { key: 'processed', label: 'Processed' },
];

const COLUMNS = 'grid-cols-[180px_1fr_110px_90px_150px_180px]';

export function InboxPage({ data }: { data: EmailListResponse }) {
  const [filter, setFilter] = useState<'all' | EmailStatus>('all');
  const rows = filter === 'all' ? data.items : data.items.filter((e) => e.status === filter);

  return (
    <div className="h-full overflow-y-auto px-9 pt-7 pb-10">
      <div className="mb-[18px] flex flex-wrap items-center justify-between gap-y-2">
        <h1 className="m-0 text-xl font-bold tracking-[-0.01em]">Inbox</h1>
        <div className="flex items-center gap-3.5">
          <div className="text-ink-40 text-[12.5px] whitespace-nowrap">
            {data.items.length} messages
          </div>
          <div className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full bg-[#3C4450] text-[12.5px] font-semibold text-white">
            D
          </div>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-end justify-between gap-y-2.5">
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((chip) => {
            const active = filter === chip.key;
            return (
              <button
                key={chip.key}
                type="button"
                onClick={() => setFilter(chip.key)}
                className={`cursor-pointer rounded-full border px-3 py-1.5 text-[12.5px] font-medium whitespace-nowrap ${
                  active ? 'border-ink bg-ink text-white' : 'bg-surface text-ink-60 border-black/10'
                }`}
              >
                {chip.label}
              </button>
            );
          })}
        </div>
        <div className="text-ink-45 flex items-center gap-1.5 text-[11.5px] whitespace-nowrap">
          <span className="bg-green h-[5px] w-[5px] rounded-full" />
          Agent last ran {fmtRelative(data.agent_last_ran_at)}
        </div>
      </div>

      <div className="border-hairline bg-surface overflow-x-auto rounded-xl border">
        <div
          className={`grid ${COLUMNS} border-hairline bg-page text-ink-45 min-w-[960px] gap-4 border-b px-[18px] py-2.5 text-[11px] font-semibold tracking-[0.03em] uppercase`}
        >
          <div>Sender</div>
          <div>Subject</div>
          <div>Received</div>
          <div>Severity</div>
          <div>Status</div>
          <div>Actions taken</div>
        </div>

        {rows.map((email) => (
          <InboxRow key={email.id} email={email} />
        ))}

        {rows.length === 0 && (
          <div className="text-ink-35 px-[18px] py-9 text-center text-[12.5px]">
            No messages match this filter
          </div>
        )}
      </div>
    </div>
  );
}

function InboxRow({ email }: { email: EmailResponse }) {
  const status = STATUS_STYLE[email.status];
  const severity = email.severity ? SEVERITY_STYLE[email.severity] : null;
  const showSeverity = email.status !== 'pending' && severity !== null;
  const actions = email.actions_taken;

  return (
    <Link
      href={`/runs/${email.id}`}
      className={`grid ${COLUMNS} border-hairline-soft hover:bg-hover min-w-[960px] cursor-pointer items-center gap-4 border-b px-[18px] py-3.5`}
    >
      <div className="min-w-0">
        <div className="truncate text-[13px] font-semibold">{senderDisplayName(email.sender)}</div>
        <div className="text-ink-50 truncate text-[11.5px]">
          {email.unit ? `Unit ${email.unit}` : email.sender}
        </div>
      </div>

      <div className="min-w-0">
        <div className="truncate text-[13px] font-medium">{email.subject}</div>
        <div className="text-ink-50 truncate text-xs">{preview(email.body)}</div>
      </div>

      <div className="text-ink-55 text-xs">{fmtClock(email.received_at)}</div>

      <div>
        {showSeverity ? (
          <div
            className="flex items-center gap-1.5 text-xs font-medium"
            style={{ color: severity.color }}
          >
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ background: severity.color }}
            />
            {severity.label}
          </div>
        ) : (
          <div className="text-ink-28 text-xs">—</div>
        )}
      </div>

      <div>
        <span
          className="inline-block rounded-full border px-2.5 py-[3px] text-[11.5px] font-semibold"
          style={{
            background: status.bg,
            color: status.text,
            borderColor: status.border,
          }}
        >
          {status.label}
        </span>
      </div>

      <div className="text-ink-60 min-w-0 truncate text-xs">
        {actions.length > 0 ? (
          actions.map(humVal).join(', ')
        ) : (
          <span className="text-ink-28">—</span>
        )}
      </div>
    </Link>
  );
}
