import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

interface LessonCodeTabProps {
  code: string | null;
  isEmpty: boolean;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => unknown;
}

function LessonCodeSkeleton() {
  return (
    <div className="space-y-3 rounded-lg border border-off-white/10 bg-surface-dark p-4">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-full" />
    </div>
  );
}

export function LessonCodeTab({
  code,
  isEmpty,
  isLoading,
  error,
  onRetry,
}: LessonCodeTabProps) {
  if (isLoading) {
    return <LessonCodeSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-start gap-4">
        <p className="text-sm text-off-white/50">Failed to load code.</p>
        <Button variant="outline" size="sm" onClick={() => { void onRetry(); }}>
          Retry
        </Button>
      </div>
    );
  }

  if (isEmpty) {
    return <p className="text-sm text-off-white/50">No code available for this lesson.</p>;
  }

  if (!code) {
    return null;
  }

  return (
    <div className="max-h-96 w-full overflow-y-auto rounded-lg border border-off-white/10 bg-surface-dark p-4">
      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
        <code className="text-sm text-off-white/90">{code}</code>
      </pre>
    </div>
  );
}
