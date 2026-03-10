interface UsageBarProps {
  consumed: number;
  dailyLimit: number;
}

export function UsageBar({ consumed, dailyLimit }: UsageBarProps) {
  const percentage = dailyLimit > 0 ? Math.min(100, (consumed / dailyLimit) * 100) : 0;

  let barColor = 'bg-green-500';
  if (percentage >= 95) {
    barColor = 'bg-red-500';
  } else if (percentage >= 80) {
    barColor = 'bg-yellow-500';
  }

  return (
    <div className="mt-4">
      <div className="mb-1 text-right text-xs font-medium text-brand-muted">
        {percentage.toFixed(1)}%
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
