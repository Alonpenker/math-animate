import { useQuery } from '@tanstack/react-query';
import { fetchArtifactText, listArtifacts } from '@/services/api';

interface UseLessonCodeParams {
  jobId: string;
  enabled?: boolean;
}

async function fetchLessonCode(jobId: string) {
  const artifacts = await listArtifacts({ job_id: jobId, artifact_type: 'py' });

  if (artifacts.length === 0) {
    return null;
  }

  return fetchArtifactText(artifacts[0].artifact_id);
}

export function useLessonCode({ jobId, enabled = true }: UseLessonCodeParams) {
  const query = useQuery({
    queryKey: ['lesson-code', jobId],
    enabled,
    retry: false,
    queryFn: () => fetchLessonCode(jobId),
  });

  return {
    code: query.data ?? null,
    isEmpty: query.isSuccess && query.data === null,
    isLoading: query.isLoading,
    error: query.data ? null : query.error,
    refetch: query.refetch,
  };
}
