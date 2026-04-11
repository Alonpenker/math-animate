import { useCallback, useEffect, useMemo, useRef, useState, memo } from 'react';
import type { CSSProperties, ReactNode, RefObject } from 'react';

interface LogoItemBase {
  href?: string;
  title?: string;
  ariaLabel?: string;
}

interface LogoImageItem extends LogoItemBase {
  src: string;
  srcSet?: string;
  sizes?: string;
  width?: number;
  height?: number;
  alt?: string;
}

interface LogoNodeItem extends LogoItemBase {
  node: ReactNode;
}

export type LogoItem = LogoImageItem | LogoNodeItem;

interface LogoLoopProps {
  logos: LogoItem[];
  speed?: number;
  direction?: 'left' | 'right' | 'up' | 'down';
  width?: number | string;
  logoHeight?: number;
  gap?: number;
  pauseOnHover?: boolean;
  hoverSpeed?: number;
  fadeOut?: boolean;
  fadeOutColor?: string;
  scaleOnHover?: boolean;
  renderItem?: (item: LogoItem, key: string) => ReactNode;
  ariaLabel?: string;
  className?: string;
  style?: CSSProperties;
}

const ANIMATION_CONFIG = { SMOOTH_TAU: 0.25, MIN_COPIES: 2, COPY_HEADROOM: 2 };

const toCssLength = (value: number | string | undefined) =>
  typeof value === 'number' ? `${value}px` : (value ?? undefined);

const useResizeObserver = (
  callback: () => void,
  elements: RefObject<Element | null>[],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  dependencies: any[],
) => {
  useEffect(() => {
    if (!window.ResizeObserver) {
      window.addEventListener('resize', callback);
      callback();
      return () => window.removeEventListener('resize', callback);
    }
    const observers = elements.map((ref) => {
      if (!ref.current) return null;
      const observer = new ResizeObserver(callback);
      observer.observe(ref.current);
      return observer;
    });
    callback();
    return () => observers.forEach((o) => o?.disconnect());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callback, elements, dependencies]);
};

