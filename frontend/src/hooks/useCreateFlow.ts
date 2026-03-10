import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  createJob, getJobStatus, getJobPlan, approveJob, isApiError, extractVideoPlan,
} from '@/services/api';
import type { JobStatus, VideoPlan, UserRequest } from '@/services/api';
import { useJobPolling } from '@/hooks/useJobPolling';

export type CreatePhase =
  | 'form'
  | 'loading_planning'
  | 'plan_review'
  | 'loading_rendering'
  | 'success'
  | 'failure'
  | 'cancelled'
  | 'rejected'
  | 'not_found'
  | 'resume_error';

export interface CreateFlowState {
  phase: CreatePhase;
  jobId: string | null;
  plan: VideoPlan | null;
  failureStatus: JobStatus | null;
  error: string | null;
}

export interface UseCreateFlowReturn {
  state: CreateFlowState;
  pollingStatus: JobStatus | 'TIMEOUT' | null;
  pollingError: Error | null;
  submit: (request: UserRequest) => Promise<void>;
  approvePlan: () => Promise<void>;
  rejectPlan: () => Promise<void>;
  resetToForm: () => void;
}

function statusToPhase(status: JobStatus): CreatePhase {
  switch (status) {
    case 'CREATED':
    case 'PLANNING':
      return 'loading_planning';
    case 'PLANNED':
      return 'plan_review';
    case 'APPROVED':
    case 'CODEGEN':
    case 'CODED':
    case 'VERIFYING':
    case 'FIXING':
    case 'VERIFIED':
    case 'RENDERING':
      return 'loading_rendering';
    case 'RENDERED':
      return 'success';
    case 'CANCELLED':
      return 'cancelled';
    default:
      if (status.startsWith('FAILED_')) return 'failure';
      return 'form';
  }
}

function phaseToPollingMode(phase: CreatePhase): 'planning' | 'rendering' | null {
  if (phase === 'loading_planning') return 'planning';
  if (phase === 'loading_rendering') return 'rendering';
  return null;
}

