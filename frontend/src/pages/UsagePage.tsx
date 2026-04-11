import { AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { UsageGauge } from '@/components/usage/UsageGauge';
import { useTokenUsage } from '@/hooks/useTokenUsage';
import { formatNumber } from '@/utils/formatters';

export function UsagePage() {
  const { usage, loading, error, refetch } = useTokenUsage();
  const percentage = usage ? Math.min(100, (usage.consumed / usage.daily_limit) * 100) : 0;

  return (
    <div className="px-4 py-12">
      <motion.div
        className="mx-auto max-w-4xl"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-8">
          <h1 className="text-4xl text-off-white">
            Token Usage
          </h1>
          <p className="mt-2 text-off-white/50 max-w-xl">
            MathAnimate is free to use. To keep costs sustainable, there is a shared daily limit of 250,000 tokens. This resets at midnight UTC.
          </p>
        </div>

        {error && (
          <div className="flex flex-col items-center py-16 text-center">
            <p className="text-off-white/50">Could not load usage stats.</p>
            <Button variant="outline" className="mt-4" onClick={refetch}>Retry</Button>
          </div>
        )}

        {!error && (
          <>
            {usage?.soft_threshold_exceeded && (
              <div
                className="mb-6 flex items-start gap-3 rounded-[10px] p-4"
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
                    {loading ? '--' : formatNumber(usage!.consumed)}
                  </p>
                  <p className="mt-auto text-center text-sm text-off-white/40">
                    of {loading ? '--' : formatNumber(usage!.daily_limit)} token daily limit
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
          </>
        )}
      </motion.div>
    </div>
  );
}
