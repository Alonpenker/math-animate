import { extractVideoPlan, getJobPlan } from '@/services/api';
import {
  PLANNING_ACTIVE_STATUSES,
  RENDERING_ACTIVE_STATUSES,
  isFailureJobStatus,
  isJobStatus,
} from '@/domain/jobStatus';
import type { JobStatus, VideoPlan } from '@/services/api';

export type CreateUiState = 'FORM' | 'NOT_FOUND' | 'RESUME_ERROR' | 'TIMEOUT' | JobStatus;

export interface CreateFlowState {
  currentState: CreateUiState;
  jobId: string | null;
  plan: VideoPlan | null;
  error: string | null;
}

export const PLAN_NOT_FOUND_ERROR = 'Plan not found for this job. It may have expired.';

const FRONTEND_ONLY_STATES: Set<CreateUiState> = new Set(['FORM', 'NOT_FOUND', 'RESUME_ERROR', 'TIMEOUT']);

export function createInitialCreateFlowState(): CreateFlowState {
  return {
    currentState: 'FORM',
    jobId: null,
    plan: null,
    error: null,
  };
}

export function isPlanningState(state: CreateUiState): state is JobStatus {
  return isJobStatus(state) && PLANNING_ACTIVE_STATUSES.has(state);
}

export function isRenderingState(state: CreateUiState): state is JobStatus {
  return isJobStatus(state) && RENDERING_ACTIVE_STATUSES.has(state);
}

export function isFailureState(state: CreateUiState): state is JobStatus {
  return !FRONTEND_ONLY_STATES.has(state) && isJobStatus(state) && isFailureJobStatus(state);
}

export function isTerminalState(state: CreateUiState): boolean {
  return state === 'RENDERED' || state === 'CANCELLED' || isFailureState(state);
}

export function getCreatePollingMode(state: CreateUiState): 'planning' | 'rendering' | null {
  if (isPlanningState(state)) return 'planning';
  if (isRenderingState(state)) return 'rendering';
  return null;
}

export async function loadCreatePlan(jobId: string): Promise<VideoPlan> {
  const planRes = await getJobPlan(jobId);
  const plan = extractVideoPlan(planRes.data);

  if (!plan) {
    throw new Error('Invalid plan payload');
  }

  return plan;
}