export function useCreateFlow(): UseCreateFlowReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, setState] = useState<CreateFlowState>({
    phase: 'form',
    jobId: null,
    plan: null,
    failureStatus: null,
    error: null,
  });

  const pollingMode = phaseToPollingMode(state.phase);
  const { status: pollingStatus, error: pollingError } = useJobPolling(
    state.jobId,
    pollingMode,
  );

  // Resume flow from URL job_id
  useEffect(() => {
    const jobIdParam = searchParams.get('job_id');
    if (!jobIdParam) return;

    let cancelled = false;
    (async () => {
      try {
        const res = await getJobStatus(jobIdParam);
        if (cancelled) return;
        const phase = statusToPhase(res.job.status);
        setState({
          phase,
          jobId: jobIdParam,
          plan: null,
          failureStatus: phase === 'failure' ? res.job.status : null,
          error: null,
        });

        // If planned, also fetch the plan
        if (res.job.status === 'PLANNED') {
          try {
            const planRes = await getJobPlan(jobIdParam);
            const plan = extractVideoPlan(planRes.data);
            if (!plan) {
              throw new Error('Invalid plan payload');
            }
            if (cancelled) return;
            setState((prev) => ({
              ...prev,
              plan,
            }));
          } catch {
            if (cancelled) return;
            setState((prev) => ({
              ...prev,
              error: 'Plan not found for this job. It may have expired.',
            }));
          }
        }
      } catch (err) {
        if (cancelled) return;
        if (isApiError(err) && err.status === 404) {
          setState({
            phase: 'not_found',
            jobId: null,
            plan: null,
            failureStatus: null,
            error: 'Job not found. It may have expired.',
          });
        } else {
          setState({
            phase: 'resume_error',
            jobId: jobIdParam,
            plan: null,
            failureStatus: null,
            error: 'Could not load job status. Check your connection.',
          });
        }
      }
    })();

    return () => { cancelled = true; };
    // Only run on mount with the initial search param
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // React to polling status changes
  useEffect(() => {
    if (!pollingStatus || pollingStatus === 'TIMEOUT') return;

    if (state.phase === 'loading_planning') {
      if (pollingStatus === 'PLANNED') {
        // Fetch the plan
        if (!state.jobId) return;
        void (async () => {
          try {
            const planRes = await getJobPlan(state.jobId!);
            const plan = extractVideoPlan(planRes.data);
            if (!plan) {
              throw new Error('Invalid plan payload');
            }
            setState((prev) => ({
              ...prev,
              phase: 'plan_review',
              plan,
            }));
          } catch {
            setState((prev) => ({
              ...prev,
              phase: 'plan_review',
              error: 'Plan not found for this job. It may have expired.',
            }));
          }
        })();
      } else if (pollingStatus.startsWith('FAILED_') || pollingStatus === 'CANCELLED') {
        setState((prev) => ({
          ...prev,
          phase: pollingStatus === 'CANCELLED' ? 'cancelled' : 'failure',
          failureStatus: pollingStatus as JobStatus,
        }));
      }
    }

    if (state.phase === 'loading_rendering') {
      if (pollingStatus === 'RENDERED') {
        setState((prev) => ({ ...prev, phase: 'success' }));
      } else if (pollingStatus.startsWith('FAILED_') || pollingStatus === 'CANCELLED') {
        setState((prev) => ({
          ...prev,
          phase: pollingStatus === 'CANCELLED' ? 'cancelled' : 'failure',
          failureStatus: pollingStatus as JobStatus,
        }));
      }
    }
  }, [pollingStatus, state.phase, state.jobId]);

  const submit = useCallback(async (request: UserRequest) => {
    setState((prev) => ({ ...prev, error: null }));
    try {
      const res = await createJob(request);
      const jobId = res.job.job_id;
      setSearchParams({ job_id: jobId }, { replace: true });
      setState({
        phase: 'loading_planning',
        jobId,
        plan: null,
        failureStatus: null,
        error: null,
      });
    } catch (err) {
      if (isApiError(err) && err.status === 422) {
        setState((prev) => ({
          ...prev,
          error: 'Validation error. Please check your inputs.',
        }));
      } else {
        setState((prev) => ({
          ...prev,
          error: 'Failed to submit. Check your connection.',
        }));
      }
    }
  }, [setSearchParams]);

  const approvePlan = useCallback(async () => {
    if (!state.jobId) return;
    try {
      await approveJob(state.jobId, true);
      setState((prev) => ({
        ...prev,
        phase: 'loading_rendering',
        error: null,
      }));
    } catch (err) {
      if (isApiError(err) && err.status === 409) {
        setState((prev) => ({
          ...prev,
          error: 'This plan can no longer be modified. Please refresh the page.',
        }));
      } else {
        setState((prev) => ({
          ...prev,
          error: 'Failed to approve plan. Please try again.',
        }));
      }
    }
  }, [state.jobId]);

  const rejectPlan = useCallback(async () => {
    if (!state.jobId) return;
    try {
      await approveJob(state.jobId, false);
      setState((prev) => ({
        ...prev,
        phase: 'rejected',
        error: null,
      }));
    } catch (err) {
      if (isApiError(err) && err.status === 409) {
        setState((prev) => ({
          ...prev,
          error: 'This plan can no longer be modified. Please refresh the page.',
        }));
      } else {
        setState((prev) => ({
          ...prev,
          error: 'Failed to reject plan. Please try again.',
        }));
      }
    }
  }, [state.jobId]);

  const resetToForm = useCallback(() => {
    setSearchParams({}, { replace: true });
    setState({
      phase: 'form',
      jobId: null,
      plan: null,
      failureStatus: null,
      error: null,
    });
  }, [setSearchParams]);

  return {
    state,
    pollingStatus,
    pollingError,
    submit,
    approvePlan,
    rejectPlan,
    resetToForm,
  };
}
