'use client';

import { ApprovalCard } from '@/components/approval-card';
import { useApprovals } from '@/components/approvals-provider';

export default function ApprovalsPage() {
  const { items, decisions, pendingCount, loading, error, approve, reject } = useApprovals();

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 px-7 pt-[22px] pb-2">
        <div className="flex items-center justify-between">
          <h1 className="m-0 text-[18px] font-bold tracking-[-0.01em]">Approvals</h1>
          <span className="text-ink/40 font-mono text-[11.5px]">{pendingCount} pending</span>
        </div>
        <p className="text-ink/50 mt-[3px] text-[12.5px]">
          Agent-drafted actions waiting on your sign-off
        </p>
      </div>

      <div className="custom-scrollbar min-h-0 flex-1 overflow-y-auto px-7 pt-3 pb-6">
        {error !== null && (
          <div className="border-danger-line bg-danger-bg text-danger rounded-[10px] border px-4 py-3 text-[13px]">
            {error}
          </div>
        )}

        {loading && <p className="text-ink/45 text-[13px]">Loading approvals…</p>}

        {!loading && error === null && items.length === 0 && (
          <div className="bg-surface text-ink/60 rounded-[10px] border border-black/8 p-5 text-[13px] leading-relaxed">
            Nothing is waiting for approval. Run a message from the inbox — anything the agent wants
            to write lands here first.
          </div>
        )}

        <div className="grid grid-cols-1 items-start gap-4 xl:grid-cols-2">
          {items.map((item) => (
            <ApprovalCard
              key={item.run_id}
              item={item}
              decision={decisions[item.run_id] ?? null}
              onApprove={() => approve(item.run_id)}
              onReject={(reason) => reject(item.run_id, reason)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
