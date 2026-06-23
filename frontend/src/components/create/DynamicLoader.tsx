import { AnimatePresence, motion } from 'framer-motion';
import type { JobStatus } from '@/services/api';
import { TextType } from '@/components/ui/TextType';
import { MathLoader } from '@/components/ui/MathLoader';
import { useShuffledMessageCycle } from '@/hooks/create/useShuffledMessageCycle';
import { LOADER_MESSAGES, FALLBACK_MESSAGES } from './loaderMessages';

interface DynamicLoaderProps {
  status: JobStatus | null;
  connectionError: Error | null;
  onCancel?: () => void;
}

export function DynamicLoader({ status, connectionError }: DynamicLoaderProps) {
  const currentMessages = (status ? LOADER_MESSAGES[status] : undefined) ?? FALLBACK_MESSAGES;
  const displayMessage = useShuffledMessageCycle(currentMessages) ?? 'Working...';

  return (
    <div className="flex flex-col items-center py-20 text-center">
      <MathLoader size={56} />
      <div className="relative mt-6 min-h-8 w-full">
        <AnimatePresence initial={false}>
          <motion.p
            key={displayMessage}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.4 }}
            className="absolute inset-0 text-xl text-off-white"
          >
            <TextType text={displayMessage} cursorCharacter="|" />
          </motion.p>
        </AnimatePresence>
      </div>
      {status && (
        <p className="mt-2 text-xs text-off-white/35">{status}</p>
      )}
      {connectionError && (
        <p className="mt-4 text-sm text-accent-orange">
          Connection lost. Retrying...
        </p>
      )}
    </div>
  );
}
