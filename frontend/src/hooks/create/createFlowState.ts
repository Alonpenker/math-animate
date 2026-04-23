import { extractVideoPlan, getJobPlan } from '@/services/api';
import type { JobStatus, VideoPlan } from '@/services/api';

export type CreateUiState = 'FORM' | 'NOT_FOUND' | 'RESUME_ERROR' | JobStatus;

export interface CreateFlowState {
  currentState: CreateUiState;
  jobId: string | null;
  plan: VideoPlan | null;
  error: string | null;
}

export const PLAN_NOT_FOUND_ERROR = 'Plan not found for this job. It may have expired.';

const FRONTEND_ONLY_STATES: Set<CreateUiState> = new Set(['FORM', 'NOT_FOUND', 'RESUME_ERROR']);
const PLANNING_STATES: Set<JobStatus> = new Set(['CREATED', 'PLANNING']);
const RENDERING_STATES: Set<JobStatus> = new Set([
  'APPROVED', 'CODEGEN', 'CODED', 'VERIFYING', 'FIXING', 'VERIFIED', 'RENDERING',
]);

export function createInitialCreateFlowState(): CreateFlowState {
  return {
    currentState: 'FORM',
    jobId: null,
    plan: null,
    error: null,
  };
}

export function isPlanningState(state: CreateUiState): state is JobStatus {
  return PLANNING_STATES.has(state as JobStatus);
}

export function isRenderingState(state: CreateUiState): state is JobStatus {
  return RENDERING_STATES.has(state as JobStatus);
}

export function isFailureState(state: CreateUiState): state is JobStatus {
  return !FRONTEND_ONLY_STATES.has(state) && state.startsWith('FAILED_');
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
