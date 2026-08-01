'use client';

import type {
  ApprovalAction,
  ApprovalCategory,
  ApprovalQueueItem,
  ApprovalSeverity,
} from '@/lib/api';
import { listApprovalQueue } from '@/lib/api';
import { formatRelativeTime } from '@/lib/format';
import {
  approvalActionButton,
  approvalActionDoneLabel,
  approvalActionLabel,
  approvalCategoryBadge,
  approvalCategoryLabel,
  approvalResponsibilityLabel,
  approvalSeverityDot,
} from '@/lib/status';
import { useEffect, useMemo, useState } from 'react';

type CategoryFilter = ApprovalCategory | 'all';
type SeverityFilter = ApprovalSeverity | 'all';
type ResponsibilityFilter = 'landlord' | 'tenant' | 'all';

const CATEGORY_OPTIONS: CategoryFilter[] = ['all', 'emergency', 'maintenance', 'lease_question'];
const SEVERITY_OPTIONS: SeverityFilter[] = ['all', 'critical', 'high', 'medium', 'low'];
const RESPONSIBILITY_OPTIONS: ResponsibilityFilter[] = ['all', 'landlord', 'tenant'];

const categoryOptionLabel = (value: CategoryFilter): string =>
  value === 'all' ? 'All' : approvalCategoryLabel[value];

const responsibilityOptionLabel = (value: ResponsibilityFilter): string =>
  value === 'all' ? 'All' : approvalResponsibilityLabel[value];

type FilterChipProps = { label: string; active: boolean; onSelect: () => void };

function FilterChip({ label, active, onSelect }: FilterChipProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`cursor-pointer rounded-full border px-2.5 py-[3px] text-[11px] font-medium whitespace-nowrap transition-colors ${
        active
          ? 'border-ink bg-ink text-white'
          : 'bg-surface text-ink/60 hover:bg-muted border-black/12'
      }`}
    >
      {label}
    </button>
  );
}

type FilterGroupProps<T extends string> = {
  label: string;
  options: T[];
  active: T;
  optionLabel: (value: T) => string;
  onSelect: (value: T) => void;
};

function FilterGroup<T extends string>({
  label,
  options,
  active,
  optionLabel,
  onSelect,
}: FilterGroupProps<T>) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-ink/35 text-[11px] whitespace-nowrap">{label}</span>
      <div className="flex flex-wrap gap-1">
        {options.map((option) => (
          <FilterChip
            key={option}
            label={optionLabel(option)}
            active={active === option}
            onSelect={() => onSelect(option)}
          />
        ))}
      </div>
    </div>
  );
}

type ApprovalRowProps = {
  item: ApprovalQueueItem;
  isOpen: boolean;
  onToggle: () => void;
  resolvedAction: ApprovalAction | null;
  onRunAction: (action: ApprovalAction) => void;
};

function ApprovalRow({ item, isOpen, onToggle, resolvedAction, onRunAction }: ApprovalRowProps) {
  const isEmergency = item.category === 'emergency';
  const who = [item.tenant_name, item.unit === null ? null : `Unit ${item.unit}`, item.address]
    .filter((part): part is string => part !== null)
    .join(' · ');

  return (
    <div
      onClick={onToggle}
      className={`bg-surface flex cursor-pointer flex-col gap-3.5 rounded-[14px] border p-[18px] shadow-[0_1px_2px_rgba(0,0,0,0.04)] ${
        isEmergency ? 'border-danger/30 animate-pulse-danger' : 'border-black/7'
      } ${resolvedAction !== null ? 'opacity-60' : ''}`}
    >
      <div className="flex items-start gap-2.5">
        <span
          className={`inline-flex shrink-0 items-center rounded-full border px-2.5 py-[3px] text-[11.5px] font-semibold whitespace-nowrap ${approvalCategoryBadge[item.category]}`}
        >
          {approvalCategoryLabel[item.category]}
        </span>
        <div className="min-w-0 flex-1 text-[14.5px] leading-tight font-semibold tracking-[-0.01em] text-pretty">
          {item.issue_summary}
        </div>
        <div
          className={`mt-0.5 flex items-center gap-1.5 text-[11.5px] whitespace-nowrap ${
            item.severity === 'critical' ? 'text-danger font-semibold' : 'text-ink/40'
          }`}
        >
          {!isEmergency && (
            <span className={`size-1.5 rounded-full ${approvalSeverityDot[item.severity]}`} />
          )}
          {item.severity}
        </div>
        <div className="text-ink/32 mt-0.5 text-[11.5px] whitespace-nowrap">
          {formatRelativeTime(item.received_at)}
        </div>
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          className={`text-ink/40 mt-0.5 shrink-0 transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`}
        >
          <path
            d="M6 9l6 6 6-6"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      <div className="grid grid-cols-[96px_1fr] items-baseline gap-x-1.5 gap-y-2 text-[12.5px]">
        <div className="text-ink/40">Tenant</div>
        <div>{who}</div>
        {!isEmergency && item.responsibility !== null && (
          <>
            <div className="text-ink/40">Responsibility</div>
            <div className="flex flex-wrap items-center gap-1.5">
              <span>{approvalResponsibilityLabel[item.responsibility]}</span>
              {item.lease_citation !== null && (
                <span className="text-ink/50 rounded-full bg-black/6 px-2 py-px font-mono text-[10.5px] font-medium whitespace-nowrap">
                  {item.lease_citation}
                </span>
              )}
            </div>
          </>
        )}
        <div className="text-ink/40">Category</div>
        <div>{item.issue_category}</div>
      </div>

      {isOpen && (
        <div className="flex flex-col gap-3 border-t border-black/7 pt-3.5">
          <div className="flex flex-col gap-1.5">
            <div className="text-ink/40 text-[12.5px]">Original email</div>
            <div className="text-ink/62 border-l-2 border-black/10 pl-2.5 text-[12.5px] leading-relaxed whitespace-pre-line">
              {item.original_email}
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="text-ink/40 text-[12.5px]">Reply draft</div>
            <div className="text-ink-soft bg-canvas rounded-[9px] p-3 text-[12.5px] leading-relaxed whitespace-pre-line">
              {item.draft}
            </div>
          </div>
        </div>
      )}

      {resolvedAction === null ? (
        <div className="flex flex-wrap gap-2">
          {item.actions.map((action) => (
            <button
              key={action}
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onRunAction(action);
              }}
              className={`cursor-pointer rounded-[7px] border px-3.5 py-[7px] text-[12px] font-semibold transition-colors ${approvalActionButton[action]}`}
            >
              {approvalActionLabel[action]}
            </button>
          ))}
        </div>
      ) : (
        <div className="border-success-line bg-success-bg text-success flex items-center gap-2 rounded-md border px-3 py-2.5 text-[12.5px] font-semibold">
          <span className="bg-success-dot size-[7px] shrink-0 rounded-full" aria-hidden />
          {approvalActionDoneLabel[resolvedAction]}
        </div>
      )}
    </div>
  );
}

