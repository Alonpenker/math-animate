import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import type { JobStatus } from '@/services/api';
import { TextType } from '@/components/ui/TextType';

const MESSAGES: Partial<Record<JobStatus | string, string[]>> = {
  CREATED: ['Initializing your lesson...', 'Setting up the workspace...', 'Sharpening the chalk and clearing the board...', 'Getting everything ready for a smooth start...'],
  PLANNING: ['Crafting your video plan...', 'Consulting the curriculum...', 'Designing scenes for maximum clarity...', 'Mapping out the visual journey...', 'Sketching the lesson one step at a time...', 'Lining up the concepts for a clean explanation...'],
  APPROVED: ['Plan approved! Preparing code generation...', 'Green light received. Translating the plan into motion...', 'Turning the blueprint into animation instructions...'],
  CODEGEN: ['Writing Manim animation code...', 'Crafting mathematical animations...', 'Building the visual sequences...', 'Converting ideas into precise scene logic...', 'Teaching the renderer how each moment should unfold...'],
  CODED: ['Code ready, starting verification...', 'The animation script is in place and under review...', 'Checking that every scene is ready for the next step...'],
  VERIFYING: ['Checking animation syntax...', 'Running quality checks...', 'Making sure the math and motion stay in sync...', 'Inspecting each scene before it hits the screen...'],
  FIXING: ['Fixing up a few things...', 'The AI is polishing the animations...', 'Tidying the rough edges behind the scenes...', 'Adjusting details so the lesson flows cleanly...'],
  VERIFIED: ['All checks passed! Starting the renderer...', 'Everything looks solid. Sending it to render...', 'The lesson is cleared for production...'],
  RENDERING: ['Rendering your video...', 'Animating mathematical concepts...', 'Creating your masterpiece...', 'This is the exciting part...', 'Putting the final chalk strokes on the lesson...', 'Bringing the board to life frame by frame...'],
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

  useEffect(() => { setMessageIndex(0); }, [status]);
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (currentMessages.length > 1) {
      intervalRef.current = setInterval(() => {
        setMessageIndex(prev => (prev + 1) % currentMessages.length);
      }, 3000);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [currentMessages]);

  return (
    <div className="flex flex-col items-center py-20 text-center">
      <motion.div
        className="rounded-full"
        style={{
          width: 56, height: 56,
          border: '3px solid rgba(245,240,232,0.15)',
          borderTopColor: '#7EC8C8',
        }}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
      />
      <motion.p
        key={displayMessage}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.4 }}
        className="mt-6 text-xl text-chalk-white"
        style={{ fontFamily: 'Patrick Hand, cursive' }}
      >
        <TextType text={displayMessage} cursorCharacter="|" />
      </motion.p>
      {status && status !== 'TIMEOUT' && (
        <p className="mt-2 text-xs text-chalk-white/35" style={{ fontFamily: 'Inter, sans-serif' }}>{status}</p>
      )}
      {connectionError && (
        <p className="mt-4 text-sm text-chalk-orange" style={{ fontFamily: 'Inter, sans-serif' }}>
          Connection lost. Retrying...
        </p>
      )}
      {status === 'TIMEOUT' && (
        <p className="mt-4 text-sm text-red-400" style={{ fontFamily: 'Inter, sans-serif' }}>
          This is taking longer than expected. Please try refreshing the page.
        </p>
      )}
    </div>
  );
}
