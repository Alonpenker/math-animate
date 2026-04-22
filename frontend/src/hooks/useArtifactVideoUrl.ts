import { useEffect, useRef, useState } from 'react';
import { fetchArtifactBlobUrl, isApiError } from '@/services/api';

interface UseArtifactVideoUrlResult {
  videoUrl: string | null;
  isLoading: boolean;
  error: string | null;
}

function getVideoErrorMessage(err: unknown) {
  if (isApiError(err) && err.status === 401) {
    return 'Video access was denied.';
  }

  return 'Could not load the video.';
}

export function useArtifactVideoUrl(artifactId: string): UseArtifactVideoUrlResult {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activeVideoUrlRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    if (activeVideoUrlRef.current) {
      URL.revokeObjectURL(activeVideoUrlRef.current);
      activeVideoUrlRef.current = null;
    }

    setVideoUrl(null);
    setError(null);
    setIsLoading(true);

    fetchArtifactBlobUrl(artifactId)
      .then((url) => {
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }

        activeVideoUrlRef.current = url;
        setVideoUrl(url);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(getVideoErrorMessage(err));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;

      if (activeVideoUrlRef.current) {
        URL.revokeObjectURL(activeVideoUrlRef.current);
        activeVideoUrlRef.current = null;
      }
    };
  }, [artifactId]);

  return { videoUrl, isLoading, error };
}
