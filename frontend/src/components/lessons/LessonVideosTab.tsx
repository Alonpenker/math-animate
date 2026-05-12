import { Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ScenePlayer } from '@/components/lessons/ScenePlayer';
import type { LessonScene } from '@/hooks/lessons/useLessonScenes';

interface LessonVideosTabProps {
  scenes: LessonScene[];
  isLoading: boolean;
  error: Error | null;
  selectedScene: LessonScene | null;
  onRetry: () => unknown;
  onSelectScene: (scene: LessonScene) => void;
  onBack: () => void;
}

function LessonVideosSkeleton() {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(3, minmax(16rem, 1fr))' }}>
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="min-h-44 rounded-lg p-6"
          style={{ border: '2px solid rgba(245,240,232,0.25)' }}
        >
          <Skeleton className="mx-auto h-4 w-24" style={{ background: 'rgba(245,240,232,0.1)' }} />
          <Skeleton
            className="mx-auto mt-6 h-14 w-14 rounded-full"
            style={{ background: 'rgba(232,146,74,0.2)' }}
          />
        </div>
      ))}
    </div>
  );
}

export function LessonVideosTab({
  scenes,
  isLoading,
  error,
  selectedScene,
  onRetry,
  onSelectScene,
  onBack,
}: LessonVideosTabProps) {
  if (selectedScene) {
    return (
      <ScenePlayer
        artifactId={selectedScene.artifactId}
        sceneNumber={selectedScene.sceneNumber}
        scenePlan={selectedScene.plan}
        onBack={onBack}
      />
    );
  }

  if (isLoading) {
    return <LessonVideosSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center py-8 text-center">
        <p className="text-off-white/50">Could not load videos. Please try again.</p>
        <Button variant="outline" className="mt-4" onClick={() => { void onRetry(); }}>
          Retry
        </Button>
      </div>
    );
  }

  if (scenes.length === 0) {
    return <p className="py-8 text-center text-off-white/50">No videos found for this job.</p>;
  }

  return (
    <div>
      <p className="mb-4 text-sm text-off-white/50">
        Select a scene to watch:
      </p>
      <div
        className="grid min-w-0 gap-4"
        style={{ gridTemplateColumns: `repeat(${Math.min(scenes.length, 3)}, minmax(16rem, 1fr))` }}
      >
        {scenes.map((scene) => (
          <button
            key={scene.artifactId}
            type="button"
            onClick={() => onSelectScene(scene)}
            className="group flex min-h-44 min-w-0 cursor-pointer flex-col items-center justify-center rounded-lg p-6 text-center transition-all hover:bg-white/5"
            style={{ border: '2px solid rgba(245,240,232,0.25)' }}
          >
            <p className="mb-4 w-full min-w-0 text-sm font-medium leading-snug text-off-white" style={{ overflowWrap: 'break-word' }}>
              {scene.displayName}
            </p>
            <span
              className="flex items-center justify-center rounded-full p-4 text-[#E8924A] transition-colors group-hover:bg-[rgba(232,146,74,0.15)]"
              style={{ border: '2px solid #E8924A' }}
            >
              <Play className="h-6 w-6" />
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
