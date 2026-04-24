export const JOB_STATUSES = [
  'CREATED',
  'PLANNING',
  'PLANNED',
  'APPROVED',
  'CODEGEN',
  'CODED',
  'VERIFYING',
  'VERIFIED',
  'FIXING',
  'RENDERING',
  'RENDERED',
  'FAILED_PLANNING',
  'FAILED_CODEGEN',
  'FAILED_VERIFICATION',
  'FAILED_RENDER',
  'FAILED_QUOTA_EXCEEDED',
  'FAILED_LLM_USAGE',
  'CANCELLED',
] as const;

export type JobStatus = typeof JOB_STATUSES[number];

export type BadgeColor = 'white' | 'green' | 'red' | 'orange' | 'cyan' | 'muted';
export type JobStatusKind = 'pending' | 'active' | 'success' | 'failure' | 'cancelled';

export interface TerminalStatusDef {
  icon: string;
  heading: string;
  explanation: string;
}

export interface JobStatusDef {
  icon: string;
  color: BadgeColor;
  label: string;
  diagramLabel: string;
  kind: JobStatusKind;
  terminal?: TerminalStatusDef;
}

export const JOB_STATUS_DEFS: Record<JobStatus, JobStatusDef> = {
  CREATED: {
    icon: 'Clock',
    color: 'muted',
    label: 'Created',
    diagramLabel: 'Created',
    kind: 'pending',
  },
  PLANNING: {
    icon: 'BrainCircuit',
    color: 'cyan',
    label: 'Planning',
    diagramLabel: 'Planning',
    kind: 'active',
  },
  PLANNED: {
    icon: 'FileCheck',
    color: 'cyan',
    label: 'Planned',
    diagramLabel: 'Planned',
    kind: 'pending',
  },
  APPROVED: {
    icon: 'ThumbsUp',
    color: 'cyan',
    label: 'Approved',
    diagramLabel: 'Approved',
    kind: 'pending',
  },
  CODEGEN: {
    icon: 'Code2',
    color: 'cyan',
    label: 'Generating Code',
    diagramLabel: 'Codegen',
    kind: 'active',
  },
  CODED: {
    icon: 'FileCode',
    color: 'cyan',
    label: 'Coded',
    diagramLabel: 'Coded',
    kind: 'pending',
  },
  VERIFYING: {
    icon: 'ScanSearch',
    color: 'cyan',
    label: 'Verifying',
    diagramLabel: 'Verifying',
    kind: 'active',
  },
  VERIFIED: {
    icon: 'ShieldCheck',
    color: 'green',
    label: 'Verified',
    diagramLabel: 'Verified',
    kind: 'success',
  },
  FIXING: {
    icon: 'Wrench',
    color: 'orange',
    label: 'Fixing',
    diagramLabel: 'Fixing',
    kind: 'active',
  },
  RENDERING: {
    icon: 'Film',
    color: 'cyan',
    label: 'Rendering',
    diagramLabel: 'Rendering',
    kind: 'active',
  },
  RENDERED: {
    icon: 'CheckCircle2',
    color: 'green',
    label: 'Rendered',
    diagramLabel: 'Rendered',
    kind: 'success',
  },
  FAILED_PLANNING: {
    icon: 'AlertCircle',
    color: 'red',
    label: 'Failed (Planning)',
    diagramLabel: 'Failed Planning',
    kind: 'failure',
    terminal: {
      icon: 'AlertCircle',
      heading: "Couldn't Generate a Plan",
      explanation: 'The AI was unable to create a plan for this topic. Try rephrasing the topic or loosening the constraints.',
    },
  },
  FAILED_CODEGEN: {
    icon: 'XSquare',
    color: 'red',
    label: 'Failed (Codegen)',
    diagramLabel: 'Failed Codegen',
    kind: 'failure',
    terminal: {
      icon: 'Code2',
      heading: 'Code Generation Failed',
      explanation: "The animation code couldn't be produced after multiple attempts. Simplifying the constraints may help.",
    },
  },
  FAILED_VERIFICATION: {
    icon: 'ShieldAlert',
    color: 'red',
    label: 'Failed (Verification)',
    diagramLabel: 'Failed Verification',
    kind: 'failure',
    terminal: {
      icon: 'ShieldAlert',
      heading: 'Code Verification Failed',
      explanation: "The generated code didn't pass our quality checks. Please try submitting again.",
    },
  },
  FAILED_RENDER: {
    icon: 'VideoOff',
    color: 'red',
    label: 'Failed (Render)',
    diagramLabel: 'Failed Render',
    kind: 'failure',
    terminal: {
      icon: 'VideoOff',
      heading: 'Rendering Failed',
      explanation: 'The rendering process encountered an unexpected error. Please try submitting your request again.',
    },
  },
  FAILED_QUOTA_EXCEEDED: {
    icon: 'Gauge',
    color: 'orange',
    label: 'Quota Exceeded',
    diagramLabel: 'Quota Exceeded',
    kind: 'failure',
    terminal: {
      icon: 'Gauge',
      heading: 'Daily Token Limit Reached',
      explanation: 'The shared daily token budget has been exhausted. Please try again after midnight UTC.',
    },
  },
  FAILED_LLM_USAGE: {
    icon: 'BrainCircuit',
    color: 'orange',
    label: 'LLM Response Limit Reached',
    diagramLabel: 'LLM Response Limit',
    kind: 'failure',
    terminal: {
      icon: 'BrainCircuit',
      heading: 'LLM Response Limit Reached',
      explanation: 'The model used its available response budget while reasoning and did not produce a usable answer. Try a smaller or more direct request.',
    },
  },
  CANCELLED: {
    icon: 'Ban',
    color: 'muted',
    label: 'Cancelled',
    diagramLabel: 'Cancelled',
    kind: 'cancelled',
    terminal: {
      icon: 'XCircle',
      heading: 'Job Cancelled',
      explanation: 'This job was cancelled before it completed.',
    },
  },
};

