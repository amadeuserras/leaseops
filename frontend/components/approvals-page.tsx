'use client';

import { CitationBadge } from '@/components/citation-badge';
import { RelativeTime } from '@/components/relative-time';
import { useApprovalActions } from '@/hooks/use-approval-actions';
import type { ApprovalListResponse, ApprovalRequestResponse, PlanAction } from '@/lib/api';
import { humVal } from '@/lib/format';
import { useState } from 'react';

const CATEGORY_STYLE: Record<
  string,
  { label: string; ink: string; bg: string; border: string; emphasis: boolean }
> = {
  emergency: {
    label: 'Emergency',
    ink: '#A3352C',
    bg: 'rgba(163,53,44,0.08)',
    border: 'rgba(163,53,44,0.28)',
    emphasis: true,
  },
  maintenance: {
    label: 'Maintenance',
    ink: '#2C7BC8',
    bg: 'rgba(44,123,200,0.08)',
    border: 'rgba(44,123,200,0.3)',
    emphasis: false,
  },
  lease_question: {
    label: 'Lease question',
    ink: 'rgba(23,24,27,0.55)',
    bg: 'rgba(0,0,0,0.04)',
    border: 'rgba(0,0,0,0.12)',
    emphasis: false,
  },
  not_our_problem: {
    label: 'Not our problem',
    ink: 'rgba(23,24,27,0.55)',
    bg: 'rgba(0,0,0,0.04)',
    border: 'rgba(0,0,0,0.12)',
    emphasis: false,
  },
};

function categoryStyle(category: string) {
  return CATEGORY_STYLE[category] ?? CATEGORY_STYLE.lease_question;
}

const SEVERITY_DOT: Record<string, string> = {
  critical: '#A3352C',
  high: '#D9483C',
  medium: '#E0A227',
  low: '#8B9099',
};

const ACTION_META: Record<string, { label: string; ink: string; icon: string }> = {
  create_work_order: {
    label: 'Create work order',
    ink: 'rgba(23,24,27,0.35)',
    icon: 'M14 3.3a3.6 3.6 0 01-4.6 4.4l-5.2 5.2a1.5 1.5 0 11-2.1-2.1l5.2-5.2A3.6 3.6 0 0111.7 1L9.8 3l1.2 2.1L13.2 5z',
  },
  send_reply: {
    label: 'Send reply',
    ink: 'rgba(23,24,27,0.35)',
    icon: 'M14.6 1.6L1.6 6.9l5 2.1 2.1 5z M14.6 1.6L6.6 9',
  },
  call_tenant: {
    label: 'Call tenant',
    ink: '#A3352C',
    icon: 'M3 3h3l1 3-1.8 1.2a8.5 8.5 0 004.6 4.6L11 10l3 1v3h-2.2A11.5 11.5 0 013 5.2z',
  },
  dispatch_emergency_vendor: {
    label: 'Dispatch emergency vendor',
    ink: '#A3352C',
    icon: 'M8 2l6 11H2z M8 6.2v3.4 M8 11.2v.6',
  },
  schedule_inspection: {
    label: 'Schedule inspection',
    ink: '#2C7BC8',
    icon: 'M2.5 3.5h11v10.5h-11z M2.5 7h11 M5.5 2v3 M10.5 2v3',
  },
  log_consent_request: {
    label: 'Log consent request',
    ink: 'rgba(23,24,27,0.35)',
    icon: 'M3 8.5l3.2 3.2L13 5',
  },
};

function actionMeta(action: string) {
  return (
    ACTION_META[action] ?? {
      label: humVal(action),
      ink: 'rgba(23,24,27,0.35)',
      icon: 'M3 8h10',
    }
  );
}

type Filters = { category: string; severity: string; responsibility: string };

const FILTER_GROUPS: { key: keyof Filters; label: string; options: string[] }[] = [
  {
    key: 'category',
    label: 'Category',
    options: ['all', 'emergency', 'maintenance', 'lease_question'],
  },
  { key: 'severity', label: 'Severity', options: ['all', 'high', 'medium', 'low'] },
  {
    key: 'responsibility',
    label: 'Responsibility',
    options: ['all', 'landlord', 'tenant'],
  },
];

