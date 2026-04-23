import { useState, useCallback, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { approveJob, createJob, isApiError } from '@/services/api';
import type { UserRequest } from '@/services/api';
import {
  createInitialCreateFlowState,
  getCreatePollingMode,
  isPlanningState,
  isRenderingState,
  loadCreatePlan,
  PLAN_NOT_FOUND_ERROR,
  type CreateFlowState,
} from '@/hooks/create/createFlowState';
import { useJobPolling } from '@/hooks/create/useJobPolling';
import { useResumeCreateJob } from '@/hooks/create/useResumeCreateJob';

export type { CreateFlowState, CreateUiState } from '@/hooks/create/createFlowState';

export interface UseCreateFlowReturn {
  state: CreateFlowState;
  pollingError: Error | null;
  submit: (request: UserRequest) => Promise<void>;
  approvePlan: () => Promise<void>;
  rejectPlan: () => Promise<void>;
  resetToForm: () => void;
}

const TIMEOUT_ERROR =
  'We could not reconnect for a while. Please refresh the page or start fresh.';

export function useCreateFlow(): UseCreateFlowReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  const jobIdParam = searchParams.get('job_id');
  const [resumeJobId, setResumeJobId] = useState(jobIdParam);
  const [state, setState] = useState<CreateFlowState>(createInitialCreateFlowState);
  const previousJobIdParamRef = useRef(jobIdParam);
  const resumedState = useResumeCreateJob(resumeJobId);
  const { status: pollingStatus, error: pollingError } = useJobPolling(
    state.jobId,
    getCreatePollingMode(state.currentState),
  );

  useEffect(() => {
    if (previousJobIdParamRef.current === jobIdParam) {
      return;
    }

    previousJobIdParamRef.current = jobIdParam;

    if (jobIdParam && jobIdParam === state.jobId) {
      setResumeJobId(null);
      return;
    }

    setResumeJobId(jobIdParam);
  }, [jobIdParam, state.jobId]);

  useEffect(() => {
    if (!resumeJobId || !resumedState) {
      return;
    }

    setState(resumedState);
  }, [resumeJobId, resumedState]);

  useEffect(() => {
    if (!pollingStatus) {
      return;
    }

    if (pollingStatus === 'TIMEOUT') {
      setState((prev) => (
        (isPlanningState(prev.currentState) || isRenderingState(prev.currentState))
          ? {
            ...prev,
            currentState: 'TIMEOUT',
            error: TIMEOUT_ERROR,
          }
          : prev
      ));
      return;
    }

    if (pollingStatus === 'PLANNED' && state.jobId && isPlanningState(state.currentState)) {
      const jobId = state.jobId;

      void loadCreatePlan(state.jobId)
        .then((plan) => {
          setState((prev) => (
            prev.jobId === jobId && isPlanningState(prev.currentState)
              ? {
                ...prev,
                currentState: 'PLANNED',
                plan,
                error: null,
              }
              : prev
          ));
        })
        .catch(() => {
          setState((prev) => (
            prev.jobId === jobId && isPlanningState(prev.currentState)
              ? {
                ...prev,
                currentState: 'PLANNED',
                plan: null,
                error: PLAN_NOT_FOUND_ERROR,
              }
              : prev
          ));
        });
      return;
    }

    setState((prev) => ({
      ...prev,
      currentState: pollingStatus,
    }));
  }, [pollingStatus, state.jobId, state.currentState]);

  const submit = useCallback(async (request: UserRequest) => {
    setResumeJobId(null);
    setState((prev) => ({ ...prev, currentState: 'FORM', error: null }));

    try {
      const res = await createJob(request);
      const jobId = res.job.job_id;

      setSearchParams({ job_id: jobId }, { replace: true });
      setState({
        currentState: res.job.status,
        jobId,
        plan: null,
        error: null,
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        currentState: 'FORM',
        error: isApiError(err) && err.status === 422
          ? 'Validation error. Please check your inputs.'
          : 'Failed to submit. Check your connection.',
      }));
    }
  }, [setSearchParams]);

  const approvePlan = useCallback(async () => {
    if (!state.jobId) {
      return;
    }

    try {
      await approveJob(state.jobId, true);
      setState((prev) => ({
        ...prev,
        currentState: 'APPROVED',
        error: null,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: isApiError(err) && err.status === 409
          ? 'This plan can no longer be modified. Please refresh the page.'
          : 'Failed to approve plan. Please try again.',
      }));
    }
  }, [state.jobId]);

  const rejectPlan = useCallback(async () => {
    if (!state.jobId) {
      return;
    }

    try {
      await approveJob(state.jobId, false);
      setState((prev) => ({
        ...prev,
        currentState: 'CANCELLED',
        error: null,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: isApiError(err) && err.status === 409
          ? 'This plan can no longer be modified. Please refresh the page.'
          : 'Failed to reject plan. Please try again.',
      }));
    }
  }, [state.jobId]);

  const resetToForm = useCallback(() => {
    setSearchParams({}, { replace: true });
    setResumeJobId(null);
    setState(createInitialCreateFlowState());
  }, [setSearchParams]);

  return {
    state,
    pollingError,
    submit,
    approvePlan,
    rejectPlan,
    resetToForm,
  };
}
