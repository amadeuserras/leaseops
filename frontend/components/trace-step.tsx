'use client';

import type { ApprovalDecision } from '@/components/approvals-provider';
import { Pill } from '@/components/pill';
import type { TraceStep as TraceStepData } from '@/lib/run-reducer';
import { ToolCallRow } from '@/components/tool-call-row';
import type { ApprovalRequest } from '@/lib/api';
import { formatCost, formatDuration, formatTokens, humanize } from '@/lib/format';
import { stepDot, stepPill } from '@/lib/status';
import type { StepStatus } from '@/lib/status';
import { useState } from 'react';

const EXTRACT_LEFT = ['tenant_name', 'address', 'unit', 'appliance_or_system'];
const EXTRACT_RIGHT = ['severity', 'issue_summary'];

const readField = (output: Record<string, unknown> | null, key: string): string | null => {
  const value = output?.[key];
  if (value === undefined) return null;
  if (value === null) return 'null';
  return String(value);
};

type FieldGridProps = { fields: { key: string; value: string }[] };

function FieldGrid({ fields }: FieldGridProps) {
  return (
    <div className="grid min-w-0 grid-cols-[auto_1fr] gap-x-2.5 gap-y-2 font-mono text-[13px]">
      {fields.map((field) => (
        <div key={field.key} className="contents">
          <span className="text-ink/45">{field.key}</span>
          <span className={`min-w-0 break-words ${field.value === 'null' ? 'text-ink/35' : ''}`}>
            {field.value}
          </span>
        </div>
      ))}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-col gap-2.5">
      <div className="skeleton-line animate-shimmer h-[9px] w-[62%] rounded" />
      <div className="skeleton-line animate-shimmer h-[9px] w-[38%] rounded" />
    </div>
  );
}

type StepBodyProps = {
  step: TraceStepData;
  pausedRequest: ApprovalRequest | null;
  decision: ApprovalDecision | null;
};

function StepBody({ step, pausedRequest, decision }: StepBodyProps) {
  const { node, output, calls } = step;

  if (node === 'classify') {
    const category = readField(output, 'category');
    if (category === null) return <Skeleton />;
    return <FieldGrid fields={[{ key: 'category', value: category }]} />;
  }

  if (node === 'extract') {
    if (output === null) return <Skeleton />;
    const toFields = (keys: string[]) =>
      keys
        .map((key) => ({ key, value: readField(output, key) }))
        .filter((field): field is { key: string; value: string } => field.value !== null);
    return (
      <div className="flex items-start gap-6">
        <div className="min-w-0 flex-1">
          <FieldGrid fields={toFields(EXTRACT_LEFT)} />
        </div>
        <div className="min-w-0 flex-1">
          <FieldGrid fields={toFields(EXTRACT_RIGHT)} />
        </div>
      </div>
    );
  }

  if (node === 'lease_check') {
    const verdict = ['lease_addresses_issue', 'responsibility']
      .map((key) => ({ key, value: readField(output, key) }))
      .filter((field): field is { key: string; value: string } => field.value !== null);

    if (calls.length === 0 && verdict.length === 0) {
      return output === null ? (
        <Skeleton />
      ) : (
        <p className="text-ink/55 text-[13px]">
          No lease on file for this sender — the lease check was skipped.
        </p>
      );
    }

    return (
      <div className="flex flex-col gap-3.5">
        {calls.map((call, index) => (
          <ToolCallRow key={`${call.tool}-${index}`} call={call} />
        ))}
        {verdict.length > 0 && (
          <div className="mt-1">
            <FieldGrid fields={verdict} />
          </div>
        )}
      </div>
    );
  }

  if (node === 'plan') {
    if (output === null) return <Skeleton />;
    const actions = output.actions;
    const value =
      Array.isArray(actions) ? actions.map(String).join(', ') : readField(output, 'actions');
    if (value === null) return <Skeleton />;
    return <FieldGrid fields={[{ key: 'actions', value }]} />;
  }

  if (node === 'draft') {
    const draft = readField(output, 'draft');
    if (draft === null) return <Skeleton />;
    return <p className="text-ink-soft text-[13px] leading-relaxed whitespace-pre-line">{draft}</p>;
  }

  if (node === 'approval' || node === 'approval_gate') {
    if (decision !== null) {
      const approved = decision.outcome === 'approved';
      return (
        <div
          className={`rounded-[7px] border px-3.5 py-3 text-[13px] leading-normal ${
            approved
              ? 'border-success-line bg-success-bg text-success'
              : 'border-danger-line bg-danger-bg text-danger'
          }`}
        >
          {approved
            ? 'Approved by a human — the run resumed and the action was executed.'
            : `Rejected${decision.reason === null ? '' : `: ${decision.reason}`}`}
        </div>
      );
    }

    if (step.status === 'paused') {
      const planned =
        pausedRequest?.actions?.length ? pausedRequest.actions.join(', ') : 'planned';
      return (
        <div className="animate-pulse-amber border-warn-line bg-warn-bg text-warn rounded-[7px] border px-3.5 py-3 text-[13px] leading-normal">
          Waiting for human approval — every{' '}
          <span className="font-mono">{planned}</span> action is routed for review before it
          executes.
        </div>
      );
    }

    const approvedField = readField(output, 'approved');
    if (approvedField === null) return <Skeleton />;
    return (
      <div
        className={`rounded-[7px] border px-3.5 py-3 text-[13px] leading-normal ${
          approvedField === 'True' || approvedField === 'true'
            ? 'border-success-line bg-success-bg text-success'
            : 'border-danger-line bg-danger-bg text-danger'
        }`}
      >
        {approvedField === 'True' || approvedField === 'true'
          ? 'Approved — proceeding to execute.'
          : `Rejected${readField(output, 'rejection_reason') === null ? '' : `: ${readField(output, 'rejection_reason')}`}`}
      </div>
    );
  }

  if (node === 'execute') {
    if (calls.length === 0 && output === null) return <Skeleton />;
    return (
      <div className="flex flex-col gap-3.5">
        {calls.map((call, index) => (
          <ToolCallRow key={`${call.tool}-${index}`} call={call} />
        ))}
        {calls.length === 0 && (
          <p className="text-ink/55 text-[13px]">No write actions were required.</p>
        )}
      </div>
    );
  }

  if (output === null) return <Skeleton />;
  return (
    <pre className="text-ink/70 overflow-x-auto font-mono text-[12px] whitespace-pre-wrap">
      {JSON.stringify(output, null, 2)}
    </pre>
  );
}

