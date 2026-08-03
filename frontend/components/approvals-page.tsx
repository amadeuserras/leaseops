"use client";

import { useState } from "react";

import { useApprovalActions } from "@/hooks/use-approval-actions";
import type { ApprovalListResponse, ApprovalRequestResponse } from "@/lib/api";
import { fmtRelative, humVal } from "@/lib/format";

const CATEGORY_STYLE: Record<
  string,
  { label: string; ink: string; bg: string; border: string; emphasis: boolean }
> = {
  emergency: {
    label: "Emergency",
    ink: "#A3352C",
    bg: "rgba(163,53,44,0.08)",
    border: "rgba(163,53,44,0.28)",
    emphasis: true,
  },
  maintenance: {
    label: "Maintenance",
    ink: "#2C7BC8",
    bg: "rgba(44,123,200,0.08)",
    border: "rgba(44,123,200,0.3)",
    emphasis: false,
  },
  lease_question: {
    label: "Lease question",
    ink: "rgba(23,24,27,0.55)",
    bg: "rgba(0,0,0,0.04)",
    border: "rgba(0,0,0,0.12)",
    emphasis: false,
  },
  not_our_problem: {
    label: "Not our problem",
    ink: "rgba(23,24,27,0.55)",
    bg: "rgba(0,0,0,0.04)",
    border: "rgba(0,0,0,0.12)",
    emphasis: false,
  },
};

function categoryStyle(category: string) {
  return CATEGORY_STYLE[category] ?? CATEGORY_STYLE.lease_question;
}

const SEVERITY_DOT: Record<string, string> = {
  critical: "#A3352C",
  high: "#D9483C",
  medium: "#E0A227",
  low: "#8B9099",
};

type Filters = { category: string; severity: string; responsibility: string };

const FILTER_GROUPS: { key: keyof Filters; label: string; options: string[] }[] = [
  {
    key: "category",
    label: "Category",
    options: ["all", "emergency", "maintenance", "lease_question", "not_our_problem"],
  },
  { key: "severity", label: "Severity", options: ["all", "critical", "high", "medium", "low"] },
  {
    key: "responsibility",
    label: "Responsibility",
    options: ["all", "landlord", "tenant", "shared", "unclear"],
  },
];

