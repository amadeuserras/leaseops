'use client';

import { useAppContext } from '@/context/app-context';
import { streamRerun, streamRun, type StreamEvent } from '@/lib/api';
import { applyStreamEvent, emptyRunState, type RunState } from '@/lib/run-state';
import { useCallback, useEffect, useRef, useState } from 'react';

export function useRunStream(emailId: string, initial: RunState) {
  const { triggerApprovalsCount } = useAppContext();
  const [state, setState] = useState<RunState>(initial);
  const abortRef = useRef<AbortController | null>(null);
  const startedAtRef = useRef(0);

  useEffect(() => {
    setState(initial);
  }, [initial]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const runStream = useCallback(
    (stream: (emailId: string, signal: AbortSignal) => AsyncGenerator<StreamEvent>) => {
      stop();
      const controller = new AbortController();
      abortRef.current = controller;
      startedAtRef.current = Date.now();
      setState({ ...emptyRunState(), live: true, phase: 'running' });

      void (async () => {
        try {
          for await (const event of stream(emailId, controller.signal)) {
            const elapsed = (Date.now() - startedAtRef.current) / 1000;
            setState((current) => applyStreamEvent(current, event, elapsed));
            if (event.type === 'paused') {
              triggerApprovalsCount();
            }
          }
        } catch (error) {
          if (controller.signal.aborted) return;
          setState((current) => ({
            ...current,
            live: false,
            phase: 'failed',
            error: error instanceof Error ? error.message : String(error),
          }));
        } finally {
          if (abortRef.current === controller) abortRef.current = null;
        }
      })();
    },
    [emailId, stop, triggerApprovalsCount],
  );

  const start = useCallback(() => {
    runStream(streamRun);
  }, [runStream]);

  const rerun = useCallback(() => {
    runStream(streamRerun);
  }, [runStream]);

  useEffect(() => {
    if (!state.live) return;
    const id = window.setInterval(() => {
      setState((current) =>
        current.live
          ? {
              ...current,
              stats: {
                ...current.stats,
                elapsed: (Date.now() - startedAtRef.current) / 1000,
              },
            }
          : current,
      );
    }, 100);
    return () => window.clearInterval(id);
  }, [state.live]);

  useEffect(() => stop, [stop]);

  return { state, start, rerun, stop };
}
