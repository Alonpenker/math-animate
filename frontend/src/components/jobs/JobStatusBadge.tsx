import {
  Clock, BrainCircuit, FileCheck, ThumbsUp, Code2, FileCode,
  ScanSearch, ShieldCheck, Wrench, Film, CheckCircle2,
  AlertCircle, XSquare, ShieldAlert, VideoOff, Gauge, Ban, HelpCircle,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { ChalkBadge } from '@/components/chalk/ChalkBadge';
import type { JobStatus } from '@/services/api';

const ICON_MAP: Record<string, LucideIcon> = {
  Clock, BrainCircuit, FileCheck, ThumbsUp, Code2, FileCode,
  ScanSearch, ShieldCheck, Wrench, Film, CheckCircle2,
  AlertCircle, XSquare, ShieldAlert, VideoOff, Gauge, Ban, HelpCircle,
};

type BadgeColor = 'white' | 'green' | 'red' | 'orange' | 'cyan' | 'muted';

interface StatusDef {
  icon: string;
  color: BadgeColor;
  label: string;
}

const STATUS_DEFS: Record<JobStatus, StatusDef> = {
  CREATED:            { icon: 'Clock',         color: 'muted',   label: 'Created' },
  PLANNING:           { icon: 'BrainCircuit',  color: 'cyan',    label: 'Planning' },
  PLANNED:            { icon: 'FileCheck',     color: 'cyan',    label: 'Planned' },
  APPROVED:           { icon: 'ThumbsUp',      color: 'cyan',    label: 'Approved' },
  CODEGEN:            { icon: 'Code2',         color: 'cyan',    label: 'Generating Code' },
  CODED:              { icon: 'FileCode',      color: 'cyan',    label: 'Coded' },
  VERIFYING:          { icon: 'ScanSearch',    color: 'cyan',    label: 'Verifying' },
  VERIFIED:           { icon: 'ShieldCheck',   color: 'green',   label: 'Verified' },
  FIXING:             { icon: 'Wrench',        color: 'orange',  label: 'Fixing' },
  RENDERING:          { icon: 'Film',          color: 'cyan',    label: 'Rendering' },
  RENDERED:           { icon: 'CheckCircle2',  color: 'green',   label: 'Rendered' },
  FAILED_PLANNING:    { icon: 'AlertCircle',   color: 'red',     label: 'Failed (Planning)' },
  FAILED_CODEGEN:     { icon: 'XSquare',       color: 'red',     label: 'Failed (Codegen)' },
  FAILED_VERIFICATION:{ icon: 'ShieldAlert',   color: 'red',     label: 'Failed (Verification)' },
  FAILED_RENDER:      { icon: 'VideoOff',      color: 'red',     label: 'Failed (Render)' },
  FAILED_QUOTA_EXCEEDED:{ icon: 'Gauge',       color: 'orange',  label: 'Quota Exceeded' },
  CANCELLED:          { icon: 'Ban',           color: 'muted',   label: 'Cancelled' },
};

interface JobStatusBadgeProps { status: JobStatus; }

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const def = STATUS_DEFS[status] ?? { icon: 'HelpCircle', color: 'muted' as BadgeColor, label: status };
  const Icon = ICON_MAP[def.icon] ?? HelpCircle;
  return (
    <ChalkBadge color={def.color}>
      <Icon className="h-3 w-3" />
      {def.label}
    </ChalkBadge>
  );
}
