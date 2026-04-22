import ReactPlayer from 'react-player';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useArtifactVideoUrl } from '@/hooks/useArtifactVideoUrl';
import type { ScenePlan } from '@/services/api';

interface ScenePlayerProps {
  artifactId: string;
  sceneNumber: number;
  scenePlan?: ScenePlan;
  onBack: () => void;
}

export function ScenePlayer({ artifactId, sceneNumber, scenePlan, onBack }: ScenePlayerProps) {
  const { videoUrl, isLoading, error } = useArtifactVideoUrl(artifactId);
  let playerContent = null;

  if (isLoading) {
    playerContent = (
      <div className="flex h-full min-h-60 items-center justify-center text-accent-cyan">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  } else if (error) {
    playerContent = (
      <div className="flex h-full min-h-60 items-center justify-center px-4 text-center text-sm text-off-white/60">
        {error}
      </div>
    );
  } else if (videoUrl) {
    playerContent = (
      <ReactPlayer
        src={videoUrl}
        controls
        width="100%"
        height="100%"
      />
    );
  }

  return (
    <div className="space-y-4">
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-sm text-off-white/50 hover:text-off-white transition-colors cursor-pointer"
        style={{ background: 'none', border: 'none', padding: 0 }}
      >
        <ArrowLeft className="h-4 w-4" />
        Back to scenes
      </button>
      <div>
        <h3 className="text-lg text-off-white">
          Scene {sceneNumber}
        </h3>
        {scenePlan && (
          <p className="mt-1 text-sm text-off-white/60">
            {scenePlan.learning_objective}
          </p>
        )}
      </div>
      <div className="overflow-hidden rounded-lg bg-black" style={{ aspectRatio: '16/9' }}>
        {playerContent}
      </div>
      {scenePlan?.voice_notes && (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-off-white/40">
            Voice Notes
          </p>
          <p className="mt-1 text-sm text-off-white/70">
            {scenePlan.voice_notes}
          </p>
        </div>
      )}
    </div>
  );
}
