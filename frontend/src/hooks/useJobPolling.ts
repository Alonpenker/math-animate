import { useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '@/services/api';
import type { JobStatus } from '@/services/api';

const PLANNING_POLL_INTERVAL = 3000;
const RENDERING_POLL_INTERVAL = 5000;
const TIMEOUT_MS = 10 * 60 * 1000;
const MAX_CONSECUTIVE_FAILURES = 3;

const PLANNING_TERMINAL: Set<string> = new Set([
  'PLANNED', 'FAILED_PLANNING', 'FAILED_QUOTA_EXCEEDED', 'CANCELLED',
]);

const RENDERING_TERMINAL: Set<string> = new Set([
  'RENDERED', 'FAILED_CODEGEN', 'FAILED_VERIFICATION', 'FAILED_RENDER',
  'FAILED_QUOTA_EXCEEDED', 'CANCELLED',
]);

export function useJobPolling(
  jobId: string | null,
  phase: 'planning' | 'rendering' | null,
) {
  const [status, setStatus] = useState<JobStatus | 'TIMEOUT' | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const mountedRef = useRef(true);
  const failureCountRef = useRef(0);
  const stoppedRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const shouldStop = useCallback((s: string): boolean => {
    if (phase === 'planning') return PLANNING_TERMINAL.has(s);
    if (phase === 'rendering') return RENDERING_TERMINAL.has(s);
    return false;
  }, [phase]);

  useEffect(() => {
    mountedRef.current = true;
    stoppedRef.current = false;
    failureCountRef.current = 0;
    setError(null);
    setStatus(null);

    if (!jobId || !phase) return;

    const startTime = Date.now();

    const clearPoll = () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };

    const poll = async () => {
      if (!mountedRef.current || stoppedRef.current) {
        clearPoll();
        return;
      }

      if (Date.now() - startTime > TIMEOUT_MS) {
        stoppedRef.current = true;
        setStatus('TIMEOUT');
        clearPoll();
        return;
      }

      try {
        const res = await getJobStatus(jobId);
        if (!mountedRef.current) return;
        failureCountRef.current = 0;
        setError(null);
        setStatus(res.job.status);

        if (shouldStop(res.job.status)) {
          stoppedRef.current = true;
          clearPoll();
        }
      } catch (err) {
        if (!mountedRef.current) return;
        failureCountRef.current += 1;
        if (failureCountRef.current >= MAX_CONSECUTIVE_FAILURES) {
          setError(err instanceof Error ? err : new Error('Network error'));
        }
      }
    };

    void poll();
    const interval = phase === 'planning' ? PLANNING_POLL_INTERVAL : RENDERING_POLL_INTERVAL;
    intervalRef.current = setInterval(() => void poll(), interval);

    return () => {
      mountedRef.current = false;
      clearPoll();
    };
  }, [jobId, phase, shouldStop]);

  return { status, error };
}
