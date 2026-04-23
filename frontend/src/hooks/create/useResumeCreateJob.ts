import { useQuery } from '@tanstack/react-query';
import { getJobStatus, isApiError } from '@/services/api';
import {
  loadCreatePlan,
  PLAN_NOT_FOUND_ERROR,
  type CreateFlowState,
} from '@/hooks/create/createFlowState';

async function fetchResumedCreateJob(jobId: string): Promise<CreateFlowState> {
  const res = await getJobStatus(jobId);

  if (res.job.status !== 'PLANNED') {
    return {
      currentState: res.job.status,
      jobId,
      plan: null,
      error: null,
    };
  }

  try {
    const plan = await loadCreatePlan(jobId);

    return {
      currentState: 'PLANNED',
      jobId,
      plan,
      error: null,
    };
  } catch {
    return {
      currentState: 'PLANNED',
      jobId,
      plan: null,
      error: PLAN_NOT_FOUND_ERROR,
    };
  }
}

export function useResumeCreateJob(jobId: string | null) {
  const query = useQuery({
    queryKey: ['resume-create-job', jobId],
    enabled: Boolean(jobId),
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    gcTime: 0,
    queryFn: () => fetchResumedCreateJob(jobId!),
  });

  if (!jobId || query.isPending) {
    return null;
  }

  if (query.error) {
    return {
      currentState: isApiError(query.error) && query.error.status === 404 ? 'NOT_FOUND' : 'RESUME_ERROR',
      jobId: isApiError(query.error) && query.error.status === 404 ? null : jobId,
      plan: null,
      error: isApiError(query.error) && query.error.status === 404
        ? 'Job not found. It may have expired.'
        : 'Could not load job status. Check your connection.',
    } satisfies CreateFlowState;
  }

  return query.data ?? null;
}
