import { Sidebar } from '@/components/sidebar';
import type { ReactNode } from 'react';

type AppShellProps = { children: ReactNode };

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="bg-canvas text-ink flex h-full w-full overflow-hidden">
      <Sidebar />
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  );
}