type TraceStepProps = {
  step: TraceStepData;
  isLast: boolean;
  pausedRequest: ApprovalRequest | null;
  decision: ApprovalDecision | null;
};

export function TraceStep({ step, isLast, pausedRequest, decision }: TraceStepProps) {
  const [collapsed, setCollapsed] = useState(false);
  const status = step.status as StepStatus;
  const running = step.status === 'running';

  const usage =
    step.model === null
      ? step.endedAt === null
        ? running
          ? 'streaming…'
          : '—'
        : formatDuration(step.endedAt - step.startedAt)
      : `${step.model} · ${formatTokens(step.inputTokens)} in / ${formatTokens(step.outputTokens)} out tok · ${formatCost(step.costUsd)}`;

  return (
    <div className="flex gap-3.5">
      <div className="flex w-3.5 shrink-0 flex-col items-center">
        <span
          className={`mt-1.5 size-[11px] shrink-0 rounded-full ${stepDot[status]} ${
            running ? 'animate-pulse-ring' : ''
          }`}
          aria-hidden
        />
        {!isLast && <span className="min-h-5 w-[1.5px] flex-1 bg-black/10" aria-hidden />}
      </div>

      <div className="min-w-0 flex-1 pb-[18px]">
        <button
          type="button"
          onClick={() => setCollapsed((previous) => !previous)}
          className={`bg-surface flex w-full cursor-pointer items-center justify-between gap-3 border border-black/8 px-3.5 py-2.5 text-left ${
            collapsed ? 'rounded-lg' : 'rounded-t-lg'
          }`}
        >
          <span className="flex min-w-0 flex-auto items-center gap-2.5 overflow-hidden">
            <span className="truncate text-[13px] font-semibold">{step.node}</span>
            <Pill className={`${stepPill[status]} px-2 py-px text-[10.5px]`}>
              {humanize(step.status)}
            </Pill>
          </span>
          <span className="text-ink/40 min-w-0 flex-initial truncate font-mono text-[11.5px]">
            {usage}
          </span>
        </button>

        {!collapsed && (
          <div className="bg-surface rounded-b-lg border border-t-0 border-black/8 p-4">
            <StepBody step={step} pausedRequest={pausedRequest} decision={decision} />
          </div>
        )}
      </div>
    </div>
  );
}