export const HAPPY_PATH: readonly JobStatus[] = [
  'CREATED',
  'PLANNING',
  'PLANNED',
  'APPROVED',
  'CODEGEN',
  'CODED',
  'VERIFYING',
  'FIXING',
  'VERIFIED',
  'RENDERING',
  'RENDERED',
];

export const PLANNING_TERMINAL_STATUSES: ReadonlySet<JobStatus> = new Set([
  'PLANNED',
  'FAILED_PLANNING',
  'FAILED_QUOTA_EXCEEDED',
  'FAILED_LLM_USAGE',
  'CANCELLED',
]);

export const RENDERING_TERMINAL_STATUSES: ReadonlySet<JobStatus> = new Set([
  'RENDERED',
  'FAILED_CODEGEN',
  'FAILED_VERIFICATION',
  'FAILED_RENDER',
  'FAILED_QUOTA_EXCEEDED',
  'FAILED_LLM_USAGE',
]);

export const PLANNING_ACTIVE_STATUSES: ReadonlySet<JobStatus> = new Set([
  'CREATED',
  'PLANNING',
]);

export const RENDERING_ACTIVE_STATUSES: ReadonlySet<JobStatus> = new Set([
  'APPROVED',
  'CODEGEN',
  'CODED',
  'VERIFYING',
  'FIXING',
  'VERIFIED',
  'RENDERING',
]);

export const FAILURE_STATUSES: readonly JobStatus[] = JOB_STATUSES.filter(
  (status) => JOB_STATUS_DEFS[status].kind === 'failure',
);

export function isJobStatus(value: string): value is JobStatus {
  return (JOB_STATUSES as readonly string[]).includes(value);
}

export function isFailureJobStatus(status: JobStatus): boolean {
  return JOB_STATUS_DEFS[status].kind === 'failure';
}
