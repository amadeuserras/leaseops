import type {
  ApprovalCategory,
  ApprovalSeverity,
  PlanAction,
  EmailStatus,
} from '@/lib/api';

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

export const approvalCategoryLabel: Record<ApprovalCategory, string> = {
  emergency: 'Emergency',
  maintenance: 'Maintenance',
  lease_question: 'Lease question',
  not_our_problem: 'Not our problem',
};

export const approvalCategoryBadge: Record<ApprovalCategory, string> = {
  emergency: 'bg-danger-bg text-danger border-danger/30',
  maintenance: 'bg-info-bg text-info border-info/28',
  lease_question: 'bg-muted text-ink/60 border-black/16',
  not_our_problem: 'bg-muted text-ink/60 border-black/16',
};

export const approvalSeverityDot: Record<ApprovalSeverity, string> = {
  high: 'bg-danger-solid',
  medium: 'bg-warn-dot',
  low: 'bg-black/30',
};

export const approvalResponsibilityLabel: Record<
  'landlord' | 'tenant' | 'shared' | 'unclear',
  string
> = {
  landlord: 'Landlord',
  tenant: 'Tenant',
  shared: 'Shared',
  unclear: 'Unclear',
};

export const approvalActionLabel: Record<PlanAction, string> = {
  call_tenant: 'Call tenant',
  send_reply: 'Send reply',
  create_work_order: 'Create work order',
};
