'use client';

import type { RunState } from '@/lib/run-reducer';
import { formatCost, formatDuration, formatTokens } from '@/lib/format';
import { useEffect, useState } from 'react';

const useElapsed = (run: RunState | undefined): number => {
  const streaming = run?.status === 'streaming';
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!streaming) return;
    const timer = setInterval(() => setNow(Date.now()), 80);
    return () => clearInterval(timer);
  }, [streaming]);

  if (run === undefined) return 0;
  return (run.endedAt ?? now) - run.startedAt;
};

type StatProps = { label: string; value: string };

function Stat({ label, value }: StatProps) {
  return (
    <div>
      <span className="text-ink/40">{label}</span>
      &nbsp;&nbsp;{value}
    </div>
  );
}

type RunStatsProps = { run: RunState | undefined };

export function RunStats({ run }: RunStatsProps) {
  const elapsed = useElapsed(run);

  return (
    <div className="bg-canvas text-ink/55 flex shrink-0 items-center gap-7 border-t border-black/8 px-7 py-3 font-mono text-[12px]">
      <Stat
        label="tokens"
        value={run === undefined ? '—' : formatTokens(run.inputTokens + run.outputTokens)}
      />
      <Stat label="cost" value={run === undefined ? '—' : formatCost(run.costUsd)} />
      <Stat label="elapsed" value={run === undefined ? '—' : formatDuration(elapsed)} />
      <Stat label="steps" value={run === undefined ? '—' : String(run.steps.length)} />
    </div>
  );
}
