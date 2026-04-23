import { useQuery } from '@tanstack/react-query';
import { useDebounce } from 'use-debounce';
import { listJobs } from '@/services/api';

interface UseLessonsParams {
  topicQuery?: string;
  jobId?: string;
  page?: number;
}

const PAGE_SIZE = 20;

export function useLessons({ topicQuery, jobId, page = 1 }: UseLessonsParams) {
  const [debouncedTopic] = useDebounce(topicQuery ?? '', 400);
  const query = useQuery({
    queryKey: ['lessons', { topic: debouncedTopic, jobId, page }],
    queryFn: () =>
      listJobs({
        status: 'RENDERED',
        topic: debouncedTopic || undefined,
        job_id: jobId,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const total = query.data?.total ?? 0;

  return {
    lessons: query.data?.jobs ?? [],
    total,
    page: query.data?.page ?? page,
    totalPages: Math.max(1, Math.ceil(total / PAGE_SIZE)),
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
