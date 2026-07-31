'use client';

import type { ToolCallRecord } from '@/components/runs-provider';
import { splitCitations } from '@/lib/format';
import { useState } from 'react';

const stringify = (value: unknown): string => {
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2) ?? 'null';
};

type LeaseAnswerProps = { answer: string };

function LeaseAnswer({ answer }: LeaseAnswerProps) {
  const { text, citations } = splitCitations(answer);
  return (
    <p className="text-ink font-mono text-[11.5px] leading-relaxed">
      {text}
      {citations.map((citation) => (
        <span
          key={citation}
          className="text-ink/50 mx-0.5 inline-flex items-center rounded-full bg-black/6 px-2 py-px font-mono text-[10.5px] font-medium whitespace-nowrap"
        >
          {citation}
        </span>
      ))}
    </p>
  );
}

type ToolCallRowProps = { call: ToolCallRecord };

export function ToolCallRow({ call }: ToolCallRowProps) {
  const [expanded, setExpanded] = useState(false);
  const question = typeof call.arguments.question === 'string' ? call.arguments.question : null;

  return (
    <div>
      <p className="text-ink-soft mb-2 text-[13px]">{call.reasoning}</p>
      <div className="overflow-hidden rounded-lg border border-black/8">
        <button
          type="button"
          onClick={() => setExpanded((previous) => !previous)}
          className="bg-canvas flex w-full cursor-pointer items-center justify-between gap-2.5 px-3 py-2.5 text-left"
        >
          <span className="flex min-w-0 items-center gap-2">
            {call.done ? (
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                className="shrink-0"
                aria-hidden
              >
                <path
                  d="M5 13l4 4L19 7"
                  stroke={call.isError ? '#963226' : '#2E8B4F'}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <span
                className="border-info/20 border-t-info size-[11px] shrink-0 animate-spin rounded-full border-[1.8px]"
                aria-hidden
              />
            )}
            <span className="text-ink/50 truncate font-mono text-[11px]">
              Tool call <span className="px-1">·</span>
              {call.tool}
            </span>
          </span>
          <svg
            width="11"
            height="11"
            viewBox="0 0 24 24"
            fill="none"
            className={`shrink-0 transition-transform ${expanded ? 'rotate-90' : ''}`}
            aria-hidden
          >
            <path
              d="M9 6l6 6-6 6"
              stroke="rgba(26,27,30,0.45)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        {expanded && (
          <div className="bg-surface flex flex-col gap-2.5 border-t border-black/6 p-3">
            {question === null ? (
              <pre className="text-ink/55 overflow-x-auto font-mono text-[11.5px] leading-relaxed break-words whitespace-pre-wrap">
                {stringify(call.arguments)}
              </pre>
            ) : (
              <p className="text-ink/55 font-mono text-[11.5px] leading-relaxed">
                question:&quot;{question}&quot;
              </p>
            )}

            {call.done &&
              (typeof call.result === 'string' ? (
                <LeaseAnswer answer={call.result} />
              ) : (
                <pre
                  className={`overflow-x-auto font-mono text-[11.5px] leading-relaxed break-words whitespace-pre-wrap ${
                    call.isError ? 'text-danger' : 'text-ink'
                  }`}
                >
                  {stringify(call.result)}
                </pre>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
