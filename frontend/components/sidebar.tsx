"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { BuildInfo } from "@/lib/api";

const NAV = [
  { href: "/inbox", label: "Inbox" },
  { href: "/runs", label: "Runs" },
  { href: "/approvals", label: "Approvals" },
] as const;

export function Sidebar({
  pendingCount,
  buildInfo,
}: {
  pendingCount: number;
  buildInfo: BuildInfo;
}) {
  const pathname = usePathname();

  return (
    <aside className="flex w-60 shrink-0 flex-col overflow-y-auto border-r border-hairline px-4 py-5">
      <div className="flex items-center gap-2.5 px-2 pt-1 pb-[22px]">
        <div className="flex h-[26px] w-8 shrink-0 items-center justify-center rounded-tl-xl rounded-tr-[10px] rounded-br-[10px] rounded-bl-[3px] bg-accent">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path
              d="M5 13l4 4L19 7"
              stroke="#ffffff"
              strokeWidth="2.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div className="text-[15px] font-semibold tracking-[-0.01em]">LeaseOps</div>
      </div>

      <nav className="flex flex-col gap-0.5">
        {NAV.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between rounded-lg px-2.5 py-2 text-[13.5px] font-medium transition-colors hover:bg-raised ${
                active ? "bg-raised text-ink" : "text-ink-55"
              }`}
            >
              <span className="flex items-center gap-2.5">
                <span
                  className={`h-1.5 w-1.5 rounded-[2px] ${
                    active ? "bg-accent" : "bg-black/12"
                  }`}
                />
                {item.label}
              </span>
              {item.label === "Approvals" && pendingCount > 0 && (
                <span className="flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full bg-ink/8 text-[10.5px] font-semibold text-ink-55">
                  {pendingCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2 border-t border-hairline px-2.5 pt-3 pb-1">
        <div className="flex items-center gap-1.5 text-[11px] text-ink-55">
          <span className="h-1.5 w-1.5 rounded-full bg-green" />
          {buildInfo.evalsPassing}/{buildInfo.evalsTotal} evals passing
        </div>
        <div className="font-mono text-[10.5px] text-ink-40">
          {buildInfo.version} · build {buildInfo.build}
        </div>
      </div>
    </aside>
  );
}
