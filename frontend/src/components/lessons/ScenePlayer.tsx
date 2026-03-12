import ReactPlayer from 'react-player';
import { ArrowLeft } from 'lucide-react';
import { getArtifactStreamUrl } from '@/services/api';
import type { ScenePlan } from '@/services/api';

interface ScenePlayerProps {
  artifactId: string;
  sceneNumber: number;
  scenePlan?: ScenePlan;
  onBack: () => void;
}

export function ScenePlayer({ artifactId, sceneNumber, scenePlan, onBack }: ScenePlayerProps) {
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
      <div className="overflow-hidden rounded-lg bg-black">
        <ReactPlayer
          src={getArtifactStreamUrl(artifactId)}
          controls
          width="100%"
          height="auto"
          style={{ aspectRatio: '16/9' }}
        />
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
