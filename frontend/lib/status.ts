import type { ActionType, EmailStatus } from '@/lib/api';

export const EMAIL_STATUSES: EmailStatus[] = ['pending', 'processed', 'escalated'];

export const emailStatusPill: Record<EmailStatus, string> = {
  pending: 'bg-muted text-ink/60 border-black/8',
  processed: 'bg-success-bg text-success border-success-line',
  escalated: 'bg-danger-bg text-danger border-danger-line',
};

export type StepStatus = 'running' | 'completed' | 'paused' | 'pending' | 'failed';

export const stepPill: Record<StepStatus, string> = {
  running: 'bg-info-bg text-info border-info-line',
  completed: 'bg-success-bg text-success border-success-line',
  paused: 'bg-warn-bg text-warn border-warn-line',
  pending: 'bg-muted text-ink/50 border-black/8',
  failed: 'bg-danger-bg text-danger border-danger-line',
};

export const stepDot: Record<StepStatus, string> = {
  running: 'bg-info',
  completed: 'bg-success-dot',
  paused: 'bg-warn-dot',
  pending: 'bg-black/12',
  failed: 'bg-danger',
};

export const actionPill: Record<ActionType, string> = {
  send_reply: 'bg-info-bg text-info border-info/25',
  create_work_order: 'bg-warn-bg text-warn border-warn/25',
  escalate: 'bg-danger-bg text-danger border-danger/25',
  no_action: 'bg-muted text-ink/60 border-black/10',
};
