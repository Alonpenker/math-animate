import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { parseStoryboard } from '@/utils/parseStoryboard';
import type { VideoPlan } from '@/services/api';

interface LessonPlanTabProps {
  plan: VideoPlan | null;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => unknown;
}

function LessonPlanSkeleton() {
  return (
    <div className="space-y-6">
      {[1, 2].map((i) => (
        <div key={i} className="space-y-3">
          <Skeleton className="h-5 w-24" />
          <div className="space-y-2 rounded-lg border border-off-white/10 bg-surface-dark p-4">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function LessonPlanTab({ plan, isLoading, error, onRetry }: LessonPlanTabProps) {
  if (isLoading) {
    return <LessonPlanSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center py-8 text-center">
        <p className="text-off-white/50">Failed to load plan. Please try again.</p>
        <Button variant="outline" className="mt-4" onClick={() => { void onRetry(); }}>
          Retry
        </Button>
      </div>
    );
  }

  if (!plan) {
    return <p className="text-sm text-off-white/50">No plan available for this lesson.</p>;
  }

  return (
    <div className="space-y-8">
      {plan.scenes.map((scene) => {
        const storyboard = parseStoryboard(scene.visual_storyboard);
        return (
          <div key={scene.scene_number} className="space-y-3">
            <h3 className="text-sm font-semibold text-off-white/70 uppercase tracking-wider">
              Scene {scene.scene_number}
            </h3>
            {!storyboard.ok ? (
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-off-white/70">
                {scene.visual_storyboard}
              </p>
            ) : (
              <div className="space-y-3">
                {storyboard.phases.map((phase, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-off-white/10 bg-surface-dark p-4 space-y-1"
                  >
                    <p className="text-sm font-semibold text-off-white">{phase.header}</p>
                    <p className="text-sm text-off-white/70 leading-relaxed">{phase.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
