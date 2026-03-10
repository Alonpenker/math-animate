import { useState, useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import type { JobStatus } from '@/services/api';

const MESSAGES: Partial<Record<JobStatus | string, string[]>> = {
  CREATED: [
    'Initializing your lesson...',
    'Setting up the workspace...',
  ],
  PLANNING: [
    'Crafting your video plan...',
    'Consulting the curriculum...',
    'Designing scenes for maximum clarity...',
    'Mapping out the visual journey...',
  ],
  APPROVED: [
    'Plan approved! Preparing code generation...',
  ],
  CODEGEN: [
    'Writing Manim animation code...',
    'Crafting mathematical animations...',
    'Building the visual sequences...',
  ],
  CODED: [
    'Code ready, starting verification...',
  ],
  VERIFYING: [
    'Checking animation syntax...',
    'Running quality checks...',
  ],
  FIXING: [
    'Fixing up a few things...',
    'The AI is polishing the animations...',
  ],
  VERIFIED: [
    'All checks passed! Starting the renderer...',
  ],
  RENDERING: [
    'Rendering your video...',
    'Animating mathematical concepts...',
    'Almost there \u2014 creating your masterpiece...',
    'This is the exciting part...',
  ],
};

interface DynamicLoaderProps {
  status: JobStatus | 'TIMEOUT' | null;
  connectionError: Error | null;
  onCancel?: () => void;
}

export function DynamicLoader({ status, connectionError }: DynamicLoaderProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const currentMessages = status && status !== 'TIMEOUT' ? MESSAGES[status] ?? [] : [];
  const displayMessage = currentMessages[messageIndex % Math.max(1, currentMessages.length)] ?? 'Working...';

  useEffect(() => {
    setMessageIndex(0);
  }, [status]);

  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    if (currentMessages.length > 1) {
      intervalRef.current = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % currentMessages.length);
      }, 3000);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [currentMessages]);

  return (
    <div className="flex flex-col items-center py-16 text-center">
      <Loader2 className="h-12 w-12 animate-spin text-brand-light" />
      <p className="mt-6 text-lg font-medium text-brand-text">{displayMessage}</p>
      {status && status !== 'TIMEOUT' && (
        <p className="mt-2 text-xs text-brand-muted">{status}</p>
      )}
      {connectionError && (
        <p className="mt-4 text-sm text-orange-600">
          Connection lost. Retrying...
        </p>
      )}
      {status === 'TIMEOUT' && (
        <p className="mt-4 text-sm text-red-600">
          This is taking longer than expected. Please try refreshing the page.
        </p>
      )}
    </div>
  );
}
