import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { LessonCodeTab } from '@/components/lessons/LessonCodeTab';
import { LessonVideosTab } from '@/components/lessons/LessonVideosTab';
import { useLessonCode } from '@/hooks/useLessonCode';
import { useLessonScenes } from '@/hooks/useLessonScenes';
import type { LessonScene } from '@/hooks/useLessonScenes';

interface LessonDialogProps {
  onClose: () => void;
  jobId: string;
  topic: string;
}

type LessonDialogTab = 'videos' | 'code';

export function LessonDialog({ onClose, jobId, topic }: LessonDialogProps) {
  const [selectedScene, setSelectedScene] = useState<LessonScene | null>(null);
  const [activeTab, setActiveTab] = useState<LessonDialogTab>('videos');
  const { scenes, isLoading: scenesLoading, error: scenesError, refetch: refetchScenes } = useLessonScenes({
    jobId,
  });
  const { code, isEmpty: codeIsEmpty, isLoading: codeLoading, error: codeError, refetch: refetchCode } = useLessonCode({
    jobId,
    enabled: activeTab === 'code',
  });

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent
        className="max-w-6xl max-h-[90vh] overflow-y-auto w-[90vw]"
        style={{ background: '#1e2b2e', border: '2px solid rgba(245,240,232,0.2)', borderRadius: '12px' }}
      >
        <DialogHeader>
          <DialogTitle className="text-xl text-off-white">
            {topic}
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value === 'code' ? 'code' : 'videos')}>
          <TabsList>
            <TabsTrigger value="videos">Videos</TabsTrigger>
            <TabsTrigger value="code">Code</TabsTrigger>
          </TabsList>

          <TabsContent value="videos">
            <LessonVideosTab
              scenes={scenes}
              isLoading={scenesLoading}
              error={scenesError}
              selectedScene={selectedScene}
              onRetry={refetchScenes}
              onSelectScene={setSelectedScene}
              onBack={() => setSelectedScene(null)}
            />
          </TabsContent>

          <TabsContent value="code" className="min-w-0 overflow-hidden">
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
