import { useEffect, useRef, useState } from 'react';

const DEFAULT_DELAY_MS = 3000;

function shuffledIndices(length: number, rand: () => number = Math.random): number[] {
  const indices = Array.from({ length: Math.max(0, length) }, (_, index) => index);

  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]];
  }

  return indices;
}

export function useShuffledMessageCycle(messages: readonly string[], delayMs = DEFAULT_DELAY_MS): string | null {
  const [messageIndex, setMessageIndex] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const queueRef = useRef<number[]>([]);

  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (messages.length === 0) {
      queueRef.current = [];
      setMessageIndex(0);
      return;
    }

    const nextQueue = shuffledIndices(messages.length);
    setMessageIndex(nextQueue.shift() ?? 0);
    queueRef.current = nextQueue;

    if (messages.length > 1) {
      intervalRef.current = setInterval(() => {
        setMessageIndex(() => {
          if (queueRef.current.length === 0) {
            queueRef.current = shuffledIndices(messages.length);
          }

          return queueRef.current.shift() ?? 0;
        });
      }, delayMs);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [delayMs, messages]);

  return messages[messageIndex] ?? null;
}
