'use client';

import { useApprovals } from '@/components/approvals-provider';
import { useRuns } from '@/components/runs-provider';
import { getBuildInfo } from '@/lib/api';
import type { BuildInfo } from '@/lib/api';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

type NavItemProps = {
  href: string;
  label: string;
  active: boolean;
  badge?: number;
};

function NavItem({ href, label, active, badge }: NavItemProps) {
  return (
    <Link
      href={href}
      className={`flex items-center justify-between rounded-md px-2.5 py-2 text-[13.5px] font-medium transition-colors ${
        active ? 'bg-muted text-ink' : 'text-ink/55 hover:bg-muted'
      }`}
    >
      <span className="flex items-center gap-2.5">
        <span
          className={`size-1.5 rounded-[2px] ${active ? 'bg-accent' : 'bg-black/12'}`}
          aria-hidden
        />
        {label}
      </span>
      {badge !== undefined && badge > 0 && (
        <span className="bg-ink/8 text-ink/55 flex size-[18px] shrink-0 items-center justify-center rounded-full text-[10.5px] font-semibold">
          {badge}
        </span>
      )}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { pendingCount } = useApprovals();
  const { activeEmailId } = useRuns();
  const [build, setBuild] = useState<BuildInfo | null>(null);

  useEffect(() => {
    void getBuildInfo().then(setBuild);
  }, []);

  const runsHref = activeEmailId === null ? '/runs' : `/runs/${activeEmailId}`;

  return (
    <aside className="bg-surface flex w-60 shrink-0 flex-col border-r border-black/8 px-4 py-5">
      <div className="flex items-center gap-2.5 px-2 pt-1 pb-[22px]">
        <div className="bg-accent flex h-[26px] w-8 shrink-0 items-center justify-center rounded-[10px] rounded-br-[3px]">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path
              d="M5 13l4 4L19 7"
              stroke="#ffffff"
              strokeWidth="2.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <span className="text-[15px] font-semibold tracking-[-0.01em]">LeaseOps</span>
      </div>

      <nav className="flex flex-col gap-0.5">
        <NavItem href="/inbox" label="Inbox" active={pathname.startsWith('/inbox')} />
        <NavItem href={runsHref} label="Runs" active={pathname.startsWith('/runs')} />
        <NavItem
          href="/approvals"
          label="Approvals"
          active={pathname.startsWith('/approvals')}
          badge={pendingCount}
        />
        <span
          title="Coming soon"
          className="text-ink/35 flex cursor-default items-center gap-2.5 rounded-md px-2.5 py-2 text-[13.5px] font-medium"
        >
          <span className="size-1.5 rounded-[2px] bg-black/8" aria-hidden />
          Metrics
        </span>
      </nav>

      <div className="mt-auto flex flex-col gap-2 border-t border-black/8 px-2.5 pt-3 pb-1">
        {build !== null && (
          <>
            <div className="text-ink/55 flex items-center gap-1.5 text-[11px]">
              <span className="bg-success-dot size-1.5 rounded-full" aria-hidden />
              {build.evalsPassing}/{build.evalsTotal} evals passing
            </div>
            <div className="text-ink/40 font-mono text-[10.5px]">
              {build.version} · build {build.commit}
            </div>
          </>
        )}
      </div>
    </aside>
  );
}