const useImageLoader = (
  seqRef: RefObject<HTMLUListElement | null>,
  onLoad: () => void,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  dependencies: any[],
) => {
  useEffect(() => {
    const images = seqRef.current?.querySelectorAll('img') ?? [];
    if (images.length === 0) { onLoad(); return; }
    let remaining = images.length;
    const tick = () => { if (--remaining === 0) onLoad(); };
    images.forEach((img: HTMLImageElement) => {
      if (img.complete) { tick(); }
      else {
        img.addEventListener('load', tick, { once: true });
        img.addEventListener('error', tick, { once: true });
      }
    });
    return () => {
      images.forEach((img: HTMLImageElement) => {
        img.removeEventListener('load', tick);
        img.removeEventListener('error', tick);
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onLoad, seqRef, dependencies]);
};

const useAnimationLoop = (
  trackRef: RefObject<HTMLDivElement | null>,
  targetVelocity: number,
  seqWidth: number,
  seqHeight: number,
  isHovered: boolean,
  hoverSpeed: number | undefined,
  isVertical: boolean,
) => {
  const rafRef = useRef<number | null>(null);
  const lastTsRef = useRef<number | null>(null);
  const offsetRef = useRef(0);
  const velocityRef = useRef(0);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    const seqSize = isVertical ? seqHeight : seqWidth;

    if (seqSize > 0) {
      offsetRef.current = ((offsetRef.current % seqSize) + seqSize) % seqSize;
      track.style.transform = isVertical
        ? `translate3d(0, ${-offsetRef.current}px, 0)`
        : `translate3d(${-offsetRef.current}px, 0, 0)`;
    }

    const animate = (ts: number) => {
      if (lastTsRef.current === null) lastTsRef.current = ts;
      const dt = Math.max(0, ts - lastTsRef.current) / 1000;
      lastTsRef.current = ts;
      const target = isHovered && hoverSpeed !== undefined ? hoverSpeed : targetVelocity;
      velocityRef.current += (target - velocityRef.current) * (1 - Math.exp(-dt / ANIMATION_CONFIG.SMOOTH_TAU));
      if (seqSize > 0) {
        let next = ((offsetRef.current + velocityRef.current * dt) % seqSize + seqSize) % seqSize;
        offsetRef.current = next;
        track.style.transform = isVertical
          ? `translate3d(0, ${-next}px, 0)`
          : `translate3d(${-next}px, 0, 0)`;
      }
      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      lastTsRef.current = null;
    };
  }, [targetVelocity, seqWidth, seqHeight, isHovered, hoverSpeed, isVertical, trackRef]);
};

export const LogoLoop = memo<LogoLoopProps>(({
  logos,
  speed = 120,
  direction = 'left',
  width = '100%',
  logoHeight = 28,
  gap = 32,
  pauseOnHover,
  hoverSpeed,
  fadeOut = false,
  fadeOutColor = '#000000',
  scaleOnHover = false,
  renderItem,
  ariaLabel = 'Partner logos',
  className,
  style,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const seqRef = useRef<HTMLUListElement>(null);

  const [seqWidth, setSeqWidth] = useState(0);
  const [seqHeight, setSeqHeight] = useState(0);
  const [copyCount, setCopyCount] = useState(ANIMATION_CONFIG.MIN_COPIES);
  const [isHovered, setIsHovered] = useState(false);

  const isVertical = direction === 'up' || direction === 'down';

  const effectiveHoverSpeed = useMemo(() => {
    if (hoverSpeed !== undefined) return hoverSpeed;
    return pauseOnHover === false ? undefined : 0;
  }, [hoverSpeed, pauseOnHover]);

  const targetVelocity = useMemo(() => {
    const mag = Math.abs(speed);
    const dir = isVertical ? (direction === 'up' ? 1 : -1) : (direction === 'left' ? 1 : -1);
    return mag * dir * (speed < 0 ? -1 : 1);
  }, [speed, direction, isVertical]);

  const updateDimensions = useCallback(() => {
    const containerWidth = containerRef.current?.clientWidth ?? 0;
    const rect = seqRef.current?.getBoundingClientRect?.();
    const sw = rect?.width ?? 0;
    const sh = rect?.height ?? 0;
    if (isVertical) {
      const ph = containerRef.current?.parentElement?.clientHeight ?? 0;
      if (containerRef.current && ph > 0) {
        const t = Math.ceil(ph);
        if (containerRef.current.style.height !== `${t}px`) containerRef.current.style.height = `${t}px`;
      }
      if (sh > 0) {
        setSeqHeight(Math.ceil(sh));
        const vp = containerRef.current?.clientHeight ?? ph ?? sh;
        setCopyCount(Math.max(ANIMATION_CONFIG.MIN_COPIES, Math.ceil(vp / sh) + ANIMATION_CONFIG.COPY_HEADROOM));
      }
    } else if (sw > 0) {
      setSeqWidth(Math.ceil(sw));
      setCopyCount(Math.max(ANIMATION_CONFIG.MIN_COPIES, Math.ceil(containerWidth / sw) + ANIMATION_CONFIG.COPY_HEADROOM));
    }
  }, [isVertical]);

  useResizeObserver(updateDimensions, [containerRef, seqRef], [logos, gap, logoHeight, isVertical]);
  useImageLoader(seqRef, updateDimensions, [logos, gap, logoHeight, isVertical]);
  useAnimationLoop(trackRef, targetVelocity, seqWidth, seqHeight, isHovered, effectiveHoverSpeed, isVertical);

  const handleMouseEnter = useCallback(() => {
    if (effectiveHoverSpeed !== undefined) setIsHovered(true);
  }, [effectiveHoverSpeed]);
  const handleMouseLeave = useCallback(() => {
    if (effectiveHoverSpeed !== undefined) setIsHovered(false);
  }, [effectiveHoverSpeed]);

  const renderLogoItem = useCallback((item: LogoItem, key: string) => {
    if (renderItem) {
      return <li key={key} style={{ flex: '0 0 auto', marginRight: gap, fontSize: logoHeight, lineHeight: 1 }}>{renderItem(item, key)}</li>;
    }
    const isNode = 'node' in item;
    const nodeStyle: CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      transition: scaleOnHover ? 'transform 0.3s cubic-bezier(0.4,0,0.2,1)' : undefined,
    };
    const imgStyle: CSSProperties = {
      height: logoHeight,
      width: 'auto',
      display: 'block',
      objectFit: 'contain',
      userSelect: 'none',
      pointerEvents: 'none',
      transition: scaleOnHover ? 'transform 0.3s cubic-bezier(0.4,0,0.2,1)' : undefined,
    };
    const content = isNode
      ? <span style={nodeStyle}>{(item as LogoNodeItem).node}</span>
      : <img src={(item as LogoImageItem).src} srcSet={(item as LogoImageItem).srcSet}
          sizes={(item as LogoImageItem).sizes} width={(item as LogoImageItem).width}
          height={(item as LogoImageItem).height} alt={(item as LogoImageItem).alt ?? ''}
          title={item.title} loading="lazy" decoding="async" draggable={false} style={imgStyle} />;

    const inner = item.href
      ? <a href={item.href} aria-label={item.ariaLabel ?? item.title ?? 'logo link'}
          target="_blank" rel="noreferrer noopener"
          style={{ display: 'inline-flex', alignItems: 'center', textDecoration: 'none' }}>{content}</a>
      : content;

    const onEnter = scaleOnHover ? (e: React.MouseEvent<HTMLLIElement>) => {
      const node = e.currentTarget.querySelector<HTMLElement>('span, img');
      if (node) node.style.transform = 'scale(1.2)';
    } : undefined;
    const onLeave = scaleOnHover ? (e: React.MouseEvent<HTMLLIElement>) => {
      const node = e.currentTarget.querySelector<HTMLElement>('span, img');
      if (node) node.style.transform = '';
    } : undefined;

    return (
      <li key={key} role="listitem"
        style={{ flex: '0 0 auto', marginRight: gap, fontSize: logoHeight, lineHeight: 1 }}
        onMouseEnter={onEnter} onMouseLeave={onLeave}>
        {inner}
      </li>
    );
  }, [renderItem, gap, logoHeight, scaleOnHover]);

  const logoLists = useMemo(() =>
    Array.from({ length: copyCount }, (_, ci) => (
      <ul key={`copy-${ci}`} role="list" aria-hidden={ci > 0}
        ref={ci === 0 ? seqRef : undefined}
        style={{ display: 'flex', alignItems: 'center', listStyle: 'none', margin: 0, padding: 0,
          ...(isVertical ? { flexDirection: 'column' } : {}) }}>
        {logos.map((item, ii) => renderLogoItem(item, `${ci}-${ii}`))}
      </ul>
    )), [copyCount, logos, renderLogoItem, isVertical]);

  const containerW = isVertical
    ? (toCssLength(width) === '100%' ? undefined : toCssLength(width))
    : (toCssLength(width) ?? '100%');

  const scaleVertPad = scaleOnHover ? logoHeight * 0.1 : 0;

  const fadeW = 'clamp(24px, 8%, 120px)';
  const fadeBase: CSSProperties = { position: 'absolute', top: 0, bottom: 0, pointerEvents: 'none', zIndex: 10, width: fadeW };

  return (
    <div ref={containerRef} role="region" aria-label={ariaLabel} className={className}
      style={{ position: 'relative', overflow: 'hidden', width: containerW,
        paddingTop: scaleVertPad, paddingBottom: scaleVertPad, ...style }}>
      {fadeOut && (
        <>
          <div style={{ ...fadeBase, left: 0, background: `linear-gradient(to right, ${fadeOutColor}, transparent)` }} />
          <div style={{ ...fadeBase, right: 0, background: `linear-gradient(to left, ${fadeOutColor}, transparent)` }} />
        </>
      )}
      <div ref={trackRef} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}
        style={{ display: 'flex', width: 'max-content', willChange: 'transform', userSelect: 'none',
          position: 'relative', zIndex: 0,
          ...(isVertical ? { flexDirection: 'column', height: 'max-content', width: '100%' } : {}) }}>
        {logoLists}
      </div>
    </div>
  );
});

LogoLoop.displayName = 'LogoLoop';

export default LogoLoop;
