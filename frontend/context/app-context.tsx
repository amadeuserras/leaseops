'use client';

import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

type AppContextValue = {
  approvalsCountTrigger: number;
  triggerApprovalsCount: () => void;
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [approvalsCountTrigger, setApprovalsCountTrigger] = useState(0);

  const triggerApprovalsCount = useCallback(() => {
    setApprovalsCountTrigger((value) => value + 1);
  }, []);

  return (
    <AppContext.Provider value={{ approvalsCountTrigger, triggerApprovalsCount }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const value = useContext(AppContext);
  if (value === null) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return value;
}
