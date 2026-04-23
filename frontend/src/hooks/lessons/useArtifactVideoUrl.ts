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
  const [videoState, setVideoState] = useState<{
    artifactId: string;
    videoUrl: string | null;
    isLoading: boolean;
    error: string | null;
  }>({
    artifactId,
    videoUrl: null,
    isLoading: true,
    error: null,
  });
  const activeVideoUrlRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    if (activeVideoUrlRef.current) {
      URL.revokeObjectURL(activeVideoUrlRef.current);
      activeVideoUrlRef.current = null;
    }

    fetchArtifactBlobUrl(artifactId)
      .then((url) => {
        if (cancelled) {
          URL.revokeObjectURL(url);
          return;
        }

        activeVideoUrlRef.current = url;
        setVideoState({
          artifactId,
          videoUrl: url,
          isLoading: false,
          error: null,
        });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setVideoState({
            artifactId,
            videoUrl: null,
            isLoading: false,
            error: getVideoErrorMessage(err),
          });
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

  const isCurrentArtifact = videoState.artifactId === artifactId;

  return {
    videoUrl: isCurrentArtifact ? videoState.videoUrl : null,
    isLoading: isCurrentArtifact ? videoState.isLoading : true,
    error: isCurrentArtifact ? videoState.error : null,
  };
}
