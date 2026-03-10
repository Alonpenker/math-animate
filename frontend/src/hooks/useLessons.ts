import { useState, useEffect } from 'react';
import { useDebounce } from 'use-debounce';
import { listJobs } from '@/services/api';
import type { JobListItem } from '@/services/api';

interface UseLessonsParams {
  topicQuery?: string;
  jobId?: string;
  page?: number;
}

export function useLessons(params: UseLessonsParams) {
  const [debouncedTopic] = useDebounce(params.topicQuery ?? '', 400);
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(params.page ?? 1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    listJobs({
      status: 'RENDERED',
      topic: debouncedTopic || undefined,
      job_id: params.jobId,
      page: params.page ?? 1,
      page_size: 20,
    })
      .then((res) => {
        if (cancelled) return;
        setJobs(res.jobs);
        setTotal(res.total);
        setPage(res.page);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err : new Error('Failed to load lessons'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [debouncedTopic, params.jobId, params.page]);

  return { jobs, total, page, loading, error };
}
