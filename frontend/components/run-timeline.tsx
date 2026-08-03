"use client";

import Link from "next/link";
import { useState } from "react";

import type { DisplayCall, DisplayStep, Field } from "@/lib/run-state";

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
            step.status === "running" ? "pulse-ring" : ""
          }`}
          style={{ background: step.dotColor }}
        />
        {step.hasNext && <div className="min-h-5 w-[1.5px] flex-1 bg-black/10" />}
      </div>

      <div className="min-w-0 flex-1 pb-[18px]">
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className={`flex w-full cursor-pointer items-center justify-between gap-3 border border-hairline bg-surface px-3.5 py-[9px] text-left ${
            expanded ? "rounded-t-xl" : "rounded-xl"
          }`}
        >
          <span className="shrink-0 text-[13px] font-semibold whitespace-nowrap">
            {step.name}
          </span>
          <span className="min-w-0 shrink truncate font-mono text-[11.5px] text-ink-40">
            {step.headerRight}
          </span>
        </button>

        {expanded && (
          <div className="rounded-b-xl border border-t-0 border-hairline bg-surface p-4">
            {step.showSkeleton && <Skeleton />}

            {step.category !== null && (
              <FieldGrid fields={[{ k: "Category", v: step.category, muted: false }]} />
            )}

            {step.fieldsLeft.length > 0 && (
              <div className="flex flex-wrap items-start gap-x-6 gap-y-[9px]">
                <FieldColumn fields={step.fieldsLeft} />
                {step.fieldsRight.length > 0 && (
                  <FieldColumn fields={step.fieldsRight} />
                )}
              </div>
            )}

            {step.calls.length > 0 && (
              <div className="flex flex-col gap-3.5">
                {step.calls.map((call) => (
                  <ToolCallRow key={call.key} call={call} />
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
                    k: step.node === "plan" ? "Suggested actions" : "Actions taken",
                    v: step.actions,
                    muted: false,
                  },
                ]}
              />
            )}

            {step.draft !== null && (
              <div className="text-[13px] leading-relaxed whitespace-pre-line text-ink-82">
                {step.draft}
              </div>
            )}

            {step.gate && step.note && (
              <div
                className={`flex items-center justify-between gap-3.5 rounded-[7px] border px-3.5 py-3 text-[13px] leading-tight ${
                  step.gate.pulse ? "pulse-amber" : ""
                }`}
                style={{
                  background: step.gate.bg,
                  borderColor: step.gate.border,
                  color: step.gate.text,
                }}
              >
                <span className="min-w-0">{step.note}</span>
                <Link
                  href="/approvals"
                  className="flex shrink-0 items-center gap-1.5 text-xs font-semibold underline underline-offset-2 opacity-70 hover:opacity-100"
                >
                  Open →
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolCallRow({ call }: { call: DisplayCall }) {
  const [open, setOpen] = useState(false);

  return (
    <div>
      {call.reasoning && (
        <div className="mb-2 text-[13px] text-ink-82">{call.reasoning}</div>
      )}
      <div className="overflow-hidden rounded-lg border border-hairline">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex w-full cursor-pointer items-center justify-between gap-2.5 bg-page px-3 py-[9px] text-left"
        >
          <span className="flex min-w-0 items-center gap-2">
            {call.done ? (
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                className="shrink-0"
              >
                <path
                  d="M5 13l4 4L19 7"
                  stroke={call.isError ? "#A3352C" : "#2E8B4F"}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <span className="spinner h-[11px] w-[11px] shrink-0 rounded-full border-[1.8px] border-blue/22 border-t-blue" />
            )}
            <span className="text-xs whitespace-nowrap text-ink-50">
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
          <div className="flex flex-col gap-2.5 border-t border-hairline-soft bg-surface p-3">
            {call.isQa && (
              <>
                <div className="text-[12.5px] leading-relaxed text-ink-55">
                  question:&quot;{call.question}&quot;
                </div>
                {call.done && (
                  <div className="text-[12.5px] leading-[1.7] text-ink">
                    {call.answer}
                    {call.citations.map((cite) => (
                      <span
                        key={cite}
                        className="mx-0.5 inline-flex cursor-pointer items-center gap-1 rounded-[20px] bg-black/[0.055] px-2 py-px align-middle text-[11.5px] font-medium whitespace-nowrap text-ink-50 hover:bg-black/10 hover:text-ink"
                      >
                        {cite}
                      </span>
                    ))}
                  </div>
                )}
              </>
            )}
            {call.isVerdict && (
              <div className="text-[12.5px] leading-relaxed text-ink-55">
                {call.argsLabel}
              </div>
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
          <div className="min-w-0 whitespace-nowrap text-ink-45">{field.k}</div>
          <div
            className={`min-w-0 break-words ${field.muted ? "text-ink-35" : "text-ink"}`}
          >
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
          <div className="min-w-0 whitespace-nowrap text-ink-45">{field.k}</div>
          <div
            className={`min-w-0 break-words ${field.muted ? "text-ink-35" : "text-ink"}`}
          >
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
