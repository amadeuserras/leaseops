'use client';

import { ApprovalsProvider } from '@/components/approvals-provider';
import { TenantsProvider } from '@/components/tenants-provider';
import type { ReactNode } from 'react';

type AppProvidersProps = { children: ReactNode };

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <ApprovalsProvider>
      <TenantsProvider>{children}</TenantsProvider>
    </ApprovalsProvider>
  );
}
