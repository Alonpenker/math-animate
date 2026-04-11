import { useState, useEffect } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ScenePlayer } from '@/components/lessons/ScenePlayer';
import { listArtifacts, fetchArtifactText, getJobPlan, extractVideoPlan } from '@/services/api';
import type { ArtifactResponse, ScenePlan } from '@/services/api';

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
  const [activeTab, setActiveTab] = useState<string>('videos');
  const [code, setCode] = useState<string | null>(null);
  const [codeLoading, setCodeLoading] = useState(false);
  const [codeError, setCodeError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) { setSelectedScene(null); setActiveTab('videos'); setCode(null); setCodeError(null); return; }
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      listArtifacts({ job_id: jobId, artifact_type: 'mp4' }),
      getJobPlan(jobId).catch(() => null),
    ])
      .then(([artifacts, planRes]) => {
        if (cancelled) return;
        const plan = planRes ? extractVideoPlan(planRes.data) : null;
        const entries: SceneEntry[] = artifacts.map((artifact) => {
          const sceneNum = parseSceneNumber(artifact.name);
          const scenePlan = plan?.scenes.find((s) => s.scene_number === sceneNum);
          return { artifact, sceneNumber: sceneNum ?? 0, displayName: sceneNum !== null ? `Scene ${sceneNum}` : artifact.name, plan: scenePlan };
        });
        entries.sort((a, b) => a.sceneNumber - b.sceneNumber);
        setScenes(entries);
      })
      .catch(() => { if (!cancelled) setError('Could not load videos. Please try again.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [open, jobId]);

  useEffect(() => {
    if (activeTab !== 'code' || code !== null) return;
    setCodeLoading(true);
    setCodeError(null);
    listArtifacts({ job_id: jobId, artifact_type: 'py' })
      .then((artifacts) => {
        if (!artifacts || artifacts.length === 0) {
          setCodeError('No code available for this lesson');
          return;
        }
        return fetchArtifactText(artifacts[0].artifact_id).then(setCode);
      })
      .catch(() => setCodeError('Failed to load code'))
      .finally(() => setCodeLoading(false));
  }, [activeTab, code, jobId]);

  const handleRetry = () => {
    setError(null);
    setLoading(true);
    Promise.all([
      listArtifacts({ job_id: jobId, artifact_type: 'mp4' }),
      getJobPlan(jobId).catch(() => null),
    ])
      .then(([artifacts, planRes]) => {
        const plan = planRes ? extractVideoPlan(planRes.data) : null;
        const entries: SceneEntry[] = artifacts.map((artifact) => {
          const sceneNum = parseSceneNumber(artifact.name);
          const scenePlan = plan?.scenes.find((s) => s.scene_number === sceneNum);
          return { artifact, sceneNumber: sceneNum ?? 0, displayName: sceneNum !== null ? `Scene ${sceneNum}` : artifact.name, plan: scenePlan };
        });
        entries.sort((a, b) => a.sceneNumber - b.sceneNumber);
        setScenes(entries);
      })
      .catch(() => setError('Could not load videos. Please try again.'))
      .finally(() => setLoading(false));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-6xl max-h-[90vh] overflow-y-auto w-[90vw]"
        style={{ background: '#1e2b2e', border: '2px solid rgba(245,240,232,0.2)', borderRadius: '12px' }}
      >
        <DialogHeader>
          <DialogTitle className="text-xl text-off-white">
            {topic}
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="videos">Videos</TabsTrigger>
            <TabsTrigger value="code">Code</TabsTrigger>
          </TabsList>

          <TabsContent value="videos">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-accent-cyan" />
              </div>
            )}

            {error && (
              <div className="flex flex-col items-center py-8 text-center">
                <p className="text-off-white/50">{error}</p>
                <Button variant="outline" className="mt-4" onClick={handleRetry}>Retry</Button>
              </div>
            )}

            {!loading && !error && scenes.length === 0 && (
              <p className="py-8 text-center text-off-white/50">No videos found for this job.</p>
            )}

            {!loading && !error && scenes.length > 0 && !selectedScene && (
              <div>
                <p className="mb-4 text-sm text-off-white/50">
                  Select a scene to watch:
                </p>
                <div
                  className="grid gap-4"
                  style={{ gridTemplateColumns: `repeat(${Math.min(scenes.length, 3)}, 1fr)` }}
                >
                  {scenes.map((scene) => (
                    <div
                      key={scene.artifact.artifact_id}
                      className="flex flex-col items-center rounded-lg p-6 transition-all hover:bg-white/5"
                      style={{ border: '2px solid rgba(245,240,232,0.25)' }}
                    >
                      <p className="mb-4 text-sm text-off-white">
                        {scene.displayName}
                      </p>
                      <button
                        onClick={() => setSelectedScene(scene)}
                        className="flex items-center justify-center rounded-full p-4 transition-all cursor-pointer"
                        style={{ border: '2px solid #E8924A', color: '#E8924A', background: 'transparent' }}
                        aria-label={`Play ${scene.displayName}`}
                        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(232,146,74,0.15)'; }}
                        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
                      >
                        <Play className="h-6 w-6" />
                      </button>
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
          </TabsContent>

          <TabsContent value="code" className="min-w-0 overflow-hidden">
            {codeLoading && <Loader2 className="h-5 w-5 animate-spin text-accent-cyan" />}
            {codeError && <p className="text-off-white/50 text-sm">{codeError}</p>}
            {code && (
              <div className="max-h-96 w-full overflow-y-auto rounded-lg bg-surface-dark border border-off-white/10 p-4">
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                  <code className="text-sm text-off-white/90">{code}</code>
                </pre>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
