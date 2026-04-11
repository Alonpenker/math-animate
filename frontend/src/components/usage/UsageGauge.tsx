import { motion } from 'framer-motion';

interface UsageGaugeProps {
  percentage: number;
}

export function UsageGauge({ percentage }: UsageGaugeProps) {
  const barColor =
    percentage >= 95 ? 'bg-red-400' :
    percentage >= 80 ? 'bg-accent-orange' :
    'bg-accent-green';

  return (
    <div className="w-full bg-off-white/10 border border-off-white/20 rounded-md h-14 relative overflow-hidden">
      <motion.div
        className={`h-full ${barColor} flex items-center justify-center`}
        initial={{ width: 0 }}
        animate={{ width: `${percentage}%` }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
      />
      <span className="absolute inset-0 flex items-center justify-center font-bold text-off-white text-sm">
        {Number.isInteger(percentage) ? percentage : percentage.toFixed(1)}%
      </span>
    </div>
  );
}
