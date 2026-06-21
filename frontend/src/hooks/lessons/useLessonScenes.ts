import { useQuery } from '@tanstack/react-query';
import { extractVideoPlan, getJobPlan, listArtifacts } from '@/services/api';
import type { ArtifactResponse, ScenePlan, VideoPlan } from '@/services/api';

interface UseLessonScenesParams {
  jobId: string;
  enabled?: boolean;
}

export interface LessonScene {
  artifactId: string;
  sceneNumber: number;
  displayName: string;
  plan?: ScenePlan;
}

function parseSceneNumber(name: string): number | null {
  const match = /^Scene(\d+)\.mp4$/i.exec(name);
  return match ? parseInt(match[1], 10) : null;
}

function formatArtifactDisplayName(name: string): string {
  return name
    .replace(/\.mp4$/i, '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .trim();
}

function buildLessonScenes(artifacts: ArtifactResponse[], plan: VideoPlan | null): LessonScene[] {
  const scenePlansByNumber = new Map(
    plan?.scenes.map((scenePlan) => [scenePlan.scene_number, scenePlan]) ?? [],
  );

  return artifacts
    .map((artifact) => {
      const sceneNumber = parseSceneNumber(artifact.name);

      return {
        artifactId: artifact.artifact_id,
        sceneNumber: sceneNumber ?? 0,
        displayName: sceneNumber !== null ? `Scene ${sceneNumber}` : formatArtifactDisplayName(artifact.name),
        plan: sceneNumber !== null ? scenePlansByNumber.get(sceneNumber) : undefined,
      };
    })
    .sort((firstScene, secondScene) => firstScene.sceneNumber - secondScene.sceneNumber);
}

function isValidVideoPlan(plan: VideoPlan | null): plan is VideoPlan {
  return plan !== null
    && plan.scenes.length > 0
    && plan.scenes.every((scene) => (
      Number.isInteger(scene.scene_number)
      && typeof scene.learning_objective === 'string'
      && typeof scene.visual_storyboard === 'string'
      && typeof scene.voice_notes === 'string'
    ));
}

export function useLessonScenes({ jobId, enabled = true }: UseLessonScenesParams) {
  const artifactsQuery = useQuery({
    queryKey: ['lesson-scenes', jobId],
    enabled,
    retry: false,
    queryFn: () => listArtifacts({ job_id: jobId, artifact_type: 'mp4' }),
  });

  const planQuery = useQuery({
    queryKey: ['lesson-plan', jobId],
    enabled,
    retry: false,
    queryFn: async () => {
      const planResponse = await getJobPlan(jobId);
      const plan = extractVideoPlan(planResponse.data);
      if (!isValidVideoPlan(plan)) {
        throw new Error('Invalid plan response.');
      }
      return plan;
    },
  });

  const plan = planQuery.data ?? null;

  return {
    scenes: buildLessonScenes(artifactsQuery.data ?? [], plan),
    plan,
    isLoading: artifactsQuery.isLoading,
    error: artifactsQuery.error,
    refetch: artifactsQuery.refetch,
    isPlanLoading: planQuery.isLoading,
    planError: planQuery.error,
    refetchPlan: planQuery.refetch,
  };
}