export function ApprovalsPage({ data }: { data: ApprovalListResponse }) {
  const [filters, setFilters] = useState<Filters>({
    category: "all",
    severity: "all",
    responsibility: "all",
  });
  const actions = useApprovalActions();

  const shown = data.items.filter(
    (item) =>
      (filters.category === "all" || item.category === filters.category) &&
      (filters.severity === "all" || item.severity === filters.severity) &&
      (filters.responsibility === "all" ||
        item.responsibility === filters.responsibility),
  );

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 items-center justify-between gap-4 px-9 pt-7 pb-[18px]">
        <h1 className="m-0 text-xl font-bold tracking-[-0.01em]">Approvals</h1>
        <div className="flex items-center gap-3.5">
          <div className="text-[12.5px] whitespace-nowrap text-ink-40">
            {shown.length} of {data.items.length} pending
          </div>
          <div className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full bg-[#3C4450] text-[12.5px] font-semibold text-white">
            D
          </div>
        </div>
      </div>

      <div className="flex shrink-0 flex-wrap items-center gap-x-[18px] gap-y-2.5 px-9">
        {FILTER_GROUPS.map((group) => (
          <div key={group.key} className="flex items-center gap-[7px]">
            <div className="text-[12.5px] whitespace-nowrap text-ink-40">
              {group.label}
            </div>
            <div className="flex flex-wrap gap-[5px]">
              {group.options.map((option) => {
                const active = filters[group.key] === option;
                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() =>
                      setFilters((f) => ({ ...f, [group.key]: option }))
                    }
                    className={`cursor-pointer rounded-full border px-3 py-1.5 text-[12.5px] font-medium whitespace-nowrap ${
                      active
                        ? "border-ink bg-ink text-white"
                        : "border-black/10 bg-surface text-ink-60"
                    }`}
                  >
                    {option === "all" ? "All" : humVal(option)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {actions.error && (
        <div className="mx-9 mt-4 rounded-lg border border-red-border bg-red-bg px-3.5 py-3 text-[13px] text-red">
          {actions.error}
        </div>
      )}

      <div className="flex min-h-0 flex-1 flex-col gap-[18px] overflow-y-auto px-9 pt-[18px] pb-10">
        {shown.length === 0 && (
          <div className="rounded-xl border border-dashed border-black/12 p-[34px] text-center text-[12.5px] text-ink-35">
            {data.items.length === 0
              ? "All approvals cleared"
              : "No approvals match these filters"}
          </div>
        )}
        {shown.map((item) => (
          <ApprovalCardView key={item.run_id} item={item} actions={actions} />
        ))}
      </div>
    </div>
  );
}

function ApprovalCardView({
  item,
  actions,
}: {
  item: ApprovalRequestResponse;
  actions: ReturnType<typeof useApprovalActions>;
}) {
  const [open, setOpen] = useState(false);
  const category = categoryStyle(item.category);
  const isEmergency = item.category === "emergency";
  const busy = actions.isPending(item.run_id);
  const pendingAction = actions.pendingAction(item.run_id);

  const cardBorder = isEmergency ? "rgba(163,53,44,0.28)" : "rgba(0,0,0,0.09)";
  const cardBg = isEmergency ? "#FDF6F5" : "#FFFFFF";
  const headerBg = isEmergency ? "#FBEFEE" : "#FFFFFF";

  return (
    <div className={`flex rounded-xl ${isEmergency ? "pulse-red" : ""}`}>
      <div className="min-w-0 flex-1">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-t-xl border px-3.5 py-[9px] text-left"
          style={{ background: headerBg, borderColor: cardBorder }}
        >
          <span className="flex min-w-0 flex-1 items-center gap-2.5 overflow-hidden">
            <span
              className="inline-flex shrink-0 items-center rounded-[20px] border px-2.5 py-0.5 text-[11.5px] whitespace-nowrap"
              style={{
                background: category.bg,
                color: category.ink,
                borderColor: category.border,
                fontWeight: category.emphasis ? 600 : 500,
              }}
            >
              {category.label}
            </span>
            <span className="min-w-0 truncate text-[13px] font-semibold">
              {item.issue_summary ?? item.original_email.slice(0, 80)}
            </span>
          </span>
          <span className="flex shrink-0 items-center gap-2.5 text-xs whitespace-nowrap text-ink-35">
            {item.severity && (
              <span
                className="inline-flex items-center gap-1.5"
                style={{
                  color: isEmergency ? "#A3352C" : "rgba(23,24,27,0.45)",
                  fontWeight: isEmergency ? 600 : 400,
                }}
              >
                {!isEmergency && (
                  <span
                    className="inline-block h-1.5 w-1.5 rounded-full"
                    style={{ background: SEVERITY_DOT[item.severity] }}
                  />
                )}
                <span className="text-[13px]">{humVal(item.severity)}</span>
                <span className="px-[3px] font-normal text-ink-28">·</span>
              </span>
            )}
            {fmtRelative(item.received_at)}
          </span>
        </button>

        <div
          className="flex flex-col gap-4 rounded-b-xl border border-t-0 p-4"
          style={{ background: cardBg, borderColor: cardBorder }}
        >
          <div className="grid grid-cols-[max-content_minmax(0,1fr)] gap-x-2.5 gap-y-2 text-[13px]">
            <div className="min-w-0 whitespace-nowrap text-ink-45">Tenant</div>
            <div className="min-w-0 break-words">
              {item.tenant_name ?? "Unknown"}
              <span className="text-ink-45">
                {item.unit ? ` · Unit ${item.unit}` : ""}
                {item.address ? ` · ${item.address}` : ""}
              </span>
            </div>

            {item.responsibility && (
              <>
                <div className="min-w-0 whitespace-nowrap text-ink-45">
                  Responsibility
                </div>
                <div className="flex min-w-0 flex-wrap items-center gap-[7px]">
                  <span>{humVal(item.responsibility)}</span>
                  {item.citation && (
                    <span className="inline-flex cursor-pointer items-center gap-1 rounded-[20px] bg-black/[0.055] px-2 py-px text-[11.5px] font-medium whitespace-nowrap text-ink-50 hover:bg-black/10 hover:text-ink">
                      {item.citation.replace(/^\[|\]$/g, "")}
                    </span>
                  )}
                </div>
              </>
            )}

            {item.appliance_or_system && (
              <>
                <div className="min-w-0 whitespace-nowrap text-ink-45">Issue type</div>
                <div className="min-w-0 break-words">
                  {humVal(item.appliance_or_system)}
                </div>
              </>
            )}
          </div>

          {open && (
            <div className="flex flex-col gap-3.5">
              <div>
                <div className="mb-2 text-[13px] text-ink-45">Original message</div>
                <div className="border-l-[1.5px] border-black/12 pl-3 text-[13px] leading-[1.7] whitespace-pre-line text-ink-82">
                  {item.original_email}
                </div>
              </div>
              {item.draft && (
                <div>
                  <div className="mb-2 text-[13px] text-ink-45">Reply draft</div>
                  <div className="border-l-[1.5px] border-black/12 pl-3 text-[13px] leading-[1.7] whitespace-pre-line text-ink-82">
                    {item.draft}
                  </div>
                </div>
              )}
            </div>
          )}

          {open && (
            <div className="flex flex-wrap items-center gap-2">
              {/*
                The planned actions are what approving will execute — the backend
                runs them all on POST /approvals/{run_id}/approve. There is no
                per-action endpoint, so these are shown, not clicked.
              */}
              {item.actions.map((action) => (
                <span
                  key={action}
                  className="flex items-center gap-1.5 rounded-lg border border-hairline bg-page px-3.5 py-1.5 text-[12.5px] font-medium whitespace-nowrap text-ink-60"
                >
                  {humVal(action)}
                </span>
              ))}
              <button
                type="button"
                disabled={busy}
                onClick={() => actions.approve(item.run_id)}
                className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-green-border bg-green-bg px-3.5 py-1.5 text-[12.5px] font-semibold whitespace-nowrap text-green-ink hover:border-green disabled:cursor-default disabled:opacity-50"
              >
                {pendingAction === "approve" ? "Approving…" : "Approve"}
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => actions.reject(item.run_id)}
                className="flex cursor-pointer items-center gap-1.5 rounded-lg border border-hairline bg-surface px-3.5 py-1.5 text-[12.5px] font-medium whitespace-nowrap text-ink-60 hover:border-black/16 hover:bg-raised disabled:cursor-default disabled:opacity-50"
              >
                {pendingAction === "reject" ? "Rejecting…" : "Reject"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
