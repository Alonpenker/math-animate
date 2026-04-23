import { useQuery } from '@tanstack/react-query';
import { listJobs } from '@/services/api';

interface UseJobsListParams {
  page?: number;
  page_size?: number;
  topic?: string;
  job_id?: string;
  status?: string;
}

export function useJobsList({
  page = 1,
  page_size = 20,
  topic,
  job_id,
  status,
}: UseJobsListParams) {
  const query = useQuery({
    queryKey: ['jobs', { page, pageSize: page_size, topic, jobId: job_id, status }],
    retry: false,
    queryFn: () =>
      listJobs({
        page,
        page_size,
        topic,
        job_id,
        status,
      }),
  });

  return {
    jobs: query.data?.jobs ?? [],
    total: query.data?.total ?? 0,
    page: query.data?.page ?? page,
    loading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
