
import { Skeleton } from '@/components/ui/skeleton';

export function PromptView({ prompt }: {prompt: string }) {
    return (
        <pre className="mt-3 max-h-96 overflow-auto rounded-lg bg-surface-dark border border-off-white/10 p-4 text-sm text-off-white/80 whitespace-pre-wrap">
            {prompt}
        </pre>
    )
}

export function SkeletonPromptView() {
    return (
        <div className="mt-3 max-h-96 overflow-auto rounded-lg bg-surface-dark border border-off-white/10 p-4">
            <div className="space-y-2">
                <Skeleton className="h-4" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4" />
                <Skeleton className="h-4" />
                <Skeleton className="h-4 w-3/4" />
            </div>
        </div>
    )
}
