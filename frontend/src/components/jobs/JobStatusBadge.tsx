import {
  Clock, BrainCircuit, FileCheck, ThumbsUp, Code2, FileCode,
  ScanSearch, ShieldCheck, Wrench, Film, CheckCircle2,
  AlertCircle, XSquare, ShieldAlert, VideoOff, Gauge, Ban, HelpCircle,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { JOB_STATUS_DEFS } from '@/domain/jobStatus';
import type { BadgeColor } from '@/domain/jobStatus';
import type { JobStatus } from '@/services/api';

const ICON_MAP: Record<string, LucideIcon> = {
  Clock, BrainCircuit, FileCheck, ThumbsUp, Code2, FileCode,
  ScanSearch, ShieldCheck, Wrench, Film, CheckCircle2,
  AlertCircle, XSquare, ShieldAlert, VideoOff, Gauge, Ban, HelpCircle,
};

function colorToVariantAndClass(color: BadgeColor): { variant: 'default' | 'secondary' | 'destructive' | 'outline'; className?: string } {
  switch (color) {
    case 'white':
    case 'muted':
      return { variant: 'secondary' };
    case 'green':
      return { variant: 'outline', className: 'border-accent-green text-accent-green' };
    case 'red':
      return { variant: 'destructive' };
    case 'orange':
      return { variant: 'outline', className: 'border-accent-orange text-accent-orange' };
    case 'cyan':
      return { variant: 'outline', className: 'border-accent-cyan text-accent-cyan' };
  }
}

interface JobStatusBadgeProps { status: JobStatus; }

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const def = JOB_STATUS_DEFS[status] ?? { icon: 'HelpCircle', color: 'muted' as BadgeColor, label: status };
  const Icon = ICON_MAP[def.icon] ?? HelpCircle;
  const { variant, className } = colorToVariantAndClass(def.color);
  return (
    <Badge variant={variant} className={className}>
      <Icon className="h-3 w-3" />
      {def.label}
    </Badge>
  );
}
