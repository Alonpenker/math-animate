import { useEffect, useRef, useState } from 'react';
import ReactPlayer from 'react-player';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { fetchArtifactBlobUrl, isApiError } from '@/services/api';
import type { ScenePlan } from '@/services/api';

interface ScenePlayerProps {
  artifactId: string;
  sceneNumber: number;
  scenePlan?: ScenePlan;
  onBack: () => void;
}

export function ScenePlayer({ artifactId, sceneNumber, scenePlan, onBack }: ScenePlayerProps) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activeVideoUrlRef = useRef<string | null>(null);

  const revokeActiveVideoUrl = () => {
    if (activeVideoUrlRef.current) {
      URL.revokeObjectURL(activeVideoUrlRef.current);
      activeVideoUrlRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      revokeActiveVideoUrl();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    revokeActiveVideoUrl();
    setVideoUrl(null);
    setError(null);
    setLoading(true);

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
        if (cancelled) {
          return;
        }

        const message = isApiError(err)
          ? err.status === 401
            ? 'Video access was denied.'
            : 'Could not load the video.'
          : 'Could not load the video.';
        setError(message);
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      revokeActiveVideoUrl();
    };
  }, [artifactId]);

  return (
    <div className="space-y-4">
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-sm text-chalk-white/50 hover:text-chalk-white transition-colors cursor-pointer"
        style={{ fontFamily: 'Inter, sans-serif', background: 'none', border: 'none', padding: 0 }}
      >
        <ArrowLeft className="h-4 w-4" />
        Back to scenes
      </button>
      <div>
        <h3 className="text-lg text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
          Scene {sceneNumber}
        </h3>
        {scenePlan && (
          <p className="mt-1 text-sm text-chalk-white/60" style={{ fontFamily: 'Inter, sans-serif' }}>
            {scenePlan.learning_objective}
          </p>
        )}
      </div>
      <div className="overflow-hidden rounded-lg bg-black" style={{ aspectRatio: '16/9' }}>
        {loading && (
          <div className="flex h-full min-h-[240px] items-center justify-center text-chalk-cyan">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        )}
        {!loading && error && (
          <div className="flex h-full min-h-[240px] items-center justify-center px-4 text-center text-sm text-chalk-white/60">
            {error}
          </div>
        )}
        {!loading && !error && videoUrl && (
          <ReactPlayer
            src={videoUrl}
            controls
            width="100%"
            height="100%"
          />
        )}
      </div>
      {scenePlan?.voice_notes && (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-chalk-white/40" style={{ fontFamily: 'Inter, sans-serif' }}>
            Voice Notes
          </p>
          <p className="mt-1 text-sm text-chalk-white/70" style={{ fontFamily: 'Inter, sans-serif' }}>
            {scenePlan.voice_notes}
          </p>
        </div>
      )}
    </div>
  );
}
