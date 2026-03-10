import { useState, useEffect, useCallback } from 'react';
import { listJobs } from '@/services/api';
import type { JobListItem } from '@/services/api';

interface UseJobsListParams {
  page?: number;
  page_size?: number;
  topic?: string;
  job_id?: string;
  status?: string;
}

export function useJobsList(params: UseJobsListParams) {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(params.page ?? 1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [fetchKey, setFetchKey] = useState(0);

  const refetch = useCallback(() => {
    setFetchKey((k) => k + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    listJobs({
      page: params.page ?? 1,
      page_size: params.page_size ?? 20,
      topic: params.topic,
      job_id: params.job_id,
      status: params.status,
    })
      .then((res) => {
        if (cancelled) return;
        setJobs(res.jobs);
        setTotal(res.total);
        setPage(res.page);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err : new Error('Failed to load jobs'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [params.page, params.page_size, params.topic, params.job_id, params.status, fetchKey]);

  return { jobs, total, page, loading, error, refetch };
}
