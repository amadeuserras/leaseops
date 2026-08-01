'use client';

import { approveRun, listApprovals, rejectRun } from '@/lib/api';
import type { PendingApproval } from '@/lib/api';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

export type ApprovalDecision = {
  outcome: 'approved' | 'rejected';
  reason: string | null;
};

type ApprovalsContextValue = {
  items: PendingApproval[];
  decisions: Record<string, ApprovalDecision>;
  pendingCount: number;
  clearedToday: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  approve: (runId: string) => Promise<void>;
  reject: (runId: string) => Promise<void>;
};

const ApprovalsContext = createContext<ApprovalsContextValue | null>(null);

const toMessage = (cause: unknown): string =>
  cause instanceof Error ? cause.message : 'could not load approvals';

type ApprovalsProviderProps = { children: ReactNode };

export function ApprovalsProvider({ children }: ApprovalsProviderProps) {
  const [items, setItems] = useState<PendingApproval[]>([]);
  const [decisions, setDecisions] = useState<Record<string, ApprovalDecision>>({});
  const [clearedToday, setClearedToday] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const next = await listApprovals();
      setItems(next);
      setError(null);
    } catch (cause: unknown) {
      setError(toMessage(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const approve = useCallback(async (runId: string) => {
    await approveRun(runId);
    setDecisions((previous) => ({ ...previous, [runId]: { outcome: 'approved', reason: null } }));
    setItems((previous) => previous.filter((item) => item.run_id !== runId));
    setClearedToday((count) => count + 1);
  }, []);

  const reject = useCallback(async (runId: string) => {
    await rejectRun(runId);
    setDecisions((previous) => ({ ...previous, [runId]: { outcome: 'rejected', reason: null } }));
    setItems((previous) => previous.filter((item) => item.run_id !== runId));
    setClearedToday((count) => count + 1);
  }, []);

  const pendingCount = items.length;

  const value = useMemo<ApprovalsContextValue>(
    () => ({
      items,
      decisions,
      pendingCount,
      clearedToday,
      loading,
      error,
      refresh,
      approve,
      reject,
    }),
    [items, decisions, pendingCount, clearedToday, loading, error, refresh, approve, reject],
  );

  return <ApprovalsContext.Provider value={value}>{children}</ApprovalsContext.Provider>;
}

export const useApprovals = (): ApprovalsContextValue => {
  const context = useContext(ApprovalsContext);
  if (context === null) throw new Error('useApprovals must be used inside <ApprovalsProvider>');
  return context;
};
