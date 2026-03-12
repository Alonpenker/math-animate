import type { CSSProperties, ReactNode } from 'react';

interface AuroraTextProps {
  children: ReactNode;
  className?: string;
  colors?: string[];
  speed?: number;
}

export function AuroraText({
  children,
  className,
  colors = ['#FF6B35', '#F7C59F', '#FFFACD', '#A8E6CF', '#88D8FF', '#C9B1FF', '#FF6B35'],
  speed = 4,
}: AuroraTextProps) {
  const gradientStyle: CSSProperties = {
    backgroundImage: `linear-gradient(90deg, ${colors.join(', ')})`,
    backgroundSize: '300% auto',
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    color: 'transparent',
    animation: `aurora-shift ${speed}s linear infinite`,
    display: 'inline-block',
  };

  return (
    <>
      <style>{`
        @keyframes aurora-shift {
          0%   { background-position: 0%   center; }
          100% { background-position: 300% center; }
        }
      `}</style>
      <span className={className} style={gradientStyle}>
        {children}
      </span>
    </>
  );
}
