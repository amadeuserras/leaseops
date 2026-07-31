'use client';

import { ApprovalsProvider } from '@/components/approvals-provider';
import { RunsProvider } from '@/components/runs-provider';
import { TenantsProvider } from '@/components/tenants-provider';
import type { ReactNode } from 'react';

type AppProvidersProps = { children: ReactNode };

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <RunsProvider>
      <ApprovalsProvider>
        <TenantsProvider>{children}</TenantsProvider>
      </ApprovalsProvider>
    </RunsProvider>
  );
}
