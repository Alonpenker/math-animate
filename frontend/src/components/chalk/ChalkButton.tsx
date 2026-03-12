import { cn } from '@/lib/utils';

interface ChalkButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'orange' | 'cyan' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export function ChalkButton({ children, className, variant = 'default', size = 'md', ...props }: ChalkButtonProps) {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-5 py-2 text-base',
    lg: 'px-7 py-3 text-lg',
  };
  const variantClasses = {
    default: 'border-2 border-chalk-white/75 text-chalk-white hover:bg-chalk-white/10',
    orange: 'border-2 border-chalk-orange text-chalk-orange hover:bg-chalk-orange/10',
    cyan: 'border-2 border-chalk-cyan text-chalk-cyan hover:bg-chalk-cyan/10',
    ghost: 'text-chalk-white/70 hover:text-chalk-white',
  };
  return (
    <button
      className={cn(
        'rounded-[10px] font-ui transition-all duration-200 disabled:opacity-40 cursor-pointer',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
