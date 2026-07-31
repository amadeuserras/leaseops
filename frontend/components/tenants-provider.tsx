'use client';

import { listTenants } from '@/lib/api';
import type { Tenant } from '@/lib/api';
import { nameFromAddress } from '@/lib/format';
import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

export type TenantProfile = {
  name: string;
  unit: string | null;
  address: string | null;
};

type TenantsContextValue = {
  profileOf: (senderAddress: string) => TenantProfile;
};

const TenantsContext = createContext<TenantsContextValue | null>(null);

type TenantsProviderProps = { children: ReactNode };

export function TenantsProvider({ children }: TenantsProviderProps) {
  const [tenants, setTenants] = useState<Tenant[]>([]);

  useEffect(() => {
    void listTenants().then(setTenants);
  }, []);

  const value = useMemo<TenantsContextValue>(() => {
    const byEmail = new Map(tenants.map((tenant) => [tenant.email.toLowerCase(), tenant]));
    return {
      profileOf: (senderAddress: string) => {
        const tenant = byEmail.get(senderAddress.toLowerCase());
        if (tenant === undefined) {
          return { name: nameFromAddress(senderAddress), unit: null, address: null };
        }
        return { name: tenant.name, unit: tenant.unit, address: tenant.address };
      },
    };
  }, [tenants]);

  return <TenantsContext.Provider value={value}>{children}</TenantsContext.Provider>;
}

export const useTenants = (): TenantsContextValue => {
  const context = useContext(TenantsContext);
  if (context === null) throw new Error('useTenants must be used inside <TenantsProvider>');
  return context;
};
