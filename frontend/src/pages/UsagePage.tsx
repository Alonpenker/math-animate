import { AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import { ChalkButton } from '@/components/chalk/ChalkButton';
import { ChalkFrame } from '@/components/chalk/ChalkFrame';
import { ChalkGauge } from '@/components/chalk/ChalkGauge';
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
          <h1 className="text-4xl text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
            Token Usage
          </h1>
          <p className="mt-2 text-chalk-white/50 max-w-xl" style={{ fontFamily: 'Inter, sans-serif' }}>
            MathAnimate is free to use. To keep costs sustainable, there is a shared daily limit of 250,000 tokens. This resets at midnight UTC.
          </p>
        </div>

        {error && (
          <div className="flex flex-col items-center py-16 text-center">
            <p className="text-chalk-white/50">Could not load usage stats.</p>
            <ChalkButton variant="default" className="mt-4" onClick={refetch}>Retry</ChalkButton>
          </div>
        )}

        {!error && (
          <>
            {usage?.soft_threshold_exceeded && (
              <div
                className="mb-6 flex items-start gap-3 rounded-[10px] p-4"
                style={{ border: '2px solid #E8924A', background: 'rgba(232,146,74,0.08)' }}
              >
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-chalk-orange" />
                <p className="text-sm text-chalk-orange" style={{ fontFamily: 'Inter, sans-serif' }}>
                  Daily token budget is over 80% used. New jobs may be limited until midnight UTC.
                </p>
              </div>
            )}

            <div className="grid gap-6 md:grid-cols-2">
              <ChalkFrame className="p-6 flex min-h-[240px] flex-col items-center">
                <p className="text-xs uppercase tracking-wide text-chalk-white/40 mb-3" style={{ fontFamily: 'Inter, sans-serif' }}>
                  Tokens Used Today
                </p>
                <p className="flex-1 flex items-center text-8xl leading-none text-chalk-white" style={{ fontFamily: 'Patrick Hand, cursive' }}>
                  {loading ? '--' : formatNumber(usage!.consumed)}
                </p>
                <p className="mt-auto text-center text-sm text-chalk-white/40" style={{ fontFamily: 'Inter, sans-serif' }}>
                  of {loading ? '--' : formatNumber(usage!.daily_limit)} token daily limit
                </p>
              </ChalkFrame>

              <ChalkFrame className="p-6 flex flex-col items-center">
                <p className="text-xs uppercase tracking-wide text-chalk-white/40 mb-3" style={{ fontFamily: 'Inter, sans-serif' }}>
                  Daily Limit
                </p>
                <ChalkGauge percentage={percentage} />
              </ChalkFrame>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}
