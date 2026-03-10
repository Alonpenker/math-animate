import { useState, useEffect } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScenePlayer } from '@/components/lessons/ScenePlayer';
import { listArtifacts, getJobPlan } from '@/services/api';
import type { ArtifactResponse, VideoPlan, ScenePlan } from '@/services/api';

interface LessonDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jobId: string;
  topic: string;
}

interface SceneEntry {
  artifact: ArtifactResponse;
  sceneNumber: number;
  displayName: string;
  plan?: ScenePlan;
}

function parseSceneNumber(name: string): number | null {
  const match = /^Scene(\d+)\.mp4$/i.exec(name);
  return match ? parseInt(match[1], 10) : null;
}

export function LessonDialog({ open, onOpenChange, jobId, topic }: LessonDialogProps) {
  const [scenes, setScenes] = useState<SceneEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedScene, setSelectedScene] = useState<SceneEntry | null>(null);

  useEffect(() => {
    if (!open) {
      setSelectedScene(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      listArtifacts({ job_id: jobId, artifact_type: 'mp4' }),
      getJobPlan(jobId).catch(() => null),
    ])
      .then(([artifacts, planRes]) => {
        if (cancelled) return;
        const plan = planRes?.data as VideoPlan | null;

        const entries: SceneEntry[] = artifacts.map((artifact) => {
          const sceneNum = parseSceneNumber(artifact.name);
          const scenePlan = plan?.scenes.find((s) => s.scene_number === sceneNum);
          return {
            artifact,
            sceneNumber: sceneNum ?? 0,
            displayName: sceneNum !== null ? `Scene ${sceneNum}` : artifact.name,
            plan: scenePlan,
          };
        });

        entries.sort((a, b) => a.sceneNumber - b.sceneNumber);
        setScenes(entries);
      })
      .catch(() => {
        if (!cancelled) {
          setError('Could not load videos. Please try again.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [open, jobId]);

  const handleRetry = () => {
    setError(null);
    setLoading(true);
    Promise.all([
      listArtifacts({ job_id: jobId, artifact_type: 'mp4' }),
      getJobPlan(jobId).catch(() => null),
    ])
      .then(([artifacts, planRes]) => {
        const plan = planRes?.data as VideoPlan | null;
        const entries: SceneEntry[] = artifacts.map((artifact) => {
          const sceneNum = parseSceneNumber(artifact.name);
          const scenePlan = plan?.scenes.find((s) => s.scene_number === sceneNum);
          return {
            artifact,
            sceneNumber: sceneNum ?? 0,
            displayName: sceneNum !== null ? `Scene ${sceneNum}` : artifact.name,
            plan: scenePlan,
          };
        });
        entries.sort((a, b) => a.sceneNumber - b.sceneNumber);
        setScenes(entries);
      })
      .catch(() => setError('Could not load videos. Please try again.'))
      .finally(() => setLoading(false));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl text-brand-text">{topic}</DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-brand-light" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center py-8 text-center">
            <p className="text-brand-muted">{error}</p>
            <Button variant="outline" className="mt-4" onClick={handleRetry}>
              Retry
            </Button>
          </div>
        )}

        {!loading && !error && scenes.length === 0 && (
          <p className="py-8 text-center text-brand-muted">No videos found for this job.</p>
        )}

        {!loading && !error && scenes.length > 0 && !selectedScene && (
          <div>
            <p className="mb-4 text-sm text-brand-muted">Select a scene to watch:</p>
            <div
              className="grid gap-4"
              style={{
                gridTemplateColumns: `repeat(${Math.min(scenes.length, 3)}, 1fr)`,
              }}
            >
              {scenes.map((scene) => (
                <div
                  key={scene.artifact.artifact_id}
                  className="flex flex-col items-center rounded-lg border border-brand-border p-6 transition-shadow hover:shadow-md"
                >
                  <p className="mb-4 text-sm font-semibold text-brand-text">
                    {scene.displayName}
                  </p>
                  <Button
                    onClick={() => setSelectedScene(scene)}
                    className="rounded-full bg-brand-accent p-4 text-white hover:bg-brand-accent/90"
                    size="icon"
                    aria-label={`Play ${scene.displayName}`}
                  >
                    <Play className="h-6 w-6" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedScene && (
          <ScenePlayer
            artifactId={selectedScene.artifact.artifact_id}
            sceneNumber={selectedScene.sceneNumber}
            scenePlan={selectedScene.plan}
            onBack={() => setSelectedScene(null)}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
