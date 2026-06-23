import { useEffect, useRef, useState } from 'react';
import { useReducedMotion } from 'framer-motion';
import { polygonMorphKeyframes, polygonPath } from '@/lib/mathLoader';
import { cn } from '@/lib/utils';

interface MathLoaderProps {
  size?: number;
  className?: string;
  label?: string;
}

// Bouncing vertex sequence: 3 → 4 → 5 → 6 → 5 → 4 → 3 → …
const SIDE_SEQUENCE = [3, 4, 5, 6, 5, 4];
const DWELL_MS = 4000;
const MORPH_MS = 550;
const ROTATION_PERIOD_MS = 7000;
const STROKE_RATIO = 0.06; 

export function MathLoader({ size = 56, className, label = 'Loading' }: MathLoaderProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const shouldReduceMotion = useReducedMotion() ?? false;
  const [isInView, setIsInView] = useState(true);
  const [isDocumentHidden, setIsDocumentHidden] = useState(
    () => typeof document !== 'undefined' && document.hidden,
  );

  const cx = size / 2;
  const cy = size / 2;
  const stroke = Math.max(2, size * STROKE_RATIO);
  const radius = size / 2 - stroke;

  // Static path for the initial render (and the reduced-motion case): a pentagon.
  const staticPath = polygonPath(5, radius, -Math.PI / 2, cx, cy);
  const morph = polygonMorphKeyframes(SIDE_SEQUENCE, DWELL_MS, MORPH_MS, radius, -Math.PI / 2, cx, cy);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || typeof IntersectionObserver === 'undefined') return;

    const observer = new IntersectionObserver(
      entries => {
        setIsInView(entries[0]?.isIntersecting ?? true);
      },
      { threshold: 0 },
    );
    observer.observe(svg);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (typeof document === 'undefined') return;

    function handleVisibilityChange() {
      setIsDocumentHidden(document.hidden);
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg || shouldReduceMotion) return;

    if (isInView && !isDocumentHidden) {
      svg.unpauseAnimations();
      return;
    }

    svg.pauseAnimations();
  }, [isDocumentHidden, isInView, shouldReduceMotion]);

  return (
    <div role="status" aria-label={label} className={cn('inline-flex', className)}>
      <svg
        ref={svgRef}
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        fill="none"
        aria-hidden="true"
      >
        <path
          d={staticPath}
          stroke="var(--color-accent-orange)"
          strokeWidth={stroke}
          strokeLinejoin="round"
          strokeLinecap="round"
        >
          {!shouldReduceMotion && (
            <>
              <animate
                attributeName="d"
                values={morph.values}
                keyTimes={morph.keyTimes}
                dur={`${morph.durationMs}ms`}
                calcMode="linear"
                repeatCount="indefinite"
              />
              <animateTransform
                attributeName="transform"
                type="rotate"
                from={`0 ${cx} ${cy}`}
                to={`360 ${cx} ${cy}`}
                dur={`${ROTATION_PERIOD_MS}ms`}
                calcMode="linear"
                repeatCount="indefinite"
              />
            </>
          )}
        </path>
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  );
}
