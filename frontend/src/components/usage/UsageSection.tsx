import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { UsageGauge } from '@/components/usage/UsageGauge';
import { formatNumber } from '@/utils/formatters';
import type { TokenUsageResponse } from '@/services/api';

interface UsageSectionProps {
    isLoading: boolean;
    error: Error | null
    data: TokenUsageResponse | undefined
    onClick: () => {}
}


export function UsageSection({isLoading,error,data,onClick}:UsageSectionProps) {
    
    const percentage = data ? Math.min(100, (data.consumed / data.daily_limit) * 100) : 0;
    
    if (error) {
        return (<div className="flex flex-col items-center py-16 text-center">
                <p className="text-off-white/50">Could not load usage stats.</p>
            <Button variant="outline" className="mt-4" onClick={onClick}>Retry</Button>
            </div>)
    }

    return (
          <>
            {data?.soft_threshold_exceeded && (
              <div
                className="mb-6 flex items-start gap-3 rounded-lg p-4"
                style={{ border: '2px solid #E8924A', background: 'rgba(232,146,74,0.08)' }}
              >
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-accent-orange" />
                <p className="text-sm text-accent-orange">
                  Daily token budget is over 80% used. New jobs may be limited until midnight UTC.
                </p>
              </div>
            )}

            <div className="grid gap-6 md:grid-cols-2">
              <Card className="border-border" style={{ background: '#221a12' }}>
                <CardContent className="p-6 flex min-h-60 flex-col items-center">
                  <p className="text-xs uppercase tracking-wide text-off-white/40 mb-3">
                    Tokens Used Today
                  </p>
                  <p className="flex-1 flex items-center text-8xl leading-none text-off-white">
                    {isLoading ? '--' : formatNumber(data!.consumed)}
                  </p>
                  <p className="mt-auto text-center text-sm text-off-white/40">
                    of {isLoading ? '--' : formatNumber(data!.daily_limit)} token daily limit
                  </p>
                </CardContent>
              </Card>

              <Card className="border-border" style={{ background: '#221a12' }}>
                <CardContent className="p-6 flex min-h-60 flex-col items-center justify-center">
                  <p className="text-xs uppercase tracking-wide text-off-white/40 mb-3">
                    Daily Limit
                  </p>
                  <UsageGauge percentage={percentage} />
                </CardContent>
              </Card>
            </div>
        </>)
}