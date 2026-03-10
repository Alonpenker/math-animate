import type { JobStatus } from '@/services/api';

interface StatusConfig {
  icon: string;
  color: string;
  label: string;
}

const STATUS_MAP: Record<JobStatus, StatusConfig> = {
  CREATED: { icon: 'Clock', color: 'brand-muted', label: 'Created' },
  PLANNING: { icon: 'BrainCircuit', color: 'brand-light', label: 'Planning' },
  PLANNED: { icon: 'FileCheck', color: 'blue-500', label: 'Planned' },
  APPROVED: { icon: 'ThumbsUp', color: 'brand', label: 'Approved' },
  CODEGEN: { icon: 'Code2', color: 'brand-light', label: 'Generating Code' },
  CODED: { icon: 'FileCode', color: 'blue-500', label: 'Coded' },
  VERIFYING: { icon: 'ScanSearch', color: 'brand-light', label: 'Verifying' },
  VERIFIED: { icon: 'ShieldCheck', color: 'green-500', label: 'Verified' },
  FIXING: { icon: 'Wrench', color: 'orange-500', label: 'Fixing' },
  RENDERING: { icon: 'Film', color: 'brand-light', label: 'Rendering' },
  RENDERED: { icon: 'CheckCircle2', color: 'green-500', label: 'Rendered' },
  FAILED_PLANNING: { icon: 'AlertCircle', color: 'red-500', label: 'Failed (Planning)' },
  FAILED_CODEGEN: { icon: 'XSquare', color: 'red-500', label: 'Failed (Codegen)' },
  FAILED_VERIFICATION: { icon: 'ShieldAlert', color: 'red-500', label: 'Failed (Verification)' },
  FAILED_RENDER: { icon: 'VideoOff', color: 'red-500', label: 'Failed (Render)' },
  FAILED_QUOTA_EXCEEDED: { icon: 'Gauge', color: 'orange-500', label: 'Quota Exceeded' },
  CANCELLED: { icon: 'Ban', color: 'brand-muted', label: 'Cancelled' },
};

export function getStatusConfig(status: JobStatus): StatusConfig {
  return STATUS_MAP[status] ?? { icon: 'HelpCircle', color: 'brand-muted', label: status };
}

export function isTerminalStatus(status: JobStatus): boolean {
  return status === 'RENDERED'
    || status === 'CANCELLED'
    || status.startsWith('FAILED_');
}

export function isFailedStatus(status: JobStatus): boolean {
  return status.startsWith('FAILED_');
}
