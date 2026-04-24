import {
  FAILURE_STATUSES,
  HAPPY_PATH,
  JOB_STATUS_DEFS,
  isFailureJobStatus,
} from '@/domain/jobStatus';
import type { JobStatus } from '@/services/api';

interface JobStateDiagramProps {
  currentStatus: JobStatus | null;
  mode: 'live' | 'static';
}

function failureClassName(status: JobStatus, isCurrent: boolean): string {
  const isOrange = JOB_STATUS_DEFS[status].color === 'orange';
  let nodeClass = 'rounded-full px-3 py-1 text-xs font-medium border ';

  if (isOrange && isCurrent) {
    nodeClass += 'bg-accent-orange/20 border-accent-orange text-accent-orange';
  } else if (isOrange) {
    nodeClass += 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange/70';
  } else if (isCurrent) {
    nodeClass += 'bg-red-500/20 border-red-400 text-red-400';
  } else {
    nodeClass += 'bg-red-500/10 border-red-400/30 text-red-400/60';
  }

  return nodeClass;
}

export function JobStateDiagram({ currentStatus, mode }: JobStateDiagramProps) {
  const currentIndex = currentStatus ? HAPPY_PATH.indexOf(currentStatus) : -1;
  const isFailure = currentStatus ? isFailureJobStatus(currentStatus) : false;

  return (
    <div className="w-full p-4 rounded-lg bg-surface-dark/50 border border-off-white/10">
      <div className="flex flex-wrap gap-2 items-center justify-center sm:justify-start">
        {HAPPY_PATH.map((status, i) => {
          const isCurrentHappy = mode === 'live' && currentStatus === status;
          const isPast = mode === 'live' && currentIndex > i && !isFailure;
          const isFuture = mode === 'live' && (currentIndex < i || isFailure);

          let nodeClass = 'rounded-full px-3 py-1 text-xs font-medium border transition-all ';
          if (mode === 'static') {
            nodeClass += 'bg-accent-orange/5 border-accent-orange/20 text-off-white/50';
          } else if (isCurrentHappy) {
            nodeClass += 'bg-accent-orange border-accent-orange text-surface-dark animate-pulse';
          } else if (isPast) {
            nodeClass += 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange';
          } else if (isFuture) {
            nodeClass += 'bg-accent-orange/5 border-accent-orange/15 text-off-white/35';
          } else {
            nodeClass += 'bg-accent-orange/5 border-accent-orange/15 text-off-white/35';
          }

          const label = JOB_STATUS_DEFS[status].diagramLabel;

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

      <div className="mt-2 text-xs text-off-white/30 text-center sm:text-left">
        Note: Verifying {'<->'} Fixing loop may repeat up to 2 times
      </div>

      {mode === 'live' && isFailure && currentStatus && (
        <div className="mt-3 flex items-center gap-2">
          <span className={failureClassName(currentStatus, true)}>
            {JOB_STATUS_DEFS[currentStatus].diagramLabel}
          </span>
        </div>
      )}

      {mode === 'static' && (
        <div className="mt-3 flex flex-wrap gap-2">
          {FAILURE_STATUSES.map((status) => (
            <span key={status} className={failureClassName(status, false)}>
              {JOB_STATUS_DEFS[status].diagramLabel}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
