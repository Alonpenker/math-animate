import { motion } from 'framer-motion';

interface ChalkGaugeProps {
  percentage: number; // 0-100
}

export function ChalkGauge({ percentage }: ChalkGaugeProps) {
  const barColor = percentage >= 95 ? '#E87070' : percentage >= 80 ? '#E8924A' : '#7DBF8E';

  return (
    <div className="w-full flex-1 flex items-center">
      <div
        className="w-full rounded-[6px] relative grow"
        style={{
          height: '52px',
          background: 'rgba(245,240,232,0.12)',
          border: '2px solid rgba(245,240,232,0.25)',
        }}
      >
        <motion.div
          className="h-full rounded-[4px]"
          style={{
            background: barColor,
            boxShadow: `0 0 8px ${barColor}80`,
          }}
          initial={{ width: '0%' }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
        <span
          className="absolute inset-0 flex items-center justify-center text-white text-xl font-bold"
          style={{ fontFamily: 'Patrick Hand, cursive' }}
        >
          {percentage.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
