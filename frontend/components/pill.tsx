import type { ReactNode } from 'react';

type PillProps = {
  className: string;
  children: ReactNode;
};

export function Pill({ className, children }: PillProps) {
  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-[3px] text-[11.5px] font-semibold whitespace-nowrap ${className}`}
    >
      {children}
    </span>
  );
}

type AvatarProps = {
  initials: string;
  size?: 'sm' | 'md';
};

export function Avatar({ initials, size = 'md' }: AvatarProps) {
  const dimension = size === 'sm' ? 'size-8 text-[12px]' : 'size-[34px] text-[13px]';
  return (
    <span
      className={`bg-info-bg text-info flex shrink-0 items-center justify-center rounded-full font-bold ${dimension}`}
    >
      {initials}
    </span>
  );
}