export function ApprovalsPage({ data }: { data: ApprovalListResponse }) {
  const [filters, setFilters] = useState<Filters>({
    category: 'all',
    severity: 'all',
    responsibility: 'all',
  });
  const actions = useApprovalActions();

  const shown = data.items.filter(
    (item) =>
      (filters.category === 'all' || item.category === filters.category) &&
      (filters.severity === 'all' || item.severity === filters.severity) &&
      (filters.responsibility === 'all' || item.responsibility === filters.responsibility),
  );

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 items-center justify-between gap-4 px-9 pt-7 pb-[18px]">
        <h1 className="m-0 text-xl font-bold tracking-[-0.01em]">Approvals</h1>
        <div className="flex items-center gap-3.5">
          <div className="text-ink-40 text-[12.5px] whitespace-nowrap">
            {shown.length} of {data.items.length} pending
          </div>
          <div className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full bg-[#3C4450] text-[12.5px] font-semibold text-white">
            D
          </div>
        </div>
      </div>

      <div className="flex shrink-0 flex-wrap items-center gap-x-[18px] gap-y-2.5 px-9">
        {FILTER_GROUPS.map((group) => (
          <div key={group.key} className="flex items-center gap-[7px]">
            <div className="text-ink-40 text-[12.5px] whitespace-nowrap">{group.label}</div>
            <div className="flex flex-wrap gap-[5px]">
              {group.options.map((option) => {
                const active = filters[group.key] === option;
                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setFilters((f) => ({ ...f, [group.key]: option }))}
                    className={`cursor-pointer rounded-full border px-3 py-1.5 text-[12.5px] font-medium whitespace-nowrap ${
                      active
                        ? 'border-ink bg-ink text-white'
                        : 'bg-surface text-ink-60 border-black/10'
                    }`}
                  >
                    {option === 'all' ? 'All' : humVal(option)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {actions.error && (
        <div className="border-red-border bg-red-bg text-red mx-9 mt-4 rounded-lg border px-3.5 py-3 text-[13px]">
          {actions.error}
        </div>
      )}

      <div className="flex min-h-0 flex-1 flex-col gap-[18px] overflow-y-auto px-9 pt-[18px] pb-10">
        {shown.length === 0 && (
          <div className="text-ink-40 text-[12.5px]">
            {data.items.length === 0
              ? 'All approvals cleared.'
              : 'No approvals match these filters.'}
          </div>
        )}
        {shown.map((item) => (
          <ApprovalCardView key={item.run_id} item={item} actions={actions} />
        ))}
      </div>
    </div>
  );
}

function ApprovalCardView({
  item,
  actions,
}: {
  item: ApprovalRequestResponse;
  actions: ReturnType<typeof useApprovalActions>;
}) {
  const [open, setOpen] = useState(false);
  const category = categoryStyle(item.category);
  const isEmergency = item.category === 'emergency';
  const busy = actions.isPending(item.run_id);
  const pendingAction = actions.pendingAction(item.run_id);
  const showResponsibility = !isEmergency && !!item.responsibility;
  const severityLabel = item.severity ? humVal(item.severity) : isEmergency ? 'Critical' : null;
  const showSeverity = !!severityLabel;

  const cardBorder = isEmergency ? 'rgba(163,53,44,0.28)' : 'rgba(0,0,0,0.09)';
  const cardBg = isEmergency ? '#FDF6F5' : '#FFFFFF';
  const headerBg = isEmergency ? '#FBEFEE' : '#FFFFFF';

  const tenantMeta = [item.unit ? `Unit ${item.unit}` : null, item.address]
    .filter(Boolean)
    .join(' · ');

  return (
    <div className={`flex rounded-xl ${isEmergency ? 'pulse-red' : ''}`}>
      <div className="min-w-0 flex-1">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-t-xl border px-3.5 py-[9px] text-left"
          style={{ background: headerBg, borderColor: cardBorder }}
        >
          <span className="flex min-w-0 flex-1 items-center gap-2.5 overflow-hidden">
            <span
              className="inline-flex shrink-0 items-center rounded-[20px] border px-2.5 py-0.5 text-[11.5px] whitespace-nowrap"
              style={{
                background: category.bg,
                color: category.ink,
                borderColor: category.border,
                fontWeight: category.emphasis ? 600 : 500,
              }}
            >
              {category.label}
            </span>
            <span className="min-w-0 truncate text-[13px] font-semibold">
              {item.tenant_name ?? 'Unknown'}
              {tenantMeta ? <span className="text-ink-45 font-normal"> · {tenantMeta}</span> : null}
            </span>
          </span>
          <span className="text-ink-35 flex shrink-0 items-center gap-3 text-xs whitespace-nowrap">
            {showSeverity && (
              <span
                className="inline-flex items-center gap-1.5"
                style={{
                  color: isEmergency ? '#A3352C' : 'rgba(23,24,27,0.45)',
                  fontWeight: isEmergency ? 600 : 400,
                }}
              >
                <span
                  className="inline-block h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{
                    background: isEmergency ? '#A3352C' : SEVERITY_DOT[item.severity ?? 'low'],
                  }}
                />
                <span className="text-[13px]">{severityLabel}</span>
              </span>
            )}
            <RelativeTime iso={item.received_at} />
          </span>
        </button>

        <div
          className="flex flex-col gap-4 rounded-b-xl border border-t-0 p-4"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            className="-m-4 cursor-pointer p-4 text-left"
          >
            <div className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-2.5 gap-y-2 text-[13px]">
              <div className="text-ink-45 min-w-0 whitespace-nowrap">Issue summary</div>
              <div className="min-w-0 break-words">
                {item.issue_summary ?? item.original_email.slice(0, 80)}
                {item.appliance_or_system ? (
                  <span className="text-ink-45"> · {humVal(item.appliance_or_system)}</span>
                ) : null}
              </div>

              {showResponsibility && (
                <>
                  <div className="text-ink-45 min-w-0 whitespace-nowrap">Responsibility</div>
                  <div className="flex min-w-0 flex-wrap items-center gap-[7px]">
                    <span>{humVal(item.responsibility)}</span>
                    {item.lease_evidence && (
                      <CitationBadge
                        citation={item.lease_evidence.citation}
                        documentId={item.lease_evidence.document_id}
                        question={item.lease_evidence.question}
                      />
                    )}
                  </div>
                </>
              )}
            </div>
          </button>

          {open && (
            <div className="flex flex-col gap-3.5">
              <div>
                <div className="text-ink-45 mb-2 text-[13px]">Original message</div>
                <div className="text-ink-82 border-l-[1.5px] border-black/12 pl-3 text-[13px] leading-[1.7] whitespace-pre-line">
                  {item.original_email}
                </div>
              </div>
              {item.draft && (
                <div>
                  <div className="text-ink-45 mb-2 text-[13px]">Reply draft</div>
                  <div className="text-ink-82 border-l-[1.5px] border-black/12 pl-3 text-[13px] leading-[1.7] whitespace-pre-line">
                    {item.draft}
                  </div>
                </div>
              )}
              {item.actions.length > 0 && (
                <div>
                  <div className="text-ink-45 mb-2 text-[13px]">Actions</div>
                  <div className="flex min-w-0 flex-wrap gap-1.5">
                    {item.actions.map((action: PlanAction) => {
                      const meta = actionMeta(action);
                      return (
                        <span
                          key={action}
                          className="inline-flex items-center gap-1.5 rounded-[20px] border border-black/[0.09] bg-[#F4F4F4] py-[3px] pr-[11px] pl-[9px] text-[11.5px] font-medium whitespace-nowrap text-[rgba(23,24,27,0.72)]"
                        >
                          <svg
                            viewBox="0 0 16 16"
                            width="12"
                            height="12"
                            fill="none"
                            stroke={meta.ink}
                            strokeWidth="1.4"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="shrink-0"
                            aria-hidden
                          >
                            <path d={meta.icon} />
                          </svg>
                          {meta.label}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {open && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => actions.approve(item.run_id)}
                className="bg-accent border-accent flex cursor-pointer items-center gap-1.5 rounded-lg border px-4 py-[7px] text-[12.5px] font-semibold whitespace-nowrap text-white transition-opacity hover:opacity-[0.87] disabled:cursor-default disabled:opacity-50"
              >
                {pendingAction === 'approve' ? 'Approving…' : 'Approve'}
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => actions.reject(item.run_id)}
                className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-black/14 bg-white px-4 py-[7px] text-[12.5px] font-medium whitespace-nowrap text-[rgba(23,24,27,0.72)] transition-[background,border-color] hover:border-[rgba(178,58,50,0.35)] hover:bg-[#FBEAEA] hover:text-[#8E2A24] disabled:cursor-default disabled:opacity-50"
              >
                {pendingAction === 'reject' ? 'Rejecting…' : 'Reject'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
