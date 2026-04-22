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
        displayName: sceneNumber !== null ? `Scene ${sceneNumber}` : artifact.name,
        plan: sceneNumber !== null ? scenePlansByNumber.get(sceneNumber) : undefined,
      };
    })
    .sort((firstScene, secondScene) => firstScene.sceneNumber - secondScene.sceneNumber);
}

export function useLessonScenes({ jobId, enabled = true }: UseLessonScenesParams) {
  const query = useQuery({
    queryKey: ['lesson-scenes', jobId],
    enabled,
    retry: false,
    queryFn: async () => {
      const [artifacts, planResponse] = await Promise.all([
        listArtifacts({ job_id: jobId, artifact_type: 'mp4' }),
        getJobPlan(jobId).catch(() => null),
      ]);

      const plan = planResponse ? extractVideoPlan(planResponse.data) : null;
      return buildLessonScenes(artifacts, plan);
    },
  });

  return {
    scenes: query.data ?? [],
    isLoading: query.isLoading,
    error: query.data ? null : query.error,
    refetch: query.refetch,
  };
}
