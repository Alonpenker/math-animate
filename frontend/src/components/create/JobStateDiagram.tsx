import type { JobStatus } from '@/services/api';

interface JobStateDiagramProps {
  currentStatus: JobStatus | null;
  mode: 'live' | 'static';
}

const HAPPY_PATH: JobStatus[] = [
  'CREATED', 'PLANNING', 'PLANNED', 'APPROVED', 'CODEGEN', 'CODED',
  'VERIFYING', 'FIXING', 'VERIFIED', 'RENDERING', 'RENDERED',
];

const FAILURE_STATES: Record<string, { label: string }> = {
  FAILED_PLANNING: { label: 'Failed Planning' },
  FAILED_CODEGEN: { label: 'Failed Codegen' },
  FAILED_VERIFICATION: { label: 'Failed Verification' },
  FAILED_RENDER: { label: 'Failed Render' },
  FAILED_QUOTA_EXCEEDED: { label: 'Quota Exceeded' },
};

const STATUS_LABELS: Partial<Record<string, string>> = {
  CREATED: 'Created',
  PLANNING: 'Planning',
  PLANNED: 'Planned',
  APPROVED: 'Approved',
  CODEGEN: 'Codegen',
  CODED: 'Coded',
  VERIFYING: 'Verifying',
  FIXING: 'Fixing',
  VERIFIED: 'Verified',
  RENDERING: 'Rendering',
  RENDERED: 'Rendered',
};

export function JobStateDiagram({ currentStatus, mode }: JobStateDiagramProps) {
  const currentIndex = currentStatus ? HAPPY_PATH.indexOf(currentStatus) : -1;
  const isFailure = currentStatus ? currentStatus.toString().startsWith('FAILED') : false;

  return (
    <div className="w-full p-4 rounded-lg bg-surface-dark/50 border border-off-white/10">
      {/* Happy path nodes */}
      <div className="flex flex-wrap gap-2 items-center justify-center sm:justify-start">
        {HAPPY_PATH.map((status, i) => {
          const isCurrentHappy = mode === 'live' && currentStatus === status;
          const isPast = mode === 'live' && currentIndex > i && !isFailure;
          const isFuture = mode === 'live' && (currentIndex < i || isFailure);

          let nodeClass = 'rounded-full px-3 py-1 text-xs font-medium border transition-all ';
          if (mode === 'static') {
            nodeClass += 'bg-off-white/5 border-off-white/20 text-off-white/50';
          } else if (isCurrentHappy) {
            nodeClass += 'bg-accent-cyan border-accent-cyan text-surface-dark animate-pulse';
          } else if (isPast) {
            nodeClass += 'bg-off-white/10 border-off-white/20 text-off-white/40';
          } else if (isFuture) {
            nodeClass += 'bg-off-white/5 border-off-white/10 text-off-white/30';
          } else {
            nodeClass += 'bg-off-white/5 border-off-white/10 text-off-white/30';
          }

          const label = STATUS_LABELS[status] ?? status;

          return (
            <div key={status} className="flex items-center gap-1">
              <span className={nodeClass}>{isPast ? '\u2713 ' : ''}{label}</span>
              {i < HAPPY_PATH.length - 1 && (
                <span className="text-off-white/20 text-xs">{'\u2192'}</span>
              )}
            </div>
          );
        })}
      </div>

      {/* FIXING loop note */}
      <div className="mt-2 text-xs text-off-white/30 text-center sm:text-left">
        Note: Verifying {'<->'} Fixing loop may repeat up to 2 times
      </div>

      {/* Show failure state if current */}
      {mode === 'live' && isFailure && currentStatus && (
        <div className="mt-3 flex items-center gap-2">
          <span className="rounded-full px-3 py-1 text-xs font-medium border bg-red-500/20 border-red-400 text-red-400">
            {FAILURE_STATES[currentStatus]?.label ?? STATUS_LABELS[currentStatus] ?? currentStatus}
          </span>
        </div>
      )}

      {/* Static mode: show failure branches */}
      {mode === 'static' && (
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(FAILURE_STATES).map(([key, val]) => (
            <span key={key} className="rounded-full px-3 py-1 text-xs font-medium border bg-red-500/10 border-red-400/30 text-red-400/60">
              {val.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
