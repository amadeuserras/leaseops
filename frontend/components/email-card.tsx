'use client';

import { Avatar } from '@/components/pill';
import type { TenantProfile } from '@/components/tenants-provider';
import type { Email } from '@/lib/api';
import { formatDateTime, initialsOf } from '@/lib/format';

type EmailCardProps = {
  email: Email;
  profile: TenantProfile;
};

export function EmailCard({ email, profile }: EmailCardProps) {
  return (
    <div className="bg-surface rounded-[10px] border border-black/8 p-5">
      <div className="mb-3.5 flex items-center gap-2">
        <Avatar initials={initialsOf(profile.name)} />
        <div className="min-w-0">
          <div className="truncate text-[13.5px] font-semibold">{profile.name}</div>
          <div className="text-ink/50 truncate text-[11.5px]">{email.sender}</div>
        </div>
      </div>
      <h2 className="mb-1 text-[14.5px] font-bold">{email.subject}</h2>
      <div className="text-ink/45 mb-3.5 font-mono text-[11px]">
        {profile.unit === null ? 'unit unknown' : `Unit ${profile.unit}`} · received{' '}
        {formatDateTime(email.received_at)}
      </div>
      <p className="text-ink-soft text-[13px] leading-relaxed whitespace-pre-line">{email.body}</p>
    </div>
  );
}
