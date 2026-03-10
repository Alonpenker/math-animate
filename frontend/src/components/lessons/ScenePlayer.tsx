import ReactPlayer from 'react-player';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
      <Button variant="ghost" size="sm" onClick={onBack} className="text-brand-muted hover:text-brand-text">
        <ArrowLeft className="mr-1 h-4 w-4" />
        Back to scenes
      </Button>

      <div>
        <h3 className="text-lg font-semibold text-brand-text">Scene {sceneNumber}</h3>
        {scenePlan && (
          <p className="mt-1 text-sm text-brand-muted">{scenePlan.learning_objective}</p>
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
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-muted">Voice Notes</p>
          <p className="mt-1 text-sm text-brand-text">{scenePlan.voice_notes}</p>
        </div>
      )}
    </div>
  );
}