export default function ApprovalsPage() {
  const [items, setItems] = useState<ApprovalQueueItem[]>([]);
  const [clearedToday, setClearedToday] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [category, setCategory] = useState<CategoryFilter>('all');
  const [severity, setSeverity] = useState<SeverityFilter>('all');
  const [responsibility, setResponsibility] = useState<ResponsibilityFilter>('all');

  const [openId, setOpenId] = useState<string | null>(null);
  const [resolved, setResolved] = useState<Record<string, ApprovalAction>>({});

  useEffect(() => {
    listApprovalQueue()
      .then((response) => {
        setItems(response.items);
        setClearedToday(response.cleared_today);
      })
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : 'could not load approvals'),
      )
      .finally(() => setLoading(false));
  }, []);

  const shown = useMemo(
    () =>
      items.filter(
        (item) =>
          (category === 'all' || item.category === category) &&
          (severity === 'all' || item.severity === severity) &&
          (responsibility === 'all' || item.responsibility === responsibility),
      ),
    [items, category, severity, responsibility],
  );

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 px-7 pt-[22px] pb-1.5">
        <div className="flex items-baseline justify-between gap-4">
          <div>
            <h1 className="m-0 text-[18px] font-bold tracking-[-0.01em]">Approvals</h1>
            <p className="text-ink/45 mt-[3px] text-[12.5px]">
              Triaged tenant email, drafted reply, waiting on your sign-off
            </p>
          </div>
          <span className="text-ink/38 text-[12.5px] whitespace-nowrap">
            {shown.length} of {items.length} pending · {clearedToday} cleared today
          </span>
        </div>
      </div>

      <div className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-2 px-7 pt-1.5">
        <FilterGroup
          label="Category"
          options={CATEGORY_OPTIONS}
          active={category}
          optionLabel={categoryOptionLabel}
          onSelect={setCategory}
        />
        <FilterGroup
          label="Severity"
          options={SEVERITY_OPTIONS}
          active={severity}
          optionLabel={(value) => (value === 'all' ? 'All' : value)}
          onSelect={setSeverity}
        />
        <FilterGroup
          label="Responsibility"
          options={RESPONSIBILITY_OPTIONS}
          active={responsibility}
          optionLabel={responsibilityOptionLabel}
          onSelect={setResponsibility}
        />
      </div>

      <div className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-7 pt-3.5 pb-6">
        {error !== null && (
          <div className="border-danger-line bg-danger-bg text-danger rounded-[10px] border px-4 py-3 text-[13px]">
            {error}
          </div>
        )}

        {loading && <p className="text-ink/45 text-[13px]">Loading approvals…</p>}

        {!loading && error === null && shown.length === 0 && (
          <div className="text-ink/35 rounded-xl border border-dashed border-black/12 p-8 text-center text-[12.5px]">
            No approvals match these filters
          </div>
        )}

        <div className="flex flex-col gap-3.5">
          {shown.map((item) => (
            <ApprovalRow
              key={item.run_id}
              item={item}
              isOpen={openId === item.run_id}
              onToggle={() =>
                setOpenId((current) => (current === item.run_id ? null : item.run_id))
              }
              resolvedAction={resolved[item.run_id] ?? null}
              onRunAction={(action) =>
                setResolved((current) => ({ ...current, [item.run_id]: action }))
              }
            />
          ))}
        </div>
      </div>
    </div>
  );
}
