import { cn } from '@/lib/utils';

interface ChalkFrameProps {
  children: React.ReactNode;
  className?: string;
  rough?: boolean;
}

export function ChalkFrame({ children, className, rough = false }: ChalkFrameProps) {
  return (
    <div className={cn(rough ? 'chalk-frame-rough' : 'chalk-frame', className)}>
      {children}
    </div>
  );
}
