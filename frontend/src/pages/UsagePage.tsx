import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { TokenStatCard } from '@/components/usage/TokenStatCard';
import { UsageBar } from '@/components/usage/UsageBar';
import { useTokenUsage } from '@/hooks/useTokenUsage';
import { formatNumber } from '@/utils/formatters';

export function UsagePage() {
  const { usage, loading, error, refetch } = useTokenUsage();

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-brand-text">Token Usage</h1>
        <p className="mt-2 text-brand-muted">
          ManimGenerator is free to use. To keep costs sustainable, there is a shared daily limit
          of 250,000 tokens. This resets at midnight UTC.
        </p>
      </div>

      {error && (
        <div className="flex flex-col items-center py-16 text-center">
          <p className="text-brand-muted">Could not load usage stats.</p>
          <Button variant="outline" className="mt-4" onClick={refetch}>
            Retry
          </Button>
        </div>
      )}

      {loading && !error && (
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-[140px] rounded-lg" />
          <Skeleton className="h-[140px] rounded-lg" />
        </div>
      )}

      {!loading && !error && usage && (
        <>
          <div className="grid gap-6 md:grid-cols-2">
            <TokenStatCard
              title="Tokens Used Today"
              value={formatNumber(usage.consumed)}
              subtitle={`of ${formatNumber(usage.daily_limit)} token daily limit`}
            />
            <TokenStatCard
              title="Daily Limit"
              value={formatNumber(usage.daily_limit)}
              subtitle="tokens per day"
            >
              <UsageBar consumed={usage.consumed} dailyLimit={usage.daily_limit} />
            </TokenStatCard>
          </div>

          {usage.soft_threshold_exceeded && (
            <div className="mt-6 flex items-start gap-3 rounded-lg border border-orange-300 bg-orange-50 p-4">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-orange-500" />
              <p className="text-sm text-orange-700">
                Daily token budget is over 80% used. New jobs may be limited until midnight UTC.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
