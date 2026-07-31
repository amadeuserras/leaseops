import type { ActionType } from '@/lib/api';

export type InboxStatus =
  'Unprocessed' | 'Running' | 'Awaiting approval' | 'Completed' | 'Escalated' | 'Failed';

export const INBOX_STATUSES: InboxStatus[] = [
  'Unprocessed',
  'Running',
  'Awaiting approval',
  'Completed',
  'Escalated',
  'Failed',
];

export const inboxStatusPill: Record<InboxStatus, string> = {
  Unprocessed: 'bg-muted text-ink/60 border-black/8',
  Running: 'bg-info-bg text-info border-info-line',
  'Awaiting approval': 'bg-warn-bg text-warn border-warn-line',
  Completed: 'bg-success-bg text-success border-success-line',
  Escalated: 'bg-danger-bg text-danger border-danger-line',
  Failed: 'bg-danger-bg text-danger border-danger-line',
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

export type Urgency = 'low' | 'medium' | 'high' | 'emergency';

export const urgencyText: Record<Urgency, string> = {
  low: 'text-ink/40',
  medium: 'text-ink/60',
  high: 'text-warn',
  emergency: 'text-danger',
};

export const urgencyDot: Record<Urgency, string> = {
  low: 'bg-ink/40',
  medium: 'bg-ink/60',
  high: 'bg-warn',
  emergency: 'bg-danger',
};

export const actionPill: Record<ActionType, string> = {
  send_reply: 'bg-info-bg text-info border-info/25',
  create_work_order: 'bg-warn-bg text-warn border-warn/25',
  escalate: 'bg-danger-bg text-danger border-danger/25',
  no_action: 'bg-muted text-ink/60 border-black/10',
};

export const isUrgency = (value: unknown): value is Urgency =>
  value === 'low' || value === 'medium' || value === 'high' || value === 'emergency';
