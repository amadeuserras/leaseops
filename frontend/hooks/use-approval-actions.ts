'use client';

import { useAppContext } from '@/context/app-context';
import { approveRun, rejectRun } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';

type Pending = { runId: string; action: 'approve' | 'reject' } | null;

export function useApprovalActions() {
  const router = useRouter();
  const { triggerApprovalsCount } = useAppContext();
  const [pending, setPending] = useState<Pending>(null);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (runId: string, action: 'approve' | 'reject') => {
      setPending({ runId, action });
      setError(null);
      try {
        await (action === 'approve' ? approveRun(runId) : rejectRun(runId));
        triggerApprovalsCount();
        router.refresh();
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause));
      } finally {
        setPending(null);
      }
    },
    [router, triggerApprovalsCount],
  );

  return {
    approve: useCallback((runId: string) => run(runId, 'approve'), [run]),
    reject: useCallback((runId: string) => run(runId, 'reject'), [run]),
    isPending: (runId: string) => pending?.runId === runId,
    pendingAction: (runId: string) => (pending?.runId === runId ? pending.action : null),
    error,
  };
}
