"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { approveRun, rejectRun } from "@/lib/api";

type Pending = { runId: string; action: "approve" | "reject" } | null;

export function useApprovalActions() {
  const router = useRouter();
  const [pending, setPending] = useState<Pending>(null);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (runId: string, action: "approve" | "reject") => {
      setPending({ runId, action });
      setError(null);
      try {
        await (action === "approve" ? approveRun(runId) : rejectRun(runId));
        router.refresh();
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause));
      } finally {
        setPending(null);
      }
    },
    [router],
  );

  return {
    approve: useCallback((runId: string) => run(runId, "approve"), [run]),
    reject: useCallback((runId: string) => run(runId, "reject"), [run]),
    isPending: (runId: string) => pending?.runId === runId,
    pendingAction: (runId: string) =>
      pending?.runId === runId ? pending.action : null,
    error,
  };
}
