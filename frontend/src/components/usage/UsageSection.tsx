import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { formatNumber } from '@/utils/formatters';
import type { TokenUsageResponse } from '@/services/api';

interface UsageSectionProps {
  isLoading: boolean;
  error: Error | null;
  data: TokenUsageResponse | undefined;
  onClick: () => void;
}

export function UsageSection({ isLoading, error, data, onClick }: UsageSectionProps) {
  const callsUsed = data?.openrouter_calls ?? 0;
  const callLimit = data?.openrouter_call_limit ?? 50;
  const callsRemaining = data?.openrouter_calls_remaining ?? callLimit;
  const callPercentage = callLimit > 0 ? Math.min(100, (callsUsed / callLimit) * 100) : 0;
  const showCallWarning = Boolean(data && callsRemaining <= 5);
  const breakdown = data?.breakdown ?? [];

  if (error) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-off-white/50">Could not load usage stats.</p>
        <Button variant="outline" className="mt-4 gap-2" onClick={onClick}>
          <RefreshCw className="h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <>
      {showCallWarning && (
        <div
          className="mb-6 flex items-start gap-3 rounded-lg p-4"
          style={{ border: '2px solid #E8924A', background: 'rgba(232,146,74,0.08)' }}
        >
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-accent-orange" />
          <p className="text-sm text-accent-orange">
            The shared daily AI call limit is nearly used. New jobs may be limited until midnight UTC.
          </p>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-border" style={{ background: '#221a12' }}>
          <CardContent className="p-6">
            <p className="text-xs uppercase tracking-wide text-off-white/40">
              AI Calls Today
            </p>
            <div className="mt-6 flex items-end justify-between gap-4">
              <p className="text-6xl leading-none text-off-white">
                {isLoading ? '--' : formatNumber(callsUsed)}
              </p>
              <p className="pb-2 text-sm text-off-white/45">
                of {isLoading ? '--' : formatNumber(callLimit)}
              </p>
            </div>
            <div className="mt-6 h-2 overflow-hidden rounded-full bg-off-white/10">
              <div
                className="h-full rounded-full bg-accent-orange"
                style={{ width: `${isLoading ? 0 : callPercentage}%` }}
              />
            </div>
            <p className="mt-3 text-sm text-off-white/45">
              {isLoading ? '--' : formatNumber(callsRemaining)} calls remaining
            </p>
          </CardContent>
        </Card>

        <Card className="border-border" style={{ background: '#221a12' }}>
          <CardContent className="p-6">
            <p className="text-xs uppercase tracking-wide text-off-white/40">
              Token Telemetry
            </p>
            <p className="mt-6 text-5xl leading-none text-off-white">
              {isLoading ? '--' : formatNumber(data?.token_totals.total_tokens ?? 0)}
            </p>
            <div className="mt-6 grid grid-cols-3 gap-3 text-sm">
              <div>
                <p className="text-off-white/35">Input</p>
                <p className="mt-1 text-off-white">{isLoading ? '--' : formatNumber(data?.token_totals.input_tokens ?? 0)}</p>
              </div>
              <div>
                <p className="text-off-white/35">Output</p>
                <p className="mt-1 text-off-white">{isLoading ? '--' : formatNumber(data?.token_totals.output_tokens ?? 0)}</p>
              </div>
              <div>
                <p className="text-off-white/35">Reasoning</p>
                <p className="mt-1 text-off-white">{isLoading ? '--' : formatNumber(data?.token_totals.reasoning_tokens ?? 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6 border-border" style={{ background: '#221a12' }}>
        <CardContent className="p-0">
          <div className="grid grid-cols-[1.2fr_0.8fr_0.5fr_0.7fr] gap-3 border-b border-border px-4 py-3 text-xs uppercase tracking-wide text-off-white/35">
            <span>Call Type</span>
            <span>Stage</span>
            <span className="text-right">Calls</span>
            <span className="text-right">Tokens</span>
          </div>
          {breakdown.length === 0 ? (
            <p className="px-4 py-6 text-sm text-off-white/45">
              {isLoading ? 'Loading usage breakdown...' : 'No OpenRouter calls recorded for today.'}
            </p>
          ) : (
            breakdown.map((entry) => (
              <div
                key={`${entry.provider}-${entry.model}-${entry.stage}-${entry.call_type}`}
                className="grid grid-cols-[1.2fr_0.8fr_0.5fr_0.7fr] gap-3 border-b border-border/60 px-4 py-3 text-sm last:border-b-0"
              >
                <span className="truncate text-off-white">{entry.call_type}</span>
                <span className="truncate text-off-white/55">{entry.stage}</span>
                <span className="text-right text-off-white/70">{formatNumber(entry.calls)}</span>
                <span className="text-right text-off-white/70">{formatNumber(entry.total_tokens)}</span>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </>
  );
}
