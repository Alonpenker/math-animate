import { useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '@/services/api';
import {
  PLANNING_TERMINAL_STATUSES,
  RENDERING_TERMINAL_STATUSES,
  isJobStatus,
} from '@/domain/jobStatus';
import type { JobStatus } from '@/services/api';

const PLANNING_POLL_INTERVAL = 5000;
const RENDERING_POLL_INTERVAL = 10000;
const TIMEOUT_MS = 10 * 60 * 1000;
const MAX_CONSECUTIVE_FAILURES = 3;

export function useJobPolling(
  jobId: string | null,
  phase: 'planning' | 'rendering' | null,
) {
  const [pollingState, setPollingState] = useState<{
    jobId: string | null;
    phase: 'planning' | 'rendering' | null;
    status: JobStatus | 'TIMEOUT' | null;
    error: Error | null;
  }>({
    jobId,
    phase,
    status: null,
    error: null,
  });
  const failureCountRef = useRef(0);
  const stoppedRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const shouldStop = useCallback((s: string): boolean => {
    if (!isJobStatus(s)) return false;
    if (phase === 'planning') return PLANNING_TERMINAL_STATUSES.has(s);
    if (phase === 'rendering') return RENDERING_TERMINAL_STATUSES.has(s);
    return false;
  }, [phase]);

  useEffect(() => {
    let cancelled = false;
    stoppedRef.current = false;
    failureCountRef.current = 0;

    if (!jobId || !phase) return;

    // This effect restarts when phase changes, so plan review time does not count as pooling time.
    const phaseStartTime = Date.now();

    const clearPoll = () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    const poll = async () => {
      if (cancelled || stoppedRef.current) {
        clearPoll();
        return;
      }

      if (Date.now() - phaseStartTime > TIMEOUT_MS) {
        stoppedRef.current = true;
        setPollingState({
          jobId,
          phase,
          status: 'TIMEOUT',
          error: null,
        });
        clearPoll();
        return;
      }

      try {
        const res = await getJobStatus(jobId);
        if (cancelled) return;
        failureCountRef.current = 0;
        setPollingState({
          jobId,
          phase,
          status: res.job.status,
          error: null,
        });

        if (shouldStop(res.job.status)) {
          stoppedRef.current = true;
          clearPoll();
        }
      } catch (err) {
        if (cancelled) return;
        failureCountRef.current += 1;
        if (failureCountRef.current >= MAX_CONSECUTIVE_FAILURES) {
          setPollingState((prev) => ({
            jobId,
            phase,
            status: prev.jobId === jobId && prev.phase === phase ? prev.status : null,
            error: err instanceof Error ? err : new Error('Network error'),
          }));
        }
      }
    };

    void poll();
    const interval = phase === 'planning' ? PLANNING_POLL_INTERVAL : RENDERING_POLL_INTERVAL;
    intervalRef.current = setInterval(() => void poll(), interval);

    return () => {
      cancelled = true;
      clearPoll();
    };
  }, [jobId, phase, shouldStop]);

  const isCurrentRun = pollingState.jobId === jobId && pollingState.phase === phase;

  return {
    status: isCurrentRun ? pollingState.status : null,
    error: isCurrentRun ? pollingState.error : null,
  };
}
