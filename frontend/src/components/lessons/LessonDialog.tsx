import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { LessonCodeTab } from '@/components/lessons/LessonCodeTab';
import { LessonPlanTab } from '@/components/lessons/LessonPlanTab';
import { LessonVideosTab } from '@/components/lessons/LessonVideosTab';
import { useLessonCode } from '@/hooks/lessons/useLessonCode';
import { useLessonScenes } from '@/hooks/lessons/useLessonScenes';
import type { LessonScene } from '@/hooks/lessons/useLessonScenes';

interface LessonDialogProps {
  onClose: () => void;
  jobId: string;
  topic: string;
}

type LessonDialogTab = 'videos' | 'plan' | 'code';

export function LessonDialog({ onClose, jobId, topic }: LessonDialogProps) {
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<LessonDialogTab>('videos');
  const {
    scenes,
    plan,
    isLoading: scenesLoading,
    error: scenesError,
    refetch: refetchScenes,
    isPlanLoading,
    planError,
    refetchPlan,
  } = useLessonScenes({ jobId });
  const selectedScene = scenes.find((scene) => scene.artifactId === selectedArtifactId) ?? null;
  const { code, isEmpty: codeIsEmpty, isLoading: codeLoading, error: codeError, refetch: refetchCode } = useLessonCode({
    jobId,
    enabled: activeTab === 'code',
  });

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent
        className="max-h-[90vh] grid-rows-[auto_minmax(0,1fr)] overflow-hidden"
        style={{ width: 'min(75vw, 48rem)', maxWidth: 'none', background: '#1e2b2e', border: '2px solid rgba(245,240,232,0.2)', borderRadius: '12px' }}
      >
        <DialogHeader>
          <DialogTitle className="text-xl text-off-white">
            {topic}
          </DialogTitle>
        </DialogHeader>

        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value === 'code' ? 'code' : value === 'plan' ? 'plan' : 'videos')}
          className="min-h-0 overflow-hidden"
        >
          <TabsList>
            <TabsTrigger value="videos">Videos</TabsTrigger>
            <TabsTrigger value="plan">Plan</TabsTrigger>
            <TabsTrigger value="code">Code</TabsTrigger>
          </TabsList>

          <TabsContent value="videos" className="min-h-0 min-w-0 overflow-x-auto overflow-y-auto">
            <LessonVideosTab
              scenes={scenes}
              isLoading={scenesLoading}
              error={scenesError}
              selectedScene={selectedScene}
              onRetry={refetchScenes}
              onSelectScene={(scene: LessonScene) => setSelectedArtifactId(scene.artifactId)}
              onBack={() => setSelectedArtifactId(null)}
            />
          </TabsContent>

          <TabsContent value="plan" className="min-h-0 min-w-0 overflow-x-hidden overflow-y-auto">
            <LessonPlanTab
              plan={plan}
              isLoading={isPlanLoading}
              error={planError}
              onRetry={refetchPlan}
            />
          </TabsContent>

          <TabsContent value="code" className="min-h-0 min-w-0 overflow-x-hidden overflow-y-auto">
            <LessonCodeTab
              code={code}
              isEmpty={codeIsEmpty}
              isLoading={codeLoading}
              error={codeError}
              onRetry={refetchCode}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
