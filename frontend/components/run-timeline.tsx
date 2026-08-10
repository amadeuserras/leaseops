'use client';

import { CitationBadge } from '@/components/citation-badge';
import type { DisplayCall, DisplayStep, Field } from '@/lib/run-state';
import Link from 'next/link';
import { useState } from 'react';

export function RunTimeline({ steps }: { steps: DisplayStep[] }) {
  return (
    <div className="relative">
      {steps.map((step) => (
        <StepRow key={step.key} step={step} />
      ))}
    </div>
  );
}

function StepRow({ step }: { step: DisplayStep }) {
  const [collapsed, setCollapsed] = useState(false);
  const hasBody =
    step.category !== null ||
    step.fieldsLeft.length > 0 ||
    step.calls.length > 0 ||
    step.actions !== null ||
    step.draft !== null ||
    step.note !== null ||
    step.showSkeleton;
  const expanded = !collapsed && hasBody;

  return (
    <div className="flex gap-3.5">
      <div className="flex w-3.5 shrink-0 flex-col items-center">
        <span
          className={`mt-1.5 h-[11px] w-[11px] shrink-0 rounded-full ${
            step.status === 'running' ? 'pulse-ring' : ''
          }`}
          style={{ background: step.dotColor }}
        />
        {step.hasNext && <div className="min-h-5 w-[1.5px] flex-1 bg-black/10" />}
      </div>

      <div className="min-w-0 flex-1 pb-[18px]">
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className={`border-hairline bg-surface flex w-full cursor-pointer items-center justify-between gap-3 border px-3.5 py-[9px] text-left ${
            expanded ? 'rounded-t-xl' : 'rounded-xl'
          }`}
        >
          <span className="shrink-0 text-[13px] font-semibold whitespace-nowrap">{step.name}</span>
          <span className="text-ink-40 min-w-0 shrink truncate font-mono text-[11.5px]">
            {step.headerRight}
          </span>
        </button>

        {expanded && (
          <div className="border-hairline bg-surface rounded-b-xl border border-t-0 p-4">
            {step.showSkeleton && <Skeleton />}

            {step.category !== null && (
              <FieldGrid fields={[{ k: 'Category', v: step.category, muted: false }]} />
            )}

            {step.fieldsLeft.length > 0 && (
              <div className="flex flex-wrap items-start gap-x-6 gap-y-[9px]">
                <FieldColumn fields={step.fieldsLeft} />
                {step.fieldsRight.length > 0 && <FieldColumn fields={step.fieldsRight} />}
              </div>
            )}

            {step.calls.length > 0 && (
              <div className="flex flex-col gap-3.5">
                {step.calls.map((call) => (
                  <ToolCallRow key={call.key} call={call} documentId={step.documentId} />
                ))}
                {step.verdictFields.length > 0 && (
                  <div className="mt-1">
                    <FieldGrid fields={step.verdictFields} />
                  </div>
                )}
              </div>
            )}

            {step.actions !== null && (
              <FieldGrid
                fields={[
                  {
                    k: step.node === 'plan' ? 'Suggested actions' : 'Succeeded',
                    v: step.actions,
                    muted: false,
                  },
                ]}
              />
            )}

            {step.draft !== null && (
              <div className="text-ink-82 text-[13px] leading-relaxed whitespace-pre-line">
                {step.draft}
              </div>
            )}

            {step.gate && step.note && (
              <div
                className={`flex items-center justify-between gap-3.5 rounded-[7px] border px-3.5 py-3 text-[13px] leading-tight ${
                  step.gate.pulse ? 'pulse-amber' : ''
                }`}
                style={{
                  background: step.gate.bg,
                  borderColor: step.gate.border,
                  color: step.gate.text,
                }}
              >
                <span className="min-w-0">{step.note}</span>
                {step.status === 'paused' && (
                  <Link
                    href="/approvals"
                    className="flex shrink-0 items-center gap-1.5 text-xs font-semibold underline underline-offset-2 opacity-70 hover:opacity-100"
                  >
                    Open →
                  </Link>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolCallRow({ call, documentId }: { call: DisplayCall; documentId: string | null }) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      {call.reasoning && <div className="text-ink-82 mb-2 text-[13px]">{call.reasoning}</div>}
      <div className="border-hairline overflow-hidden rounded-lg border">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="bg-page flex w-full cursor-pointer items-center justify-between gap-2.5 px-3 py-[9px] text-left"
        >
          <span className="flex min-w-0 items-center gap-2">
            {call.done ? (
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" className="shrink-0">
                <path
                  d="M5 13l4 4L19 7"
                  stroke={call.isError ? '#A3352C' : '#2E8B4F'}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <span className="spinner border-blue/22 border-t-blue h-[11px] w-[11px] shrink-0 rounded-full border-[1.8px]" />
            )}
            <span className="text-ink-50 text-xs whitespace-nowrap">
              Tool call<span className="px-[5px]">·</span>
              {call.tool}
            </span>
          </span>
          <svg
            width="11"
            height="11"
            viewBox="0 0 24 24"
            fill="none"
            className="shrink-0 transition-transform duration-150"
            style={{ transform: `rotate(${open ? 90 : 0}deg)` }}
          >
            <path
              d="M9 6l6 6-6 6"
              stroke="rgba(23,24,27,0.4)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        {open && (
          <div className="border-hairline-soft bg-surface flex flex-col gap-2.5 border-t p-3">
            {call.isQa && (
              <>
                <div className="text-ink-55 text-[12.5px] leading-relaxed">
                  question:&quot;{call.question}&quot;
                </div>
                {call.done && (
                  <div className="text-ink text-[12.5px] leading-[1.7]">
                    {call.answer}
                    {call.citations.map((cite) => (
                      <CitationBadge
                        key={cite}
                        citation={cite}
                        documentId={documentId}
                        question={call.question}
                        className="mx-0.5 align-middle"
                      />
                    ))}
                  </div>
                )}
              </>
            )}
            {call.isVerdict && (
              <div className="text-ink-55 text-[12.5px] leading-relaxed">{call.argsLabel}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function FieldColumn({ fields }: { fields: Field[] }) {
  return (
    <div className="flex min-w-0 flex-1 basis-60 flex-col gap-[9px]">
      {fields.map((field) => (
        <div
          key={field.k}
          className="grid min-w-0 grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-x-2.5 gap-y-2 text-[13px]"
        >
          <div className="text-ink-45 min-w-0 whitespace-nowrap">{field.k}</div>
          <div className={`min-w-0 break-words ${field.muted ? 'text-ink-35' : 'text-ink'}`}>
            {field.v}
          </div>
        </div>
      ))}
    </div>
  );
}

function FieldGrid({ fields }: { fields: Field[] }) {
  return (
    <div className="grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-x-2.5 gap-y-2 text-[13px]">
      {fields.map((field) => (
        <div key={field.k} className="contents">
          <div className="text-ink-45 min-w-0 whitespace-nowrap">{field.k}</div>
          <div className={`min-w-0 break-words ${field.muted ? 'text-ink-35' : 'text-ink'}`}>
            {field.v}
          </div>
        </div>
      ))}
    </div>
  );
}

function Skeleton() {
  return (
    <div className="flex flex-col gap-[9px]">
      <div className="shimmer-bar h-[9px] w-[62%] rounded" />
      <div className="shimmer-bar h-[9px] w-[38%] rounded [animation-delay:0.15s]" />
    </div>
  );
}
