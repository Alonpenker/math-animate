import { cn } from '@/lib/utils';

interface ChalkBadgeProps {
  children: React.ReactNode;
  color?: 'white' | 'green' | 'red' | 'orange' | 'cyan' | 'muted';
  className?: string;
}

const colorMap = {
  white: 'border-chalk-white/70 text-chalk-white',
  green: 'border-chalk-green text-chalk-green',
  red: 'border-red-400 text-red-400',
  orange: 'border-chalk-orange text-chalk-orange',
  cyan: 'border-chalk-cyan text-chalk-cyan',
  muted: 'border-chalk-white/30 text-chalk-white/50',
};

export function ChalkBadge({ children, color = 'white', className }: ChalkBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 border rounded-full px-2.5 py-0.5 text-xs font-medium',
        colorMap[color],
        className
      )}
    >
      {children}
    </span>
  );
}
