import {
  Clock, BrainCircuit, FileCheck, ThumbsUp, Code2, FileCode,
  ScanSearch, ShieldCheck, Wrench, Film, CheckCircle2,
  AlertCircle, XSquare, ShieldAlert, VideoOff, Gauge, Ban, HelpCircle,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { JobStatus } from '@/services/api';

const ICON_MAP: Record<string, LucideIcon> = {
  Clock, BrainCircuit, FileCheck, ThumbsUp, Code2, FileCode,
  ScanSearch, ShieldCheck, Wrench, Film, CheckCircle2,
  AlertCircle, XSquare, ShieldAlert, VideoOff, Gauge, Ban, HelpCircle,
};

interface StatusDef {
  icon: string;
  colorClass: string;
  label: string;
}

const STATUS_DEFS: Record<JobStatus, StatusDef> = {
  CREATED: { icon: 'Clock', colorClass: 'bg-gray-100 text-brand-muted border-gray-200', label: 'Created' },
  PLANNING: { icon: 'BrainCircuit', colorClass: 'bg-blue-50 text-brand-light border-blue-200', label: 'Planning' },
  PLANNED: { icon: 'FileCheck', colorClass: 'bg-blue-50 text-blue-600 border-blue-200', label: 'Planned' },
  APPROVED: { icon: 'ThumbsUp', colorClass: 'bg-blue-50 text-brand border-blue-200', label: 'Approved' },
  CODEGEN: { icon: 'Code2', colorClass: 'bg-blue-50 text-brand-light border-blue-200', label: 'Generating Code' },
  CODED: { icon: 'FileCode', colorClass: 'bg-blue-50 text-blue-600 border-blue-200', label: 'Coded' },
  VERIFYING: { icon: 'ScanSearch', colorClass: 'bg-blue-50 text-brand-light border-blue-200', label: 'Verifying' },
  VERIFIED: { icon: 'ShieldCheck', colorClass: 'bg-green-50 text-green-600 border-green-200', label: 'Verified' },
  FIXING: { icon: 'Wrench', colorClass: 'bg-orange-50 text-orange-600 border-orange-200', label: 'Fixing' },
  RENDERING: { icon: 'Film', colorClass: 'bg-blue-50 text-brand-light border-blue-200', label: 'Rendering' },
  RENDERED: { icon: 'CheckCircle2', colorClass: 'bg-green-50 text-green-600 border-green-200', label: 'Rendered' },
  FAILED_PLANNING: { icon: 'AlertCircle', colorClass: 'bg-red-50 text-red-600 border-red-200', label: 'Failed (Planning)' },
  FAILED_CODEGEN: { icon: 'XSquare', colorClass: 'bg-red-50 text-red-600 border-red-200', label: 'Failed (Codegen)' },
  FAILED_VERIFICATION: { icon: 'ShieldAlert', colorClass: 'bg-red-50 text-red-600 border-red-200', label: 'Failed (Verification)' },
  FAILED_RENDER: { icon: 'VideoOff', colorClass: 'bg-red-50 text-red-600 border-red-200', label: 'Failed (Render)' },
  FAILED_QUOTA_EXCEEDED: { icon: 'Gauge', colorClass: 'bg-orange-50 text-orange-600 border-orange-200', label: 'Quota Exceeded' },
  CANCELLED: { icon: 'Ban', colorClass: 'bg-gray-100 text-brand-muted border-gray-200', label: 'Cancelled' },
};

interface JobStatusBadgeProps {
  status: JobStatus;
}

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const def = STATUS_DEFS[status] ?? { icon: 'HelpCircle', colorClass: 'bg-gray-100 text-brand-muted border-gray-200', label: status };
  const Icon = ICON_MAP[def.icon] ?? HelpCircle;

  return (
    <Badge variant="outline" className={`inline-flex items-center gap-1.5 ${def.colorClass}`}>
      <Icon className="h-3.5 w-3.5" />
      <span className="text-xs font-medium">{def.label}</span>
    </Badge>
  );
}
