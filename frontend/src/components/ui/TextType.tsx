import { useState, useEffect, useRef } from 'react';
import { gsap } from 'gsap';

interface TextTypeProps {
  text: string;
  typingSpeed?: number;
  cursorBlinkDuration?: number;
  showCursor?: boolean;
  cursorCharacter?: string;
  className?: string;
  style?: React.CSSProperties;
}

export function TextType({
  text,
  typingSpeed = 38,
  cursorBlinkDuration = 0.5,
  showCursor = true,
  cursorCharacter = '|',
  className,
  style,
}: TextTypeProps) {
  const [displayed, setDisplayed] = useState('');
  const indexRef = useRef(0);
  const cursorRef = useRef<HTMLSpanElement>(null);

  // Blink cursor with GSAP
  useEffect(() => {
    if (!showCursor || !cursorRef.current) return;
    gsap.set(cursorRef.current, { opacity: 1 });
    const tween = gsap.to(cursorRef.current, {
      opacity: 0,
      duration: cursorBlinkDuration,
      repeat: -1,
      yoyo: true,
      ease: 'power2.inOut',
    });
    return () => { tween.kill(); };
  }, [showCursor, cursorBlinkDuration]);

  // Type out text character by character, reset when text changes
  useEffect(() => {
    setDisplayed('');
    indexRef.current = 0;

    const id = setInterval(() => {
      if (indexRef.current < text.length) {
        indexRef.current++;
        setDisplayed(text.slice(0, indexRef.current));
      } else {
        clearInterval(id);
      }
    }, typingSpeed);

    return () => clearInterval(id);
  }, [text, typingSpeed]);

  return (
    <span className={className} style={style}>
      {displayed}
      {showCursor && <span ref={cursorRef}>{cursorCharacter}</span>}
    </span>
  );
}
